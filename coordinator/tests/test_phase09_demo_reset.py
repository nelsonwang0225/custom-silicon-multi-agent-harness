"""Scripted integration testing: isolated HTTP/MCP and deterministic model doubles.

No paid model or actual human approval. Historical project artifacts are read
only for preservation checks. Failure injection is private to these tests.
"""
from contextlib import contextmanager
import hashlib
import json
import time
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from coordinator.evals.phase08_5.probe import environment, post, ask, confirm
from coordinator.evals.phase08_4c.fixtures import mutate
from mock_enterprise.config import PROJECT, Settings
from mock_enterprise.db import connect, Store
from mock_enterprise.demo_management import inspect_source, maintenance_lock, current_rows
from program_coordinator.application.automations import example_definitions
from program_coordinator.application.models import WorkflowError
from program_coordinator.control_host.server import create_app
from program_coordinator.control_host.demo_management import DemoManagement
from program_coordinator.control_host.operations_artifacts import EVAL_ARTIFACTS

HEADERS = {'Origin':'http://testserver','X-Stratos-Action':'1','X-Stratos-Demo-Maintainer':'local-demo-reset'}


@contextmanager
def connected(root, variant='base'):
    with environment(root,variant=variant) as (host,settings,doubles):
        host.demo_management = DemoManagement(host,settings)
        with TestClient(create_app(host,allowed_origins=('http://testserver',),allowed_hosts=('testserver',))) as client:
            yield client,host,settings,doubles


@pytest.fixture
def demo(tmp_path):
    with connected(tmp_path/'demo') as env:
        assert reset(env).status_code==200
        yield env


def reset(env, scope='full', **extra):
    epoch = env[0].get('/control-api/demo').json()['epoch']
    return env[0].post('/control-api/demo/reset',headers=HEADERS,
        json={'scope':scope,'confirmation':'RESET','expected_epoch':epoch,**extra})


def run_case(env, case):
    body = {'invocation_id':'ui_reset_test_'+uuid4().hex,'change_id':case,
            'workflow_id':{'QE-004':'yield_exception_recovery','DR-009':'delivery_readiness'}.get(case,'requirement_change_analysis')}
    r = post(env[0],'cases/'+case+'/investigations',body)
    assert r.status_code==202,r.text
    for _ in range(800):
        if not env[1].tasks:
            value = env[0].get('/control-api/cases/'+case).json()
            assert value['runs'][0]['status']=='completed',value
            return value
        time.sleep(.02)
    pytest.fail('Isolated workflow did not finish')


def execute(env, case, value):
    client = env[0]
    if case=='CR-017':
        body = {'reference':value['proposals'][0]['execution']['reference']}
        reviewed = post(client,'proposals/review',{**body,'decision':'approve','comment':'Scripted demo review'},'engineer')
        assert reviewed.status_code==200,reviewed.text
        r = post(client,'proposals/execute',body,'automation')
        assert r.status_code==200,r.text
        assert r.json()['status']=='completed_execution',r.text
    else:
        plan = value['records']['plans'][0]
        body = {'run_id':value['progress'][0]['run_id'],'plan_id':plan['id'],'plan_version':plan['plan_version'],'plan_digest':plan['plan_digest']}
        prefix = 'quality-recovery' if case=='QE-004' else 'delivery-commitment'
        reviewed = post(client,prefix+'/review',{**body,'decision':'approve','comment':'Scripted demo Program Owner review'},'program_owner')
        assert reviewed.status_code==200,reviewed.text
        r = post(client,prefix+'/execute',body,'program_owner')
        assert r.status_code==200,r.text
        assert r.json()['status']=='verified',r.text
    return r.json()


def all_source(settings):
    con = connect(settings.db_path)
    try:return current_rows(con)
    finally:con.close()


