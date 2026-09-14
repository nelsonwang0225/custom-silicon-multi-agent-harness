"""Scripted integration tests: real source HTTP + scoped MCP, deterministic SDK runner double."""
import json
import time
from pathlib import Path
from contextlib import contextmanager
import pytest
from fastapi.testclient import TestClient
from mock_enterprise.config import Settings
from program_coordinator.application.store import ActivityStore
from program_coordinator.infrastructure.source_gateway import SourceGateway,HumanDecisionGateway
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import ProgramChangeEvent
from program_coordinator.control_host.server import ControlHost,create_app
from coordinator.evals.phase08_4a.fixtures import prepare,VARIANTS
from coordinator.evals.phase08_4a.network import network
from coordinator.evals.phase08_4a.doubles import StandardInvestigationDouble
from tests.test_standard_change import source_counts

from coordinator.evals.phase08_4a.probe import environment,post,read,investigate

@pytest.fixture
def host(tmp_path):
    with environment(tmp_path) as value:yield value


def test_connected_standard_handoff_and_duplicate(host):
    client,service,double,settings=host;before=source_counts(settings)
    state=investigate(host)
    assert state['handoffs'],json.dumps(state)
    handoff=state['handoffs'][0]
    assert handoff['status']=='handoff_verified',json.dumps(state)
    assert state['runs'][0]['status']=='completed'
    assert double.harnesses[0].runner.peak_active==3
    assert len(state['runs'][0]['specialists'])==3
    assert handoff['package']['reusable_evidence_ids'][0]=='RES-BASELINE-B'
    assert handoff['package']['remaining_work']
    assert handoff['intake']['lab_authorization']=='pending'
    assert handoff['intake']['physical_testing']=='not_started'
    assert handoff['intake']['customer_acceptance']=='pending'
    events=[a['event_type'] for a in state['activity']]
    assert events.index('standard_action_succeeded')<events.index('standard_handoff_verified')
    assert source_counts(settings)=={**before,'validation.intake':1}
    assert client.get('/control-api/cases/CR-017').json()['proposals']==[]
    assert post(client,'proposals/prepare',{'run_id':state['runs'][0]['run_id']}).status_code==409
    replay=post(client,'cases/CR-019/investigations',{'invocation_id':'ui_standard_first','change_id':'CR-019'})
    assert replay.json()['replayed'] and double.calls==1
    again=investigate(host,'ui_standard_second')
    assert again['handoffs'][0]['status']=='handoff_verified'
    assert again['handoffs'][0]['reused_existing']
    assert again['handoffs'][0]['intake']['id']==handoff['intake']['id']
    assert source_counts(settings)=={**before,'validation.intake':1}


def test_running_standard_investigation_withholds_final_eligibility(host):
    client,service,double,settings=host
    double.delay=.5
    response=post(client,'cases/CR-019/investigations',{
        'invocation_id':'ui_standard_running_projection','change_id':'CR-019',
    })
    assert response.status_code==202,response.text
    state=read(client)
    assert state['runs'][0]['run_id']==response.json()['run_id']
    assert state['runs'][0]['status']=='running'
    assert state['eligibility'] is None
    for _ in range(200):
        state=read(client)
        if state['runs'][0]['status']=='completed':break
        time.sleep(.03)
    assert state['runs'][0]['status']=='completed',json.dumps(state)
    assert len(state['eligibility']['checks'])==18
    assert all(check['passed'] for check in state['eligibility']['checks'])
    assert state['eligibility']['reusable_evidence_ids']==['RES-BASELINE-B']


def test_standard_event_provenance_tracks_engineering_source_only(host):
    from program_coordinator.control_host.standard_change import event
    from program_coordinator.application.standard_handoff_models import StandardHandoff
    from program_coordinator.application.store import MetadataIndex
    from mock_enterprise.db import Store,connect

    context=host[1].standard.context()
    original=event(context)
    con=connect(host[3].db_path)
    with con:
        Store(con).update('engineering.standard_request','STD-REQUEST-019',{
            'request_source':'engineering',
            'requested_by':'Alternate authorized Engineering intake',
        })
    con.close()
    changed=event(host[1].standard.context())
    assert original.source_system=='customer_intake'
    assert original.requested_by=='Helios AI / acceptance package coordination'
    assert changed.source_system=='engineering'
    assert changed.requested_by=='Alternate authorized Engineering intake'
    assert original.model_dump(exclude={'source_system','requested_by'})==changed.model_dump(exclude={'source_system','requested_by'})
    assert not {'request_source','requested_by'} & set(StandardHandoff.model_fields)
    assert not {'standard_context','standard_request'} & set(MetadataIndex.model_fields)

