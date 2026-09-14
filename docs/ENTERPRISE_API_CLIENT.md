# Phase 04 — Step 4: deterministic enterprise API client

This is the Step 4 implementation record. Step 5 subsequently added a separate
[local MCP server](MCP_SERVER_HANDOFF.md) exposing 25 selected read capabilities,
and optional shared correlation IDs to the client's HTTP transport. The backend
and client business behavior remain unchanged; the agent is still future work.

The `enterprise_api` package reads authoritative Stratos Silicon HTTP records and
server-calculated coverage/options. It performs no business reasoning, option
ranking, monetary/timing calculations, scheduling, approval, or other business
writes. It does not import or read the backend's classes, SQLite, fixtures, UI
state, `.env.local`, OpenAI SDK, or API key. No Git setup is required.

The authorized architecture remains:

```text
Future OpenAI Agent → MCP Server → Enterprise API Client → Stratos HTTP APIs → five mock applications
                                  [implemented here]
```

The Agent and MCP Server are future work. There are no function-tool decorators,
retrieval indexes, file search, or orchestration in this step. Historical
foundation-phase restrictions in `AGENTS.md` continue to apply to the business
systems; the user's Step 4 authorization permits this separate client only.

## Modules

| Module | Responsibility |
| --- | --- |
| `src/enterprise_api/__init__.py` | Public `EnterpriseClient`, `ClientConfig`, `Scope`, `EnterpriseAPIError` exports. |
| `src/enterprise_api/client.py` | Narrow business methods, scope checks, typed response validation, unchanged JSON results. |
| `src/enterprise_api/config.py` | Immutable customer/program scope, read-only selector choices, loopback origin and timeout/retry configuration. |
| `src/enterprise_api/models.py` | Independent Pydantic read DTOs based on the HTTP contract; no backend imports. |
| `src/enterprise_api/endpoints.py` | Explicit internal mapping to 30 existing GET operations. |
| `src/enterprise_api/transport.py` | Internal `ReadTransport` protocol, `ReadResponse`, and GET-only HTTPX adapter. |
| `src/enterprise_api/errors.py` | Safe structured client exceptions. |
| `scripts/check_enterprise_client.py` | Explicit real HTTP context collector and request receipts; no model calls or business writes. |
| `tests/test_enterprise_api.py` | Isolated-database HTTP tests and deterministic transport/error tests. |

## Install and call

HTTPX is the sole client-specific dependency and was already installed for this
project. It is declared in the optional `enterprise-client` extra; Pydantic is
already a main project dependency. Existing package versions and default backend
requirements are unchanged. The wheel includes the separate client package.

```sh
# Keep the earlier optional OpenAI runtime installed as well; this makes no API calls.
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --locked --extra enterprise-client --group openai-runtime --python .venv/bin/python --no-python-downloads
```

```python
from enterprise_api import ClientConfig, EnterpriseClient, Scope

config = ClientConfig(
    base_url="http://127.0.0.1:18013",
    scope=Scope(program_id="PRG-A17", customer_id="CUST-FML01"),
    reader_identity="demo-reader-local-only",
)
with EnterpriseClient(config) as client:
    change = client.get_change_request("CR-017")
    evidence = client.get_validation_coverage(change["id"])
    options = client.get_validation_options(change["id"])
```

Every business method returns a JSON-serializable dictionary. List routes preserve
the backend's `items` envelope. DTOs validate record envelopes, identifiers,
important source references, evidence structures, costs and workflow states while
preserving all additional JSON fields. Validation is intentionally not a duplicate
implementation of every backend business invariant. The client returns the
original JSON structure without coercing values or injecting model defaults.
Integer USD cents, explicit timestamp strings, source versions/digests, historical
snapshots, null timing, all eligibility flags and mismatch reasons remain intact.
An empty list means the API returned no records; it does not manufacture context.

## Public reads and future MCP mapping

All **34** `get_*` methods below are intended to become narrowly named, read-only
MCP tools in the next step. Their existing names, docstrings and typed string
inputs form the mapping contract. The future adapter should keep connection
settings, reader identity and client scope under trusted host configuration;
these are not arbitrary agent-supplied headers or URL inputs. `close`, context
management, the internal endpoint registry, and `ReadTransport.get` are not tools.
No MCP server or registration logic is included now.

