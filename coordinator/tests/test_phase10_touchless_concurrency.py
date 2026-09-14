"""Deterministic local HTTP/SDK concurrency and touchless authority checks."""
import asyncio
import json
import time

import pytest
from coordinator.tests.test_phase10_autonomous import connected, action, wait, status, HEADERS
from coordinator.tests.test_phase09_demo_reset import reset
from coordinator.evals.phase10_knowledge_integration.doubles import scripted_retrieval


def start(env, case='CR-017', key='ui_concurrent_cr017'):
    return env[0].post('/control-api/workflows/requirement_change_analysis/runs', headers=HEADERS,
        json={'invocation_id':key,'workflow_id':'requirement_change_analysis','change_id':case})


def finish(env):
    for _ in range(400):
        if not env[1].tasks: return
        time.sleep(.025)
    pytest.fail('Admitted tasks did not settle')


def test_independent_event_and_manual_runs_and_receipts(tmp_path):
    with connected(tmp_path/'parallel', agent_delay=.5) as env, scripted_retrieval():
        c,h,settings,doubles=env
        from program_coordinator.application.demo_identity import AUTOMATION
        h.knowledge.sync(AUTOMATION)
        doubles['CR-017'].delay=1.2
        assert action(env,'prepare').status_code==200
        qe=wait(env,{'workflow_running','failed'})
        cr=start(env)
        assert cr.status_code==202,cr.text
        crid=cr.json()['run_id'];qeid=qe['run_id'];assert qeid!=crid
        live=c.get('/control-api/agent-workspace',headers=HEADERS).json()
        assert live['active_run_count']==2 and live['selected_run_id']==crid
        assert {r['invocation_source'] for r in live['runs']}=={'Source event','User initiated'}
        from coordinator.evals.phase08_5.probe import ask
        response,_=ask(env,'What are the agents working on?')
        assert {card['run_id'] for card in response['cards']}=={qeid,crid}
        chosen=c.get('/control-api/agent-workspace?run_id='+qeid,headers=HEADERS).json()
        assert chosen['selected_run_id']==qeid
        duplicate=start(env,key='ui_same_case_other')
        assert duplicate.status_code==409 and duplicate.json()['error']['code']=='RUN_ALREADY_RUNNING'
        assert wait(env,{'touchless_handoff_verified','failed'})['status']=='touchless_handoff_verified'
        with h.store.transaction() as data:
            assert data.runs[qeid].status=='completed' and data.runs[crid].status=='running'
        finish(env)
        with h.store.transaction() as data:
            assert data.runs[crid].status=='completed'
            assert data.runs[crid].recommendation.requires_human_review
            assert data.quality_recoveries[qeid].status=='handoff_verified'
            assert all(e.reference.run_id==crid for e in data.executions.values())
            assert all(a.case_id==data.runs[a.run_id].case_id for a in data.activity if a.run_id)
        states={rid:json.loads(h.checkpoint_path(type('Run',(),{'run_id':rid})()).read_text()) for rid in (qeid,crid)}
        invocations=[{i['invocation_id'] for i in state['requested_specialists']} for state in states.values()]
        assert not invocations[0]&invocations[1]
        assert all('validation_evidence' in {i['specialist'] for i in state['requested_specialists']} for state in states.values())
        for rid,expected,forbidden in ((qeid,'QE-011','CR-017'),(crid,'CR-017','QE-011')):
            calls=json.loads((h.checkpoint_path(type('Run',(),{'run_id':rid})()).parent/'tool-calls.json').read_text())
            assert forbidden not in json.dumps([call['arguments'] for call in calls])
            detail=c.get('/control-api/operations/runs/'+rid,headers=HEADERS).json()
            assert detail['run']['case_id']==expected
        qeops=c.get('/control-api/operations/runs/'+qeid,headers=HEADERS).json()['run']
        assert qeops['decision_state']=='Not required for executed actions'
        assert qeops['policy_route']=='Touchless / standard quality investigation'
        assert qeops['business_outcome']=='Quality investigation handoff verified'
        assert h.quality.records('QE-011').investigations[0].workflow_run_id==qeid
        for rid,case in ((qeid,'QE-011'),(crid,'CR-017')):
            knowledge=c.get('/control-api/knowledge/events?run_id='+rid,headers=HEADERS).json()
            assert knowledge and all(k['run_id']==rid and k['case_id']==case for k in knowledge)
        snapshot=c.get('/control-api/cases/CR-017',headers=HEADERS).json()
        assert next(s for s in snapshot['case_summaries'] if s['change_id']=='QE-011')['attention']=='none'
        assert not any(d['change_id']=='QE-011' for d in snapshot['decision_summaries'])


