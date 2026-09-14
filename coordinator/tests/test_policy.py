import json
from pathlib import Path

import pytest

from program_coordinator.models import SpecialistResult
from program_coordinator.policy import determine_policy
from helpers import harness, event, assessment, triage, seed_sources


def administrative_case():
    h = harness(event=event("touchless"))
    for call in json.loads((Path(__file__).parent / "data/cr018_reads.json").read_text()):
        h.sources.add(call["tool"], call["arguments"], call["data"], "validation_evidence", "work_test", {}, 0.0)
    h.state.scope_verified = True
    h.state.triage = triage()
    h.state.triage.risk_level = "low"
    h.state.completed_assessments = [SpecialistResult(invocation_id="work_test", specialist="validation_evidence",
                                                      assessment=assessment(h, "validation_evidence"))]
    return h


def test_touchless_requires_explicit_policy_and_actual_coverage():
    h = administrative_case()
    result = determine_policy(h.state, h.sources)
    assert result.policy_path == "touchless_eligible" and result.execution_allowed is False
    assert result.source_ids and result.rule == "existing_evidence_packet_only"


@pytest.mark.parametrize("alter", ["policy_draft", "policy_missing", "scope", "spend", "writes", "new_requirement", "unapproved", "coverage", "risk", "low_confidence", "missing_intake"])
def test_touchless_rule_fails_closed(alter):
    h = administrative_case()
    p = h.sources.latest("get_document", document_id="DOC-COORD-POLICY-01")["data"]
    req = h.sources.latest("get_document", document_id="DOC-COORD-REQUEST-018")["data"]
    body = json.loads(req["content"])
    if alter == "policy_draft": p["status"] = "draft"
    if alter == "policy_missing": h.sources.calls.remove(h.sources.latest("get_document", document_id="DOC-COORD-POLICY-01"))
    if alter == "scope": body["program_id"] = "PRG-OTHER"
    if alter == "spend": body["incremental_cost_cents"] = 1
    if alter == "writes":
        rule = json.loads(p["content"]); rule["permits_business_mutations"] = True; p["content"] = json.dumps(rule)
    if alter == "new_requirement": h.sources.latest("get_change_request")["data"]["proposed_requirement_revision_id"] = "REQ-042-V2"
    if alter == "unapproved": h.sources.latest("get_requirement_revision")["data"]["status"] = "requested"
    if alter == "coverage": h.state.completed_assessments[0].assessment.coverage_status = "insufficient"
    if alter == "risk": h.state.triage.risk_level = "high"
    if alter == "low_confidence": h.state.triage.confidence = 0.5
    if alter == "missing_intake": h.state.scope_verified = False
    req["content"] = json.dumps(body)
    result = determine_policy(h.state, h.sources)
    assert result.policy_path == "escalation_required" and not result.execution_allowed


def test_classification_and_approval_eligibility_do_not_authorize():
    h = seed_sources(harness()); h.state.triage = triage()
    h.state.triage.likely_policy_path = "touchless_eligible"
    h.state.triage.risk_level = "low"
    result = determine_policy(h.state, h.sources)
    assert result.policy_path == "human_review_required" and not result.execution_allowed


def test_conflicting_coordinator_findings_escalate():
    h = seed_sources(harness()); h.state.triage = triage()
    h.state.unresolved_questions = ["Specialists disagree about the required revision."]
    h.state.blocking_issues = list(h.state.unresolved_questions)
    assert determine_policy(h.state, h.sources).policy_path == "escalation_required"


def test_nonblocking_engineering_review_question_does_not_force_escalation():
    h = seed_sources(harness());h.state.triage = triage()
    h.state.unresolved_questions = ["Verify exact numerical limits during authorized engineering review."]
    assert determine_policy(h.state, h.sources).policy_path == "human_review_required"
    h.state.blocking_issues = ["Requirement scope is materially contradictory."]
    assert determine_policy(h.state, h.sources).policy_path == "escalation_required"


def test_touchless_still_requires_no_unresolved_questions():
    h = administrative_case();h.state.unresolved_questions = ["Does this evidence cover the request?"]
    assert determine_policy(h.state, h.sources).policy_path == "escalation_required"
