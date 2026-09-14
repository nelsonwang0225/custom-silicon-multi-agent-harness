"""Isolated source fixtures for optional live evaluation; never an agent capability.

Only this developer bootstrap reads seed/SQLite. Agents see normal scoped MCP/HTTP.
No expected answers, grader rubrics or eval documents are inserted into retrieval.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
from mock_enterprise.app import create_app
from mock_enterprise.config import Settings
from mock_enterprise.seed import initialize
from program_coordinator.application.execution import ExecutionService, reference
from program_coordinator.application.store import ActivityStore
from program_coordinator.infrastructure.source_gateway import SourceGateway, HumanDecisionGateway, ENGINEER
from .execution_probe import analysis_fixture

ROOT = Path(__file__).resolve().parents[3]
VARIANTS = {'gap', 'covered', 'wrong_software', 'bypass', 'scheduled', 'ambiguous'}


def seed_variant(variant):
    if variant not in VARIANTS:
        raise ValueError('Unknown live source fixture')
    seed = json.loads((ROOT / 'fixtures/seed.json').read_text())
    if variant in {'covered', 'wrong_software'}:
        full = deepcopy(next(r for r in seed['validation']['results'] if r['id'] == 'RES-SHORT-B'))
        full.update(id='RES-FULL-B-EVAL', actual_suite_minutes=480,
                    observed_minutes_by_context_bin={'32768': 160, '65536': 160, '131072': 160})
        if variant == 'wrong_software':
            config = deepcopy(next(r for r in seed['engineering']['configurations'] if r['id'] == 'CFG-B-01'))
            config.update(id='CFG-OLD-SW-EVAL', firmware='FW-2.2', runtime='RT-4.0')
            seed['engineering']['configurations'].append(config)
            full.update(id='RES-OLD-SW-EVAL', configuration_id=config['id'])
        else:
            # Set descriptive context before initialization binds result snapshots.
            config = next(r for r in seed['engineering']['configurations'] if r['id'] == full['configuration_id'])
            config['validation_support'] = (
                'Applicable completed evidence for WF-LC-V2 is recorded in '
                'RES-FULL-B-EVAL; engineering review remains pending.'
            )
        seed['validation']['results'].append(full)
    return seed


def initialize_source(variant, directory):
    settings = Settings(directory / 'enterprise.sqlite3', directory, True)
    initialize(settings, source=seed_variant(variant))
    if variant == 'scheduled':
        # Fixed synthetic scheduled state via the unchanged Phase 06 boundary,
        # before the live run's read-only fingerprint. No model can access this.
        with TestClient(create_app(settings)) as http:
            source = SourceGateway(demo_mode=True, http_client=http)
            human = HumanDecisionGateway(demo_mode=True, http_client=http)
            store = ActivityStore(directory / 'setup-activity')
            run = analysis_fixture(store, source)
            service = ExecutionService(store, source)
            p = service.prepare(run.run_id, 'scheduled_fixture')
            service.review(reference(p), 'approve', 'DEVELOPER synthetic scheduled fixture; reviewer simulated.', ENGINEER, human)
            if service.resume(reference(p)).status != 'completed_execution':
                raise ValueError('Scheduled source fixture did not verify')
    return settings


def fingerprint(settings):
    settings.validate(existing=True)
    with sqlite3.connect(f'file:{settings.db_path}?mode=ro', uri=True) as con:
        return hashlib.sha256('\n'.join(con.iterdump()).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description='Developer-only live eval source; NO AI or real human approval.')
    parser.add_argument('--storage', type=Path, required=True)
    parser.add_argument('--variant', choices=sorted(VARIANTS), default='gap')
    parser.add_argument('--port', type=int)
    parser.add_argument('--fingerprint', action='store_true')
    args = parser.parse_args()
    directory = args.storage.absolute()
    if not directory.resolve().is_relative_to(ROOT / '.cache/phase07'):
        parser.error('Live source storage must be isolated under .cache/phase07')
    settings = Settings(directory / 'enterprise.sqlite3', directory, True)
    if args.fingerprint:
        print(fingerprint(settings))
        return
    if not args.port or not 0 < args.port < 65536:
        parser.error('A loopback port is required')
    settings = initialize_source(args.variant, directory)
    import uvicorn
    uvicorn.run(create_app(settings), host='127.0.0.1', port=args.port, access_log=False, log_level='warning')


if __name__ == '__main__':
    main()
