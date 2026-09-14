"""Client tests cross HTTP only; backend imports below are test-server bootstrap only."""

import ast
import inspect
import json
from pathlib import Path

from fastapi.testclient import TestClient
import httpx
import pytest
from pydantic import ValidationError

from enterprise_api import ClientConfig, EnterpriseAPIError, EnterpriseClient, Scope
from enterprise_api.endpoints import ENDPOINTS
from enterprise_api.transport import HttpxReadTransport
from mock_enterprise.app import create_app
from mock_enterprise.config import Settings
from mock_enterprise.seed import initialize
from scripts.check_enterprise_client import RecordingReads, collect_context, summarize

PROJECT = Path(__file__).resolve().parents[1]
LEGACY = Scope(program_id="PRG-A17", customer_id="CUST-FML01")
PORTFOLIO = Scope(program_id="PRG-P01", customer_id="CUST-NORTH")


@pytest.fixture
def backend(tmp_path):
    settings = Settings(tmp_path / "enterprise.sqlite3", tmp_path, True)
    initialize(settings)
    with TestClient(create_app(settings)) as server:
        yield server


def client_for(server, scope=LEGACY, *, portfolio=False):
    config = ClientConfig(scope=scope, reader_identity="demo-portfolio-reader-local-only" if portfolio else "demo-reader-local-only")
    transport = RecordingReads(HttpxReadTransport(config, http_client=server))
    return EnterpriseClient(config, transport=transport), transport


def raw(server, path, *, portfolio=False, params=None):
    identity = "demo-portfolio-reader-local-only" if portfolio else "demo-reader-local-only"
    response = server.get("/api/v1" + path, params=params, headers={"Authorization": "Bearer " + identity})
    assert response.status_code == 200
    return response.json()


def test_readonly_context_preserves_authoritative_records_and_all_options(backend):
    before = raw(backend, "/portfolio", portfolio=True)
    client, recorder = client_for(backend)
    context = collect_context(client, "CR-017")
    assert set(context) == {"engineering", "validation", "manufacturing", "erp", "planner"}
    assert context["engineering"]["change"] == raw(backend, "/engineering/changes/CR-017")
    assert context["validation"]["coverage"] == raw(backend, "/validation/coverage", params={"change_id": "CR-017"})
    assert context["validation"]["options"] == raw(backend, "/validation/options", params={"change_id": "CR-017"})
    for result_id, result in context["validation"]["results"].items():
        assert result == raw(backend, "/validation/results/" + result_id)
    for pair in context["manufacturing"]["provenance"].values():
        assert pair["unit"] == raw(backend, "/manufacturing/units/" + pair["unit"]["id"])
        assert pair["lot"] == raw(backend, "/manufacturing/lots/" + pair["lot"]["id"])
    assert raw(backend, "/portfolio", portfolio=True) == before
    assert all(r["method"] == "GET" and r["status"] == 200 for r in recorder.receipts)
    summary = summarize(context, recorder.receipts)
    assert summary["counts"]["validation_options"] == len(context["validation"]["options"]["items"])
    assert json.loads(json.dumps(context)) == context


