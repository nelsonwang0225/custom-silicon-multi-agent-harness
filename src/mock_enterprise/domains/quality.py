"""Manufacturing investigation and exact human recovery approval; no inventory writes."""
from fastapi import APIRouter,Request
from enterprise_api.quality_models import (QualityContext,QualityRecords,QualityIntent,QualityInvestigation,RecoveryPlan,RecoveryDecision,
    RecoveryTask,RecoveryReviewInput,RecoveryExecuteInput)
from enterprise_api.quality_policy import analyze,plan_digest,standard_investigation_policy,recovery_workstreams
from enterprise_api.quality_events import QualitySourceEvent
from enterprise_api.standard_policy import digest
from ..core import fail,identity,metadata,new_id
from ..db import read_store
from ..http import mutate,attributed,duplicate

router=APIRouter(tags=['Quality recovery'])

@router.get('/manufacturing/quality-events/{event_id}', response_model=QualitySourceEvent, operation_id='get_quality_source_event')
def read_event(event_id: str, request: Request):
    import json
    from ..autonomous_quality import EVENT_KEY
    with read_store(request.app.state.settings.db_path) as store:
        value = json.loads(store.con.execute('SELECT data FROM demo_metadata WHERE id=1').fetchone()[0]).get(EVENT_KEY)
        fail(value is not None and value.get('event_id') == event_id, 404, 'NOT_FOUND', 'Source event not found.')
        # Reading the event requires the same source scope as its business record.
        store.get('manufacturing.quality_exception', value['exception_id'], identity(request))
        return QualitySourceEvent.model_validate(value)

def exists(store):
    return store.con.execute("SELECT 1 FROM sqlite_master WHERE name='manufacturing_quality_exception'").fetchone() is not None

def context(store,actor,exception_id):
    fail(exists(store),404,'NOT_FOUND','Quality exception not installed.')
    q=store.get('manufacturing.quality_exception',exception_id,actor)
    get=lambda kind,rid:store.get(kind,rid,actor)
    def optional(kind,rid):
        from ..core import BusinessError
        try:return get(kind,rid)
        except BusinessError as exc:
            if exc.status==404:return None
            raise
    data=dict(exception_id=q['id'],program_id=q['program_id'],customer_id=q['customer_id'],exception=q,
        lot=get('manufacturing.lot',q['lot_id']),observation=get('manufacturing.quality_observation',q['observation_id']),
        baseline=optional('manufacturing.quality_baseline',q['baseline_id']),configuration=get('engineering.configuration',q['configuration_id']),
        material=[get('manufacturing.quality_material',rid) for rid in q['material_ids']],
        procedure=optional('engineering.quality_procedure',q['investigation_procedure_id']),
        evidence=[e for e in [optional('validation.result',rid) for rid in q['evidence_ids']] if e],
        milestone=get('planner.milestone',q['milestone_id']),order=get('erp.order',q['order_id']))
    if exception_id == 'QE-011':
        # Reuse the existing approved Quality destination; this is not a queue service.
        data['investigation_destination'] = optional('engineering.quality_procedure','PROC-QE-B-01')
        data['conflicting_exception_ids'] = sorted(v['id'] for v in store.list('manufacturing.quality_exception', actor)
            if v['id'] != exception_id and v['lot_id'] == q['lot_id'] and v['status'] == 'open')
    result=QualityContext.model_validate({**data,'context_digest':digest(data)})
    return result.model_copy(update={'analysis':analyze(result)})

def records(store,actor,exception_id):
    c=context(store,actor,exception_id)
    return dict(exception_id=exception_id,program_id=c.program_id,customer_id=c.customer_id,
        **{key:store.list(kind,actor,exception_id=exception_id) for key,kind in (
            ('investigations','manufacturing.quality_investigation'),('plans','manufacturing.recovery_plan'),
            ('decisions','manufacturing.recovery_decision'),('tasks','planner.recovery_task'))})

