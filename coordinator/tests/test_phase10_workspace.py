"""Read-only workspace projections over isolated deterministic host records."""
import os
from datetime import datetime, timezone, timedelta
import pytest
from test_phase08_control_host import env, host, investigate, headers
from program_coordinator.control_host.agent_workspace import snapshot, checkpoint, OBSERVATION_TTL
from program_coordinator.control_host.access import ACTORS
from program_coordinator.control_host.operations_models import OpsHealth
from program_coordinator.models import CaseState


def view(host,role='reader',run=None):
    r=host[0].get('/control-api/agent-workspace',headers=headers(role),params={'run_id':run} if run else {})
    assert r.status_code==200,r.text
    return r.json()


def recorded(host):
    investigate(host)
    with host[1].store.transaction() as data:run=next(iter(data.runs.values()))
    path=host[1].checkpoint_path(run)
    return run,CaseState.model_validate_json(path.read_text()),path


def write_state(host,run,state,path,status='running'):
    with host[1].store.transaction(write=True) as data:
        data.runs[run.run_id].status=status
        data.runs[run.run_id].completed_at=None if status=='running' else run.completed_at
    path.write_text(state.model_dump_json())


@pytest.mark.parametrize('role',list(ACTORS))
def test_idle_is_fresh_scoped_and_zero_model_source_or_business_writes(host,role,monkeypatch):
    db=host[3].db_path.read_bytes(); count=host[2].calls
    def forbidden(*a,**kw):raise AssertionError('Rendering must not probe sources or run models')
    monkeypatch.setattr(host[1],'snapshot',forbidden)
    monkeypatch.setattr(host[1].source.read,'get_change_request',forbidden)
    v=view(host,role)
    assert v['runs']==[] and v['active_run_count']==0 and v['fresh_source_count'] is None
    assert all(s['checked_at'] is None for s in v['sources'])
    assert v['model_state']=='Deterministic test runtime'
    assert host[3].db_path.read_bytes()==db and host[2].calls==count


def test_unknown_role_scope_and_guessed_run_are_denied(host):
    c=host[0]
    for params in ({'program_id':'PRG-UNKNOWN'},{'customer_id':'CUST-UNKNOWN'}):assert c.get('/control-api/agent-workspace',params=params,headers=headers()).status_code==403
    assert c.get('/control-api/agent-workspace',headers=headers('admin')).status_code==403
    assert c.get('/control-api/agent-workspace?run_id=guessed',headers=headers()).status_code==404


@pytest.mark.parametrize('role',list(ACTORS))
def test_completed_agents_and_human_handoff_remain_separate(host,role):
    run,state,path=recorded(host);count=host[2].calls
    v=view(host,role);r=v['runs'][0]
    assert r['run_id']==run.run_id and r['telemetry']=='recorded'
    assert all(a['state']=='completed' for a in r['agents'] if a['tasks'])
    assert r['handoff']['label']=='Awaiting Engineering review'
    assert r['handoff']['version'] and r['handoff']['digest']
    assert any(a['tasks'][0]['evidence'] for a in r['agents'] if a['tasks'])
    assert any(l['label']=='View run' for l in r['links'])==(role=='automation')
    assert 'trace_id' not in str(v) and 'rationale' not in str(v) and 'tool_calls' not in str(v)
    assert host[2].calls==count


def test_parallel_work_staleness_and_failure_keep_invocation_provenance(host):
    run,state,path=recorded(host)
    state.workflow_stage='specialists';active={'validation_evidence','program_commercial'}
    active_ids={i.invocation_id for i in state.requested_specialists if i.specialist in active}
    for i in state.requested_specialists:
        if i.specialist in active:i.status='running';i.ended_ms=None
    state.completed_assessments=[a for a in state.completed_assessments if a.invocation_id not in active_ids]
    write_state(host,run,state,path)
    r=view(host)['runs'][0];agents={a['id']:a for a in r['agents']}
    assert {k for k,a in agents.items() if a['state']=='working'}==active
    assert agents['coordinator']['state']=='delegated'
    assert r['handoff'] is None
    assert all(a['label']=='Investigating' for a in agents.values() if a['state']=='working')
    assert agents['change_impact']['tasks'][0]['finding']
    os.utime(path,(0,0));r=view(host)['runs'][0]
    assert r['telemetry']=='stale' and not any(a['state']=='working' for a in r['agents'])
    for i in state.requested_specialists:
        if i.specialist=='validation_evidence':i.status='failed';i.error='Private stack detail';i.ended_ms=20
    write_state(host,run,state,path,'failed')
    r=view(host)['runs'][0];agents={a['id']:a for a in r['agents']}
    assert agents['validation_evidence']['state']=='failed' and agents['change_impact']['state']=='completed'
    assert agents['change_impact']['tasks'][0]['finding']
    assert 'Private stack detail' not in str(r)
    assert agents['program_commercial']['state']=='unknown' # no claim of continued work after failed run