All endpoint paths in this table are relative to `/api/v1`. Inputs are required
strings. Even where the backend permits an omitted program filter, this client
requires the bound `program_id` and always sends the filter. IDs accept only
1–100 ASCII letters, digits, underscores or hyphens, preventing path/query injection.

| Client method and inputs | Existing source GET | Description |
| --- | --- | --- |
| `get_change_requests(program_id)` | `/engineering/changes?program_id={program_id}` | List existing change requests for the bound program; no client filtering or ranking. |
| `get_change_request(change_id)` | `/engineering/changes/{change_id}` | Get a change, exact baseline/proposed revision references, and existing plans. |
| `get_requirement_revision(requirement_revision_id)` | `/engineering/requirements/{requirement_revision_id}` | Get the exact named requirement revision and its requested/approved status. |
| `get_configuration(configuration_id)` | `/engineering/configurations/{configuration_id}` | Get authoritative hardware, firmware, runtime and model applicability. |
| `get_workload_profile(workload_profile_id)` | `/engineering/workloads/{workload_profile_id}` | Get the exact workload manifest, bins, concurrency and required duration. |
| `get_procedure(procedure_id)` | `/engineering/procedures/{procedure_id}` | Get procedure eligibility, timing inputs, criteria reference and document ID. |
| `get_policy(policy_id)` | `/engineering/policies/{policy_id}` | Read delegated approval limits and permitted actions; grants no approval authority. |
| `get_acceptance_criteria(criteria_id)` | `/engineering/acceptance-criteria/{criteria_id}` | Get existing acceptance-criteria context without changing or inventing thresholds. |
| `get_documents(program_id)` | `/engineering/documents?program_id={program_id}` | List server-allowlisted business-document metadata for the bound program. |
| `get_document(document_id)` | `/engineering/documents/{document_id}` | Get one allowlisted business document by ID, including its content and provenance. |
| `get_plan(plan_id)` | `/engineering/plans/{plan_id}` | Get an existing immutable plan, digest, source snapshot and execution context. |
| `get_plan_decision(decision_id)` | `/engineering/decisions/{decision_id}` | Read an existing recorded decision and its exact plan binding; never approve. |
| `get_validation_coverage(change_id)` | `/validation/coverage?change_id={change_id}` | Get server-calculated coverage and all evidence/mismatch records; no local conclusions. |
| `get_validation_options(change_id)` | `/validation/options?change_id={change_id}` | Get every server-calculated option with timing, costs, eligibility and source versions. |
| `get_validation_result(result_id)` | `/validation/results/{result_id}` | Read recorded validation evidence and historical applicability snapshots. |
| `get_validation_samples(program_id)` | `/validation/samples?program_id={program_id}` | List samples, physical-unit references and current availability for the bound program. |
| `get_validation_jobs(change_id)` | `/validation/jobs?change_id={change_id}` | List existing jobs and their embedded reservations; scheduled is not tested. |
| `get_validation_job(job_id)` | `/validation/jobs/{job_id}` | Get an existing scheduled job and its exact resource reservation. |
| `get_historical_validation_job(job_id)` | `/validation/history/{job_id}` | Get imported lab-execution provenance and independent result IDs, separate from booking. |
| `get_manufacturing_units(program_id)` | `/manufacturing/units?program_id={program_id}` | List physical units and their recorded restrictions within the bound program. |
| `get_manufacturing_lots(program_id)` | `/manufacturing/lots?program_id={program_id}` | List manufacturing source lots and their recorded restrictions within the bound program. |
| `get_manufacturing_unit(unit_id)` | `/manufacturing/units/{unit_id}` | Get physical-unit provenance, source lot, restrictions and hold details. |
| `get_manufacturing_lot(lot_id)` | `/manufacturing/lots/{lot_id}` | Get a source lot with its authoritative restrictions and hold provenance. |
| `get_customer_orders(program_id)` | `/erp/orders?program_id={program_id}` | List authoritative customer orders and commitments for the bound program. |
| `get_customer_order(order_id)` | `/erp/orders/{order_id}` | Read customer quantity and committed delivery without altering commitments. |
| `get_cost_rates(program_id)` | `/erp/cost-rates?program_id={program_id}` | Get rates approved and effective at the server scenario time; preserve integer USD cents. |
| `get_programs(program_id)` | `/programs?program_id={program_id}` | Read the program directory narrowed to the bound program, including scenario metadata. |
| `get_program(program_id)` | `/programs/{program_id}` | Get the program and verify its customer association against this client's immutable scope. |
| `get_program_milestone(program_id, milestone_id)` | `/programs/{program_id}/milestones/{milestone_id}` | Get a milestone with baseline, forecast, record version and dependencies kept distinct. |
| `get_implementation_links(program_id, change_id)` | `/programs/{program_id}/implementation-links?change_id={change_id}` | Read existing Planner implementation links with their embedded tasks for this change. |
| `get_change_plans(change_id)` | `/engineering/changes/{change_id}` → unchanged `plans`, with change/program ID and record version | Project unchanged existing plans from the authoritative change response. |
| `get_validation_reservation(job_id)` | `/validation/jobs/{job_id}` → unchanged embedded `reservation` | Project the unchanged reservation embedded in GET /validation/jobs/{job_id}. |
| `get_manufacturing_provenance(unit_id)` | `/manufacturing/units/{unit_id}` then `/manufacturing/lots/{source_lot_id}` → both raw records | Read the unit and its referenced lot separately; retain both restriction sets unchanged. |
| `get_dependencies(program_id, milestone_id)` | `/programs/{program_id}/milestones/{milestone_id}` → unchanged `dependencies`, with milestone/program ID and record version | Project the milestone's unchanged dependencies with its ID and record version. |

