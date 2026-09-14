"""Read projections of existing business/runtime observations, never an executor."""
from .access import require_surface, route_allowed
from datetime import datetime, timezone
from fastapi import Request
from program_investigator.config import PROJECT
from ..application.models import WorkflowError, now_utc
from ..application.demo_identity import READER
from ..application.observability import visible, identifier
from .operations_models import *
from .operations_artifacts import evals, run_artifacts, read_json

SCOPE=('CUST-FML01','PRG-A17')
SYSTEMS=('Engineering Hub','Validation Lab','Manufacturing Portal','Commercial ERP','Program Planner')
LABELS={'Handed to Validation Operations':'Handoff verified · Lab authorization pending','awaiting_review':'Waiting for human review','waiting_for_approval':'Waiting for human review','proposal_ready':'Waiting for human review',
 'partial_completion':'Partial execution','partially_executed':'Partial execution','handoff_verified':'Handoff verified · Lab authorization pending',
 'verified':'Execution verified','approved':'Approved · Execution pending','verification_failed':'Not verified · Readback failed',
 'stale':'Stale proposal · Reassessment required','outcome_unknown':'Reconciliation required','readiness_blocked':'Readiness blocked',
 'completed_execution':'Execution verified · Physical result pending','review_required':'Human review required', 'Waiting for review':'Waiting for human review', 'Verification failed':'Not verified · Readback failed', 'Partially executed':'Partial execution'}

def label(v):return LABELS.get(v,v.replace('_',' ').capitalize())

def outcome_label(value,case):
    return 'Quality investigation handoff verified' if case=='QE-011' and value=='handoff_verified' else label(value)

def current_case(row,snapshot):
    summary=next((c for c in snapshot.case_summaries if c.change_id==row.case_id),None)
    if summary:
        row.current_case_state=summary.state
        row.current_case_label=summary.state_label
        row.source_checked_at=snapshot.fetched_at
