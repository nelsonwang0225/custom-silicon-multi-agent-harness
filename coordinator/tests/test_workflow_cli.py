"""Exercise the existing CLI, with the existing SDK harness replaced by its offline test double."""
import contextlib
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

from program_coordinator import __main__ as cli
from test_orchestration import wired


@pytest.mark.parametrize("arguments,status", [
    (["--list-workflows"], 0),
    (["--workflow-id", "yield_exception_recovery", "--phase06", "resume"], 2),
    (["--workflow-id", "delivery_readiness", "--phase06", "resume"], 2),
    (["--workflow-id", "unknown"], 2),
])
def test_offline_catalog_and_unsupported_cli_never_load_key_or_start_agent(monkeypatch, capsys, tmp_path, arguments, status):
    key = Mock(side_effect=AssertionError("No credential access permitted"))
    execute = Mock(side_effect=AssertionError("No runner permitted"))
    monkeypatch.setattr(cli, "PROJECT", tmp_path)
    monkeypatch.setattr(cli, "load_key", key)
    monkeypatch.setattr(cli, "execute", execute)
    monkeypatch.setattr(sys, "argv", ["program_coordinator", *arguments])
    assert cli.main() == status
    result = json.loads(capsys.readouterr().out)
    assert len(result) == 3 if status == 0 else result["status"] == "unsupported"
    key.assert_not_called(); execute.assert_not_called()


def test_existing_event_cli_dispatches_via_service_and_replay_does_not_load_key(monkeypatch, capsys, tmp_path):
    calls = []
    def offline_harness(config, event, model, recorder, **kwargs):
        h, _ = wired()
        h.state.case_id = kwargs["case_id"]
        h.state.run_id = kwargs["run_id"]
        h.state.workflow_id = kwargs["workflow_id"]
        h.state.workflow_definition_version = kwargs["workflow_definition_version"]
        h.checkpoint_callback = kwargs["checkpoint"]
        calls.append(h)
        return h
    monkeypatch.setattr(cli, "PROJECT", tmp_path)
    monkeypatch.setattr(cli, "CaseHarness", offline_harness)
    key = Mock(return_value="offline-test-placeholder")
    monkeypatch.setattr(cli, "load_key", key)
    monkeypatch.setattr(cli, "set_trace_processors", lambda *a: None)
    monkeypatch.setattr(cli, "set_tracing_disabled", lambda *a: None)
    monkeypatch.setattr(cli, "trace", lambda *a, **kw: contextlib.nullcontext())
    monkeypatch.setattr(cli, "flush_traces", lambda: None)
    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(sys, "argv", ["program_coordinator", "--event", str(root / "coordinator/scenarios/human_review.json"),
        "--metadata-dir", str(tmp_path / "metadata"), "--invocation-id", "cli_retry"])
    assert cli.main() == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "completed" and len(calls) == 1
    state = json.loads((Path(first["artifact_directory"]) / "case-state.json").read_text())
    assert state["run_id"] and state["workflow_id"] == "requirement_change_analysis"
    assert cli.main() == 0
    second = json.loads(capsys.readouterr().out)
    assert second["status"] == "replayed" and len(calls) == 1 and key.call_count == 1
    report = json.loads((Path(second["artifact_directory"]) / "report.json").read_text())
    assert report["original_artifact_directory"] == first["artifact_directory"]
    assert report["run_id"] == state["run_id"]
    from coordinator.evals.build_report import is_case_attempt
    assert is_case_attempt(Path(first["artifact_directory"]) / "report.json", first)
    assert not is_case_attempt(Path(second["artifact_directory"]) / "report.json", report)
