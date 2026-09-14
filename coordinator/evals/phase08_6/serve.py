"""Scripted integration fixture, real local HTTP/MCP, no paid models."""
import argparse
from uuid import uuid4
import uvicorn
from mock_enterprise.config import PROJECT
from program_coordinator.control_host.server import create_app
from program_coordinator.application.execution_models import SourceFailure
from coordinator.evals.phase08_5.probe import environment

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--variant',choices=('base','partial','mismatch'),default='base');args=parser.parse_args()
    with environment(PROJECT/'.cache/phase08-6/browser'/uuid4().hex,source_port=18044,mcp_port=19044) as (host,_,__):
        if args.variant=='partial':
            def fail(*args):raise SourceFailure('SOURCE_WRITE_REJECTED')
            host.source.delivery_link=fail
        elif args.variant=='mismatch':
            original=host.delivery.records
            def mismatch():
                value=original()
                if value.commitments:value.commitments[0].quantity+=1
                return value
            host.delivery.records=mismatch
        uvicorn.run(create_app(host,allowed_origins=('http://127.0.0.1:5180',)),host='127.0.0.1',port=18089,access_log=False)
if __name__=='__main__':main()
