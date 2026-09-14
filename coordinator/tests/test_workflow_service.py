"""Offline application-boundary checks using the existing CaseHarness/model double."""
import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
import json
import multiprocessing

import pytest
from pydantic import ValidationError

from program_coordinator.application.models import TrustedActor, WorkflowInvocation, WorkflowError
from program_coordinator.application.registry import list_workflows, dispatch_error
from program_coordinator.application.service import WorkflowService
from program_coordinator.application.store import ActivityStore
from program_coordinator.controls import HarnessConfig, TOOL_MATRIX
from program_coordinator.models import TriageDecision
from helpers import event, request
from test_orchestration import wired, ModelDouble, MemorySession
from test_policy import administrative_case


def actor():
    return TrustedActor("demo-reader", "reader", frozenset({("CUST-FML01", "PRG-A17")}))


def invocation(name="human_review", invocation_id="invoke_one", **updates):
    return WorkflowInvocation.model_validate(dict(invocation_id=invocation_id, customer_id="CUST-FML01",
        program_id="PRG-A17", event=event(name), **updates))


class ExistingHarnessAdapter:
    def __init__(self):
        self.calls = 0
        self.harnesses = []

    async def __call__(self, incoming, run):
        self.calls += 1
        if incoming.event.change_id == "CR-018":
            h = administrative_case()
            h.state.completed_assessments = []
            h.server_factory = MemorySession
            h.intake_source_ids = {r.source_id for r in h.state.source_references}
            async def intake(): pass
            h.intake_case = intake
            double = ModelDouble(h, [request("validation_evidence")])
            async def runner(agent, prompt, **kwargs):
                result = await double(agent, prompt, **kwargs)
                if issubclass(agent.output_type, TriageDecision):
                    result.final_output.classified_change_type = "administrative_evidence_reference"
                    result.final_output.risk_level = "low"
                return result
            h.runner = runner
        elif incoming.event.change_id is None:
            from helpers import harness
            h = harness(event=incoming.event)
            h.runner = ModelDouble(h)
        else:
            h, _ = wired([request("change_impact"), request("validation_evidence"), request("program_commercial")], nested=True)
        h.state.case_id, h.state.run_id = run.case_id, run.run_id
        h.state.workflow_id, h.state.workflow_definition_version = run.workflow_id, run.definition_version
        h.state.event = incoming.event
        self.harnesses.append(h)
        return await h.run()


def service(tmp_path, adapter=None):
    identity = actor()
    handler = adapter or ExistingHarnessAdapter()
    svc = WorkflowService(ActivityStore(tmp_path), config=HarnessConfig(), investigate=handler,
        actors=[identity], execution_mode="deterministic_test")
    return svc, identity, handler


def test_registry_reports_only_existing_analysis():
    definitions = list_workflows()
    assert {d.workflow_id for d in definitions} == {"requirement_change_analysis", "yield_exception_recovery", "delivery_readiness"}
    assert [d.supported_operations for d in definitions] == [("analyze",), ("analyze",), ("analyze",)]
    assert all(not d.business_execution_available for d in definitions)
    assert definitions[0].tool_policy_reference == "program_coordinator.controls.TOOL_MATRIX"
    assert set(definitions[0].participating_specialists) == set(TOOL_MATRIX) - {"coordinator"}
    with pytest.raises(ValidationError):
        definitions[1].implementation_status = "analysis_implemented"


@pytest.mark.parametrize("fields,code", [
    ({"workflow_id": "yield_exception_recovery", "operation":"execute"}, "OPERATION_NOT_IMPLEMENTED"),
    ({"workflow_id": "delivery_readiness", "operation":"execute"}, "OPERATION_NOT_IMPLEMENTED"),
    ({"workflow_id": "unknown"}, "UNKNOWN_WORKFLOW"),
    ({"definition_version": 2}, "UNSUPPORTED_WORKFLOW_VERSION"),
    ({"operation": "execute"}, "OPERATION_NOT_IMPLEMENTED"),
])
def test_unsupported_stops_before_agent_tool_or_case_start(tmp_path, fields, code):
    svc, identity, handler = service(tmp_path)
    result = asyncio.run(svc.invoke(invocation(**fields), identity))
    assert result.status == "unsupported" and result.error_code == code and result.run is None
    assert handler.calls == 0 and not svc.store.path.exists()


