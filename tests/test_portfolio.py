"""Expanded source graph + real application contracts, always isolated storage."""
import copy
import json
import time

import pytest
from fastapi.testclient import TestClient

from mock_enterprise.app import create_app
from mock_enterprise.config import Settings
from mock_enterprise.core import PORTFOLIO_SCOPES, Identity, canonical
from mock_enterprise.db import MODELS, connect, read_store
from mock_enterprise.portfolio import SCOPES
from mock_enterprise.seed import initialize, load_seed, validate_graph
from mock_enterprise.snapshots import check_live, plan_digest
from conftest import READER, AUTOMATION, ENGINEER, get, post, draft, approve, book, link_body


def headers(role='reader'):
    return {'Authorization':f'Bearer demo-portfolio-{role}-local-only'}

@pytest.fixture
def portfolio(tmp_path):
    settings=Settings(tmp_path/'portfolio.sqlite3',tmp_path,True)
    initialize(settings)
    with TestClient(create_app(settings)) as client:
        yield client,settings


def business_dump(settings):
    with read_store(settings.db_path) as s:
        return {**{k:s.list(k) for k in MODELS},'audit':[dict(r) for r in s.con.execute('SELECT * FROM audit_events ORDER BY sequence')]}


def test_counts_names_and_scope_integrity(portfolio):
    c,s=portfolio
    data=get(c,'/portfolio',headers())
    northstar=next(p for p in get(c,'/programs',headers())['items'] if p['id']=='PRG-P01')
    assert northstar['name']=='Northstar Boreal' and northstar['health']=='on_track'
    with read_store(s.db_path) as store:
        expected={'engineering.customer':9,'planner.program':11,'engineering.change':41,'engineering.requirement':82,'engineering.configuration':26,'validation.result':113,'validation.job':20,'validation.history':10,'validation.sample':53,'validation.slot':53,'manufacturing.lot':53,'manufacturing.unit':113,'erp.order':21,'planner.milestone':91,'engineering.plan':30,'engineering.decision':27,'planner.link':10,'planner.task':10}
        assert {k:len(store.list(k)) for k in expected}==expected
        assert len(data['activity'])==397
        assert sum(len(m['dependencies']) for m in data['milestones'])==191
        assert store.get('engineering.supplier','SUP-001')['name']=='STRATOS SILICON'
        assert store.get('engineering.customer','CUST-FML01')['name']=='HELIOS AI'
        text=canonical(business_dump(s)).lower()
        for forbidden in ('frontier model lab (fictional)','custom silicon co','broadcom','openai','anthropic','microsoft','google','meta platforms','apple inc'):
            assert forbidden not in text
        assert store.con.execute('PRAGMA foreign_key_check').fetchall()==[]
    assert SCOPES==PORTFOLIO_SCOPES
    assert len({c['change']['category'] for c in data['cases']})>=10
    assert {c['change']['priority'] for c in data['cases']}=={'critical','high','medium','low'}


def test_generation_and_two_guarded_resets_are_identical(portfolio):
    client,s=portfolio
    initial=business_dump(s)
    # Active lifecycle lock must still reject reset, even on isolated storage.
    with pytest.raises(ValueError,match='Stop the service'):
        initialize(s,reset=True,confirmed=True)
    client.__exit__(None,None,None)
    for _ in range(2):
        initialize(s,reset=True,confirmed=True)
        assert business_dump(s)==initial
    client.__enter__()
    r1,m1=load_seed();r2,m2=load_seed()
    assert canonical(r1)==canonical(r2) and m1==m2


@pytest.mark.parametrize('corruption',['duplicate','scope','missing','lineage','snapshot','duration','accepted_request','history'])
def test_generated_graph_rejects_corruption(corruption):
    rows,_=load_seed()
    if corruption=='duplicate': rows['engineering.change'].append(copy.deepcopy(rows['engineering.change'][-1]))
    if corruption=='scope': rows['engineering.change'][-1]['customer_id']='CUST-FML01'
    if corruption=='missing': rows['engineering.change'][-1]['configuration_id']='CFG-MISSING'
    if corruption=='lineage': rows['manufacturing.unit'][-1]['product_id']='WRONG-PRODUCT'
    if corruption=='snapshot': rows['validation.result'][-1]['configuration_snapshot']['firmware']='WRONG-FW'
    if corruption=='duration': rows['engineering.procedure'][-1]['suite_minutes']+=1
    if corruption=='accepted_request': rows['planner.milestone'][-2]['dependencies'][0]['state']='completed'
    if corruption=='history': rows['validation.history'][-1]['result_ids']=['RES-BASELINE-B']
    with pytest.raises(ValueError): validate_graph(rows)


