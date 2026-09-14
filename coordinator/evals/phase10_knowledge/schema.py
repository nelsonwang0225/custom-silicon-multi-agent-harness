"""Developer-only schema generation with isolated source setup, no model calls."""
import json
from pathlib import Path
from mock_enterprise.config import Settings
from mock_enterprise.seed import initialize
from program_coordinator.control_host.server import ControlHost,create_app
from program_coordinator.application.store import ActivityStore
from program_coordinator.infrastructure.source_gateway import SourceGateway,HumanDecisionGateway
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import ProgramChangeEvent
root=Path('.cache/phase10-rag/schema').absolute();root.mkdir(parents=True,exist_ok=True)
settings=Settings(root/'source.sqlite3',root,True)
if not settings.db_path.exists(): initialize(settings)
source=SourceGateway(demo_mode=True);human=HumanDecisionGateway(demo_mode=True)
async def no_model(*args): raise RuntimeError('NO_MODEL')
event=ProgramChangeEvent.model_validate_json(Path('coordinator/scenarios/human_review.json').read_text())
host=ControlHost(ActivityStore(root/'metadata'),source,human,HarnessConfig(),no_model,event,mode='deterministic_test',demo_settings=settings)
Path('docs/phase10-knowledge-host-openapi.json').write_text(json.dumps(create_app(host).openapi(),indent=2)+'\n')
source.close();human.close()
print('Generated complete host schema offline')
