"""Independent read DTOs based on the public OpenAPI contract, not backend imports.

Validate important record/reference structures while retaining every additional
JSON field. The client returns the original JSON, without injecting defaults,
coercing values, recomputing eligibility, or interpreting evidence.
"""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from .config import RecordID

JSONRecord = dict[str, JsonValue]
T = TypeVar("T")


class ReadModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True, hide_input_in_errors=True)
    __pydantic_extra__: dict[str, JsonValue] = Field(init=False)


class Items(ReadModel, Generic[T]):
    items: list[T]


class Record(ReadModel):
    id: RecordID
    program_id: RecordID
    owning_system: Literal["engineering", "validation", "manufacturing", "erp", "planner"]
    synthetic: Literal[True]
    content_version: int = Field(gt=0)
    updated_at: str


class Configuration(Record):
    product_id: RecordID
    product_revision: str
    model_bundle_id: RecordID
    firmware: str
    runtime: str
    memory_configuration: str
    quantization: str
    device_count: int = Field(gt=0)


class RequirementRevision(Record):
    customer_id: RecordID
    requirement_id: RecordID
    revision: int = Field(gt=0)
    status: Literal["approved", "requested"]
    configuration_id: RecordID
    workload_profile_id: RecordID
    acceptance_limits_ref: RecordID


class WorkloadProfile(Record):
    model_bundle_id: RecordID
    context_bins: list[int]
    concurrency: int = Field(gt=0)
    output_tokens: int = Field(gt=0)
    total_suite_minutes: int = Field(gt=0)


class Procedure(Record):
    status: Literal["approved", "retired"]
    document_id: RecordID
    supported_configuration_ids: list[RecordID]
    workload_profile_id: RecordID
    acceptance_limits_ref: RecordID
    setup_minutes: int
    suite_minutes: int
    per_bin_minutes: int
    review_minutes: int


class Policy(Record):
    status: Literal["approved", "retired"]
    document_id: RecordID
    permitted_procedure_ids: list[RecordID]
    approver_role: Literal["engineer"]
    max_incremental_cost_cents: int = Field(ge=0)
    currency: Literal["USD"]
    permitted_actions: list[str]


class AcceptanceCriteria(Record):
    status: Literal["approved", "retired"]
    scope: str
    writable: Literal[False]


class DocumentMetadata(Record):
    customer_id: RecordID
    document_type: str
    document_version: str
    status: str
    content_hash: str


class Document(DocumentMetadata):
    content: str


class ValidationResult(Record):
    customer_id: RecordID
    configuration_id: RecordID
    workload_profile_id: RecordID
    acceptance_limits_ref: RecordID
    sample_id: RecordID
    product_revision: str
    model_bundle_id: RecordID
    status: Literal["completed", "running", "failed"]
    criteria_passed: bool
    covered_context_bins: list[int]
    actual_suite_minutes: int = Field(ge=0)
    observed_minutes_by_context_bin: dict[str, int]
    completed_at: str
    configuration_snapshot: Configuration
    workload_snapshot: WorkloadProfile
    criteria_snapshot: AcceptanceCriteria


class CoverageItem(ReadModel):
    result: ValidationResult
    satisfies: bool
    mismatch_reasons: list[str]


class Coverage(ReadModel):
    synthetic: Literal[True]
    change_id: RecordID
    coverage_satisfied: bool
    evidence_set_digest: str
    items: list[CoverageItem]


class Sample(Record):
    unit_id: RecordID
    configuration_id: RecordID
    availability: Literal["available", "reserved", "unavailable"]
    availability_version: int = Field(gt=0)
    campus: str


class Slot(Record):
    lab_id: RecordID
    rate_id: RecordID
    starts_at: str
    ends_at: str
    availability: Literal["available", "reserved", "unavailable"]
    availability_version: int = Field(gt=0)


class CostRate(Record):
    currency: Literal["USD"]
    incremental_cost_cents: int = Field(ge=0)
    status: Literal["approved", "retired"]
    effective_from: str
    effective_to: str


class Timing(ReadModel):
    lab_start_at: str
    execution_start_at: str
    lab_end_at: str
    review_ready_at: str
    deadline_slack_minutes: int


