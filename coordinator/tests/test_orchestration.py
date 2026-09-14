import asyncio
import json
from types import SimpleNamespace

import pytest
from agents.tool_context import ToolContext

from program_coordinator.agents import OUTPUTS
from program_coordinator.controls import HarnessConfig, HarnessError
from program_coordinator.harness import CaseHooks
from program_coordinator.models import (
    TriageDecision,
    CoordinatorReview,
    FinalDecisionPackage,
    QuestionResolution,
    SpecialistResult,
)
from helpers import harness, seed_sources, assessment, request, triage, final, event, fact


class MemorySession:
    def __init__(self, h, role, invocation_id):
        self.h = h
        self.seen_sources = {r.source_id for r in h.state.source_references}
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def list_tools(self): return []


class ModelDouble:
    """Tests scheduling with deterministic model responses, not an AI run."""
    def __init__(self, h, work=(), *, nested=False, fail=None, delay=0.01, malformed=None):
        self.h, self.work, self.nested, self.fail, self.delay, self.malformed = h, list(work), nested, fail, delay, malformed
        self.active = 0
        self.peak_active = 0
        self.started = []
        self.ended = []
        self.coordinator_phases = []
    async def __call__(self, agent, prompt, **kwargs):
        value = json.loads(prompt)
        if issubclass(agent.output_type, TriageDecision):
            self.coordinator_phases.append("triage")
            return SimpleNamespace(final_output=triage(self.work))
        if issubclass(agent.output_type, CoordinatorReview):
            self.coordinator_phases.append("reconcile")
            return SimpleNamespace(final_output=CoordinatorReview(additional_work=[], disagreements=[], unresolved_questions=[], ready_to_synthesize=True))
        if agent.output_type is FinalDecisionPackage:
            self.coordinator_phases.append("synthesis")
            return SimpleNamespace(final_output=final(self.h, self.h.state.policy_decision.policy_path))
        role = next(r for r, cls in OUTPUTS.items() if cls is agent.output_type)
        self.active += 1; self.peak_active = max(self.peak_active, self.active); self.started.append(role)
        try:
            await asyncio.sleep(self.delay)
            if self.fail == role: raise RuntimeError("private error must not be recorded")
            if self.malformed == role: return SimpleNamespace(final_output={"invalid": True})
            if self.nested and role == "validation_evidence":
                result = await agent.tools[0].on_invoke_tool(ToolContext(context=None, tool_name="consult_specialist", tool_call_id="call_test", tool_arguments="{}"),
                    json.dumps({"request": request("manufacturing", "Explain the held unit provenance.").model_dump()}))
                assert json.loads(result)["status"] == "completed"
            return SimpleNamespace(final_output=assessment(self.h, role))
        finally:
            self.active -= 1; self.ended.append(role)


def wired(work=(), **kwargs):
    h = seed_sources(harness(server_factory=MemorySession, config=kwargs.pop("config", HarnessConfig())))
    h.intake_source_ids = {r.source_id for r in h.state.source_references}
    async def intake(): pass
    h.intake_case = intake
    double = ModelDouble(h, work, **kwargs)
    h.runner = double
    return h, double


@pytest.mark.parametrize("roles", [[], ["change_impact"], ["change_impact", "validation_evidence", "program_commercial"]])
def test_zero_one_multiple_specialists_same_entrypoint(roles):
    h, model = wired([request(r) for r in roles])
    state = asyncio.run(h.run())
    assert state.workflow_stage == "completed"
    assert {r.specialist for r in state.completed_assessments} == set(roles)
    assert len(state.requested_specialists) == len(roles)
    assert not state.pending_specialist_work
    assert model.coordinator_phases[0] == "triage" and model.coordinator_phases[-1] == "synthesis"
    if len(roles) > 1:
        assert model.peak_active == len(roles)
        assert h.parallel_branches[0]["parallel"] is True


def test_dependency_wave_does_not_run_early():
    h, model = wired([request("change_impact"), request("program_commercial", depends_on=["change_impact"])])
    asyncio.run(h.run())
    assert model.peak_active == 1
    assert len(h.parallel_branches) == 2


def test_dynamic_specialist_call_returns_to_parent_and_coordinator():
    h, model = wired([request("validation_evidence")], nested=True)
    state = asyncio.run(h.run())
    assert [w.specialist for w in state.requested_specialists] == ["validation_evidence", "manufacturing"]
    assert state.requested_specialists[1].caller == "validation_evidence"
    assert state.requested_specialists[1].depth == 2
    assert h.delegations[0]["status"] == "completed"
    assert len(state.final_package.specialist_findings) == 2


