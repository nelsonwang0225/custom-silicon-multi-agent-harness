Current enrichment work is documented in [DATA_ENRICHMENT_HANDOFF.md](DATA_ENRICHMENT_HANDOFF.md).
This build handoff is the historical API-foundation milestone.

# Mock-enterprise build handoff

**BUILD STATUS: PASS.** Implementation, automated tests and real localhost HTTP
verification completed September 10, 2026. Final suite: **172 passed in 25.52s;
0 failed, 0 skipped**. No AI-agent or business-frontend phase was started.

## Delivered behavior

One Python FastAPI service with five domain modules, persistent file-backed SQLite,
typed input/output models, generated interactive docs and exported OpenAPI. Four
controlled POSTs persist immutable plans/assessments, exact engineer decisions,
Validation jobs/reservations, and Planner links/tasks/conditional forecasts.

The automation identity cannot approve. A supplied approval ID is checked against
its actual decision, role, plan ID/version/digest, scope, selected resources, cost,
permitted actions and source snapshot. Changed sources reject unexecuted actions.
Approval workflow updates and the same plan's own reservation are recognized as
expected transitions. Source content, availability and workflow versions are distinct.

Every successful business mutation commits an immutable audit event and durable
idempotency receipt with its owned changes. Successful retries return the original
status/body; new-key duplicates cannot book or link again. SQLite foreign keys,
uniqueness constraints, immutable-row triggers, optimistic comparisons and per-domain
SQL write authorizers backstop service validation. No distributed transaction is
claimed. Planner failure preserves an already committed lab booking.

Manufacturing and ERP expose only GETs. No API edits commitments, baseline dates,
acceptance criteria or test results. Scheduling leaves evidence unchanged and never
sets tested/passed/qualified/accepted state. Results and business documents remain
persisted synthetic data, not dynamically fabricated responses.

## Tested stack

| Component | Actual installed version |
|---|---|
| Python | 3.12.10, installed under project `.tools/python/` |
| uv | 0.7.6, pre-existing executable |
| SQLite | 3.47.1 through Python standard library |
| FastAPI / Starlette | 0.115.14 / 0.46.2 |
| Pydantic | 2.10.6 |
| Uvicorn | 0.52.4 |
| pytest | 9.1.1 |
| HTTPX / AnyIO | 0.28.1 / 4.9.0 |

`uv.lock` captures resolved versions. Dependency ranges deliberately retain the
verified HTTPX/TestClient combination. No OpenAI, Agents SDK, cloud, ORM, message
broker or frontend dependency was added. All installed tools/environments/caches
are under the project; no user configuration or files outside it were changed.

## Exact setup, serve, test and reset commands

Run from the project root:

```sh
mkdir -p .cache/tmp .cache/uv .tools/python
export UV_CACHE_DIR="$PWD/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$PWD/.tools/python"
export TMPDIR="$PWD/.cache/tmp"
uv sync --locked --python 3.12

# Only when the default DB does not already exist:
DEMO_MODE=true .venv/bin/mock-enterprise init-demo

# Serve existing persisted state:
DEMO_MODE=true .venv/bin/mock-enterprise serve --port 8000
```

Default DB: `.demo/enterprise.sqlite3`. Current handoff service uses port 8000 and
original seed state. API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
Schema: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json).
The CLI binds only to 127.0.0.1. Stop the server before starting another on that port.

```sh
# All automated checks, including real server lifecycle integration:
TMPDIR="$PWD/.cache/tmp" .venv/bin/pytest -q

# Independent fixture consistency check, not an API test:
.venv/bin/python scripts/validate_scenario.py

# Standalone real-server workflow, restart and two resets on an isolated DB:
TMPDIR="$PWD/.cache/tmp" .venv/bin/python scripts/verify_http_lifecycle.py

# HTTP-only golden path against an already running clean demo:
.venv/bin/python scripts/smoke_http.py --base-url http://127.0.0.1:8000

# After restarting against that same DB:
.venv/bin/python scripts/smoke_http.py --mode verify

# Stop server first; this confirmation deliberately destroys generated demo state:
DEMO_MODE=true .venv/bin/mock-enterprise reset-demo --yes
DEMO_MODE=true .venv/bin/mock-enterprise serve --port 8000
.venv/bin/python scripts/smoke_http.py --mode baseline

# Export actual implemented OpenAPI, no business mutation:
DEMO_MODE=true .venv/bin/python scripts/export_openapi.py
```

