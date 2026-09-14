"""Offline verification of live dispatch; no paid models in automated tests."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from agents.tracing import trace, custom_span
from program_investigator.telemetry import Recorder
from program_coordinator.control_host.runtime import DemoInvestigation, metadata_router
from program_coordinator.control_host import __main__ as live
from coordinator.tests.test_phase10_autonomous import connected, action, wait, HEADERS
from coordinator.tests.test_phase09_demo_reset import run_case


def test_only_main_cases_use_live_and_provider_failure_never_falls_back(monkeypatch, tmp_path):
    actual = AsyncMock(return_value='live result')
    monkeypatch.setattr(live, 'live_investigation', actual)
    runtime = DemoInvestigation(None, None)
    runtime.opening = AsyncMock(return_value='scripted result')
    async def check():
        for case in ('CR-017','CR-019','QE-004','DR-009','QE-011'):
            request = SimpleNamespace(event=SimpleNamespace(change_id=case))
            result = await runtime(request, None, tmp_path/'state.json')
            assert result == ('scripted result' if case=='QE-011' else 'live result')
        assert actual.await_count == 4 and runtime.opening.await_count == 1
        actual.side_effect = RuntimeError('provider unavailable')
        with pytest.raises(RuntimeError, match='provider unavailable'):
            await runtime(SimpleNamespace(event=SimpleNamespace(change_id='CR-019')), None, tmp_path/'state.json')
        assert runtime.opening.await_count == 1
        with pytest.raises(ValueError, match='LIVE_DEMO_CASE_REQUIRED'):
            await runtime(SimpleNamespace(event=SimpleNamespace(change_id='UNKNOWN')), None, tmp_path/'state.json')
    asyncio.run(check())


def test_concurrent_scripted_trace_does_not_disable_or_mix_live_metadata():
    DemoInvestigation(None, None)
    a, b = Recorder('trace_'+'a'*32), Recorder('trace_'+'b'*32)
    metadata_router.recorders.update({a.trace_id:a, b.trace_id:b})
    async def observed(recorder):
        with trace('live metadata test', trace_id=recorder.trace_id):
            await asyncio.sleep(.01)
            with custom_span('safe work', data={'role':'coordinator'}):
                await asyncio.sleep(.01)
    async def scripted():
        with trace('scripted metadata test', disabled=True):
            with custom_span('scripted work'):
                await asyncio.sleep(.015)
    async def check():
        await asyncio.gather(observed(a), scripted(), observed(b))
    try:
        asyncio.run(check())
        assert len(a.spans)==len(b.spans)==1
        assert {s['trace_id'] for s in a.spans}=={a.trace_id}
        assert {s['trace_id'] for s in b.spans}=={b.trace_id}
    finally:
        metadata_router.recorders.clear()


def test_host_persists_per_case_mode_and_scripted_opening_needs_no_key(tmp_path, monkeypatch):
    with connected(tmp_path/'mixed') as env:
        c,h,_,doubles = env
        # Exercise the real host + dispatcher with an explicit offline stand-in
        # at the paid-call boundary; historical mode must not follow host.mode.
        async def paid_boundary(incoming, run, checkpoint, **kwargs):
            return await doubles[incoming.event.change_id](incoming,run,checkpoint)
        monkeypatch.setattr(live, 'live_investigation', paid_boundary)
        runtime = DemoInvestigation(h.config, h.store)
        async def immediate(seconds): pass
        runtime.opening.pacing_sleep = immediate
        h.investigate, h.mode = runtime, 'live_model'
        monkeypatch.setattr('program_coordinator.control_host.readiness.model_configuration',
            lambda: {'credential_present':False, 'status':'unavailable'})
        assert action(env,'prepare').status_code==200
        assert wait(env,{'touchless_handoff_verified','failed'})['status']=='touchless_handoff_verified'
        for case in ('CR-017','CR-019','QE-004','DR-009'):
            value = run_case(env,case)
            assert value['runs'][0]['execution_mode']=='live_model'
        assert c.get('/control-api/cases/QE-011').json()['runs'][0]['execution_mode']=='deterministic_test'
        view=c.get('/control-api/cases/CR-017',headers=HEADERS).json()
        assert view['case_runtime_modes']==runtime.case_modes
        assert c.get('/control-api/agent-workspace',headers=HEADERS).json()['runs']
        # Configuration changes never relabel saved runs.
        h.mode='deterministic_test'
        assert c.get('/control-api/cases/CR-019').json()['runs'][0]['execution_mode']=='live_model'