def test_every_public_read_maps_to_actual_get_and_preserves_response(backend):
    client, _ = client_for(backend, PORTFOLIO, portfolio=True)
    portfolio = raw(backend, "/portfolio", portfolio=True)
    case = next(c for c in portfolio["cases"] if c["change"]["program_id"] == PORTFOLIO.program_id and c["jobs"] and c["links"])
    change = case["change"]
    job = case["jobs"][0]
    plan = next(p for p in change["plans"] if p["id"] == job["plan_id"])
    sample = next(s for s in portfolio["samples"] if s["program_id"] == PORTFOLIO.program_id)
    unit = raw(backend, "/manufacturing/units/" + sample["unit_id"], portfolio=True)
    history = next(h for h in portfolio["history"] if h["program_id"] == PORTFOLIO.program_id)
    values = {
        "program_id": PORTFOLIO.program_id, "change_id": change["id"],
        "requirement_revision_id": change["proposed_requirement_revision_id"],
        "configuration_id": change["configuration_id"], "workload_profile_id": case["target"]["workload_profile_id"],
        "procedure_id": case["procedures"][0]["id"], "policy_id": case["policies"][0]["id"],
        "criteria_id": case["criteria"]["id"], "document_id": change["request_document_id"],
        "plan_id": plan["id"], "decision_id": plan["decision_id"], "result_id": case["coverage"]["items"][0]["result"]["id"],
        "job_id": job["id"], "unit_id": unit["id"], "lot_id": unit["source_lot_id"],
        "order_id": change["order_id"], "milestone_id": change["milestone_id"],
    }
    schema = backend.get("/openapi.json").json()
    for name, endpoint in ENDPOINTS.items():
        if name in {'get_standard_change_context','get_standard_validation_intakes','get_standard_validation_intake','get_quality_context','get_quality_records','get_delivery_context','get_delivery_records'}:
            # Distinct source installations are exercised by standard and quality client tests.
            continue
        method = getattr(client, name)
        args = {p: values[p] for p in inspect.signature(method).parameters}
        if name == "get_historical_validation_job":
            args["job_id"] = history["id"]
        operation = schema["paths"]["/api/v1" + endpoint.path]["get"]
        documented = {p["name"] for p in operation.get("parameters", [])}
        assert set(args) == documented
        path_params = {p["name"] for p in operation.get("parameters", []) if p["in"] == "path"}
        expected = raw(backend, endpoint.path.format(**args), portfolio=True,
                       params={k: v for k, v in args.items() if k not in path_params})
        assert method(**args) == expected, name
    assert client.get_validation_reservation(job["id"]) == job["reservation"]
    assert client.get_dependencies(PORTFOLIO.program_id, change["milestone_id"])["dependencies"] == case["milestone"]["dependencies"]
    assert client.get_change_plans(change["id"])["items"] == change["plans"]
    pair = client.get_manufacturing_provenance(unit["id"])
    assert pair["unit"] == unit and pair["lot"]["id"] == unit["source_lot_id"]
    public_reads = {name for name, _ in inspect.getmembers(EnterpriseClient, inspect.isfunction) if name.startswith("get_")}
    assert public_reads == set(ENDPOINTS) | {"get_change_plans", "get_dependencies", "get_validation_reservation", "get_manufacturing_provenance"}
    assert all(getattr(EnterpriseClient, name).__doc__ for name in public_reads)


def test_legacy_server_scope_stays_narrow_and_unknown_matches_inaccessible(backend):
    client, _ = client_for(backend)
    errors = []
    for change_id in ("CR-105", "DOES-NOT-EXIST"):
        with pytest.raises(EnterpriseAPIError) as exc:
            client.get_change_request(change_id)
        errors.append((exc.value.info.kind, exc.value.info.http_status, exc.value.info.code))
    assert errors == [("not_found", 404, "NOT_FOUND")] * 2


def test_portfolio_client_rejects_other_scope_and_empty_aggregate_before_fetch(backend):
    client, recorder = client_for(backend, LEGACY, portfolio=True)
    for method in (client.get_validation_coverage, client.get_validation_options, client.get_validation_jobs):
        with pytest.raises(EnterpriseAPIError) as exc:
            method("CR-105")
        assert exc.value.info.kind == "scope"
    with pytest.raises(EnterpriseAPIError):
        client.get_implementation_links(LEGACY.program_id, "CR-105")
    assert not any(r["path"].endswith(("/coverage", "/options", "/jobs", "/implementation-links")) for r in recorder.receipts)
    with pytest.raises(EnterpriseAPIError):
        client.get_program(PORTFOLIO.program_id)


def test_customer_pairing_is_checked_even_for_program_only_records(backend):
    client, recorder = client_for(backend, Scope(program_id="PRG-P01", customer_id="CUST-FML01"), portfolio=True)
    with pytest.raises(EnterpriseAPIError) as exc:
        client.get_configuration("CFG-P01-TARGET")
    assert exc.value.info.kind == "scope"
    assert [r["path"] for r in recorder.receipts] == ["/api/v1/programs/PRG-P01"]


@pytest.mark.parametrize("bad_id", ["../plans", "CR-017?role=engineer", "https://example.com", "%2f..", "", "x" * 101, None, 1])
def test_invalid_identifiers_never_reach_transport(bad_id):
    class NoReads:
        def get(self, *args):
            pytest.fail("Invalid input caused HTTP access")
        def close(self):
            pass
    client = EnterpriseClient(ClientConfig(scope=LEGACY), transport=NoReads())
    with pytest.raises(EnterpriseAPIError) as exc:
        client.get_document(bad_id)
    assert exc.value.info.kind == "input"