def test_full_reset_mutated_all_scenarios_and_history(demo):
    client,host,settings,_ = demo
    protected = {path:(PROJECT/path).read_bytes() for _,_,path in EVAL_ARTIFACTS if (PROJECT/path).exists()}
    original = all_source(settings)
    assert original[('planner.program','PRG-P01')]['health']=='on_track'
    standard = run_case(demo,'CR-019')
    assert standard['handoffs'][0]['status']=='handoff_verified'
    for case in ('QE-004','DR-009','CR-017'):
        execute(demo,case,run_case(demo,case))
    # Include the distinct Validation Lab synthetic arrival and Engineering review.
    from tests.conftest import get, post as source_post, ENGINEER
    with httpx.Client(base_url=host.source.config.base_url,trust_env=False) as source:
        job = get(source,'/validation/jobs?change_id=CR-017')['items'][0]
        r = source_post(source,f'/validation/jobs/{job["id"]}/synthetic-result',{'expected_plan_digest':job['plan_digest']},'reset-lab',{'Authorization':'Bearer demo-lab-local-only'})
        assert r.status_code==201,r.text
        physical = get(source,'/validation/changes/CR-017/physical-validation')
        r = source_post(source,'/engineering/changes/CR-017/evidence-reviews',{'expected_evidence_digest':physical['evidence_digest'],'decision':'approve','reason':'Exact synthetic Engineering review'},'reset-evidence',ENGINEER)
        assert r.status_code==201,r.text
    turn, body = ask(demo,'Check DR-009 every weekday at 7 AM CT')
    assert confirm(demo,turn,body).status_code==200
    traces = {p:p.read_bytes() for p in host.artifacts.rglob('*.json')}
    assert not client.get('/control-api/demo/verify').json()['baseline_valid']
    value = reset(demo)
    assert value.status_code==200,value.text
    check = value.json()['validation']
    assert check['baseline_valid'] and not check['discrepancies']
    assert check['scenario_checks']=={c:True for c in ('CR-017','CR-019','QE-004','DR-009')}
    assert list(check['quantities'].values())==[1000,250,150,600,800,200]
    assert all_source(settings)==original
    with host.store.transaction() as data:
        assert not data.cases and not data.runs and not data.proposals and not data.executions
        assert not data.concierge_sessions and not data.activity and not data.execution_attempts
    with host.automations.transaction() as data:
        assert data.definitions==example_definitions() and not data.receipts
        assert all(not a.background_execution_enabled for a in data.definitions.values())
    assert not host.concierge.actions and not host.concierge.turns
    assert confirm(demo,turn,body).status_code==409
    assert all((PROJECT/p).read_bytes()==v for p,v in protected.items())
    assert all(p.read_bytes()==v for p,v in traces.items())
    assert (host.store.directory/'demo-archives'/value.json()['epoch']/'source.json').is_file()
    second = reset(demo)
    assert second.status_code==200,second.text
    assert all_source(settings)==original
    assert second.json()['validation']['source_digest']==check['source_digest']
    assert second.json()['validation']['control_digest']==check['control_digest']
    operations = client.get('/control-api/operations',headers={'X-Stratos-Demo-Profile':'automation'}).json()
    assert not operations['runs'] and not operations['sessions']
    if any(e['eval_id']=='live-original' for e in operations['evals']):
        old = next(e for e in operations['evals'] if e['eval_id']=='live-original')
        assert (old['passed'],old['total'],old['hard_gate'])==(4,6,'FAIL')


@pytest.mark.parametrize('case',['CR-017','CR-019','QE-004','DR-009'])
def test_single_scenario_resets_and_preserves_unrelated(demo, case):
    client,host,settings,_ = demo
    other = 'QE-004' if case.startswith('CR') else 'CR-019'
    other_view = run_case(demo,other)
    value = run_case(demo,case)
    if case!='CR-019':execute(demo,case,value)
    from mock_enterprise.demo_management import selected_rows,scope_cases
    before = all_source(settings)
    selected = selected_rows(before,scope_cases(case))
    unrelated = {k:v for k,v in before.items() if k not in selected}
    result = reset(demo,case)
    assert result.status_code==200,result.text
    assert inspect_source(settings,case)['discrepancies']==[]
    after = all_source(settings)
    assert {k:after[k] for k in unrelated}==unrelated
    assert client.get('/control-api/cases/'+other).json()['runs']==other_view['runs']
    assert not client.get('/control-api/cases/'+case).json()['runs']
    assert reset(demo,case).status_code==200


