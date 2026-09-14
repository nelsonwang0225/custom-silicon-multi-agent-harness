"""Product descriptions over the registry. These records never install an executor."""
from typing import Literal
from pydantic import Field
from ..models import ID, Model
from .registry import list_workflows, dispatch_error

Authority = Literal['read_only', 'proposal_only', 'bounded_execution']

class CatalogWorkflow(Model):
    workflow_id: ID
    invocation_workflow_id: ID = "requirement_change_analysis"
    connected_route: str | None = None
    name: str
    purpose: str
    mode: Literal['Connected', 'Simulated', 'Preview']
    registry_entry: bool
    definition_version: int = 1
    manual_available: bool = False
    authority: Authority = 'read_only'
    configuration_authorities: list[Authority] = Field(default_factory=lambda: ['read_only'])
    specialists: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    programs: list[str] = Field(default_factory=lambda: ['PRG-A17'])
    cases: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    approvals: str
    limits: str
    story: str | None = None
    latest_run_id: ID | None = None
    source_event_scope: str | None = None

_SYSTEMS = ['Engineering Hub', 'Validation Lab', 'Manufacturing Portal', 'Commercial ERP', 'Program Planner']
_EXTRAS = (
    ('standard_change', 'Standard Change / Touchless Handoff', 'Prepare a standard downstream handoff when scope and evidence match.', '1A · Standard change'),
    ('specification_drift', 'Specification Drift Detection', 'Compare changing specifications with approved program scope.', None),
    ('tapeout_readiness', 'Tapeout Readiness Review', 'Bring evidence and unresolved gates into a readiness review.', None),
    ('platform_ip_errata', 'Platform IP / Errata Propagation', 'Identify programs affected by shared IP or errata changes.', None),
    ('supply_manufacturing', 'Supply & Manufacturing Signals', 'Relate supply exceptions to program constraints.', None),
    ('post_silicon', 'Post-Silicon Bring-Up / Errata', 'Connect bring-up observations, applicability and follow-up.', None),
    ('customer_commitment', 'Customer Commitment Review', 'Review readiness against recorded customer commitments.', None),
    ('portfolio_risk', 'Portfolio Risk / Early Warning', 'Review risk signals and dependencies across program scope.', None),
    ('scenario_capacity', 'Scenario / Capacity Planning', 'Compare illustrative resource and timing scenarios.', None),
    ('next_generation_requirements', 'Next-Generation Requirements Harvest', 'Organize future requirements for authorized human review.', None),
)

