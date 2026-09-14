"""Offline checks: no credentials or paid requests. Business examples are invented test data."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from agents import AgentOutputSchema
from agents.mcp import MCPServerStreamableHttp
from mcp.types import CallToolResult, Tool, ToolAnnotations
from pydantic import ValidationError

from program_investigator.agent import build_agent, run_investigation, task_input
from program_investigator.config import MODEL, InvestigatorConfig, InvestigatorError, load_key
from program_investigator.instructions import INSTRUCTIONS
from program_investigator.mcp import READ_TOOLS, StratosMCP, trace_receipt, validate_payload
from program_investigator.models import InvestigationResult
from program_investigator.telemetry import Recorder, SafeMetadataProcessor
from program_investigator.validation import validate_sources


def server():
    return StratosMCP(InvestigatorConfig(), Recorder("trace_" + "0" * 32), "CASE-TEST")


def assessment():
    finding = {"statement": "Needs review based on available records", "basis": "fact", "source_refs": ["s1"]}
    return {
        "case_id": "CASE-TEST", "customer": {"id": "C-TEST", "name": "Test Customer", "source_refs": ["s1"]},
        "program": {"id": "P-TEST", "name": "Test Program", "source_refs": ["s1"]},
        "change_summary": finding, "affected_scope": [], "confirmed_facts": [finding],
        "validation_coverage_status": {"status": "insufficient", "coverage_satisfied": False,
                                       "explanation": "No evidence returned", "source_refs": ["s1"]},
        "evidence_gaps": [], "relevant_evidence": [], "manufacturing_constraints": [],
        "customer_commitment": None, "program_milestone": None,
        "eligible_options": [], "ineligible_options": [], "risks": [], "unresolved_questions": [],
        "recommended_next_step": dict(finding, basis="recommendation"), "requires_human_review": True,
        "source_references": [{"ref_id": "s1", "tool_name": "get_validation_coverage",
                               "inputs": [{"name": "change_id", "value": "CASE-TEST"}],
                               "record_id": "CASE-TEST", "content_version": None, "record_version": None}],
    }


def calls():
    return [{"tool": "get_validation_coverage", "arguments": {"change_id": "CASE-TEST"},
             "data": {"change_id": "CASE-TEST", "coverage_satisfied": False, "items": []}},
            {"tool": "get_validation_options", "arguments": {"change_id": "CASE-TEST"},
             "data": {"change_id": "CASE-TEST", "items": []}}]


def test_configuration_and_mcp_attachment():
    mcp = server()
    agent = build_agent(mcp)
    assert isinstance(mcp, MCPServerStreamableHttp)
    assert agent.name == "ProgramInvestigator" and agent.model == MODEL == "gpt-6-astra"
    assert agent.mcp_servers == [mcp] and not agent.tools and not agent.handoffs
    assert agent.output_type is InvestigationResult
    assert agent.model_settings.store is False
    assert mcp.use_structured_content and mcp.max_retry_attempts == 0


@pytest.mark.parametrize("url", ["https://example.com/mcp", "http://user:pass@127.0.0.1/mcp",
                                 "http://127.0.0.1/mcp?key=x", "http://127.0.0.1/api/v1",
                                 "http://127.0.0.1/mcp#fragment", "http://127.0.0.1:99999/mcp"])
def test_config_rejects_untrusted_endpoints(url):
    with pytest.raises(ValidationError):
        InvestigatorConfig(mcp_url=url)


def test_schema_strict_and_no_golden_prompt():
    schema = AgentOutputSchema(InvestigationResult).json_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert all(v.get("additionalProperties") is False for v in schema["$defs"].values() if v["type"] == "object")
    for text in (INSTRUCTIONS, json.dumps(schema)):
        assert all(x not in text for x in ("CR-017", "Helios", "PRG-A17", "REQ-042", "SLOT-"))
    assert "CASE-TEST" in task_input("CASE-TEST", "Test Customer")


def test_runtime_has_no_business_bypass():
    package = Path(__file__).resolve().parents[2] / "src/program_investigator"
    import ast
    forbidden = {"enterprise_api", "stratos_mcp", "sqlite3", "subprocess", "stratos", "investigator.evals"}
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name.split(".")[0] in forbidden for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not node.module or node.module.split(".")[0] not in forbidden


def tool(name, readonly=True):
    return Tool(name=name, description="Test read", input_schema={"type": "object"},
                annotations=ToolAnnotations(read_only_hint=readonly, destructive_hint=not readonly,
                                            idempotent_hint=True, open_world_hint=False))


def test_catalog_allowlist_and_readonly_hints(monkeypatch):
    # Exercise the SDK's real static filter, then this package's hint validation.
    mcp = server()
    mcp.session = SimpleNamespace()
    mcp._cache_dirty = False
    mcp._tools_list = [tool(name) for name in READ_TOOLS] + [tool("create_plan", False)]
    listed = asyncio.run(mcp.list_tools())
    assert {t.name for t in listed} == READ_TOOLS and len(listed) == 25
    mcp._tools_list[0].annotations.read_only_hint = False
    with pytest.raises(InvestigatorError, match="unsafe_mcp_capability"):
        asyncio.run(mcp.list_tools())


def test_direct_write_call_rejected_before_sdk(monkeypatch):
    call = AsyncMock()
    monkeypatch.setattr(MCPServerStreamableHttp, "call_tool", call)
    with pytest.raises(InvestigatorError, match="tool_not_allowed"):
        asyncio.run(server().call_tool("create_plan", {"change_id": "CASE-TEST"}))
    call.assert_not_called()


def test_mcp_unavailable_never_reaches_runner(monkeypatch):
    from program_investigator import agent
    async def unavailable(self):
        raise RuntimeError("sensitive transport details")
    monkeypatch.setattr(MCPServerStreamableHttp, "connect", unavailable)
    run = AsyncMock()
    monkeypatch.setattr(agent.Runner, "run", run)
    with pytest.raises(InvestigatorError, match="^mcp_unavailable$"):
        asyncio.run(run_investigation(InvestigatorConfig(), "CASE-TEST", "Test Customer", "unused", Recorder("test")))
    run.assert_not_called()


@pytest.mark.parametrize("payload,is_error", [
    (None, False), ({"ok": True}, False), ({"ok": "true", "data": {}, "error": None}, False),
    ({"ok": True, "data": [], "error": None}, False),
    ({"ok": True, "data": {}, "error": None}, True),
    ({"ok": True, "data": {}, "error": {"message": "unexpected"}}, False),
    ({"ok": True, "data": {}, "error": None, "extra": 1}, False),
])
def test_malformed_tool_results(payload, is_error):
    with pytest.raises(InvestigatorError, match="malformed_mcp_result"):
        validate_payload(SimpleNamespace(structured_content=payload, is_error=is_error))


def test_source_error_stops_assessment():
    with pytest.raises(InvestigatorError, match="^mcp_source_error$"):
        validate_payload(SimpleNamespace(structured_content={"ok": False, "data": None,
                        "error": {"code": "sensitive"}}, is_error=True))


def test_missing_or_write_receipt_rejected():
    with pytest.raises(InvestigatorError, match="invalid_mcp_receipt"):
        trace_receipt(SimpleNamespace(meta={}))


def test_tool_transport_failure_is_safe(monkeypatch):
    monkeypatch.setattr(MCPServerStreamableHttp, "call_tool", AsyncMock(side_effect=RuntimeError("private details")))
    with pytest.raises(InvestigatorError, match="^mcp_call_failed$"):
        asyncio.run(server().call_tool("get_change_request", {"change_id": "CASE-TEST"}))


def test_altered_option_money_and_missing_options_rejected():
    value = assessment()
    option = dict(slot_id="SLOT-TEST", sample_id="SAMPLE-TEST", unit_id="UNIT-TEST", lot_id="LOT-TEST",
                  configuration_id="CFG-TEST", procedure_id="PROC-TEST", policy_id="POLICY-TEST",
                  milestone_id="MS-TEST", rate_id="RATE-TEST", cost_cents=12000, currency="USD",
                  resource_eligible=True, approval_eligible=True, meets_deadline=True,
                  eligibility_reasons=[], approval_reasons=[], timing=None, source_refs=["s1"])
    value["eligible_options"] = [option]
    source = calls()
    raw = {k: v for k, v in option.items() if k not in {"slot_id", "sample_id", "rate_id", "source_refs"}}
    raw.update(slot={"id": "SLOT-TEST"}, sample={"id": "SAMPLE-TEST"}, rate={"id": "RATE-TEST"})
    source[1]["data"]["items"] = [raw]
    validate_sources(InvestigationResult.model_validate(value), source, "CASE-TEST")
    option["cost_cents"] = 12001
    with pytest.raises(InvestigatorError, match="output_options_mismatch"):
        validate_sources(InvestigationResult.model_validate(value), source, "CASE-TEST")
    value["eligible_options"] = []
    with pytest.raises(InvestigatorError, match="output_options_mismatch"):
        validate_sources(InvestigationResult.model_validate(value), source, "CASE-TEST")


def test_valid_output_and_source_checks():
    result = InvestigationResult.model_validate(assessment())
    validate_sources(result, calls(), "CASE-TEST")
    assert InvestigationResult.model_validate_json(result.model_dump_json()) == result


def test_namespace_and_projection_citations():
    value = assessment()
    value["source_references"][0]["tool_name"] = "functions.get_validation_coverage"
    result = InvestigationResult.model_validate(value)
    assert result.source_references[0].tool_name == "get_validation_coverage"
    validate_sources(result, calls(), "CASE-TEST")
    source = calls() + [{"tool": "get_dependencies", "arguments": {"program_id": "P-TEST", "milestone_id": "MS-TEST"},
                        "data": {"milestone_id": "MS-TEST", "program_id": "P-TEST", "record_version": 2,
                                 "dependencies": []}}]
    value["source_references"].append({"ref_id": "s2", "tool_name": "functions.get_dependencies",
        "inputs": [{"name": "program_id", "value": "P-TEST"}, {"name": "milestone_id", "value": "MS-TEST"}],
        "record_id": "MS-TEST", "content_version": None, "record_version": 2})
    validate_sources(InvestigationResult.model_validate(value), source, "CASE-TEST")
    value["source_references"][-1]["record_version"] = 3
    with pytest.raises(InvestigatorError, match="output_source_version_mismatch"):
        validate_sources(InvestigationResult.model_validate(value), source, "CASE-TEST")


@pytest.mark.parametrize("mutation", ["no_review", "bad_ref", "fact_as_inference", "coverage_conflict", "extra"])
def test_invalid_output_rejected(mutation):
    value = deepcopy(assessment())
    if mutation == "no_review": value["requires_human_review"] = False
    if mutation == "bad_ref": value["customer"]["source_refs"] = ["invented"]
    if mutation == "fact_as_inference": value["confirmed_facts"][0]["basis"] = "inference"
    if mutation == "coverage_conflict": value["validation_coverage_status"]["status"] = "sufficient"
    if mutation == "extra": value["approved"] = True
    with pytest.raises(ValidationError):
        InvestigationResult.model_validate(value)


@pytest.mark.parametrize("mutation", ["fake_tool", "fake_args", "fake_record", "fake_version", "fake_coverage"])
def test_invented_source_facts_rejected(mutation):
    value = deepcopy(assessment())
    ref = value["source_references"][0]
    if mutation == "fake_tool": ref["tool_name"] = "get_document"
    if mutation == "fake_args": ref["inputs"][0]["value"] = "ANOTHER-CASE"
    if mutation == "fake_record": ref["record_id"] = "INVENTED"
    if mutation == "fake_version": ref["content_version"] = 99
    source = calls()
    if mutation == "fake_coverage": source[0]["data"]["coverage_satisfied"] = True
    with pytest.raises(InvestigatorError):
        validate_sources(InvestigationResult.model_validate(value), source, "CASE-TEST")


def test_trace_payloads_and_errors_redacted():
    recorder = Recorder("test")
    span = SimpleNamespace(span_data=SimpleNamespace(type="function", input="private", output="private"),
                           error={"message": "private"}, trace_id="test", span_id="span", parent_id=None,
                           started_at=None, ended_at=None)
    span.set_error = lambda value: setattr(span, "error", value)
    SafeMetadataProcessor(recorder).on_span_end(span)
    assert span.span_data.input is None and span.span_data.output is None
    assert span.error == {"message": "investigator_operation_failed", "data": {}}
    assert "private" not in json.dumps(recorder.spans)


def test_secure_file_loader(tmp_path):
    path = tmp_path / ".env.local"
    key = "sk-" + "synthetic" * 5
    path.write_text("OPENAI_API_KEY=" + key)
    path.chmod(0o600)
    assert load_key(path) == key
    path.chmod(0o644)
    with pytest.raises(InvestigatorError, match="unsafe_env_file"):
        load_key(path)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(InvestigatorError, match="env_file_unavailable"):
        load_key(link)


def test_offline_revalidation_preserves_assessment_and_original_run(tmp_path):
    from program_investigator.revalidate import revalidate
    value = assessment()
    value["source_references"][0]["tool_name"] = "functions.get_validation_coverage"
    original = {"trace_id": "trace_test", "status": "failed", "error_category": "output_source_mismatch"}
    (tmp_path / "report.json").write_text(json.dumps(original))
    (tmp_path / "rejected-result.json").write_text(json.dumps(value))
    (tmp_path / "tool-calls.json").write_text(json.dumps(calls()))
    receipt = revalidate(tmp_path)
    assert receipt["model_calls"] == 0 and receipt["business_assessment_unchanged"]
    result = json.loads((tmp_path / "result.json").read_text())
    assert result == assessment()
    assert json.loads((tmp_path / "report.json").read_text()) == original
    assert json.loads((tmp_path / "rejected-result.json").read_text()) == value
    with pytest.raises(FileExistsError):
        revalidate(tmp_path)


def test_completed_runner_output_passes_final_pipeline(monkeypatch):
    from program_investigator import agent
    from agents.usage import Usage
    recorder = Recorder("trace_" + "1" * 32)
    recorder.calls = calls()
    monkeypatch.setattr(StratosMCP, "connect", AsyncMock())
    monkeypatch.setattr(StratosMCP, "cleanup", AsyncMock())
    monkeypatch.setattr(StratosMCP, "list_tools", AsyncMock(return_value=[]))
    completed = SimpleNamespace(final_output=InvestigationResult.model_validate(assessment()),
                                context_wrapper=SimpleNamespace(usage=Usage()))
    run = AsyncMock(return_value=completed)
    monkeypatch.setattr(agent.Runner, "run", run)
    output, usage = asyncio.run(run_investigation(InvestigatorConfig(), "CASE-TEST", "Test Customer", "fake", recorder))
    assert output == completed.final_output and usage["requests"] == 0
    config = run.call_args.kwargs["run_config"]
    assert config.tracing_disabled is False and config.trace_include_sensitive_data is False
    assert recorder.candidate_output == assessment()