def test_portfolio_reads_do_not_expand_legacy_scope_or_mutate(portfolio):
    c,s=portfolio;before=business_dump(s)
    assert len(get(c,'/programs',READER)['items'])==1
    assert len(get(c,'/portfolio',READER)['cases'])==1
    for path in ['/programs/PRG-P01','/engineering/changes/CR-105','/manufacturing/lots/LOT-P01-0']:
        assert c.get('/api/v1'+path,headers=READER).status_code==404
        assert c.get('/api/v1'+path,headers=headers()).status_code==200
    assert c.get('/api/v1/programs?program_id=PRG-UNLISTED',headers=headers()).status_code==404
    after=business_dump(s)
    assert {k:v for k,v in after.items() if k!='audit'}=={k:v for k,v in before.items() if k!='audit'}
    assert not c.get('/api/v1/portfolio').is_success


def test_golden_workflow_preserved_inside_portfolio(portfolio):
    c,s=portfolio
    options=get(c,'/validation/options?change_id=CR-017',headers())['items']
    assert len(options)==9
    eligible=[o for o in options if o['resource_eligible']]
    assert {(o['cost_cents'],o['timing']['deadline_slack_minutes']) for o in eligible}=={(0,-1680),(180000,1320)}
    before=business_dump(s)
    p=draft(c);a=approve(c,p);j=book(c,p,a)
    assert post(c,'/programs/PRG-A17/implementation-links',link_body(p,a,j),'gold-link').status_code==201
    after=business_dump(s)
    for kind in ['validation.result','validation.history','manufacturing.lot','manufacturing.unit','erp.order','erp.rate','engineering.criteria','engineering.requirement']:
        assert before[kind]==after[kind]
    assert get(c,'/engineering/changes/CR-017',headers())['execution_state']=='scheduled_awaiting_execution'
    assert not get(c,'/validation/coverage?change_id=CR-017')['coverage_satisfied']
    assert len([j for j in after['validation.job'] if j['change_id']=='CR-017'])==1
    assert get(c,'/erp/orders/ORD-1204')['committed_delivery_at']=='2026-11-23T18:00:00Z'


def test_seeded_plans_bind_real_scope_and_partial_followthrough(portfolio):
    c,s=portfolio
    with read_store(s.db_path) as store:
        for plan in store.list('engineering.plan'):
            assert plan_digest(plan)==plan['plan_digest']
            actor=Identity('test-reader','reader',plan['program_id'],plan['customer_id'])
            jobs=store.list('validation.job',actor,plan_id=plan['id'])
            check_live(store,actor,plan,job=jobs[0] if jobs else None)
    p=get(c,'/engineering/plans/plan-P01-2',headers())
    assert p['execution_state']=='lab_scheduled_pending_planner'
    response=post(c,'/programs/PRG-P01/implementation-links',dict(plan_id=p['id'],approval_id=p['decision_id'],job_id=p['job_id'],expected_milestone_record_version=1),'portfolio-link',headers('automation'))
    assert response.status_code==201,response.text
    assert response.json()['program_id']=='PRG-P01' and response.json()['customer_id']=='CUST-NORTH'
    assert get(c,'/engineering/plans/'+p['id'],headers())['execution_state']=='scheduled_awaiting_execution'


def test_portfolio_roles_cannot_self_approve_or_write_protected_records(portfolio):
    c,s=portfolio
    p=get(c,'/engineering/plans/plan-P03-3',headers())
    body=dict(decision='approve',expected_plan_version=p['plan_version'],expected_plan_digest=p['plan_digest'],reason='Unauthorized self approval probe')
    assert post(c,'/engineering/plans/'+p['id']+'/decisions',body,'deny',headers('automation')).status_code==403
    assert post(c,'/validation/jobs',dict(plan_id=p['id'],approval_id='decision-P01-1'),'mismatch',headers('automation')).status_code==404
    for path in ['/erp/orders/ORD-P01','/manufacturing/lots/LOT-P01-0','/validation/results/RES-P01-0','/validation/history/HJOB-P01','/engineering/acceptance-criteria/CRIT-P01']:
        assert post(c,path,{},'protected',headers('automation')).status_code==405