Initialization refuses an existing file. Reset requires explicit `--yes` or interactive
`RESET`; it rejects non-demo/unknown-schema DBs, symlinks, hard links, out-of-storage
targets and a running server's lifecycle lock. Reset is one atomic reload, and a
failed reload restores the prior transaction. No public reset/failure-injection route
exists. Tests use `.cache/pytest/`; real-server verification uses isolated
`.demo/verify-<run-id>.sqlite3` files, not the developer's default DB.

## Actual commands and results

| Command/check run | Actual result |
|---|---|
| Project-local `uv sync --python 3.12` with UV_CACHE_DIR / UV_PYTHON_INSTALL_DIR | Installed Python and dependencies locally; final resolved versions above |
| Final project-local `uv sync --locked --python 3.12` | Exit 0: resolved 22 packages and audited 21 installed packages; lockfile is current |
| Initial read/calculation and workflow tests | 31 read/calculation tests passed; initial write failure exposed receipt SQL placeholder mismatch, corrected; combined rerun 35 passed |
| `pytest tests/test_authority_staleness.py -q` | 97 passed in 9.21s |
| `pytest tests/test_recovery_persistence.py -q` | Initial 23 passed in 2.08s; audit-failure/lock tests added afterward |
| `pytest tests/test_interface_edges.py -q` | Initial 12 passed in 6.04s, including real HTTP lifecycle; later interface regressions added |
| `TMPDIR="$PWD/.cache/tmp" .venv/bin/pytest -q` | Final **172 passed in 25.52s**, no failures/skips |
| `.venv/bin/python scripts/verify_http_lifecycle.py` | Standalone real HTTP golden path, actual process restart, then two deterministic resets passed; also rerun by full pytest suite |
| `.venv/bin/python scripts/validate_scenario.py` | PASS: 42 records, 110 references, six documents, three insufficient results, nine computed option combinations, six rejected in-memory corruption probes |
| `DEMO_MODE=true .venv/bin/python scripts/export_openapi.py` | Exported `docs/openapi.json` from implemented app |
| `DEMO_MODE=true .venv/bin/mock-enterprise serve --port 8000` | Uvicorn started and reported application ready on loopback |
| Inline HTTPX requests to port 8000 | Health/docs/schema and representative GETs across all five domains returned 200; original seed state confirmed; exported schema equaled live OpenAPI |
| Final local Markdown/link checks and repeated HTTP reads after the last restart | Exit 0: links resolve, fences balance, all five domains respond, live/exported OpenAPI match and default demo remains in original seed state |

Dependency setup initially encountered missing-package build detection during
scaffolding and upstream TestClient deprecations in newer dependency combinations.
The package target and compatible ranges were corrected. Warnings remain errors
in pytest. Test assertions and business requirements were not weakened to pass.

The final review also corrected audit attribution so denied attempts do not invent
IDs for uncreated plans/jobs, and limited ERP's rate-list endpoint to approved rates
effective at the fixed scenario time. Their regression tests are included above.

## Real HTTP proof

The script explicitly prints:

```text
SCRIPTED MOCK-SYSTEM INTEGRATION TEST — NO AI INFERENCE; ENGINEER IDENTITY IS SIMULATED.
```

The standalone harness starts actual Uvicorn processes on a free loopback port. It
uses the HTTP smoke script for every business read, mutation and assertion. Only
process start/stop and local init/reset use the CLI. It proves:

1. Reads work across Engineering, Validation, Manufacturing, ERP and Planner.
2. Automation self-approval returns 403 `FORBIDDEN_ROLE`; a nonexistent approval
   cannot schedule and returns scoped 404 `NOT_FOUND`.
3. A simulated engineer records the exact decision; automation persists one job,
   one reservation, one planner link and one task.
4. GETs read back the actual records. Forecast is Nov 18 20:00Z and explicitly
   conditional; baseline is Nov 19 18:00Z; customer commitment remains Nov 23 18:00Z.
5. Same-key job/link retries return exact original 201 bodies and replay headers.
   New-key duplicates return 409 `ACTION_ALREADY_RECORDED`.
6. Stopping and starting a new server against the same DB preserves those exact
   records. Subsequent reset/serve cycles restore original HTTP baseline twice.

All three seeded results stay unchanged and insufficient for the target obligation.
No physical test was executed and no actual human review occurred. The latest
retained lifecycle report/receipt paths are listed below; those verification servers
have been stopped and their isolated databases are reset.

