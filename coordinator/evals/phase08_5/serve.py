"""Explicit scripted integration server. Paid models never run here."""
import argparse
from uuid import uuid4
import uvicorn
from mock_enterprise.config import PROJECT
from program_coordinator.control_host.server import create_app
from .probe import environment

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-port',type=int,default=18043);p.add_argument('--mcp-port',type=int,default=19043)
    p.add_argument('--host-port',type=int,default=18088);p.add_argument('--ui-origin',default='http://127.0.0.1:5179')
    args=p.parse_args()
    with environment(PROJECT/'.cache/phase08-5/browser'/uuid4().hex,source_port=args.source_port,mcp_port=args.mcp_port) as (host,_,__):
        uvicorn.run(create_app(host,allowed_origins=(args.ui_origin,)),host='127.0.0.1',port=args.host_port,access_log=False)
if __name__=='__main__':main()
