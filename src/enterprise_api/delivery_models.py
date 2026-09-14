"""Source-owned delivery release requests and exact commercial commitment contracts."""
from typing import Literal
from pydantic import Field, field_validator
from .quality_models import QualityRecord, QualityMaterial
from .standard_models import Strict, Digest
from .config import RecordID as ID


class DeliveryRecord(QualityRecord):
    pass


class DeliveryRequest(DeliveryRecord):
    order_id: ID
    line_id: ID
    milestone_id: ID
    configuration_id: ID
    requirement_revision_id: ID
    clearance_id: ID
    technical_change_id: ID | None
    logistics_id: ID
    material_ids: list[ID] = Field(min_length=1)
    allocation_ids: list[ID]
    future_supply_ids: list[ID]
    quantity: int | None = Field(ge=1)
    requested_at: str | None
    date_semantics: Literal['arrival', 'ship']
    destination: str | None
    request_source: Literal['erp']
    requested_by: str = Field(min_length=1)
    received_at: str
    summary: str
    commitment_owner: str
    customer_agreement: Literal['pending', 'accepted', 'rejected'] = 'pending'

    @field_validator('requested_at')
    @classmethod
    def utc_date(cls, value):
        if value is not None:
            from datetime import datetime
            if not value.endswith('Z') or datetime.fromisoformat(value).utcoffset().total_seconds() != 0:
                raise ValueError('Explicit UTC date required')
        return value


class DeliveryState(DeliveryRecord):
    delivery_id: ID
    record_version: int = Field(default=1, ge=1)
    current_commitment_id: ID | None = None


class DeliveryAllocation(DeliveryRecord):
    material_id: ID
    order_id: ID
    quantity: int = Field(gt=0)
    release_reference: str
    status: Literal['allocated'] = 'allocated'


class DeliveryClearance(DeliveryRecord):
    configuration_id: ID
    requirement_revision_id: ID
    evidence_ids: list[ID]
    review_digest: Digest
    status: Literal['approved', 'pending', 'rejected']
    signer_role: Literal['engineer']
    signer_identity: ID
    acceptance_blockers: list[str]
    customer_technical_acceptance: Literal['pending', 'accepted', 'not_required']


class DeliveryLogistics(DeliveryRecord):
    milestone_id: ID
    destination: str
    state: Literal['confirmed', 'conditional', 'unknown']
    material_ready_at: str | None
    preparation_minutes: int | None = Field(ge=0)
    loading_minutes: int | None = Field(ge=0)
    transit_minutes: int | None = Field(ge=0)
    owner: str
    calendar: Literal['elapsed_UTC'] = 'elapsed_UTC'


class FutureSupply(DeliveryRecord):
    configuration_id: ID
    quantity: int = Field(gt=0)
    expected_at: str | None
    status: Literal['expected', 'conditional', 'unconfirmed']
    release_prerequisites: list[str]
    quality_complete: bool
    validation_complete: bool


class DeliveryOption(Strict):
    id: Literal['partial_commitment', 'allocation_review', 'future_supply']
    quantity: int
    remaining_gap: int | None
    proposed_at: str | None
    date_semantics: Literal['arrival', 'ship', 'expected_material']
    executable: bool
    owner: str
    required_role: str
    prerequisites: list[str]
    effect: str
    affected_obligations: list[ID]
    cost_cents: int | None = None


class DeliveryAnalysis(Strict):
    technical_readiness: Literal['READY', 'BLOCKED', 'CONDITIONAL', 'UNKNOWN']
    technical_reasons: list[str]
    physical_total: int
    held_quantity: int
    allocated_quantity: int
    configuration_mismatch_quantity: int
    released_unallocated_quantity: int
    other_unavailable_quantity: int
    eligible_quantity: int
    requested_quantity: int | None
    gap_quantity: int | None
    customer_ready_quantity: int
    future_expected_quantity: int
    inventory_consistent: bool
    inventory_reasons: list[str]
    earliest_ship_at: str | None
    earliest_arrival_at: str | None
    proposed_at: str | None
    timing_status: Literal['supported', 'conditional', 'unknown', 'late']
    timing_reasons: list[str]
    full_request_supportable: bool
    proposal_allowed: bool
    blockers: list[str]
    options: list[DeliveryOption]


