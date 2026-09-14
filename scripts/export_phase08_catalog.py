"""Developer-only export of registry-derived browser fallback metadata and host schema."""
import json
from pathlib import Path
from program_coordinator.application.workflow_catalog import workflow_catalog
from program_coordinator.control_host.server import create_app

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    (ROOT / 'mock_apps_ui/src/control/workflow-catalog.json').write_text(json.dumps(
        [w.model_dump(mode='json') for w in workflow_catalog()], indent=2) + '\n')
    (ROOT / 'docs/phase08-3-host-openapi.json').write_text(json.dumps(create_app(None).openapi(), indent=2) + '\n')
