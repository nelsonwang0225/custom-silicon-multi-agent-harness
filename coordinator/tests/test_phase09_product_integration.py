"""Cross-workflow scripted integration: real local HTTP/MCP, no paid model."""
from pathlib import Path
import time
import pytest
from coordinator.tests.test_phase09_demo_reset import connected,reset,run_case,execute
from coordinator.evals.phase08_5.probe import post
from coordinator.evals.phase08_4c.fixtures import mutate
from program_coordinator.control_host.concierge_reads import grounded_cards,resolve
from program_coordinator.application.execution_models import SourceFailure,SourceReadFailure

@pytest.fixture
def product(tmp_path):
    with connected(tmp_path/'product') as env:
        assert reset(env).status_code==200
        yield env

def snap(env):
    response=env[0].get('/control-api/cases/CR-017',headers={'X-Stratos-Demo-Profile':'automation'})
    assert response.status_code==200,response.text
    return response.json()

def summaries(value):return {v['change_id']:v for v in value['case_summaries']}

def test_baseline_shared_source_scope_and_catalog(product):
    value=snap(product);cases=summaries(value)
    assert set(cases)=={'CR-017','CR-019','QE-004','DR-009'}
    assert all(c['state']=='new' and c['source_available'] for c in cases.values())
    assert not value['decision_summaries'] and cases['CR-019']['attention']=='blocker'
    assert cases['CR-019']['detail']=='Source request exists; policy eligibility has not been assessed.'
    assert value['standard']['eligibility'] is None
    q=value['quality']['context'];d=value['delivery']['context']
    held_q=next(m for m in q['material'] if m['id']=='MAT-B-204')
    held_d=next(m for m in d['material'] if m['id']=='MAT-B-204')
    assert held_q==held_d and held_d['held_quantity']==250 and held_d['eligible_unallocated_quantity']==0
    assert d['analysis']['eligible_quantity']==600 and d['analysis']['gap_quantity']==200
    dep=next(v for v in value['dependencies'] if v['kind']=='technical')
    assert dep['from_case'] is None and 'REQ-042-V1' in dep['source_ids'] and 'separate obligation' in dep['detail']
    assert next(v for v in value['dependencies'] if v['kind']=='supply')['from_case']=='QE-004'
    for workflow in ('requirement_change_analysis','standard_change','yield_exception_recovery','delivery_readiness'):
        assert next(w for w in value['workflows'] if w['workflow_id']==workflow)['mode']=='Connected'
    assert all(not a['background_execution_enabled'] for a in value['automations'])


def test_all_four_cases_have_current_semantics_exact_decisions_and_operations(product):
    values={case:run_case(product,case) for case in ('CR-019','QE-004','DR-009','CR-017')}
    value=snap(product);cases=summaries(value)
    assert cases['CR-019']['state']=='waiting_external' and cases['CR-019']['attention']=='none'
    assert all(cases[c]['state']=='needs_review' for c in ('CR-017','QE-004','DR-009'))
    ds=value['decision_summaries'];assert len(ds)==3 and all(d['requires_human'] and d['current'] for d in ds)
    assert all(d['change_id']!='CR-019' and d['version']>=1 and len(d['digest'])==64 for d in ds)
    for case in ('QE-004','DR-009','CR-017'):execute(product,case,values[case])
    value=snap(product);cases=summaries(value)
    assert all(c['state']=='waiting_external' for c in cases.values())
    assert not any(d['requires_human'] for d in value['decision_summaries'])
    assert all(d['reviewer'] and d['source_decision_id'] and d['status']=='executed' for d in value['decision_summaries'])
    assert '200 gap' in cases['DR-009']['detail'] and 'held material' in cases['QE-004']['detail']
    operations=product[0].get('/control-api/operations', headers={'X-Stratos-Demo-Profile':'automation'}).json()
    assert {r['case_id'] for r in operations['runs']}==set(cases)
    for r in operations['runs']:
        detail=product[0].get('/control-api/operations/runs/'+r['run_id'], headers={'X-Stratos-Demo-Profile':'automation'}).json()
        assert r['current_case_state']==cases[r['case_id']]['state']
        assert detail['run']['current_case_state']==r['current_case_state']
        assert detail['run']['case_id']==r['case_id'] and detail['evidence'] and detail['actions']
        assert detail['run']['business_outcome']==r['business_outcome']
        for link in detail['links']:
            if link['label']=='View exact proposal':
                assert '?digest=' in link['href']
                assert resolve(product[1],link['href'])['case_id']=='CR-017'
    before=product[1].snapshot()
    for case in cases:
        card=grounded_cards(product[1],before,case,'status')[0]
        assert dict(card.facts)['Current case state']==cases[case]['state']
        assert dict(card.facts)['Current source']==cases[case]['detail']
    assert reset(product).status_code==200
    reset_state=snap(product)
    assert not reset_state['decision_summaries']
    assert all(c['state']=='new' for c in reset_state['case_summaries'])
    assert not product[0].get('/control-api/operations', headers={'X-Stratos-Demo-Profile':'automation'}).json()['runs']