@router.get('/manufacturing/quality-exceptions/{exception_id}/context',response_model=QualityContext,operation_id='get_quality_context')
def read_context(exception_id:str,request:Request):
    with read_store(request.app.state.settings.db_path) as store:return context(store,identity(request),exception_id)

@router.get('/manufacturing/quality-exceptions/{exception_id}/records',response_model=QualityRecords,operation_id='get_quality_records')
def read_records(exception_id:str,request:Request):
    with read_store(request.app.state.settings.db_path) as store:return records(store,identity(request),exception_id)

def current(store,actor,body,request):
    c=context(store,actor,body.exception_id);attributed(request,{**c.exception.model_dump(),'change_id':c.exception_id})
    fail(c.context_digest==body.expected_context_digest,409,'STALE_SOURCE','Source changed; reassess.')
    fail(analyze(c).investigation_allowed,409,'QUALITY_POLICY_INELIGIBLE','Approved scoped investigation procedure required.')
    return c

def meta(store,actor,owner,prefix):return {**metadata(store,owner,new_id(prefix),actor),'customer_id':actor.customer_id}

@router.post('/manufacturing/quality-investigations',response_model=QualityInvestigation,status_code=201,operation_id='create_quality_investigation')
def investigate(body:QualityIntent,request:Request):
    def execute(store,actor,payload):
        c=current(store,actor,body,request)
        if c.exception_id == 'QE-011':
            fail(not standard_investigation_policy(c),409,'QUALITY_POLICY_INELIGIBLE','Standard investigation policy requires escalation.')
        duplicate(store.list('manufacturing.quality_investigation',actor,exception_id=c.exception_id,context_digest=c.context_digest))
        item=store.insert('manufacturing.quality_investigation',{**meta(store,actor,'manufacturing','investigation'),
            'exception_id':c.exception_id,'lot_id':c.exception.lot_id,'observation_id':c.observation.id,'test_program_version':c.observation.test_program_version,
            'context_digest':c.context_digest,'queue_id':c.procedure.queue_id,'owner':c.procedure.owner,'tasks':c.procedure.tasks,
            'evidence_ids':[e['id'] for e in c.evidence],'workflow_run_id':body.workflow_run_id,'workflow_case_id':body.workflow_case_id})
        return item,{'exception_id':c.exception_id,'lot_remains_held':True}
    return mutate(request,body,'quality_investigation','automation','create_quality_investigation','manufacturing.quality_investigation',execute)

@router.post('/manufacturing/recovery-plans',response_model=RecoveryPlan,status_code=201,operation_id='create_recovery_plan')
def prepare(body:QualityIntent,request:Request):
    def execute(store,actor,payload):
        c=current(store,actor,body,request)
        duplicate(store.list('manufacturing.recovery_plan',actor,exception_id=c.exception_id,context_digest=c.context_digest))
        investigations=store.list('manufacturing.quality_investigation',actor,exception_id=c.exception_id,context_digest=c.context_digest)
        fail(len(investigations)==1,409,'INVESTIGATION_REQUIRED','Route and verify investigation first.')
        value=RecoveryPlan(**meta(store,actor,'manufacturing','recovery'),exception_id=c.exception_id,lot_id=c.exception.lot_id,
            milestone_id=c.exception.milestone_id,order_id=c.exception.order_id,investigation_id=investigations[0]['id'],
            plan_version=len(store.list('manufacturing.recovery_plan',actor,exception_id=c.exception_id))+1,plan_digest='pending',
            context_digest=c.context_digest,analysis=analyze(c),recovery_owner=c.procedure.recovery_owner,
            workflow_run_id=body.workflow_run_id,workflow_case_id=body.workflow_case_id,
            workstreams=recovery_workstreams(c)).model_dump(mode='json')
        value['plan_digest']=plan_digest(value)
        return store.insert('manufacturing.recovery_plan',value),{'exception_id':c.exception_id,'required_role':'program_owner'}
    return mutate(request,body,'quality_plan','automation','create_recovery_plan','manufacturing.recovery_plan',execute)

