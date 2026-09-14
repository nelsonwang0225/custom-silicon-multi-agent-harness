"""Model-authored assessment contracts; no case-specific defaults or conclusions."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class SourceInput(Model):
    name: str
    value: str


class SourceReference(Model):
    ref_id: str
    tool_name: str
    inputs: list[SourceInput]
    record_id: str | None
    content_version: int | None
    record_version: int | None

    @field_validator("tool_name")
    @classmethod
    def canonical_tool_name(cls, value: str) -> str:
        # Some Responses outputs use the visible functions namespace in citations.
        # Execution still uses only the exact discovered tool names. The source
        # checker must subsequently match this canonical name and all inputs.
        return value.removeprefix("functions.")


class Finding(Model):
    statement: str
    basis: Literal["fact", "inference", "missing_information", "question", "recommendation"]
    source_refs: list[str] = Field(min_length=1)


class Entity(Model):
    id: str
    name: str
    source_refs: list[str] = Field(min_length=1)


class AffectedScope(Model):
    kind: str
    id: str
    description: str
    source_refs: list[str] = Field(min_length=1)


class Coverage(Model):
    status: Literal["sufficient", "insufficient", "unknown", "conflicting"]
    coverage_satisfied: bool | None
    explanation: str
    source_refs: list[str] = Field(min_length=1)


class Evidence(Model):
    result_id: str
    configuration_id: str
    workload_profile_id: str
    status: str
    criteria_passed: bool
    covered_context_bins: list[int]
    satisfies: bool
    mismatch_reasons: list[str]
    source_refs: list[str] = Field(min_length=1)


class ManufacturingContext(Model):
    unit_id: str
    source_lot_id: str
    unit_restrictions: list[str]
    lot_restrictions: list[str]
    provenance: str
    source_refs: list[str] = Field(min_length=1)


class Commitment(Model):
    order_id: str
    quantity: int = Field(ge=0)
    quantity_unit: str
    committed_delivery_at: str
    source_refs: list[str] = Field(min_length=1)


class Milestone(Model):
    milestone_id: str
    baseline_at: str
    current_forecast_at: str
    forecast_status: str
    source_refs: list[str] = Field(min_length=1)


class Timing(Model):
    lab_start_at: str
    execution_start_at: str
    lab_end_at: str
    review_ready_at: str
    deadline_slack_minutes: int


class ValidationOption(Model):
    """Exact API fields, identified by the slot/sample pair; no ranking or selection."""
    slot_id: str
    sample_id: str
    unit_id: str
    lot_id: str
    configuration_id: str
    procedure_id: str
    policy_id: str
    milestone_id: str
    rate_id: str
    cost_cents: int = Field(ge=0)
    currency: str
    resource_eligible: bool
    approval_eligible: bool
    meets_deadline: bool | None
    eligibility_reasons: list[str]
    approval_reasons: list[str]
    timing: Timing | None
    source_refs: list[str] = Field(min_length=1)

    @property
    def eligible(self) -> bool:
        return self.resource_eligible and self.approval_eligible and self.meets_deadline is True


class InvestigationResult(Model):
    case_id: str
    customer: Entity
    program: Entity
    change_summary: Finding
    affected_scope: list[AffectedScope]
    confirmed_facts: list[Finding]
    validation_coverage_status: Coverage
    evidence_gaps: list[Finding]
    relevant_evidence: list[Evidence]
    manufacturing_constraints: list[ManufacturingContext]
    customer_commitment: Commitment | None
    program_milestone: Milestone | None
    eligible_options: list[ValidationOption]
    ineligible_options: list[ValidationOption]
    risks: list[Finding]
    unresolved_questions: list[Finding]
    recommended_next_step: Finding
    requires_human_review: bool
    source_references: list[SourceReference] = Field(min_length=1)

    @model_validator(mode="after")
    def internally_consistent(self):
        refs = [r.ref_id for r in self.source_references]
        if len(refs) != len(set(refs)) or not self.requires_human_review:
            raise ValueError("Assessment must have unique sources and require human review")
        if any(f.basis != "fact" for f in self.confirmed_facts):
            raise ValueError("Confirmed facts must be labeled facts")
        if self.recommended_next_step.basis != "recommendation":
            raise ValueError("Next step must be labeled a recommendation")
        options = self.eligible_options + self.ineligible_options
        if len({(o.slot_id, o.sample_id) for o in options}) != len(options):
            raise ValueError("Duplicate option")
        if any(not o.eligible for o in self.eligible_options) or any(o.eligible for o in self.ineligible_options):
            raise ValueError("Option classification must preserve all API eligibility flags")
        coverage = self.validation_coverage_status
        if coverage.coverage_satisfied is not None and coverage.status != (
            "sufficient" if coverage.coverage_satisfied else "insufficient"
        ):
            raise ValueError("Coverage must agree with the API boolean")

        def walk(value):
            if isinstance(value, dict):
                if "source_refs" in value and not set(value["source_refs"]).issubset(refs):
                    raise ValueError("Unknown source reference")
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.model_dump())
        return self