def test_capacity_denial_is_retryable_and_does_not_claim_or_lose_key(tmp_path):
    with connected(tmp_path/'capacity',agent_delay=.5) as env:
        env[1].max_concurrent_workflow_runs=1
        assert action(env,'prepare').status_code==200
        assert wait(env,{'workflow_running','failed'})['status']=='workflow_running'
        denied=start(env)
        assert denied.status_code==409 and denied.json()['error']['code']=='WORKFLOW_CAPACITY_REACHED'
        assert env[3]['CR-017'].calls==0
        finish(env)
        admitted=start(env)
        assert admitted.status_code==202,admitted.text
        finish(env)
        replay=start(env)
        assert replay.json()['replayed'] and replay.json()['run_id']==admitted.json()['run_id']
        assert env[3]['CR-017'].calls==1


def test_scoped_autonomous_reset_preserves_concurrent_cr017(tmp_path):
    with connected(tmp_path/'reset',agent_delay=1.5) as env:
        env[3]['CR-017'].delay=.7
        assert action(env,'prepare').status_code==200
        assert wait(env,{'workflow_running','failed'})['status']=='workflow_running'
        cr=start(env);assert cr.status_code==202,cr.text
        assert action(env,'reset').status_code==200
        assert status(env)['status']=='idle'
        with env[1].store.transaction() as data:
            assert cr.json()['run_id'] in data.runs
            assert all(data.cases[r.case_id].change_id=='CR-017' for r in data.runs.values())
        finish(env)
        with env[1].store.transaction() as data:
            assert data.runs[cr.json()['run_id']].status=='completed'
            assert data.executions


def test_default_capacity_admits_three_independent_cases_then_rejects_fourth(tmp_path):
    with connected(tmp_path/'three') as env:
        c,h,_,_=env
        assert h.max_concurrent_workflow_runs==3
        original=h.investigate;gate=asyncio.Event()
        async def paused(*args):
            await gate.wait()
            return await original(*args)
        h.investigate=paused
        try:
            assert action(env,'prepare').status_code==200
            assert wait(env,{'workflow_running','failed'})['status']=='workflow_running'
            assert start(env).status_code==202
            third=c.post('/control-api/workflows/delivery_readiness/runs',headers=HEADERS,
                json={'invocation_id':'ui_third','workflow_id':'delivery_readiness','change_id':'DR-009'})
            assert third.status_code==202,third.text
            fourth=start(env,'CR-019','ui_fourth')
            assert fourth.status_code==409 and fourth.json()['error']['code']=='WORKFLOW_CAPACITY_REACHED'
            assert c.get('/control-api/agent-workspace',headers=HEADERS).json()['active_run_count']==3
            with h.store.transaction() as data:assert all(r.invocation_id!='ui_fourth' for r in data.runs.values())
        finally:
            async def release():gate.set()
            c.portal.call(release)
            finish(env)


def test_full_reset_disarms_qe_and_preserves_existing_busy_policy(tmp_path):
    with connected(tmp_path/'full-reset',agent_delay=1.5) as env:
        env[3]['CR-017'].delay=.7
        assert action(env,'prepare').status_code==200
        assert wait(env,{'workflow_running','failed'})['status']=='workflow_running'
        cr=start(env);assert cr.status_code==202
        refused=reset(env,'full')
        assert refused.status_code==409 and refused.json()['error']['code']=='DEMO_RESET_BUSY'
        with env[1].store.transaction() as data:
            assert data.runs[cr.json()['run_id']].status=='running'
        finish(env)
        assert reset(env,'full').status_code==200
        assert status(env)['status']=='idle'
        with env[1].store.transaction() as data:assert not data.runs


@pytest.mark.parametrize('variant',['actions','queue','procedure','type','tasks'])
def test_ineligible_policy_escalates_without_handoff(tmp_path,monkeypatch,variant):
    from mock_enterprise import autonomous_quality
    original=autonomous_quality.records
    def records():
        values=original()
        q=values['manufacturing.quality_exception'][0]
        p=values['engineering.quality_procedure'][0]
        if variant=='actions':q['requested_actions']=['release_material']
        if variant=='queue':p['standard_policy']['queue_status']='inactive'
        if variant=='procedure':p['status']='retired'
        if variant=='type':q['exception_type']='nonstandard_retest'
        if variant=='tasks':p['tasks']=['Release material']
        return values
    with connected(tmp_path/variant) as env:
        monkeypatch.setattr(autonomous_quality,'records',records)
        assert action(env,'prepare').status_code==200
        result=wait(env,{'escalated','failed'})
        assert result['status']=='escalated',result
        records=env[1].quality.records('QE-011')
        assert not any((records.investigations,records.plans,records.decisions,records.tasks))
        snapshot=env[0].get('/control-api/cases/CR-017',headers=HEADERS).json()
        assert next(s for s in snapshot['case_summaries'] if s['change_id']=='QE-011')['state']=='escalated'