There is no standalone dependency or reservation route. Those convenience methods
are explicit projections, not invented endpoints. Unit and lot restriction arrays
remain separate; provenance retrieval does not calculate a release or eligibility
decision. Existing plans expose their decision IDs for `get_plan_decision`.
Imported historical jobs are separate from scheduled jobs and independent results.
The broad `/portfolio` UI aggregate and audit endpoint are deliberately not public
client methods in this step.

## Identity and scoping

Only the existing `demo-reader-local-only` and
`demo-portfolio-reader-local-only` mock selectors can be configured. Automation,
engineer, arbitrary bearer strings and real credentials are rejected as settings.
These public selectors are role-test stand-ins, not production authentication or
proof of a human's identity.

The default reader remains server-scoped to PRG-A17 / CUST-FML01. The portfolio
reader retains its existing server-owned membership allowlist, while each client
instance is narrowed to one explicit `Scope`. A scope cannot add server permission.
To work in a different authorized scope, construct another client instance; methods
cannot switch identities or widen the scope.

Before its first ordinary read, the client retrieves the bound program over HTTP
and verifies the customer/program association. It remembers only that verification,
not business records. All subsequent responses are checked recursively for matching
program/customer fields, including nested records and snapshots. A supplied
`program_id` outside the bound scope fails locally. A direct record lookup is still
server-authorized, then checked against the client scope before returning it.
Mixed-scope collections are rejected in full rather than silently filtered.

Coverage, options, job lists and implementation-link lists first retrieve their
change to verify its scope, even if the aggregate could return an empty list with
no scope fields. Missing/inaccessible resources preserve the server's indistinguishable
404 behavior. Local narrowing failures use `kind=scope`, `code=SCOPE_MISMATCH` or
`CHANGE_SCOPE_MISMATCH`, without pretending that the server returned a 403/404.

## Transport, timeouts and retries

`EnterpriseClient` accepts an injected internal `ReadTransport` for direct tests
and other trusted callers. The default `HttpxReadTransport` is independent of MCP
or any model SDK. Tests inject an HTTPX client connected to an isolated ASGI
backend or MockTransport. Backend classes are used only to bootstrap those test
servers, never inside the client or real integration collector.

- Configurable HTTP(S) **loopback origin** only; default `http://127.0.0.1:8000`.
  Origins cannot include credentials, a path prefix, query, fragment or whitespace.
