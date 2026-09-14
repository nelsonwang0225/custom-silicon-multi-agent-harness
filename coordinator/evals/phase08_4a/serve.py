"""Explicit isolated browser fixture: deterministic runner, real HTTP/MCP. No model calls."""
import argparse
from pathlib import Path
import signal
from uuid import uuid4
import uvicorn
from .fixtures import VARIANTS,prepare
from .network import network
from .doubles import StandardInvestigationDouble
from coordinator.evals.phase08_2.doubles import InvestigationDouble
from mock_enterprise.config import Settings,PROJECT
from program_coordinator.controls import HarnessConfig
from program_coordinator.application.store import ActivityStore
from program_coordinator.infrastructure.source_gateway import SourceGateway,HumanDecisionGateway
from program_coordinator.control_host.server import ControlHost,create_app
from program_coordinator.models import ProgramChangeEvent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant',choices=VARIANTS,default='success')
    p.add_argument('--source-port',type=int,default=18040);p.add_argument('--mcp-port',type=int,default=19040)
    p.add_argument('--host-port',type=int,default=18085);p.add_argument('--ui-origin',default='http://127.0.0.1:5176')
    p.add_argument('--delay',type=float,default=.35)
    args=p.parse_args();root=PROJECT/'.cache/phase08-4a/browser'/uuid4().hex
    root.mkdir(parents=True);settings=Settings(root/'source.sqlite3',root,True);prepare(settings,args.variant)
    with network(settings,args.source_port,args.mcp_port) as (source_url,mcp_url):
        source=SourceGateway(source_url,demo_mode=True);human=HumanDecisionGateway(source_url,demo_mode=True)
        config=HarnessConfig(mcp_url=mcp_url)
        standard=StandardInvestigationDouble(config,delay=args.delay);material=InvestigationDouble(source,delay=args.delay)
        async def investigate(incoming,run,checkpoint):
            return await (standard if incoming.event.change_id=='CR-019' else material)(incoming,run,checkpoint)
        event=ProgramChangeEvent.model_validate_json((PROJECT/'coordinator/scenarios/human_review.json').read_text())
        host=ControlHost(ActivityStore(root/'metadata'),source,human,config,investigate,event,mode='deterministic_test')
        print(f'SCRIPTED INTEGRATION FIXTURE · No paid model · {args.variant} · {root}',flush=True)
        try:uvicorn.run(create_app(host,allowed_origins=(args.ui_origin,)),host='127.0.0.1',port=args.host_port,access_log=False)
        finally:source.close();human.close()
if __name__=='__main__':main()