@pytest.mark.parametrize("name,path,roles", [
    ("human_review", "human_review_required", {"change_impact", "validation_evidence", "program_commercial", "manufacturing"}),
    ("touchless", "touchless_eligible", {"validation_evidence"}),
    ("escalation", "escalation_required", set()),
])
def test_existing_three_policy_paths_through_service(tmp_path, name, path, roles):
    svc, identity, handler = service(tmp_path)
    result = asyncio.run(svc.invoke(invocation(name), identity, trace_id="trace_offline"))
    assert result.status == "completed"
    assert result.run.recommendation.policy_path == path
    assert not result.run.customer_accepted and not result.run.business_execution_available
    assert result.run.execution_mode == "deterministic_test"
    assert result.run.data_provenance == "synthetic_source_systems"
    assert {w.specialist for w in handler.harnesses[0].state.requested_specialists} == roles
    restored = ActivityStore(tmp_path).runs(identity, customer_id="CUST-FML01", program_id="PRG-A17")
    assert restored == [result.run]
    events = svc.timeline(identity, customer_id="CUST-FML01", program_id="PRG-A17", case_id=result.run.case_id)
    assert [e.event_type for e in events] == ["case_created", "analysis_started", "analysis_completed", "recommendation_recorded"]
    assert all(e.trace_id == "trace_offline" and e.run_id == result.run.run_id for e in events)
    with svc.store.transaction() as data:
        assert not data.proposals and not data.decisions and not data.actions and not data.verifications


def test_reruns_reuse_case_and_retries_reuse_run_after_reload(tmp_path):
    svc, identity, handler = service(tmp_path)
    first = asyncio.run(svc.invoke(invocation(), identity))
    replay = asyncio.run(svc.invoke(invocation(), identity))
    assert replay.replayed and replay.run == first.run and handler.calls == 1
    svc, identity, handler = service(tmp_path)
    assert asyncio.run(svc.invoke(invocation(), identity)).replayed and handler.calls == 0
    second = asyncio.run(svc.invoke(invocation(invocation_id="invoke_two", case_id=first.run.case_id), identity))
    assert second.status == "completed" and second.run.case_id == first.run.case_id and second.run.run_id != first.run.run_id
    third = asyncio.run(svc.invoke(invocation(invocation_id="invoke_three"), identity))
    assert third.run.case_id == first.run.case_id
    with svc.store.transaction() as data:
        assert len(data.cases) == 1 and len(data.runs) == 3
        assert sum(e.event_type == "case_created" for e in data.activity) == 1


def test_same_invocation_changed_payload_is_conflict(tmp_path):
    svc, identity, handler = service(tmp_path)
    asyncio.run(svc.invoke(invocation(), identity))
    changed = invocation(); changed.event.request_summary += " Additional question."
    result = asyncio.run(svc.invoke(changed, identity))
    assert result.error_code == "INVOCATION_ID_CONFLICT" and handler.calls == 1


@pytest.mark.parametrize("kind", ["actor", "event", "mcp", "unknown_case", "wrong_case_change"])
def test_scope_denials_do_not_invoke_handler(tmp_path, kind):
    svc, identity, handler = service(tmp_path)
    incoming = invocation()
    if kind == "actor":
        identity = replace(identity, role="engineer")
    if kind == "event":
        incoming.event.program_id = "PRG-OTHER"
    if kind == "mcp":
        incoming.program_id = incoming.event.program_id = "PRG-OTHER"
        identity = TrustedActor("scoped", "reader", frozenset({("CUST-FML01", "PRG-OTHER")}))
        svc.actors[identity.actor_id] = identity
    if kind == "unknown_case":
        incoming.case_id = "case_missing"
    if kind == "wrong_case_change":
        first = asyncio.run(svc.invoke(invocation(), identity))
        incoming = invocation(invocation_id="invoke_two", case_id=first.run.case_id)
        incoming.event.change_id = "CR-OTHER"
    before = handler.calls
    result = asyncio.run(svc.invoke(incoming, identity))
    assert result.status == "rejected" and handler.calls == before


def test_client_role_and_trigger_permissions_are_not_contract_fields():
    for extra in ({"role": "engineer"}, {"actor": {"role": "engineer"}}, {"approved": True},
                  {"trigger": {"kind": "chat", "permitted_actions": ["schedule_validation"]}}):
        with pytest.raises(ValidationError):
            WorkflowInvocation.model_validate(invocation().model_dump() | extra)


@pytest.mark.parametrize("kind", ["manual", "schedule", "source_event", "chat"])
def test_trigger_labels_share_the_same_read_only_boundary(tmp_path, kind):
    svc, identity, handler = service(tmp_path)
    incoming = invocation("escalation");incoming.trigger.kind = kind
    result = asyncio.run(svc.invoke(incoming, identity))
    assert result.status == "completed" and handler.calls == 1
    assert result.run.trigger.kind == kind and not result.run.business_execution_available


