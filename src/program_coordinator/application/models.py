"""Business activity metadata, separate from the existing SDK execution state."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field, JsonValue, field_validator

from ..models import ID, Model, Text, ProgramChangeEvent, FinalDecisionPackage, SourceReference


def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class WorkflowError(Exception):
    """Stable, non-sensitive application error code."""


@dataclass(frozen=True)
class TrustedActor:
    """Created by the trusted host, never parsed from an invocation or LLM output.

    Local demo hosts provide public mock identities, not authenticated humans.
    Production callers must resolve these attributes through their auth layer.
    """
    actor_id: str
    role: str
    scopes: frozenset[tuple[str, str]]  # (customer_id, program_id)
    identity_source: str = "local_demo"

    def require_scope(self, customer_id, program_id):
        if (customer_id, program_id) not in self.scopes:
            raise WorkflowError("SCOPE_FORBIDDEN")


class Trigger(Model):
    kind: Literal["manual", "schedule", "source_event", "chat"] = "manual"
    source_reference: ID | None = None
    event_name: Literal['quality_exception_created'] | None = None
    event_version: int | None = Field(default=None, ge=1)
    # Provenance only. Only the bounded trusted demo dispatcher supplies events.


class WorkflowInvocation(Model):
    workflow_id: ID = "requirement_change_analysis"
    definition_version: int = Field(default=1, ge=1)
    operation: ID = "analyze"
    invocation_id: ID
    customer_id: ID
    program_id: ID
    case_id: ID | None = None
    trigger: Trigger = Field(default_factory=Trigger)
    event: ProgramChangeEvent


class CaseRecord(Model):
    case_id: ID
    customer_id: ID
    program_id: ID
    change_id: ID | None
    intake_key: str
    created_at: str
    scope_verified: bool = False


class RunRecord(Model):
    run_id: ID
    case_id: ID
    customer_id: ID
    program_id: ID
    workflow_id: ID
    definition_version: int
    invocation_id: ID
    request_digest: str
    correlation_id: ID
    actor_id: ID
    actor_source: str
    trigger: Trigger
    trace_id: ID | None
    execution_mode: Literal["live_model", "deterministic_test"]
    data_provenance: Literal["synthetic_source_systems"] = "synthetic_source_systems"
    status: Literal["running", "completed", "failed", "cancelled"] = "running"
    started_at: str
    completed_at: str | None = None
    error_code: str | None = None
    artifact_directory: str | None = None
    recommendation: FinalDecisionPackage | None = None
    # Recommendations are existing final packages, not approvals or readiness.
    customer_accepted: Literal[False] = False
    business_execution_available: Literal[False] = False


class ActivityRecord(Model):
    event_id: ID
    timestamp: str
    customer_id: ID
    program_id: ID
    case_id: ID
    run_id: ID
    event_type: Literal["case_created", "analysis_started", "analysis_completed", "analysis_failed",
                        "analysis_cancelled", "recommendation_recorded", "proposal_retained", "policy_escalated", "quality_policy_confirmed",
                        "source_decision_retained", "action_record_retained", "verification_record_retained",
                        "proposal_created", "proposal_superseded", "approval_requested", "proposal_approved",
                        "proposal_rejected", "proposal_stale", "workflow_resumed", "action_started",
                        "validation_job_created", "program_plan_updated", "action_failed", "action_outcome_unknown",
                        "action_reconciled", "verification_started", "source_state_verified", "verification_failed",
                        "execution_partially_completed", "execution_completed", "execution_denied",
                        "standard_review_required", "standard_package_prepared", "standard_handoff_started",
                        "standard_action_succeeded", "standard_handoff_verified", "standard_verification_failed",
                        "standard_handoff_recovered", "standard_handoff_failed", "standard_handoff_unknown"]
    actor_id: ID
    actor_source: str
    trace_id: ID | None
    proposal_id: ID | None = None
    action_id: ID | None = None
    details: dict[str, JsonValue] = Field(default_factory=dict)
    source_references: list[SourceReference] = Field(default_factory=list)

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_utc(cls, value):
        if not value.endswith("Z"):
            raise ValueError("UTC timestamp required")
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class InvocationResult(Model):
    status: Literal["completed", "running", "failed", "cancelled", "unsupported", "rejected"]
    error_code: str | None = None
    replayed: bool = False
    run: RunRecord | None = None