def test_shared_inventory_conflict_requires_full(demo):
    _,host,settings,_ = demo
    def changed(store):
        store.update('manufacturing.quality_material','MAT-B-204',{'held_quantity':0,'released_quantity':250,'eligible_unallocated_quantity':250,'disposition':'released','content_version':2})
    mutate(settings,changed)
    before = all_source(settings)
    for scope in ('QE-004','DR-009'):
        preview = demo[0].get('/control-api/demo/preview',params={'scope':scope}).json()
        assert not preview['allowed'] and 'shared' in str(preview['discrepancies'])
        assert reset(demo,scope).status_code==409
    assert all_source(settings)==before
    assert reset(demo).status_code==200


def test_full_reset_restores_northstar_overview_baseline(demo):
    _,_,settings,_ = demo
    mutate(settings,lambda store:store.update('planner.program','PRG-P01',{
        'health':'at_risk',
        'next_action':'Legacy demo state',
    }))
    assert inspect_source(settings,'CR-019')['discrepancies']==[]
    full = inspect_source(settings)
    assert any('planner.program:PRG-P01' in item for item in full['discrepancies'])
    assert reset(demo,'CR-019').status_code==200
    assert all_source(settings)[('planner.program','PRG-P01')]['health']=='at_risk'
    assert reset(demo).status_code==200
    northstar=all_source(settings)[('planner.program','PRG-P01')]
    assert northstar['health']=='on_track'
    assert 'sustained-load qualification' in northstar['next_action']


def test_cr017_technical_dependency_and_touchless_resource_conflicts(demo):
    _,_,settings,_ = demo
    mutate(settings,lambda store:store.update('erp.delivery_request','DR-009',{'technical_change_id':'CR-017','requirement_revision_id':'REQ-042-V2'}))
    assert reset(demo,'CR-017').status_code==409
    assert reset(demo).status_code==200
    run_case(demo,'CR-019')
    execute(demo,'CR-017',run_case(demo,'CR-017'))
    assert reset(demo,'CR-017').status_code==409
    assert reset(demo).status_code==200


@pytest.mark.parametrize('stage',['source','reconciliation','readback','resume'])
def test_failure_partial_journal_retry_and_no_false_success(demo,monkeypatch,stage):
    client,host,settings,_ = demo
    run_case(demo,'CR-019')
    before = all_source(settings)
    with monkeypatch.context() as m:
        if stage=='source':
            def fail(*args,**kwargs):raise OSError('private diagnostic must not be exposed')
            m.setattr('program_coordinator.control_host.demo_management.restore_source',fail)
        elif stage=='reconciliation':
            def fail(*args,**kwargs):raise OSError('private diagnostic must not be exposed')
            m.setattr(host.demo_management,'reconcile',fail)
        elif stage=='resume':
            def fail(*args,**kwargs):raise OSError('private diagnostic must not be exposed')
            m.setattr('program_coordinator.control_host.demo_management.finish_source_reset',fail)
        else:
            def fail(*args,**kwargs):raise WorkflowError('SOURCE_READ_FAILED')
            m.setattr(host.source.read,'get_manufacturing_lots',fail)
        r = reset(demo)
        assert r.status_code==503,r.text
        assert r.json()['result']==('failed' if stage=='source' else 'partial')
        assert not r.json()['validation']['baseline_valid']
        assert 'private diagnostic' not in r.text
        assert client.get('/control-api/demo').json()['recovery_required']
        if stage=='source': assert all_source(settings)==before
        else:
            assert not inspect_source(settings)['discrepancies']
            response=host.source._http.post(host.source.config.base_url+'/api/v1/validation/jobs',json={})
            assert response.status_code==503 and response.json()['error']['code']=='DEMO_RESET_RECONCILIATION_REQUIRED'
        if stage=='readback':assert 'manufacturing' in str(r.json()['validation']['discrepancies'])
        assert post(client,'cases/CR-019/investigations',{'invocation_id':'ui_blocked','change_id':'CR-019'}).status_code==409
        assert not client.get('/control-api/demo/verify').json()['baseline_valid']
    assert reset(demo).status_code==200
    assert client.get('/control-api/demo/verify').json()['baseline_valid']