Latest report: [.cache/http-lifecycle/fc3def03f3f94ce9974ad0e1b28d0f89/report.json](../.cache/http-lifecycle/fc3def03f3f94ce9974ad0e1b28d0f89/report.json).
HTTP receipt: [.cache/http-lifecycle/fc3def03f3f94ce9974ad0e1b28d0f89/receipt.json](../.cache/http-lifecycle/fc3def03f3f94ce9974ad0e1b28d0f89/receipt.json).

| Persisted artifact before reset | Verified ID |
|---|---|
| Plan | `plan-b50dcac9e7a544ed80b69a3b104ca133` |
| Approved decision | `decision-c106af6eb6794fa58784363b25a96177` |
| Job | `job-594e8d6b5e4b4c56999653fb8ef8a883` |
| Reservation | `reservation-52a9ea6982204128b6f17d9d9a64c0a3` |
| Planner link | `link-483dd6b17fd046948e5b4ba654a76bbb` |
| Task | `task-dcc80375b9ba459889a4868686731996` |

## Implemented endpoint inventory

All paths below use `/api/v1`. Query IDs are required where shown. Responses and
request models are in the [exported OpenAPI](openapi.json); contract semantics are
in [API_CONTRACT.md](API_CONTRACT.md).

| Domain | Method and path |
|---|---|
| Engineering | GET `/engineering/changes/{change_id}` |
| Engineering | GET `/engineering/requirements/{requirement_revision_id}` |
| Engineering | GET `/engineering/configurations/{configuration_id}` |
| Engineering | GET `/engineering/workloads/{workload_profile_id}` |
| Engineering | GET `/engineering/procedures/{procedure_id}` |
| Engineering | GET `/engineering/policies/{policy_id}` |
| Engineering | GET `/engineering/acceptance-criteria/{criteria_id}` |
| Engineering | GET `/engineering/documents?program_id=...` |
| Engineering | GET `/engineering/documents/{document_id}` |
| Engineering | POST `/engineering/changes/{change_id}/plans` |
| Engineering | GET `/engineering/plans/{plan_id}` |
| Engineering | POST `/engineering/plans/{plan_id}/decisions` |
| Engineering | GET `/engineering/decisions/{decision_id}` |
| Validation | GET `/validation/coverage?change_id=...` |
| Validation | GET `/validation/options?change_id=...` |
| Validation | GET `/validation/results/{result_id}` |
| Validation | GET `/validation/samples?program_id=...` |
| Validation | POST `/validation/jobs` |
| Validation | GET `/validation/jobs?change_id=...` |
| Validation | GET `/validation/jobs/{job_id}` |
| Manufacturing | GET `/manufacturing/units/{unit_id}` |
| Manufacturing | GET `/manufacturing/lots/{lot_id}` |
| ERP | GET `/erp/orders/{order_id}` |
| ERP | GET `/erp/cost-rates?program_id=...` |
| Planner | GET `/programs/{program_id}` |
| Planner | GET `/programs/{program_id}/milestones/{milestone_id}` |
| Planner | POST `/programs/{program_id}/implementation-links` |
| Planner | GET `/programs/{program_id}/implementation-links?change_id=...` |
| Shared audit | GET `/audit/events?change_id=...` |

Additional public local routes: `/health`, `/docs`, `/openapi.json`. No frontend
project or generic SQL/filesystem/CRUD interface exists.

Example read (public synthetic selector):

```sh
curl -sS 'http://127.0.0.1:8000/api/v1/validation/options?change_id=CR-017' \
  -H 'Authorization: Bearer demo-reader-local-only'
```

Example mutation body shapes (replace IDs/digest with actual persisted values;
these example identifiers do not authorize anything):

```json
{"decision":"approve","expected_plan_version":1,"expected_plan_digest":"<digest from GET plan>","reason":"Simulated engineering decision"}
```

```json
{"plan_id":"<persisted plan ID>","approval_id":"<persisted approved decision ID>"}
```

```json
{"plan_id":"<persisted plan ID>","approval_id":"<persisted approved decision ID>","job_id":"<persisted job ID>","expected_milestone_record_version":1}
```

Every POST requires an Idempotency-Key and authorized role selector. For a complete
valid plan request, retrieve `/validation/options`, copy the selected option's
source object/IDs, and supply the structured assessment defined in OpenAPI. The
executable `smoke_http.py` demonstrates this without fixture/DB access.

