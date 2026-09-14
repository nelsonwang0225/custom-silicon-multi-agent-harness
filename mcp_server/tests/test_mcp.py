import asyncio
import ast
import inspect
import json
from pathlib import Path
import re
import subprocess

import httpx
from jsonschema import Draft202012Validator
from mcp import Client
from pydantic import ValidationError
import pytest

from enterprise_api import ClientConfig, Scope
from enterprise_api.endpoints import ENDPOINTS
from enterprise_api.transport import HttpxReadTransport
from stratos_mcp.catalog import CATALOG
from stratos_mcp.config import ServerConfig
from stratos_mcp.server import create_server
from stratos_mcp.service import ToolService
from mcp_server.check_mcp import connect, run_integration
from mcp_server.testing import MCP_PYTHON, PROJECT, free_port, mcp_server, process_env

SCOPE = Scope(program_id="PRG-A17", customer_id="CUST-FML01")
EXPECTED = {
    "get_change_request", "get_requirement_revision", "get_configuration", "get_workload_profile",
    "get_procedure", "get_policy", "get_acceptance_criteria", "get_document", "get_documents", "get_plan", "get_decision",
    "get_validation_coverage", "get_validation_options", "get_validation_result", "get_validation_samples",
    "get_validation_jobs", "get_validation_job", "get_manufacturing_unit", "get_manufacturing_lot",
    "get_customer_order", "get_cost_rates", "get_program", "get_program_milestone", "get_dependencies",
    "get_implementation_links", "get_standard_change_context", "get_quality_context", "get_delivery_context",
}


def config(base_url="http://127.0.0.1:8000", **values):
    return ServerConfig(enterprise=ClientConfig(scope=SCOPE, base_url=base_url, **values))


@pytest.mark.anyio
async def test_discovery_and_schemas_match_existing_client_and_openapi():
    server = create_server(ToolService(config()))
    schema = json.loads((PROJECT / "docs/openapi.json").read_text())
    async with Client(server) as client:
        tools = (await client.list_tools()).tools
        assert {t.name for t in tools} == EXPECTED and len(tools) == 28
        for tool in tools:
            spec = CATALOG[tool.name]
            args = set(inspect.signature(spec.method).parameters) - {"self"}
            assert tool.input_schema["additionalProperties"] is False
            assert set(tool.input_schema["required"]) == set(tool.input_schema["properties"]) == args
            for value in tool.input_schema["properties"].values():
                assert value["type"] == "string" and value["maxLength"] == 100
                assert value["pattern"] == r"^[A-Za-z0-9_-]+$" and value["description"]
            Draft202012Validator.check_schema(tool.input_schema)
            Draft202012Validator.check_schema(tool.output_schema)
            method = spec.method.__name__ if tool.name != "get_dependencies" else "get_program_milestone"
            endpoint = ENDPOINTS[method]
            assert "get" in schema["paths"]["/api/v1" + endpoint.path]
            assert args == {p["name"] for p in schema["paths"]["/api/v1" + endpoint.path]["get"].get("parameters", [])}
            assert tool.annotations.read_only_hint and tool.annotations.idempotent_hint
            assert tool.annotations.destructive_hint is False and tool.annotations.open_world_hint is False
            assert "CR-017" not in tool.description and "recommended" not in tool.description


@pytest.mark.anyio
@pytest.mark.parametrize("arguments", [{}, {"change_id": "../secret"}, {"change_id": "https://evil.invalid"},
    {"change_id": "CR-017?role=engineer"}, {"change_id": "x" * 101}, {"change_id": ""}, {"change_id": 17},
    {"change_id": None}, {"change_id": True}, {"change_id": "CR-017", "identity": "private-canary"},
    {"change_id": "CR-017", "base_url": "private-canary"}])
async def test_invalid_input_never_reaches_transport_and_does_not_echo(arguments):
    def no_transport(*args, **kwargs):
        pytest.fail("Invalid input reached transport")
    async with Client(create_server(ToolService(config(), transport_factory=no_transport))) as client:
        result = await client.call_tool("get_change_request", arguments)
        assert result.is_error and result.structured_content["data"] is None
        assert result.structured_content["error"]["code"] == "INVALID_TOOL_INPUT"
        assert result.meta["stratos/trace"]["http_reads"] == []
        assert "private-canary" not in result.model_dump_json()


@pytest.mark.anyio
@pytest.mark.parametrize("name", ["query_system", "create_plan", "approve_plan", "schedule_validation_job",
                                       "link_program_plan", "close", "get", "__dict__", "private-canary"])
async def test_unregistered_tools_cannot_execute(name):
    async with Client(create_server(ToolService(config()))) as client:
        result = await client.call_tool(name, {})
        assert result.is_error and result.structured_content["error"]["code"] == "UNKNOWN_TOOL"
        assert result.meta["stratos/trace"]["http_reads"] == []
        assert "private-canary" not in result.model_dump_json()


