"""Durable Phase 06 host state; never supplied as model tools or approval identity."""
from typing import Literal
from pydantic import Field
from mock_enterprise.schemas import PlanInput, Milestone, JobInput, LinkInput
from ..models import ID, Model, Text
from .contracts import Origin


class ProposalRef(Origin):
    proposal_id: ID
    proposal_version: int
    proposal_digest: str


class Preparation(Model):
    preparation_id: ID
    origin: Origin
    request: PlanInput
    milestone_before: Milestone
    rationale: Text
    created_at: str
    proposal_version: int
    supersedes_key: str | None
    proposal_key: str | None = None


class OperatorEscalation(Model):
    """Host-owned operator handoff; it grants no source or approval authority."""
    escalation_id: ID
    run_id: ID
    case_id: ID
    customer_id: ID
    program_id: ID
    change_id: Literal['CR-017'] = 'CR-017'
    stage: Literal['validation_plan', 'evidence_review'] = 'validation_plan'
    evidence_digest: str | None = None
    subject: Text
    recommendation: Text
    business_context: Text
    operator_notes: Text
    recommendation_digest: str
    submitted_by: ID
    submitted_at: str
    status: Literal['submitted'] = 'submitted'


class HumanReview(Model):
    review_id: ID
    reference: ProposalRef
    actor_id: ID
    actor_role: Literal['engineer'] = 'engineer'
    authority_source: str
    decision: Literal['approve', 'reject']
    comment: Text
    requested_at: str
    policy_id: ID
    policy_version: int
    source_reason: Text
    source_decision_id: ID | None = None
    decided_at: str | None = None
    status: Literal['recording', 'approved', 'rejected'] = 'recording'


class ExecutionStep(Model):
    action_id: ID
    status: Literal['not_attempted', 'started', 'succeeded', 'failed', 'unknown', 'already_completed'] = 'not_attempted'
    request: JobInput | LinkInput | None = None
    resource_id: ID | None = None
    error_code: str | None = None
    verification: Literal['matched', 'mismatch', 'inconclusive'] | None = None


class ExecutionRecord(Model):
    reference: ProposalRef
    status: Literal['proposal_ready', 'waiting_for_approval', 'approved', 'rejected', 'stale', 'superseded',
                    'resuming', 'executing', 'verifying', 'completed_execution', 'execution_failed',
                    'partially_executed', 'attention_required'] = 'proposal_ready'
    review_id: ID | None = None
    steps: list[ExecutionStep]
    error_code: str | None = None
    case_status: Literal['open', 'in_validation'] = 'open'
    validation_plan: Literal['proposed', 'approved', 'approved_and_scheduled'] = 'proposed'
    validation_coverage: Literal['pending_test_results'] = 'pending_test_results'
    customer_acceptance: Literal['pending'] = 'pending'
    hardware_adequacy: Literal['unvalidated'] = 'unvalidated'


class ExecutionAttempt(Model):
    attempt_id: ID
    action_id: ID
    reference: ProposalRef
    decision_id: ID
    idempotency_key: ID
    request: JobInput | LinkInput
    started_at: str
    finished_at: str | None = None
    outcome: Literal['started', 'succeeded', 'failed', 'unknown', 'already_completed'] = 'started'
    source_request_id: str | None = None
    resource_id: ID | None = None
    error_code: str | None = None


from .models import WorkflowError


class SourceReadFailure(WorkflowError):
    pass


class SourceFailure(WorkflowError):
    def __init__(self, code, *, unknown=False):
        super().__init__(code)
        self.unknown = unknown
