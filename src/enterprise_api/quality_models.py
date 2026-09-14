"""Public source contracts for bounded quality investigation and recovery planning."""
from typing import Literal
from pydantic import Field, model_validator, ConfigDict
from .standard_models import Strict, Digest
from .config import RecordID as ID

class QualityRecord(Strict):
    model_config = ConfigDict(extra='forbid', strict=False)
    id: ID
    program_id: ID
    customer_id: ID
    owning_system: Literal['manufacturing','engineering','validation','planner','erp']
    content_version: int = Field(default=1, ge=1)
    synthetic: Literal[True] = True
    updated_at: str

class QualityException(QualityRecord):
    lot_id: ID
    configuration_id: ID
    milestone_id: ID
    order_id: ID
    observation_id: ID
    baseline_id: ID
    investigation_procedure_id: ID
    evidence_ids: list[ID]
    material_ids: list[ID]
    request_source: Literal['manufacturing'] = 'manufacturing'
    requested_by: str
    received_at: str
    summary: str
    status: Literal['open','closed'] = 'open'
    exception_type: str | None = None
    requested_actions: list[str] = Field(default_factory=list)

class QualityMaterial(QualityRecord):
    lot_id: ID
    configuration_id: ID
    disposition: Literal['hold','released','rejected']
    physical_quantity: int = Field(ge=0)
    first_pass_pass_quantity: int = Field(ge=0)
    released_quantity: int = Field(ge=0)
    held_quantity: int = Field(ge=0)
    allocated_quantity: int = Field(ge=0)
    eligible_unallocated_quantity: int = Field(ge=0)
    expected_milestone_id: ID | None
    allocation_order_id: ID | None

    @model_validator(mode='after')
    def quantities(self):
        if (self.first_pass_pass_quantity > self.physical_quantity or self.released_quantity+self.held_quantity > self.physical_quantity
            or self.allocated_quantity > self.released_quantity or self.eligible_unallocated_quantity > self.released_quantity-self.allocated_quantity
            or self.disposition!='released' and (self.released_quantity or self.eligible_unallocated_quantity)):
            raise ValueError('Inconsistent source material quantities')
        return self

class QualityObservation(QualityRecord):
    lot_id: ID
    configuration_id: ID
    configuration_content_version: int = Field(ge=1)
    product_revision: str
    test_stage: str
    test_program_version: str | None
    conditions_id: str | None
    population: str | None
    equipment_family: str | None
    sites: list[str]
    tested_quantity: int = Field(gt=0)
    passed_quantity: int = Field(ge=0)
    failed_quantity: int = Field(ge=0)
    site_counts: dict[str,list[int]]
    root_cause: str | None = None

    @model_validator(mode='after')
    def counts(self):
        if self.passed_quantity+self.failed_quantity!=self.tested_quantity:
            raise ValueError('Test denominator mismatch')
        if (set(self.site_counts)!=set(self.sites) or any(len(v)!=2 or min(v)<0 or v[1]>v[0] for v in self.site_counts.values())
            or sum(v[0] for v in self.site_counts.values())!=self.tested_quantity
            or sum(v[1] for v in self.site_counts.values())!=self.passed_quantity):
            raise ValueError('Site counts mismatch')
        return self

class QualityBaseline(QualityRecord):
    configuration_id: ID
    configuration_content_version: int = Field(ge=1)
    product_revision: str
    test_stage: str
    test_program_version: str | None
    conditions_id: str | None
    population: str | None
    equipment_family: str | None
    sites: list[str]
    tested_quantity: int = Field(gt=0)
    passed_quantity: int = Field(ge=0)
    status: Literal['approved','retired']

class StandardQualityPolicy(Strict):
    route: Literal['standard_quality_investigation_handoff']
    exception_type: Literal['final_test_anomaly']
    exception_id: ID
    lot_id: ID
    queue_id: ID
    queue_status: Literal['active','inactive']
    owner: str
    permitted_actions: list[str]
    approved_tasks: list[str]

class QualityProcedure(QualityRecord):
    configuration_id: ID
    status: Literal['approved','retired']
    queue_id: ID
    owner: str
    tasks: list[str] = Field(min_length=1)
    evidence_ids: list[ID]
    recovery_owner: str
    recovery_role: Literal['program_owner'] = 'program_owner'
    permitted_action: Literal['record_recovery_task'] = 'record_recovery_task'
    investigation_hours: int = Field(gt=0)
    standard_policy: StandardQualityPolicy | None = None

class QualityContext(Strict):
    exception_id: ID
    program_id: ID
    customer_id: ID
    exception: QualityException
    lot: dict
    observation: QualityObservation
    baseline: QualityBaseline | None
    material: list[QualityMaterial]
    configuration: dict
    procedure: QualityProcedure | None
    evidence: list[dict]
    milestone: dict
    order: dict
    context_digest: Digest
    analysis: "QualityAnalysis | None" = None
    conflicting_exception_ids: list[ID] = Field(default_factory=list)
    investigation_destination: QualityProcedure | None = None

