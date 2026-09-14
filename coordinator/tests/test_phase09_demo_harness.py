"""Offline operator guards. No model requests, real microphone or working demo writes."""
from dataclasses import asdict
import json
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from program_coordinator.control_host import demo_harness as harness
from program_coordinator.control_host import readiness
from program_investigator.config import InvestigatorError


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, 'PROJECT', tmp_path)
    root = tmp_path/'.demo/test'
    return harness.Config(str(root), str(root/'enterprise.sqlite3'), str(root/'metadata'))


def test_paths_refuse_outside_symlink_and_hardlink(config, tmp_path):
    with pytest.raises(harness.DemoError): harness.safe_path(tmp_path/'arbitrary')
    root = config.directory; root.mkdir(parents=True)
    original = root/'original'; original.write_text('synthetic')
    link = root/'link'; link.symlink_to(original)
    with pytest.raises(harness.DemoError): harness.safe_path(link)
    link.unlink(); link.hardlink_to(original)
    with pytest.raises(harness.DemoError): harness.safe_path(link)


def test_invalid_port_and_json_fail_closed(config):
    with pytest.raises(harness.DemoError): harness.Config(**{**asdict(config), 'ui_port':8000}).validate()
    config.directory.mkdir(parents=True)
    p=config.directory/'state.json';p.write_text('[]')
    with pytest.raises(harness.DemoError): harness.read_json(p)


def test_stop_never_signals_unowned_or_reused_pid(config, monkeypatch):
    state={'pid':23456,'identity':'old process','token':'a'*32,'status':'running'}
    harness.write_json(config.directory/'processes.json', state)
    monkeypatch.setattr(harness, 'process_identity', lambda pid:'different process')
    monkeypatch.setattr(harness.os, 'kill', lambda *args:pytest.fail('unowned process signaled'))
    with pytest.raises(harness.DemoError, match='ownership'): harness.stop(config)


def test_occupied_port_starts_nothing(config, monkeypatch):
    monkeypatch.setattr(harness, 'prerequisites', lambda c:None)
    monkeypatch.setattr(harness, 'port_free', lambda p:p != 8000)
    monkeypatch.setattr(harness.subprocess, 'Popen', lambda *a,**kw:pytest.fail('unexpected child'))
    with pytest.raises(harness.DemoError, match='Ports occupied: 8000'): harness.start(config)


def test_live_listener_refused_but_closed_connections_allow_restart():
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('127.0.0.1', 0)); listener.listen()
        port=listener.getsockname()[1]
        assert not harness.port_free(port)
        with socket.create_connection(('127.0.0.1', port)) as client:
            accepted,_=listener.accept();accepted.close()
    assert harness.port_free(port)


def test_existing_owned_start_is_idempotent(config, monkeypatch):
    harness.write_json(config.directory/'processes.json', {'status':'running','config':asdict(config)})
    monkeypatch.setattr(harness, 'owns_supervisor', lambda s:True)
    monkeypatch.setattr(harness, 'service_health', lambda c:{'source':True})
    monkeypatch.setattr(harness.subprocess, 'Popen', lambda *a,**kw:pytest.fail('duplicate child'))
    assert harness.start(config)['result']=='already_running'


def test_init_never_overwrites_and_requires_confirmation(config):
    with pytest.raises(harness.DemoError, match='requires --yes'): harness.initialize(config, False)
    config.directory.mkdir(parents=True);Path(config.source_db).write_text('retained')
    with pytest.raises(harness.DemoError, match='already exists'): harness.initialize(config, True)
    assert Path(config.source_db).read_text()=='retained'


def test_reset_delegates_existing_cli_exact_scope_and_origin(config, monkeypatch):
    from program_coordinator.control_host import demo_cli
    monkeypatch.setattr(harness, 'owns_supervisor', lambda s:True)
    observed=[]
    monkeypatch.setattr(demo_cli, 'main', lambda:observed.append(list(harness.sys.argv)))
    harness.write_json(config.directory/'processes.json', {'config':{**asdict(config), 'source_port':8011}})
    with pytest.raises(harness.DemoError, match='matching owned harness'): harness.reset(config, 'full', True)
    assert observed == []
    harness.write_json(config.directory/'processes.json', {'config':asdict(config)})
    harness.reset(config, 'CR-019', True)
    assert observed == [['demo_cli','--host-url','http://127.0.0.1:18082','--ui-origin','http://127.0.0.1:5188','reset','--scope','CR-019','--yes']]


def test_model_presence_never_returns_credential_or_calls_provider(monkeypatch):
    sentinel='synthetic-private-test-value'
    monkeypatch.setattr(readiness, 'load_key', lambda p:sentinel)
    result=readiness.model_configuration()
    assert result['status']=='configured' and result['paid_call_made'] is False
    assert sentinel not in json.dumps(result)
    def absent(p):raise InvestigatorError('key_missing_or_invalid_format')
    monkeypatch.setattr(readiness, 'load_key', absent)
    assert readiness.model_configuration()['status']=='unavailable'


def test_readiness_is_read_only_and_doubles_do_not_inspect_keys(monkeypatch, tmp_path):
    from coordinator.evals.phase08_5.probe import client_environment
    monkeypatch.setattr(readiness, 'load_key', lambda p:pytest.fail('test runtime inspected a real key'))
    with client_environment(tmp_path/'readiness') as env:
        client,host,*_=env
        with host.store.transaction() as data: before=data.model_dump(mode='json')
        response=client.get('/control-api/readiness');assert response.status_code==200
        result=response.json()
        assert result['model_configuration']['status']=='deterministic_test'
        assert result['concierge_route_available'] and result['active_workflows']==[]
        assert set(result['background_execution'].values())=={'not_installed'}
        with host.store.transaction() as data: assert data.model_dump(mode='json')==before


def test_ready_requires_every_gate_and_unavailable_is_not_zero(config, monkeypatch):
    monkeypatch.setattr(harness, 'service_health', lambda c:{'source':True,'mcp':True,'control_host':True,'frontend':True})
    monkeypatch.setattr(harness, 'owns_supervisor', lambda s:True)
    monkeypatch.setattr(harness, 'read_json', lambda p:{'status':'running','config':asdict(config)})
    observations={
        '/demo/verify?scope=full':{'baseline_valid':True}, '/demo':{'enabled':True,'recovery_required':False},
        '/readiness':{'model_configuration':{'status':'configured'},'runtime_invocable':True,
            'concierge_route_available':True, 'active_workflows':[], 'active_host_tasks':0,'active_concierge_turns':0,
            'background_execution':{k:'not_installed' for k in ('schedulers','event_listeners','condition_evaluators')}},
        '/operations/health':[{'system':s,'status':'Available'} for s in harness.SYSTEMS],
        '/cases/CR-017':{'case_summaries':[{'change_id':c,'source_available':True,'state_label':'New'} for c in harness.CASES], 'decision_summaries':[]}}
    monkeypatch.setattr(harness, 'request', lambda url,**kw:observations.get(url.split('/control-api')[1]))
    assert harness.status(config)['result']=='Demo ready'
    observations['/readiness']['active_concierge_turns']=1
    assert harness.status(config)['result']=='Not ready'
    observations['/readiness']=None
    value=harness.status(config)
    assert value['result']=='Not ready' and value['checks']['no_running_work'] is False
    assert value['model_configuration']['status']=='unavailable'