@pytest.mark.parametrize("url", ["https://example.com", "http://user:secret@127.0.0.1:8000", "http://127.0.0.1:8000/api/v1", "http://127.0.0.1:8000?secret=yes", "file:///tmp/db", "http://127.0.0.1:99999", "http://127.0.0.1:8000?", "http://127.0.0.1:8000#", "http://127.0.0.1:8000\n"])
def test_base_url_rejects_nonlocal_credentials_and_paths(url):
    with pytest.raises(ValidationError) as exc:
        ClientConfig(scope=LEGACY, base_url=url)
    assert "user:secret" not in str(exc.value) and "secret=yes" not in str(exc.value)


@pytest.mark.parametrize("url", ["http://localhost:8000", "http://127.0.0.1:18013/", "http://[::1]:8000", "https://127.0.0.1"])
def test_valid_loopback_origins(url):
    assert ClientConfig(scope=LEGACY, base_url=url).base_url == url.rstrip("/")


@pytest.mark.parametrize("identity", ["demo-engineer-local-only", "demo-automation-local-only", "demo-portfolio-engineer-local-only", "unknown"])
def test_only_readonly_identities_can_be_configured(identity):
    with pytest.raises(ValidationError):
        ClientConfig(scope=LEGACY, reader_identity=identity)


MOCK_PROGRAM = {"id": "PRG-A17", "program_id": "PRG-A17", "customer_id": "CUST-FML01",
                "owning_system": "planner", "synthetic": True, "content_version": 1,
                "updated_at": "2026-11-16T09:00:00Z", "supplier_id": "SUP-001",
                "configuration_id": "CFG-B-01", "milestone_ids": [], "order_id": "ORD-1204"}


def mock_client(handler, **config_values):
    config = ClientConfig(scope=LEGACY, **config_values)
    http = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
    return EnterpriseClient(config, transport=HttpxReadTransport(config, http_client=http)), http


@pytest.mark.parametrize("status,kind,attempts", [(401, "unauthenticated", 1), (403, "forbidden", 1),
    (404, "not_found", 1), (409, "conflict", 1), (422, "validation", 1), (500, "server", 1),
    (502, "server", 3), (503, "server", 3), (504, "server", 3), (429, "http", 1)])
def test_error_status_mapping_retry_bounds_and_no_body_leak(status, kind, attempts, capsys, monkeypatch):
    calls = []
    sleeps = []
    monkeypatch.setattr("enterprise_api.transport.time.sleep", sleeps.append)
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"code": "NOT_FOUND" if status == 404 else "secret-value",
            "message": "private response body", "details": {"token": "private token"}}})
    client, http = mock_client(handler)
    with http, client, pytest.raises(EnterpriseAPIError) as exc:
        client.get_program(LEGACY.program_id)
    assert exc.value.info.kind == kind and exc.value.info.http_status == status
    assert exc.value.info.attempts == len(calls) == attempts
    assert len(sleeps) == attempts - 1
    serialized = json.dumps(exc.value.to_dict()) + str(exc.value)
    assert all(x not in serialized for x in ("secret-value", "private response body", "private token", "Bearer"))
    captured = capsys.readouterr()
    assert not captured.out and not captured.err


def test_transient_read_recovers_with_same_correlation_and_explicit_timeouts(monkeypatch):
    calls = []
    sleeps = []
    monkeypatch.setattr("enterprise_api.transport.time.sleep", sleeps.append)
    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.headers["authorization"] == "Bearer demo-reader-local-only"
        assert request.extensions["timeout"] == {"connect": 2.0, "read": 10.0, "write": 2.0, "pool": 2.0}
        return httpx.Response(503) if len(calls) < 3 else httpx.Response(200, json=MOCK_PROGRAM)
    client, http = mock_client(handler)
    with http, client:
        assert client.get_program(LEGACY.program_id) == MOCK_PROGRAM
    assert len(calls) == 3 and sleeps == [0.1, 0.2]
    assert len({r.headers["x-correlation-id"] for r in calls}) == 1


