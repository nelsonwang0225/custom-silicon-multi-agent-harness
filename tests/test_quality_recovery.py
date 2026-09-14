import copy
import pytest
from enterprise_api.quality_models import QualityContext
from enterprise_api.quality_policy import analyze
from mock_enterprise.quality_upgrade import install, extension
from mock_enterprise.db import connect, Store
from conftest import get, post, AUTOMATION, ENGINEER, READER
OWNER={'Authorization':'Bearer demo-program-owner-local-only'}
SUBMISSION='1'*64
RECOMMENDATION='Contain LOT-B-204; investigate SITE-2; execute controlled recovery; protect MS-HEL-800.'
BUSINESS_CONTEXT='The 16 percentage-point yield drop represents $1.4M of synthetic potential shipment value exposure.'

@pytest.fixture
def quality(tmp_path):
    from mock_enterprise.config import Settings
    from mock_enterprise.seed import initialize
    from mock_enterprise.app import create_app
    from fastapi.testclient import TestClient
    settings=Settings(tmp_path/'demo.sqlite3',tmp_path,True)
    initialize(settings);install(settings);install(settings)
    with TestClient(create_app(settings)) as client: yield client,settings

def context(client):return get(client,'/manufacturing/quality-exceptions/QE-004/context')
def records(client):return get(client,'/manufacturing/quality-exceptions/QE-004/records')
def intent(client):return dict(exception_id='QE-004',expected_context_digest=context(client)['context_digest'],workflow_run_id='run-qe',workflow_case_id='case-qe')
def prepare(client):
    body=intent(client)
    a=post(client,'/manufacturing/quality-investigations',body,'investigate');assert a.status_code==201,a.text
    b=post(client,'/manufacturing/recovery-plans',body,'plan');assert b.status_code==201,b.text
    return a.json(),b.json()
def review(client,p,role=OWNER,decision='approve'):
    return post(client,'/manufacturing/recovery-decisions',dict(plan_id=p['id'],expected_plan_version=p['plan_version'],expected_plan_digest=p['plan_digest'],decision=decision,comment='Program owner recovery planning decision',submission_digest=SUBMISSION,recommendation=RECOMMENDATION,business_context=BUSINESS_CONTEXT),'review',role)

def test_primary_quality_http(quality):
    client,settings=quality;c=context(client);a=analyze(QualityContext.model_validate(c))
    assert (a.comparable,a.observed_rate_bps,a.baseline_rate_bps)==('true',8000,9600)
    assert (a.affected_physical_quantity,a.first_pass_pass_quantity,a.affected_eligible_quantity,a.held_quantity)==(250,200,0,250)
    assert (a.eligible_quantity,a.requested_quantity,a.gap_quantity)==(600,800,200)
    assert (a.first_pass_shortfall_quantity,a.first_pass_shortfall_value_cents)==(40,140_000_000)
    assert (a.held_value_exposure_cents,a.gap_value_exposure_cents)==(875_000_000,700_000_000)
    assert a.root_cause is None and a.failed_by_site=={'SITE-1':5,'SITE-2':45}
    investigation,p=prepare(client)
    for role in (AUTOMATION,ENGINEER,READER):assert review(client,p,role).status_code==403
    d=review(client,p);assert d.status_code==201,d.text
    b=dict(plan_id=p['id'],decision_id=d.json()['id'],expected_plan_digest=p['plan_digest'],expected_submission_digest=SUBMISSION)
    for key in ['execute','execute']:
        r=post(client,'/programs/recovery-tasks',b,key);assert r.status_code==201,r.text
    assert post(client,'/programs/recovery-tasks',b,'another').status_code==409
    read=records(client)
    assert [len(read[k]) for k in ('investigations','plans','decisions','tasks')]==[1,1,1,1]
    assert read['investigations'][0]==investigation
    assert read['tasks'][0]['allocation_changed'] is False
    assert read['tasks'][0]['approved_recommendation']==RECOMMENDATION
    assert {item['id'] for item in read['tasks'][0]['workstreams']}=={'containment','site_investigation','controlled_recovery','supply_protection'}
    assert context(client)==c
    assert read['tasks'][0]['commitment_changed'] is False

