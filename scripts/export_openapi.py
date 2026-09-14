#!/usr/bin/env python3
"""Export actual app schemas; read-only, no business mutations."""
import json
from pathlib import Path
from mock_enterprise.app import create_app
from mock_enterprise.config import PROJECT, Settings


def main():
    schema = create_app(Settings.environment()).openapi()
    target = PROJECT / 'docs/openapi.json'
    target.write_text(json.dumps(schema, indent=2, sort_keys=True) + '\n')
    print('Exported docs/openapi.json from the implemented application.')


if __name__ == '__main__':
    main()