class ValidationOption(ReadModel):
    slot: Slot
    lab: Record
    sample: Sample
    unit_id: RecordID
    lot_id: RecordID
    configuration_id: RecordID
    procedure_id: RecordID
    policy_id: RecordID
    milestone_id: RecordID
    rate: CostRate
    cost_cents: int = Field(ge=0)
    currency: Literal["USD"]
    resource_eligible: bool
    approval_eligible: bool
    meets_deadline: bool | None
    eligibility_reasons: list[str]
    approval_reasons: list[str]
    timing: Timing | None
    expected_source_versions: JSONRecord


class ValidationOptions(ReadModel):
    synthetic: Literal[True]
    change_id: RecordID
    items: list[ValidationOption]


class Plan(Record):
    customer_id: RecordID
    change_id: RecordID
    plan_version: int = Field(gt=0)
    plan_digest: str
    state: Literal["draft", "approved", "rejected"]
    record_version: int = Field(gt=0)
    decision_id: RecordID | None
    job_id: RecordID | None
    implementation_link_id: RecordID | None
    source_snapshot: list[JSONRecord]
    assessment: JSONRecord
    coverage: Coverage
    timing: Timing
    cost_cents: int = Field(ge=0)
    currency: Literal["USD"]
    execution_state: str


class ChangeRequest(Record):
    customer_id: RecordID
    baseline_requirement_revision_id: RecordID
    proposed_requirement_revision_id: RecordID
    configuration_id: RecordID
    milestone_id: RecordID
    order_id: RecordID
    request_document_id: RecordID
    record_version: int = Field(gt=0)
    title: str
    workflow_state: str
    current_plan_id: RecordID | None


class ChangeRequestView(ChangeRequest):
    plans: list[Plan]
    execution_state: str


class Decision(Record):
    customer_id: RecordID
    change_id: RecordID
    plan_id: RecordID
    plan_version: int = Field(gt=0)
    plan_digest: str
    decision: Literal["approve", "reject"]
    signer_identity: RecordID
    signer_role: Literal["engineer"]
    source_snapshot: list[JSONRecord]
    permitted_actions: list[str]


class Reservation(Record):
    change_id: RecordID
    plan_id: RecordID
    job_id: RecordID
    slot_id: RecordID
    sample_id: RecordID
    lab_id: RecordID
    starts_at: str
    ends_at: str


class ValidationJob(Record):
    customer_id: RecordID
    change_id: RecordID
    plan_id: RecordID
    approval_id: RecordID
    reservation_id: RecordID
    status: Literal["scheduled"]
    timing: Timing
    reservation: Reservation


class HistoricalValidationJob(Record):
    customer_id: RecordID
    status: Literal["completed", "engineering_disposition_pending"]
    result_ids: list[RecordID]
    source_reference: str
    recorded_by: str
    started_at: str
    completed_at: str


class ManufacturingLot(Record):
    product_id: RecordID
    product_revision: str
    restrictions: list[str]
    hold_details: list[JSONRecord]


class ManufacturingUnit(ManufacturingLot):
    source_lot_id: RecordID


class CustomerOrder(Record):
    customer_id: RecordID
    product_id: RecordID
    product_revision: str
    quantity: int = Field(gt=0)
    quantity_unit: Literal["accelerator_units"]
    planning_unit_value_cents: int | None = Field(default=None, ge=0)
    planning_value_basis: str | None = None
    committed_delivery_at: str
    status: str


class Program(Record):
    customer_id: RecordID
    supplier_id: RecordID
    configuration_id: RecordID
    milestone_ids: list[RecordID]
    order_id: RecordID


class Dependency(ReadModel):
    kind: Literal["requirement_evidence", "validation_job"]
    state: str
    requirement_revision_id: RecordID | None
    job_id: RecordID | None


class Milestone(Record):
    order_id: RecordID
    baseline_at: str
    current_forecast_at: str
    forecast_status: str
    record_version: int = Field(gt=0)
    dependencies: list[Dependency]


class ImplementationLink(Record):
    customer_id: RecordID
    change_id: RecordID
    plan_id: RecordID
    approval_id: RecordID
    job_id: RecordID
    milestone_id: RecordID
    task_id: RecordID
    forecast_at: str
    status: Literal["linked"]
    task: Record
