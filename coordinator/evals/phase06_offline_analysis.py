"""Developer-only existing CaseHarness/model-double bridge. NO model/API calls.

Uses the existing Phase 05 deterministic specialist fixtures and runner double.
It is not a live investigation and is never runtime retrieval or an agent tool.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'coordinator/tests'))
from agents import set_tracing_disabled
from test_workflow_service import ExistingHarnessAdapter, invocation, actor
from program_coordinator.application.service import WorkflowService
from program_coordinator.application.store import ActivityStore
from program_coordinator.controls import HarnessConfig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata-dir', type=Path, required=True)
    args = parser.parse_args()
    set_tracing_disabled(True)
    identity = actor()
    handler = ExistingHarnessAdapter()
    service = WorkflowService(ActivityStore(args.metadata_dir), config=HarnessConfig(), investigate=handler,
                              actors=[identity], execution_mode='deterministic_test')
    result = asyncio.run(service.invoke(invocation(invocation_id='phase06_offline_analysis'), identity))
    if result.status != 'completed':
        raise RuntimeError('Offline existing harness failed')
    print(json.dumps({'run_id': result.run.run_id, 'case_id': result.run.case_id,
                      'policy_path': result.run.recommendation.policy_path, 'model_calls': 0,
                      'mode': 'deterministic_existing_harness_model_double'}))


if __name__ == '__main__':
    main()