def test_complete_material_flow_keeps_v1_delivery_independent_then_v2_dependency(product):
    client,host,settings,_=product
    execute(product,'CR-017',run_case(product,'CR-017'))
    job=host.source.read.get_validation_jobs(change_id='CR-017')['items'][0]
    r=host.source._http.post(host.source.config.base_url+'/api/v1/validation/jobs/'+job['id']+'/synthetic-result',
        headers={'Authorization':'Bearer demo-lab-local-only','Idempotency-Key':'phase09_result'},json={'expected_plan_digest':job['plan_digest']})
    assert r.status_code==201,r.text
    v=snap(product);assert summaries(v)['CR-017']['state']=='waiting_external'
    evidence=v['downstream']['physical']['evidence_digest']
    r=post(client,'cases/CR-017/assess-validation-result',{'expected_evidence_digest':evidence})
    assert r.status_code==202,r.text
    for _ in range(500):
        if not host.tasks:break
        time.sleep(.02)
    v=snap(product)
    assert summaries(v)['CR-017']['state']=='needs_review'
    ready=[d for d in v['decision_summaries'] if d['requires_human']]
    assert len(ready)==1 and ready[0]['kind']=='engineering_evidence'
    assert ready[0]['version'] is None and ready[0]['digest']==evidence
    review={'expected_evidence_digest':evidence,'decision':'approve','comment':'Exact engineering evidence reviewed in scripted integration.'}
    assert post(client,'cases/CR-017/evidence-review',review,'engineer').status_code==200
    v=snap(product)
    assert summaries(v)['CR-017']['state']=='completed_technical'
    assert summaries(v)['CR-017']['attention']=='none'
    assert v['downstream']['physical']['customer_acceptance']=='pending'
    assert not any(d['requires_human'] for d in v['decision_summaries'])
    assert v['delivery']['context']['analysis']['technical_readiness']=='READY'
    mutate(settings,lambda s:s.update('erp.delivery_request','DR-009',{'technical_change_id':'CR-017','requirement_revision_id':'REQ-042-V2','content_version':2}))
    v=snap(product);dep=next(d for d in v['dependencies'] if d['kind']=='technical')
    assert dep['from_case']=='CR-017' and 'REQ-042-V2' in dep['source_ids']
    assert v['delivery']['context']['analysis']['technical_readiness']=='READY'
    mutate(settings,lambda s:s.update('engineering.criteria','CRIT-BASE-V1',{'content_version':2}))
    v=snap(product)
    assert summaries(v)['CR-017']['state'] in {'stale','escalated'}
    assert v['delivery']['context']['analysis']['technical_readiness']!='READY'


@pytest.mark.parametrize('case,method,prefix',[('QE-004','quality_execute','quality-recovery'),('DR-009','delivery_link','delivery-commitment')])
def test_partial_failure_exposes_verified_first_step_and_pending_second(product,monkeypatch,case,method,prefix):
    v=run_case(product,case);p=v['progress'][0]
    ref={k:p[k] for k in ('run_id','plan_id','plan_version','plan_digest')}
    assert post(product[0],prefix+'/review',{**ref,'decision':'approve','comment':'Bounded metadata only'},'program_owner').status_code==200
    def fail(*args):raise SourceFailure('SOURCE_WRITE_REJECTED')
    with monkeypatch.context() as m:
        m.setattr(product[1].source,method,fail)
        assert post(product[0],prefix+'/execute',ref,'program_owner').status_code in (409,502,503)
        state=snap(product);assert summaries(state)[case]['state']=='partial_failure'
        detail=product[0].get('/control-api/operations/runs/'+p['run_id'], headers={'X-Stratos-Demo-Profile':'automation'}).json()
        assert any(a['source_id'] and a['verification']=='Verified' for a in detail['actions'])
        assert any(a['verification']!='Verified' for a in detail['actions'])
    assert post(product[0],prefix+'/execute',ref,'program_owner').status_code==200
    assert summaries(snap(product))[case]['state']=='waiting_external'


def test_stale_source_cannot_remain_reviewable_or_current(product,monkeypatch):
    run_case(product,'DR-009')
    mutate(product[2],lambda s:s.update('manufacturing.quality_material','MAT-B-203',{'eligible_unallocated_quantity':500,'content_version':2}))
    value=snap(product)
    assert summaries(value)['DR-009']['state']=='stale'
    assert not any(d['requires_human'] for d in value['decision_summaries'])
    def unavailable(*args):raise SourceReadFailure('SOURCE_READ_FAILED')
    monkeypatch.setattr(product[1].delivery,'context',unavailable)
    value=snap(product)
    assert summaries(value)['DR-009']['state']=='unavailable'
    assert all(d['status']=='unavailable' for d in value['decision_summaries'] if d['change_id']=='DR-009')


def test_historical_applicable_evidence_is_not_a_hardcoded_gap(product):
    def add(store):
        row=dict(store.get('validation.result','RES-SHORT-B'))
        row.update(id='RES-PRODUCT-COVERED',actual_suite_minutes=480,
            observed_minutes_by_context_bin={'32768':160,'65536':160,'131072':160})
        store.insert('validation.result',row)
    mutate(product[2],add)
    assert product[1].source.read.get_validation_coverage('CR-017')['coverage_satisfied']
    case=summaries(snap(product))['CR-017']
    assert 'evidence available' in case['detail'] and 'evidence gap' not in case['detail']
    assert case['state']!='completed_technical' and not case['decision_ids']


def test_verified_standard_intake_remains_historical_when_policy_changes(product):
    run_case(product,'CR-019')
    mutate(product[2],lambda s:s.update('engineering.criteria','CRIT-BASE-V1',{'content_version':2}))
    value=snap(product);case=summaries(value)['CR-019']
    assert value['standard']['handoffs'][0]['status']=='handoff_verified'
    assert case['state']=='stale' and case['attention']=='stale'
    assert not any(d['change_id']=='CR-019' for d in value['decision_summaries'])
