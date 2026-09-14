"""Narrow source transactions for a human-authorized delivery commitment."""
from fastapi import APIRouter, Request
from enterprise_api.delivery_models import (DeliveryContext, DeliveryRecords, DeliveryPrepareInput, CommitmentPlan,
    CommitmentDecision, DeliveryCommitment, DeliveryLink, DeliveryExecuteInput)
from enterprise_api.quality_models import RecoveryReviewInput
from enterprise_api.delivery_policy import analyze, plan_digest
from enterprise_api.standard_policy import digest
from ..core import fail, identity, metadata, new_id
from ..db import read_store
from ..http import mutate, attributed, duplicate

router = APIRouter(tags=['Delivery readiness'])


def optional(store, actor, kind, record_id):
    from ..core import BusinessError
    try: return store.get(kind, record_id, actor)
    except BusinessError as exc:
        if exc.status == 404: return None
        raise


def context(store, actor, delivery_id):
    fail(store.con.execute("SELECT 1 FROM sqlite_master WHERE name='erp_delivery_request'").fetchone(),404,'NOT_FOUND','Delivery case not installed.')
    r = store.get('erp.delivery_request',delivery_id,actor)
    get = lambda kind,rid: store.get(kind,rid,actor)
    req = get('engineering.requirement',r['requirement_revision_id'])
    clearance = optional(store,actor,'engineering.delivery_clearance',r['clearance_id'])
    material = [get('manufacturing.quality_material',rid) for rid in r['material_ids']]
    allocations = [get('erp.delivery_allocation',rid) for rid in r['allocation_ids']]
    dependency = None
    if r['technical_change_id']:
        fail(r['technical_change_id']=='CR-017',422,'INVALID_SCOPE','Only the existing CR-017 dependency is supported.')
        from .downstream import physical
        current = physical(store,actor)
        # Delivery consumes a bounded current-state projection. The evidence digest
        # binds the full Validation contract, including historical snapshots; those
        # immutable content projections are not competing current business records.
        projection = {k:current[k] for k in ('change_id','available','job_status','result','engineering_status','technical_state',
            'evidence_digest','applicability','mismatch_reasons','customer_acceptance','customer_commitment')}
        binding=current.get('evidence_binding')
        projection['evidence_binding'] = {k:binding[k] for k in ('requirement','plan_id','plan_version','plan_digest','approval_id','evidence_set_digest')} if binding else None
        review=current.get('current_review')
        projection['current_review'] = {k:v for k,v in review.items() if k!='evidence_binding'} if review else None
        dependency = dict(change=get('engineering.change',r['technical_change_id']),physical=projection)
    evidence_ids = clearance['evidence_ids'] if clearance else []
    if dependency:
        clearance = None  # CR-017 uses its own exact Engineering evidence review.
        evidence_ids = [dependency['physical']['result']['id']] if dependency['physical'].get('result') else []
    data = dict(delivery_id=delivery_id,program_id=r['program_id'],customer_id=r['customer_id'],request=r,
        order=get('erp.order',r['order_id']),milestone=get('planner.milestone',r['milestone_id']),configuration=get('engineering.configuration',r['configuration_id']),
        requirement=req,workload=get('engineering.workload',req['workload_profile_id']),criteria=get('engineering.criteria',req['acceptance_limits_ref']),
        evidence=[e for rid in evidence_ids if (e:=optional(store,actor,'validation.result',rid))],clearance=clearance,technical_dependency=dependency,
        material=material,lots=[get('manufacturing.lot',m['lot_id']) for m in material],allocations=allocations,
        allocation_orders=[get('erp.order',rid) for rid in sorted({a['order_id'] for a in allocations})],
        future_supply=[get('manufacturing.future_supply',rid) for rid in r['future_supply_ids']],logistics=optional(store,actor,'planner.delivery_logistics',r['logistics_id']))
    input_digest=digest(data)
    states=store.list('erp.delivery_state',actor,delivery_id=delivery_id)
    fail(len(states)==1,409,'DELIVERY_STATE_MISSING','Exact source commercial state required.')
    state=states[0];commitment=get('erp.delivery_commitment',state['current_commitment_id']) if state['current_commitment_id'] else None
    data.update(state=state,commitment=commitment)
    c=DeliveryContext.model_validate(dict(**data,input_digest=input_digest,context_digest=digest(data)))
    return c.model_copy(update={'analysis':analyze(c)})


def records(store,actor,delivery_id):
    c=context(store,actor,delivery_id)
    return dict(delivery_id=delivery_id,program_id=c.program_id,customer_id=c.customer_id,
        **{key:store.list(kind,actor,delivery_id=delivery_id) for key,kind in (
            ('plans','erp.commitment_plan'),('decisions','erp.commitment_decision'),('commitments','erp.delivery_commitment'),('links','planner.delivery_link'))})


