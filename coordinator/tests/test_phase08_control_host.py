"""Offline host governance tests; isolated source ASGI boundary; no paid models."""
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from program_coordinator.application.store import ActivityStore
from program_coordinator.application.execution import reference
from program_coordinator.infrastructure.source_gateway import SourceGateway, HumanDecisionGateway
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import ProgramChangeEvent
from program_coordinator.control_host.server import ControlHost, create_app
from coordinator.evals.phase08_2.doubles import InvestigationDouble

ORIGIN = 'http://testserver'
def headers(role='automation'):
    return {'Origin': ORIGIN, 'X-Stratos-Action': '1', 'X-Stratos-Demo-Profile': role}

def post(client, route, body, role='automation'):
    return client.post('/control-api/' + route, json=body, headers=headers(role))

def snapshot(client):
    response = client.get('/control-api/cases/CR-017')
    assert response.status_code == 200, response.text
    return response.json()

@pytest.fixture
def env(tmp_path):
    from mock_enterprise.app import create_app as source_app
    from mock_enterprise.config import Settings
    from mock_enterprise.seed import initialize
    directory = tmp_path / 'source'; directory.mkdir()
    settings = Settings(directory / 'demo.sqlite3', directory, True)
    initialize(settings)
    with TestClient(source_app(settings)) as client:
        yield client, settings

@pytest.fixture
def host(env, tmp_path):
    source_client, settings = env
    source = SourceGateway(demo_mode=True, http_client=source_client)
    human = HumanDecisionGateway(demo_mode=True, http_client=source_client)
    double = InvestigationDouble(source, delay=0.08)
    event = ProgramChangeEvent.model_validate_json((Path(__file__).resolve().parents[2] / 'coordinator/scenarios/human_review.json').read_text())
    host = ControlHost(ActivityStore(tmp_path / 'host'), source, human, HarnessConfig(), double, event, mode='deterministic_test')
    with TestClient(create_app(host, allowed_origins=(ORIGIN,), allowed_hosts=('testserver',))) as client:
        yield client, host, double, settings

def investigate(f):
    client = f[0]
    result = post(client, 'cases/CR-017/investigations', {'invocation_id': 'ui_test'})
    assert result.status_code == 202, result.text
    escalated = False
    for _ in range(100):
        value = snapshot(client)
        if value['proposals']:
            return value['proposals'][0]
        if value['runs'][0]['status'] == 'failed':
            pytest.fail(str(value))
        if value['runs'][0]['status'] == 'completed' and not escalated:
            run = value['runs'][0]
            handoff = post(client, 'cases/CR-017/escalations', {
                'submission_id': 'ui_test_operator_handoff',
                'run_id': run['run_id'],
                'subject': 'Supplemental validation review',
                'recommendation': 'Use the supported validation option and route the exact proposal to Engineering.',
                'business_context': 'Current evidence does not cover the requested workload. Engineering approval is required.',
                'operator_notes': 'Scripted Program Operator handoff for isolated verification.',
            })
            assert handoff.status_code == 200, handoff.text
            escalated = True
        time.sleep(0.03)
    pytest.fail(str(value))