def test_follow_up_evidence_gets_a_second_reconciliation_before_synthesis():
    """A live follow-up answer must be reconciled before the final guard runs."""
    question = "Which eligible option meets the review deadline?"
    follow_up = request("validation_evidence", question)
    h, model = wired([request("program_commercial")])
    reviews = 0

    async def runner(agent, prompt, **kwargs):
        nonlocal reviews
        result = await model(agent, prompt, **kwargs)
        if agent.output_type is OUTPUTS["program_commercial"]:
            result.final_output.unresolved_questions = [question]
        elif issubclass(agent.output_type, CoordinatorReview):
            reviews += 1
            if reviews == 1:
                result.final_output = CoordinatorReview(
                    additional_work=[follow_up],
                    disagreements=[],
                    unresolved_questions=[question],
                    ready_to_synthesize=True,
                )
            else:
                supporting = fact(h)
                result.final_output = CoordinatorReview(
                    additional_work=[],
                    disagreements=[],
                    unresolved_questions=[],
                    ready_to_synthesize=True,
                    resolved_questions=[
                        QuestionResolution(
                            question=question,
                            resolution="The follow-up supplied the required source-backed answer.",
                            supporting_facts=supporting.facts,
                        )
                    ],
                )
        return result

    h.runner = runner
    state = asyncio.run(h.run())
    assert reviews == 2
    assert state.workflow_stage == "completed"
    assert question not in state.unresolved_questions
    assert state.final_package_status == "validated"


def test_explicit_option_provenance_follow_up_uses_narrow_contract():
    h, _ = wired()
    prior = assessment(h, "validation_evidence")
    h.state.completed_assessments = [SpecialistResult(
        invocation_id="work_validation", specialist="validation_evidence", assessment=prior)]
    work = request("validation_evidence",
        "Provide exact SourceFact assertions for option timing. This is a provenance-only follow-up; "
        "do not repeat coverage or options investigation.")
    review = CoordinatorReview(additional_work=[work], disagreements=[], unresolved_questions=[],
                               ready_to_synthesize=True)

    normalized = h.normalize_reconciliation_work(review).additional_work[0]

    assert normalized.result_kind == "validation_clarification"
    assert normalized.prior_assessment_invocation_id == "work_validation"


@pytest.mark.parametrize("kind", ["edge", "cycle", "depth", "max_calls", "duplicate", "scope"])
def test_delegation_controls_are_code_enforced(kind):
    h = harness(config=HarnessConfig(max_specialist_calls=1) if kind == "max_calls" else HarnessConfig())
    with pytest.raises(HarnessError):
        if kind == "edge": h.reserve(request("manufacturing"), "change_impact", ("change_impact",), "parent")
        if kind == "cycle": h.reserve(request("change_impact"), "program_commercial", ("change_impact", "program_commercial"), "parent")
        if kind == "depth": h.reserve(request("manufacturing"), "validation_evidence", ("change_impact", "validation_evidence"), "parent")
        if kind in {"max_calls", "duplicate"}:
            h.reserve(request("change_impact"), "coordinator", (), None)
            h.reserve(request("change_impact"), "coordinator", (), None)
        if kind == "scope":
            w = request("change_impact"); w.focus_record_ids = ["CUST-OTHER"]
            h.reserve(w, "coordinator", (), None)


def test_running_sibling_consultation_never_waits_or_creates_cycle():
    async def scenario():
        h = harness()
        parent = h.reserve(request("validation_evidence"), "coordinator", (), None)
        sibling = h.reserve(request("program_commercial"), "coordinator", (), None)
        tool = h.consultation_tool(parent, ("validation_evidence",), set())
        result = await tool.on_invoke_tool(ToolContext(context=None, tool_name="consult_specialist", tool_call_id="call_test", tool_arguments="{}"), json.dumps({"request": request("program_commercial").model_dump()}))
        assert json.loads(result)["status"] == "already_running" and json.loads(result)["invocation_id"] == sibling.invocation_id
        assert len(h.state.requested_specialists) == 2
    asyncio.run(scenario())