@router.get('/erp/delivery-requests/{delivery_id}/context',response_model=DeliveryContext,operation_id='get_delivery_context')
def read_context(delivery_id:str,request:Request):
    with read_store(request.app.state.settings.db_path) as store:return context(store,identity(request),delivery_id)


@router.get('/erp/delivery-requests/{delivery_id}/records',response_model=DeliveryRecords,operation_id='get_delivery_records')
def read_records(delivery_id:str,request:Request):
    with read_store(request.app.state.settings.db_path) as store:return records(store,identity(request),delivery_id)


def meta(store,actor,owner,prefix):return {**metadata(store,owner,new_id(prefix),actor),'customer_id':actor.customer_id}


@router.post('/erp/commitment-plans',response_model=CommitmentPlan,status_code=201,operation_id='create_commitment_plan')
def prepare(body:DeliveryPrepareInput,request:Request):
    def execute(store,actor,payload):
        c=context(store,actor,body.delivery_id);attributed(request,{'program_id':c.program_id,'change_id':c.delivery_id})
        duplicate(store.list('erp.commitment_plan',actor,delivery_id=c.delivery_id,context_digest=c.context_digest,selected_option=body.selected_option))
        fail(c.context_digest==body.expected_context_digest,409,'STALE_SOURCE','Reassess current delivery inputs.')
        a=analyze(c);fail(a.proposal_allowed,409,'DELIVERY_NOT_READY','Technical, supply and timing gates must be satisfied.')
        option=next(o for o in a.options if o.id==body.selected_option and o.executable)
        # A rerun of an unchanged committed release is a status read, not another promise.
        fail(c.commitment is None or (c.commitment.quantity,c.commitment.committed_at)!=(option.quantity,option.proposed_at),409,'COMMITMENT_ALREADY_CURRENT','Current authorized commitment already matches.')
        value=CommitmentPlan(**meta(store,actor,'erp','commitment-plan'),delivery_id=c.delivery_id,order_id=c.request.order_id,line_id=c.request.line_id,
            milestone_id=c.request.milestone_id,plan_version=len(store.list('erp.commitment_plan',actor,delivery_id=c.delivery_id))+1,plan_digest='pending',
            context_digest=c.context_digest,input_digest=c.input_digest,expected_state_version=c.state.record_version,prior_commitment_id=c.state.current_commitment_id,
            selected_option=option.id,quantity=option.quantity,committed_at=option.proposed_at,date_semantics=c.request.date_semantics,destination=c.request.destination,
            analysis=a,owner=c.request.commitment_owner,permitted_actions=['record_delivery_commitment','link_delivery_plan'],
            assumptions=['No reallocation or held-material release','No shipment or customer acceptance recorded','Customer agreement remains source-recorded and separate'],
            workflow_run_id=body.workflow_run_id,workflow_case_id=body.workflow_case_id).model_dump(mode='json')
        value['plan_digest']=plan_digest(value)
        return store.insert('erp.commitment_plan',value),{'delivery_id':c.delivery_id,'commitment_changed':False}
    return mutate(request,body,'delivery_plan','automation','create_commitment_plan','erp.commitment_plan',execute)


def checked_plan(store,actor,plan_id,request,*,owned_commitment=False):
    p=store.get('erp.commitment_plan',plan_id,actor);attributed(request,{'program_id':p['program_id'],'change_id':p['delivery_id']})
    c=context(store,actor,p['delivery_id'])
    valid=p['plan_digest']==plan_digest(p) and p['input_digest']==c.input_digest and p['analysis']==analyze(c).model_dump(mode='json')
    exact=p['context_digest']==c.context_digest
    if owned_commitment and c.commitment:
        exact=exact or (c.commitment.plan_id==p['id'] and c.commitment.plan_digest==p['plan_digest'] and
            c.state.record_version==p['expected_state_version']+1 and c.commitment.supersedes_commitment_id==p['prior_commitment_id'])
    fail(valid and exact,409,'STALE_SOURCE','Exact current source plan required; unrelated changes are not owned transitions.')
    fail(analyze(c).proposal_allowed,409,'DELIVERY_NOT_READY','Delivery gates changed.')
    return p,c


