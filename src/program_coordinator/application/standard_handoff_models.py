"""Host-owned standard handoff progress, separate from human-approval proposals."""
from typing import Literal
from pydantic import Field
from enterprise_api.standard_models import TouchlessEligibility, HandoffPackage, ValidationIntake
from ..models import ID, Model

class StandardHandoff(Model):
    run_id: ID
    case_id: ID
    change_id: ID
    customer_id: ID
    program_id: ID
    version: int = 1
    status: Literal['review_required','prepared','action_started','action_succeeded','outcome_unknown',
                    'write_failed','handoff_verified','verification_failed','source_unavailable']
    eligibility: TouchlessEligibility | None = None
    package: HandoffPackage | None = None
    action_key: ID | None = None
    action_status: Literal['not_attempted','started','succeeded','failed','unknown'] = 'not_attempted'
    verification_status: Literal['not_started','verified','failed','unavailable'] = 'not_started'
    intake: ValidationIntake | None = None
    reused_existing: bool = False
    error_code: str | None = None
    reasons: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str

class HandoffActionRequest(Model):
    run_id: ID
    expected_version: int = Field(ge=1)