- Default connect timeout **2 seconds**, read timeout **10 seconds**, and
  write/pool timeouts **2 seconds**. Connect is configurable up to 30 seconds and
  read up to 60 seconds. These are HTTPX phase timeouts, not an end-to-end deadline.
- Default **2 retries / 3 attempts per GET**, configurable down to zero retries.
  Only transport timeouts, network failures, remote protocol failures and HTTP
  **502/503/504** retry. Fixed exponential sleeps are **0.1, 0.2 seconds** by
  default; there is no random jitter or indefinite retry loop.
- 401/403/404/409/422, 429, 500 and other statuses are not automatically retried.
  Malformed successful JSON and scope/identifier failures are not retried.
- One generated correlation ID is reused across attempts of one logical GET.
  Server-generated request IDs are retained only in their documented safe form.
- Redirects are rejected, environment proxy configuration is not inherited, and
  TLS verification stays enabled. Only GET is sent; no business-write primitive
  or public arbitrary URL/query method is exposed.
- A business method may make a scope-validation GET as well as its source GET.
  Compositions may make several reads; the three-attempt cap applies to each read.
- No business-record cache, database fallback, local fixture fallback or cross-system
  transaction is implemented. A multi-read context is a sequence of authoritative
  reads, not a guaranteed atomic cross-system snapshot. Returned versions and HTTP
  receipts allow later reasoning to assess freshness.
- Context management closes client-owned transports. Injected transports and their
  HTTP clients remain caller-owned. Custom transports are trusted infrastructure
  and must implement appropriate read-only I/O and retry behavior.

## Error model

Catch `EnterpriseAPIError` and use `to_dict()` for a JSON-safe result. Fields are
`kind`, `code`, `http_status`, `retryable`, `attempts`, `request_id`, and
`correlation_id`. Exceptions use fixed messages. Raw HTTP bodies, server prose,
`error.details`, headers and underlying exception strings are never serialized.
Only explicitly allowlisted backend error codes are retained; other codes become
`HTTP_ERROR`. Underlying transport/validation tracebacks are suppressed at the
public error boundary. The client itself adds no request/body logging.

| Condition | Error kind | Automatic retry |
| --- | --- | --- |
| 401 | `unauthenticated` | No |
| 403 | `forbidden` | No |
| 404, including inaccessible records | `not_found` | No |
| 409 | `conflict` | No |
| 422 | `validation` | No |
| 5xx | `server` | Only 502/503/504, bounded as above |
| Other non-200 HTTP status, including redirects | `http` | No |
| Transport timeout | `timeout` / `READ_TIMEOUT` | Bounded |
| Transient network/protocol failure | `connection` / `READ_CONNECTION_FAILED` | Bounded |
| Other HTTPX transport error | `connection` / `READ_TRANSPORT_FAILED` | No |
| Malformed successful data or unexpected record ID | `invalid_response` | No |
| Invalid identifier | `input` / `INVALID_IDENTIFIER` | No HTTP call |
| Local scope mismatch | `scope` | No further fetch or returned data |
| Closed client | `closed` / `CLIENT_CLOSED` | No HTTP call |

`retryable=true` identifies a transient category after the client's bounded retries
are exhausted; it is not a promise of success or permission for unbounded outer
retries. Configuration models raise Pydantic validation errors with input values
hidden in their displayed messages.

## CR-017 real localhost integration

The running service on port **8000** was an older preview: it lacked `/portfolio`
and `/validation/history/{job_id}` and had older additive response fields. This
was surfaced during inspection. The already-running enriched Stratos preview on
**18013** returned an OpenAPI schema exactly equal to `docs/openapi.json`, including
33 GET operations (32 business reads and health). It was used without restarting,
resetting, reseeding or otherwise changing either running service.

Command actually run once:

```sh
.venv/bin/python scripts/check_enterprise_client.py --base-url http://127.0.0.1:18013 --output .cache/enterprise-client/cr017-http.json
```

The collector followed IDs from the change, requirements, coverage, options,
samples, plans and jobs. It kept every validation option and evidence record and
retrieved only raw source records or server-calculated results. It neither selected
an option nor asserted an expected business answer. Its only calculations are
request latency, record counts and response hashes for HTTP receipts.

