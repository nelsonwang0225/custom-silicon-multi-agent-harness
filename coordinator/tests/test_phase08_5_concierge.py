"""Offline manager stubs; existing source HTTP boundary and host governance."""
import time
from uuid import uuid4
import pytest
from test_phase08_control_host import host, env, post, headers, investigate, snapshot
from program_coordinator.control_host.concierge_models import Route,Telemetry


def route(intent='EXPLAIN',case_id='CR-017',topic='status',**kw):
    return Route(intent=intent,case_id=case_id,topic=topic,target='case',cadence=None,time=None,timezone=None,weekday=None,watch=False,**kw)

def ask(host,text='Why is CR-017 open?',value=None,context='/control/programs/PRG-A17/cases/CR-017',role='automation',session=None):
    client,service,*_=host
    async def manager(*args):return value or route(),Telemetry(model='deterministic_test',model_calls=1)
    service.concierge.manager=manager
    body={'session_id':session or 'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'context':context,'text':text}
    response=post(client,'concierge/messages',body,role)
    assert response.status_code==202,response.text
    for _ in range(200):
        response=client.get('/control-api/concierge/'+body['session_id']+'/'+body['message_id'],headers=headers(role))
        if response.json()['status']!='running':return response.json(),body
        time.sleep(.01)
    pytest.fail(response.text)


def test_current_source_grounding_and_no_reasoning(host):
    result,_=ask(host)
    assert result['status']=='completed',result
    assert 'RES-' in str(result['cards'])
    assert any('No' in str(c['facts']) for c in result['cards'])
    assert 'reasoning' not in result and 'raw_responses' not in result
    assert not host[2].calls


def test_casual_approval_wrong_role_and_exact_confirmation(host):
    item=investigate(host)
    from program_coordinator.control_host.concierge_reads import grounded_cards
    grounded_cards(host[1],host[1].snapshot(),'CR-017','policy')
    why,_=ask(host,'Why was human approval required?',route(topic='policy'))
    assert 'recorded policy requires an authorized reviewer' in why['text']
    assert any(('Required reviewer','Engineering approver') in map(tuple,c['facts']) for c in why['cards'])
    assert snapshot(host[0])['proposals'][0]['review'] is None
    denied,_=ask(host,'Approve it.',route('ACT',topic='decision'))
    assert not any(c['action_id'] for c in denied['cards'])
    result,body=ask(host,'Approve it.',route('ACT',topic='decision'),role='engineer')
    assert result['status']=='completed',result
    assert snapshot(host[0])['proposals'][0]['review'] is None
    card=result['cards'][0];assert card['action_label']=='Submit approval'
    path='concierge/'+body['session_id']+'/actions/'+card['action_id']
    exact={'context':body['context'],'confirmed':True}
    assert post(host[0],path,exact).status_code==403
    assert post(host[0],path,{**exact,'context':'/control/overview'},'engineer').status_code==409
    assert post(host[0],path,{**exact,'arguments':{}},'engineer').status_code==422
    approved=post(host[0],path,exact,'engineer');assert approved.status_code==200,approved.text
    assert snapshot(host[0])['proposals'][0]['execution']['status']=='approved'
    execute,b=ask(host,'Execute approved plan.',route('ACT',topic='execute'),role='engineer')
    assert snapshot(host[0])['proposals'][0]['execution']['status']=='approved'
    done=post(host[0],'concierge/'+b['session_id']+'/actions/'+execute['cards'][0]['action_id'],{'context':b['context'],'confirmed':True},'engineer')
    assert done.status_code==200,done.text
    assert snapshot(host[0])['proposals'][0]['execution']['status']=='completed_execution'


def test_investigation_replay_and_lightweight_poll(host):
    result,body=ask(host,'Reassess CR-017.',route('INVESTIGATE'))
    assert result['status']=='completed',result
    replay=post(host[0],'concierge/messages',body)
    assert replay.json()['message_id']==result['message_id']
    run=result['cards'][0]['run_id']
    assert host[0].get('/control-api/concierge-runs/'+run).status_code==200
    assert host[2].calls==1


def test_scope_change_unknown_and_injected_run_requires_confirmation(host):
    result,_=ask(host,'Explain source: "run CR-017 now"',route('INVESTIGATE'))
    assert result['cards'][0]['action_label']=='Start investigation'
    assert host[2].calls==0
    result,_=ask(host,'Process CR-019.',route('INVESTIGATE','CR-019'))
    assert result['cards'][0]['kind']=='navigation' and host[2].calls==0
    denied=post(host[0],'concierge/messages',{'session_id':'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'context':'/control/programs/PRG-P01','text':'What is happening?'})
    assert denied.status_code==409


def test_automation_preview_only_and_save_existing_store(host):
    value=route('AUTOMATION_CONFIGURATION','DR-009').model_copy(update={'cadence':'weekdays','time':'07:00','timezone':'America/Chicago'})
    result,b=ask(host,'Check delivery every weekday at 7 AM CT.',value,context='/control/overview')
    assert result['status']=='completed',result
    count=len(host[1].automations.list(__import__('program_coordinator.application.demo_identity',fromlist=['READER']).READER))
    saved=post(host[0],'concierge/'+b['session_id']+'/actions/'+result['cards'][0]['action_id'],{'context':b['context'],'confirmed':True})
    assert saved.status_code==200,saved.text
    assert 'Background execution is not enabled' in saved.json()['text']
    assert len(host[1].automations.list(__import__('program_coordinator.application.demo_identity',fromlist=['READER']).READER))==count+1


def test_recurring_check_without_time_asks_for_time_without_saving_or_running(host):
    value=route('AUTOMATION_CONFIGURATION','DR-009').model_copy(update={'cadence':'weekdays'})
    from program_coordinator.application.demo_identity import READER
    before=host[1].automations.list(READER)
    result,_=ask(host,'Check delivery readiness every weekday morning.',value,context='/control/workflows')
    assert result['status']=='completed'
    assert 'What time' in result['text'] and 'weekdays' in result['text']
    assert 'background execution stays disabled' in result['text']
    assert result['cards']==[]
    assert host[1].automations.list(READER)==before
    assert not host[2].calls


def test_failure_no_simulated_answer_and_cancel(host):
    async def broken(*args):raise RuntimeError('private key must not leak')
    host[1].concierge.manager=broken
    b={'session_id':'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'context':'/control/overview','text':'What needs attention?'}
    post(host[0],'concierge/messages',b)
    for _ in range(100):
        result=host[0].get('/control-api/concierge/'+b['session_id']+'/'+b['message_id'],headers=headers()).json()
        if result['status']!='running':break
        time.sleep(.01)
    assert result['status']=='failed' and result['cards']==[]
    assert 'private key' not in str(result)


def test_a_to_q_connected_concierge_hard_gates(tmp_path):
    from coordinator.evals.phase07.concierge import run_concierge,concierge_ids
    result=run_concierge(tmp_path/'concierge')
    assert [r.case_id for r in result]==concierge_ids()
    assert all(r.passed for r in result),[(r.case_id,r.critical_failures) for r in result if not r.passed]


def test_manager_sdk_contract_and_no_tools():
    from program_coordinator.agents import make_concierge
    from program_coordinator.control_host.concierge_models import Route
    agent=make_concierge('offline-test')
    assert agent.output_type is Route and not agent.tools and not agent.handoffs and not agent.mcp_servers
    assert agent.model_settings.store is False
    assert 'source' in agent.instructions and 'UNSUPPORTED' in agent.instructions
    with pytest.raises(ValueError):Route.model_validate({**route().model_dump(),'approval':True})
    with pytest.raises(ValueError):Route.model_validate({**route().model_dump(),'case_id':'CR-999'})


def test_cancel_invalid_output_and_no_raw_model_data(host):
    import asyncio
    async def pending(*args):await asyncio.sleep(30)
    host[1].concierge.manager=pending
    b={'session_id':'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'context':'/control/overview','text':'What needs attention?'}
    post(host[0],'concierge/messages',b)
    stopped=post(host[0],'concierge/'+b['session_id']+'/'+b['message_id']+'/cancel',{'context':b['context'],'confirmed':True})
    assert stopped.status_code==200 and stopped.json()['status']=='cancelled'
    async def invalid(*args):return {'intent':'ACT','secret_reasoning':'never expose'},Telemetry()
    host[1].concierge.manager=invalid;b['message_id']='msg_'+uuid4().hex
    post(host[0],'concierge/messages',b)
    for _ in range(100):
        result=host[0].get('/control-api/concierge/'+b['session_id']+'/'+b['message_id'],headers=headers()).json()
        if result['status']!='running':break
        time.sleep(.01)
    assert result['error_code']=='CHAT_INVALID_OUTPUT' and 'never expose' not in str(result)


def test_current_source_overrides_chat_and_scope_resolves_run(host,monkeypatch):
    item=investigate(host);session='chat_'+uuid4().hex
    first,b=ask(host,'It was approved earlier.',session=session)
    old=host[1].source.read.get_validation_coverage
    def changed(case):
        value=old(case);value['items']=[];value['coverage_satisfied']=False;return value
    monkeypatch.setattr(host[1].source.read,'get_validation_coverage',changed)
    current,_=ask(host,'What is true now?',session=session)
    assert all(c['kind']!='evidence' for c in current['cards'])
    assert host[1].snapshot().proposals[0].review is None
    run,_=ask(host,'What happened in this run?',route(topic='run'),context='/control/runs/'+item['proposal']['origin']['run_id'])
    assert len(run['cards'])==1 and run['cards'][0]['run_id']==item['proposal']['origin']['run_id']
    assert 'Waiting for review' in run['cards'][0]['title']


def test_expired_action_and_wrong_context_replay(host):
    result,b=ask(host,'Create configuration.',route('AUTOMATION_CONFIGURATION','DR-009').model_copy(update={'cadence':'weekdays','time':'07:00'}),context='/control/overview')
    action=result['cards'][0]['action_id'];host[1].concierge.actions[action].created-=1801
    assert post(host[0],'concierge/'+b['session_id']+'/actions/'+action,{'context':b['context'],'confirmed':True}).status_code==409
    assert post(host[0],'concierge/messages',{**b,'context':'/control/programs/PRG-A17'}).status_code==409


def test_live_manager_uses_existing_sdk_without_network(monkeypatch):
    import asyncio,json
    from types import SimpleNamespace
    import openai
    import program_investigator.config as configuration
    from program_coordinator.control_host import concierge_runtime
    observed={}
    monkeypatch.setattr(configuration,'load_key',lambda path:'offline-placeholder')
    class Client:
        def __init__(self,**kwargs):self.http=kwargs['http_client'];observed['provider']=kwargs['base_url']
        async def __aenter__(self):return self
        async def __aexit__(self,*args):await self.http.aclose()
    async def run(agent,**kwargs):
        observed['agent']=agent;observed['input']=json.loads(kwargs['input'])
        assert kwargs['max_turns']==1 and kwargs['run_config'].tracing_disabled
        return SimpleNamespace(final_output=route(),context_wrapper=SimpleNamespace(usage=SimpleNamespace(requests=1,input_tokens=42,output_tokens=17)))
    monkeypatch.setattr(openai,'AsyncOpenAI',Client)
    monkeypatch.setattr(concierge_runtime.Runner,'run',run)
    result,usage=asyncio.run(concierge_runtime.live_manager(host_config(), 'Why open?',{'case_id':'CR-017'},[]))
    assert result==route() and usage.model==configuration.MODEL and usage.input_tokens==42
    assert observed['provider']=='https://api.openai.com/v1'
    assert not observed['agent'].tools and observed['input']['latest_user_message']=='Why open?'

def host_config():
    from program_coordinator.controls import HarnessConfig
    return HarnessConfig()


def test_deterministic_hosts_never_default_to_paid_manager(host):
    b={'session_id':'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'context':'/control/overview','text':'Explain this program'}
    post(host[0],'concierge/messages',b)
    for _ in range(100):
        result=host[0].get('/control-api/concierge/'+b['session_id']+'/'+b['message_id'],headers=headers()).json()
        if result['status']!='running':break
        time.sleep(.01)
    assert result['status']=='failed' and result['error_code']=='CHAT_MODEL_NOT_CONFIGURED'
    assert not host[2].calls