@router.post('/erp/commitment-decisions',response_model=CommitmentDecision,status_code=201,operation_id='record_commitment_decision')
def review(body:RecoveryReviewInput,request:Request):
    def execute(store,actor,payload):
        p,c=checked_plan(store,actor,body.plan_id,request)
        fail((p['plan_version'],p['plan_digest'])==(body.expected_plan_version,body.expected_plan_digest),409,'STALE_PLAN','Review exact quantity/date and version.')
        duplicate(store.list('erp.commitment_decision',actor,plan_id=p['id']),decision=body.decision)
        return store.insert('erp.commitment_decision',{**meta(store,actor,'erp','commitment-decision'),'delivery_id':c.delivery_id,
            'plan_id':p['id'],'plan_version':p['plan_version'],'plan_digest':p['plan_digest'],'context_digest':p['context_digest'],
            'signer_identity':actor.id,'signer_role':actor.role,'decision':body.decision,'comment':body.comment}),{'delivery_id':c.delivery_id}
    return mutate(request,body,'delivery_decision','program_owner','record_commitment_decision','erp.commitment_decision',execute)


def approved(store,actor,body,request,*,owned=False):
    p,c=checked_plan(store,actor,body.plan_id,request,owned_commitment=owned)
    d=store.get('erp.commitment_decision',body.decision_id,actor)
    fail(d['decision']=='approve' and d['signer_role']==p['required_role'] and d['signer_identity']=='demo-program-owner'
        and d['plan_id']==p['id'] and d['plan_version']==p['plan_version'] and d['plan_digest']==body.expected_plan_digest==p['plan_digest']
        and d['context_digest']==p['context_digest'] and d['delivery_id']==c.delivery_id,409,'APPROVAL_REQUIRED','Exact source-recorded Program Owner decision required.')
    return p,c,d


@router.post('/erp/delivery-commitments',response_model=DeliveryCommitment,status_code=201,operation_id='record_delivery_commitment')
def commit(body:DeliveryExecuteInput,request:Request):
    def execute(store,actor,payload):
        p,c,d=approved(store,actor,body,request,owned=True)
        duplicate(store.list('erp.delivery_commitment',actor,plan_id=p['id']))
        fail(c.state.record_version==p['expected_state_version'] and c.state.current_commitment_id==p['prior_commitment_id'],409,'STALE_SOURCE','Commercial state changed.')
        record=store.insert('erp.delivery_commitment',{**meta(store,actor,'erp','delivery-commitment'),'delivery_id':c.delivery_id,
            'order_id':p['order_id'],'line_id':p['line_id'],'plan_id':p['id'],'decision_id':d['id'],'plan_digest':p['plan_digest'],
            'quantity':p['quantity'],'committed_at':p['committed_at'],'date_semantics':p['date_semantics'],'destination':p['destination'],
            'remaining_uncommitted_quantity':c.request.quantity-p['quantity'],'customer_agreement':c.request.customer_agreement,'supersedes_commitment_id':p['prior_commitment_id']})
        store.update('erp.delivery_state',c.state.id,{'current_commitment_id':record['id'],'record_version':c.state.record_version+1},expected={'record_version':p['expected_state_version']})
        return record,{'delivery_id':c.delivery_id,'allocation_changed':False,'customer_acceptance_changed':False}
    return mutate(request,body,'delivery_commitment','automation','record_delivery_commitment','erp.delivery_commitment',execute)


@router.post('/programs/delivery-links',response_model=DeliveryLink,status_code=201,operation_id='link_delivery_plan')
def link(body:DeliveryExecuteInput,request:Request):
    def execute(store,actor,payload):
        p,c,d=approved(store,actor,body,request,owned=True)
        commitment=c.commitment
        fail(commitment is not None and commitment.plan_id==p['id'] and commitment.decision_id==d['id'],409,'COMMITMENT_REQUIRED','Read the exact ERP commitment before Planner linkage.')
        fail((commitment.quantity,commitment.committed_at,commitment.date_semantics,commitment.destination)==(p['quantity'],p['committed_at'],p['date_semantics'],p['destination']),409,'VERIFICATION_MISMATCH','ERP commitment differs from approved plan.')
        duplicate(store.list('planner.delivery_link',actor,plan_id=p['id']))
        return store.insert('planner.delivery_link',{**meta(store,actor,'planner','delivery-link'),'delivery_id':c.delivery_id,'order_id':p['order_id'],
            'milestone_id':p['milestone_id'],'plan_id':p['id'],'decision_id':d['id'],'commitment_id':commitment.id,'plan_digest':p['plan_digest'],
            'quantity':p['quantity'],'committed_at':p['committed_at'],'date_semantics':p['date_semantics'],'remaining_uncommitted_quantity':commitment.remaining_uncommitted_quantity,
            'owner':p['owner'],'customer_agreement':commitment.customer_agreement}),{'delivery_id':c.delivery_id,'baseline_changed':False}
    return mutate(request,body,'delivery_link','automation','link_delivery_plan','planner.delivery_link',execute)
