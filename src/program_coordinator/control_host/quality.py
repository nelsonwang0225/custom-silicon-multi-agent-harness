"""Current source projections; persisted host metadata contains references and attempts."""
from pydantic import Field
from enterprise_api.quality_models import QualityContext, QualityRecords
from ..models import Model, ProgramChangeEvent
from ..application.contracts import digest
from ..application.quality_recovery_models import QualityProgress
from ..application.execution_models import SourceReadFailure
from ..application.models import ActivityRecord
from .models import RunView, QualityCaseView


def event(c):
    q=c.exception;key='quality_'+digest([q.id,q.content_version,c.context_digest])[:30]
    return ProgramChangeEvent(event_id=key,change_id=q.id,customer_id=q.customer_id,program_id=q.program_id,
        source_system=q.request_source,change_type_hint='quality_exception',priority='high',requested_by=q.requested_by,
        received_at=q.received_at,request_summary=q.summary,linked_record_ids=[q.lot_id,q.observation_id,q.configuration_id,q.milestone_id,q.order_id],correlation_id=key)


def snapshot(host, exception_id='QE-004'):
    with host.store.transaction() as data:
        ids={c.case_id for c in data.cases.values() if (c.customer_id,c.program_id,c.change_id)==('CUST-FML01','PRG-A17',exception_id)}
        runs=sorted([r for r in data.runs.values() if r.case_id in ids],key=lambda r:r.started_at,reverse=True)
        progress=[data.quality_recoveries[r.run_id] for r in runs if r.run_id in data.quality_recoveries]
        activity=[a for a in data.activity if a.case_id in ids][-200:]
    c=records=None;available=True
    try:c=host.quality.context(exception_id);records=host.quality.records(exception_id)
    except (SourceReadFailure,ValueError):
        available=False
        if not runs:return None
    views=[host.run_view(r,change_id=exception_id) for r in runs]
    for view in views:
        p=next((p for p in progress if p.run_id==view.run_id),None)
        status=p.status if p else 'Analysis failed' if view.status in {'failed','cancelled'} else 'Analysis complete · No handoff authorized' if view.status=='completed' else 'Investigating'
        if p and c and p.context_digest!=c.context_digest:status='stale'
        view.business_outcome=status;view.policy_route=p.policy_route if p else ('standard_quality_investigation_handoff' if exception_id=='QE-011' else 'quality_recovery')
        view.authority='No human approval required for verified standard investigation routing' if view.policy_route=='standard_quality_investigation_handoff' else 'Standard investigation; exact Program Owner review for recovery task'
    return QualityCaseView(change_id=exception_id,source_available=available,context=c,records=records,status=views[0].business_outcome if views else 'Quality exception opened',runs=views,progress=progress,activity=activity)
