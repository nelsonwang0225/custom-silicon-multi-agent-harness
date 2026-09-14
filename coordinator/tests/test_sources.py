from copy import deepcopy
import json

import pytest

from program_coordinator.controls import HarnessError
from program_coordinator.models import SpecialistResult, PolicyDecision
from program_coordinator.sources import validate_assessment, validate_final, assert_scope, check_prose, validate_common
from helpers import harness, seed_sources, assessment, fact, triage, final


def test_versioned_projection_receipt_round_trips():
    from program_coordinator.models import SourceReference
    h = harness()
    sid = h.sources.add("get_dependencies", {"program_id": "PRG-A17", "milestone_id": "MS-ACCEPT-01"},
        {"program_id": "PRG-A17", "milestone_id": "MS-ACCEPT-01", "record_version": 1, "dependencies": []},
        "program_commercial", "work_test", {}, 0.0)
    ref = h.state.source_references[-1]
    assert ref.record_id == "MS-ACCEPT-01" and ref.record_version == 1
    h.sources.validate_reference(ref)
    aggregate = ref.model_copy(update={"record_id": None})
    h.sources.validate_reference(aggregate)
    for candidate in [ref.model_copy(update={"record_version": 2}), aggregate.model_copy(update={"record_version": 2})]:
        with pytest.raises(HarnessError, match="source_version_mismatch"):
            h.sources.validate_reference(candidate)


@pytest.mark.parametrize("role", ["change_impact", "validation_evidence", "program_commercial", "manufacturing"])
def test_each_domain_can_be_evaluated_independently(role):
    h = seed_sources(harness())
    validate_assessment(assessment(h, role), h.sources, {r.source_id for r in h.state.source_references})


@pytest.mark.parametrize("field,value", [("customer_id", "CUST-OTHER"), ("program_id", "PRG-OTHER")])
def test_nested_cross_scope_is_rejected(field, value):
    with pytest.raises(HarnessError, match="source_scope_mismatch"):
        assert_scope({"items": [{"nested": {field: value}}]}, "CUST-FML01", "PRG-A17")


def test_same_case_changed_source_version_rejected():
    h = seed_sources(harness())
    c = h.sources.calls[0]
    data = deepcopy(c["data"])
    data["content_version"] += 1
    with pytest.raises(HarnessError, match="source_version_changed"):
        h.sources.add(c["tool"], c["arguments"], data, "coordinator", "test", {}, 1.0)


@pytest.mark.parametrize("alter", ["source_id", "version", "pointer", "value", "unseen"])
def test_fabricated_citations_and_facts_rejected(alter):
    h = seed_sources(harness())
    a = assessment(h, "change_impact")
    allowed = {r.source_id for r in h.state.source_references}
    if alter == "source_id": a.source_references[0].source_id = "made_up"
    if alter == "version": a.source_references[0].content_version = 99
    if alter == "pointer": a.requirement_delta[0].facts[0].pointer = "/invented"
    if alter == "value": a.requirement_delta[0].facts[0].value_json = '"invented"'
    if alter == "unseen": allowed = set()
    with pytest.raises(HarnessError):
        validate_assessment(a, h.sources, allowed)


@pytest.mark.parametrize("claim", ["We approved the plan.", "Approval was granted.", "The customer accepted.",
    "Validation passed.", "The root cause is defective silicon.", "Customer commitment was changed.", "The hold was released."])
def test_unsupported_consequential_claims_rejected(claim):
    with pytest.raises(HarnessError, match="unsupported_consequential_claim"):
        check_prose(claim, seed_sources(harness()).sources)


@pytest.mark.parametrize("claim", ["No approval was granted.", "Validation has not passed.", "A hold must not be released without review.",
    "Customer acceptance is not established.", "The historical RES-BASELINE-B validation passed."])
def test_negated_and_historical_claims_are_not_new_actions(claim):
    check_prose(claim, seed_sources(harness()).sources)


@pytest.mark.parametrize("alter", ["coverage", "wrong_revision", "omitted_result", "cost", "timing", "hold", "missing_option", "eligible_late"])
def test_validation_rejects_semantic_and_numeric_fabrication(alter):
    h = seed_sources(harness())
    a = assessment(h, "validation_evidence")
    if alter == "coverage": a.coverage_status = "sufficient"
    if alter == "wrong_revision": next(e for e in a.inapplicable_evidence if e.result_id == "RES-LONG-A").mismatch_reasons = []
    if alter == "omitted_result": a.inapplicable_evidence.pop()
    if alter == "cost": a.eligible_options[0].cost_cents = 0
    if alter == "timing": a.eligible_options[0].timing.review_ready_at = "2026-11-16T10:00:00Z"
    if alter == "hold": next(o for o in a.ineligible_options if o.sample_id == "SAMPLE-B-018").eligibility_reasons = []
    if alter == "missing_option": a.ineligible_options.pop()
    if alter == "eligible_late":
        late = next(o for o in a.ineligible_options if o.resource_eligible)
        a.ineligible_options.remove(late); a.eligible_options.append(late)
    with pytest.raises(HarnessError):
        validate_assessment(a, h.sources, {r.source_id for r in h.state.source_references})


