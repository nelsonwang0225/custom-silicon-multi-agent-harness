import json
from pathlib import Path

import pytest
from agents.agent_output import AgentOutputSchema
from pydantic import ValidationError

from program_coordinator.agents import build_agent, OUTPUTS
from program_coordinator.controls import GRAPH, TOOL_MATRIX, HarnessConfig, HarnessError, transition, validate_workflow
from program_coordinator.models import ProgramChangeEvent, WorkRequest, CaseState, Finding, FinalDecisionPackage
from program_investigator.mcp import READ_TOOLS

ROOT = Path(__file__).resolve().parents[2]


def event(name="human_review"):
    return ProgramChangeEvent.model_validate_json((ROOT / "coordinator/scenarios" / (name + ".json")).read_text())


def work(role="change_impact", **kwargs):
    return WorkRequest(specialist=role, question="Inspect the requested scope", rationale="Establish the requirement delta",
                       focus_record_ids=[], depends_on=kwargs.pop("depends_on", []), **kwargs)


@pytest.mark.parametrize("role", list(TOOL_MATRIX))
def test_five_agents_and_strict_schemas(role):
    agent = build_agent(role)
    assert agent.model == "gpt-6-astra"
    assert not agent.handoffs
    assert not agent.tools
    assert agent.model_settings.store is False
    schema = AgentOutputSchema(agent.output_type).json_schema()
    assert schema["additionalProperties"] is False
    assert agent.output_type == (OUTPUTS[role] if role != "coordinator" else __import__("program_coordinator.models", fromlist=["TriageDecision"]).TriageDecision)


@pytest.mark.parametrize("phase", ["triage", "reconcile", "synthesis"])
def test_coordinator_phase_schemas(phase):
    assert AgentOutputSchema(build_agent("coordinator", phase=phase).output_type).json_schema()


def test_matrix_is_least_privilege_and_read_only():
    assert all(allowed < READ_TOOLS for allowed in TOOL_MATRIX.values())
    assert TOOL_MATRIX["coordinator"] == {"get_change_request", "get_program", "get_document", "get_documents"}
    assert not any("manufacturing" in tool for tool in TOOL_MATRIX["validation_evidence"])
    assert all(name.startswith("get_") for names in TOOL_MATRIX.values() for name in names)
    assert set(GRAPH["manufacturing"]) == set()
    assert "manufacturing" not in GRAPH["change_impact"]
    assert "validation_evidence" not in GRAPH["program_commercial"]


@pytest.mark.parametrize("name", ["touchless", "human_review", "escalation"])
def test_same_generic_intake(name):
    assert isinstance(event(name), ProgramChangeEvent)


@pytest.mark.parametrize("patch", [{"received_at": "2026-11-16T09:00:00-05:00"}, {"event_id": "../secret"},
    {"source_system": "shell"}, {"priority": "urgent"}, {"request_summary": ""}, {"approved": True}])
def test_malformed_event(patch):
    with pytest.raises(ValidationError):
        ProgramChangeEvent.model_validate(event().model_dump() | patch)


def test_workflow_cycles_and_unknown_dependencies():
    validate_workflow([work("change_impact"), work("program_commercial", depends_on=["change_impact"])])
    for items in ([work("change_impact", depends_on=["manufacturing"])],
                  [work("change_impact", depends_on=["program_commercial"]), work("program_commercial", depends_on=["change_impact"])]):
        with pytest.raises(HarnessError, match="invalid_workflow_dependencies"):
            validate_workflow(items)


def test_state_is_application_owned_and_terminal():
    e = event()
    state = CaseState(case_id="case_test", correlation_id=e.correlation_id, customer_id=e.customer_id, program_id=e.program_id, event=e)
    transition(state, "triage")
    transition(state, "synthesis")
    transition(state, "completed")
    restored = CaseState.model_validate_json(state.model_dump_json())
    assert restored.workflow_stage == "completed" and len(restored.transitions) == 3
    with pytest.raises(HarnessError):
        transition(restored, "specialists")


def test_fact_requires_exact_assertion():
    with pytest.raises(ValidationError):
        Finding(statement="Validation passed", basis="fact", source_refs=[], facts=[])


def test_limits_have_hard_upper_bounds():
    for key, value in (("max_specialist_calls", 100), ("max_delegation_depth", 100), ("max_tool_calls", 1000), ("run_timeout_seconds", 10000)):
        with pytest.raises(ValidationError):
            HarnessConfig(**{key: value})


def test_work_metadata_schema_cannot_introduce_undiscovered_ids():
    from program_coordinator.models import scoped_work_output
    cls = scoped_work_output({"CR-017", "CFG-B-01"}, "triage")
    schema = AgentOutputSchema(cls).json_schema()
    ids = schema["$defs"]["ScopedWorkRequest"]["properties"]["focus_record_ids"]["items"]["enum"]
    assert set(ids) == {"CR-017", "CFG-B-01"}
    request = work().model_dump();request["focus_record_ids"] = ["WF-NOT-YET-DISCOVERED"]
    from helpers import triage
    with pytest.raises(ValidationError):
        cls.model_validate(triage().model_dump() | {"specialists_required": [request]})
