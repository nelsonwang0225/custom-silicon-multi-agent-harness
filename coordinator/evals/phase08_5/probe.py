"""Real isolated HTTP/MCP; model/SDK workflow doubles. No paid API access."""
import json
import time
from contextlib import contextmanager
from uuid import uuid4
from fastapi.testclient import TestClient
from mock_enterprise.config import Settings,PROJECT
from mock_enterprise.standard_upgrade import install as install_standard
from coordinator.evals.phase08_4a.fixtures import additions
from coordinator.evals.phase08_4c.fixtures import prepare,mutate
from coordinator.evals.phase08_4a.network import network
from coordinator.evals.phase08_4c.doubles import DeliveryInvestigationDouble
from coordinator.evals.phase08_4b.doubles import QualityInvestigationDouble
from coordinator.evals.phase08_4a.doubles import StandardInvestigationDouble
from coordinator.evals.phase08_2.doubles import InvestigationDouble
from program_coordinator.controls import HarnessConfig
from program_coordinator.application.store import ActivityStore
from program_coordinator.infrastructure.source_gateway import SourceGateway,HumanDecisionGateway
from program_coordinator.control_host.server import ControlHost,create_app
from program_coordinator.models import ProgramChangeEvent
from .doubles import ManagerDouble

@contextmanager
def environment(root,variant='base',standard='success',source_port=None,mcp_port=None):
    root.mkdir(parents=True,exist_ok=True)
    settings=Settings(root/'source.sqlite3',root,True);prepare(settings,variant);install_standard(settings,additions=additions(standard))
    with network(settings,source_port,mcp_port) as (url,mcp):
        source=SourceGateway(url,demo_mode=True);human=HumanDecisionGateway(url,demo_mode=True);config=HarnessConfig(mcp_url=mcp)
        doubles={'CR-017':InvestigationDouble(source,delay=.05),'CR-019':StandardInvestigationDouble(config),
            'QE-004':QualityInvestigationDouble(config),'DR-009':DeliveryInvestigationDouble(config)}
        async def investigate(incoming,run,checkpoint):return await doubles[incoming.event.change_id](incoming,run,checkpoint)
        event=ProgramChangeEvent.model_validate_json((PROJECT/'coordinator/scenarios/human_review.json').read_text())
        host=ControlHost(ActivityStore(root/'metadata'),source,human,config,investigate,event,mode='deterministic_test')
        host.concierge_manager=ManagerDouble()
        try:yield host,settings,doubles
        finally:source.close();human.close()

@contextmanager
def client_environment(root,variant='base',standard='success'):
    with environment(root,variant,standard) as (host,settings,doubles):
        with TestClient(create_app(host,allowed_origins=('http://testserver',),allowed_hosts=('testserver',))) as client:
            yield client,host,settings,doubles

def post(client,path,body,role='automation'):
    return client.post('/control-api/'+path,json=body,headers={'Origin':'http://testserver','X-Stratos-Action':'1','X-Stratos-Demo-Profile':role})

def ask(env,text,case=None,role='automation',session=None):
    body={'session_id':session or 'chat_'+uuid4().hex,'message_id':'msg_'+uuid4().hex,'context':'/control/programs/PRG-A17/cases/'+case if case else '/control/overview','text':text}
    r=post(env[0],'concierge/messages',body,role);assert r.status_code==202,r.text
    for _ in range(400):
        r=env[0].get('/control-api/concierge/'+body['session_id']+'/'+body['message_id'],headers={'X-Stratos-Demo-Profile':role});turn=r.json()
        if turn['status']!='running':
            assert turn['status']=='completed',turn
            return turn,body
        time.sleep(.02)
    raise AssertionError('Concierge did not finish')

def wait_run(env,turn,case):
    run=turn['cards'][0]['run_id']
    for _ in range(600):
        state=env[0].get('/control-api/cases/'+case).json()
        value=next((r for r in state['runs'] if r['run_id']==run),None)
        if value and value['status']!='running':
            # Investigation completion precedes the host's CR-017 preparation
            # boundary. Wait for the admitted task before launching another case;
            # do not reinterpret RUN_ALREADY_RUNNING as an eval hard-gate failure.
            if not env[1].tasks:
                return state
        time.sleep(.03)
    raise AssertionError('Workflow did not finish')

def confirm(env,turn,body,role='automation'):
    return post(env[0],'concierge/'+body['session_id']+'/actions/'+turn['cards'][0]['action_id'],{'context':body['context'],'confirmed':True},role)
