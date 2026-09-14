"""Operations integrity through isolated HTTP/MCP and persisted source receipts."""
import json
import time
from pathlib import Path
from uuid import uuid4
import pytest
from coordinator.evals.phase08_5.probe import client_environment,ask,wait_run,confirm,post
from program_coordinator.control_host.operations_artifacts import evals,EVAL_ARTIFACTS,read_json
from program_coordinator.control_host.operations import rows,health
from program_coordinator.application.observability import visible
from program_coordinator.application.execution_models import SourceFailure
from program_investigator.config import PROJECT


def test_historical_eval_truth_and_semantic_skips():
    values,missing=evals(PROJECT)
    by={v.eval_id:v for v in values}
    original=by['live-original'];assert (original.mode,original.passed,original.total,original.hard_gate)==('live',4,6,'FAIL')
    for key,case in [('live-covered','cr017_covered'),('live-scheduled','cr017_scheduled')]:
        v=by[key];assert (v.passed,v.total,v.hard_gate)==(1,1,'PASS');assert v.cases[0].case_id==case
    for v in values:
        assert len(v.critical_failures)==sum(len(c.critical_failures) for c in v.cases)
        assert v.semantic=='Skipped / unavailable'
    assert by['offline-08-5'].total==112


def test_eval_counts_are_read_not_invented_and_fail_closed(tmp_path):
    assert evals(tmp_path)[0]==[]
    key,_,relative=EVAL_ARTIFACTS[-2];target=tmp_path/relative;target.parent.mkdir(parents=True)
    original=json.loads((PROJECT/relative).read_text());target.write_text(json.dumps(original))
    assert evals(tmp_path)[0][0].total==len(original['cases'])
    original['scorecard']['total_cases']=999;target.write_text(json.dumps(original))
    assert evals(tmp_path)[0]==[]
    target.unlink();target.symlink_to(PROJECT/relative);assert evals(tmp_path)[0]==[]
    with pytest.raises(ValueError):read_json(tmp_path,'../secret')
    with pytest.raises(ValueError):read_json(tmp_path,'/etc/passwd')


@pytest.fixture
def env(tmp_path):
    with client_environment(tmp_path/'operations') as value:yield value


def read(env,path=''):
    r=env[0].get('/control-api/operations'+path,headers={'X-Stratos-Demo-Profile':'automation'});assert r.status_code==200,r.text;return r.json()


def launch(env,case,session=None):
    t,b=ask(env,'Investigate '+case,case,session=session);wait_run(env,t,case);return t['cards'][0]['run_id'],b['session_id']


def test_four_workflows_participation_evidence_and_read_only_poll(env):
    for case in ('CR-017','CR-019','QE-004','DR-009'):
        run,session=launch(env,case);detail=read(env,'/runs/'+run)
        assert detail['run']['case_id']==case and detail['run']['case_link'].endswith(case)
        assert detail['run']['invocation_source']=='Concierge'
        assert detail['evidence'] and detail['calls']
        assert detail['agents'][0]['name']=='Program Coordinator'
        names=[a['name'] for a in detail['agents']]
        assert 'manufacturing' in names if case in ('QE-004','DR-009') else True
        assert detail['input_tokens'] is None and detail['model_latency_ms'] is None
        assert any(a['duration_ms'] is not None for a in detail['agents'][1:])
        s=read(env,'/sessions/'+session);assert run in s['run_ids']
        if case=='CR-019':
            assert detail['run']['business_outcome']=='Handoff verified · Lab authorization pending'
            assert detail['actions'][0]['verification']=='Verified'
        if case=='DR-009':assert '600' in str(detail['facts']) and '800' in str(detail['facts'])
    before=env[1].store.path.read_bytes();counts=[v.calls for v in env[3].values()]
    read(env,'/runs');read(env,'/runs')
    assert env[1].store.path.read_bytes()==before and [v.calls for v in env[3].values()]==counts
    assert env[0].get('/control-api/operations/runs/../../etc/passwd').status_code!=200
    assert env[0].get('/control-api/operations/artifact?path=/etc/passwd').status_code==404