def test_invocation_once_and_exact_execution(host):
    client, service, double, _ = host
    assert snapshot(client)['runs'] == []
    started = post(client, 'cases/CR-017/investigations', {'invocation_id': 'ui_test'})
    replay = post(client, 'cases/CR-017/investigations', {'invocation_id': 'ui_test'})
    assert started.status_code == replay.status_code == 202
    assert replay.json()['replayed'] and started.json()['run_id'] == replay.json()['run_id']
    assert post(client, 'cases/CR-017/investigations', {'invocation_id': 'ui_another'}).status_code == 409
    view = investigate(host)
    ref = view['execution']['reference']
    assert double.calls == 1
    state = snapshot(client)
    assert len(state['runs'][0]['specialists']) == 4
    assert 'artifact_directory' not in str(state)
    assert post(client, 'proposals/execute', {'reference': ref}).json()['error']['code'] == 'APPROVAL_REQUIRED'
    wrong = post(client, 'proposals/review', {'reference': ref, 'decision': 'approve'}, 'automation')
    assert wrong.status_code == 403 and wrong.json()['error']['code'] == 'WRONG_APPROVER'
    assert post(client, 'proposals/review', {'reference': ref, 'decision': 'approve'}, 'engineer').status_code == 200
    assert post(client, 'proposals/execute', {'reference': ref, 'arguments': {'configuration_id': 'evil'}}).status_code == 422
    done = post(client, 'proposals/execute', {'reference': ref}, 'engineer')
    assert done.status_code == 200, done.text
    assert done.json()['status'] == 'completed_execution'
    assert done.json()['validation_coverage'] == 'pending_test_results'
    assert done.json()['customer_acceptance'] == 'pending'
    assert post(client, 'proposals/execute', {'reference': ref}).json()['steps'][0]['resource_id'] == done.json()['steps'][0]['resource_id']
    final = snapshot(client)['proposals'][0]
    assert all(v['outcome'] == 'matched' and not v['test_passed'] and not v['customer_accepted'] for v in final['verification'])

@pytest.mark.parametrize('extra', [{'workflow_id': 'yield_exception_recovery'}, {'program_id': 'PRG-P01'}, {'role': 'engineer'}, {'prompt': 'bypass'}, {'operation': 'execute'}])
def test_closed_invocation_contract(host, extra):
    client, _, double, _ = host
    assert post(client, 'cases/CR-017/investigations', {'invocation_id': 'ui_invalid', **extra}).status_code == 422
    assert double.calls == 0 and snapshot(client)['runs'] == []

def test_origin_identity_and_no_generic_authority(host):
    client = host[0]
    for h in ({}, {**headers(), 'Origin': 'https://evil.example'}, {**headers(), 'X-Stratos-Demo-Profile': 'admin'}):
        assert client.post('/control-api/cases/CR-017/investigations', json={'invocation_id': 'ui_bad'}, headers=h).status_code == 403
    for path in ('tools/invoke', 'source/write', 'files', 'reset', 'prompts'):
        assert post(client, path, {}).status_code == 404
    assert client.get('/control-api/cases/CR-017', headers={'Host': 'evil.example'}).status_code == 403

