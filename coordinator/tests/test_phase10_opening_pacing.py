"""Full-team, explicitly paced preview; offline HTTP/MCP, no paid models."""
import asyncio
from collections import Counter
import time

import pytest

from coordinator.evals.phase08_4b.doubles import QualityInvestigationDouble
from coordinator.tests.test_phase10_autonomous import connected, action, wait, HEADERS
from program_coordinator.quality import policy


def test_paced_opening_uses_all_domains_and_coordinator_phases(tmp_path):
    pauses=[]
    async def record_delay(seconds):pauses.append(seconds)
    with connected(tmp_path/'paced') as env:
        client,host,_,doubles=env
        double=QualityInvestigationDouble(host.config,pace_opening=True,pacing_sleep=record_delay)
        doubles['QE-011']=double
        assert action(env,'prepare').status_code==200
        done=wait(env,{'touchless_handoff_verified','failed'})
        assert done['status']=='touchless_handoff_verified',done
        h=double.harnesses[0]
        assert Counter(pauses)==Counter({84:4,12:3})
        assert [phase for role,phase in h.runner.phases if role=='coordinator']==['triage','reconcile','synthesis']
        expected={'change_impact','validation_evidence','program_commercial','manufacturing'}
        assert {r.specialist for r in h.state.completed_assessments}==expected
        assert {r.specialist for r in h.state.final_package.specialist_findings}==expected
        change=next(i for i in h.state.requested_specialists if i.specialist=='change_impact')
        assert any(c['tool']=='get_configuration' and c['invocation_id']==change.invocation_id for c in h.sources.calls)
        workspace=client.get('/control-api/agent-workspace',headers=HEADERS).json()
        assert workspace['runs'][0]['demo_pacing_min_seconds']==120
        assert all(a['state']=='completed' for a in workspace['runs'][0]['agents'])
        assert not host.quality.records('QE-011').decisions
        h.state.completed_assessments=[r for r in h.state.completed_assessments if r.specialist!='change_impact']
        assert policy(h.state,h.sources).rule=='quality_analysis_incomplete'


@pytest.mark.parametrize('blocked_delay',[12,84])
def test_reset_cancels_paced_coordinator_or_specialists(tmp_path,blocked_delay):
    entered=[]
    gate=asyncio.Event()
    async def pause(seconds):
        if seconds==blocked_delay:
            entered.append(seconds)
            await gate.wait()
    with connected(tmp_path/str(blocked_delay)) as env:
        env[3]['QE-011']=QualityInvestigationDouble(env[1].config,pace_opening=True,pacing_sleep=pause)
        assert action(env,'prepare').status_code==200
        for _ in range(100):
            if entered:break
            time.sleep(.025)
        assert entered
        assert action(env,'reset').status_code==200
        assert not env[1].tasks
        assert env[0].get('/control-api/runs',headers=HEADERS).json()==[]