def test_runtime_complete_is_not_success_and_human_wait(env):
    run,_=launch(env,'CR-017');d=read(env,'/runs/'+run)
    assert d['run']['runtime_state']=='completed' and d['run']['business_outcome']=='Waiting for human review'
    assert d['human_wait_ms'] is not None and d['run']['duration_ms'] is not None
    with env[1].store.transaction(write=True) as data:
        data.executions.clear();data.runs[run].recommendation.policy_path='escalation_required';data.runs[run].recommendation.escalation_reason='Required source dependency missing'
    assert read(env,'/runs')[0]['business_outcome']=='Escalation required'


@pytest.mark.parametrize('failure',['partial','mismatch'])
def test_execution_and_readback_separate(env,failure):
    run,session=launch(env,'DR-009')
    t,b=ask(env,'Approve it','DR-009',role='program_owner');assert confirm(env,t,b,'program_owner').status_code==200
    if failure=='partial':
        def fail(*args):raise SourceFailure('SOURCE_WRITE_REJECTED')
        env[1].source.delivery_link=fail
    else:
        # Real ERP receipt persists; independently read source record is deliberately mismatched.
        original=env[1].delivery.records
        def wrong():
            value=original()
            if value.commitments:value.commitments[0].quantity+=1
            return value
        env[1].delivery.records=wrong
    t,b=ask(env,'Execute approved plan','DR-009',role='program_owner');confirm(env,t,b,'program_owner')
    d=read(env,'/runs/'+run)
    if failure=='partial':
        assert d['run']['business_outcome']=='Partial execution'
        assert next(a for a in d['actions'] if a['name']=='ERP commitment')['verification']=='Verified'
        assert next(a for a in d['actions'] if a['name']=='Planner update')['status']=='Failed'
    else:
        assert d['run']['verification_state']=='Mismatch'
        assert next(a for a in d['actions'] if a['name']=='ERP commitment')['status']=='Succeeded'
    assert d['run']['attention'] and d['failure']


def test_concierge_decision_confirmation_automation_and_sanitization(env):
    run,session=launch(env,'CR-017')
    t,b=ask(env,'Approve it','CR-017',role='engineer');assert confirm(env,t,b,'engineer').status_code==200
    t,b=ask(env,'Check DR-009 every weekday at 7 AM CT',session=session);assert confirm(env,t,b).status_code==200
    s=read(env,'/sessions/'+session)
    assert not any(c['plan_id'] for c in s['confirmations'])  # Engineering confirmation belongs to its own session.
    assert any(c['automation_id'] for c in s['confirmations'])
    assert not any(c['kind']=='decision' for t in s['turns'] for c in t['cards'])
    assert 'action_id' not in str(s) and 'reasoning' not in s and 'audio' not in s
    assert visible('sk-testsecret /Users/private/key Authorization: Bearer xyz').count('[redacted]')>=1
    assert '/Users/' not in visible('/Users/test/private')
    # A new service reads history in the existing index, no chat-memory dependency.
    env[1].concierge.turns.clear();assert read(env,'/sessions/'+session)['session_id']==session


def test_source_health_unknown_available_stale_and_error(env):
    assert all(v['status']=='Unknown / not checked' for v in read(env)['health'])
    assert all(v['status']=='Available' for v in read(env,'/health'))
    for h in env[1].operations_health:h.checked_at='2020-01-01T00:00:00Z'
    assert all(v.status.startswith('Stale') for v in health(env[1]))
    from program_coordinator.application.execution_models import SourceReadFailure
    def fail(*args):raise SourceReadFailure('SOURCE_READ_FAILED')
    env[1].source.read.get_program=fail
    assert read(env,'/health')[-1]['status']=='Unavailable'


def test_missing_invocations_and_tools_do_not_become_completed(env):
    run,_=launch(env,'CR-017');path=env[1].artifacts/run/'case-state.json'
    value=json.loads(path.read_text());value['requested_specialists']=[];path.write_text(json.dumps(value))
    calls=env[1].artifacts/run/'tool-calls.json';calls.write_text(json.dumps([{'tool':'get_program','role':'coordinator','status':'failed','error':True,'arguments':{'program_id':'PRG-A17','authorization':'secret'},'latency_ms':8}]))
    d=read(env,'/runs/'+run);assert len(d['agents'])==1 and d['calls'][0]['status']=='Failed'
    assert 'authorization' not in str(d['calls'])
    (env[1].artifacts/run/'report.json').write_text(json.dumps({'run_id':run,'case_id':env[1].store.runs(__import__('program_coordinator.application.demo_identity',fromlist=['READER']).READER,customer_id='CUST-FML01',program_id='PRG-A17')[0].case_id,'model':'test-model','trace_id':'trace_example','usage':{'input_tokens':20,'output_tokens':8,'total_tokens':28},'generations':[{'latency_ms':16}],'secret':'do not expose'}))
    d=read(env,'/runs/'+run);assert d['total_tokens']==28 and d['model_latency_ms']==16 and d['run']['trace_id']=='trace_example'
    assert 'do not expose' not in str(d)
    report=env[1].artifacts/run/'report.json';value=json.loads(report.read_text());value['usage']=None;report.write_text(json.dumps(value))
    assert read(env,'/runs/'+run)['total_tokens'] is None

