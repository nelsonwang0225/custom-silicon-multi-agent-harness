"""Isolated real HTTP/MCP + deterministic SDK agents. No paid API calls."""
import asyncio
import time
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from coordinator.evals.phase08_5.probe import environment
from coordinator.evals.phase08_4b.doubles import QualityInvestigationDouble
from program_coordinator.control_host.server import create_app
from program_coordinator.control_host.demo_management import DemoManagement
from program_coordinator.application.models import WorkflowError
from coordinator.evals.phase10_knowledge_integration.doubles import scripted_retrieval
from coordinator.tests.test_phase09_demo_reset import reset, all_source

HEADERS = {'Origin':'http://testserver', 'X-Stratos-Action':'1',
           'X-Stratos-Demo-Profile':'automation', 'X-Stratos-Demo-Maintainer':'local-demo-reset'}


@contextmanager
def connected(root, delay=.15, agent_delay=.15):
    with environment(root) as (host, settings, doubles):
        doubles['QE-011'] = QualityInvestigationDouble(host.config, delay=agent_delay)
        host.demo_management = DemoManagement(host, settings)
        app = create_app(host, allowed_origins=('http://testserver',), allowed_hosts=('testserver',))
        async def sleep(seconds):
            assert seconds == 8
            await asyncio.sleep(delay)
        host.autonomous.sleep = sleep
        with TestClient(app) as client:
            env = client, host, settings, doubles
            assert reset(env).status_code == 200
            yield env


def action(env, name):
    epoch = env[0].get('/control-api/demo').json()['epoch']
    return env[0].post('/control-api/demo/autonomous/'+name, headers=HEADERS, json={'expected_epoch':epoch})


def enter(env):
    epoch = env[0].get('/control-api/demo').json()['epoch']
    return env[0].post('/control-api/demo/autonomous/enter', headers=HEADERS, json={'expected_epoch':epoch})


def status(env):
    return env[0].get('/control-api/demo/autonomous', headers=HEADERS).json()


def wait(env, states):
    for _ in range(400):
        value = status(env)
        if value['status'] in states: return value
        time.sleep(.025)
    pytest.fail(str(value))


def test_event_source_shared_workflow_handoff_and_replay(tmp_path):
    with connected(tmp_path/'autonomous') as env:
        c,h,settings,doubles = env
        baseline = all_source(settings)
        assert status(env)['status'] == 'idle'
        assert c.get('/control-api/cases/QE-011').status_code != 200
        result = action(env, 'prepare')
        assert result.status_code == 200, result.text
        assert result.json()['status'] == 'armed'
        assert doubles['QE-011'].calls == 0
        value = wait(env, {'touchless_handoff_verified','failed'})
        assert value['status'] == 'touchless_handoff_verified', value
        q = c.get('/control-api/cases/QE-011').json()
        assert q['context']['exception']['lot_id'] == 'LOT-B-219'
        assert q['context']['analysis']['affected_eligible_quantity'] == 0
        assert len(q['records']['investigations']) == 1 and not q['records']['plans']
        assert not q['records']['decisions'] and not q['records']['tasks']
        assert q['runs'][0]['trigger']['kind'] == 'source_event'
        # Internal redelivery goes through source validation and the shared key.
        replay = c.portal.call(h.autonomous.dispatch, h.autonomous.state().event)
        assert replay['replayed'] and replay['run_id'] == value['run_id']
        assert doubles['QE-011'].calls == 1
        after = all_source(settings)
        assert all(after[k] == v for k,v in baseline.items())
        result = action(env, 'reset')
        assert result.status_code == 200, result.text
        assert all_source(settings) == baseline
        assert not h.tasks
        assert c.get('/control-api/cases/QE-011').status_code != 200
        assert action(env, 'reset').status_code == 200
        assert action(env, 'prepare').status_code == 200
        again = wait(env, {'touchless_handoff_verified','failed'})
        assert again['status'] == 'touchless_handoff_verified', again
        assert again['event']['event_id'] != value['event']['event_id']
        assert doubles['QE-011'].calls == 2
        with h.store.transaction() as data:
            assert len(data.runs) == 1


