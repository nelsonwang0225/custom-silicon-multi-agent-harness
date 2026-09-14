"""Host-only additive envelopes around the EXISTING source Plan and Decision.

These pure contracts neither fetch records nor grant execution authority. A future
trusted adapter must obtain source records through approved HTTP/MCP interfaces.
Importing the existing Pydantic schemas does not import a source store or handler.
"""

import hashlib
import json
from typing import Literal

from pydantic import ConfigDict, Field, JsonValue, model_validator
from mock_enterprise.schemas import Plan, PlanView, Decision, Policy, Snapshot, JobInput, LinkInput, Milestone, UTC

from ..models import ID, Model, SourceReference, Text
from .models import TrustedActor, WorkflowError


def digest(value):
    # Same canonical JSON as the source-system plan digest; no backend-store import.
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


class Origin(Model):
    customer_id: ID
    program_id: ID
    case_id: ID
    run_id: ID
    workflow_id: ID
    definition_version: int = Field(ge=1)

    @classmethod
    def from_run(cls, run):
        return cls.model_validate({k: getattr(run, k) for k in cls.model_fields})


class ProposedAction(Model):
    action: Literal["schedule_validation", "link_program_plan"]
    arguments: dict[str, JsonValue]


class ManifestAction(Model):
    action_id: ID
    sequence: int
    operation: Literal["schedule_validation_job", "link_approved_validation_plan"]
    target_system: Literal["validation", "planner"]
    target: str
    arguments: dict[str, JsonValue]
    depends_on: ID | None
    idempotency_key: ID
    approval_reference: Literal["exact_proposal_decision"] = "exact_proposal_decision"
    expected: dict[str, JsonValue]


def plan_actions(plan):
    """Exact semantic action arguments already bound by the existing source plan.

    These are NOT new HTTP request bodies. Runtime approval/job IDs and Planner CAS
    are supplied separately through the unchanged JobInput/LinkInput contracts.
    """
    p = plan.model_dump(mode="json")
    common = {k: p[k] for k in ("program_id", "customer_id", "change_id")}
    common.update(plan_id=plan.id, plan_version=plan.plan_version, plan_digest=plan.plan_digest)
    definitions = {
        "schedule_validation": common | {k: p[k] for k in (
            "configuration_id", "procedure_id", "sample_id", "slot_id", "cost_cents", "currency", "timing", "review_minutes")},
        "link_program_plan": common | {"milestone_id": plan.milestone_id,
            "forecast_at": plan.timing.review_ready_at, "forecast_status": "conditional_on_test_and_review"},
    }
    if len(set(plan.permitted_actions)) != len(plan.permitted_actions):
        raise WorkflowError("INVALID_PLAN_ACTIONS")
    # Source permitted_actions is a permission set (currently sorted by name),
    # not execution order. Keep the scheduling-before-Planner dependency explicit.
    return [ProposedAction(action=name, arguments=arguments) for name, arguments in definitions.items()
            if name in plan.permitted_actions]


class Proposal(Model):
    model_config = ConfigDict(frozen=True)
    origin: Origin
    proposal_id: ID
    proposal_version: int = Field(ge=1)
    proposal_digest: str
    source_plan: Plan
    actions: list[ProposedAction]
    evidence_references: list[SourceReference]
    rationale: Text
    assumptions: list[Text]
    preconditions: list[Text]
    required_policy_id: ID
    required_policy_version: int = Field(ge=1)
    required_role: Literal["engineer"] = "engineer"
    # Additive Phase 06 fields. Empty defaults preserve legacy envelope digests.
    created_at: UTC | None = None
    manifest: list[ManifestAction] = Field(default_factory=list)
    milestone_before: Milestone | None = None


def proposal_digest(proposal):
    excluded = {"proposal_digest"}
    for name in ("created_at", "manifest", "milestone_before"):
        if not getattr(proposal, name):
            excluded.add(name)
    return digest(proposal.model_dump(mode="json", exclude=excluded))