def test_live_host_retains_existing_sdk_metadata_without_model_calls(env,monkeypatch):
    import asyncio
    from program_coordinator.control_host import __main__ as live
    from program_coordinator import __main__ as runtime
    from program_investigator import config
    run,_=launch(env,'CR-017')
    with env[1].store.transaction() as data:record=data.runs[run]
    checkpoint=env[1].store.directory/'live-observer-test'/run/'case-state.json'
    checkpoint.parent.parent.mkdir()
    monkeypatch.setattr(config,'load_key',lambda _: 'test-credential-never-networked')
    async def execute(config,event,recorder,key,report,folder,run_record=None):
        recorder.generations.append({'latency_ms':7,'usage':{'input_tokens':11,'output_tokens':4,'total_tokens':15}})
        recorder.calls.append({'tool':'get_program','role':'coordinator','arguments':{'program_id':'PRG-A17'},'data':{'id':'PRG-A17'},'latency_ms':2})
        report['output']={'hidden':'not exposed as telemetry'}
        return 'observed'
    monkeypatch.setattr(runtime,'execute',execute)
    from types import SimpleNamespace
    result=asyncio.run(live.live_investigation(SimpleNamespace(event=env[1].event),record,checkpoint,
        config=env[1].config,store=env[1].store))
    assert result=='observed'
    report=json.loads((checkpoint.parent/'report.json').read_text())
    assert report['usage']['total_tokens']==15 and report['run_id']==run and 'output' not in report
    assert report['platform_trace_visibility_verified'] is False
    with env[1].store.transaction() as data:assert data.runs[run].trace_id==report['trace_id']
    assert (checkpoint.parent/'tool-calls.json').is_file() and (checkpoint.parent/'trace-metadata.json').is_file()


def test_current_staleness_comes_from_same_workbench_read(env):
    from coordinator.evals.phase08_4c.fixtures import mutate
    run,_=launch(env,'DR-009')
    mutate(env[2],lambda store:store.update('erp.delivery_state','STATE-DR-009',{'record_version':2}))
    current=read(env)
    assert next(r for r in current['runs'] if r['run_id']==run)['business_outcome']=='Stale proposal · Reassessment required'
    detail=read(env,'/runs/'+run)
    assert detail['run']['business_outcome']=='Stale proposal · Reassessment required'


def test_manual_run_referenced_by_chat_retains_origin_and_completed_decision(env):
    started=post(env[0],'cases/CR-017/investigations',{'invocation_id':'ui_manual_'+uuid4().hex})
    assert started.status_code==202
    run=started.json()['run_id']
    state=wait_run(env,{'cards':[{'run_id':run}]},'CR-017')
    _,chat=ask(env,'Why was human approval required?','CR-017')
    before=read(env,'/runs/'+run)['run']
    assert chat['session_id'] in before['session_ids']
    assert before['invocation_source']=='Manual'
    # Runtime completion precedes the host's automatic proposal preparation.
    # Wait for the exact business record needed by this review assertion.
    for _ in range(200):
        state=env[0].get('/control-api/cases/CR-017').json()
        if any(p['proposal']['origin']['run_id']==run for p in state['proposals']):break
        time.sleep(.01)
    ref=next(p for p in state['proposals'] if p['proposal']['origin']['run_id']==run)['execution']['reference']
    assert post(env[0],'proposals/review',{'reference':ref,'decision':'approve'},'engineer').status_code==200
    assert post(env[0],'proposals/execute',{'reference':ref}).status_code==200
    after=read(env,'/runs/'+run)['run']
    assert after['invocation_source']=='Manual'
    assert after['decision_state']=='Approved' and after['verification_state']=='Verified'
