# Phase 04 — Step 5: local Stratos Silicon MCP server

The local service exposes **25 read-only tools over Streamable HTTP** at
**http://127.0.0.1:9000/mcp**. Its current backend is **http://127.0.0.1:9001**,
running the existing Stratos code against a separate initialized demo database.
All five source systems remain in one existing FastAPI backend process.

```text
Future OpenAI Agent (not implemented)
    → MCP client
    → Stratos MCP server :9000/mcp
    → existing EnterpriseClient
    → existing Stratos HTTP APIs :9001
    → Engineering / Validation / Manufacturing / ERP / Program Planner
```

This step builds only the MCP adapter. It creates no agent, approval workflow,
business-write tool, retrieval index, file search, orchestration, model routing,
or control plane. **No OpenAI model calls occurred.** The MCP process does not
load `.env.local`, read an OpenAI key, or import the OpenAI/Agents SDKs. There is
no Git prerequisite.

## Official guidance and dependencies

Guidance checked on 2026-09-11 UTC:

- The [official OpenAI Agents SDK MCP guide](https://openai.github.io/openai-agents-python/mcp/)
  documents `MCPServerStreamableHttp` for locally reachable services and compatibility
  with MCP Python SDK v1/v2. That connection is future work; no agent was built.
- The [official MCP Python SDK](https://py.sdk.modelcontextprotocol.io/)
  identifies v2 as its current stable line. This project locks **mcp 2.2.0**.
- The [transport guide](https://py.sdk.modelcontextprotocol.io/run/)
  documents Streamable HTTP and recommends it over the legacy SSE transport.
- The [low-level Server guide](https://py.sdk.modelcontextprotocol.io/advanced/low-level-server/)
  supports explicit schemas, structured content, errors and result metadata.
  This adapter uses that official `Server` with typed Pydantic input validation,
  rather than reimplementing MCP parsing, discovery, handshakes or transport.

The MCP SDK requires Pydantic >=2.12; the backend intentionally retains its
existing >=2.10,<2.11 constraint. `mcp_server/pyproject.toml` and its separate
`uv.lock` therefore manage **mcp_server/.venv**. The root environment and lock
remain unchanged. Both use the existing Python **3.12.10** installation.
The MCP environment contains Pydantic **2.13.5**, HTTPX **0.28.1** for the
enterprise client, and the SDK's HTTPX2 **2.12.0** for MCP connections.
There are 36 installed MCP-environment packages, including test dependencies.
No MCP CLI extra, OpenAI SDK or Agents SDK is installed there. The SDK's
transitive OpenTelemetry API is present; no exporter, observability service,
or external tracing vendor is configured.

The local source checkout is made importable with `PYTHONPATH="$PWD/src"`.
The MCP runtime is a separate local environment, not a new root wheel/deployment.
Both environments import the same `src/enterprise_api` source; no client code is
copied or forked.

## Modules

| File | Responsibility |
| --- | --- |
| `src/stratos_mcp/catalog.py` | Explicit domain catalog, typed ID inputs, tool annotations and structured output schema. |
| `src/stratos_mcp/service.py` | Safe execution through EnterpriseClient, per-call resources, bounded workers, trace receipts and readiness. |
| `src/stratos_mcp/server.py` | Official MCP Server, Streamable HTTP app, safe protocol boundary, health and Host/Origin checks. |
| `src/stratos_mcp/config.py` | Immutable, trusted loopback listener and enterprise-client settings. |
| `src/stratos_mcp/__main__.py` | Local CLI, sanitized argument failures, safe event logs and Uvicorn lifecycle. |
| `src/enterprise_api/transport.py` | Small compatible extension: optional trusted correlation ID and sanitized server correlation echo. |
| `mcp_server/client.py` | Reusable official SDK client connection, without models or database imports. |
| `mcp_server/probe.py` | Model-free discovery and one-change connection check. |
| `mcp_server/check_mcp.py` | Real HTTP integration collector and exact enterprise-client comparisons. |
| `mcp_server/testing.py`, `backend_fixture.py` | Test-only isolated backend/process setup, shutdown and database fingerprints. Never imported by the MCP service. |
| `mcp_server/tests/` | Automated protocol, schema, scope, error, lifecycle and integration checks. |

## Catalog and source mapping

Every input below is required, strictly a string, 1–100 ASCII letters/digits,
underscore or hyphen. Additional inputs are rejected. No URL, credential,
identity, SQL, file path or arbitrary query argument is available.

All source paths below are existing **GET** operations relative to `/api/v1`.
The client may additionally read the configured program or change to verify scope.
All 25 names are intended for the future agent's MCP tool catalog.

| Domain | MCP tool and inputs | EnterpriseClient method | Source GET |
| --- | --- | --- | --- |
| Engineering | `get_change_request(change_id)` | same name | `/engineering/changes/{change_id}` |
| Engineering | `get_requirement_revision(requirement_revision_id)` | same name | `/engineering/requirements/{requirement_revision_id}` |
| Engineering | `get_configuration(configuration_id)` | same name | `/engineering/configurations/{configuration_id}` |
| Engineering | `get_workload_profile(workload_profile_id)` | same name | `/engineering/workloads/{workload_profile_id}` |
| Engineering | `get_procedure(procedure_id)` | same name | `/engineering/procedures/{procedure_id}` |
| Engineering | `get_policy(policy_id)` | same name | `/engineering/policies/{policy_id}` |
| Engineering | `get_acceptance_criteria(criteria_id)` | same name | `/engineering/acceptance-criteria/{criteria_id}` |
| Engineering | `get_document(document_id)` | same name | `/engineering/documents/{document_id}` |
| Engineering | `get_documents(program_id)` | same name | `/engineering/documents?program_id=…` |
| Engineering | `get_plan(plan_id)` | same name | `/engineering/plans/{plan_id}` |
| Engineering | `get_decision(decision_id)` | `get_plan_decision` | `/engineering/decisions/{decision_id}` |
| Validation | `get_validation_coverage(change_id)` | same name | `/validation/coverage?change_id=…` |
| Validation | `get_validation_options(change_id)` | same name | `/validation/options?change_id=…` |
| Validation | `get_validation_result(result_id)` | same name | `/validation/results/{result_id}` |
| Validation | `get_validation_samples(program_id)` | same name | `/validation/samples?program_id=…` |
| Validation | `get_validation_jobs(change_id)` | same name | `/validation/jobs?change_id=…` |
| Validation | `get_validation_job(job_id)` | same name | `/validation/jobs/{job_id}`; reservation remains embedded |
| Manufacturing | `get_manufacturing_unit(unit_id)` | same name | `/manufacturing/units/{unit_id}` |
| Manufacturing | `get_manufacturing_lot(lot_id)` | same name | `/manufacturing/lots/{lot_id}` |
| ERP | `get_customer_order(order_id)` | same name | `/erp/orders/{order_id}` |
| ERP | `get_cost_rates(program_id)` | same name | `/erp/cost-rates?program_id=…` |
| Planner | `get_program(program_id)` | same name | `/programs/{program_id}` |
| Planner | `get_program_milestone(program_id, milestone_id)` | same name | `/programs/{program_id}/milestones/{milestone_id}` |
| Planner | `get_dependencies(program_id, milestone_id)` | same name | Same milestone GET; projects unchanged dependencies plus IDs/version |
| Planner | `get_implementation_links(program_id, change_id)` | same name | `/programs/{program_id}/implementation-links?change_id=…` |

The one addition to the 24 requested names is scoped document discovery. It
allows supplemental allowlisted documents to be found entirely through MCP.
Redundant collection/projection methods and historical-job lookup remain available
on EnterpriseClient but are not MCP tools in this step.

## Output, errors and traceability

Each tool advertises an `outputSchema` and returns the same JSON envelope in
`structuredContent` and a JSON text content block:

```json
{"ok": true, "data": {"...": "unchanged enterprise-client record or items envelope"}, "error": null}
```

Success data is not ranked, summarized, coerced or augmented. Its domain shape is
validated by the existing enterprise client's DTOs. The MCP output schema types
the envelope and JSON data; it intentionally does not duplicate every backend DTO.
On failure, `ok=false`, `data=null`, and MCP **isError=true**. The structured
`error` contains only `kind`, `code`, `http_status`, `retryable`, `attempts`,
`request_id`, and `correlation_id`.

| Failure | Result |
| --- | --- |
| Invalid IDs, missing/extra inputs | `input / INVALID_TOOL_INPUT`; no downstream HTTP |
| Unregistered tool | `input / UNKNOWN_TOOL`; no dispatch or HTTP |
| 401 / 403 / 404 | `unauthenticated` / `forbidden` / `not_found`; original safe status retained |
| 409 / 422 | `conflict` / `validation` |
| 5xx | `server`; only 502/503/504 receive bounded client retries |
| Backend unavailable / timeout | `connection` / `timeout`; bounded retries exhausted safely |
| Wrong customer/program or mixed-scope data | `scope`; no returned business data |
| Malformed success | `invalid_response`; no invented fallback |
| Unexpected adapter exception | fixed `server / INTERNAL_ERROR`; no exception prose |
| Malformed/unsupported MCP request | sanitized protocol error, not a business success |

No raw HTTP error bodies, `error.details`, headers, credentials, stack traces or
database paths are returned. CLI parsing and startup errors likewise avoid echoing
supplied values. Third-party request/debug/error logging is suppressed in the CLI;
the service emits fixed-field startup, tool-call and shutdown events only.

Each call generates an `mcp-<32 hex>` call ID and a `corr-<32 hex>` correlation ID.
Result `_meta["stratos/trace"]` holds both plus latency and downstream receipts.
Every scope/source GET within that call sends the same `X-Correlation-ID`, including
retries. Receipts contain GET path/query, final status, attempt count, latency,
sanitized server request ID and correlation echo. Tests verify that the server
echo equals the call's generated correlation ID. The backend already uses this
header for request/audit correlation; no backend change was needed.

Incoming `_meta` and MCP authorization headers cannot set identity, scope or
downstream headers. Future agent code can retain the returned trace metadata
alongside its own run/tool-call ID. Metadata is not mixed into authoritative data.
Receipts identify the final HTTP response of a retried GET, not every intermediate
response. Logs retain call IDs/counts, not business payloads or input arguments.

## Security, timeouts and lifecycle

The running server is fixed to **PRG-A17 / CUST-FML01** and the existing legacy
reader. Trusted startup configuration also supports the existing portfolio reader,
still narrowed to one explicit customer/program pair. Only the two reader
selectors pass configuration validation. A caller cannot promote itself by sending
engineer headers or metadata. The backend remains authoritative for membership;
missing and inaccessible records retain indistinguishable 404 responses.

Mock identities remain role-test stand-ins, not production authentication. Any
local process able to reach this endpoint has its configured scoped read access.
There is no OAuth, remote ingress, public tunnel, CORS grant or public deployment.
The CLI accepts only `127.0.0.1`, `localhost` (normalized to 127.0.0.1), or `::1`.
Exact local Host/Origin allowlists protect MCP and health routes against DNS
rebinding. Forwarded proxy headers are disabled. HTTP bodies are capped at 16 KiB.

Streamable HTTP uses the official stateless transport with JSON responses and
`/mcp`. There is no legacy `/sse` endpoint. Tests also exercise the legacy MCP
handshake **over Streamable HTTP**, in addition to modern discovery.

Defaults inherited from EnterpriseClient: connect/write/pool **2 seconds**, read
**10 seconds**, at most **2 retries / 3 attempts per GET**, fixed delays **0.1/0.2
seconds**. Only network/timeouts/remote protocol errors and 502/503/504 retry.
401/403/404/409/422/429/500 and malformed successful data do not retry. Redirects
and inherited proxy settings are disabled. There is no outer MCP retry loop.

Each tool call owns a fresh client/HTTP transport and closes it, including on
failure. Blocking reads use at most eight workers; cancellation joins the worker
so a connection is not closed while its GET is in flight. Timeouts are HTTP phase
timeouts, not a total tool deadline; scope checks can add GETs and queued calls
can wait for a worker. The reusable MCP client has a 120-second read timeout.
Adjust that deliberately if using larger backend timeout settings.

`GET /health` reports process liveness without backend access. `GET /ready`
performs a fresh scoped program GET with a 0.5-second connect timeout, 1-second
read timeout and no retries; it returns 200 or 503. It verifies that scoped read,
not every possible tool. Discovery still works while the backend is unavailable.
Ctrl-C completes Uvicorn/SDK shutdown and emits a `stopped` event. Tests verify
exit code zero and close only the processes they started.

## Local operations

Run these commands from the repository root:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --project mcp_server --locked \
  --python "$PWD/.venv/bin/python" --no-python-downloads

env -u OPENAI_API_KEY PYTHONPATH="$PWD/src" \
  mcp_server/.venv/bin/python -m stratos_mcp \
  --backend-url http://127.0.0.1:9001 --host 127.0.0.1 --port 9000
```

Stop with Ctrl-C in that terminal. `--help` lists program/customer/reader and
timeout settings. If port 9000 is busy, select another loopback port explicitly;
the CLI fails safely rather than attaching to an unknown service.

The previously enriched preview on 18013 was no longer running. Port 8000 still
served an older schema: a probe correctly returned `INVALID_RESPONSE` for its
older change record. Its schema/DTO requirements were not relaxed and that
service was not stopped, reset or reseeded. A separate current backend was
initialized at `.demo/mcp-step5.sqlite3` and started on 9001:

```sh
# Initialization was already completed. This command refuses to replace an
# existing database; do not reset it to restart the service.
env -u OPENAI_API_KEY DEMO_MODE=true DEMO_DB="$PWD/.demo/mcp-step5.sqlite3" \
  .venv/bin/python -m mock_enterprise.cli init-demo

# Restart only needs this command, in a separate terminal.
env -u OPENAI_API_KEY DEMO_MODE=true DEMO_DB="$PWD/.demo/mcp-step5.sqlite3" \
  .venv/bin/python -m mock_enterprise.cli serve --port 9001
```

At handoff both are listening on 127.0.0.1: MCP PID **86315**, backend PID **82413**.
To stop these specific current processes, use `kill -INT 86315` and
`kill -INT 82413`. These IDs are only valid for this recorded run; after a restart,
use the new terminal's Ctrl-C instead. The existing frontend is unchanged and
was not redirected to this separate demo database.

Connect with the reusable model-free probe:

```sh
env -u OPENAI_API_KEY PYTHONPATH="$PWD/src" \
  mcp_server/.venv/bin/python -m mcp_server.probe --origin http://127.0.0.1:9000
```

Or call the official SDK connection directly from local Python in that environment:

```python
from mcp_server.client import connect

async def read_change():
    async with connect("http://127.0.0.1:9000/mcp") as client:
        tools = await client.list_tools()
        result = await client.call_tool("get_change_request", {"change_id": "CR-017"})
        return result.structured_content, result.meta
```

## Verification actually performed

Final commands/results:

```sh
TMPDIR="$PWD/.cache/tmp" mcp_server/.venv/bin/python -m pytest \
  -c mcp_server/pyproject.toml mcp_server/tests -q --tb=short
# 56 passed in 10.31 seconds; no failures/skips.

TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q \
  tests runtime_checks/test_openai_connection.py --tb=short
# 282 passed in 45.93 seconds; no failures/skips. OpenAI tests are offline.

uv pip check --python mcp_server/.venv/bin/python --cache-dir .cache/uv
# 36 installed packages, all compatible.
uv pip check --python .venv/bin/python --cache-dir .cache/uv
# 26 installed packages, all compatible.

env -u OPENAI_API_KEY PYTHONPATH="$PWD/src" \
  mcp_server/.venv/bin/python -m mcp_server.check_mcp
```

Tests cover all required categories: startup/discovery, schema-to-client/OpenAPI
mapping, strict input validation, unauthorized/missing records, customer pairing,
non-widening portfolio scope, ignored caller identity/metadata, errors and retry
bounds, backend unavailable readiness, malformed protocol requests, Host/Origin
rejection, body limits, unknown/write-tool rejection, concurrent call isolation,
deterministic results, real HTTP integrity and graceful shutdown.

Development fixes included the Starlette 1.x middleware registration API, keeping
pytest temporary paths under the project, and exercising Ctrl-C for deterministic
zero-exit shutdown (Uvicorn re-raises SIGTERM after graceful cleanup). All were
resolved before the final results above.

The separate integration run recorded **2026-09-11T02:33:59.919143+00:00** used a
fresh isolated temporary database, current backend at `http://127.0.0.1:59592`,
and MCP at `http://127.0.0.1:59607/mcp`. These temporary servers were stopped after
verification and their database removed. Their OpenAPI matched
`docs/openapi.json` exactly.

**25 tools discovered and successfully invoked; 40 successful MCP tool calls;
84 downstream logical GETs / 84 attempts, all HTTP 200.** CR-017 accounted for
36 calls / 75 GETs, including a repeated change read. Four additional calls read
existing seeded plan `plan-P01-1`, decision `decision-P01-1`, job `job-P01-1` and
CR-105 implementation links using a separate MCP instance fixed to
PRG-P01 / CUST-NORTH. No records were created to exercise these tools.
Observed server tool latency: min **12.59 ms**, median **14.68 ms**, max **33.66 ms**;
these are tool execution measurements, not a performance guarantee.

Every MCP `data` result equaled the corresponding enterprise-client JSON. All
context retrieval, including document discovery, crossed MCP. The independent
comparison oracle uses the enterprise client over HTTP; the test also reads the
existing portfolio API before/after. Neither server runtime uses that test oracle.

| CR-017 authoritative context | Observed count |
| --- | --- |
| Requirement revisions / configurations / workloads | 2 / 1 / 2 |
| Procedures / policies / acceptance criteria | 1 / 1 / 1 |
| Allowlisted business documents | 6 |
| Validation options / recorded results / samples | 9 / 3 / 3 |
| Manufacturing units / source lots | 3 / 3 |
| Customer orders / approved rates | 1 / 3 |
| Existing plans / decisions / jobs | 0 / 0 / 0 |
| Milestones / dependencies / implementation links | 1 / 1 / 0 |

The collector follows source IDs and retains every option/evidence item. Empty
collections remain empty. It does not assert CR-017's answer, select a recommended
option, or perform business reasoning. Representative calls were
`get_change_request({"change_id":"CR-017"})`, baseline/proposed revision reads
using returned IDs, `get_validation_coverage` / `get_validation_options` for the
change, unit/lot reads from returned sample references, the referenced customer
order, and the program's milestone/dependencies/links.

Both the API-visible portfolio and **all persisted tables**, including audit and
idempotency, were unchanged in the successful isolated integration. The test-only
bootstrap computed equal logical-dump SHA-256 fingerprints:
`adca393c493e6e21d3b26e4e31061d35e5ca966d308af004239dcefa26e7501f`.
Only the test helper accesses this isolated database; the MCP service and client
never do. Negative authorization tests use a different isolated database, where
the existing backend may record denials without changing business state.

The full report, raw authoritative context and trace receipts are in
[live-integration.json](../.cache/mcp-server/live-integration.json).
The final persistent 9000→9001 service also passed 25-tool discovery and 36 CR-017
calls across all five domains, with exact client comparisons, captured in
[running-preview.json](../.cache/mcp-server/running-preview.json).
Developer artifacts and tests are outside the business-document allowlist.

Hashes confirmed all 39 protected existing backend/frontend source and root
dependency files unchanged; see
[preservation.json](../.cache/mcp-server/preservation.json). Existing client JSON
behavior is unchanged; its HTTP transport gained correlation support only.
README and new MCP files/documentation are the other work products.
Frontend/browser/build checks were not repeated because no frontend code changed.

## Next phase and limitations

A future locally running OpenAI Agents SDK process should connect with
`MCPServerStreamableHttp` using this loopback URL, discover/cache the stable
catalog, and attach that connection to its agent through `mcp_servers`. It should
inspect `isError`/`ok` before reasoning over `data` and retain trace metadata.
Configure any model key in that future agent process, not in this MCP service.
No agent code or model execution is included in this handoff. A hosted Responses
MCP tool cannot reach this private loopback listener from OpenAI infrastructure;
the intended next step is a local Agents SDK MCP connection.

Scope is fixed per server instance; switching customers requires trusted startup
configuration for another authorized pair. This is a synthetic local trust model,
not production multi-user authentication. No distributed snapshot is promised:
multiple source GETs can observe changing versions, which remain in the returned
records. Supplemental context is allowlisted business content, not instructions
for an agent to obey. There is no business cache or database/fixture fallback.
Production hosting, OAuth, remote tracing, write tools and approval workflows
remain out of scope.

MCP SERVER STATUS: PASS
