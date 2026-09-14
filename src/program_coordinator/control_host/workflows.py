"""Read projections of existing records; no alternate workflow executor."""
from ..models import Model
from .models import RunView, ProposalView
from ..application.models import ActivityRecord
from .downstream import DownstreamView
from ..application.standard_handoff_models import StandardHandoff

class RunDetail(Model):
    run: RunView
    business_question: str
    activity: list[ActivityRecord]
    proposals: list[ProposalView]
    downstream: DownstreamView | None
    source_available: bool
    standard_handoff: StandardHandoff | None = None


def business_outcome(run, proposals, downstream, source_available):
    if run.status == 'running':
        return 'Investigation in progress'
    if run.status != 'completed':
        return 'Investigation cancelled' if run.status == 'cancelled' else 'Investigation failed'
    if not run.recommendation:
        return 'Outcome unavailable'
    if run.recommendation.policy_path == 'escalation_required':
        return 'Escalation required'
    proposal = next((p for p in proposals if p.proposal.origin.run_id == run.run_id), None)
    if proposal:
        if proposal.execution.error_code == 'VERIFICATION_MISMATCH':
            return 'Verification failed'
        status = proposal.effective_status
        if status == 'completed_execution':
            if not source_available:
                return 'Execution recorded · Current source unavailable'
            if downstream and downstream.physical.job and downstream.physical.job.plan_id == proposal.proposal.source_plan.id:
                return physical_outcome(downstream)
            return 'Physical result pending'
        return {
            'proposal_ready': 'Waiting for review', 'waiting_for_approval': 'Waiting for review',
            'approved': 'Approved · Execution pending', 'rejected': 'Rejected', 'stale': 'Stale · Reassessment required',
            'superseded': 'Superseded', 'partially_executed': 'Partially executed',
            'attention_required': 'Reconciliation required', 'execution_failed': 'Execution failed',
            'executing': 'Execution in progress',
        }.get(status, status.replace('_', ' ').capitalize())
    if run.trigger.source_reference and run.trigger.source_reference.startswith('evidence_'):
        if not source_available or not downstream:
            return 'Assessment recorded · Current source unavailable'
        if downstream.assessment and downstream.assessment.run_id == run.run_id:
            return physical_outcome(downstream)
        return 'Assessment recorded · Historical evidence'
    if run.recommendation.policy_path == 'human_review_required':
        return 'Human review required · Proposal not recorded'
    return 'Analysis completed · No business actions executed'


def physical_outcome(value):
    physical = value.physical
    if not physical.result:
        return 'Physical result pending'
    if physical.applicability != 'confirmed':
        return 'Validation gap remains'
    return {
        'approved': 'Validation complete · Customer acceptance pending',
        'rejected': 'Engineering evidence rejected',
        'stale': 'Engineering review stale',
    }.get(physical.engineering_status, 'Waiting for engineering review' if value.review_ready else 'Validation result received · Reassessment pending')
