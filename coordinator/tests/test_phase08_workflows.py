"""Phase 08.3 contracts. Offline deterministic model doubles and isolated source state."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_phase08_control_host import env, host, investigate, post, snapshot, headers
from test_phase08_downstream import execution_and_result, assess
from program_coordinator.application.automations import AutomationStore, CreateAutomation
from program_coordinator.application.demo_identity import AUTOMATION
from program_coordinator.application.workflow_catalog import workflow_catalog
from program_coordinator.application.models import WorkflowError
from program_coordinator.control_host.workflows import business_outcome


def config(**changes):
    return dict(name='Morning evidence review', workflow_id='requirement_change_analysis',
        customer_id='CUST-FML01', program_id='PRG-A17', case_scope='CR-017', authority='read_only',
        trigger={'type':'schedule','cadence':'weekdays','time':'07:00','timezone':'America/Chicago'}, **changes)


def create(client, value=None, key='create_test'):
    return post(client, 'automations', {'request_id':key, 'configuration':value or config()})


def wait_run(client, run_id):
    for _ in range(100):
        result=client.get('/control-api/runs/'+run_id, headers={'X-Stratos-Demo-Profile':'automation'})
        assert result.status_code==200,result.text
        if result.json()['run']['status']!='running':
            return result.json()
        time.sleep(.03)
    pytest.fail('Run did not complete')


def test_registry_modes_and_generated_catalog(host):
    client, service, double, _=host
    catalog=client.get('/control-api/workflows', headers={'X-Stratos-Demo-Profile':'automation'}).json()
    assert len(catalog)==13
    connected=[w for w in catalog if w['mode']=='Connected']
    assert [w['workflow_id'] for w in connected]==['requirement_change_analysis','yield_exception_recovery','delivery_readiness','standard_change']
    assert connected[3]['invocation_workflow_id']=='requirement_change_analysis' and connected[3]['authority']=='bounded_execution'
    assert connected[0]['manual_available'] and connected[0]['authority']=='read_only'
    assert not any(w['mode']=='Simulated' for w in catalog)
    assert sum(w['registry_entry'] for w in catalog)==3
    assert client.get('/control-api/workflows/no_such_workflow', headers={'X-Stratos-Demo-Profile':'automation'}).status_code==404
    generated=Path('mock_apps_ui/src/control/workflow-catalog.json')
    assert json.loads(generated.read_text())==[w.model_dump(mode='json') for w in workflow_catalog()]
    assert not service.tasks and double.calls==0


@pytest.mark.parametrize('workflow', ['yield_exception_recovery','delivery_readiness','standard_change','specification_drift','unknown'])
def test_nonconnected_never_invokes(host, workflow):
    client,service,double,_=host
    r=post(client,f'workflows/{workflow}/runs',{'invocation_id':'ui_no'})
    assert r.status_code==409 and r.json()['error']['code']=='WORKFLOW_NOT_CONNECTED'
    assert double.calls==0 and not service.tasks and not snapshot(client)['runs']


def test_manual_shared_service_replays_across_entry_points(host):
    client,service,double,_=host
    body={'invocation_id':'ui_catalog'}
    first=post(client,'workflows/requirement_change_analysis/runs',body)
    assert first.status_code==202,first.text
    replay=post(client,'cases/CR-017/investigations',body)
    assert replay.status_code==202 and replay.json()['replayed']
    assert first.json()['run_id']==replay.json()['run_id']
    assert post(client,'workflows/requirement_change_analysis/runs',{'invocation_id':'ui_other'}).status_code==409
    run=wait_run(client,first.json()['run_id'])
    assert double.calls==1 and len(snapshot(client)['runs'])==1
    assert run['run']['actor_id']=='demo-automation' and run['run']['trigger']['kind']=='manual'
    assert run['run']['status']=='completed'
    assert 'success' not in run['run']['business_outcome'].lower()
    assert run['run']['business_outcome'] in {'Waiting for review','Human review required · Proposal not recorded'}
    assert run['run']['specialists'] and run['activity']
    assert all(a['run_id']==run['run']['run_id'] for a in run['activity'])
    assert 'artifact_directory' not in run['run'] and 'request_digest' not in run['run']
    assert 'private error' not in json.dumps(run)
    assert client.get('/control-api/runs/no_such_run', headers={'X-Stratos-Demo-Profile':'automation'}).status_code==404
    assert client.get('/control-api/runs', headers={'X-Stratos-Demo-Profile':'automation'}).json()[0]['run_id']==run['run']['run_id']
    assert client.get('/control-api/workflows/requirement_change_analysis', headers={'X-Stratos-Demo-Profile':'automation'}).json()['latest_run_id']==run['run']['run_id']
    conflict=post(client,'workflows/requirement_change_analysis/runs',body,'engineer')
    assert conflict.status_code==409 and conflict.json()['error']['code']=='INVOCATION_ID_CONFLICT'


@pytest.mark.parametrize('extra',[{'program_id':'PRG-P01'},{'change_id':'CR-107'},{'change_id':'CR-018'},{'customer_id':'CUST-OTHER'},{'operation':'execute'},{'authority':'bounded_execution'},{'prompt':'arbitrary'}])
def test_manual_scope_and_closed_body(host,extra):
    client,_,double,_=host
    assert post(client,'workflows/requirement_change_analysis/runs',{'invocation_id':'ui_invalid',**extra}).status_code==422
    assert double.calls==0


@pytest.mark.parametrize('trigger',[
    {'type':'schedule','cadence':'daily','time':'12:30','timezone':'UTC','start_date':'2026-11-18'},
    {'type':'schedule','cadence':'weekly','weekday':4,'time':'07:00','timezone':'America/Chicago'},
    {'type':'source_event','system':'validation','event':'result_received'},
    {'type':'condition','condition':{'field':'evidence_age_hours','operator':'greater_than','value':24}},
    {'type':'condition','condition':{'field':'eligible_quantity','operator':'less_than','value':'requested_quantity'}},
    {'type':'condition','condition':{'field':'milestone_risk','operator':'equals','value':'high'}},
    {'type':'condition','condition':{'field':'approval_pending_hours','operator':'greater_than','value':48}},
    {'type':'manual'}, {'type':'chat'},
])
def test_saved_triggers_have_no_execution_or_source_effect(host,trigger):
    client,service,double,settings=host
    old_db=settings.db_path.read_bytes()
    old_index=service.store.path.read_bytes() if service.store.path.exists() else None
    body={**config(),'trigger':trigger}
    result=create(client,body)
    assert result.status_code==201,result.text
    item=result.json()
    assert item['execution_mode']=='configuration_preview' and not item['background_execution_enabled']
    assert item['trigger_summary']
    assert create(client,body).json()==item
    assert client.get('/control-api/automations/'+item['automation_id'], headers={'X-Stratos-Demo-Profile':'automation'}).json()==item
    assert not service.tasks and double.calls==0
    assert (service.store.path.read_bytes() if service.store.path.exists() else None)==old_index
    assert settings.db_path.read_bytes()==old_db
    assert AutomationStore(service.store.directory).read(item['automation_id'],AUTOMATION).model_dump(mode='json')==item


@pytest.mark.parametrize('change,code',[
    ({'authority':'proposal_only'},409), ({'authority':'bounded_execution'},409),
    ({'program_id':'PRG-P01'},403), ({'customer_id':'CUST-OTHER'},403),
    ({'case_scope':'CR-107'},409), ({'case_scope':None},409),
    ({'workflow_id':'yield_exception_recovery'},409),
    ({'workflow_id':'unknown'},404), ({'owner_actor_id':'engineer'},422),
    ({'execution_mode':'live_model'},422), ({'background_execution_enabled':True},422),
    ({'trigger':{'type':'schedule','cadence':'weekly','time':'07:00','timezone':'UTC'}},422),
    ({'trigger':{'type':'schedule','cadence':'daily','time':'25:00','timezone':'UTC'}},422),
    ({'trigger':{'type':'schedule','cadence':'daily','time':'07:00','timezone':'not/a-zone'}},422),
    ({'trigger':{'type':'schedule','cadence':'daily','time':'07:00','timezone':'UTC','start_date':'2026-02-30'}},422),
    ({'trigger':{'type':'source_event','system':'engineering','event':'result_received'}},422),
    ({'trigger':{'type':'source_event','system':'validation','event':'result_received','webhook':'https://example.com'}},422),
    ({'trigger':{'type':'condition','condition':{'field':'evidence_age_hours','operator':'eval','value':'code()'}}},422),
    ({'trigger':{'type':'condition','condition':{'field':'evidence_age_hours','operator':'greater_than','value':0}}},422),
    ({'safeguards':{'reopen_resolved_case':True}},422),
    ({'safeguards':{'minimum_recheck_minutes':0}},422),
    ({'safeguards':{'deduplicate_by':'event'}},409),
])
def test_invalid_configurations_fail_closed(host,change,code):
    client,service,double,_=host
    result=create(client,{**config(),**change})
    assert result.status_code==code,result.text
    assert len(client.get('/control-api/automations', headers={'X-Stratos-Demo-Profile':'automation'}).json())==3
    assert not service.tasks and double.calls==0


def test_edit_pause_delete_receipts_versions_and_no_reseed(host):
    client,service,double,settings=host
    old_db=settings.db_path.read_bytes()
    item=create(client).json(); key=item['automation_id']
    route=f'automations/{key}'
    changed={**config(),'name':'Weekly evidence review','trigger':{'type':'schedule','cadence':'weekly','weekday':2,'time':'08:15','timezone':'America/Chicago'}}
    update={'request_id':'edit','expected_version':1,'configuration':changed}
    item=post(client,route+'/update',update).json()
    assert item['version']==2 and item['name']=='Weekly evidence review'
    assert post(client,route+'/update',{**update,'request_id':'stale'}).status_code==409
    assert post(client,route+'/update',update).json()==item
    paused=post(client,route+'/state',{'request_id':'pause','expected_version':2,'configuration_state':'paused'}).json()
    assert paused['version']==3 and paused['configuration_state']=='paused'
    resumed=post(client,route+'/state',{'request_id':'resume','expected_version':3,'configuration_state':'configured'}).json()
    assert resumed['version']==4 and resumed['configuration_state']=='configured'
    deletion={'request_id':'delete','expected_version':4}
    assert post(client,route+'/delete',deletion).status_code==200
    assert post(client,route+'/delete',deletion).status_code==200
    assert client.get('/control-api/'+route, headers={'X-Stratos-Demo-Profile':'automation'}).status_code==404
    assert post(client,route+'/update',update).json()['version']==2  # exact old receipt, never resurrects
    assert create(client).json()['automation_id']==key
    assert client.get('/control-api/'+route, headers={'X-Stratos-Demo-Profile':'automation'}).status_code==404
    assert create(client,{**config(),'name':'Changed under same key'}).status_code==409
    seed=client.get('/control-api/automations/example_yield', headers={'X-Stratos-Demo-Profile':'automation'}).json()
    assert post(client,'automations/example_yield/delete',{'request_id':'delete_seed','expected_version':seed['version']}).status_code==200
    service.automations.seed_examples()
    assert client.get('/control-api/automations/example_yield', headers={'X-Stratos-Demo-Profile':'automation'}).status_code==404
    assert len(client.get('/control-api/automations', headers={'X-Stratos-Demo-Profile':'automation'}).json())==2
    with service.automations.transaction() as data:
        assert [a.action for a in data.activity if a.action != "denied"]==['create','update','pause','resume','delete','delete']
    assert not service.store.path.exists() and double.calls==0 and settings.db_path.read_bytes()==old_db


def test_configuration_role_origin_and_concurrent_retry(host):
    client,service,double,_=host
    assert create(client).status_code==201
    for role in ('reader','unknown'):
        assert post(client,'automations',{'request_id':'deny','configuration':config()},role).status_code==403
    assert client.post('/control-api/automations',json={'request_id':'deny','configuration':config()}).status_code==403
    body=CreateAutomation(request_id='concurrent',configuration=config())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _: service.automations.mutate('create',body,AUTOMATION),range(4)))
    assert len({r.automation_id for r in results})==1
    assert len(client.get('/control-api/automations', headers={'X-Stratos-Demo-Profile':'automation'}).json())==5
    assert double.calls==0


def test_run_outcomes_preserve_review_execution_and_physical_boundary(host):
    client=host[0]
    proposal=investigate(host); ref=proposal['execution']['reference']; route='/control-api/runs/'+ref['run_id']
    assert client.get(route, headers={'X-Stratos-Demo-Profile':'automation'}).json()['run']['business_outcome']=='Waiting for review'
    assert post(client,'proposals/review',{'reference':ref,'decision':'approve'},'engineer').status_code==200
    assert client.get(route, headers={'X-Stratos-Demo-Profile':'automation'}).json()['run']['business_outcome']=='Approved · Execution pending'
    assert post(client,'proposals/execute',{'reference':ref}).status_code==200
    assert client.get(route, headers={'X-Stratos-Demo-Profile':'automation'}).json()['run']['business_outcome']=='Physical result pending'
    assert client.get(route, headers={'X-Stratos-Demo-Profile':'automation'}).json()['run']['status']=='completed'


def test_downstream_history_and_separate_customer_acceptance(host):
    client=host[0]
    execution_and_result(host)
    value,_=assess(host)
    run=value['runs'][0]
    detail=client.get('/control-api/runs/'+run['run_id'], headers={'X-Stratos-Demo-Profile':'automation'}).json()
    assert detail['run']['business_outcome']=='Waiting for engineering review'
    physical=value['downstream']['physical']
    assert post(client,'cases/CR-017/evidence-review',{'expected_evidence_digest':physical['evidence_digest'],'decision':'approve','comment':'Scripted exact evidence review.'},'engineer').status_code==200
    assert client.get('/control-api/runs/'+run['run_id'], headers={'X-Stratos-Demo-Profile':'automation'}).json()['run']['business_outcome']=='Validation complete · Customer acceptance pending'


def test_runtime_completed_escalation_is_not_success():
    run=SimpleNamespace(status='completed',recommendation=SimpleNamespace(policy_path='escalation_required'))
    assert business_outcome(run,[],None,True)=='Escalation required'

@pytest.mark.parametrize('fault,expected',[('reject','Rejected'),('partial','Partially executed'),('mismatch','Verification failed')])
def test_run_detail_projects_actual_business_failures(host,monkeypatch,fault,expected):
    from program_coordinator.application.execution_models import SourceFailure
    client,service,_,_=host
    proposal=investigate(host); ref=proposal['execution']['reference']
    assert post(client,'proposals/review',{'reference':ref,'decision':'reject' if fault=='reject' else 'approve'},'engineer').status_code==200
    if fault!='reject':
        if fault=='partial':
            def fail(*args): raise SourceFailure('RESOURCE_CONFLICT')
            monkeypatch.setattr(service.source,'link',fail)
        else:
            original=service.source.read.get_validation_job
            def wrong(*args):
                value=original(*args); value['configuration_id']='CFG-WRONG'; return value
            monkeypatch.setattr(service.source.read,'get_validation_job',wrong)
        assert post(client,'proposals/execute',{'reference':ref}).status_code==200
    detail=client.get('/control-api/runs/'+ref['run_id'], headers={'X-Stratos-Demo-Profile':'automation'}).json()
    assert detail['run']['status']=='completed' and detail['run']['business_outcome']==expected


def test_configuration_denials_are_metadata_only_audited(host):
    client,service,_,_=host
    assert create(client,{**config(),'authority':'bounded_execution'}).status_code==409
    with service.automations.transaction() as data:
        assert data.activity[-1].action=='denied'
        assert data.activity[-1].error_code=='AUTOMATION_AUTHORITY_EXCEEDED'
        assert data.activity[-1].actor_id=='demo-automation'
    assert not service.store.path.exists()