def test_idle_navigation_and_pending_reset(tmp_path):
    with connected(tmp_path/'idle', delay=.5) as env:
        c,h,settings,doubles = env
        baseline = all_source(settings)
        for path in ('/control-api/case','/control-api/agent-workspace','/control-api/operations','/control-api/workflows'):
            c.get(path, headers=HEADERS)
        time.sleep(.6)
        assert doubles['QE-011'].calls == 0 and status(env)['status'] == 'idle'
        assert action(env, 'prepare').status_code == 200
        assert action(env, 'reset').status_code == 200
        time.sleep(.6)
        assert status(env)['status'] == 'idle' and doubles['QE-011'].calls == 0
        assert all_source(settings) == baseline


def test_actual_participation_then_human_handoff_and_operations(tmp_path):
    with connected(tmp_path/'activity', agent_delay=.6) as env, scripted_retrieval():
        c,h,settings,doubles = env
        # Explicit operator indexing uses the existing offline provider.
        from program_coordinator.application.demo_identity import AUTOMATION
        h.knowledge.sync(AUTOMATION)
        assert action(env, 'prepare').status_code == 200
        running = wait(env, {'workflow_running','failed'})
        assert running['status'] == 'workflow_running', running
        snapshot = c.get('/control-api/cases/CR-017', headers=HEADERS).json()
        summary = next(s for s in snapshot['case_summaries'] if s['change_id']=='QE-011')
        assert summary['state'] == 'investigating' and summary['attention'] == 'none'
        assert not any(d['requires_human'] for d in snapshot['decision_summaries'] if d['change_id']=='QE-011')
        for _ in range(80):
            workspace = c.get('/control-api/agent-workspace', headers=HEADERS).json()
            agents = workspace['runs'][0]['agents']
            if sum(bool(a['tasks']) for a in agents) == 5: break
            time.sleep(.02)
        assert {a['id'] for a in agents if a['tasks']} == {'coordinator','change_impact','manufacturing','validation_evidence','program_commercial'}
        assert workspace['runs'][0]['handoff'] is None
        done = wait(env, {'touchless_handoff_verified','failed'})
        assert done['status'] == 'touchless_handoff_verified', done
        workspace = c.get('/control-api/agent-workspace', headers=HEADERS).json()
        assert workspace['runs'][0]['handoff']['kind'] == 'complete'
        assert all(a['state'] in {'completed','not_invoked'} for a in workspace['runs'][0]['agents'])
        ops = c.get('/control-api/operations/runs/'+done['run_id'], headers=HEADERS)
        assert ops.status_code == 200, ops.text
        row = ops.json()['run']
        assert row['invocation_source'] == 'Manufacturing source event'
        assert row['event_id'] == done['event']['event_id'] and row['event_version'] == 1
        history = c.get('/control-api/runs', headers=HEADERS).json()
        assert len(history) == 1 and history[0]['change_id'] == 'QE-011'
        detail = c.get('/control-api/runs/'+done['run_id'], headers=HEADERS)
        assert detail.status_code == 200, detail.text
        events = c.get('/control-api/knowledge/events?run_id='+done['run_id'], headers=HEADERS).json()
        assert len(events) == 3
        assert all(e['profile']=='MANUFACTURING_QUALITY' and e['case_id']=='QE-011' for e in events)
        assert all(p['metadata']['program_id']=='PRG-A17' for e in events for p in e['passages'])
        q = c.get('/control-api/cases/QE-011').json()
        p=q['progress'][0]
        assert p['plan_id'] is None and not q['records']['plans']
        assert q['context']['analysis']['root_cause'] is None