def test_demo_guards_csrf_scope_epoch_and_agent_boundary(demo):
    client,host,settings,_ = demo
    epoch = client.get('/control-api/demo').json()['epoch']
    body = {'scope':'full','confirmation':'RESET','expected_epoch':epoch}
    for headers in ({}, {'X-Stratos-Action':'1','Origin':'http://evil.example','X-Stratos-Demo-Maintainer':'local-demo-reset'},
                    {'X-Stratos-Action':'1','Origin':'http://testserver','X-Stratos-Demo-Profile':'automation'}):
        assert client.post('/control-api/demo/reset',json=body,headers=headers).status_code in (403,409)
    for update in ({'scope':'CR-999'},{'scope':'../../fixtures'},{'database':'anything'},{'confirmation':'yes'}):
        assert client.post('/control-api/demo/reset',json={**body,**update},headers=HEADERS).status_code==422
    assert reset(demo).status_code==200
    assert client.post('/control-api/demo/reset',json=body,headers=HEADERS).status_code==409
    r = post(client,'cases/CR-017/investigations',{'invocation_id':'ui_stale_epoch'})
    # Wait for this valid current request; stale epoch itself is checked separately.
    while host.tasks:time.sleep(.01)
    stale = client.post('/control-api/proposals/prepare',json={'run_id':r.json()['run_id']},headers={**HEADERS,'X-Stratos-Demo-Epoch':epoch,'X-Stratos-Demo-Profile':'automation'})
    assert stale.status_code==409 and stale.json()['error']['code']=='DEMO_STATE_CHANGED'
    with pytest.raises(ValueError):DemoManagement(host,Settings(settings.db_path,settings.storage_root,False))
    from stratos_mcp.catalog import TOOLS
    assert 'reset' not in str(TOOLS).lower()


def test_source_lock_blocks_reads_writes_and_wrong_binding(demo):
    client,host,settings,_ = demo
    with maintenance_lock(settings,exclusive=True):
        r = host.source._http.get(host.source.config.base_url+'/api/v1/engineering/changes/CR-017')
        assert r.status_code==503
    from mock_enterprise.seed import initialize
    other = Settings(settings.storage_root/'other.sqlite3',settings.storage_root,True)
    initialize(other)
    original = host.demo_management.settings
    host.demo_management.settings = other
    assert reset(demo).status_code==409
    host.demo_management.settings = original
    assert reset(demo).status_code==200


def test_active_workflow_refuses_reset_without_mutation(demo):
    client,host,settings,_ = demo
    before = all_source(settings)
    host.tasks.add('private-test-active-task')
    try:
        response = reset(demo)
        assert response.status_code==409 and response.json()['error']['code']=='DEMO_RESET_BUSY'
    finally:host.tasks.clear()
    assert all_source(settings)==before


def test_real_source_restore_rollback_preserves_immutable_protections(demo,monkeypatch):
    client,host,settings,_ = demo
    execute(demo,'CR-017',run_case(demo,'CR-017'))
    before = all_source(settings)
    original = Store.insert
    with monkeypatch.context() as m:
        def fail(self,kind,record):
            if kind=='validation.result':raise OSError('private restore failure')
            return original(self,kind,record)
        m.setattr(Store,'insert',fail)
        r = reset(demo)
        assert r.status_code==503 and not r.json()['validation']['baseline_valid']
        assert all_source(settings)==before
    con = connect(settings.db_path)
    try:
        with pytest.raises(Exception,match='immutable record'):
            con.execute('DELETE FROM engineering_plan')
    finally:con.close()
    assert reset(demo).status_code==200


