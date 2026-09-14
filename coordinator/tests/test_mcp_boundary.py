import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from agents.mcp import MCPServerStreamableHttp
from mcp.types import CallToolResult, Tool, ToolAnnotations

from program_coordinator.mcp import ScopedMCP
from program_coordinator.controls import HarnessConfig, HarnessError, TOOL_MATRIX
from helpers import harness, seed_sources


def mcp(role="change_impact", **kwargs):
    h = harness(**kwargs)
    return ScopedMCP(h, role, "work_test")


@pytest.mark.parametrize("role", TOOL_MATRIX)
def test_catalog_filters_unknown_and_write_tools(role):
    server = mcp(role)
    server.session = SimpleNamespace()
    server._cache_dirty = False
    server._tools_list = [Tool(name=n, input_schema={"type": "object"},
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False))
        for n in TOOL_MATRIX[role]] + [Tool(name="create_plan", input_schema={"type": "object"})]
    result = asyncio.run(server.list_tools())
    assert {t.name for t in result} == TOOL_MATRIX[role]
    server._tools_list[0].annotations.read_only_hint = False
    with pytest.raises(HarnessError, match="unsafe_mcp_capability"):
        asyncio.run(server.list_tools())


def test_missing_tool_catalog_fails_closed():
    server = mcp()
    server.session = SimpleNamespace(); server._cache_dirty = False
    server._tools_list = [Tool(name="get_change_request", input_schema={"type": "object"})]
    with pytest.raises(HarnessError, match="mcp_catalog_mismatch"):
        asyncio.run(server.list_tools())


@pytest.mark.parametrize("tool,args,error", [
    ("create_plan", {"change_id": "CR-017"}, "tool_not_allowed"),
    ("get_manufacturing_lot", {"lot_id": "LOT-4492"}, "tool_not_allowed"),
    ("get_change_request", {"change_id": "CR-OTHER"}, "undiscovered_record_id"),
    ("get_change_request", {"change_id": "../secret"}, "invalid_tool_arguments"),
    ("get_change_request", {"change_id": {"id": "CR-017"}}, "invalid_tool_arguments"),
])
def test_capability_and_id_denials_happen_before_transport(monkeypatch, tool, args, error):
    call = AsyncMock()
    monkeypatch.setattr(MCPServerStreamableHttp, "call_tool", call)
    with pytest.raises(HarnessError, match=error):
        asyncio.run(mcp().call_tool(tool, args))
    call.assert_not_called()


def receipt():
    return {"stratos/trace": {"call_id": "mcp-" + "a"*32, "correlation_id": "corr-" + "b"*32,
        "http_reads": [{"method": "GET", "path": "/api/v1/engineering/changes/CR-017", "status": 200,
        "attempts": 1, "request_id": "request-" + "c"*32, "correlation_id": "corr-" + "b"*32,
        "server_correlation_id": "corr-" + "b"*32, "latency_ms": 1.0}]}}


@pytest.mark.parametrize("kind", ["valid", "scope", "record", "envelope", "write_receipt", "error", "version"])
def test_response_validation_precedes_model_context(monkeypatch, kind):
    h = seed_sources(harness())
    server = ScopedMCP(h, "change_impact", "work_test")
    data = deepcopy(h.sources.latest("get_change_request")["data"])
    meta = receipt()
    if kind == "scope": data["program_id"] = "PRG-OTHER"
    if kind == "record": data["id"] = "CR-OTHER"
    if kind == "version": data["content_version"] += 1
    if kind == "write_receipt": meta["stratos/trace"]["http_reads"][0]["method"] = "POST"
    payload = {"ok": True, "data": data, "error": None}
    if kind == "envelope": payload.pop("ok")
    if kind == "error": payload = {"ok": False, "data": None, "error": {"code": "NOT_FOUND"}}
    result = CallToolResult(content=[], structured_content=payload, is_error=kind=="error", meta=meta)
    monkeypatch.setattr(MCPServerStreamableHttp, "call_tool", AsyncMock(return_value=result))
    original_count = len(h.sources.calls)
    if kind != "valid":
        with pytest.raises(HarnessError): asyncio.run(server.call_tool("get_change_request", {"change_id": "CR-017"}))
        assert len(h.sources.calls) == original_count
    else:
        result = asyncio.run(server.call_tool("get_change_request", {"change_id": "CR-017"}))
        assert result.structured_content["data"]["_receipt"]["source_id"] in server.seen_sources
        assert h.sources.calls[-1]["data"] == data and "_receipt" not in data


def test_tool_timeout_and_budget(monkeypatch):
    async def wait(*args, **kwargs): await asyncio.sleep(1)
    monkeypatch.setattr(MCPServerStreamableHttp, "call_tool", wait)
    s = mcp(config=HarnessConfig(tool_timeout_seconds=0.001, max_tool_calls=1))
    with pytest.raises(HarnessError, match="tool_timeout"):
        asyncio.run(s.call_tool("get_change_request", {"change_id": "CR-017"}))
    with pytest.raises(HarnessError, match="max_tool_calls"):
        asyncio.run(s.call_tool("get_change_request", {"change_id": "CR-017"}))


def test_wrong_record_type_is_rejected_locally_as_structured_feedback(monkeypatch):
    h = seed_sources(harness())
    server = ScopedMCP(h, "change_impact", "work_test")
    transport = AsyncMock()
    monkeypatch.setattr(MCPServerStreamableHttp, "call_tool", transport)
    result = asyncio.run(server.call_tool("get_document", {"document_id": "CRIT-BASE-V1"}))
    assert result.is_error and result.structured_content["error"]["code"] == "TYPED_RECORD_REFERENCE_DENIED"
    assert "DOC-REQUEST-01" in result.structured_content["error"]["known_ids_for_parameter"]["document_id"]
    assert h.state.guardrail_events == ["typed_record_reference_denied"]
    transport.assert_not_called()


def test_agent_runtime_has_no_business_bypass():
    import ast
    from pathlib import Path
    package = Path(__file__).resolve().parents[2] / "src/program_coordinator"
    forbidden = {"enterprise_api", "stratos_mcp", "mock_enterprise", "sqlite3", "subprocess", "coordinator"}
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
            assert not any(n and n.split(".")[0] in forbidden and n not in {"enterprise_api.standard_models", "enterprise_api.standard_policy", "enterprise_api.quality_models", "enterprise_api.quality_policy", "enterprise_api.delivery_models", "enterprise_api.delivery_policy"} for n in names)
