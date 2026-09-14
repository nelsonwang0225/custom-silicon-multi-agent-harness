"""Owned local HTTP/MCP preview. Offline by default; explicit live-model opt-in."""
import argparse
from pathlib import Path
import uvicorn
from mock_enterprise.config import PROJECT, Settings
from mock_enterprise.seed import initialize
from mock_enterprise.standard_upgrade import install as standard
from mock_enterprise.delivery_upgrade import install as delivery
from coordinator.evals.phase08_4a.network import network
from coordinator.evals.phase08_2.doubles import InvestigationDouble
from coordinator.evals.phase08_4a.doubles import StandardInvestigationDouble
from coordinator.evals.phase08_4b.doubles import QualityInvestigationDouble
from coordinator.evals.phase08_4c.doubles import DeliveryInvestigationDouble
from coordinator.evals.phase08_5.doubles import ManagerDouble
from program_coordinator.infrastructure.source_gateway import SourceGateway, HumanDecisionGateway
from program_coordinator.application.store import ActivityStore
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import ProgramChangeEvent
from program_coordinator.control_host.server import ControlHost, create_app


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--port',type=int,default=18191)
    p.add_argument('--source-port',type=int,default=18192)
    p.add_argument('--mcp-port',type=int,default=19192)
    p.add_argument('--ui-origin',default='http://127.0.0.1:5191')
    p.add_argument('--cr-delay',type=float,default=.05,help='Deterministic browser fixture specialist delay only')
    p.add_argument('--live-models',action='store_true',help='Use the existing paid model for the four main cases and Concierge; QE-011 stays scripted. Preserve existing storage.')
    args = p.parse_args()
    root = args.root.absolute()
    if not any(root.is_relative_to(PROJECT/'.cache'/phase) for phase in ('phase09-1','phase09-2','phase09-3')):
        p.error('Only isolated .cache/phase09-1, phase09-2 or phase09-3 storage is supported')
    root.mkdir(parents=True,exist_ok=True)
    settings = Settings(root/'source.sqlite3',root,True)
    # Explicit developer fixture launch creates a missing isolated test DB only.
    # Neither an existing source nor its host metadata is ever reset on restart.
    if not settings.db_path.exists():
        initialize(settings)
    # The installers are additive and idempotent. Run them before any source
    # server owns the database so an existing demo receives newly introduced
    # optional columns without resetting its business records.
    standard(settings)
    delivery(settings)
    with network(settings,args.source_port,args.mcp_port) as (url,mcp):
        source, human = SourceGateway(url,demo_mode=True), HumanDecisionGateway(url,demo_mode=True)
        config = HarnessConfig(mcp_url=mcp)
        doubles = {'CR-017':InvestigationDouble(source,delay=args.cr_delay),'CR-019':StandardInvestigationDouble(config),
                   'QE-004':QualityInvestigationDouble(config),'QE-011':QualityInvestigationDouble(config,pace_opening=True),'DR-009':DeliveryInvestigationDouble(config)}
        async def investigate(incoming,run,checkpoint):
            return await doubles[incoming.event.change_id](incoming,run,checkpoint)
        event = ProgramChangeEvent.model_validate_json((PROJECT/'coordinator/scenarios/human_review.json').read_text())
        store = ActivityStore(root/'metadata')
        if args.live_models:
            from program_coordinator.control_host.runtime import DemoInvestigation
            investigate = DemoInvestigation(config, store)
        host = ControlHost(store,source,human,config,investigate,event,
                           mode='live_model' if args.live_models else 'deterministic_test',demo_settings=settings)
        if not args.live_models:
            host.concierge_manager = ManagerDouble()
        try:
            uvicorn.run(create_app(host,allowed_origins=(args.ui_origin,)),host='127.0.0.1',port=args.port,access_log=False,log_level='error')
        finally:
            source.close(); human.close()


if __name__=='__main__': main()
