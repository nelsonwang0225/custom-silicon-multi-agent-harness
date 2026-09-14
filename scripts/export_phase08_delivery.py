"""Export current delivery contracts without replacing historical phase snapshots."""
import json
from pathlib import Path
from program_coordinator.control_host.server import create_app
from program_coordinator.application.workflow_catalog import workflow_catalog
root=Path(__file__).resolve().parents[1]
(root/'docs/phase08-4c-host-openapi.json').write_text(json.dumps(create_app(None).openapi(),indent=2)+'\n')
(root/'mock_apps_ui/src/control/workflow-catalog.json').write_text(json.dumps([w.model_dump(mode='json') for w in workflow_catalog()],indent=2)+'\n')
