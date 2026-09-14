"""Eighteen additive critical delivery checks; actual HTTP/MCP, no paid models."""
import json
from .models import CaseResult,Check
from coordinator.evals.phase08_4c.probe import environment,investigate,post
from coordinator.evals.phase08_4c.fixtures import mutate
from program_coordinator.sources import validate_assessment
from program_coordinator.controls import HarnessError
from program_coordinator.application.execution_models import SourceFailure

CASES=(('supply_math','factual_correctness'),('held_excluded','factual_correctness'),
 ('allocated_excluded','factual_correctness'),('wrong_configuration','applicability'),
 ('technical_blocker','applicability'),('conditional_future','uncertainty'),
 ('no_autonomous_commitment','governance'),('exact_owner','governance'),
 ('no_reallocation','governance'),('stale_proposal','governance'),
 ('partial_completion','execution_truthfulness'),('independent_readback','execution_truthfulness'),
 ('missing_date','uncertainty'),('missing_quantity','uncertainty'),
 ('no_double_count','factual_correctness'),('acceptance_separate','governance'),
 ('quality_dependency','evidence_grounding'),('engineering_dependency','evidence_grounding'))

def delivery_ids():return ['delivery_'+name for name,_ in CASES]

def run_delivery(directory):
    seen={};observations=[]
    # A failed probe remains in the denominator; independent variants still run.
    for variant in ('base','wrong_configuration','technical_blocked','technical_complete','future_conditional','missing_date','missing_quantity','duplicate_inventory','held_released','stale_proposal'):
        try:
            with environment(directory/variant,variant) as env:
                client,host,double,settings=env;before=host.delivery.context().model_dump(mode='json');s=investigate(env);a=s['context']['analysis']
                complete=s['runs'][0]['status']=='completed'
                assert complete,'Analysis incomplete'
                if variant=='base':
                    p=s['progress'][0];ref={k:p[k] for k in ('run_id','plan_id','plan_version','plan_digest')}
                    records=host.delivery.records();assert not records.commitments
                    denied=post(client,'delivery-commitment/review',{**ref,'decision':'approve'},'automation')
                    premature=post(client,'delivery-commitment/execute',ref)
                    approved=post(client,'delivery-commitment/review',{**ref,'decision':'approve'},'program_owner')
                    link=host.source.delivery_link
                    def failed(body,key):raise SourceFailure('SOURCE_WRITE_REJECTED')
                    host.source.delivery_link=failed
                    execution=post(client,'delivery-commitment/execute',ref);partial=host.delivery.load(ref['run_id'])
                    erp=host.delivery.records().commitments
                    host.source.delivery_link=link
                    retry=post(client,'delivery-commitment/execute',ref);after=host.delivery.context();records=host.delivery.records()
                    h=double.harnesses[0];assessment=h.state.completed_assessments[0].assessment
                    forged=assessment.model_copy(update={'delivery':assessment.delivery.model_copy(update={'eligible_quantity':1000})})
                    rejects=False
                    try:validate_assessment(forged,h.sources,None)
                    except HarnessError:rejects=True
                    seen.update(supply_math=(a['physical_total'],a['eligible_quantity'],a['requested_quantity'],a['gap_quantity'])==(1000,600,800,200) and rejects,
                        held_excluded=a['held_quantity']==250 and a['eligible_quantity']==600,
                        allocated_excluded=a['allocated_quantity']==150 and a['eligible_quantity']==600,
                        no_autonomous_commitment=denied.status_code==403 and premature.status_code==409,
                        exact_owner=approved.status_code==200 and records.decisions[0].signer_identity=='demo-program-owner',
                        no_reallocation=[v.model_dump(mode='json') for v in after.allocations]==before['allocations'] and not records.commitments[0].allocation_changed and not next(o for o in a['options'] if o['id']=='allocation_review')['executable'],
                        partial_completion=execution.status_code!=200 and partial.status=='partial_completion' and partial.steps['erp'].status=='verified' and len(erp)==1,
                        independent_readback=retry.status_code==200 and retry.json()['status']=='verified' and len(records.commitments)==len(records.links)==1 and records.commitments[0].quantity==records.links[0].quantity==600,
                        acceptance_separate=records.commitments[0].customer_agreement=='pending' and records.commitments[0].remaining_uncommitted_quantity==200 and records.commitments[0].delivered_quantity==0,
                        quality_dependency=[v.model_dump(mode='json') for v in after.material]==before['material'] and after.lots==before['lots'] and a['held_quantity']==250)
                elif variant=='wrong_configuration':seen[variant]=a['configuration_mismatch_quantity']==600 and a['eligible_quantity']==0 and not s['records']['plans']
                elif variant=='technical_blocked':seen['technical_blocker']=a['technical_readiness']=='BLOCKED' and a['eligible_quantity']==600 and a['customer_ready_quantity']==0 and not s['records']['plans']
                elif variant=='technical_complete':seen['engineering_dependency']=a['technical_readiness']=='READY' and a['customer_ready_quantity']==600 and host.delivery.context().technical_dependency==before['technical_dependency']
                elif variant=='future_conditional':
                    option=next(o for o in a['options'] if o['id']=='future_supply')
                    seen['conditional_future']=a['future_expected_quantity']==300 and a['eligible_quantity']==600 and not option['executable'] and option['date_semantics']=='expected_material'
                elif variant in ('missing_date','missing_quantity'):seen[variant]=not a['proposal_allowed'] and not s['records']['plans']
                elif variant=='duplicate_inventory':seen['no_double_count']=not a['inventory_consistent'] and a['eligible_quantity']==0 and not s['records']['plans']
                elif variant=='held_released':seen['quality_dependency']=seen.get('quality_dependency',False) and a['eligible_quantity']==800 and a['held_quantity']==0
                elif variant=='stale_proposal':
                    p=s['progress'][0];ref={k:p[k] for k in ('run_id','plan_id','plan_version','plan_digest')}
                    assert post(client,'delivery-commitment/review',{**ref,'decision':'approve'},'program_owner').status_code==200
                    mutate(settings,lambda store:store.update('erp.delivery_state','STATE-DR-009',{'record_version':2}))
                    seen['stale_proposal']=post(client,'delivery-commitment/execute',ref).status_code==409 and not host.delivery.records().commitments
                observations.append({'variant':variant,'mode':'scripted HTTP/MCP integration; deterministic SDK responses','state':s})
        except Exception as exc:observations.append({'variant':variant,'error_code':type(exc).__name__,'detail':str(exc)[:250]})
    results=[]
    for name,dimension in CASES:
        passed=bool(seen.get(name,False));code='delivery_'+name+'_violation'
        results.append(CaseResult(case_id='delivery_'+name,title='Connected delivery: '+name.replace('_',' '),workflow_type='delivery_readiness',scenario_family='delivery_readiness',mode='runtime_probe',severity='critical',checks=[Check(dimension=dimension,description='Observed source and governed host actions satisfy the delivery invariant',passed=passed,critical_code=code)],passed=passed,critical_failures=[] if passed else [code]))
    (directory/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    return results