class DeliveryContext(Strict):
    delivery_id: ID
    customer_id: ID
    program_id: ID
    request: DeliveryRequest
    order: dict
    milestone: dict
    configuration: dict
    requirement: dict
    workload: dict
    criteria: dict
    evidence: list[dict]
    clearance: DeliveryClearance | None
    technical_dependency: dict | None
    material: list[QualityMaterial]
    lots: list[dict]
    allocations: list[DeliveryAllocation]
    allocation_orders: list[dict]
    future_supply: list[FutureSupply]
    logistics: DeliveryLogistics | None
    state: DeliveryState
    commitment: 'DeliveryCommitment | None'
    input_digest: Digest
    context_digest: Digest
    analysis: DeliveryAnalysis | None = None


class DeliveryPrepareInput(Strict):
    delivery_id: ID
    expected_context_digest: Digest
    workflow_run_id: ID
    workflow_case_id: ID
    selected_option: Literal['partial_commitment'] = 'partial_commitment'


class CommitmentPlan(DeliveryRecord):
    delivery_id: ID
    order_id: ID
    line_id: ID
    milestone_id: ID
    plan_version: int = Field(ge=1)
    plan_digest: str
    context_digest: Digest
    input_digest: Digest
    expected_state_version: int = Field(ge=1)
    prior_commitment_id: ID | None
    selected_option: Literal['partial_commitment']
    quantity: int = Field(gt=0)
    committed_at: str
    date_semantics: Literal['arrival', 'ship']
    destination: str
    analysis: DeliveryAnalysis
    required_role: Literal['program_owner'] = 'program_owner'
    owner: str
    permitted_actions: list[Literal['record_delivery_commitment', 'link_delivery_plan']]
    assumptions: list[str]
    allocation_changed: Literal[False] = False
    workflow_run_id: ID
    workflow_case_id: ID


class CommitmentDecision(DeliveryRecord):
    delivery_id: ID
    plan_id: ID
    plan_version: int
    plan_digest: Digest
    context_digest: Digest
    signer_role: Literal['program_owner']
    signer_identity: ID
    decision: Literal['approve', 'reject']
    comment: str


class DeliveryCommitment(DeliveryRecord):
    delivery_id: ID
    order_id: ID
    line_id: ID
    plan_id: ID
    decision_id: ID
    plan_digest: Digest
    quantity: int = Field(gt=0)
    committed_at: str
    date_semantics: Literal['arrival', 'ship']
    destination: str
    remaining_uncommitted_quantity: int = Field(ge=0)
    status: Literal['authorized_commitment'] = 'authorized_commitment'
    allocation_changed: Literal[False] = False
    customer_agreement: Literal['pending', 'accepted', 'rejected']
    delivered_quantity: Literal[0] = 0
    supersedes_commitment_id: ID | None


class DeliveryLink(DeliveryRecord):
    delivery_id: ID
    order_id: ID
    milestone_id: ID
    plan_id: ID
    decision_id: ID
    commitment_id: ID
    plan_digest: Digest
    quantity: int
    committed_at: str
    date_semantics: Literal['arrival', 'ship']
    remaining_uncommitted_quantity: int
    owner: str
    status: Literal['commitment_linked_pending_fulfillment'] = 'commitment_linked_pending_fulfillment'
    customer_agreement: Literal['pending', 'accepted', 'rejected']
    shipment_completed: Literal[False] = False


class DeliveryExecuteInput(Strict):
    plan_id: ID
    decision_id: ID
    expected_plan_digest: Digest


class DeliveryRecords(Strict):
    delivery_id: ID
    program_id: ID
    customer_id: ID
    plans: list[CommitmentPlan]
    decisions: list[CommitmentDecision]
    commitments: list[DeliveryCommitment]
    links: list[DeliveryLink]

DeliveryContext.model_rebuild()