@pytest.mark.parametrize('variant',VARIANTS[1:])
def test_ineligible_stops_without_write(tmp_path,variant):
    with environment(tmp_path,variant) as value:
        before=source_counts(value[3]);state=investigate(value)
        assert state['runs'][0]['status']=='completed',json.dumps(state)
        assert state['handoffs'][0]['status']=='review_required',json.dumps(state)
        assert not state['eligibility']['touchless_eligible']
        assert state['handoffs'][0]['reasons']
        assert state['handoffs'][0]['package'] is None
        assert source_counts(value[3])==before

@pytest.mark.parametrize('fault',['known_failure','unknown_no_write','unknown_committed','readback_unavailable','readback_mismatch'])
def test_durable_failure_reconciliation_never_blindly_reposts(host,monkeypatch,fault):
    from program_coordinator.application.execution_models import SourceFailure,SourceReadFailure
    client,service,double,settings=host;before=source_counts(settings)
    original_write=service.source.standard_intake;original_read=service.source.read.get_standard_validation_intake
    writes=[]
    def write(*args):
        writes.append(args)
        if fault=='known_failure':raise SourceFailure('RESOURCE_CONFLICT')
        if fault=='unknown_no_write':raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
        result=original_write(*args)
        if fault=='unknown_committed':raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
        return result
    def readback(*args):
        if fault=='readback_unavailable':raise SourceReadFailure('SOURCE_READ_FAILED')
        value=original_read(*args)
        if fault=='readback_mismatch':value['downstream_owner']='Wrong queue owner'
        return value
    with monkeypatch.context() as m:
        m.setattr(service.source,'standard_intake',write);m.setattr(service.source.read,'get_standard_validation_intake',readback)
        state=investigate(host);h=state['handoffs'][0]
        assert h['status']!='handoff_verified'
        assert len(writes)==1
    args={'run_id':h['run_id'],'expected_version':h['version']}
    if fault=='unknown_no_write':
        with monkeypatch.context() as m:
            m.setattr(service.source,'standard_intake',lambda *a:pytest.fail('Unknown outcome blindly reposted'))
            recovered=post(client,'standard-handoffs/retry',args)
        assert recovered.json()['status']=='outcome_unknown'
        assert source_counts(settings)==before
    else:
        recovered=post(client,'standard-handoffs/'+('retry' if fault=='known_failure' else 'reconcile'),args)
        assert recovered.status_code==200,recovered.text
        assert recovered.json()['status']=='handoff_verified'
        assert source_counts(settings)=={**before,'validation.intake':1}
    assert post(client,'standard-handoffs/reconcile',args).status_code==409


def test_source_changed_after_analysis_and_model_cannot_override(host,monkeypatch):
    client,service,double,settings=host
    original=service.standard.context
    def changed():
        context=original();context.context_digest='a'*64
        return context
    # Intake/start reads the original source; only the host post-analysis policy read changes.
    count=[0]
    def context():
        count[0]+=1
        return original() if count[0]==1 else changed()
    monkeypatch.setattr(service.standard,'context',context)
    state=investigate(host)
    assert state['handoffs'][0]['error_code']=='STANDARD_SOURCE_CHANGED'
    assert source_counts(settings)['validation.intake']==0


def test_closed_host_route_scope_and_reader_denials(host):
    client,service,double,settings=host
    assert post(client,'cases/CR-019/investigations',{'invocation_id':'ui_reader','change_id':'CR-019'},'reader').status_code==403
    assert post(client,'cases/CR-017/investigations',{'invocation_id':'ui_cross','change_id':'CR-019'}).status_code==409
    assert post(client,'workflows/standard_change/runs',{'invocation_id':'ui_cross','change_id':'CR-017'}).status_code==409
    for extra in ({'procedure_id':'PROC-EVIL'},{'package':{}},{'role':'engineer'},{'operation':'execute'}):
        assert post(client,'cases/CR-019/investigations',{'invocation_id':'ui_extra','change_id':'CR-019',**extra}).status_code==422
    assert not double.calls

def test_new_run_cannot_bypass_previous_unknown_action(host,monkeypatch):
    from program_coordinator.application.execution_models import SourceFailure
    client,service,double,settings=host
    def unknown(*args):raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
    with monkeypatch.context() as m:
        m.setattr(service.source,'standard_intake',unknown)
        first=investigate(host)
    with monkeypatch.context() as m:
        m.setattr(service.source,'standard_intake',lambda *a:pytest.fail('New invocation bypassed unresolved action'))
        second=investigate(host,'ui_after_unknown')
    assert second['handoffs'][0]['status']=='outcome_unknown'
    assert second['handoffs'][0]['package']==first['handoffs'][0]['package']
    assert source_counts(settings)['validation.intake']==0
