"""Scripted integration tests: real source HTTP + scoped MCP, deterministic SDK runner double."""
import json
import time
from pathlib import Path
from contextlib import contextmanager
from fastapi.testclient import TestClient
from mock_enterprise.config import Settings
from program_coordinator.application.store import ActivityStore
from program_coordinator.infrastructure.source_gateway import SourceGateway,HumanDecisionGateway
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import ProgramChangeEvent
from program_coordinator.control_host.server import ControlHost,create_app
from coordinator.evals.phase08_4b.fixtures import prepare,VARIANTS
from coordinator.evals.phase08_4a.network import network
from coordinator.evals.phase08_4b.doubles import QualityInvestigationDouble

ORIGIN='http://testserver'
def post(client,path,body,role='automation'):
    return client.post('/control-api/'+path,json=body,headers={'Origin':ORIGIN,'X-Stratos-Action':'1','X-Stratos-Demo-Profile':role})

def read(client):
    result=client.get('/control-api/cases/QE-004');assert result.status_code==200,result.text
    return result.json()

@contextmanager
def environment(root,variant='comparable'):
    root.mkdir(parents=True,exist_ok=True)
    settings=Settings(root/'source.sqlite3',root,True);prepare(settings,variant)
    with network(settings) as (url,mcp):
        source=SourceGateway(url,demo_mode=True);human=HumanDecisionGateway(url,demo_mode=True)
        config=HarnessConfig(mcp_url=mcp)
        double=QualityInvestigationDouble(config)
        event=ProgramChangeEvent.model_validate_json(Path('coordinator/scenarios/human_review.json').read_text())
        host=ControlHost(ActivityStore(root/'metadata'),source,human,config,double,event,mode='deterministic_test')
        try:
            with TestClient(create_app(host,allowed_origins=(ORIGIN,),allowed_hosts=('testserver',))) as client:
                yield client,host,double,settings
        finally:source.close();human.close()


def investigate(value,invocation='ui_quality_first'):
    client=value[0]
    response=post(client,'cases/QE-004/investigations',{'invocation_id':invocation,'change_id':'QE-004','workflow_id':'yield_exception_recovery'})
    assert response.status_code==202,response.text
    for _ in range(300):
        
        try: state=read(client)
        except AssertionError:
            from program_coordinator.control_host.quality import snapshot
            snapshot(value[1])
            raise
        if state['runs'] and state['runs'][0]['run_id']==response.json()['run_id'] and state['runs'][0]['status'] not in ('running','queued'):
            return state
        time.sleep(.03)
    raise AssertionError(str(state))
