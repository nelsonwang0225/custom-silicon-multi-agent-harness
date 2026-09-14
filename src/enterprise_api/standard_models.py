"""Public standard-change contracts. Pure typed data; no source storage or agent runtime."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator
from .config import RecordID as ID

Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, hide_input_in_errors=True)

class StandardRecord(Strict):
    # SQLite scalar decoding is source-owned; HTTP action envelopes remain strict.
    model_config = ConfigDict(extra='forbid', strict=False, hide_input_in_errors=True)
    id: ID
    program_id: ID
    customer_id: ID
    owning_system: Literal['engineering', 'validation']
    content_version: int = Field(default=1, ge=1)
    updated_at: str
    synthetic: Literal[True] = True

class OperatingConditions(Strict):
    context_bins: list[int] = Field(min_length=1, max_length=10)
    concurrency: int = Field(ge=1, le=100)
    output_tokens: int = Field(ge=1, le=100000)
    total_suite_minutes: int = Field(ge=1, le=10000)

class ConfigurationBinding(Strict):
    configuration_id: ID
    content_version: int = Field(ge=1)
    product_id: ID
    product_revision: ID
    model_bundle_id: ID
    device_count: int = Field(ge=1)
    firmware: str
    runtime: str
    quantization: str
    memory_configuration: str

class StandardRequest(StandardRecord):
    request_source: Literal['engineering', 'validation', 'manufacturing', 'erp', 'planner', 'customer_intake']
    requested_by: str = Field(min_length=1, max_length=200)
    change_id: ID
    request_document_id: ID
    request_reference: str = Field(min_length=1, max_length=200)
    request_type: Literal['add_approved_profile', 'non_standard_validation', 'acceptance_change']
    baseline_requirement_revision_id: ID
    baseline_content_version: int = Field(ge=1)
    procedure_id: ID | None
    procedure_content_version: int | None = Field(ge=1)
    routing_rule_id: ID
    configuration: ConfigurationBinding | None
    workload_profile_id: ID
    workload_content_version: int = Field(ge=1)
    conditions: OperatingConditions | None
    sample_ids: list[ID] = Field(min_length=1, max_length=5)
    requested_at: str
    requested_action: str = Field(min_length=1, max_length=100)
    changes_acceptance_criteria: bool
    requests_waiver: bool
    changes_customer_commitment: bool
    quality_disposition_requested: bool
    material_exception_ids: list[ID]
    summary: str = Field(min_length=1, max_length=2000)

    @field_validator('requested_at')
    @classmethod
    def utc_time(cls, value):
        if not value.endswith('Z'):
            raise ValueError('UTC required')
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value

class StandardWork(Strict):
    work_id: ID
    description: str
    procedure_step: str
    required_inputs: list[str] = Field(min_length=1)
    completion_criteria: str
    requires_lab_authorization: Literal[True] = True

class StandardRule(StandardRecord):
    status: Literal['approved', 'retired']
    document_id: ID
    policy_version: int = Field(ge=1)
    recognized_change_type: Literal['add_approved_profile']
    permitted_action: Literal['create_standard_validation_intake']
    procedure_id: ID
    procedure_content_version: int = Field(ge=1)
    configuration: ConfigurationBinding
    workload_profile_id: ID
    workload_content_version: int = Field(ge=1)
    criteria_id: ID
    criteria_content_version: int = Field(ge=1)
    conditions: OperatingConditions
    downstream_queue_id: ID | None
    downstream_owner: str | None
    sample_count: int = Field(ge=1, le=5)
    reusable_evidence_required: bool
    remaining_work: list[StandardWork] = Field(min_length=1)
    completion_criteria: list[str] = Field(min_length=1)
    permits_lab_authorization: Literal[False] = False
    permits_scheduling: Literal[False] = False
    permits_acceptance: Literal[False] = False

class ValidationIntakeQueue(StandardRecord):
    name: str
    owner: str
    status: Literal['open', 'closed']
    permitted_action: Literal['create_standard_validation_intake'] = 'create_standard_validation_intake'

class StandardContext(Strict):
    change_id: ID
    customer_id: ID
    program_id: ID
    scenario_at: str
    request: StandardRequest
    rule: StandardRule | None
    queue: ValidationIntakeQueue | None
    change: dict[str, JsonValue]
    program: dict[str, JsonValue]
    baseline: dict[str, JsonValue] | None
    configuration: dict[str, JsonValue] | None
    workload: dict[str, JsonValue] | None
    criteria: dict[str, JsonValue] | None
    procedure: dict[str, JsonValue] | None
    procedure_document: dict[str, JsonValue] | None
    policy_document: dict[str, JsonValue] | None
    request_document: dict[str, JsonValue]
    milestone: dict[str, JsonValue] | None
    evidence: list[dict[str, JsonValue]]
    samples: list[dict[str, JsonValue]]
    context_digest: Digest

class RuleCheck(Strict):
    code: str
    passed: bool
    reason: str

class TouchlessEligibility(Strict):
    touchless_eligible: bool
    policy_path: Literal['standard_touchless_handoff', 'review_required']
    rule_id: ID | None
    rule_version: int | None
    context_digest: Digest
    checks: list[RuleCheck]
    reusable_evidence_ids: list[ID]
    remaining_work: list[StandardWork]
    requires_human_approval_for_handoff: bool
    downstream_lab_authorization: Literal['pending'] = 'pending'
    physical_testing: Literal['not_started'] = 'not_started'
    customer_acceptance: Literal['pending'] = 'pending'

class EvidenceReference(Strict):
    result_id: ID
    content_version: int = Field(ge=1)
    result_digest: Digest
    reuse: Literal['historical_profile_evidence'] = 'historical_profile_evidence'

class HandoffPackage(Strict):
    package_id: ID
    package_version: Literal[1] = 1
    customer_id: ID
    program_id: ID
    change_id: ID
    request_id: ID
    request_content_version: int
    customer_request_reference: str
    baseline_requirement_revision_id: ID
    baseline_content_version: int
    procedure_id: ID
    procedure_content_version: int
    configuration: ConfigurationBinding
    workload_profile_id: ID
    conditions: OperatingConditions
    evidence_references: list[EvidenceReference]
    reusable_evidence_ids: list[ID]
    remaining_work: list[StandardWork]
    sample_ids: list[ID]
    requested_at: str
    downstream_queue_id: ID
    downstream_owner: str
    completion_criteria: list[str]
    routing_rule_id: ID
    routing_rule_version: int
    context_digest: Digest
    source_record_digests: dict[str, Digest]
    workflow_id: Literal['requirement_change_analysis'] = 'requirement_change_analysis'
    workflow_run_id: ID
    workflow_case_id: ID
    authority: Literal['bounded_pre_authorized_handoff'] = 'bounded_pre_authorized_handoff'
    lab_authorization: Literal['pending'] = 'pending'
    physical_testing: Literal['not_started'] = 'not_started'
    customer_acceptance: Literal['pending'] = 'pending'

class StandardIntakeInput(Strict):
    package: HandoffPackage
    expected_context_digest: Digest

class ValidationIntake(StandardRecord):
    change_id: ID
    request_content_version: int
    record_version: Literal[1] = 1
    package: HandoffPackage
    package_digest: Digest
    status: Literal['received'] = 'received'
    package_status: Literal['complete'] = 'complete'
    downstream_queue_id: ID
    downstream_owner: str
    received_at: str
    received_by: ID
    lab_authorization: Literal['pending'] = 'pending'
    physical_testing: Literal['not_started'] = 'not_started'
    customer_acceptance: Literal['pending'] = 'pending'

class IntakeList(Strict):
    program_id: ID
    customer_id: ID
    change_id: ID
    items: list[ValidationIntake]