def validate_proposal(proposal):
    # Revalidate every use: frozen outer models do not freeze nested dictionaries.
    proposal = Proposal.model_validate_json(proposal.model_dump_json())
    p = proposal.source_plan
    if (proposal.proposal_digest != proposal_digest(proposal)
            or p.plan_digest != digest(p.model_dump(mode="json", exclude={"plan_digest"}))):
        raise WorkflowError("PROPOSAL_CONTENT_CHANGED")
    if (proposal.origin.customer_id != p.customer_id or proposal.origin.program_id != p.program_id
            or proposal.proposal_id != p.id or proposal.required_policy_id != p.policy_id):
        raise WorkflowError("PROPOSAL_SCOPE_MISMATCH")
    if proposal.origin.workflow_id != "requirement_change_analysis" or proposal.origin.definition_version != 1:
        raise WorkflowError("PROPOSAL_WORKFLOW_UNSUPPORTED")
    if proposal.actions != plan_actions(p):
        raise WorkflowError("PROPOSAL_ACTION_MISMATCH")
    policy = next((s for s in p.source_snapshot if s.resource_type == "engineering.policy" and s.resource_id == p.policy_id), None)
    if not policy or policy.content_version != proposal.required_policy_version:
        raise WorkflowError("PROPOSAL_POLICY_MISMATCH")
    for snapshot in p.source_snapshot:
        if snapshot.content_digest != digest(snapshot.content):
            raise WorkflowError("SOURCE_CONTENT_CHANGED")
    return proposal


def proposal_from_plan(plan, origin, *, rationale, assumptions=(), preconditions=(), evidence_references=(), proposal_version=1,
                       created_at=None, manifest=(), milestone_before=None):
    """Wrap a trusted source plan read; no plan creation or approval occurs here."""
    raw = plan.model_dump(mode="json")
    source = Plan.model_validate({k: raw[k] for k in Plan.model_fields})
    policy = next(s for s in source.source_snapshot if s.resource_type == "engineering.policy" and s.resource_id == source.policy_id)
    proposal = Proposal(origin=origin, proposal_id=source.id, proposal_version=proposal_version, proposal_digest="pending",
        source_plan=source, actions=plan_actions(source), rationale=rationale, assumptions=list(assumptions),
        preconditions=list(preconditions), evidence_references=list(evidence_references),
        required_policy_id=source.policy_id, required_policy_version=policy.content_version,
        created_at=created_at, manifest=list(manifest), milestone_before=milestone_before)
    proposal = proposal.model_copy(update={"proposal_digest": proposal_digest(proposal)})
    return validate_proposal(proposal)


class DecisionBinding(Model):
    """Future host review binding plus the unchanged, server-recorded Decision.

    No factory records a decision here. An old source decision alone cannot prove
    review of this envelope; Phase 06 still needs the trusted binding workflow.
    """
    origin: Origin
    proposal_id: ID
    proposal_version: int = Field(ge=1)
    proposal_digest: str
    source_decision: Decision


class ContractCheck(Model):
    binding_valid: Literal[True] = True
    execution_allowed: Literal[False] = False
    note: str = "Contract consistency only. Source authorization, resource checks and execution remain separate."


