"""Durable orchestration references only; ERP/Planner own business records."""
from typing import Literal
from pydantic import Field
from ..models import Model, ID
from .quality_recovery_models import QualityActionRequest, QualityReviewRequest, QualityReconcileRequest

class DeliveryStep(Model):
    operation: Literal['prepare','review','erp','planner']
    key: ID
    request_digest: str
    status: Literal['started','action_succeeded','verified','outcome_unknown','failed','verification_failed']
    source_id: ID | None = None
    request_id: ID | None = None
    error_code: str | None = None

class DeliveryProgress(Model):
    run_id: ID
    case_id: ID
    delivery_id: ID
    context_digest: str
    input_digest: str
    status: str = 'analysis_complete'
    steps: dict[str,DeliveryStep] = Field(default_factory=dict)
    plan_id: ID | None = None
    plan_version: int | None = None
    plan_digest: str | None = None
    decision: Literal['approve','reject'] | None = None
    decision_comment: str | None = None
    error_code: str | None = None

# Reuse the existing exact-reference browser envelope; no quantity/date/actor input.
DeliveryActionRequest = QualityActionRequest
DeliveryReviewRequest = QualityReviewRequest
DeliveryReconcileRequest = QualityReconcileRequest
