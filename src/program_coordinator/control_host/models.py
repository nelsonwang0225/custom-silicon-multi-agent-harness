"""Browser contracts contain references, never source write arguments or actors."""
from typing import Literal
from pydantic import Field, model_validator
from ..models import Model, ID, SourceReference, FinalDecisionPackage
from ..application.models import CaseRecord, ActivityRecord, Trigger
from ..application.automations import AutomationView
from ..application.workflow_catalog import CatalogWorkflow
from ..application.contracts import Proposal, VerificationRecord
from ..application.execution_models import ProposalRef, HumanReview, ExecutionRecord, ExecutionAttempt, OperatorEscalation

class StartRequest(Model):
    invocation_id: str = Field(pattern=r"^ui_[A-Za-z0-9_-]{1,90}$")
    workflow_id: Literal['requirement_change_analysis', 'yield_exception_recovery', 'delivery_readiness'] = 'requirement_change_analysis'
    definition_version: Literal[1] = 1
    operation: Literal['analyze'] = 'analyze'
    customer_id: Literal['CUST-FML01'] = 'CUST-FML01'
    program_id: Literal['PRG-A17'] = 'PRG-A17'
    change_id: Literal['CR-017', 'CR-019', 'QE-004', 'DR-009', 'QE-011'] = 'CR-017'

    @model_validator(mode='after')
    def workflow_case_scope(self):
        if (self.change_id in {'QE-004','QE-011'}) != (self.workflow_id == 'yield_exception_recovery'):
            raise ValueError('Quality workflow requires the quality case')
        if (self.change_id == 'DR-009') != (self.workflow_id == 'delivery_readiness'):
            raise ValueError('Delivery workflow requires the delivery case')
        return self

class PrepareRequest(Model):
    run_id: ID
    supersedes: ProposalRef | None = None

class EscalationRequest(Model):
    submission_id: str = Field(pattern=r"^ui_[A-Za-z0-9_-]{1,90}$")
    run_id: ID
    subject: str = Field(min_length=3, max_length=180)
    recommendation: str = Field(min_length=3, max_length=3000)
    business_context: str = Field(min_length=3, max_length=3000)
    operator_notes: str = Field(default='', max_length=2000)

class EvidenceEscalationRequest(EscalationRequest):
    expected_evidence_digest: str = Field(pattern=r'^[a-f0-9]{64}$')

class ExactRequest(Model):
    reference: ProposalRef

class ReviewRequest(ExactRequest):
    decision: Literal['approve', 'reject']
    comment: str = Field(default='', max_length=1500)

class SpecialistView(Model):
    invocation_id: ID
    parent_invocation_id: ID | None = None
    caller: str = "coordinator"
    specialist: str
    status: str
    task: str
    result_kind: str = "domain_assessment"
    depth: int = 1
    started_ms: float = 0
    ended_ms: float | None = None
    summary: str | None = None
    source_references: list[SourceReference] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    error_code: str | None = None

class RunView(Model):
    change_id: ID = "CR-017"
    policy_route: str = "material_change_human_review"
    authority: str = "Separate exact human approval for governed execution"
    customer_id: ID
    program_id: ID
    actor_id: ID
    actor_source: str
    trigger: Trigger
    trace_id: ID | None = None
    business_outcome: str = "Outcome pending"
    run_id: ID
    case_id: ID
    workflow_id: ID
    definition_version: int
    invocation_id: ID
    status: str
    execution_mode: str
    started_at: str
    completed_at: str | None
    error_code: str | None
    recommendation: FinalDecisionPackage | None
    specialists: list[SpecialistView] = Field(default_factory=list)
    findings_state: Literal['recorded', 'not_recorded', 'unavailable']

class ProposalView(Model):
    proposal: Proposal
    execution: ExecutionRecord
    review: HumanReview | None
    attempts: list[ExecutionAttempt]
    verification: list[VerificationRecord]
    current_check: str
    effective_status: str
    replacement: ProposalRef | None = None

from .downstream import DownstreamView
from .integration_models import CaseSummary, DecisionSummary, CaseDependency

from enterprise_api.standard_models import StandardContext, TouchlessEligibility
from ..application.standard_handoff_models import StandardHandoff

class StandardCaseView(Model):
    change_id: Literal['CR-019'] = 'CR-019'
    source_available: bool
    context: StandardContext | None
    eligibility: TouchlessEligibility | None
    status: str
    runs: list[RunView]
    handoffs: list[StandardHandoff]
    activity: list[ActivityRecord]

from enterprise_api.quality_models import QualityContext, QualityRecords
from ..application.quality_recovery_models import QualityProgress

class QualityCaseView(Model):
    change_id: str = 'QE-004'
    source_available: bool
    context: QualityContext | None
    records: QualityRecords | None
    status: str
    runs: list[RunView] = Field(default_factory=list)
    progress: list[QualityProgress] = Field(default_factory=list)
    activity: list[ActivityRecord] = Field(default_factory=list)



from enterprise_api.delivery_models import DeliveryContext, DeliveryRecords
from ..application.delivery_models import DeliveryProgress

class DeliveryCaseView(Model):
    change_id: str = 'DR-009'
    source_available: bool
    context: DeliveryContext | None
    records: DeliveryRecords | None
    status: str
    runs: list[RunView] = Field(default_factory=list)
    progress: list[DeliveryProgress] = Field(default_factory=list)
    activity: list[ActivityRecord] = Field(default_factory=list)

class CaseView(Model):
    case_runtime_modes: dict[str, Literal['live_model', 'deterministic_test']] = Field(default_factory=dict)
    # Read cadence hint only; never a business state or an invocation instruction.
    pending_source_event: bool = False
    case_summaries: list[CaseSummary] = Field(default_factory=list)
    decision_summaries: list[DecisionSummary] = Field(default_factory=list)
    dependencies: list[CaseDependency] = Field(default_factory=list)
    delivery: DeliveryCaseView | None = None
    quality: QualityCaseView | None = None
    autonomous_quality: QualityCaseView | None = None
    standard: StandardCaseView | None = None
    customer_id: Literal['CUST-FML01'] = 'CUST-FML01'
    program_id: Literal['PRG-A17'] = 'PRG-A17'
    change_id: Literal['CR-017'] = 'CR-017'
    mode: Literal['live_model', 'deterministic_test']
    source_url: str
    fetched_at: str
    source_available: bool
    cases: list[CaseRecord]
    runs: list[RunView]
    proposals: list[ProposalView]
    operator_escalations: list[OperatorEscalation] = Field(default_factory=list)
    activity: list[ActivityRecord]
    downstream: DownstreamView | None = None
    workflows: list[CatalogWorkflow] = Field(default_factory=list)
    automations: list[AutomationView] = Field(default_factory=list)

class StartResponse(Model):
    run_id: ID
    status: str
    replayed: bool