Recorded UTC timestamp: `2026-09-11T01:44:51.831526+00:00`.

**40 logical GETs / 40 HTTP attempts; every response was HTTP 200.**

Scope: `CR-017`, `PRG-A17`, `CUST-FML01`, using the legacy reader.

| Retrieved context | Observed count |
| --- | --- |
| requirement revisions | 2 |
| configurations | 1 |
| workloads | 2 |
| procedures | 1 |
| policies | 1 |
| criteria | 1 |
| documents | 6 |
| validation results | 3 |
| validation options | 9 |
| samples | 3 |
| unit lot provenance pairs | 3 |
| orders | 1 |
| approved cost rates | 3 |
| plans | 0 |
| decisions | 0 |
| jobs | 0 |
| reservations | 0 |
| milestones | 1 |
| dependencies | 1 |
| implementation links | 0 |

Zero plans/decisions/jobs/reservations/links reflects the running CR-017 state; none
was created to fill those gaps. Those populated-record methods were exercised
against the existing seeded records in isolated portfolio test databases.

The complete raw context and per-request receipts are retained at
[`.cache/enterprise-client/cr017-http.json`](../.cache/enterprise-client/cr017-http.json).
Each receipt includes the exact GET path/query, status, attempt count, elapsed
time, request/correlation IDs and a canonical response hash. Credentials and
request headers are absent. The artifact and developer tests are outside the
backend's allowlisted business-document retrieval.

## Verification and limits

- Initial focused run: **50 client tests passed in 2.71 seconds**. An initial
  Starlette TestClient timeout deprecation was fixed by building the timed HTTPX
  GET request explicitly before sending it; runtime timeouts were preserved.
- Full suite command: `TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q tests runtime_checks/test_openai_connection.py --tb=short`.
  **275 passed in 46.77 seconds** before the final URL-delimiter/whitespace edge
  cases were added. Final verification is recorded below.
- Each of the 30 direct methods is checked against the real route and parameter
  inventory of an isolated backend, and its full JSON output is compared to that
  endpoint. The four projections are compared with their source records.
- Tests cover non-widening identities, legacy and portfolio scopes, customer/program
  pairing, mixed-scope collections, empty aggregates, injection-shaped identifiers,
  preservation of extra JSON fields, malformed success, 401/403/404/409/422/5xx,
  redirects, timeout/network failures, bounded retries, and owned resource cleanup.
- The read-only context test compares the entire API-visible portfolio before and
  after client reads. No business mutation methods are used by the new tests.
- Existing backend/frontend source remains unchanged; no OpenAI call, Agents SDK
  agent, MCP server, function tool, retrieval or orchestration was built or run.
- Frontend browser/build checks were not rerun because this step changes no
  frontend files. Production authentication, nonlocal hosting, distributed
  snapshots and an MCP adapter remain outside this step.

### Final verification

- Focused final client regression:
  `TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q tests/test_enterprise_api.py --tb=short`
  — **57 passed in 2.95 seconds**.
- Final complete regression, including the existing backend suite and offline
  OpenAI connectivity tests:
  `TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q tests runtime_checks/test_openai_connection.py --tb=short`
  — **282 passed in 45.72 seconds**, zero failures/skips.
- `uv pip check --python .venv/bin/python --cache-dir .cache/uv`
  — **26 installed packages checked; all compatible**.
- `uv lock` and `uv sync --locked --extra enterprise-client --group openai-runtime`
  with the existing Python and project-local cache completed successfully. No new
  package or existing package-version change was required.
- `scripts/check_enterprise_client.py --help` completed without HTTP requests.
- Hash comparisons confirmed no changes to existing backend/frontend source.
  The modified existing files are `pyproject.toml`, `uv.lock`, and `README.md`.
  New code is confined to `src/enterprise_api/`, the integration script, tests,
  and this handoff. Preservation metadata is recorded in
  [`.cache/enterprise-client/preservation.json`](../.cache/enterprise-client/preservation.json).
- One CR-017 live integration collector run made **40 successful GETs**; no live
  retries, business writes, resets or service restarts occurred. The client was
  not used to make any OpenAI requests.

ENTERPRISE API CLIENT STATUS: PASS
