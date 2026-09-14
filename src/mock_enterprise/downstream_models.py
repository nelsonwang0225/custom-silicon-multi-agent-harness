"""Additive source contracts. Booking and execution approvals remain unchanged."""
from typing import Literal
from pydantic import Field
from .schemas import Model, Scoped, ID, Digest, UTC, Positive, Result, Job, JobView, Requirement, Snapshot, LabCompletion




class PublishResultInput(Model):
    expected_plan_digest: Digest


class EvidenceBinding(Model):
    review_policy: Literal['CR017-ENGINEERING-EVIDENCE-V1']
    change_id: Literal['CR-017']
    requirement: Requirement
    job: Job
    plan_id: ID
    plan_version: Positive
    plan_digest: Digest
    approval_id: ID
    completion: LabCompletion
    result: Result
    current_sources: list[Snapshot]
    evidence_set_digest: Digest


class EvidenceReview(Scoped):
    customer_id: ID
    change_id: ID
    job_id: ID
    plan_id: ID
    result_id: ID
    result_content_version: Positive
    evidence_digest: Digest
    review_version: Literal[1] = 1
    decision_type: Literal['engineering_evidence'] = 'engineering_evidence'
    decision: Literal['approve', 'reject']
    signer_identity: ID
    signer_role: Literal['engineer'] = 'engineer'
    reason: str = Field(max_length=1500)
    recorded_at: UTC
    evidence_binding: EvidenceBinding
    customer_acceptance: Literal['pending'] = 'pending'


class EvidenceReviewInput(Model):
    expected_evidence_digest: Digest
    decision: Literal['approve', 'reject']
    reason: str = Field(min_length=1, max_length=1500)


class PhysicalValidation(Model):
    change_id: Literal['CR-017'] = 'CR-017'
    available: bool = True
    job: JobView | None = None
    completion: LabCompletion | None = None
    result: Result | None = None
    job_status: Literal['not_scheduled', 'scheduled', 'completed', 'failed', 'running'] = 'not_scheduled'
    applicability: Literal['pending', 'confirmed', 'gap_remains'] = 'pending'
    mismatch_reasons: list[str] = Field(default_factory=list)
    evidence_digest: Digest | None = None
    evidence_binding: EvidenceBinding | None = None
    reviews: list[EvidenceReview] = Field(default_factory=list)
    current_review: EvidenceReview | None = None
    engineering_status: Literal['not_ready', 'ready', 'approved', 'rejected', 'stale'] = 'not_ready'
    technical_state: Literal['validation_pending', 'engineering_review_ready', 'validation_complete', 'validation_gap', 'engineering_rejected'] = 'validation_pending'
    customer_acceptance: Literal['pending'] = 'pending'
    customer_commitment: Literal['unchanged'] = 'unchanged'