def test_missing_checkpoint_is_unknown_and_mismatched_scope_cannot_leak(host):
    run,state,path=recorded(host);path.unlink()
    r=view(host)['runs'][0]
    assert r['telemetry']=='unavailable'
    assert all(a['state']=='unknown' for a in r['agents'] if a['id']!='coordinator')
    state.run_id='run_other';path.write_text(state.model_dump_json())
    assert all(not a['tasks'] for a in view(host)['runs'][0]['agents'] if a['id']!='coordinator')


def test_multiple_runs_sort_active_first_and_explicit_selection_is_stable(host):
    run,state,path=recorded(host)
    other=run.model_copy(update={'run_id':'run_parallel','invocation_id':'ui_parallel','status':'running','completed_at':None})
    with host[1].store.transaction(write=True) as data:data.runs[other.run_id]=other
    otherstate=state.model_copy(deep=True);otherstate.run_id=other.run_id;otherstate.workflow_stage='specialists'
    for i in otherstate.requested_specialists:i.status='running'
    otherstate.completed_assessments=[]
    otherpath=host[1].checkpoint_path(other);otherpath.parent.mkdir(parents=True);otherpath.write_text(otherstate.model_dump_json())
    v=view(host);assert v['selected_run_id']==other.run_id and v['active_run_count']==1
    v=view(host,run=run.run_id);assert v['selected_run_id']==run.run_id
    byid={r['run_id']:r for r in v['runs']}
    assert all(not t['finding'] for a in byid[other.run_id]['agents'][1:] for t in a['tasks'])
    assert any(t['finding'] for a in byid[run.run_id]['agents'] for t in a['tasks'])
    assert view(host,run='all')['selected_run_id'] == other.run_id # Legacy URL resolves to one active run, never a merged graph.


def test_five_source_checks_require_actual_recent_observations(host):
    now=datetime.now(timezone.utc)
    from program_coordinator.control_host.operations import SYSTEMS
    host[1].operations_health=[OpsHealth(system=s,status='Available',checked_at=now.isoformat().replace('+00:00','Z')) for s in SYSTEMS]
    assert view(host)['fresh_source_count']==5
    host[1].operations_health[0].checked_at=(now-timedelta(minutes=6)).isoformat().replace('+00:00','Z')
    v=view(host);assert v['fresh_source_count']==4 and v['sources'][0]['status'].startswith('Stale')
    host[1].mode='live_model'
    assert view(host)['model_state']=='Not checked' and view(host)['last_completed_model_run_at'] is None


def test_foreign_metadata_does_not_enter_counts_or_findings(host):
    run,state,path=recorded(host)
    other=run.model_copy(update={'run_id':'run_foreign','customer_id':'CUST-FOREIGN'})
    with host[1].store.transaction(write=True) as data:data.runs[other.run_id]=other
    v=view(host);assert v['total_permitted_runs']==1
    assert host[0].get('/control-api/agent-workspace?run_id=run_foreign',headers=headers()).status_code==404


def test_verified_standard_handoff_retains_pending_lab_authority(tmp_path):
    from coordinator.evals.phase08_4a.probe import environment, investigate as standard_investigate
    with environment(tmp_path) as fixture:
        source = standard_investigate(fixture)
        before = fixture[3].db_path.read_bytes()
        calls = fixture[2].calls
        run = view(fixture)['runs'][0]
        handoff = source['handoffs'][0]
        assert run['case_id'] == 'CR-019'
        assert run['handoff']['kind'] == 'external'
        assert run['handoff']['label'] == 'Handoff verified · Lab authorization pending'
        assert run['handoff']['record_id'] == handoff['intake']['id']
        assert run['handoff']['version'] == handoff['version']
        assert handoff['intake']['lab_authorization'] == 'pending'
        assert all(a['state'] in {'completed', 'not_invoked'} for a in run['agents'])
        assert fixture[3].db_path.read_bytes() == before and fixture[2].calls == calls