@pytest.mark.parametrize("values", [{"host": "0.0.0.0"}, {"host": "::"}, {"host": "example.com"},
    {"port": 0}, {"port": 65536}, {"port": "9000"}])
def test_only_loopback_listener_configuration(values):
    with pytest.raises(ValidationError):
        ServerConfig(enterprise=config().enterprise, **values)


@pytest.mark.parametrize("identity", ["demo-engineer-local-only", "demo-automation-local-only",
                                      "demo-portfolio-engineer-local-only", "private-canary"])
def test_only_existing_readers_can_be_configured(identity):
    with pytest.raises(ValidationError):
        config(reader_identity=identity)


@pytest.mark.anyio
async def test_missing_and_inaccessible_records_remain_indistinguishable(live_backend):
    async with Client(create_server(ToolService(config(live_backend)))) as client:
        errors = []
        for change_id in ("MISSING", "CR-105"):
            result = await client.call_tool("get_change_request", {"change_id": change_id})
            assert result.is_error and result.structured_content["data"] is None
            error = result.structured_content["error"]
            errors.append((error["kind"], error["http_status"], error["code"]))
        assert errors == [("not_found", 404, "NOT_FOUND")] * 2


@pytest.mark.anyio
async def test_scope_cannot_be_widened_in_parameters_or_metadata(live_backend):
    async with Client(create_server(ToolService(config(live_backend, reader_identity="demo-portfolio-reader-local-only")))) as client:
        for name in ("get_validation_coverage", "get_validation_options", "get_validation_jobs"):
            result = await client.call_tool(name, {"change_id": "CR-105"},
                                             meta={"program_id": "PRG-P01", "customer_id": "CUST-NORTH"})
            assert result.is_error and result.structured_content["error"]["kind"] == "scope"
            assert not any(r["path"].endswith(("/coverage", "/options", "/jobs")) for r in result.meta["stratos/trace"]["http_reads"])
        result = await client.call_tool("get_program", {"program_id": "PRG-P01"})
        assert result.is_error and result.meta["stratos/trace"]["http_reads"] == []


@pytest.mark.anyio
async def test_wrong_customer_pairing_is_rejected(live_backend):
    cfg = ServerConfig(enterprise=ClientConfig(base_url=live_backend,
        scope=Scope(program_id="PRG-P01", customer_id="CUST-FML01"), reader_identity="demo-portfolio-reader-local-only"))
    async with Client(create_server(ToolService(cfg))) as client:
        result = await client.call_tool("get_configuration", {"configuration_id": "CFG-P01-TARGET"})
        assert result.is_error and result.structured_content["error"]["kind"] == "scope"


@pytest.fixture
def mocked_service():
    clients = []
    def make(handler):
        def factory(cfg, **kwargs):
            http = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
            clients.append(http)
            return HttpxReadTransport(cfg, http_client=http, **kwargs)
        return ToolService(config(retry_backoff=0), transport_factory=factory)
    yield make
    for client in clients:
        client.close()


@pytest.mark.anyio
@pytest.mark.parametrize("status,kind,attempts", [(401,"unauthenticated",1),(403,"forbidden",1),
    (404,"not_found",1),(409,"conflict",1),(422,"validation",1),(500,"server",1),
    (502,"server",3),(503,"server",3),(504,"server",3),(429,"http",1)])
async def test_safe_http_errors_and_bounded_retries(mocked_service, status, kind, attempts, caplog):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": {"code": "private-canary", "message": "Bearer private-canary",
                                                     "details": {"path": "/private/internal.sqlite3"}}},
                              headers={"X-Request-ID": "private-canary", "X-Correlation-ID": "private-canary"})
    async with Client(create_server(mocked_service(handler))) as client:
        result = await client.call_tool("get_program", {"program_id": SCOPE.program_id})
        assert result.is_error and result.structured_content["error"]["kind"] == kind
        assert result.structured_content["error"]["http_status"] == status
        assert result.structured_content["error"]["attempts"] == len(requests) == attempts
        assert len({r.headers["X-Correlation-ID"] for r in requests}) == 1
        assert all(r.method == "GET" and r.headers["Authorization"] == "Bearer demo-reader-local-only" for r in requests)
        output = result.model_dump_json() + caplog.text
        assert "private-canary" not in output and "internal.sqlite3" not in output


@pytest.mark.anyio
@pytest.mark.parametrize("exception,kind", [(httpx.ConnectError,"connection"), (httpx.ReadTimeout,"timeout"),
                                             (RuntimeError,"server")])
async def test_transport_and_unexpected_exceptions_are_safe(mocked_service, exception, kind, caplog):
    def handler(request):
        raise exception("private-canary internal credentials")
    async with Client(create_server(mocked_service(handler))) as client:
        result = await client.call_tool("get_program", {"program_id": SCOPE.program_id})
        assert result.is_error and result.structured_content["error"]["kind"] == kind
        assert "private-canary" not in result.model_dump_json() + caplog.text