@pytest.mark.parametrize('scope', ['full','QE-011'])
def test_reset_cancels_running_work_and_clears_only_owned_records(tmp_path, scope):
    with connected(tmp_path/'running', agent_delay=1.5) as env:
        baseline=all_source(env[2])
        assert action(env,'prepare').status_code == 200
        assert wait(env,{'workflow_running','failed'})['status']=='workflow_running'
        value=reset(env,scope)
        assert value.status_code==200,value.text
        time.sleep(.3)
        assert status(env)['status']=='idle' and not env[1].tasks
        assert all_source(env[2])==baseline
        with env[1].store.transaction() as data: assert not data.runs


@pytest.mark.parametrize('change', [
    {'event_name':'delivery_ready'}, {'event_version':2}, {'exception_id':'QE-004'},
    {'lot_id':'LOT-B-204'}, {'program_id':'PRG-OTHER'}, {'workflow_id':'delivery_readiness'},
])
def test_event_contract_rejects_arbitrary_dispatch(tmp_path, change):
    with connected(tmp_path/'invalid') as env:
        assert action(env,'prepare').status_code==200
        done=wait(env,{'touchless_handoff_verified','failed'})
        assert done['status']=='touchless_handoff_verified',done
        bad={**done['event'],**change}
        with pytest.raises(ValueError): env[0].portal.call(env[1].autonomous.dispatch,bad)
        assert env[3]['QE-011'].calls==1


def test_restart_disarms_without_source_publication(tmp_path):
    with environment(tmp_path/'restart') as (h,settings,doubles):
        doubles['QE-011']=QualityInvestigationDouble(h.config)
        h.demo_management=DemoManagement(h,settings)
        app=create_app(h,allowed_origins=('http://testserver',),allowed_hosts=('testserver',))
        with TestClient(app) as c:
            env=c,h,settings,doubles
            assert reset(env).status_code==200
            assert action(env,'prepare').status_code==200
        with TestClient(app) as c:
            env=c,h,settings,doubles
            assert status(env)['status']=='failed'
            assert status(env)['error_code']=='HOST_INTERRUPTED'
            assert h.autonomous.timer is None
            assert doubles['QE-011'].calls==0
            assert c.get('/control-api/cases/QE-011').status_code!=200


def test_scope_role_epoch_guards_and_generic_automations_stay_inactive(tmp_path):
    with connected(tmp_path/'guards') as env:
        c,h,settings,doubles=env
        epoch=c.get('/control-api/demo').json()['epoch']
        for role in ('reader','engineer','program_owner'):
            r=c.post('/control-api/demo/autonomous/prepare',headers={**HEADERS,'X-Stratos-Demo-Profile':role},json={'expected_epoch':epoch})
            assert r.status_code==409
        r=c.post('/control-api/demo/autonomous/prepare',headers=HEADERS,json={'expected_epoch':'stale'})
        assert r.status_code==409 and status(env)['status']=='idle'
        assert action(env,'prepare').status_code==200
        assert wait(env,{'touchless_handoff_verified','failed'})['status']=='touchless_handoff_verified'
        with h.automations.transaction() as data:
            assert all(not a.background_execution_enabled for a in data.definitions.values())
        assert doubles['DR-009'].calls==0 and doubles['QE-004'].calls==0 and doubles['CR-017'].calls==0


def test_app_entry_runs_touchlessly_without_login_or_maintenance_authority(tmp_path):
    with connected(tmp_path/'entry') as env:
        c,h,settings,doubles=env
        epoch=h.demo_management.state().epoch
        baseline=all_source(settings)
        headers={'Origin':'http://testserver','X-Stratos-Action':'1'}
        response=c.post('/control-api/demo/autonomous/enter',headers=headers,json={'expected_epoch':epoch})
        assert response.status_code==200 and response.json()['status']=='armed'
        assert h.demo_management.state().epoch==epoch # Entry never resets the demo.
        done=wait(env,{'touchless_handoff_verified','failed'})
        assert done['status']=='touchless_handoff_verified',done
        assert not h.quality.records('QE-011').decisions
        after=all_source(settings)
        assert all(after[k]==v for k,v in baseline.items())
        for profile in (None,'reader','engineer','program_owner','automation'):
            selected={**headers,**({'X-Stratos-Demo-Profile':profile} if profile else {})}
            again=c.post('/control-api/demo/autonomous/enter',headers=selected,json={'expected_epoch':epoch})
            assert again.status_code==200 and again.json()['run_id']==done['run_id']
        assert doubles['QE-011'].calls==1