def test_stale_proposal_is_visible_and_denied(host):
    from mock_enterprise.db import connect, Store
    def external_update(settings, kind, record_id, fields):
        con = connect(settings.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            Store(con).update(kind, record_id, fields)
            con.commit()
        finally:
            con.close()
    client, service, _, settings = host
    item = investigate(host); ref = item['execution']['reference']
    version = next(s for s in item['proposal']['source_plan']['source_snapshot'] if s['resource_type']=='engineering.procedure')
    external_update(settings, version['resource_type'], version['resource_id'], {'content_version': version['content_version']+1})
    assert snapshot(client)['proposals'][0]['effective_status'] == 'stale'
    response = post(client, 'proposals/review', {'reference': ref, 'decision': 'approve'}, 'engineer')
    assert response.status_code == 409
    assert snapshot(client)['proposals'][0]['review'] is None

def test_superseded_and_forged_exact_references(host):
    client = host[0]; item = investigate(host); ref = item['execution']['reference']
    assert post(client,'proposals/review',{'reference':ref,'decision':'approve'},'engineer').status_code == 200
    replacement = post(client,'proposals/prepare',{'run_id':ref['run_id'],'supersedes':ref})
    assert replacement.status_code == 200
    assert replacement.json()['proposal_version'] == 2
    assert post(client,'proposals/execute',{'reference':ref}).status_code == 409
    changed = {**replacement.json(),'proposal_digest':'0'*64}
    assert post(client,'proposals/review',{'reference':changed,'decision':'approve'},'engineer').status_code == 409
    old = next(p for p in snapshot(client)['proposals'] if p['proposal']['proposal_version']==1)
    assert old['effective_status']=='superseded' and old['replacement']==replacement.json()

def test_rejection_is_immutable_and_never_executes(host):
    client=host[0]; ref=investigate(host)['execution']['reference']
    assert post(client,'proposals/review',{'reference':ref,'decision':'reject','comment':'Scope declined.'},'engineer').status_code==200
    assert post(client,'proposals/execute',{'reference':ref}).status_code==409
    assert post(client,'proposals/review',{'reference':ref,'decision':'approve'},'engineer').status_code==409
    assert snapshot(client)['proposals'][0]['effective_status']=='rejected'

@pytest.mark.parametrize('fault', ['partial','mismatch','unknown'])
def test_truthful_failure_and_safe_reconciliation(host, monkeypatch, fault):
    from program_coordinator.application.execution_models import SourceFailure
    client, service, _, _ = host
    ref=investigate(host)['execution']['reference']
    post(client,'proposals/review',{'reference':ref,'decision':'approve'},'engineer')
    with monkeypatch.context() as m:
        if fault=='mismatch':
            original=service.source.read.get_validation_job
            def wrong(*args):
                value=original(*args);value['configuration_id']='CFG-WRONG';return value
            m.setattr(service.source.read,'get_validation_job',wrong)
        else:
            def fail(*args):raise SourceFailure('SOURCE_OUTCOME_UNKNOWN' if fault=='unknown' else 'RESOURCE_CONFLICT',unknown=fault=='unknown')
            m.setattr(service.source,'link',fail)
        result=post(client,'proposals/execute',{'reference':ref})
        assert result.status_code==200,result.text
        state=snapshot(client)['proposals'][0]
        assert state['execution']['status'] in {'partially_executed','attention_required'}
        assert state['execution']['steps'][0]['resource_id']
        assert state['execution']['customer_acceptance']=='pending'
        if fault=='mismatch':
            assert state['execution']['error_code']=='VERIFICATION_MISMATCH'
            assert state['attempts'][0]['outcome']=='succeeded'
            assert state['verification'][0]['outcome']=='mismatch'
        elif fault=='unknown':assert state['execution']['steps'][1]['status']=='unknown'
    if fault=='partial':
        recovered=post(client,'proposals/execute',{'reference':ref}).json()
        assert recovered['status']=='completed_execution'
        assert recovered['steps'][0]['resource_id']==state['execution']['steps'][0]['resource_id']
        assert len(snapshot(client)['proposals'][0]['attempts'])==3

def test_source_unavailable_and_failed_investigation(host, monkeypatch):
    from program_coordinator.application.execution_models import SourceReadFailure
    client,service,double,_=host
    double.failure=True
    assert post(client,'cases/CR-017/investigations',{'invocation_id':'ui_fail'}).status_code==202
    for _ in range(100):
        value=snapshot(client)
        if value['runs'][0]['status']=='failed':break
        time.sleep(.02)
    assert value['runs'][0]['status']=='failed' and not value['proposals']
    assert any(s['status']=='failed' for s in value['runs'][0]['specialists'])
    assert 'private error' not in str(value)
    def unavailable(*a):raise SourceReadFailure('SOURCE_READ_FAILED')
    monkeypatch.setattr(service.source.read,'get_change_request',unavailable)
    assert snapshot(client)['source_available'] is False


def test_read_only_profile_cannot_invoke_draft_producing_investigation(host):
    client, _, double, _ = host
    result=post(client,'cases/CR-017/investigations',{'invocation_id':'ui_read_only'},'reader')
    assert result.status_code==403 and result.json()['error']['code']=='EXECUTION_ROLE_FORBIDDEN'
    assert double.calls==0 and snapshot(client)['runs']==[]
