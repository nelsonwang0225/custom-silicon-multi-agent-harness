"""Strict model contracts and application-owned state, independent of conversation history."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, create_model

from program_investigator.models import ValidationOption

ID = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")]
Text = Annotated[str, Field(min_length=1, max_length=3000)]
Specialist = Literal["change_impact", "validation_evidence", "program_commercial", "manufacturing"]
Role = Literal["coordinator", "change_impact", "validation_evidence", "program_commercial", "manufacturing"]
ChangeType = Literal["validation_requirement_change", "workload_profile_change", "runtime_firmware_change",
                     "power_thermal_requirement", "performance_acceptance_change", "manufacturing_constraint",
                     "program_schedule_change", "customer_acceptance_change", "administrative_evidence_reference",
                     "existing_case_status", "standard_validation_package", "quality_exception", "delivery_readiness", "other_or_unknown"]
PolicyPath = Literal["touchless_eligible", "human_review_required", "escalation_required"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True, revalidate_instances="always")


class ProgramChangeEvent(Model):
    event_id: ID
    change_id: ID | None
    customer_id: ID | None
    program_id: ID | None
    source_system: Literal["engineering", "validation", "manufacturing", "erp", "planner", "customer_intake"]
    change_type_hint: ChangeType | None
    priority: Literal["low", "medium", "high", "critical"]
    requested_by: Text
    received_at: str
    request_summary: Text
    linked_record_ids: list[ID] = Field(max_length=30)
    correlation_id: ID

    @field_validator("received_at")
    @classmethod
    def utc_only(cls, value):
        if not value.endswith("Z") or datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset().total_seconds() != 0:
            raise ValueError("Explicit UTC timestamp required")
        return value


class WorkRequest(Model):
    specialist: Specialist
    question: Text
    rationale: Text
    focus_record_ids: list[ID]
    depends_on: list[Specialist]
    result_kind: Literal["domain_assessment", "validation_clarification"] = "domain_assessment"
    prior_assessment_invocation_id: ID | None = None

    @model_validator(mode="after")
    def clarification_scope(self):
        if self.result_kind == "validation_clarification":
            if self.specialist != "validation_evidence" or not self.prior_assessment_invocation_id:
                raise ValueError("Validation clarification requires a prior assessment invocation")
        elif self.prior_assessment_invocation_id is not None:
            raise ValueError("Prior assessment is only used by a clarification")
        return self


class StatusInspectionScope(Model):
    """Model-proposed scope, independently matched to authoritative intake by the host."""
    workflow_id: Literal["requirement_change_analysis"]
    intent: Literal["read_only_status"]
    change_id: ID
    customer_id: ID
    program_id: ID
    plan_id: ID
    job_id: ID
    implementation_link_id: ID
    questions: list[Literal["validation_job_status", "planner_linkage", "results_availability",
                            "customer_acceptance"]] = Field(min_length=1)


class TriageDecision(Model):
    classified_change_type: ChangeType
    confidence: float = Field(ge=0, le=1)
    rationale: Text
    specialists_required: list[WorkRequest] = Field(max_length=4)
    missing_information: list[Text]
    risk_level: Literal["low", "medium", "high", "critical"]
    proposed_workflow: Text
    likely_policy_path: PolicyPath
    status_inspection: StatusInspectionScope | None = None

    @model_validator(mode="after")
    def unique_work(self):
        roles = [w.specialist for w in self.specialists_required]
        if len(roles) != len(set(roles)):
            raise ValueError("Duplicate initial specialist")
        return self


class SourceReference(Model):
    source_id: ID
    tool_name: str
    record_id: str | None
    content_version: int | None
    record_version: int | None


class SourceFact(Model):
    """A checkable assertion about an exact JSON pointer within one MCP receipt."""
    source_id: ID
    pointer: str
    value_json: str


class Finding(Model):
    statement: Text
    basis: Literal["fact", "inference", "question", "recommendation", "missing_information"]
    source_refs: list[ID]
    facts: list[SourceFact]

    @model_validator(mode="after")
    def factual_basis(self):
        if self.basis == "fact" and (not self.facts or not self.source_refs):
            raise ValueError("Facts require exact source assertions")
        if any(f.source_id not in self.source_refs for f in self.facts):
            raise ValueError("Assertion must cite its receipt")
        return self


class KnowledgeEvidence(Model):
    verification_id: str
    document_id: str
    document_version: str
    chunk_id: str
    section: str | None
    profile: str
    program_id: str
    configuration_id: str | None
    approval_status: str
    current: bool
    historical: bool
    source_reference: str
    why_relevant: str


class Assessment(Model):
    knowledge_evidence: list[KnowledgeEvidence] = Field(default_factory=list, max_length=8)
    case_id: ID
    summary: Text
    confidence: float = Field(ge=0, le=1)
    unresolved_questions: list[Text]
    source_references: list[SourceReference]


class ChangeImpactAssessment(Assessment):
    change_type: ChangeType
    requirement_delta: list[Finding]
    affected_scope: list[Finding]
    confirmed_impacts: list[Finding]
    possible_impacts: list[Finding]
    unaffected_scope: list[Finding]
    missing_information: list[Text]


class EvidenceItem(Model):
    result_id: ID
    status: str
    criteria_passed: bool
    satisfies: bool
    mismatch_reasons: list[str]
    source_id: ID


class ValidationEvidenceAssessment(Assessment):
    coverage_status: Literal["sufficient", "insufficient", "unknown", "conflicting"]
    coverage_source_id: ID
    evidence_gaps: list[Finding]
    applicable_evidence: list[EvidenceItem]
    inapplicable_evidence: list[EvidenceItem]
    eligible_options: list[ValidationOption]
    ineligible_options: list[ValidationOption]
    technical_constraints: list[Finding]


class DeliveryClaim(Model):
    delivery_id: ID
    order_id: ID
    technical_readiness: Literal["READY", "BLOCKED", "CONDITIONAL", "UNKNOWN"]
    physical_total: int
    held_quantity: int
    allocated_quantity: int
    eligible_quantity: int
    requested_quantity: int | None
    gap_quantity: int | None
    customer_ready_quantity: int
    future_expected_quantity: int
    earliest_ship_at: str | None
    earliest_arrival_at: str | None
    proposed_at: str | None
    timing_status: Literal["supported", "conditional", "unknown", "late"]
    full_request_supportable: bool
    proposal_allowed: bool
    committed_quantity: int
    customer_agreement: Literal["pending", "accepted", "rejected"]
    allocation_authorized: Literal[False] = False
    commitment_changed: Literal[False] = False


class DeliveryAssessment(Assessment):
    context_source_id: ID
    delivery: DeliveryClaim
    findings: list[Finding] = Field(min_length=1)


class QualityClaim(Model):
    exception_id: ID
    lot_id: ID
    comparable: Literal["true", "false", "unknown"]
    confirmed_degradation: bool
    observed_rate_bps: int
    baseline_rate_bps: int | None
    held_quantity: int
    affected_eligible_quantity: int
    eligible_quantity: int
    requested_quantity: int
    gap_quantity: int
    root_cause: str | None
    evidence_status: Literal["available", "missing"]
    release_authorized: Literal[False] = False
    allocation_authorized: Literal[False] = False
    commitment_changed: Literal[False] = False


class QualityAssessment(Assessment):
    context_source_id: ID
    quality: QualityClaim
    findings: list[Finding] = Field(min_length=1)


class StandardValidationAssessment(Assessment):
    """Same Validation specialist, bounded standard-procedure analysis contract."""
    context_source_id: ID
    applicability_matches: bool
    procedure_id: ID | None
    procedure_content_version: int | None
    reusable_evidence_ids: list[ID]
    remaining_work_ids: list[ID]
    findings: list[Finding] = Field(min_length=1)
    lab_authorization: Literal["pending"] = "pending"
    physical_testing: Literal["not_started"] = "not_started"
    customer_acceptance: Literal["pending"] = "pending"


class ValidationClarificationResult(Assessment):
    """Additive evidence; never a replacement coverage assessment."""
    clarification_type: Literal["criteria_detail", "requirement_detail", "option_provenance"]
    question: Text
    prior_assessment_invocation_id: ID
    findings: list[Finding] = Field(min_length=1)
    invalidates_prior_coverage: bool
    introduces_blocker: bool


class MilestoneImpact(Model):
    milestone_id: ID
    baseline_at: str
    current_forecast_at: str
    forecast_status: str
    source_id: ID


class CustomerCommitment(Model):
    order_id: ID
    committed_delivery_at: str
    quantity: int
    quantity_unit: str
    source_id: ID


class ProgramCommercialAssessment(Assessment):
    affected_milestones: list[MilestoneImpact]
    dependencies: list[Finding]
    customer_commitments: list[CustomerCommitment]
    schedule_exposure: list[Finding]
    cost_context: list[Finding]
    owners: list[Finding]
    risks: list[Finding]


class UnitFinding(Model):
    unit_id: ID
    source_lot_id: ID
    restrictions: list[str]
    source_id: ID


class LotFinding(Model):
    lot_id: ID
    restrictions: list[str]
    source_id: ID


class ManufacturingAssessment(Assessment):
    units: list[UnitFinding]
    lots: list[LotFinding]
    active_restrictions: list[Finding]
    provenance_findings: list[Finding]
    freshness_findings: list[Finding]
    release_conditions: list[Finding]


AssessmentUnion = DeliveryAssessment | QualityAssessment | ChangeImpactAssessment | ValidationEvidenceAssessment | StandardValidationAssessment | ValidationClarificationResult | ProgramCommercialAssessment | ManufacturingAssessment


class SpecialistResult(Model):
    invocation_id: ID
    specialist: Specialist
    assessment: AssessmentUnion


class SpecialistSynopsis(Model):
    invocation_id: ID
    specialist: Specialist
    summary: Text


class PolicyDecision(Model):
    policy_path: PolicyPath
    rule: str
    reasons: list[str]
    source_ids: list[ID]
    execution_allowed: Literal[False] = False
    standard_context_digest: str | None = None
    quality_context_digest: str | None = None
    delivery_context_digest: str | None = None


class FinalDecisionPackage(Model):
    quality: QualityClaim | None = None
    delivery: DeliveryClaim | None = None
    case_id: ID
    customer_id: ID | None
    program_id: ID | None
    classified_change_type: ChangeType
    change_summary: Text
    affected_scope: list[Finding]
    specialist_findings: list[SpecialistSynopsis]
    confirmed_facts: list[Finding]
    evidence_gaps: list[Finding]
    available_options: list[ValidationOption]
    relevant_constraints: list[Finding]
    program_impact: list[Finding]
    risks: list[Finding]
    unresolved_questions: list[Text]
    recommended_next_step: Text
    policy_path: PolicyPath
    requires_human_review: bool
    escalation_reason: str | None
    source_references: list[SourceReference]
    business_actions_executed: Literal[False]
    approval_granted: Literal[False]
    customer_accepted: Literal[False]
    new_validation_pass_claimed: Literal[False]

    @model_validator(mode="after")
    def policy_consistency(self):
        if self.requires_human_review != (self.policy_path != "touchless_eligible"):
            raise ValueError("Review flag must match policy path")
        if self.policy_path == "escalation_required" and not self.escalation_reason:
            raise ValueError("Escalation reason required")
        if any(f.basis != "fact" for f in self.confirmed_facts):
            raise ValueError("Confirmed facts must be factual")
        return self


class QuestionResolution(Model):
    question: Text
    resolution: Text
    supporting_facts: list[SourceFact] = Field(min_length=1)


class CoordinatorReview(Model):
    """The Coordinator can request bounded follow-up work before final synthesis."""
    additional_work: list[WorkRequest] = Field(max_length=4)
    disagreements: list[Text]
    unresolved_questions: list[Text]
    ready_to_synthesize: bool
    resolved_questions: list[QuestionResolution] = Field(default_factory=list)
    blocking_issues: list[Text] = Field(default_factory=list)


def scoped_work_output(known_ids, phase, pending_questions=(), prior_assessments=()):
    """Constrain model-authored work metadata to already verified source IDs.

    The provider sees this bounded enum in its structured output schema. The
    runtime still applies all graph/scope checks independently before dispatch.
    """
    focus_type = Literal[tuple(sorted(known_ids))] if known_ids else ID
    work = create_model("ScopedWorkRequest", __base__=WorkRequest,
        result_kind=(Literal["domain_assessment", "validation_clarification"] if prior_assessments else Literal["domain_assessment"],
                     Field(default="domain_assessment")),
        prior_assessment_invocation_id=(Literal[tuple(prior_assessments)] | None if prior_assessments else type(None),
                                        Field(default=None)),
        focus_record_ids=(list[focus_type], Field(max_length=30 if known_ids else 0,
            description="Only IDs already established by structured source references. Do not copy IDs from document prose.")))
    base, field = (TriageDecision, "specialists_required") if phase == "triage" else (CoordinatorReview, "additional_work")
    fields = {field: (list[work], Field(max_length=4))}
    if phase == "reconcile":
        questions = tuple(dict.fromkeys(pending_questions))
        resolution = create_model("ScopedQuestionResolution", __base__=QuestionResolution,
            question=(Literal[questions] if questions else Text, Field(
                description="Select an exact question from the host pending-question set; never paraphrase.")))
        fields["resolved_questions"] = (list[resolution], Field(default_factory=list,
            max_length=len(questions), description="Resolve only host pending questions with exact source facts. Empty when none are pending."))
    return create_model("Scoped" + base.__name__, __base__=base, **fields)


class Invocation(Model):
    invocation_id: ID
    parent_invocation_id: ID | None
    caller: Role
    specialist: Specialist
    question: str
    rationale: str
    focus_record_ids: list[ID]
    result_kind: Literal["domain_assessment", "validation_clarification"] = "domain_assessment"
    prior_assessment_invocation_id: ID | None = None
    depth: int
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    started_ms: float
    ended_ms: float | None = None
    error: str | None = None


class CaseState(Model):
    # Presentation pacing is authored only by deterministic demo fixtures.
    # Zero for real model runs and older checkpoints; never an efficiency metric.
    demo_pacing_min_seconds: int = Field(default=0, ge=0, le=120)
    case_id: ID
    # Additive host linkage. Legacy checkpoints remain readable; this object
    # continues to represent one investigation's state, not the durable case.
    run_id: ID | None = None
    workflow_id: ID | None = None
    workflow_definition_version: int | None = None
    correlation_id: ID
    customer_id: ID | None
    program_id: ID | None
    event: ProgramChangeEvent
    workflow_stage: Literal["intake", "triage", "specialists", "reconcile", "synthesis", "completed", "terminated"] = "intake"
    scope_verified: bool = False
    triage: TriageDecision | None = None
    requested_specialists: list[Invocation] = Field(default_factory=list)
    completed_assessments: list[SpecialistResult] = Field(default_factory=list)
    pending_specialist_work: list[ID] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    coordinator_reviews: list[CoordinatorReview] = Field(default_factory=list)
    guardrail_events: list[str] = Field(default_factory=list)
    transitions: list[str] = Field(default_factory=list)
    policy_decision: PolicyDecision | None = None
    final_package: FinalDecisionPackage | None = None
    final_package_status: Literal["pending", "validated", "rejected", "unavailable"] = "pending"
    termination_reason: str | None = None