def test_concurrent_app_entries_share_one_event_and_reset_requires_new_epoch(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    with connected(tmp_path/'entry-tabs',delay=.5) as env:
        c,h,settings,doubles=env
        epoch=h.demo_management.state().epoch
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses=list(pool.map(lambda _: enter(env),range(4)))
        assert all(r.status_code==200 for r in responses)
        assert len({r.json()['generation'] for r in responses})==1
        assert h.demo_management.state().epoch==epoch
        assert action(env,'reset').status_code==200
        stale=c.post('/control-api/demo/autonomous/enter',headers=HEADERS,json={'expected_epoch':epoch})
        assert stale.status_code==409
        time.sleep(.6)
        assert doubles['QE-011'].calls==0 and status(env)['status']=='idle'
        assert enter(env).status_code==200
        assert wait(env,{'touchless_handoff_verified','failed'})['status']=='touchless_handoff_verified'


def test_entry_does_not_retry_failure_or_bypass_local_origin(tmp_path):
    with connected(tmp_path/'entry-failed') as env:
        c,h,settings,doubles=env
        epoch=h.demo_management.state().epoch
        denied=c.post('/control-api/demo/autonomous/enter',json={'expected_epoch':epoch})
        assert denied.status_code==403 and status(env)['status']=='idle'
        state=h.autonomous.state()
        state.status='failed';state.error_code='HOST_INTERRUPTED'
        h.autonomous.save(state)
        assert enter(env).json()['status']=='failed'
        assert doubles['QE-011'].calls==0


def test_entry_checks_keep_reads_available_and_reset_prevents_late_arming(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    with connected(tmp_path/'entry-read-reset') as env:
        c,h,settings,doubles=env
        entered,release=Event(),Event()
        verify=h.demo_management.verify
        def paused(scope='full', **kw):
            if scope=='QE-011' and not kw.get('allow_pending'):
                entered.set()
                assert release.wait(10)
            return verify(scope,**kw)
        monkeypatch.setattr(h.demo_management,'verify',paused)
        epoch=h.demo_management.state().epoch
        with ThreadPoolExecutor(max_workers=2) as pool:
            entry=pool.submit(enter,env)
            assert entered.wait(10)
            assert c.get('/control-api/capabilities',headers=HEADERS).status_code==200
            reset_request=pool.submit(c.post,'/control-api/demo/autonomous/reset',headers=HEADERS,json={'expected_epoch':epoch})
            try:
                for _ in range(100):
                    if h.demo_management.resetting: break
                    time.sleep(.01)
                assert h.demo_management.resetting
            finally:
                release.set()
            assert entry.result(10).status_code==409
            assert reset_request.result(10).status_code==200
        time.sleep(.2)
        assert status(env)['status']=='idle' and doubles['QE-011'].calls==0


def test_concurrent_event_redelivery_claims_one_run(tmp_path):
    with connected(tmp_path/'duplicate', agent_delay=.6) as env:
        assert action(env,'prepare').status_code == 200
        value=wait(env,{'workflow_running','failed'})
        assert value['status']=='workflow_running'
        async def redeliver():
            return await asyncio.gather(*(env[1].autonomous.dispatch(value['event']) for _ in range(3)))
        results=env[0].portal.call(redeliver)
        assert all(r['replayed'] and r['run_id']==value['run_id'] for r in results)
        assert wait(env,{'touchless_handoff_verified','failed'})['status']=='touchless_handoff_verified'
        with env[1].store.transaction() as data: assert len(data.runs)==1
        assert env[3]['QE-011'].calls==1


def test_authoritative_event_mismatch_and_changed_source_fail_closed(tmp_path, monkeypatch):
    with connected(tmp_path/'stale') as env:
        assert action(env,'prepare').status_code == 200
        value=wait(env,{'touchless_handoff_verified','failed'})
        bad={**value['event'],'event_timestamp':'2026-09-12T00:00:00Z'}
        with pytest.raises(WorkflowError,match='SOURCE_EVENT_MISMATCH'):
            env[0].portal.call(env[1].autonomous.dispatch,bad)
        current=env[1].quality.context('QE-011')
        monkeypatch.setattr(env[1].quality,'context',lambda case:current.model_copy(update={'context_digest':'changed'}))
        with pytest.raises(WorkflowError,match='STALE_SOURCE_EVENT'):
            env[0].portal.call(env[1].autonomous.dispatch,value['event'])
        assert env[3]['QE-011'].calls==1


def test_reset_drains_inflight_source_publication_without_launch(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from mock_enterprise import autonomous_quality
    entered,release=Event(),Event()
    original=autonomous_quality.publish
    def blocked(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    monkeypatch.setattr(autonomous_quality,'publish',blocked)
    with connected(tmp_path/'publishing') as env:
        baseline=all_source(env[2])
        assert action(env,'prepare').status_code == 200
        assert entered.wait(5)
        epoch=env[1].demo_management.state().epoch
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(env[0].post,'/control-api/demo/autonomous/reset',headers=HEADERS,json={'expected_epoch':epoch})
            try:
                for _ in range(100):
                    if env[1].demo_management.resetting:break
                    time.sleep(.01)
                assert env[1].demo_management.resetting
            finally:release.set()
            response=pending.result(10)
        assert response.status_code==200,response.text
        assert status(env)['status']=='idle' and env[3]['QE-011'].calls==0
        assert all_source(env[2])==baseline


def test_touchless_has_no_decision_or_consequential_writes(tmp_path):
    with connected(tmp_path/'touchless') as env:
        c,h,settings,doubles=env
        baseline=all_source(settings)
        assert action(env,'prepare').status_code==200
        assert wait(env,{'touchless_handoff_verified','failed'})['status']=='touchless_handoff_verified'
        records=h.quality.records('QE-011')
        assert len(records.investigations)==1
        assert not records.plans and not records.decisions and not records.tasks
        context=h.quality.context('QE-011')
        assert context.analysis.root_cause is None and context.analysis.affected_eligible_quantity==0
        assert context.material[0].disposition=='hold'
        after=all_source(settings)
        assert all(after[k]==v for k,v in baseline.items())


def test_partial_reset_disarms_and_requires_explicit_reconciliation(tmp_path, monkeypatch):
    with connected(tmp_path/'partial',delay=.8) as env:
        c,h,settings,doubles=env
        assert action(env,'prepare').status_code==200
        old_epoch=h.demo_management.state().epoch
        reconcile=h.demo_management.reconcile
        def fail(*args): raise RuntimeError('deterministic reconciliation failure')
        monkeypatch.setattr(h.demo_management,'reconcile',fail)
        response=action(env,'reset')
        assert response.status_code==409 and response.json()['error']['code']=='DEMO_BASELINE_INVALID'
        assert response.headers['x-stratos-demo-epoch']!=old_epoch
        assert h.demo_management.state().recovery_required
        assert status(env)['status']=='failed' and h.autonomous.timer is None
        time.sleep(.9)
        assert doubles['QE-011'].calls==0
        monkeypatch.setattr(h.demo_management,'reconcile',reconcile)
        assert action(env,'reset').status_code==200
        assert status(env)['status']=='idle' and not h.demo_management.state().recovery_required