def duration(start,end):
    try:return max(0,(datetime.fromisoformat(end.replace('Z','+00:00'))-datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds()*1000)
    except (TypeError,ValueError,AttributeError):return None

def numeric(v):return v if type(v) in (int,float) and v>=0 else None

def case_path(case,program='PRG-A17'):return f'/control/programs/{program}/cases/{case}'

def target(tool):
    for words,system in ((('manufacturing','quality'),'Manufacturing Portal'),(('validation','coverage','lab','sample'),'Validation Lab'),(('customer_order','delivery','erp','cost'),'Commercial ERP'),(('program','milestone','planner'),'Program Planner')):
        if any(w in tool.lower() for w in words):return system
    return 'Engineering Hub' if tool.startswith('get_') else 'Host / runtime'


def rows(host,data):
    values=[]
    for r in sorted(data.runs.values(),key=lambda r:r.started_at,reverse=True):
        if (r.customer_id,r.program_id)!=SCOPE:continue
        c=data.cases.get(r.case_id)
        if not c or not c.change_id:continue
        p=data.delivery_commitments.get(r.run_id) or data.quality_recoveries.get(r.run_id)
        h=data.standard_handoffs.get(r.run_id)
        e=next((v for v in data.executions.values() if v.reference.run_id==r.run_id),None)
        outcome='Investigation in progress' if r.status=='running' else 'Investigation incomplete' if r.status!='completed' else 'Analysis complete · No business execution recorded'
        if r.recommendation:
            if r.recommendation.policy_path=='escalation_required':outcome='Escalation required'
            elif r.recommendation.policy_path=='human_review_required':outcome='Waiting for human review'
        state=p or h or e
        if state:outcome=label(state.status)
        verification='Not recorded';decision='Not recorded'
        if e:
            review=data.reviews.get(e.review_id);decision=review.status.replace('_',' ').capitalize() if review else 'Pending'
            states=[s.verification for s in e.steps]
            verification='Mismatch' if 'mismatch' in states else 'Inconclusive' if 'inconclusive' in states else 'Verified' if states and all(s=='matched' for s in states) else 'Pending'
        if p:
            decision={'approve':'Approved','reject':'Rejected'}.get(p.decision,label(p.decision)) if p.decision else 'Pending' if p.plan_id else 'Not recorded'
            verification='Mismatch' if p.error_code=='VERIFICATION_MISMATCH' else 'Failed / inconclusive' if p.status=='verification_failed' else 'Verified' if p.status in ('verified','commitment_current','handoff_verified') else 'Pending'
            if getattr(p,'policy_route',None)=='standard_quality_investigation_handoff':
                decision='Not required for executed actions' if p.status=='handoff_verified' else 'Standard policy check; escalate if ineligible'
                if p.status=='handoff_verified':outcome='Quality investigation handoff verified'
        if h:verification=h.verification_status.replace('_',' ').capitalize();decision='Pre-authorized intake policy' if h.status!='review_required' else 'Human review required'
        if getattr(state,'error_code',None)=='VERIFICATION_MISMATCH':verification='Mismatch';outcome='Not verified · Readback mismatch'
        sessions=[s.session_id for s in data.concierge_sessions.values() if r.run_id in s.run_ids and (s.customer_id,s.program_id)==SCOPE]
        report={}
        try:
            candidate=read_json(host.store.directory,'runs/'+r.run_id+'/report.json')
            if isinstance(candidate,dict) and (candidate.get('run_id'),candidate.get('case_id'))==(r.run_id,r.case_id):report=candidate
        except (OSError,ValueError):pass
        values.append(OpsRun(run_id=r.run_id,case_id=c.change_id,program_id=r.program_id,workflow_id='standard_change' if c.change_id=='CR-019' else r.workflow_id,
            invocation_source='Concierge' if r.invocation_id.startswith('ui_chat_') else 'Manufacturing source event' if r.trigger.kind=='source_event' else label(r.trigger.kind),
            event_id=r.trigger.source_reference if r.trigger.kind=='source_event' else None, event_name=r.trigger.event_name, event_version=r.trigger.event_version,actor=visible(r.actor_id),started_at=r.started_at,completed_at=r.completed_at,
            duration_ms=duration(r.started_at,r.completed_at),runtime_state=r.status,business_outcome=outcome,decision_state=decision,verification_state=verification,
            trace_id=identifier(r.trace_id or report.get('trace_id')),model=identifier(report.get('model')),execution_mode=r.execution_mode,case_link=case_path(c.change_id,r.program_id),
            policy_route='Touchless / standard quality investigation' if getattr(p,'policy_route',None)=='standard_quality_investigation_handoff' else r.recommendation.policy_path if r.recommendation else 'Not assessed',
            session_ids=sessions,attention=r.status in ('failed','cancelled') or any(v in outcome.lower() for v in ('fail','partial','stale','escalat','reconcil','not verified','blocked'))))
    return values


def run_detail(host,run_id):
    with host.store.transaction() as data:
        row=next((r for r in rows(host,data) if r.run_id==run_id),None)
        if not row:raise WorkflowError('RUN_NOT_FOUND')
        r=data.runs[run_id]
    artifacts,artifact_state=run_artifacts(host,r);state=artifacts.get('case-state',{});report=artifacts.get('report',{})
    d=OpsRunDetail(run=row,question=visible(state['event']['request_summary']) if state.get('event') else None,artifact_state=artifact_state,
        links=[OpsLink(label='Open '+row.case_id,href=row.case_link),OpsLink(label='Open program',href='/control/programs/'+row.program_id),
            OpsLink(label='View decisions',href='/control/decisions')])
    # Only actual invocations; no inferred "completed" specialists or rationale/hidden reasoning.
    if state:
        d.agents.append(OpsAgent(name='Program Coordinator',status=r.status,started_at=r.started_at,completed_at=r.completed_at,duration_ms=row.duration_ms))
        assessments={v['invocation_id']:v['assessment'] for v in state.get('completed_assessments',[])}
        for i in state.get('requested_specialists',[]):
            d.agents.append(OpsAgent(name=visible(i['specialist']),invocation_id=identifier(i['invocation_id']),caller=identifier(i.get('caller')),status=visible(i['status']),duration_ms=max(0,i['ended_ms']-i['started_ms']) if i.get('ended_ms') is not None else None,
                summary=visible(assessments[i['invocation_id']]['summary']) if i['invocation_id'] in assessments else None,error='Specialist failed' if i.get('error') else None))
        for ref in state.get('source_references',[]):
            if ref.get('tool_name')=='verify_knowledge_document':continue
            d.evidence.append(OpsEvidence(source_id=visible(ref['source_id']),tool=visible(ref['tool_name']),record_id=identifier(ref.get('record_id')),
                content_version=ref.get('content_version'),record_version=ref.get('record_version'),link=row.case_link+'?tab=evidence'+('&evidence='+ref['record_id'] if row.case_id=='CR-017' and identifier(ref.get('record_id')) and ref['record_id'].startswith('RES-') else '')))
    for call in artifacts.get('tool-calls',[]):
        ids=[v for k,v in call.get('arguments',{}).items() if k.endswith('_id') and identifier(v)]
        d.calls.append(OpsCall(name=visible(call.get('tool','Unknown tool')),caller=visible(call.get('role','Not recorded')),target=target(call.get('tool','')),
            status='Failed' if call.get('error') or call.get('status')=='failed' else 'Succeeded' if call.get('data') is not None else 'Unknown',
            duration_ms=numeric(call.get('latency_ms')),identifiers=ids,source_id=identifier(call.get('source_id')),link=row.case_link+'?tab=evidence'))
    for span in artifacts.get('trace-metadata',[]):
        if span.get('error'):
            d.calls.append(OpsCall(name=visible(span.get('tool') or ('SDK '+str(span.get('type','operation'))+' failure')),
                caller=visible(span.get('role') or 'Unavailable'),target=target(span.get('tool','')),
                status='Failed',duration_ms=duration(span.get('started_at'),span.get('ended_at')),link=row.case_link))
    usage=report.get('usage') or {}
    if not isinstance(usage,dict):usage={}
    d.input_tokens=numeric(usage.get('input_tokens'));d.output_tokens=numeric(usage.get('output_tokens'));d.total_tokens=numeric(usage.get('total_tokens'))
    generations=report.get('generations') or []
    if not isinstance(generations,list) or any(not isinstance(g,dict) for g in generations):generations=[]
    d.model_latency_ms=sum(g['latency_ms'] for g in generations) if generations and all(numeric(g.get('latency_ms')) is not None for g in generations) else None
    events=[a for a in data.activity if a.run_id==run_id and (a.customer_id,a.program_id)==SCOPE]
    d.timeline=[OpsEvent(timestamp=a.timestamp,stage=label(a.event_type),actor=visible(a.actor_id),status=visible(a.details.get('status','')) or None,error=visible(a.details['error_code']) if a.details.get('error_code') else None) for a in events]
    # Wall-clock review interval is separate from investigation/runtime elapsed time.
    requested=next((a.timestamp for a in events if a.event_type=='approval_requested'),None)
    decided=next((a.timestamp for a in events if a.event_type in ('proposal_approved','proposal_rejected')),None)
    if requested:d.human_wait_ms=duration(requested,decided or now_utc())
    for e in data.executions.values():
        if e.reference.run_id!=run_id:continue
        p=data.proposals.get(f'{e.reference.proposal_id}:{e.reference.proposal_version}');review=data.reviews.get(e.review_id)
        d.decision.extend([('Proposal',e.reference.proposal_id),('Version',str(e.reference.proposal_version)),('Digest',e.reference.proposal_digest),('Decision',review.status if review else 'Pending'),('Approver',review.actor_id if review else 'Not recorded')])
        if p:d.links.append(OpsLink(label='View exact proposal',href=f'/control/decisions/{p.proposal_id}/{p.proposal_version}?digest={p.proposal_digest}'))
        for s in e.steps:
            attempts=[a for a in data.execution_attempts if a.reference==e.reference and a.action_id==s.action_id]
            v=[v for v in data.verifications.values() if v.origin.run_id==run_id and v.action_id==s.action_id]
            action=next((a for a in p.manifest if a.action_id==s.action_id),None) if p else None
            d.actions.append(OpsAction(name=label(action.operation if action else s.action_id),status=label(s.status),verification=label(s.verification or 'not_started'),
                source_id=s.resource_id,error=s.error_code,idempotency_key=attempts[-1].idempotency_key if attempts else None,
                expected=visible(action.expected) if action else 'Exact approved plan '+e.reference.proposal_id,actual=visible(v[-1].explanation) if v else 'No independent readback recorded',
                attempts=[(a.started_at,label(a.outcome)) for a in attempts]))
    p=data.delivery_commitments.get(run_id) or data.quality_recoveries.get(run_id)
    if p:
        d.decision.extend([(k,str(getattr(p,k))) for k in ('plan_id','plan_version','plan_digest','decision') if getattr(p,k) is not None])
        for op,s in p.steps.items():
            # Review/prepare calls are retained separately from authorized business execution.
            d.calls.append(OpsCall(name={'erp':'ERP commitment update','planner':'Planner update','execute':'Planner recovery task','investigate':'Manufacturing investigation','prepare':'Prepare source plan','review':'Record source decision'}.get(op,op),caller='Trusted host',target='Commercial ERP' if row.case_id=='DR-009' and op!='planner' else 'Program Planner' if op in ('planner','execute') else 'Manufacturing Portal',status=label(s.status),identifiers=[s.source_id] if s.source_id else [],link=row.case_link))
            d.actions.append(OpsAction(name={'erp':'ERP commitment','planner':'Planner update','execute':'Planner recovery task','investigate':'Standard investigation'}.get(op,label(op)),status='Succeeded' if s.status in ('verified','verification_failed','action_succeeded') and s.source_id else label(s.status),
                verification='Verified' if s.status=='verified' else 'Mismatch' if s.error_code=='VERIFICATION_MISMATCH' or (s.status=='verification_failed' and p.error_code=='VERIFICATION_MISMATCH') else 'Inconclusive' if s.status=='verification_failed' else 'Pending',
                source_id=s.source_id,error=s.error_code,idempotency_key=s.key,expected='Exact source plan '+str(p.plan_id) if p.plan_id else 'Exact current context '+p.context_digest,
                actual=('Independent source record '+s.source_id+' matched' if s.status=='verified' and s.source_id else 'Readback did not establish a match'),
                attempts=[(a.timestamp,label(a.event_type)) for a in events if str(a.details.get('status','')).startswith(op+'_')]))
    h=data.standard_handoffs.get(run_id)
    if h:
        d.actions.append(OpsAction(name='Validation Operations intake',status=label(h.action_status),verification=h.verification_status.replace("_"," ").capitalize(),source_id=h.intake.id if h.intake else None,
            error=h.error_code,idempotency_key=h.action_key,expected='Exact standard package '+h.package.package_id if h.package else 'Package not prepared',
            actual='Intake '+h.intake.id+' · '+h.intake.status if h.intake else 'Not read back'))
    # Current source facts use the same source projection as cases and Concierge.
    from .concierge_reads import grounded_cards
    try:
        snapshot=host.snapshot();d.source_checked_at=snapshot.fetched_at
        current_case(d.run,snapshot)
        current=[*snapshot.runs,*getattr(snapshot.standard,'runs',[]),*getattr(snapshot.quality,'runs',[]),*getattr(snapshot.autonomous_quality,'runs',[]),*getattr(snapshot.delivery,'runs',[])]
        current_run=next((v for v in current if v.run_id==run_id),None)
        if current_run and d.run.verification_state!='Mismatch':
            d.run.business_outcome=outcome_label(current_run.business_outcome,row.case_id);d.run.attention|='stale' in d.run.business_outcome.lower()
        for card in grounded_cards(host,snapshot,row.case_id,'status'):
            d.facts.extend([(visible(k),visible(v)) for k,v in card.facts])
        # Approver and immutable manifest remain source-owned for quality/delivery.
        records=getattr(snapshot.delivery if row.case_id=='DR-009' else snapshot.quality if row.case_id=='QE-004' else snapshot.autonomous_quality if row.case_id=='QE-011' else None,'records',None)
        if p and records:
            plan=next((v for v in records.plans if v.id==p.plan_id),None)
            dec=next((v for v in records.decisions if v.plan_id==p.plan_id),None)
            if plan:
                for k in ('permitted_actions','permitted_action','quantity','committed_at','destination'):
                    if hasattr(plan,k):d.decision.append((label(k),visible(getattr(plan,k))))
            for action in d.actions:
                if action.name=='ERP commitment' and plan:
                    action.expected=visible({'plan_id':plan.id,'quantity':plan.quantity,'committed_at':plan.committed_at,'destination':plan.destination})
                    actual=next((v for v in getattr(records,'commitments',[]) if v.id==action.source_id),None)
                    if actual:
                        action.actual=visible({k:getattr(actual,k) for k in ('id','plan_id','quantity','committed_at','destination') if hasattr(actual,k)})
            if dec:
                for k in ('id','actor_id','signer_identity','decided_at','created_at','decision'):
                    if hasattr(dec,k):d.decision.append((label(k),visible(getattr(dec,k))))
    except (WorkflowError,ValueError):d.facts=[('Current source','Unavailable · Retained run observations are historical')]
    failures=[a for a in events if a.details.get('error_code')]
    if r.error_code or row.attention:
        last=failures[-1] if failures else None
        d.failure=[('Stage',label(last.event_type) if last else 'See business outcome'),('Category',visible(r.error_code or (last.details.get('error_code') if last else 'Outcome needs attention'))),
            ('Last successful activity',label(next((a.event_type for a in reversed(events) if a.event_type in {'analysis_completed','recommendation_recorded','source_state_verified','standard_handoff_verified','source_decision_retained','proposal_approved','program_plan_updated','validation_job_created','action_reconciled'}),'not_recorded'))),
            ('Business mutation','Observed source write' if any(a.source_id and a.status in ('Succeeded','Verified') for a in d.actions) else 'Not established by available receipts'),
            ('Next step','Inspect the case to retry or reconcile through the existing governed controls')]
    for sid in row.session_ids:d.links.append(OpsLink(label='Open Concierge session',href='/control/operations/sessions/'+sid))
    return d


def health(host,check=False):
    if check:
        reads=(('Engineering Hub','get_change_request',('CR-017',)),('Validation Lab','get_validation_coverage',('CR-017',)),
            ('Manufacturing Portal','get_manufacturing_lots',('PRG-A17',)),('Commercial ERP','get_customer_order',('ORD-1204',)),('Program Planner','get_program',('PRG-A17',)))
        result=[]
        for system,method,args in reads:
            try:getattr(host.source.read,method)(*args);status='Available';detail='Scoped source read succeeded'
            except AttributeError:status='Unknown / not checked';detail='Read adapter unavailable'
            except WorkflowError:status='Unavailable';detail='Scoped source read failed'
            result.append(OpsHealth(system=system,status=status,checked_at=now_utc(),detail=detail))
        host.operations_health=result
    result=getattr(host,'operations_health',None) or [OpsHealth(system=s) for s in SYSTEMS]
    return [v.model_copy(update={'status':'Stale · '+v.status}) if v.checked_at and (duration(v.checked_at,now_utc()) or 0)>300000 else v for v in result]


def attach(app,host,actor):
    @app.get('/control-api/operations',response_model=OpsIndex)
    def index(request:Request):
        require_surface(actor(request), 'operations')
        with host.store.transaction() as data:
            runs=rows(host,data);sessions=[OpsSessionSummary(session_id=s.session_id,created_at=s.created_at,updated_at=s.updated_at,turn_count=len(s.turns),run_ids=s.run_ids) for s in data.concierge_sessions.values() if (s.customer_id,s.program_id)==SCOPE and s.owner_actor_id==actor(request).actor_id]
        # Initial/explicit refresh uses the SAME current source view as the workbench.
        # The separate /runs poll remains metadata-only and does not trigger source reads.
        try:
            snapshot=host.snapshot()
            current={r.run_id:r for r in [*snapshot.runs,*getattr(snapshot.standard,'runs',[]),*getattr(snapshot.quality,'runs',[]),*getattr(snapshot.autonomous_quality,'runs',[]),*getattr(snapshot.delivery,'runs',[])]}
            for row in runs:
                current_case(row,snapshot)
                v=current.get(row.run_id)
                if v and row.verification_state!='Mismatch':
                    row.business_outcome=outcome_label(v.business_outcome,row.case_id)
                    row.attention|='stale' in row.business_outcome.lower()
        except (WorkflowError,ValueError):pass
        # Limited to installed scope, allowlisted artifacts and this actor's chats.
        evaluations,missing=evals(getattr(host,'operations_artifact_root',PROJECT))
        for row in runs:
            row.session_ids=[sid for sid in row.session_ids if any(s.session_id==sid for s in sessions)]
        return OpsIndex(runs=runs,evals=evaluations,unavailable_artifacts=missing,sessions=sessions,health=health(host),
            runtime=('Live AI for main cases · Scripted QE-011 · Connectivity not checked' if host.runtime_mode('QE-011')=='deterministic_test' else 'Configured live runtime · Credentials/connectivity not checked') if host.mode=='live_model' else 'Deterministic test runtime · No paid model',observability_error=getattr(host,'observability_error',None))

    @app.get('/control-api/operations/runs',response_model=list[OpsRun])
    def runs(request:Request):
        require_surface(actor(request), 'operations')
        with host.store.transaction() as data:
            values=rows(host,data)
            for row in values:
                row.session_ids=[sid for sid in row.session_ids if data.concierge_sessions[sid].owner_actor_id==actor(request).actor_id]
            return values

    @app.get('/control-api/operations/runs/{run_id}',response_model=OpsRunDetail)
    def detail(run_id:str,request:Request):
        require_surface(actor(request), 'operations')
        value=run_detail(host,run_id)
        with host.store.transaction() as data:
            value.run.session_ids=[sid for sid in value.run.session_ids if data.concierge_sessions[sid].owner_actor_id==actor(request).actor_id]
        value.links=[l for l in value.links if route_allowed(actor(request),l.href) and ('/sessions/' not in l.href or l.href.rsplit('/',1)[-1] in value.run.session_ids)]
        return value

    @app.get('/control-api/operations/health',response_model=list[OpsHealth])
    def check(request:Request):
        require_surface(actor(request), 'operations')
        return health(host,True)

    @app.get('/control-api/operations/sessions/{session_id}',response_model=ObservedSession)
    def session(session_id:str,request:Request):
        require_surface(actor(request), 'operations')
        with host.store.transaction() as data:
            s=data.concierge_sessions.get(session_id)
            if not s or (s.customer_id,s.program_id)!=SCOPE:raise WorkflowError('CHAT_SESSION_EXPIRED')
            if s.owner_actor_id!=actor(request).actor_id:raise WorkflowError('CHAT_SESSION_FORBIDDEN')
            s=s.model_copy(deep=True)
        from ..knowledge.concierge import visible_cards
        for t in s.turns:t.cards=visible_cards(host,t.cards,actor(request))
        return s
