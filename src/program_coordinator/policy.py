"""Conservative classification of a future policy path; never execution authority."""

import json
from typing import Literal
from pydantic import Field, ValidationError

from .models import Model, ID, PolicyDecision, ValidationEvidenceAssessment
from .status_inspection import status_scope_error, status_completion_error


class AdministrativeRule(Model):
    policy_kind: Literal["evidence_reference_packet"]
    policy_version: Literal[1]
    customer_id: ID
    program_id: ID
    permitted_followthrough: Literal["prepare_existing_evidence_packet"]
    requires_approved_identical_requirement: Literal[True]
    requires_sufficient_coverage: Literal[True]
    max_incremental_cost_cents: Literal[0]
    permits_business_mutations: Literal[False]


class AdministrativeRequest(Model):
    request_kind: Literal["evidence_reference_packet"]
    customer_id: ID
    program_id: ID
    change_id: ID
    policy_document_id: ID
    requirement_revision_id: ID
    requested_followthrough: Literal["prepare_existing_evidence_packet"]
    incremental_cost_cents: Literal[0]
    changes_configuration: Literal[False]
    changes_requirements: Literal[False]
    changes_customer_commitment: Literal[False]
    description: str


def determine_policy(state, registry):
    reasons = list(state.blocking_issues)
    failed = [w for w in state.requested_specialists if w.status != "completed"]
    assessments = [r.assessment for r in state.completed_assessments]
    if (not state.scope_verified or not state.triage or state.triage.confidence < 0.75
            or state.triage.classified_change_type == "other_or_unknown" or state.triage.missing_information
            or status_scope_error(state, registry)
            or status_completion_error(state, registry)
            or failed or reasons or any(a.confidence < 0.75 for a in assessments)):
        return PolicyDecision(policy_path="escalation_required", rule="incomplete_or_uncertain",
            reasons=reasons or ["Required scope, evidence, confidence, or specialist work is incomplete."], source_ids=[])
    if state.workflow_id == "delivery_readiness":
        from .delivery import policy
        return policy(state, registry)
    if state.workflow_id == "yield_exception_recovery":
        from .quality import policy
        return policy(state, registry)
    change_call = registry.latest("get_change_request", change_id=state.event.change_id)
    if not change_call:
        return PolicyDecision(policy_path="escalation_required", rule="change_not_verified",
                              reasons=["Authoritative change record missing."], source_ids=[])
    change = change_call["data"]
    if state.triage.classified_change_type == "existing_case_status":
        return PolicyDecision(policy_path="human_review_required", rule="existing_case_status_read_only",
            reasons=["Read-only verification of existing work. Testing, engineering review and customer acceptance remain separate; no action or approval is authorized."],
            source_ids=[change_call["source_id"]])
    request_call = registry.latest("get_document", document_id=change["request_document_id"])
    if request_call and request_call["data"].get("document_type") == "standard_validation_request":
        return standard_route_decision(state, registry)
    # A model hint/category never enables this rule. The request and approved policy
    # must be actual source-system documents with validated structured business fields.
    if request_call and request_call["data"].get("document_type") == "coordination_request":
        try:
            request = AdministrativeRequest.model_validate_json(request_call["data"]["content"])
            policy_call = registry.latest("get_document", document_id=request.policy_document_id)
            if not policy_call or policy_call["data"].get("document_type") != "coordination_policy" or policy_call["data"].get("status") != "approved":
                raise ValueError()
            rule = AdministrativeRule.model_validate_json(policy_call["data"]["content"])
            if (rule.customer_id != state.customer_id or rule.program_id != state.program_id
                    or request.customer_id != state.customer_id or request.program_id != state.program_id
                    or request.change_id != state.event.change_id):
                raise ValueError()
            baseline = registry.latest("get_requirement_revision", requirement_revision_id=change["baseline_requirement_revision_id"])
            target = registry.latest("get_requirement_revision", requirement_revision_id=change["proposed_requirement_revision_id"])
            validation = [a for a in assessments if isinstance(a, ValidationEvidenceAssessment)]
            if (state.triage.risk_level != "low" or state.unresolved_questions or not baseline or not target or baseline["data"] != target["data"]
                    or target["data"].get("status") != "approved" or target["data"]["id"] != request.requirement_revision_id
                    or not validation or any(a.coverage_status != "sufficient" for a in validation)):
                raise ValueError()
            return PolicyDecision(policy_path="touchless_eligible", rule="existing_evidence_packet_only",
                reasons=["Approved source policy permits preparation of existing evidence only; no engineering change, spend, approval, or business mutation is authorized."],
                source_ids=[change_call["source_id"], request_call["source_id"], policy_call["source_id"], target["source_id"],
                            *[a.coverage_source_id for a in validation]])
        except (ValidationError, ValueError, TypeError):
            return PolicyDecision(policy_path="escalation_required", rule="administrative_policy_not_satisfied",
                                  reasons=["The administrative request does not satisfy its approved source policy."], source_ids=[request_call["source_id"]])
    return PolicyDecision(policy_path="human_review_required", rule="consequential_change_review",
        reasons=["Engineering or program change requires authorized human review. Eligibility and classification are not approval."],
        source_ids=[change_call["source_id"]])


def standard_route_decision(state, registry):
    from enterprise_api.standard_models import StandardContext
    from enterprise_api.standard_policy import evaluate
    from .models import StandardValidationAssessment
    call = registry.latest("get_standard_change_context", change_id=state.event.change_id)
    roles = {r.specialist for r in state.completed_assessments}
    validation = [r.assessment for r in state.completed_assessments if isinstance(r.assessment, StandardValidationAssessment)]
    if (not call or not {"change_impact", "validation_evidence", "program_commercial"} <= roles or not validation
            or state.triage.classified_change_type != "standard_validation_package"):
        return PolicyDecision(policy_path="escalation_required", rule="standard_analysis_incomplete",
            reasons=["Standard handoff requires scoped Change Impact, Validation and Program analysis with authoritative context."], source_ids=[])
    try:
        context = StandardContext.model_validate(call["data"])
        result = evaluate(context)
        if context.change_id != state.event.change_id or (context.customer_id,context.program_id) != (state.customer_id,state.program_id):
            raise ValueError()
        if not registry.latest("get_program_milestone", program_id=state.program_id, milestone_id=context.change["milestone_id"]):
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        return PolicyDecision(policy_path="escalation_required", rule="standard_source_unavailable",
            reasons=["Exact standard context and milestone must be established from source reads."], source_ids=[])
    reasons = [c.reason for c in result.checks if not c.passed]
    if result.touchless_eligible:
        reasons = ["The exact approved standard scope permits intake handoff only. Existing evidence is reusable; standard lab work, lab authorization and customer acceptance remain downstream."]
    return PolicyDecision(policy_path="touchless_eligible" if result.touchless_eligible else "escalation_required",
        rule="standard_touchless_handoff_v1", reasons=reasons, source_ids=[call["source_id"]],
        standard_context_digest=context.context_digest)
