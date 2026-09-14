"""Host orchestration metadata only; operational records remain in source systems."""
from typing import Literal
from pydantic import Field
from ..models import Model, ID

class QualityStep(Model):
    operation: Literal['investigate','prepare','review','execute']
    key: ID
    request_digest: str
    status: Literal['started','action_succeeded','verified','outcome_unknown','failed','verification_failed']
    source_id: ID | None = None
    request_id: ID | None = None
    error_code: str | None = None

class QualityProgress(Model):
    run_id: ID
    case_id: ID
    exception_id: ID
    context_digest: str
    status: str = 'prepared'
    policy_route: str = 'quality_recovery'
    policy_reasons: list[str] = Field(default_factory=list)
    steps: dict[str, QualityStep] = Field(default_factory=dict)
    plan_id: ID | None = None
    plan_version: int | None = None
    plan_digest: str | None = None
    submission_id: ID | None = None
    submission_subject: str | None = None
    submitted_recommendation: str | None = None
    submitted_business_context: str | None = None
    operator_notes: str = ''
    submission_digest: str | None = None
    submitted_by: ID | None = None
    submitted_at: str | None = None
    decision: Literal['approve','reject'] | None = None
    decision_comment: str | None = None
    error_code: str | None = None

class QualityActionRequest(Model):
    run_id: ID
    plan_id: ID
    plan_version: int
    plan_digest: str

class QualityReviewRequest(QualityActionRequest):
    decision: Literal['approve','reject']
    comment: str = Field(default='', max_length=1500)

class QualitySubmissionRequest(QualityActionRequest):
    submission_id: str = Field(pattern=r"^ui_[A-Za-z0-9_-]{1,90}$")
    subject: str = Field(min_length=3, max_length=180)
    recommendation: str = Field(min_length=3, max_length=3000)
    business_context: str = Field(min_length=3, max_length=3000)
    operator_notes: str = Field(default='', max_length=2000)

class QualityReconcileRequest(Model):
    run_id: ID