def test_portfolio_case_sources_are_isolated_and_coverage_varies(portfolio):
    c,s=portfolio
    options=get(c,'/validation/options?change_id=CR-105',headers())['items']
    assert len(options)==25
    assert all(o['sample']['program_id']=='PRG-P01' and o['slot']['program_id']=='PRG-P01' for o in options)
    assert any('RESOURCE_UNAVAILABLE' in o['eligibility_reasons'] for o in options)
    assert any('MANUFACTURING_RESTRICTION' in o['eligibility_reasons'] for o in options)
    assert get(c,'/validation/coverage?change_id=CR-105',headers())['coverage_satisfied']
    even=get(c,'/validation/coverage?change_id=CR-109',headers())
    assert not even['coverage_satisfied']
    reasons={reason for item in even['items'] for reason in item['mismatch_reasons']}
    assert {'WRONG_CONFIGURATION','WRONG_PRODUCT_REVISION','WRONG_PROFILE','MISSING_CONTEXT_BINS','INSUFFICIENT_DURATION','NOT_COMPLETED_PASS'} <= reasons
    start=time.monotonic();r=c.get('/api/v1/portfolio',headers=headers());elapsed=time.monotonic()-start
    assert r.status_code==200 and elapsed<5
    assert r.headers['content-encoding']=='gzip'


def test_new_portfolio_plan_uses_exact_selected_scope_and_fresh_approval(portfolio):
    c,s=portfolio
    change=get(c,'/engineering/changes/CR-115',headers())
    option=next(o for o in get(c,'/validation/options?change_id=CR-115',headers())['items'] if o['resource_eligible'])
    body=dict(expected_change_content_version=change['content_version'],target_requirement_revision_id=change['proposed_requirement_revision_id'],configuration_id=option['configuration_id'],procedure_id=option['procedure_id'],sample_id=option['sample']['id'],slot_id=option['slot']['id'],milestone_id=option['milestone_id'],assessment=dict(facts=[dict(text='Review exact Meridian integration evidence.',source_refs=[dict(resource_type='engineering.change',resource_id=change['id'])])],evidence_gaps=['Recorded observations do not close every review question.'],unresolved_questions=['Future engineering disposition remains unknown.']),expected_source_versions=option['expected_source_versions'])
    bad=copy.deepcopy(body);bad['assessment']['facts'][0]['source_refs'].append(dict(resource_type='engineering.change',resource_id='CR-017'))
    assert post(c,'/engineering/changes/CR-115/plans',bad,'cross-citation',headers('automation')).status_code==404
    r=post(c,'/engineering/changes/CR-115/plans',body,'portfolio-draft',headers('automation'))
    assert r.status_code==201,r.text
    p=r.json();assert (p['program_id'],p['customer_id'])==('PRG-P03','CUST-MERIDIAN')
    decision=dict(decision='approve',expected_plan_version=p['plan_version'],expected_plan_digest=p['plan_digest'],reason='Explicit simulated engineer integration check')
    assert post(c,'/engineering/plans/'+p['id']+'/decisions',decision,'unscoped',ENGINEER).status_code==404
    r=post(c,'/engineering/plans/'+p['id']+'/decisions',decision,'scoped-approve',headers('engineer'));assert r.status_code==201,r.text
    before=get(c,'/validation/coverage?change_id=CR-115',headers())
    r=post(c,'/validation/jobs',dict(plan_id=p['id'],approval_id=r.json()['id']),'scoped-book',headers('automation'));assert r.status_code==201,r.text
    assert r.json()['program_id']=='PRG-P03'
    assert get(c,'/validation/coverage?change_id=CR-115',headers())==before


def test_closed_change_cannot_reenter_drafting(portfolio):
    c,s=portfolio
    change=get(c,'/engineering/changes/CR-116',headers())
    assert change['workflow_state']=='closed'
    option=next(o for o in get(c,'/validation/options?change_id=CR-116',headers())['items'] if o['resource_eligible'])
    body=dict(expected_change_content_version=1,target_requirement_revision_id=change['proposed_requirement_revision_id'],configuration_id=option['configuration_id'],procedure_id=option['procedure_id'],sample_id=option['sample']['id'],slot_id=option['slot']['id'],milestone_id=option['milestone_id'],assessment=dict(facts=[dict(text='Must not reopen a closed scope',source_refs=[dict(resource_type='engineering.change',resource_id=change['id'])])],evidence_gaps=[],unresolved_questions=[]),expected_source_versions=option['expected_source_versions'])
    r=post(c,'/engineering/changes/'+change['id']+'/plans',body,'closed',headers('automation'))
    assert r.status_code==409 and r.json()['error']['code']=='CHANGE_CLOSED'