@pytest.mark.parametrize("failure", ["error", "timeout", "malformed"])
def test_failed_work_is_recorded_and_never_promoted_to_success(failure):
    cfg = HarnessConfig(specialist_timeout_seconds=0.005) if failure == "timeout" else HarnessConfig()
    h, model = wired([request("validation_evidence")], config=cfg,
        fail="validation_evidence" if failure == "error" else None,
        malformed="validation_evidence" if failure == "malformed" else None)
    state = asyncio.run(h.run())
    assert state.final_package.policy_path == "escalation_required"
    assert not state.completed_assessments
    assert state.requested_specialists[0].status == "failed"
    assert state.unresolved_questions and not state.pending_specialist_work
    assert "private error" not in state.model_dump_json()


def test_missing_required_dependency_terminates_and_records_reason():
    h, _ = wired([request("change_impact"), request("program_commercial", depends_on=["change_impact"])], fail="change_impact")
    with pytest.raises(HarnessError, match="missing_specialist_dependency"):
        asyncio.run(h.run())
    assert h.state.workflow_stage == "terminated"
    assert h.state.termination_reason == "missing_specialist_dependency"


def test_case_timeout_cancels_all_pending_branches():
    h, model = wired([request("change_impact"), request("program_commercial")], config=HarnessConfig(run_timeout_seconds=0.01), delay=1)
    with pytest.raises(TimeoutError): asyncio.run(h.run())
    assert h.state.workflow_stage == "terminated" and h.state.termination_reason == "case_timeout"
    assert not h.state.pending_specialist_work
    assert all(w.status == "cancelled" for w in h.state.requested_specialists)


def test_low_confidence_triage_cannot_launch_specialists():
    h, model = wired([request("change_impact")])
    async def runner(agent, prompt, **kwargs):
        if issubclass(agent.output_type, TriageDecision):
            t = triage([request("change_impact")]); t.confidence = 0.4
            return SimpleNamespace(final_output=t)
        return await model(agent, prompt, **kwargs)
    h.runner = runner
    state = asyncio.run(h.run())
    assert not state.requested_specialists
    assert "triage_specialists_suppressed" in state.guardrail_events
    assert state.final_package.policy_path == "escalation_required"


def test_incomplete_event_uses_no_source_or_specialist():
    h = harness(event=event("escalation"))
    model = ModelDouble(h)
    h.runner = model
    state = asyncio.run(h.run())
    assert not h.sources.calls and not state.requested_specialists
    assert state.final_package.policy_path == "escalation_required"
    assert len(model.coordinator_phases) == 2


def test_coordinator_total_turn_budget():
    async def scenario():
        h = harness(config=HarnessConfig(max_coordinator_turns=2))
        hooks = CaseHooks(h, "coordinator", "test", "triage")
        await hooks.on_llm_start(None, None, None, None)
        await hooks.on_llm_start(None, None, None, None)
        with pytest.raises(HarnessError, match="max_coordinator_turns"):
            await hooks.on_llm_start(None, None, None, None)
    asyncio.run(scenario())


def test_failed_wave_admission_leaves_no_stranded_pending_work():
    async def scenario():
        h = harness()
        bad = request("validation_evidence");bad.focus_record_ids = ["UNKNOWN"]
        with pytest.raises(HarnessError, match="delegation_scope_mismatch"):
            await h.execute_batch([request("change_impact"), bad])
        assert not h.state.requested_specialists and not h.state.pending_specialist_work
        assert not h.seen_requests
    asyncio.run(scenario())


@pytest.mark.parametrize("reconcile_rounds", [0, 1])
def test_touchless_never_ignores_specialist_questions_at_policy_boundary(reconcile_rounds):
    from test_policy import administrative_case
    h = administrative_case()
    h.config = HarnessConfig(max_reconcile_rounds=reconcile_rounds)
    h.server_factory = MemorySession
    h.state.completed_assessments = []
    h.intake_source_ids = {r.source_id for r in h.state.source_references}
    async def intake(): pass
    h.intake_case = intake
    model = ModelDouble(h, [request("validation_evidence")])
    question = "Is a later source restriction relevant to this packet?"
    async def runner(agent, prompt, **kwargs):
        result = await model(agent, prompt, **kwargs)
        if issubclass(agent.output_type, TriageDecision):
            result.final_output.classified_change_type = "administrative_evidence_reference"
            result.final_output.risk_level = "low"
        elif agent.output_type is OUTPUTS["validation_evidence"]:
            result.final_output.unresolved_questions = [question]
        return result
    h.runner = runner
    state = asyncio.run(h.run())
    assert state.policy_decision.policy_path == "escalation_required"
    assert question in state.final_package.unresolved_questions