## Implementation choices reconciled with the plan

The original plan was deliberately detailed; the build uses a smaller equivalent
layout while preserving business rules:

- Each of the five domains has one explicit router/handler module. Shared schemas,
  snapshots, storage, projections and transaction/audit helpers avoid tiny forwarding
  files. Manufacturing and ERP have no mutation handler.
- `db.py` generates fixed per-entity typed SQL columns/FKs/indexes from the Pydantic
  registry. There is no generic record-blob table or generic HTTP CRUD framework.
- Small collections (supported IDs, workload bins, observed bin minutes, milestone
  dependencies) are validated JSON columns instead of separate child tables.
  Scalar relationships use deferred scoped SQL foreign keys; list relationships
  are validated at import and by the relevant domain handler. Immutable snapshots
  and structured assessments are validated JSON. This reduces schema boilerplate
  for the bounded demo, without allowing unrestricted writes.
- One transaction per domain action writes that domain's allowlisted tables plus
  audit/receipt infrastructure. SQLite authorizers enforce this, and tests attempt
  forbidden cross-domain writes. Read projections join persisted outputs without
  writing status into another domain.
- Response option times/slack are grouped under `timing`; this object is null for
  resource-ineligible combinations. Eligibility and deadline flags remain separate.
- A unique plan ID always has immutable version 1; a revision receives a new ID and
  its own version 1, linked through optional `supersedes_plan_id`. No prior approval
  is transferred. This matches the planning clarification, rather than adding edits.

The validated fixture values and six business documents were not changed during
implementation. The runtime augments imports with typed defaults, explicit program
scope and captured result configuration/workload/criteria snapshots. Developer test
expectations remain outside runtime imports and retrieval.

## Files created or updated

Created:

- `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`.
- `src/mock_enterprise/`: app, CLI/settings, typed schemas/DB/seed, identity and core
  helpers, approvals/snapshots, read projections and mutation/audit infrastructure.
- `src/mock_enterprise/domains/`: Engineering, Validation, Manufacturing, ERP,
  Planner and deterministic validation-rule modules.
- `tests/conftest.py`, `test_reads_calculations.py`, `test_workflow.py`,
  `test_authority_staleness.py`, `test_recovery_persistence.py`,
  `test_interface_edges.py`.
- `scripts/smoke_http.py`, `scripts/verify_http_lifecycle.py`,
  `scripts/export_openapi.py`, `docs/openapi.json`, `docs/BUILD_HANDOFF.md`.

Updated: `README.md`, the implementation reconciliation in
`docs/IMPLEMENTATION_PLAN.md`, and response-shape notes in `docs/API_CONTRACT.md`.
Generated, ignored local artifacts: `.venv/`, `.tools/python/`, `.cache/`, `.demo/`.
AGENTS.md, prompts and validated fixture business inputs were preserved.
No Git repository existed, so no commit/diff/branch operation was performed.

## Remaining limitations and future adapter notes

There are no unresolved build failures or skipped required checks. The known
modeling boundaries are intentional:

- Public mock selectors prove role enforcement only; they are not production auth
  or evidence that a real human signed. One local database and process do not model
  distributed isolation. Someone controlling the local files can tamper with them.
- The fixed scenario clock, 24/7 review calendar and same-campus setup assumption
  are synthetic. Numeric hardware acceptance thresholds and test execution are
  unmodeled. A scheduled job does not establish performance or customer acceptance.
- A sample remains reserved for its one outstanding job; no cancellation, release,
  rescheduling or multi-job sample calendar is implemented. A later critical source
  change after booking preserves the job and may require manual reassessment.
- Audit is immutable within a demo generation; explicitly confirmed local reset
  destroys generated state, including audit and idempotency receipts. This is not
  tamper-evident archival storage.
- Standard Swagger assets may need browser internet access. The API business path
  and automated verification do not call enterprise or AI services.
- Verification ran locally on macOS arm64 / Python 3.12.10. Production deployment,
  external integrations, load benchmarking and cross-platform lock behavior were
  not attempted or claimed.

Future adapters must use documented HTTP reads/writes, retrieve the exact source
versions, present an actual approval boundary outside automation's role, and verify
persisted outputs. They must preserve partial successes and retry only missing
work. Do not expose developer specifications/tests/seed JSON as business retrieval,
pass the engineer selector to an automation tool, or infer passing tests from
scheduling. Agent and frontend development remain separate phases.