class QualityAnalysis(Strict):
    comparable: Literal['true','false','unknown']
    comparison_reasons: list[str]
    observed_rate_bps: int
    baseline_rate_bps: int | None
    confirmed_degradation: bool
    affected_physical_quantity: int
    first_pass_pass_quantity: int
    affected_eligible_quantity: int
    held_quantity: int
    eligible_quantity: int
    requested_quantity: int
    gap_quantity: int
    planning_unit_value_cents: int | None = Field(default=None, ge=0)
    held_value_exposure_cents: int | None = Field(default=None, ge=0)
    baseline_expected_pass_quantity: int | None = Field(default=None, ge=0)
    first_pass_shortfall_quantity: int | None = Field(default=None, ge=0)
    first_pass_shortfall_value_cents: int | None = Field(default=None, ge=0)
    gap_value_exposure_cents: int | None = Field(default=None, ge=0)
    planning_value_basis: str | None = None
    failed_by_site: dict[str,int]
    root_cause: str | None
    evidence_status: Literal['available','missing']
    investigation_allowed: bool
    options: list[dict]
    protected_decisions: list[str]

class QualityIntent(Strict):
    exception_id: ID
    expected_context_digest: Digest
    workflow_run_id: ID
    workflow_case_id: ID

class QualityInvestigation(QualityRecord):
    exception_id: ID
    lot_id: ID
    observation_id: ID
    test_program_version: str | None
    context_digest: Digest
    queue_id: ID
    owner: str
    tasks: list[str]
    evidence_ids: list[ID]
    status: Literal['routed'] = 'routed'
    workflow_run_id: ID
    workflow_case_id: ID

class RecoveryWorkstream(Strict):
    id: Literal['containment','site_investigation','controlled_recovery','supply_protection']
    source_system: Literal['manufacturing','engineering','planner']
    owner: str
    objective: str
    actions: list[str] = Field(min_length=1)
    completion_criteria: str
    status: Literal['planned'] = 'planned'

class RecoveryPlan(QualityRecord):
    exception_id: ID
    lot_id: ID
    milestone_id: ID
    order_id: ID
    investigation_id: ID
    plan_version: int = Field(ge=1)
    plan_digest: str
    context_digest: Digest
    analysis: QualityAnalysis
    required_role: Literal['program_owner'] = 'program_owner'
    permitted_action: Literal['record_recovery_task'] = 'record_recovery_task'
    recovery_owner: str
    workflow_run_id: ID
    workflow_case_id: ID
    workstreams: list[RecoveryWorkstream] = Field(default_factory=list,max_length=4)

class RecoveryReviewInput(Strict):
    plan_id: ID
    expected_plan_version: int = Field(ge=1)
    expected_plan_digest: Digest
    decision: Literal['approve','reject']
    comment: str = Field(max_length=1500)
    submission_digest: Digest | None = None
    recommendation: str | None = Field(default=None,max_length=3000)
    business_context: str | None = Field(default=None,max_length=3000)

class RecoveryDecision(QualityRecord):
    exception_id: ID
    plan_id: ID
    plan_version: int
    plan_digest: Digest
    context_digest: Digest
    decision: Literal['approve','reject']
    signer_identity: ID
    signer_role: Literal['program_owner']
    comment: str
    submission_digest: Digest | None = None
    recommendation: str | None = None
    business_context: str | None = None

class RecoveryExecuteInput(Strict):
    plan_id: ID
    decision_id: ID
    expected_plan_digest: Digest
    expected_submission_digest: Digest | None = None

class RecoveryTask(QualityRecord):
    exception_id: ID
    lot_id: ID
    milestone_id: ID
    plan_id: ID
    decision_id: ID
    plan_digest: Digest
    owner: str
    status: Literal['recovery_plan_recorded'] = 'recovery_plan_recorded'
    eligible_quantity: int
    gap_quantity: int
    submission_digest: Digest | None = None
    approved_recommendation: str | None = None
    business_context: str | None = None
    workstreams: list[RecoveryWorkstream] = Field(default_factory=list,max_length=4)
    allocation_changed: Literal[False] = False
    commitment_changed: Literal[False] = False
    lot_released: Literal[False] = False

class QualityRecords(Strict):
    exception_id: ID
    program_id: ID
    customer_id: ID
    investigations: list[QualityInvestigation]
    plans: list[RecoveryPlan]
    decisions: list[RecoveryDecision]
    tasks: list[RecoveryTask]

QualityContext.model_rebuild()