@pytest.mark.anyio
async def test_malformed_success_is_safe(mocked_service):
    service = mocked_service(lambda request: httpx.Response(200, json={"body": "private-canary"}))
    async with Client(create_server(service)) as client:
        result = await client.call_tool("get_program", {"program_id": SCOPE.program_id})
        assert result.is_error and result.structured_content["error"]["kind"] == "invalid_response"
        assert "private-canary" not in result.model_dump_json()


@pytest.mark.anyio
async def test_concurrent_calls_have_independent_correlations(live_backend):
    async with Client(create_server(ToolService(config(live_backend)))) as client:
        results = await asyncio.gather(*(client.call_tool("get_validation_coverage", {"change_id": "CR-017"}) for _ in range(4)))
        assert all(r.structured_content == results[0].structured_content for r in results)
        traces = [r.meta["stratos/trace"] for r in results]
        assert len({t["correlation_id"] for t in traces}) == 4
        for trace in traces:
            assert re.fullmatch(r"mcp-[a-f0-9]{32}", trace["call_id"])
            assert len(trace["http_reads"]) == 3
            assert all(r["correlation_id"] == r["server_correlation_id"] == trace["correlation_id"] for r in trace["http_reads"])


def test_real_streamable_http_end_to_end_and_persisted_state(tmp_path):
    report = run_integration(tmp_path)
    assert all(report["checks"].values())
    assert set(report["tools"]) == EXPECTED


@pytest.mark.anyio
async def test_http_startup_health_auth_headers_origin_and_shutdown(tmp_path, live_backend):
    with mcp_server(tmp_path, live_backend) as (url, process):
        with httpx.Client(trust_env=False, timeout=5) as http:
            assert http.get(url + "/health").json()["status"] == "alive"
            assert http.get(url + "/ready").status_code == 200
            assert http.get(url + "/health", headers={"Host": "evil.invalid"}).status_code == 421
            assert http.post(url + "/mcp", json={}, headers={"Origin": "https://evil.invalid"}).status_code == 403
            assert http.post(url + "/mcp", content=b"x" * 16385, headers={"Content-Type":"application/json"}).status_code == 413
            assert http.get(url + "/sse").status_code == 404
            envelope = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                        "io.modelcontextprotocol/clientCapabilities": {}}
            for params in ({"name": "get_program", "arguments": "private-canary"},
                           {"name": {"private-canary": 1}, "arguments": {}}):
                response = http.post(url + "/mcp", headers={"Accept": "application/json, text/event-stream",
                                     "MCP-Protocol-Version": "2026-07-28"},
                                     json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {**params, "_meta": envelope}})
                assert "error" in response.json()
                assert "private-canary" not in response.text
        # Supplying a stronger identity on the MCP connection cannot change the
        # configured reader. A legacy handshake is also checked over real HTTP.
        async with connect(url + "/mcp", headers={"Authorization":"Bearer demo-portfolio-engineer-local-only"}, mode="legacy") as client:
            result = await client.call_tool("get_change_request", {"change_id":"CR-105"})
            assert result.is_error and result.structured_content["error"]["http_status"] == 404
    assert process.returncode == 0
    assert all("private-canary" not in path.read_text() for path in tmp_path.glob("mcp-*.log"))


@pytest.mark.anyio
async def test_backend_unavailable_readiness_and_tool_error(tmp_path):
    with mcp_server(tmp_path, f"http://127.0.0.1:{free_port()}") as (url, process):
        with httpx.Client(trust_env=False, timeout=5) as http:
            assert http.get(url + "/health").status_code == 200
            assert http.get(url + "/ready").status_code == 503
        async with connect(url + "/mcp") as client:
            assert len((await client.list_tools()).tools) == 28
            result = await client.call_tool("get_program", {"program_id":"PRG-A17"})
            assert result.is_error and result.structured_content["error"]["kind"] == "connection"
            assert result.structured_content["error"]["attempts"] == 3
    assert process.returncode == 0


@pytest.mark.parametrize("arguments", [["--backend-url", "http://user:private-canary@127.0.0.1:8000"],
                                       ["--port", "private-canary"], ["--unknown", "private-canary"]])
def test_invalid_cli_config_does_not_echo_supplied_secrets(arguments):
    result = subprocess.run([str(MCP_PYTHON), "-m", "stratos_mcp", *arguments], env=process_env(),
                            cwd=PROJECT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "private-canary" not in result.stdout + result.stderr


def test_runtime_has_no_backend_storage_or_model_imports():
    forbidden = {"mock_enterprise", "sqlite3", "openai", "agents", "dotenv", "subprocess"}
    for path in (PROJECT / "src/stratos_mcp").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {x.name.split(".")[0] for x in node.names} & forbidden
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec"}