@pytest.mark.parametrize('variant',['technical_blocked','technical_complete','future_conditional','wrong_configuration'])
def test_full_reset_restores_developer_variants_to_same_canonical_story(tmp_path,variant):
    with connected(tmp_path/variant,variant=variant) as env:
        result = reset(env)
        assert result.status_code==200,result.text
        r = all_source(env[2])[('erp.delivery_request','DR-009')]
        assert r['technical_change_id'] is None and r['requirement_revision_id']=='REQ-042-V1'
        assert r['future_supply_ids']==[]
        assert env[0].get('/control-api/demo/verify').json()['baseline_valid']


def test_single_reset_invalidates_concierge_card_and_preserves_unrelated_history(demo):
    run_case(demo,'CR-017')
    turn,body = ask(demo,'Approve it.',case='CR-017',role='engineer')
    assert turn['cards'][0]['action_id']
    unrelated,_ = ask(demo,'What is happening?',case='QE-004')
    assert reset(demo,'CR-017').status_code==200
    assert confirm(demo,turn,body,role='engineer').status_code==409
    with demo[1].store.transaction() as data:
        assert body['session_id'] not in data.concierge_sessions
        assert unrelated['session_id'] in data.concierge_sessions


def test_off_mode_routes_absent_and_read_only_navigation_does_not_reset(tmp_path):
    with environment(tmp_path/'disabled') as (host,settings,_):
        before = all_source(settings)
        for _ in range(2):
            with TestClient(create_app(host,allowed_origins=('http://testserver',),allowed_hosts=('testserver',))) as client:
                assert client.get('/control-api/demo').json()['enabled'] is False
                assert client.get('/control-api/cases/CR-017').status_code==200
                assert client.post('/control-api/demo/reset',headers=HEADERS,json={'scope':'full','confirmation':'RESET','expected_epoch':'initial'}).status_code==404
            assert all_source(settings)==before


def test_partial_reset_survives_new_host_instance_then_explicit_retry(tmp_path,monkeypatch):
    from program_coordinator.control_host.server import ControlHost
    from program_coordinator.application.store import ActivityStore
    with environment(tmp_path/'restart') as (host,settings,doubles):
        host.demo_management=DemoManagement(host,settings)
        app_options={'allowed_origins':('http://testserver',),'allowed_hosts':('testserver',)}
        with TestClient(create_app(host,**app_options)) as client:
            env=(client,host,settings,doubles)
            assert reset(env).status_code==200
            run_case(env,'CR-019')
            with monkeypatch.context() as m:
                def fail(*args):raise OSError('injected interrupted reconciliation')
                m.setattr(host.demo_management,'reconcile',fail)
                assert reset(env).status_code==503
            epoch=host.demo_management.state().epoch
        restarted=ControlHost(ActivityStore(host.store.directory),host.source,host.human,host.config,
            host.investigate,host.event,mode='deterministic_test',demo_settings=settings)
        with TestClient(create_app(restarted,**app_options)) as client:
            assert client.get('/control-api/demo').json()['recovery_required']
            assert restarted.demo_management.state().epoch==epoch
            assert not client.get('/control-api/demo/verify').json()['baseline_valid']
            assert reset((client,restarted,settings,doubles)).status_code==200


def test_source_epoch_refuses_old_ui_requests(demo):
    client,host,settings,_=demo
    epoch=client.get('/control-api/demo').json()['epoch']
    assert reset(demo).status_code==200
    with httpx.Client(base_url=host.source.config.base_url,trust_env=False) as source:
        r=source.post('/api/v1/validation/jobs',json={},headers={'X-Stratos-Demo-Epoch':epoch})
        assert r.status_code==409 and r.json()['error']['code']=='DEMO_STATE_CHANGED'


def test_baseline_validator_rejects_successful_http_with_wrong_business_projection(demo,monkeypatch):
    source=demo[1].source.read
    original=source.get_delivery_context
    def wrong(case):
        value=original(case)
        value['analysis']['eligible_quantity']=601
        return value
    monkeypatch.setattr(source,'get_delivery_context',wrong)
    result=demo[0].get('/control-api/demo/verify').json()
    assert not result['baseline_valid'] and not result['scenario_checks']['DR-009']
    assert any('DR-009' in d for d in result['discrepancies'])