def test_concurrent_duplicate_never_starts_second_investigation(tmp_path):
    async def exercise():
        svc, identity, handler = service(tmp_path)
        first, second = await asyncio.gather(svc.invoke(invocation(), identity), svc.invoke(invocation(), identity))
        assert handler.calls == 1 and first.run.run_id == second.run.run_id
        assert second.replayed and second.status == "running"
    asyncio.run(exercise())


def _process_claim(directory, request_json):
    run, replay = ActivityStore(directory).claim(WorkflowInvocation.model_validate_json(request_json), actor(), execution_mode="deterministic_test")
    return run.run_id, replay


def test_file_lock_prevents_duplicate_starts_across_processes(tmp_path):
    with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context("spawn")) as pool:
        futures = [pool.submit(_process_claim, str(tmp_path), invocation().model_dump_json()) for _ in range(2)]
        results = [f.result(timeout=30) for f in futures]
    assert len({r[0] for r in results}) == 1 and sorted(r[1] for r in results) == [False, True]


@pytest.mark.parametrize("cancelled", [False, True])
def test_failures_and_cancellation_are_persisted_and_not_restarted(tmp_path, cancelled):
    async def fail(*args):
        if cancelled: raise asyncio.CancelledError()
        raise RuntimeError("sensitive provider error text")
    svc, identity, _ = service(tmp_path, fail)
    if cancelled:
        with pytest.raises(asyncio.CancelledError): asyncio.run(svc.invoke(invocation(), identity))
    else:
        assert asyncio.run(svc.invoke(invocation(), identity)).status == "failed"
    replay = asyncio.run(svc.invoke(invocation(), identity))
    assert replay.replayed and replay.run.status == ("cancelled" if cancelled else "failed")
    assert "sensitive provider" not in svc.store.path.read_text()


def test_case_and_run_retrieval_enforce_scope(tmp_path):
    svc, identity, _ = service(tmp_path)
    asyncio.run(svc.invoke(invocation(), identity))
    with pytest.raises(WorkflowError):
        svc.timeline(identity, customer_id="CUST-FML01", program_id="PRG-OTHER")
    with pytest.raises(WorkflowError):
        svc.runs(replace(identity), customer_id="CUST-FML01", program_id="PRG-A17")
    assert len(svc.cases(identity, customer_id="CUST-FML01", program_id="PRG-A17")) == 1
    with pytest.raises(WorkflowError):
        svc.cases(identity, customer_id="CUST-OTHER", program_id="PRG-A17")


def test_existing_case_cannot_be_attached_to_another_authorized_program(tmp_path):
    svc, identity, _ = service(tmp_path)
    existing = asyncio.run(svc.invoke(invocation(), identity))
    other = TrustedActor("other_reader", "reader", frozenset({("CUST-OTHER", "PRG-OTHER")}))
    handler = ExistingHarnessAdapter()
    other_service = WorkflowService(ActivityStore(tmp_path), config=HarnessConfig(customer_id="CUST-OTHER", program_id="PRG-OTHER"),
        investigate=handler, actors=[other], execution_mode="deterministic_test")
    incoming = invocation(invocation_id="invoke_other", case_id=existing.run.case_id)
    incoming.customer_id = incoming.event.customer_id = "CUST-OTHER"
    incoming.program_id = incoming.event.program_id = "PRG-OTHER"
    result = asyncio.run(other_service.invoke(incoming, other))
    assert result.error_code == "CASE_SCOPE_MISMATCH" and handler.calls == 0


def test_legacy_checkpoint_additive_fields_are_optional():
    from pathlib import Path
    from program_coordinator.models import CaseState
    h, _ = wired()
    old = asyncio.run(h.run()).model_dump(mode="json")
    for key in ("run_id", "workflow_id", "workflow_definition_version"): old.pop(key)
    assert CaseState.model_validate_json(json.dumps(old)).run_id is None


def test_no_new_business_access_or_runner_in_application_modules():
    import ast
    from pathlib import Path
    directory = Path(__file__).resolve().parents[2] / "src/program_coordinator/application"
    forbidden = {"openai", "agents", "enterprise_api", "stratos_mcp", "sqlite3", "subprocess", "httpx", "httpx2"}
    for path in directory.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
            assert not any(n and n.split(".")[0] in forbidden and n not in {"enterprise_api.standard_models", "enterprise_api.standard_policy", "enterprise_api.quality_models", "enterprise_api.quality_policy", "enterprise_api.delivery_models", "enterprise_api.delivery_policy"} for n in names)
            assert not any(n and n.startswith("mock_enterprise") and n != "mock_enterprise.schemas" for n in names)