@pytest.mark.parametrize("alter", ["baseline", "forecast", "commitment", "quantity", "missing_order"])
def test_commercial_dates_and_money_are_not_invented(alter):
    h = seed_sources(harness()); a = assessment(h, "program_commercial")
    if alter == "baseline": a.affected_milestones[0].baseline_at = "2026-12-01T00:00:00Z"
    if alter == "forecast": a.affected_milestones[0].current_forecast_at = "2026-12-01T00:00:00Z"
    if alter == "commitment": a.customer_commitments[0].committed_delivery_at = "2026-11-18T00:00:00Z"
    if alter == "quantity": a.customer_commitments[0].quantity = 10000
    if alter == "missing_order": a.customer_commitments = []
    with pytest.raises(HarnessError):
        validate_assessment(a, h.sources, {r.source_id for r in h.state.source_references})


@pytest.mark.parametrize("alter", ["lot", "restrictions", "omitted_hold", "released"])
def test_manufacturing_holds_and_provenance(alter):
    h = seed_sources(harness()); a = assessment(h, "manufacturing")
    if alter == "lot": a.units[0].source_lot_id = "LOT-4491"
    if alter == "restrictions": a.lots[0].restrictions = []
    if alter == "omitted_hold": a.active_restrictions = []
    if alter == "released": a.summary = "The hold was released."
    with pytest.raises(HarnessError):
        validate_assessment(a, h.sources, {r.source_id for r in h.state.source_references})


@pytest.mark.parametrize("alter", [None, "policy", "specialist", "option", "gap", "unresolved", "scope"])
def test_final_is_consistent_with_specialists_and_policy(alter):
    h = seed_sources(harness()); h.state.triage = triage()
    h.state.completed_assessments = [SpecialistResult(invocation_id="work_test", specialist="validation_evidence", assessment=assessment(h, "validation_evidence"))]
    h.state.policy_decision = PolicyDecision(policy_path="human_review_required", rule="test", reasons=[], source_ids=[])
    h.state.unresolved_questions = ["Which owner will review?"]
    a = final(h)
    if alter == "policy": a.policy_path = "touchless_eligible"
    if alter == "specialist": a.specialist_findings = []
    if alter == "option": a.available_options = []
    if alter == "gap": a.evidence_gaps = []
    if alter == "unresolved": a.unresolved_questions = []
    if alter == "scope": a.customer_id = "CUST-OTHER"
    if alter:
        with pytest.raises(HarnessError): validate_final(a, h.sources, h.state, {r.source_id for r in h.state.source_references})
    else:
        validate_final(a, h.sources, h.state, {r.source_id for r in h.state.source_references})


def test_semantic_refinement_never_changes_execution_policy():
    h = seed_sources(harness());h.state.triage = triage()
    h.state.policy_decision = PolicyDecision(policy_path="human_review_required", rule="test", reasons=[], source_ids=[])
    a = final(h);a.classified_change_type = "validation_requirement_change"
    validate_final(a, h.sources, h.state, {r.source_id for r in h.state.source_references})
    a.classified_change_type = "other_or_unknown"
    with pytest.raises(HarnessError, match="requires_escalation"):
        validate_final(a, h.sources, h.state, {r.source_id for r in h.state.source_references})


@pytest.mark.parametrize("alter", [None, "invented_question", "wrong_fact", "unseen_source"])
def test_coordinator_resolution_requires_exact_pending_question_and_source_fact(alter):
    from program_coordinator.models import CoordinatorReview, QuestionResolution
    from program_coordinator.sources import apply_review
    h = seed_sources(harness())
    h.state.unresolved_questions = ["What is the recorded requirement status?"]
    h.state.blocking_issues = list(h.state.unresolved_questions)
    assertion = fact(h, "get_requirement_revision", "/status").facts[0]
    review = CoordinatorReview(additional_work=[], disagreements=[], unresolved_questions=[], ready_to_synthesize=True,
        resolved_questions=[QuestionResolution(question=h.state.unresolved_questions[0], resolution="The requirement remains requested.", supporting_facts=[assertion])],
        blocking_issues=[])
    allowed = {r.source_id for r in h.state.source_references}
    if alter == "invented_question": review.resolved_questions[0].question = "An unrelated question?"
    if alter == "wrong_fact": review.resolved_questions[0].supporting_facts[0].value_json = '"approved"'
    if alter == "unseen_source": allowed = set()
    if alter:
        with pytest.raises(HarnessError): apply_review(review, h.sources, h.state, allowed)
        assert h.state.unresolved_questions
    else:
        apply_review(review, h.sources, h.state, allowed)
        assert not h.state.unresolved_questions and not h.state.blocking_issues
        assert len(h.state.coordinator_reviews) == 1
