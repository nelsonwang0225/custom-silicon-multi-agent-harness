"""Offline CLI dispatch and host pause integration; no model/credential access."""
import contextlib
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest
from program_coordinator import __main__ as cli
from program_coordinator.application import execution_cli
from program_coordinator.application.models import WorkflowError
from test_workflow_service import service, invocation
import asyncio


@pytest.mark.parametrize('operation', ['prepare', 'inspect', 'review', 'resume'])
def test_phase06_cli_dispatch_never_loads_model_or_key(monkeypatch, capsys, tmp_path, operation):
    key = Mock(side_effect=AssertionError('No key access'))
    runner = Mock(side_effect=AssertionError('No model calls'))
    handler = Mock(return_value=0)
    monkeypatch.setattr(cli, 'load_key', key)
    monkeypatch.setattr(cli, 'execute', runner)
    monkeypatch.setattr(execution_cli, 'main', handler)
    monkeypatch.setattr(sys, 'argv', ['program_coordinator', '--phase06', operation, '--metadata-dir', str(tmp_path)])
    assert cli.main() == 0
    assert handler.call_args.args[0].phase06 == operation
    key.assert_not_called(); runner.assert_not_called()


@pytest.mark.parametrize('workflow', ['yield_exception_recovery', 'delivery_readiness'])
def test_phase06_cli_cannot_open_illustrative_workflows(monkeypatch, capsys, workflow):
    handler = Mock(side_effect=AssertionError('Must stop before source capability creation'))
    monkeypatch.setattr(execution_cli, 'main', handler)
    monkeypatch.setattr(sys, 'argv', ['program_coordinator', '--phase06', 'resume', '--workflow-id', workflow])
    assert cli.main() == 2
    assert json.loads(capsys.readouterr().out)['error_code'] == 'WORKFLOW_NOT_IMPLEMENTED'
    handler.assert_not_called()


@pytest.mark.parametrize('outcome', ['pause', 'failure'])
def test_existing_analysis_replay_can_prepare_without_reinvoking_sdk(monkeypatch, capsys, tmp_path, outcome):
    svc, actor, adapter = service(tmp_path / 'activity')
    result = asyncio.run(svc.invoke(invocation(), actor))
    assert result.status == 'completed'
    event = tmp_path / 'event.json'; event.write_text(invocation().event.model_dump_json())
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.setattr(cli, 'PROJECT', tmp_path)
    key = Mock(side_effect=AssertionError('Replay must not load credentials'))
    runner = Mock(side_effect=AssertionError('Replay must not invoke SDK'))
    monkeypatch.setattr(cli, 'load_key', key); monkeypatch.setattr(cli, 'execute', runner)
    source = Mock()
    monkeypatch.setattr(execution_cli, 'create_service', lambda args: source)
    prepare = Mock(return_value={'status': 'waiting_for_approval', 'reference': {'proposal_id': 'plan_offline'}, 'proposal': {'synthetic': True}})
    if outcome == 'failure': prepare.side_effect = WorkflowError('ANALYSIS_STALE')
    monkeypatch.setattr(execution_cli, 'prepare', prepare)
    monkeypatch.setattr(sys, 'argv', ['program_coordinator', '--event', str(event), '--metadata-dir', str(tmp_path / 'activity'),
        '--invocation-id', 'invoke_one', '--prepare-execution', '--preparation-id', 'prep'])
    # The original test service used deterministic_test; the CLI host must use the
    # same mode for its replay digest. No source or SDK handler is replaced.
    original = cli.WorkflowService
    monkeypatch.setattr(cli, 'WorkflowService', lambda *a, **kw: original(*a, **kw, execution_mode='deterministic_test'))
    assert cli.main() == (0 if outcome == 'pause' else 1)
    report = json.loads(capsys.readouterr().out)
    if outcome == 'pause': assert report['phase06']['status'] == 'waiting_for_approval'
    else: assert report['error_category'] == 'ANALYSIS_STALE'
    key.assert_not_called(); runner.assert_not_called(); prepare.assert_called_once()
    source.source.close.assert_called_once()
