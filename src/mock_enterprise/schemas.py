from datetime import datetime
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, JsonValue, model_validator


def utc_string(value: str) -> str:
    if not value.endswith('Z'):
        raise ValueError('UTC timestamp ending in Z required')
    datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value


UTC = Annotated[str, AfterValidator(utc_string)]
ID = Annotated[str, Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')]
Positive = Annotated[int, Field(strict=True, gt=0)]
Cents = Annotated[int, Field(strict=True, ge=0)]
Text = Annotated[str, Field(min_length=1, max_length=2000)]
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Action = Literal['schedule_validation', 'link_program_plan']
Domain = Literal['engineering', 'validation', 'manufacturing', 'erp', 'planner']
SourceType = Literal[
    'engineering.supplier', 'engineering.customer', 'engineering.configuration',
    'engineering.workload', 'engineering.requirement', 'engineering.change',
    'engineering.procedure', 'engineering.criteria', 'engineering.policy', 'engineering.document',
    'validation.result', 'validation.lab', 'validation.slot', 'validation.sample',
    'manufacturing.unit', 'manufacturing.lot', 'erp.order', 'erp.rate',
    'planner.program', 'planner.milestone',
]


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')


T = TypeVar('T')


class Items(Model, Generic[T]):
    items: list[T]


class Record(Model):
    id: ID
    content_version: Positive = 1
    updated_at: UTC
    synthetic: Literal[True] = True
    owning_system: Domain


class Scoped(Record):
    program_id: ID


class Supplier(Record):
    name: str


class Customer(Supplier):
    kind: str


class Configuration(Scoped):
    product_id: ID
    product_revision: str
    model_bundle_id: ID
    device_count: Positive
    firmware: str
    runtime: str
    quantization: str
    memory_configuration: str
    validation_support: str | None = None


class Workload(Scoped):
    model_bundle_id: ID
    context_bins: list[Positive]
    concurrency: Positive
    output_tokens: Positive
    total_suite_minutes: Positive


class Requirement(Scoped):
    summary: str | None = None
    requirement_id: ID
    revision: Positive
    customer_id: ID
    status: Literal['approved', 'requested']
    configuration_id: ID
    workload_profile_id: ID
    acceptance_limits_ref: ID


class Change(Scoped):
    category: str | None = None
    owner: str | None = None
    priority: Literal['critical', 'high', 'medium', 'low'] | None = None
    next_action: str | None = None
    customer_id: ID
    baseline_requirement_revision_id: ID
    proposed_requirement_revision_id: ID
    configuration_id: ID
    milestone_id: ID
    order_id: ID
    request_document_id: ID
    workflow_state: Literal['pending_impact_assessment', 'plan_drafted', 'approved_awaiting_scheduling', 'plan_rejected', 'new', 'awaiting_customer_clarification', 'blocked', 'closed', 'superseded']
    record_version: Positive
    request_received_at: UTC
    title: str
    current_plan_id: ID | None = None


class Procedure(Scoped):
    status: Literal['approved', 'retired']
    document_id: ID
    supported_configuration_ids: list[ID]
    workload_profile_id: ID
    setup_minutes: Positive
    suite_minutes: Positive
    per_bin_minutes: Positive
    review_minutes: Positive
    acceptance_limits_ref: ID


class Criteria(Scoped):
    status: Literal['approved', 'retired']
    scope: str
    writable: Literal[False]


class Policy(Scoped):
    status: Literal['approved', 'retired']
    permitted_procedure_ids: list[ID]
    approver_role: Literal['engineer']
    max_incremental_cost_cents: Cents
    currency: Literal['USD']
    permitted_actions: list[Action]
    document_id: ID


class DocumentMetadata(Scoped):
    customer_id: ID
    document_type: str
    status: str
    document_version: str
    content_hash: Digest
    title: str | None = None
    product: ID | None = None
    configuration_id: ID | None = None
    owner_team: str | None = None
    effective_date: UTC | None = None
    superseded_by: ID | None = None
    applicable_workflows: list[str] | None = None
    historical: bool = False


class Document(DocumentMetadata):
    status: Literal['requested', 'approved', 'draft', 'historical']
    content: str


class Result(Scoped):
    customer_id: ID
    configuration_id: ID
    configuration_content_version: Positive
    workload_profile_id: ID
    workload_profile_content_version: Positive
    acceptance_limits_ref: ID
    acceptance_criteria_content_version: Positive
    product_revision: str
    model_bundle_id: ID
    sample_id: ID
    status: Literal['completed', 'running', 'failed']
    criteria_passed: bool
    covered_context_bins: list[Positive]
    actual_suite_minutes: Cents
    observed_minutes_by_context_bin: dict[str, Cents]
    completed_at: UTC
    configuration_snapshot: Configuration
    workload_snapshot: Workload
    criteria_snapshot: Criteria


class Lab(Scoped):
    campus: str
    supported_configuration_ids: list[ID]
    supported_procedure_ids: list[ID]


class Available(Scoped):
    availability: Literal['available', 'reserved', 'unavailable']
    availability_version: Positive
    reserved_by_job_id: ID | None = None


class Slot(Available):
    lab_id: ID
    starts_at: UTC
    ends_at: UTC
    rate_id: ID


class Sample(Available):
    unit_id: ID
    configuration_id: ID
    campus: str


class HoldDetail(Model):
    restriction: Text
    rationale: Text
    responsible_team: Text
    release_conditions: Text


class Lot(Scoped):
    inventory_state: str | None = None
    product_id: ID
    product_revision: str
    restrictions: list[str]
    hold_details: list[HoldDetail] = Field(default_factory=list)

    @model_validator(mode='after')
    def known_restrictions(self):
        refs = [detail.restriction for detail in self.hold_details]
        if len(refs) != len(set(refs)) or not set(refs).issubset(self.restrictions):
            raise ValueError('Hold details must uniquely describe recorded restrictions')
        return self


class Unit(Lot):
    source_lot_id: ID


class Order(Scoped):
    customer_id: ID
    product_id: ID
    product_revision: str
    quantity: Positive
    quantity_unit: Literal['accelerator_units']
    planning_unit_value_cents: Cents | None = None
    planning_value_basis: Text | None = None
    committed_delivery_at: UTC
    status: str


class Rate(Scoped):
    service_name: Text | None = None
    service_description: Text | None = None
    currency: Literal['USD']
    incremental_cost_cents: Cents
    status: Literal['approved', 'retired']
    effective_from: UTC
    effective_to: UTC


class Program(Scoped):
    name: str | None = None
    business_unit: str | None = None
    lifecycle: str | None = None
    health: str | None = None
    next_action: str | None = None
    customer_id: ID
    supplier_id: ID
    product_id: ID
    product_revision: str
    owner: str
    configuration_id: ID
    milestone_ids: list[ID]
    order_id: ID


class Dependency(Model):
    kind: Literal['requirement_evidence', 'validation_job']
    requirement_revision_id: ID | None = None
    job_id: ID | None = None
    state: Literal['pending_assessment', 'validation_scheduled', 'scheduled', 'evidence_available', 'review_required', 'blocked', 'completed']
    owner: str | None = None
    note: str | None = None


class ProgramSummary(Program):
    customer_name: str
    supplier_name: str
    scenario_at: UTC
    partner_freshness_limit_minutes: Positive


class Milestone(Scoped):
    owner: str | None = None
    health: str | None = None
    next_action: str | None = None
    order_id: ID
    name: str
    baseline_at: UTC
    current_forecast_at: UTC
    forecast_status: Literal['not_reassessed_for_new_request', 'conditional_on_test_and_review']
    record_version: Positive
    dependencies: list[Dependency]


class SourceRef(Model):
    resource_type: SourceType
    resource_id: ID


class SourceVersion(SourceRef):
    content_version: Positive
    availability_version: Positive | None = None


class ExpectedSources(Model):
    records: list[SourceVersion] = Field(min_length=1, max_length=200)
    evidence_set_digest: Digest


class Snapshot(SourceVersion):
    content: dict[str, JsonValue]
    content_digest: Digest


class Fact(Model):
    text: Text
    source_refs: list[SourceRef] = Field(min_length=1, max_length=20)


class Assessment(Model):
    facts: list[Fact] = Field(min_length=1, max_length=30)
    evidence_gaps: list[Text] = Field(max_length=30)
    unresolved_questions: list[Text] = Field(max_length=30)


class PlanInput(Model):
    expected_change_content_version: Positive
    target_requirement_revision_id: ID
    configuration_id: ID
    procedure_id: ID
    sample_id: ID
    slot_id: ID
    milestone_id: ID
    assessment: Assessment
    expected_source_versions: ExpectedSources
    supersedes_plan_id: ID | None = None


class DecisionInput(Model):
    model_config = ConfigDict(extra='forbid', json_schema_extra={'examples': [{'decision': 'approve', 'expected_plan_version': 1, 'expected_plan_digest': '0' * 64, 'reason': 'Simulated review: replace digest with the exact persisted plan digest.'}]})
    decision: Literal['approve', 'reject']
    expected_plan_version: Positive
    expected_plan_digest: Digest
    reason: Text


class JobInput(Model):
    model_config = ConfigDict(extra='forbid', json_schema_extra={'examples': [{'plan_id': 'plan-example', 'approval_id': 'decision-example'}]})
    plan_id: ID
    approval_id: ID


class LinkInput(JobInput):
    model_config = ConfigDict(extra='forbid', json_schema_extra={'examples': [{'plan_id': 'plan-example', 'approval_id': 'decision-example', 'job_id': 'job-example', 'expected_milestone_record_version': 1}]})
    job_id: ID
    expected_milestone_record_version: Positive


class Timing(Model):
    lab_start_at: UTC
    execution_start_at: UTC
    lab_end_at: UTC
    review_ready_at: UTC
    deadline_slack_minutes: int


class CoverageItem(Model):
    result: Result
    satisfies: bool
    mismatch_reasons: list[str]


class Coverage(Model):
    synthetic: Literal[True] = True
    change_id: ID
    coverage_satisfied: bool
    evidence_set_digest: Digest
    items: list[CoverageItem]


class Option(Model):
    slot: Slot
    lab: Lab
    sample: Sample
    unit_id: ID
    lot_id: ID
    configuration_id: ID
    procedure_id: ID
    policy_id: ID
    milestone_id: ID
    rate: Rate
    cost_cents: Cents
    currency: Literal['USD'] = 'USD'
    resource_eligible: bool
    approval_eligible: bool
    eligibility_reasons: list[str]
    approval_reasons: list[str]
    meets_deadline: bool | None
    timing: Timing | None
    expected_source_versions: ExpectedSources


class Options(Model):
    synthetic: Literal[True] = True
    change_id: ID
    items: list[Option]


class Plan(Scoped):
    customer_id: ID
    change_id: ID
    plan_version: Positive = 1
    plan_digest: Digest
    supersedes_plan_id: ID | None = None
    target_requirement_revision_id: ID
    configuration_id: ID
    procedure_id: ID
    sample_id: ID
    slot_id: ID
    milestone_id: ID
    policy_id: ID
    assessment: Assessment
    source_snapshot: list[Snapshot]
    evidence_set_digest: Digest
    cost_cents: Cents
    currency: Literal['USD']
    timing: Timing
    review_minutes: Positive
    permitted_actions: list[Action]
    coverage: Coverage
    created_by: ID


class PlanState(Model):
    id: ID
    program_id: ID
    state: Literal['draft', 'approved', 'rejected']
    record_version: Positive
    decision_id: ID | None = None


ExecutionState = Literal['not_scheduled', 'lab_scheduled_pending_planner', 'scheduled_awaiting_execution']


class PlanView(Plan):
    state: Literal['draft', 'approved', 'rejected']
    record_version: Positive
    decision_id: ID | None
    execution_state: ExecutionState
    job_id: ID | None
    implementation_link_id: ID | None


class Decision(Scoped):
    customer_id: ID
    change_id: ID
    plan_id: ID
    plan_version: Positive
    plan_digest: Digest
    decision: Literal['approve', 'reject']
    signer_identity: ID
    signer_role: Literal['engineer']
    reason: Text
    policy_id: ID
    policy_content_version: Positive
    cost_cents: Cents
    permitted_actions: list[Action]
    source_snapshot: list[Snapshot]
    configuration_id: ID
    sample_id: ID
    slot_id: ID
    milestone_id: ID


class Job(Scoped):
    customer_id: ID
    change_id: ID
    plan_id: ID
    approval_id: ID
    plan_digest: Digest
    configuration_id: ID
    procedure_id: ID
    workload_profile_id: ID
    sample_id: ID
    slot_id: ID
    lab_id: ID
    cost_cents: Cents
    timing: Timing
    review_minutes: Positive
    status: Literal['scheduled'] = 'scheduled'
    reservation_id: ID


class Reservation(Scoped):
    change_id: ID
    plan_id: ID
    job_id: ID
    slot_id: ID
    sample_id: ID
    lab_id: ID
    starts_at: UTC
    ends_at: UTC
    slot_version_before: Positive
    slot_version_after: Positive
    sample_version_before: Positive
    sample_version_after: Positive


class LabCompletion(Scoped):
    customer_id: ID
    change_id: ID
    job_id: ID
    plan_id: ID
    plan_version: Positive
    plan_digest: Digest
    result_id: ID
    result_digest: Digest
    requirement_revision_id: ID
    requirement_content_version: Positive
    procedure_id: ID
    procedure_content_version: Positive
    source_snapshot: list[Snapshot]
    started_at: UTC
    completed_at: UTC
    recorded_at: UTC
    generated_by: Literal['demo_lab_action'] = 'demo_lab_action'
    recorded_by: ID
    source_reference: str
    note: str


class JobView(Job):
    reservation: Reservation
    completion: LabCompletion | None = None


class Task(Scoped):
    change_id: ID
    plan_id: ID
    job_id: ID
    milestone_id: ID
    link_id: ID
    name: str
    status: Literal['scheduled'] = 'scheduled'
    forecast_at: UTC


class Link(Scoped):
    customer_id: ID
    change_id: ID
    plan_id: ID
    approval_id: ID
    job_id: ID
    milestone_id: ID
    task_id: ID
    forecast_at: UTC
    milestone_version_before: Positive
    milestone_version_after: Positive
    status: Literal['linked'] = 'linked'


class LinkView(Link):
    task: Task


class ChangeView(Change):
    plans: list[PlanView]
    execution_state: ExecutionState


class HistoricalJob(Scoped):
    """Imported lab execution history; never created by the booking operation."""
    customer_id: ID
    configuration_id: ID
    procedure_id: ID
    sample_id: ID
    lab_id: ID
    status: Literal['completed', 'engineering_disposition_pending']
    started_at: UTC
    completed_at: UTC
    result_ids: list[ID] = Field(min_length=1)
    recorded_by: str
    source_reference: str
    note: str


class AuditEvent(Model):
    sequence: Positive
    id: ID
    synthetic: Literal[True]
    scenario_at: UTC
    wall_clock_at: UTC
    domain: str
    actor_id: ID | None
    actor_role: str | None
    program_id: ID | None
    customer_id: ID | None
    change_id: ID | None
    action: str
    outcome: Literal['succeeded', 'denied', 'failed', 'replay']
    resource_id: ID | None
    plan_id: ID | None
    approval_id: ID | None
    job_id: ID | None
    request_id: ID
    correlation_id: str
    idempotency_hash: Digest | None
    changes: dict[str, JsonValue]


class ErrorInfo(Model):
    code: str
    message: str
    details: dict[str, JsonValue]


class ErrorResponse(Model):
    error: ErrorInfo
    correlation_id: str