def checked_plan(store,actor,plan_id,request):
    p=store.get('manufacturing.recovery_plan',plan_id,actor)
    attributed(request,{**p,'change_id':p['exception_id']})
    c=context(store,actor,p['exception_id'])
    fail(p['plan_digest']==plan_digest(p) and p['context_digest']==c.context_digest,409,'STALE_SOURCE','Exact current source plan required.')
    fail(analyze(c).investigation_allowed and p['analysis']==analyze(c).model_dump(mode='json'),409,'QUALITY_POLICY_INELIGIBLE','Recovery scope changed.')
    return p,c

@router.post('/manufacturing/recovery-decisions',response_model=RecoveryDecision,status_code=201,operation_id='record_recovery_decision')
def review(body:RecoveryReviewInput,request:Request):
    def execute(store,actor,payload):
        p,c=checked_plan(store,actor,body.plan_id,request)
        fail((body.expected_plan_version,body.expected_plan_digest)==(p['plan_version'],p['plan_digest']),409,'STALE_PLAN','Review exact plan version and digest.')
        fail(bool(body.submission_digest and body.recommendation and body.business_context),409,'OPERATOR_ESCALATION_REQUIRED','Exact operator recommendation required.')
        duplicate(store.list('manufacturing.recovery_decision',actor,plan_id=p['id']),decision=body.decision)
        return store.insert('manufacturing.recovery_decision',{**meta(store,actor,'manufacturing','recovery-decision'),
            'exception_id':c.exception_id,'plan_id':p['id'],'plan_version':p['plan_version'],'plan_digest':p['plan_digest'],
            'context_digest':p['context_digest'],'decision':body.decision,'signer_identity':actor.id,'signer_role':actor.role,'comment':body.comment,
            'submission_digest':body.submission_digest,'recommendation':body.recommendation,'business_context':body.business_context}),{'exception_id':c.exception_id}
    return mutate(request,body,'quality_decision','program_owner','record_recovery_decision','manufacturing.recovery_decision',execute)

@router.post('/programs/recovery-tasks',response_model=RecoveryTask,status_code=201,operation_id='record_recovery_task')
def execute_plan(body:RecoveryExecuteInput,request:Request):
    def execute(store,actor,payload):
        p,c=checked_plan(store,actor,body.plan_id,request)
        d=store.get('manufacturing.recovery_decision',body.decision_id,actor)
        fail(d['decision']=='approve' and d['signer_role']==p['required_role'] and d['plan_id']==p['id']
            and d['plan_version']==p['plan_version'] and d['plan_digest']==body.expected_plan_digest==p['plan_digest']
            and d['context_digest']==c.context_digest and d['exception_id']==c.exception_id
            and body.expected_submission_digest==d['submission_digest'],409,'APPROVAL_REQUIRED','Exact authorized recovery decision required.')
        duplicate(store.list('planner.recovery_task',actor,plan_id=p['id']))
        return store.insert('planner.recovery_task',{**meta(store,actor,'planner','recovery-task'),
            'exception_id':c.exception_id,'lot_id':p['lot_id'],'milestone_id':p['milestone_id'],'plan_id':p['id'],'decision_id':d['id'],
            'plan_digest':p['plan_digest'],'owner':p['recovery_owner'],'eligible_quantity':p['analysis']['eligible_quantity'],
            'gap_quantity':p['analysis']['gap_quantity'],'submission_digest':d['submission_digest'],
            'approved_recommendation':d['recommendation'],'business_context':d['business_context'],
            'workstreams':p['workstreams']}),{'exception_id':c.exception_id,'allocation_changed':False,'commitment_changed':False}
    return mutate(request,body,'quality_task','automation','record_recovery_task','planner.recovery_task',execute)
