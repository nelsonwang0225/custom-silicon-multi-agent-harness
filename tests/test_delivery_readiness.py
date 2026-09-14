"""Delivery source boundaries, deterministic math and exact multi-system writes."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from mock_enterprise.config import Settings
from mock_enterprise.seed import initialize
from mock_enterprise.delivery_upgrade import install
from mock_enterprise.app import create_app

READ={'Authorization':'Bearer demo-reader-local-only'}
AUTO={'Authorization':'Bearer demo-automation-local-only'}
OWNER={'Authorization':'Bearer demo-program-owner-local-only'}

@pytest.fixture
def delivery(tmp_path):
    settings=Settings(tmp_path/'delivery.sqlite3',tmp_path,True)
    initialize(settings);install(settings)
    with TestClient(create_app(settings)) as client:yield client,settings


def context(client):
    r=client.get('/api/v1/erp/delivery-requests/DR-009/context',headers=READ)
    assert r.status_code==200,r.text
    return r.json()


def post(client,path,body,key='delivery-test',actor=AUTO):
    return client.post('/api/v1/'+path,json=body,headers={**actor,'Idempotency-Key':key})


def prepare(client):
    c=context(client)
    p=post(client,'erp/commitment-plans',dict(delivery_id='DR-009',expected_context_digest=c['context_digest'],workflow_run_id='run_delivery',workflow_case_id='case_delivery'))
    assert p.status_code==201,p.text
    return c,p.json()


def approve(client,p):
    d=post(client,'erp/commitment-decisions',dict(plan_id=p['id'],expected_plan_version=p['plan_version'],expected_plan_digest=p['plan_digest'],decision='approve',comment='Exact released quantity and confirmed arrival; no reallocation.'),actor=OWNER)
    assert d.status_code==201,d.text
    return dict(plan_id=p['id'],decision_id=d.json()['id'],expected_plan_digest=p['plan_digest'])


def test_base_math_dates_and_source_ownership(delivery):
    client,_=delivery;c=context(client);a=c['analysis']
    assert (a['physical_total'],a['held_quantity'],a['allocated_quantity'],a['eligible_quantity'],a['requested_quantity'],a['gap_quantity'])==(1000,250,150,600,800,200)
    assert a['technical_readiness']=='READY',a
    assert a['earliest_ship_at']=='2026-11-18T09:00:00Z'
    assert a['earliest_arrival_at']=='2026-11-20T09:00:00Z'
    assert a['proposed_at']=='2026-11-23T18:00:00Z'
    assert a['proposal_allowed'] and not a['full_request_supportable']
    assert [o['id'] for o in a['options']]==['partial_commitment','allocation_review']
    assert a['options'][1]['remaining_gap']==50 and not a['options'][1]['executable']
    assert c['request']['owning_system']=='erp' and c['clearance']['owning_system']=='engineering'
    quality=client.get('/api/v1/manufacturing/quality-exceptions/QE-004/context',headers=READ).json()
    assert next(m for m in c['material'] if m['id']=='MAT-B-204')==quality['material'][0]


def test_exact_commitment_planner_readback_and_replay(delivery):
    client,_=delivery;c,p=prepare(client);body=approve(client,p)
    absent=post(client,'programs/delivery-links',body)
    assert absent.status_code==409
    result=post(client,'erp/delivery-commitments',body)
    assert result.status_code==201,result.text
    assert post(client,'erp/delivery-commitments',body).json()==result.json()
    assert post(client,'erp/delivery-commitments',body,key='other').status_code==409
    link=post(client,'programs/delivery-links',body)
    assert link.status_code==201,link.text
    assert post(client,'programs/delivery-links',body).json()==link.json()
    after=context(client)
    assert after['input_digest']==c['input_digest'] and after['context_digest']!=c['context_digest']
    assert after['state']['record_version']==2
    assert after['commitment']['quantity']==600 and after['commitment']['remaining_uncommitted_quantity']==200
    assert after['commitment']['customer_agreement']=='pending' and after['commitment']['delivered_quantity']==0
    assert link.json()['commitment_id']==result.json()['id']
    for key in ('material','lots','allocations','order','milestone','evidence','clearance'):assert after[key]==c[key]
    events=client.get('/api/v1/audit/events?change_id=DR-009',headers=READ)
    assert events.status_code==200,events.text


@pytest.mark.parametrize('role',['reader','automation','engineer','portfolio-engineer'])
def test_wrong_role_cannot_approve(delivery,role):
    client,_=delivery;c,p=prepare(client)
    r=post(client,'erp/commitment-decisions',dict(plan_id=p['id'],expected_plan_version=1,expected_plan_digest=p['plan_digest'],decision='approve',comment=''),actor={'Authorization':f'Bearer demo-{role}-local-only'})
    assert r.status_code==403


def test_no_self_approval_or_arbitrary_source_changes(delivery):
    client,_=delivery;c,p=prepare(client)
    r=post(client,'erp/delivery-commitments',dict(plan_id=p['id'],decision_id='fake',expected_plan_digest=p['plan_digest']))
    assert r.status_code in (404,409)
    for path in ['manufacturing/lots/LOT-B-204/release','erp/allocations/ALLOC-HEL-150','erp/orders/ORD-HEL-800','validation/results/RES-BASELINE-B']:
        assert post(client,path,{}).status_code in (404,405)
    r=post(client,'erp/commitment-plans',dict(delivery_id='DR-009',expected_context_digest=c['context_digest'],workflow_run_id='run_x',workflow_case_id='case_x',selected_option='allocation_review'))
    assert r.status_code==422

@pytest.mark.parametrize('variant,technical,eligible,gap,allowed',[
    ('base','READY',600,200,True),('technical_blocked','BLOCKED',600,200,False),
    ('technical_complete','READY',600,200,True),('future_conditional','READY',600,200,True),
    ('wrong_configuration','READY',0,800,False),('held_released','READY',800,0,True),
    ('requested_600','READY',600,0,True),('missing_date','READY',600,200,False),
    ('missing_quantity','READY',600,None,False),('missing_logistics','READY',600,200,False),
    ('duplicate_inventory','READY',0,800,False)])
def test_source_variants(tmp_path,variant,technical,eligible,gap,allowed):
    from coordinator.evals.phase08_4c.fixtures import prepare as variant_prepare
    settings=Settings(tmp_path/'source.sqlite3',tmp_path,True);variant_prepare(settings,variant)
    with TestClient(create_app(settings)) as client:
        c=context(client);a=c['analysis']
        assert (a['technical_readiness'],a['eligible_quantity'],a['gap_quantity'],a['proposal_allowed'])==(technical,eligible,gap,allowed),a
        if variant=='technical_blocked':
            assert a['customer_ready_quantity']==0 and c['technical_dependency']['change']['id']=='CR-017'
            assert c['evidence']==[] and c['clearance'] is None
        if variant=='technical_complete':
            physical=c['technical_dependency']['physical']
            assert c['clearance'] is None and c['evidence'][0]['id']==physical['result']['id']
            assert c['evidence'][0]['workload_profile_id']=='WF-LC-V2'
            assert physical['current_review']['evidence_digest']==physical['evidence_digest']
            assert 'current_sources' not in physical['evidence_binding']
        if variant=='future_conditional':
            assert a['future_expected_quantity']==300
            assert not next(o for o in a['options'] if o['id']=='future_supply')['executable']
        if variant=='wrong_configuration':assert a['configuration_mismatch_quantity']==600
        if variant in ('missing_date','missing_logistics'):assert a['proposed_at'] is None
        if not allowed:
            p=post(client,'erp/commitment-plans',dict(delivery_id='DR-009',expected_context_digest=c['context_digest'],workflow_run_id='run_x',workflow_case_id='case_x'))
            assert p.status_code==409,p.text


@pytest.mark.parametrize('target',['inventory','technical','commercial','logistics','request'])
def test_stale_exact_plan_rejected(delivery,target):
    from coordinator.evals.phase08_4c.fixtures import mutate
    client,settings=delivery;c,p=prepare(client);body=approve(client,p)
    def change(store):
        if target=='inventory':store.update('manufacturing.quality_material','MAT-B-203',{'eligible_unallocated_quantity':500,'content_version':2})
        if target=='technical':store.update('engineering.delivery_clearance','CLEAR-HEL-BASE',{'status':'pending','content_version':2})
        if target=='commercial':store.update('erp.delivery_state','STATE-DR-009',{'record_version':2})
        if target=='logistics':store.update('planner.delivery_logistics','LOG-HEL-800',{'transit_minutes':6000,'content_version':2})
        if target=='request':store.update('erp.delivery_request','DR-009',{'requested_at':'2026-11-24T18:00:00Z','content_version':2})
    mutate(settings,change)
    assert post(client,'erp/delivery-commitments',body).status_code==409
    assert context(client)['commitment'] is None


def test_rejected_tampered_and_cross_scope_actions(delivery):
    client,_=delivery;c,p=prepare(client)
    d=post(client,'erp/commitment-decisions',dict(plan_id=p['id'],expected_plan_version=p['plan_version'],expected_plan_digest=p['plan_digest'],decision='reject',comment='Not agreed.'),actor=OWNER)
    assert d.status_code==201
    body=dict(plan_id=p['id'],decision_id=d.json()['id'],expected_plan_digest=p['plan_digest'])
    assert post(client,'erp/delivery-commitments',body).status_code==409
    assert post(client,'erp/delivery-commitments',{**body,'quantity':800}).status_code==422
    assert client.get('/api/v1/erp/delivery-requests/DR-OTHER/context',headers=READ).status_code==404
    assert context(client)['commitment'] is None


def test_source_client_reads_exact_contract(delivery):
    import httpx
    from enterprise_api.client import EnterpriseClient
    from enterprise_api.config import ClientConfig,Scope
    from enterprise_api.transport import HttpxReadTransport
    client,_=delivery
    config=ClientConfig(base_url='http://127.0.0.1:8000',scope=Scope(customer_id='CUST-FML01',program_id='PRG-A17'))
    from enterprise_api.transport import ReadResponse
    class Transport:
        def get(self,path,params):
            r=client.get(path,params=params,headers=READ)
            return ReadResponse(status=r.status_code,body=r.json(),attempts=1,request_id=r.headers.get("x-request-id"),correlation_id=r.headers.get("x-correlation-id"))
        def close(self):pass
    reader=EnterpriseClient(config,transport=Transport())
    assert reader.get_delivery_context('DR-009')==context(client)
    assert reader.get_delivery_records('DR-009')['commitments']==[]
