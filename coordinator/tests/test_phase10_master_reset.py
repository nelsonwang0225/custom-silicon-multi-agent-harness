"""Master restart verification across isolated HTTP sources and scripted agents."""
import threading
import time

from coordinator.tests.test_phase09_demo_reset import all_source, run_case, execute
from coordinator.tests.test_phase10_autonomous import connected, HEADERS, wait, status, enter


def restart(env, **body):
    return env[0].post('/control-api/demo/reset', headers=HEADERS, json={
        'scope': 'full', 'confirmation': 'RESET', 'restart_opening': True,
        'expected_epoch': env[1].demo_management.state().epoch, **body})


def test_master_reset_restores_all_sources_and_restarts_only_qe011(tmp_path):
    with connected(tmp_path/'master', delay=.8) as env:
        c,h,settings,doubles = env
        baseline = all_source(settings)
        standard = run_case(env, 'CR-019')
        assert standard['handoffs'][0]['status'] == 'handoff_verified'
        for case in ('CR-017','QE-004','DR-009'):
            execute(env, case, run_case(env, case))
        assert enter(env).status_code == 200
        first = wait(env, {'touchless_handoff_verified','failed'})
        assert first['status'] == 'touchless_handoff_verified'
        response = restart(env)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result['validation']['baseline_valid'] and result['opening_status'] == 'armed'
        assert all_source(settings) == baseline
        assert all(result['validation']['scenario_checks'].values())
        initial = c.get('/control-api/cases/CR-019').json()
        assert initial['runs'] == [] and initial['eligibility'] is None
        assert not initial['handoffs'] and not h.source.read.get_standard_validation_intakes('CR-019')['items']
        summary = c.get('/control-api/cases/CR-017').json()
        assert all(s['state'] == 'new' for s in summary['case_summaries'] if s['change_id'] in {'CR-017','CR-019','QE-004','DR-009'})
        assert (h.store.directory/'demo-archives'/result['epoch']/'source.json').is_file()
        second = wait(env, {'touchless_handoff_verified','failed'})
        assert second['status'] == 'touchless_handoff_verified', second
        assert second['generation'] != first['generation']
        assert [r['change_id'] for r in c.get('/control-api/runs', headers=HEADERS).json()] == ['QE-011']
        assert doubles['QE-011'].calls == 2
        assert run_case(env, 'CR-019')['handoffs'][0]['status'] == 'handoff_verified'


def test_master_reset_drains_active_source_writes_before_restore(tmp_path):
    with connected(tmp_path/'drain', delay=.8) as env:
        c,h,settings,_ = env
        baseline = all_source(settings)
        entered, release = threading.Event(), threading.Event()
        original = h.standard.process
        def delayed(*args):
            entered.set()
            assert release.wait(5)
            return original(*args)
        h.standard.process = delayed
        response = c.post('/control-api/cases/CR-019/investigations', headers=HEADERS, json={
            'invocation_id':'ui_master_reset_drain','change_id':'CR-019','workflow_id':'requirement_change_analysis'})
        assert response.status_code == 202, response.text
        assert entered.wait(5)
        threading.Timer(.2, release.set).start()
        response = restart(env)
        assert response.status_code == 200, response.text
        assert response.json()['opening_status'] == 'armed'
        assert all_source(settings) == baseline
        time.sleep(.15)
        assert h.source.read.get_standard_validation_intakes('CR-019')['items'] == []


def test_master_reset_cancels_running_opening_and_rejects_stale_repeat(tmp_path):
    with connected(tmp_path/'active', agent_delay=1.5) as env:
        assert enter(env).status_code == 200
        first = wait(env, {'workflow_running','failed'})
        assert first['status'] == 'workflow_running'
        old_epoch = env[1].demo_management.state().epoch
        result = restart(env)
        assert result.status_code == 200, result.text
        new_generation = status(env)['generation']
        assert new_generation != first['generation']
        assert restart(env, expected_epoch=old_epoch).status_code == 409
        assert status(env)['generation'] == new_generation
        done = wait(env, {'touchless_handoff_verified','failed'})
        assert done['status'] == 'touchless_handoff_verified', done
        assert len(env[0].get('/control-api/runs', headers=HEADERS).json()) == 1


def test_master_reset_guards_and_failed_opening_are_truthful(tmp_path, monkeypatch):
    with connected(tmp_path/'failure') as env:
        c,h,_,_ = env
        epoch = h.demo_management.state().epoch
        body = {'scope':'full','confirmation':'RESET','restart_opening':True,'expected_epoch':epoch}
        for role in ('reader','engineer','program_owner'):
            assert c.post('/control-api/demo/reset', headers={**HEADERS,'X-Stratos-Demo-Profile':role}, json=body).status_code == 409
        assert restart(env, scope='CR-019').status_code == 422
        assert h.demo_management.state().epoch == epoch
        async def unavailable(**kwargs):
            raise RuntimeError('private provider diagnostic')
        monkeypatch.setattr(h.autonomous, 'arm', unavailable)
        response = restart(env)
        assert response.status_code == 200
        result = response.json()
        assert result['validation']['baseline_valid']
        assert result['opening_status'] == 'failed' and result['opening_error'] == 'AUTONOMOUS_START_FAILED'
        assert status(env)['status'] == 'failed'
        assert enter(env).json()['status'] == 'failed'
        assert not h.tasks
