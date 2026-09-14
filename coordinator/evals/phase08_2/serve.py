"""Owned isolated HTTP browser fixture. Deterministic doubles, never an AI run.

Fault selection is developer-only CLI input. No HTTP reset/fault/admin endpoints.
"""
import argparse
import os
from pathlib import Path
import subprocess
import signal
import socket
import time
from uuid import uuid4
import httpx
import uvicorn
from program_coordinator.application.store import ActivityStore
from program_coordinator.application.execution_models import SourceFailure
from program_coordinator.infrastructure.source_gateway import SourceGateway, HumanDecisionGateway
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import ProgramChangeEvent
from program_coordinator.control_host.server import ControlHost, create_app
from .doubles import InvestigationDouble, ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-port',type=int,default=18020)
    parser.add_argument('--host-port',type=int,default=18083)
    parser.add_argument('--ui-origin',default='http://127.0.0.1:5175')
    parser.add_argument('--fault',choices=['none','planner_rejected','readback_mismatch','analysis_failed','lab_failed'],default='none')
    parser.add_argument('--delay',type=float,default=1)
    args=parser.parse_args()
    for port in (args.source_port, args.host_port):
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))  # Refuse occupied ports before creating any fixture.
    run_id=uuid4().hex
    db=ROOT/'.demo'/f'phase08-2-{run_id}.sqlite3'
    metadata=ROOT/'.cache/phase08-2/browser'/run_id
    env={**os.environ,'DEMO_MODE':'true','DEMO_DB':str(db),'PYTHONPATH':str(ROOT/'src')}
    command=[str(ROOT/'.venv/bin/python'),'-m','mock_enterprise.cli']
    subprocess.run(command+['init-demo'],cwd=ROOT,env=env,check=True)
    source_command = [str(ROOT/'.venv/bin/python'), '-m', 'coordinator.evals.phase08_2_1.lab_source', '--port', str(args.source_port)] if args.fault == 'lab_failed' else command+['serve','--port',str(args.source_port)]
    source_process=subprocess.Popen(source_command,cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def terminate_source(signum, frame):
        if source_process.poll() is None:
            source_process.terminate()
    signal.signal(signal.SIGTERM, terminate_source)
    signal.signal(signal.SIGINT, terminate_source)
    url=f'http://127.0.0.1:{args.source_port}'
    source=SourceGateway(url,demo_mode=True);human=HumanDecisionGateway(url,demo_mode=True)
    try:
        with httpx.Client(trust_env=False) as http:
            for _ in range(100):
                try:
                    if source_process.poll() is not None:raise RuntimeError('Isolated source failed')
                    if http.get(url+'/health').status_code==200:break
                except httpx.HTTPError:pass
                if source_process.poll() is not None:raise RuntimeError('Isolated source failed')
                time.sleep(.05)
            else:raise RuntimeError('Isolated source unavailable')
        if args.fault=='planner_rejected':
            def fail(*args):raise SourceFailure('RESOURCE_CONFLICT')
            source.link=fail
        if args.fault=='readback_mismatch':
            original=source.read.get_validation_job
            def wrong(*args):
                value=original(*args);value['configuration_id']='CFG-TEST-MISMATCH';return value
            source.read.get_validation_job=wrong
        event=ProgramChangeEvent.model_validate_json((ROOT/'coordinator/scenarios/human_review.json').read_text())
        double=InvestigationDouble(source,delay=args.delay,failure=args.fault=='analysis_failed')
        host=ControlHost(ActivityStore(metadata),source,human,HarnessConfig(),double,event,mode='deterministic_test')
        print(f'DETERMINISTIC TEST DOUBLE. NO PAID MODEL. Isolated metadata: {metadata}',flush=True)
        uvicorn.run(create_app(host,allowed_origins=(args.ui_origin,)),host='127.0.0.1',port=args.host_port,access_log=False)
    finally:
        human.close();source.close()
        source_process.terminate()
        source_process.wait(timeout=10)

if __name__=='__main__':main()
