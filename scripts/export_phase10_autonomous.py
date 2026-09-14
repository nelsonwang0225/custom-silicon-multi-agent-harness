"""Export the host contract using isolated deterministic demo wiring; no model calls."""
import json
from pathlib import Path
from uuid import uuid4
from coordinator.evals.phase08_5.probe import environment
from program_coordinator.control_host.demo_management import DemoManagement
from program_coordinator.control_host.server import create_app

root=Path(__file__).resolve().parents[1]
with environment(root/'.cache/phase10-autonomous'/('schema_'+uuid4().hex)) as (host,settings,_):
    host.demo_management=DemoManagement(host,settings)
    schema=create_app(host).openapi()
(root/'docs/phase10-autonomous-host-openapi.json').write_text(json.dumps(schema,indent=2)+'\n')
print('Exported docs/phase10-autonomous-host-openapi.json from isolated demo wiring.')
