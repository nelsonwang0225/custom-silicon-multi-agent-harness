"""Thin standard-route projections; the shared service owns invocation."""
from enterprise_api.standard_models import StandardContext
from enterprise_api.standard_policy import evaluate, digest
from ..models import ProgramChangeEvent
from ..application.demo_identity import READER
from ..application.models import now_utc
from ..application.execution_models import SourceReadFailure


def event(context):
    r=context.request
    return ProgramChangeEvent(event_id='standard_'+digest([r.id,r.content_version])[:24],change_id=context.change_id,
        customer_id=context.customer_id,program_id=context.program_id,source_system=r.request_source,
        change_type_hint='standard_validation_package',priority='low',requested_by=r.requested_by,
        received_at=context.change['request_received_at'],request_summary=r.summary,
        linked_record_ids=[r.change_id,r.baseline_requirement_revision_id],correlation_id='standard_'+digest([r.id,r.content_version])[:24])


def outcome(value):
    if value is None:
        return 'Assessing applicability'
    return {'handoff_verified':'Handed to Validation Operations','review_required':'Standard change requires review',
        'source_unavailable':'Source context unavailable','prepared':'Package prepared','action_started':'Handoff in progress',
        'action_succeeded':'Action succeeded · Verification pending','outcome_unknown':'Handoff outcome unknown · Reconciliation required',
        'write_failed':'Handoff failed','verification_failed':'Handoff verification failed'}[value.status]


def snapshot(host):
    from .models import StandardCaseView
    with host.store.transaction() as data:
        cases=[c for c in data.cases.values() if (c.customer_id,c.program_id,c.change_id)==('CUST-FML01','PRG-A17','CR-019')]
        ids={c.case_id for c in cases}
        runs=sorted([r for r in data.runs.values() if r.case_id in ids],key=lambda r:r.started_at,reverse=True)
        handoffs=[data.standard_handoffs[r.run_id] for r in runs if r.run_id in data.standard_handoffs]
        activity=[a for a in data.activity if a.case_id in ids][-200:]
    context=None;available=True
    try:
        definitions=host.source.read.get_standard_change_requests('PRG-A17')['items']
        if not any(r['change_id']=='CR-019' for r in definitions):
            if not runs:return None
            available=False
        else:
            context=host.standard.context()
    except (SourceReadFailure,ValueError):
        available=False
        if not runs:return None
    views=[host.run_view(r,change_id='CR-019') for r in runs]
    for view in views:
        handoff=next((h for h in handoffs if h.run_id==view.run_id),None)
        view.business_outcome=outcome(handoff) if handoff else 'Investigation failed' if view.status in {'failed','cancelled'} else 'Assessing applicability'
        view.policy_route='standard_touchless_handoff'
        view.authority='Bounded pre-authorized handoff'
    # Eligibility is an investigation result, not a passive page-load fact.
    # A run record exists while agents are still working, so publish the result
    # only after the latest investigation has reached a completed state. A
    # running, failed or cancelled rerun must not inherit a prior result.
    result_recorded = bool(runs and runs[0].status == 'completed')
    return StandardCaseView(source_available=available,context=context,eligibility=evaluate(context) if context and result_recorded else None,
        status=views[0].business_outcome if views else 'Standard change · New request',runs=views,handoffs=handoffs,activity=activity)
