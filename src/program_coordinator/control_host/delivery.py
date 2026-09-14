"""Delivery projections always re-read current source business state."""
from ..models import ProgramChangeEvent
from ..application.contracts import digest
from ..application.execution_models import SourceReadFailure
from .models import DeliveryCaseView


def event(c):
    r=c.request;key='delivery_'+digest([r.id,c.context_digest])[:30]
    return ProgramChangeEvent(event_id=key,change_id=r.id,customer_id=r.customer_id,program_id=r.program_id,
        source_system=r.request_source,change_type_hint='delivery_readiness',priority='high',requested_by=r.requested_by,
        received_at=r.received_at,request_summary=r.summary,linked_record_ids=[r.order_id,r.milestone_id,r.configuration_id,r.requirement_revision_id],correlation_id=key)


def snapshot(host):
    with host.store.transaction() as data:
        ids={c.case_id for c in data.cases.values() if (c.customer_id,c.program_id,c.change_id)==('CUST-FML01','PRG-A17','DR-009')}
        runs=sorted([r for r in data.runs.values() if r.case_id in ids],key=lambda r:r.started_at,reverse=True)
        progress=[data.delivery_commitments[r.run_id] for r in runs if r.run_id in data.delivery_commitments]
        activity=[a for a in data.activity if a.case_id in ids][-200:]
    c=records=None;available=True
    try:c=host.delivery.context();records=host.delivery.records()
    except (SourceReadFailure,ValueError):
        available=False
        if not runs:return None
    views=[host.run_view(r,change_id='DR-009') for r in runs]
    for view in views:
        p=next((p for p in progress if p.run_id==view.run_id),None)
        status=p.status if p else 'Analysis failed' if view.status in {'failed','cancelled'} else 'Analysis complete' if view.status=='completed' else 'Investigating'
        if p and c:
            plan=next((x for x in records.plans if x.id==p.plan_id),None) if records else None
            own=bool(plan and c.commitment and c.commitment.plan_id==p.plan_id and c.commitment.plan_digest==p.plan_digest and c.state.record_version==plan.expected_state_version+1)
            if c.input_digest!=p.input_digest or (c.context_digest!=p.context_digest and not own):status='stale'
        view.business_outcome=status;view.policy_route='delivery_commitment';view.authority='Exact Program Owner approval for ERP commitment and Planner link; no reallocation'
    status=views[0].business_outcome if views else 'Readiness not assessed'
    return DeliveryCaseView(source_available=available,context=c,records=records,status=status,runs=views,progress=progress,activity=activity)