@pytest.mark.parametrize("error,kind", [(httpx.ConnectTimeout, "timeout"), (httpx.ReadTimeout, "timeout"), (httpx.ConnectError, "connection"), (httpx.ReadError, "connection"), (httpx.RemoteProtocolError, "connection")])
def test_transport_failures_are_bounded_and_safe(error, kind):
    calls = []
    def handler(request):
        calls.append(request)
        raise error("do not disclose this transport body", request=request)
    client, http = mock_client(handler, retry_backoff=0)
    with http, client, pytest.raises(EnterpriseAPIError) as exc:
        client.get_program(LEGACY.program_id)
    assert len(calls) == 3 and exc.value.info.kind == kind
    assert "do not disclose" not in str(exc.value) and exc.value.__suppress_context__


def test_redirect_is_not_followed():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(307, headers={"Location": "https://example.invalid/private"})
    client, http = mock_client(handler)
    with http, client, pytest.raises(EnterpriseAPIError) as exc:
        client.get_program(LEGACY.program_id)
    assert exc.value.info.http_status == 307 and len(calls) == 1


@pytest.mark.parametrize("body", [None, [], {"error": "private"}, {**MOCK_PROGRAM, "content_version": "1"}, {**MOCK_PROGRAM, "id": "WRONG"}, {**MOCK_PROGRAM, "extra": float("nan")}])
def test_invalid_success_is_never_canned_success_or_retried(body):
    from enterprise_api.transport import ReadResponse
    class Fake:
        calls = 0
        def get(self, path, params):
            self.calls += 1
            return ReadResponse(200, body)
        def close(self):
            pass
    transport = Fake()
    client = EnterpriseClient(ClientConfig(scope=LEGACY), transport=transport)
    with pytest.raises(EnterpriseAPIError) as exc:
        client.get_program(LEGACY.program_id)
    assert exc.value.info.kind == "invalid_response" and transport.calls == 1


def test_extra_authoritative_fields_preserved_and_no_record_cache():
    source = {**MOCK_PROGRAM, "future_metadata": {"keep": [1, "yes", None]}}
    client, http = mock_client(lambda request: httpx.Response(200, json=source))
    with http, client:
        first = client.get_program(LEGACY.program_id)
        assert first == source
        first["future_metadata"]["keep"].append("local mutation")
        source["content_version"] = 2
        assert client.get_program(LEGACY.program_id) == source
    assert not any(name.startswith(("post", "put", "patch", "delete", "approve", "create", "query")) for name in dir(EnterpriseClient))


def test_mixed_scope_collection_is_rejected_instead_of_silently_filtered():
    def handler(request):
        if request.url.path.endswith("/programs/PRG-A17"):
            return httpx.Response(200, json=MOCK_PROGRAM)
        return httpx.Response(200, json={"items": [MOCK_PROGRAM, {**MOCK_PROGRAM, "id": "PRG-OTHER", "program_id": "PRG-OTHER"}]})
    client, http = mock_client(handler)
    with http, client, pytest.raises(EnterpriseAPIError) as exc:
        client.get_programs(LEGACY.program_id)
    assert exc.value.info.kind == "scope"


def test_close_keeps_injected_transport_owned_by_caller():
    client, http = mock_client(lambda request: httpx.Response(200, json=MOCK_PROGRAM))
    client.close()
    assert not http.is_closed
    with pytest.raises(EnterpriseAPIError) as exc:
        client.get_program(LEGACY.program_id)
    assert exc.value.info.kind == "closed"
    http.close()


def test_runtime_package_has_no_backend_filesystem_or_model_dependencies():
    forbidden = {"mock_enterprise", "sqlite3", "openai", "agents", "mcp", "pathlib", "dotenv"}
    for path in (PROJECT / "src/enterprise_api").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not forbidden.intersection(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden
            elif isinstance(node, ast.Call):
                assert not (isinstance(node.func, ast.Name) and node.func.id == "open")
                assert not (isinstance(node.func, ast.Attribute) and node.func.attr in {"read_text", "read_bytes"})
    source = (PROJECT / "src/enterprise_api/client.py").read_text()
    assert "CR-017" not in source and "SLOT-PRIORITY" not in source