def workflow_catalog():
    result = []
    for definition in list_workflows():
        connected = dispatch_error(definition.workflow_id, definition.definition_version) is None
        item = CatalogWorkflow(workflow_id=definition.workflow_id, name=definition.display_name,
            purpose=definition.description, mode='Connected' if connected else 'Preview', registry_entry=True,
            definition_version=definition.definition_version, manual_available=connected,
            specialists=list(definition.participating_specialists), source_systems=_SYSTEMS,
            approvals='Exact engineering approval before governed scheduling and Planner linking.' if connected else 'Future human quality, allocation or commitment authority; none installed.',
            limits='Cannot approve itself, author lab results, release holds, change criteria or customer commitments.' if connected else 'This workflow is not connected yet. No agent, simulation or source actions run.')
        if definition.workflow_id == 'delivery_readiness':
            item.name='Delivery Readiness / Commitment Planning'
            item.invocation_workflow_id=definition.workflow_id;item.connected_route='delivery_commitment'
            item.cases=['DR-009'];item.authority='bounded_execution'
            item.configuration_authorities=['read_only','proposal_only']
            item.inputs=['Exact ERP order/release quantity and arrival or ship date','Engineering/Validation readiness','Shared Manufacturing material and ERP allocations','Planner logistics']
            item.outputs=['Deterministic readiness and supply calculation','Exact partial commitment proposal','Approved ERP commitment and verified Planner link']
            item.actions=['Read-only specialist analysis','Draft source-bound commitment','Execute exact ERP and Planner updates after Program Owner approval']
            item.approvals='Exact Program Owner approval for quantity/date commitment. Allocation changes require separate authority and are analysis-only.'
            item.limits='No reallocation, quality release, manufacturing or validation change, shipment or customer acceptance. Schedule saved; background scheduler not enabled.'
            item.story='3 · Delivery readiness'
            result.append(item)
            continue
        if definition.workflow_id == 'yield_exception_recovery':
            item.name='Yield / Quality Exception Recovery'
            item.invocation_workflow_id=definition.workflow_id
            item.connected_route='quality_recovery'
            item.cases=['QE-004'];item.authority='bounded_execution'
            item.configuration_authorities=['read_only','proposal_only']
            item.inputs=['QE-004 Manufacturing exception or explicitly armed QE-011 event','Exact source program/configuration/test context','Milestone and customer demand']
            item.outputs=['Validated comparison and supply exposure','Standard investigation handoff','Exact human recovery plan and verified Planner task']
            item.actions=['Read-only specialist investigation','Route approved standard investigation','Record Planner recovery task only after exact Program Owner approval']
            item.approvals='QE-004: Program Owner reviews the exact recovery plan. QE-011: approved standard investigation handoff needs no new human approval. Quality disposition, allocation and customer commitments retain separate authority.'
            item.source_event_scope='Connected for bounded quality_exception_created demo trigger · QE-011 only'
            item.limits='No lot release, test changes, inventory allocation or ERP writes. Only explicitly prepared QE-011 can start from a source event. Saved generic automations remain configuration-only.'
            item.story='2 · Yield / quality recovery'
            result.append(item)
            continue
        if connected:
            item.name = 'Requirement Change Analysis'
            item.purpose = 'Investigate changed requirements, evidence, options and program impact.'
            item.cases = ['CR-017', 'CR-019']
            item.inputs = ['CR-017 material change or CR-019 standard package', 'Exact program and customer scope', 'Current source evidence']
            item.outputs = ['Recorded findings and specialist assessments', 'Exact proposal when supported; separate engineering decision', 'Governed handoff through the existing case workbench']
            item.actions = ['Read-only agent investigation', 'Existing host may prepare an exact proposal for review', 'Execute only separately approved actions in the case workbench']
            item.story = '1A / 1B · Connected change-management family'
            item.approvals = 'CR-017: exact engineering approval before execution. CR-019: prior approved policy permits intake handoff only; no new approval.'
        else:
            item.inputs = ['Illustrative PRG-A17 program context']
            item.outputs = list(definition.planned_capabilities)
            item.actions = ['Save configuration previews only']
            if definition.workflow_id == 'yield_exception_recovery':
                item.name = 'Yield / Quality Exception Recovery'
                item.configuration_authorities = ['read_only', 'proposal_only']
                item.story = '2 · Yield / quality recovery'
                item.specialists = ['manufacturing', 'validation_evidence', 'program_commercial']
            else:
                item.name = 'Delivery Readiness / Commitment Planning'
                item.story = '3 · Delivery readiness'
                item.specialists = ['program_commercial', 'manufacturing', 'validation_evidence']
        result.append(item)
    for key, name, purpose, story in _EXTRAS:
        if key == 'standard_change':
            result.append(CatalogWorkflow(workflow_id=key, name=name, purpose='Verify exact approved scope and deliver the standard package to Validation Operations.',
                mode='Connected', registry_entry=False, connected_route='standard_touchless_handoff', manual_available=True,
                authority='bounded_execution', configuration_authorities=['read_only','bounded_execution'],
                specialists=['change_impact','validation_evidence','program_commercial'],
                source_systems=['Engineering Hub','Validation Lab','Program Planner'], cases=['CR-019'],
                inputs=['CR-019 approved-profile package request','Exact approved procedure/configuration and evidence','Nominated sample and timing'],
                outputs=['Verified applicability and reusable evidence','Execution-ready standard package','Independently verified Validation Operations intake'],
                actions=['Shared requirement-change Coordinator investigation','Deterministic standard policy check','Create one bounded standard intake and read it back'],
                story=story, approvals='No new human approval for the pre-authorized intake handoff. Lab authorization and acceptance remain downstream.',
                limits='Connected route within Requirement Change Analysis. Cannot schedule or authorize a lab job, change criteria, grant acceptance or commitments.'))
            continue
        result.append(CatalogWorkflow(workflow_id=key, name=name, purpose=purpose, mode='Preview', registry_entry=False,
            inputs=['Illustrative PRG-A17 program context'], outputs=['Future findings or review packet'],
            actions=['Save configuration previews only'], story=story,
            approvals='Any future consequential action requires an installed policy and authorized human review.',
            limits='Product concept only. No executor, source access or interactive simulation is installed.'))
    return result

def get_workflow(workflow_id):
    return next((w for w in workflow_catalog() if w.workflow_id == workflow_id), None)