@pytest.mark.parametrize('field,value,expected',[
 ('test_program_version','FT-B-8','false'),('configuration_content_version',2,'false'),('product_revision','REV-C','false'),('conditions_id',None,'unknown'),('configuration_id','CFG-A-01','false'),
 ('sites',['SITE-9'],'false'),('population',None,'unknown'),('equipment_family','OTHER','false'),('test_stage','wafer_test','false')])
def test_comparability_variants(quality,field,value,expected):
    c=QualityContext.model_validate(context(quality[0]));c.baseline=c.baseline.model_copy(update={field:value})
    a=analyze(c);assert a.comparable==expected and not a.confirmed_degradation
    assert a.investigation_allowed

def test_supply_variants(quality):
    c=QualityContext.model_validate(context(quality[0]));m=c.material[1]
    m.eligible_unallocated_quantity=0;m.allocated_quantity=600;m.allocation_order_id='ORD-1204'
    a=analyze(c);assert (a.eligible_quantity,a.gap_quantity)==(0,800)
    assert any(o['required_role']=='supply_owner' for o in a.options)
    c.evidence=[];assert analyze(c).evidence_status=='missing'

@pytest.mark.parametrize('path,body',[
 ('/manufacturing/lots/LOT-B-204/release',{}),('/manufacturing/lots/LOT-B-204/disposition',{'disposition':'released'}),
 ('/manufacturing/quality-investigations',{'exception_id':'QE-004','release_lot':True}),
 ('/erp/orders/ORD-HEL-800/commitment',{'quantity':600})])
def test_forbidden_actions(quality,path,body):
    assert post(quality[0],path,body,'forbidden').status_code in (404,405,422)

@pytest.mark.parametrize('mutation', ['source','version','digest','reject'])
def test_exact_recovery_governance(quality,mutation):
    client,settings=quality;_,p=prepare(client)
    if mutation=='source':
        con=connect(settings.db_path);Store(con).update('manufacturing.quality_observation','OBS-QE-004',{'content_version':2});con.close()
    if mutation=='version':p['plan_version']+=1
    if mutation=='digest':p['plan_digest']='0'*64
    response=review(client,p,decision='reject' if mutation=='reject' else 'approve')
    if mutation=='reject':
        assert response.status_code==201
        assert post(client,'/programs/recovery-tasks',dict(plan_id=p['id'],decision_id=response.json()['id'],expected_plan_digest=p['plan_digest'],expected_submission_digest=SUBMISSION),'execute').status_code==409
    else:assert response.status_code==409,response.text
    assert records(client)['tasks']==[]

def test_wrong_scope_extra_actions_and_install_idempotent(quality):
    client,settings=quality
    body=intent(client);body['exception_id']='QE-999'
    assert post(client,'/manufacturing/quality-investigations',body,'wrong').status_code==404
    body=intent(client);body['owner']='Invented owner'
    assert post(client,'/manufacturing/quality-investigations',body,'invented').status_code==422
    assert records(client)['investigations']==[]


def test_quality_client_reads_preserve_source_json(quality):
    from enterprise_api import EnterpriseClient,ClientConfig,Scope
    from enterprise_api.transport import HttpxReadTransport
    client,settings=quality
    config=ClientConfig(base_url='http://127.0.0.1:8000',scope=Scope(customer_id='CUST-FML01',program_id='PRG-A17'))
    # Use the same actual source routes; no source fixture access through the public client.
    from enterprise_api.transport import ReadResponse
    class Transport:
        def get(self,path,params):
            response=client.get(path,params=params,headers=READER)
            return ReadResponse(status=response.status_code,body=response.json(),attempts=1,request_id=response.headers.get('x-request-id'),correlation_id=response.headers.get('x-correlation-id'))
        def close(self):pass
    with EnterpriseClient(config,transport=Transport()) as api:
        assert api.get_quality_context('QE-004')==context(client)
        assert api.get_quality_records('QE-004')==records(client)
    investigation,p=prepare(client)
    events=get(client,'/audit/events?change_id=QE-004')['items']
    assert all(e['change_id']=='QE-004' for e in events)
    assert {'create_quality_investigation','create_recovery_plan'}<={e['action'] for e in events}