def validate_decision_contract(proposal, decision, *, trusted_reviewer: TrustedActor,
        current_plan: PlanView, current_policy: Policy, current_sources: list[Snapshot], evidence_set_digest: str,
        proposal_status="current"):
    """Pure preflight over TRUSTED host-supplied records, never a write permit."""
    proposal = validate_proposal(proposal)
    if proposal_status != "current":
        raise WorkflowError("PROPOSAL_NOT_CURRENT")
    if decision is None:
        raise WorkflowError("APPROVAL_REQUIRED")
    decision = DecisionBinding.model_validate_json(decision.model_dump_json())
    source, p = decision.source_decision, proposal.source_plan
    if (decision.origin != proposal.origin or decision.proposal_id != proposal.proposal_id
            or decision.proposal_version != proposal.proposal_version or decision.proposal_digest != proposal.proposal_digest):
        raise WorkflowError("DECISION_PROPOSAL_MISMATCH")
    trusted_reviewer.require_scope(p.customer_id, p.program_id)
    if trusted_reviewer.role != "engineer" or trusted_reviewer.actor_id != source.signer_identity:
        raise WorkflowError("WRONG_APPROVER")
    if source.decision != "approve" or current_plan.state != "approved" or current_plan.decision_id != source.id:
        raise WorkflowError("APPROVAL_REQUIRED")
    if any(getattr(current_plan, k) != getattr(p, k) for k in Plan.model_fields):
        raise WorkflowError("STALE_PLAN")
    if (source.plan_id != p.id or source.plan_version != p.plan_version or source.plan_digest != p.plan_digest
            or source.signer_role != "engineer" or source.policy_content_version != proposal.required_policy_version
            or any(getattr(source, k) != getattr(p, k) for k in ("customer_id", "program_id", "change_id", "policy_id",
                "cost_cents", "permitted_actions", "source_snapshot", "configuration_id", "sample_id", "slot_id", "milestone_id"))):
        raise WorkflowError("DECISION_SOURCE_MISMATCH")
    if (current_policy.id != p.policy_id or current_policy.content_version != proposal.required_policy_version
            or current_policy.program_id != p.program_id or current_policy.status != "approved"
            or current_policy.approver_role != proposal.required_role or p.cost_cents > current_policy.max_incremental_cost_cents
            or p.procedure_id not in current_policy.permitted_procedure_ids
            or not set(p.permitted_actions) <= set(current_policy.permitted_actions)):
        raise WorkflowError("APPROVAL_POLICY_MISMATCH")
    prior = {(s.resource_type, s.resource_id): s for s in p.source_snapshot}
    current = {(s.resource_type, s.resource_id): s for s in current_sources}
    if len(prior) != len(p.source_snapshot) or len(current) != len(current_sources) or prior.keys() != current.keys():
        raise WorkflowError("INVALID_SOURCE_SET")
    if evidence_set_digest != p.evidence_set_digest:
        raise WorkflowError("STALE_EVIDENCE")
    for key, old in prior.items():
        new = current[key]
        if new.content_digest != digest(new.content) or (new.content_version, new.content_digest) != (old.content_version, old.content_digest):
            raise WorkflowError("STALE_SOURCE")
    # Availability and owned-reservation provenance still belong to the existing
    # per-action source validators. This function cannot replace check_live().
    return ContractCheck()


class ActionAttempt(Model):
    action_id: ID
    origin: Origin
    proposal_id: ID
    proposal_version: int
    proposal_digest: str
    decision_id: ID
    action: Literal["schedule_validation", "link_program_plan"]
    request: JobInput | LinkInput
    idempotency_key: ID
    attempted_at: UTC
    outcome: Literal["succeeded", "failed", "unknown"]
    source_request_id: ID | None
    resource_id: ID | None
    error_code: str | None

    @model_validator(mode="after")
    def request_matches_action(self):
        if (self.action == "link_program_plan") != isinstance(self.request, LinkInput):
            raise ValueError("Action must match the existing source request schema")
        if self.request.plan_id != self.proposal_id or self.request.approval_id != self.decision_id:
            raise ValueError("Action plan/decision references must match")
        if self.outcome == "succeeded" and (not self.source_request_id or not self.resource_id):
            raise ValueError("A successful action requires its source receipt and resource ID")
        return self


class VerificationRecord(Model):
    verification_id: ID
    action_id: ID
    origin: Origin
    verified_at: UTC
    claim: Literal["job_scheduled", "planner_link_recorded"]
    outcome: Literal["matched", "mismatch", "inconclusive"]
    source_references: list[SourceReference] = Field(min_length=1)
    explanation: Text
    test_passed: Literal[False] = False
    customer_accepted: Literal[False] = False
