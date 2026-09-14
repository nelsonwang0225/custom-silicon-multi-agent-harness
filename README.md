# Custom Silicon Multi-Agent Harness

STRATOS SILICON is a local end-to-end demo of agent-assisted semiconductor program
management. It combines five fictional enterprise source systems, scoped HTTP and
MCP interfaces, a Coordinator with four specialist roles, governed human approval
boundaries, and a React control plane. All companies, programs, records and results
are synthetic.

The current demo supports four connected cases: CR-017 requirement change,
CR-019 standard validation intake, QE-004 quality recovery and DR-009 delivery
readiness. Those cases can use the configured GPT-6 Astra runtime. QE-011 is a
deterministic two-minute full-team opening that begins after an eight-second local
Manufacturing event; it makes no model call. Source ownership, exact approvals and
independent readback remain authoritative in both modes.

## Quick start — offline and no API key

This path lets anyone clone and run the complete UI with deterministic agent
doubles. It exercises the real local source APIs and MCP boundary, but it is
scripted integration behavior, not live AI.

Prerequisites:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Node.js 22 or newer with npm
- A modern desktop browser

```sh
git clone https://github.com/nelsonwang0225/custom-silicon-multi-agent-harness.git
cd custom-silicon-multi-agent-harness

uv sync --locked --python 3.12
uv sync --project mcp_server --locked --python 3.12
uv sync --project coordinator --locked --python 3.12
npm --prefix mock_apps_ui ci
```

Start the deterministic source/MCP/control-host stack in one terminal:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve \
  --root .cache/phase09-3/public-preview \
  --port 18082 --source-port 18000 --mcp-port 19000 \
  --ui-origin http://127.0.0.1:5188
```

Start the frontend in a second terminal:

```sh
MOCK_API_URL=http://127.0.0.1:18000 \
CONTROL_HOST_URL=http://127.0.0.1:18082 \
npm --prefix mock_apps_ui run dev -- --port 5188
```

Open [http://127.0.0.1:5188/control/overview](http://127.0.0.1:5188/control/overview).
The first launch initializes isolated state under `.cache/phase09-3/public-preview`;
later launches preserve it. Stop both processes with Ctrl-C.

## Full live demo — optional OpenAI API access

The owned demo harness uses `gpt-6-astra` for the four main investigations and
Concierge. You need an OpenAI API key with access to that model; availability,
rate limits and billing depend on your API account. See the
[official GPT-6 Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra).

Create an uncommitted `.env.local` containing `OPENAI_API_KEY`, then restrict it
to the current user. Do not shell-source, print or commit the file.

```dotenv
OPENAI_API_KEY=replace_with_your_key
```

```sh
chmod 600 .env.local

# First use only: create the dedicated .demo/interview database.
./scripts/demo init --yes
./scripts/demo start
./scripts/demo prepare --yes
./scripts/demo check
```

Open [http://127.0.0.1:5188/control/overview](http://127.0.0.1:5188/control/overview).
Initialization, startup, preparation and readiness checks do not call the model.
Only an explicit investigation or Concierge send can incur API usage. State
persists across restarts; use `./scripts/demo stop` to stop only owned processes.
For custom ports, reset behavior, personas, walkthroughs and troubleshooting, use
the authoritative [demo runbook](docs/DEMO_RUNBOOK.md).

The [master reset](docs/PHASE10_MASTER_RESET.md) restores all four main cases and
source systems, then restarts the deterministic QE-011 opening. The
[full-team opening](docs/PHASE10_MINUTE_FULL_TEAM_OPENING.md) lasts at least two
minutes and shows Coordinator triage, four parallel specialist assessments,
reconciliation and synthesis. Historical sections below describe earlier slices
and should not be read as the current launch procedure.

Nine fictional customers, eleven custom-semiconductor programs and five interactive
source-system applications. HELIOS AI / CR-017 remains the unchanged manual
assessment → exact approval → scheduling → Planner walkthrough.

The current [data enrichment handoff](docs/DATA_ENRICHMENT_HANDOFF.md) describes
counts, generator provenance, checks and the [expanded preview](http://127.0.0.1:5183/).
Fresh initialization creates the versioned portfolio; existing files are never
silently reseeded or renamed. The older preview sections below document earlier
work and do not promise that those services are still running.


**Working local APIs and five interactive source-system applications.** Five logical systems share one FastAPI process
and a persistent SQLite database. All company, customer, workload, cost and capacity
records are fictional. Scheduling creates work; it does not execute tests, produce
passing results, qualify hardware or establish customer acceptance.

The React/TypeScript/Vite frontend in `mock_apps_ui/` uses these same HTTP APIs.
The business application has no AI runtime, OpenAI/Agents SDK dependency, API key
requirement or real enterprise integration. An optional, isolated
[OpenAI connectivity check](runtime_checks/README.md) uses a separate dependency
group and the project's private `.env.local`; it does not change the business APIs
or frontend.

Phase 04 Step 4 adds a separate [read-only enterprise API client](docs/ENTERPRISE_API_CLIENT.md)
that accesses all five systems through HTTP. Step 5 exposes it through a separate
[local Streamable HTTP MCP service](docs/MCP_SERVER_HANDOFF.md) with 25 scoped read tools.
Neither layer uses the OpenAI runtime. Step 6 adds a separate
[ProgramInvestigator agent](docs/PROGRAM_INVESTIGATOR_HANDOFF.md) using GPT-6 Astra
and the Agents SDK, with business access exclusively through those MCP read tools.
Its dependencies and paid CLI entry point live separately from the business application.

Phase 05 adds the separate [coordinator-led multi-agent harness](docs/MULTI_AGENT_HARNESS_HANDOFF.md)
under `src/program_coordinator/`, with its own locked `coordinator/` environment.
It uses five GPT-6 Astra agent roles, typed shared case state, narrow MCP tool sets,
bounded specialist collaboration, deterministic policy checks and read-only final
decision packages. The single-agent ProgramInvestigator remains intact. Its agent
and specialist tools remain read-only; model routing and a control-plane UI are excluded.

The [workflow compatibility update](docs/WORKFLOW_COMPATIBILITY_HANDOFF.md) adds a
host-only registry, a shared invocation service, persistent case/run/activity links,
and typed proposal/decision adapters around the existing source contracts. Only
requirement-change analysis is executable. Yield recovery and delivery readiness
are illustrative catalog entries. The existing manual source-app approval/scheduling
workflow is preserved.

[Phase 06 — Human Approval & Execution](docs/HUMAN_APPROVAL_EXECUTION_HANDOFF.md)
adds the CR-017 host workflow: exact proposal → trusted demo engineer review →
persisted resume → approved Validation scheduling → approved Planner linking →
independent readback. Agents keep their existing read tools. Execution and
verification are separate from the completed investigation; the case stays in
validation, with test results and customer acceptance pending. Use the existing
Coordinator CLI with `--phase06` or `--prepare-execution`; the handoff documents
commands, identity limitations, failure recovery and offline verification.

[Phase 07 — Evals & Reliability](docs/EVALS_RELIABILITY_HANDOFF.md) adds 40
developer-only behavioral cases, deterministic graders, real Phase 06 recovery
probes, JSON/Markdown scorecards and optional live CR-017/semantic evaluation.
The default suite makes no paid model calls. An offline passing score measures
fixture contracts and reliability; it does not establish live-model reasoning
quality. Source permissions, agent prompts and the execution boundary are unchanged.

```sh
# From repository root; offline, with isolated source/metadata storage.
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07
```

## Phase 08.3 — Workflows & Automations

[Open workflows](http://127.0.0.1:5189/control/workflows) to discover capabilities,
manually launch supported CR-017 investigation, inspect real run history and save
future trigger configurations. Schedules, events and conditions are previews only;
no background execution is enabled. The [08.3 handoff](docs/PHASE08_3_WORKFLOWS_HANDOFF.md)
documents authority, persistence, APIs, tests and limitations. Existing CR-017
approvals, execution and downstream validation remain intact. No paid models were
automatically run. The next slice is 08.4 interactive scenario simulations.

## Phase 08.2.1 downstream validation

[Open CR-017](http://127.0.0.1:5189/control/programs/PRG-A17/cases/CR-017) to continue
from the existing verified job. The explicit **Publish synthetic result** action
lives in Validation Lab under a separate demo lab identity. Return to the case,
explicitly reassess with the existing agents, then review the exact evidence as
Engineering approver. Validation completion retains pending customer acceptance.
Agents do not physically perform the test. The configured paid reassessment is
manual; no paid calls were run for this implementation.

See the [08.2.1 handoff](docs/PHASE08_2_1_DOWNSTREAM_HANDOFF.md) for source ownership,
review authority, preserved demo state, additive migration, manual steps, tests and
limitations. Earlier phase descriptions below remain historical context.

## Phase 08.1 control-plane shell

Latest visual update: [darker blue and minimalist Overview](docs/PHASE08_1_MINIMAL_DESIGN_HANDOFF.md), with design research, screenshots, verification and local start commands. [Open preview](http://127.0.0.1:5188/control/overview).

The additive `/control/overview` route provides Overview → Program → Case → evidence,
plus useful capability previews and Stratos Concierge with optional browser dictation into an editable draft. Replies/actions remain preview-only. It reads the
existing source APIs as the fixed mock portfolio reader. It does not invoke agents,
create proposals, approve or execute work. All five original application routes
remain available at `/`, `/engineering`, `/validation`, `/manufacturing`, `/erp`
and `/programs`.

Use the [current Phase 08.1 Overview handoff](docs/PHASE08_1_OVERVIEW_HANDOFF.md) for the gradient visual system, global search, demo profiles, source alerts, dictation limits and verification. See the [initial handoff](docs/PHASE08_1_HANDOFF.md) for the isolated local
preview, exact launch commands, screenshots, verification and the preservation
exception for one automatic denied-read audit on the pre-existing server. The
[shared product requirements](docs/PHASE08_CONTROL_PLANE_REQUIREMENTS.md) and
[six-slice plan](docs/PHASE08_IMPLEMENTATION_PLAN.md) govern later work.
Stop for visual review before implementing 08.2.

## Standalone source API setup

Use this section when you want only the five mock source systems and their public
business APIs. For the integrated control plane, follow Quick start above.

Run these commands from this project directory. Python, environment and caches stay
inside the project. `uv` must already be available; the development environment used
uv 0.7.6. The committed lockfile records the tested dependency versions.

```sh
mkdir -p .cache/tmp .cache/uv .tools/python
export UV_CACHE_DIR="$PWD/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$PWD/.tools/python"
export TMPDIR="$PWD/.cache/tmp"
uv sync --locked --python 3.12
DEMO_MODE=true uv run --locked mock-enterprise init-demo
```

Initialization creates `.demo/enterprise.sqlite3` and refuses to overwrite an
existing file. If it already exists, use it as-is or use the guarded reset below.
Startup never reseeds or overwrites persisted business state.

## Run and API documentation

```sh
DEMO_MODE=true .venv/bin/mock-enterprise serve --port 8000
```

The CLI binds only to `127.0.0.1`, uses one worker and disables HTTP access logging.
Stop it with Ctrl-C. An optional `DEMO_DB` must point inside this project's `.demo/`
directory. `DEMO_MODE=true` is required for initialization, serving and reset.

- [Interactive API docs](http://127.0.0.1:8000/docs)
- [Live OpenAPI schema](http://127.0.0.1:8000/openapi.json)
- [Readiness](http://127.0.0.1:8000/health)
- [Exported schema](docs/openapi.json)

The docs UI uses FastAPI's standard Swagger assets. The business APIs require only
localhost and the local database; no external business service is called.

## Deliberately fake role selectors

Business requests use `Authorization: Bearer <selector>`. These public values are
**mock role-test selectors, not production authentication or proof of human identity**:

| Selector | Allowed actions |
|---|---|
| `demo-reader-local-only` | Scoped business reads and audit |
| `demo-automation-local-only` | Reads, draft plans, approved lab scheduling, approved planner linking |
| `demo-engineer-local-only` | Reads and exact-plan approve/reject decisions within policy |

The original three selectors remain scoped server-side to CUST-FML01 / PRG-A17.
The UIs use `demo-portfolio-reader-local-only`,
`demo-portfolio-automation-local-only`, and `demo-portfolio-engineer-local-only`,
with an explicit server-owned allowlist of eleven customer/program pairs.
Query filters cannot expand that list. Each write is narrowed to its target
program before validating references and recording a decision or reservation. Automation cannot approve,
edit engineering criteria, author results, release manufacturing holds or change
customer commitments. Engineer is not an unrestricted administrator. A future
agent adapter must never receive the engineer selector.

Example read (the value below is intentionally public synthetic test data):

```sh
curl -sS 'http://127.0.0.1:8000/api/v1/validation/options?change_id=CR-017' \
  -H 'Authorization: Bearer demo-reader-local-only'
```

Read the associated change:

```sh
curl -sS 'http://127.0.0.1:8000/api/v1/engineering/changes/CR-017' \
  -H 'Authorization: Bearer demo-reader-local-only'
```

## Integration boundary and workflow

The service implements 40 business method/path pairs: 34 GETs and six POSTs,
plus health and generated documentation. All business paths start with `/api/v1`.

| Domain | Major paths | Writes |
|---|---|---|
| Engineering Hub | `/engineering/changes/{id}`, `/requirements/{id}`, `/configurations/{id}`, `/workloads/{id}`, `/procedures/{id}`, `/policies/{id}`, `/acceptance-criteria/{id}`, `/documents`, `/plans/{id}`, `/decisions/{id}` (all under `/engineering`) | Create change plan; record plan decision |
| Validation Lab | `/validation/coverage`, `/validation/options`, `/validation/results/{id}`, `/validation/samples`, `/validation/jobs` | Schedule approved job and reserve resources |
| Manufacturing Portal | `/manufacturing/units/{id}`, `/manufacturing/lots/{id}` | None |
| Commercial ERP | `/erp/orders/{id}`, `/erp/cost-rates` | None |
| Program Planner | `/programs/{id}`, `/programs/{id}/milestones/{id}`, `/programs/{id}/implementation-links` | Link job/task and update conditional internal forecast |
| Audit | `/audit/events?change_id=CR-017` | No public writes |

Use the [full API contract](docs/API_CONTRACT.md) and generated schema for exact
paths, input models, stable error codes and operation IDs.

1. Read the change and exact requirement revisions; retrieve coverage and options.
   Options compute all slot/sample combinations, embed lab/slot metadata, and return
   the complete `expected_source_versions` object. They do not supply a canned winner.
2. POST `/engineering/changes/CR-017/plans` as automation, providing selected IDs,
   structured assessment and the returned source versions. Cost, timing, actions,
   source snapshot and digest are computed and persisted by the server.
3. POST `/engineering/plans/{plan_id}/decisions` as the simulated engineer with
   `decision`, `expected_plan_version`, `expected_plan_digest`, and `reason`.
4. POST `/validation/jobs` as automation with `{plan_id, approval_id}`. The approval
   must be an actual matching approved decision. One job and one reservation bind
   the exact sample/slot; no result is generated.
5. POST `/programs/PRG-A17/implementation-links` with `{plan_id, approval_id, job_id,
   expected_milestone_record_version}`. The server derives the forecast and creates
   one task/dependency atomically, preserving baseline and ERP commitment.
6. Read the plan, decision, job/reservation, link/task, milestone and audit back.

Every POST requires `Idempotency-Key`; optional `X-Correlation-ID` is returned with
a generated request ID. Exact successful retries return the original status/body
and `Idempotency-Replayed: true`. Changed content under that key is 409. A new-key
repeat of the same completed decision/job/link is 409 `ACTION_ALREADY_RECORDED`
with the existing resource ID; recover through GET.

Plans are immutable version 1 under unique IDs; revisions create new IDs and may
reference `supersedes_plan_id`. Old approval never authorizes the revised content.
Critical content versions differ from workflow/availability/forecast versions.
The plan's own approval and reservation do not invalidate its next action. If
Planner fails after booking, the job persists and execution state reads
`lab_scheduled_pending_planner`; retry only the missing planner action.

## Tests and real HTTP verification

```sh
# Independent static fixture validation; developer-only, not a runtime module.
.venv/bin/python scripts/validate_scenario.py

# Entire automated suite, including a real Uvicorn/HTTP restart/reset workflow.
TMPDIR="$PWD/.cache/tmp" .venv/bin/pytest -q

# Standalone lifecycle proof: creates an isolated .demo/verify-*.sqlite3,
# starts/stops Uvicorn, runs HTTP mutations, restarts, then resets twice.
TMPDIR="$PWD/.cache/tmp" .venv/bin/python scripts/verify_http_lifecycle.py

# Against an already running server in clean seed state:
.venv/bin/python scripts/smoke_http.py --base-url http://127.0.0.1:8000

# After stopping and restarting that server against the same database:
.venv/bin/python scripts/smoke_http.py --mode verify

# Export schema from the implemented app (requires initialized local demo DB):
DEMO_MODE=true .venv/bin/python scripts/export_openapi.py
```

The smoke script prints:

```text
SCRIPTED MOCK-SYSTEM INTEGRATION TEST — NO AI INFERENCE; ENGINEER IDENTITY IS SIMULATED.
```

It uses HTTPX for all business operations, rejects non-loopback URLs, exits nonzero
on mismatches, and reports plan/approval/job/reservation/link/task IDs. It selects
from computed feasible options and deliberately emulates the engineer role for
integration testing. This is not an AI run or an actual human approval.

The lifecycle harness stores HTTP receipts, reports and sanitized server logs under
`.cache/http-lifecycle/<run-id>/`, and leaves its isolated database reset. Pytest
uses `.cache/pytest/` databases, never the developer's active demo DB. Failure hooks
exist only in test code; there is no public chaos/admin endpoint.

## Guarded deterministic reset

Stop the service first, then explicitly confirm reset:

```sh
DEMO_MODE=true .venv/bin/mock-enterprise reset-demo --yes
DEMO_MODE=true .venv/bin/mock-enterprise serve --port 8000
# Optional HTTP check after a smoke workflow was previously recorded:
.venv/bin/python scripts/smoke_http.py --mode baseline
```

Without `--yes`, reset requires an interactive `RESET` confirmation. It refuses
unmarked/unknown-schema databases, symlinks, hard links, targets outside configured
project demo storage, and databases locked by a running service. Reset is atomic;
a failed reload rolls back. It restores the deterministic initial portfolio, removes subsequent workflow
writes/receipts, and restores the authored initial history. CR-017 returns to
zero plans, approvals, jobs, reservations and Planner links. Surrounding programs
retain their deterministic initial operational records.
Audit is append-only within each demo generation; reset is the deliberate local
exception. There is no public reset endpoint and no arbitrary fixture/path API.

## Scenario and limitations

The fixed scenario time is 2026-11-16 09:00 UTC. Review uses elapsed 24/7 time and
same-campus movement is included in setup. The priority option costs 180,000 cents
and finishes review 22 hours before the deadline; standard costs zero and finishes
28 hours late. These are calculated from seeded inputs, not performance claims.
The workload suite is 480 minutes total, including 160 minutes per required bin.

This demo has public mock selectors, one SQLite file and a conservative one-outstanding-
job reservation per sample. No cancellation/release or numerical
acceptance engine, requirement promotion or customer acceptance workflow is exposed.
A critical source change after booking preserves that booking and may require manual
reassessment. It does not silently cancel, reapprove or change commitments.

Six explicitly allowlisted authored documents and thirty controlled generated
business documents are imported into the DB and served by ID. Developer specifications, fixture JSON, prompts, scripts and
tests are excluded from business retrieval. Existing DB contents survive fixture edits;
use the guarded local reset to load fixture changes.

See [BUILD_HANDOFF.md](docs/BUILD_HANDOFF.md) for actual commands/results, resolved
issues, implementation choices and remaining limits. The original
[implementation plan](docs/IMPLEMENTATION_PLAN.md), [scenario](docs/SCENARIO.md),
[acceptance requirements](docs/ACCEPTANCE_TESTS.md) and [phase prompts](prompts/02_BUILD.md)
remain available as historical foundation specifications. The five source-system UI
phase is authorized and implemented; the agent/control-plane phase remains out of scope.

## Five source-system applications

Node.js 22+ is required (tested with Node 24.13.1). From the project root:

```sh
# Install frontend dependencies into this project only.
npm --prefix mock_apps_ui ci --cache "$PWD/.cache/npm"

# Terminal 1: use the existing working database; do not reinitialize or reset it.
DEMO_MODE=true .venv/bin/mock-enterprise serve --port 8000

# Terminal 2: loopback frontend, /api proxied to port 8000.
npm --prefix mock_apps_ui run dev
```

Stop each service with Ctrl-C in its own terminal. Do not stop unrelated processes.
Vite uses a strict port and exits on conflicts. To use an alternate backend port,
start the backend with `--port 8001` and run
`MOCK_API_URL=http://127.0.0.1:8001 npm --prefix mock_apps_ui run dev`.
An alternate frontend port can be passed as `-- --port 5175`. Both remain loopback.
The default preview uses the same `.demo/enterprise.sqlite3`; no second business
store, fixture import or browser-local business database exists.

| Application | Preview URL |
|---|---|
| Launcher | [Applications](http://127.0.0.1:5173/) |
| Engineering Hub | [Change requests](http://127.0.0.1:5173/engineering) |
| Validation Lab | [Evidence and coverage](http://127.0.0.1:5173/validation) |
| Manufacturing Portal | [Unit inventory](http://127.0.0.1:5173/manufacturing) |
| Commercial ERP | [Customer orders](http://127.0.0.1:5173/erp) |
| Program Planner | [Program workspaces](http://127.0.0.1:5173/programs) |

The app switcher navigates between systems; “Open app in new tab” opens the current
record directly. Refresh, tab focus/visibility and successful writes re-fetch API
state. A lightweight tab notification requests re-fetching after UI mutations; it
carries no business records. Direct API clients can make the same changes, which
appear on focus or Refresh. Record update times use scenario UTC; last API refresh
and audit recording times use separately labeled wall-clock UTC.

Personas are explicit and tab-scoped (`sessionStorage`), defaulting to viewer:

| UI persona | Existing API role | Mutations |
|---|---|---|
| Read-only viewer | `reader` | None |
| Program operator | `automation` | Draft assessment/plan; book approved job; link approved scheduled job |
| Engineering approver | `engineer` | Approve/reject exact immutable plan within policy |

These are public local demo selectors, not production authentication or verified
human identities. The UI never switches identities to make a request succeed.
Manufacturing and ERP remain read-only for all personas. Plan approval does not
promote a requested requirement or accept hardware.

A write stores its exact request and one idempotency key as tab-scoped retry metadata.
If the reply is lost, use **Retry same request**, including after a page reload.
The UI reads back persisted records before reporting success. Existing jobs/links
are recovered through GET after duplicate conflicts. A definitive denial permits
explicit revision after refresh; an unresolved transport failure retains its original
request. Forms and retry metadata are the only stored state besides the persona;
retrieved business records are never saved to localStorage or a browser database.

### UI checks

```sh
npm --prefix mock_apps_ui run typecheck
npm --prefix mock_apps_ui run build

# Generate client schema after an intentional backend schema change.
DEMO_MODE=true .venv/bin/python scripts/export_openapi.py
npm --prefix mock_apps_ui run schema

# Install the browser locally, then run real HTTP/browser integration tests.
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" \
  npm --prefix mock_apps_ui exec -- playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" \
  npm --prefix mock_apps_ui run test:e2e
```

Playwright starts its own backend on **18000** and frontend on **5174**, refuses to
reuse existing servers, initializes a unique `.demo/ui-e2e-*.sqlite3` test database,
and stops only its own services. Test databases are retained for inspection and
never replace or reset the working DB. All successful workflow responses cross real
HTTP; a test-only interception deliberately drops one already-committed response to
prove retry recovery. This is scripted integration testing with simulated personas,
not an AI run or an actual human approval. Chromium screenshots are developer
artifacts under `docs/ui_screenshots/`, outside business retrieval.

See [MOCK_APPS_UI_HANDOFF.md](docs/MOCK_APPS_UI_HANDOFF.md) for verified results,
the screen/endpoint map, click-by-click workflow, screenshots and limitations.

The launcher now summarizes the customer change, deadline, current decision and
execution state, and the next responsible role. Scheduled work links directly to
its job and Planner record. Assessments support multiple facts/citations with
source previews; plan review supports immutable revisions, scope comparison and
expanded audit details. Each revision requires its own engineering decision.

The follow-up handoff lists a separate clean preview at **5181 / API 18011** and
the preserved scheduled preview at **5180 / API 18010**. Both use isolated demo
files. New files include descriptive Manufacturing hold and ERP rate context;
older files display missing context explicitly and are never silently reseeded.

## Phase 04 — local read-only MCP server

The enterprise client is now exposed through **25 scoped read-only MCP tools**
using Streamable HTTP at `http://127.0.0.1:9000/mcp`. The verified local backend
for this service runs separately on port **9001**; existing UI previews are unchanged.
The MCP service uses its own locked Python environment to preserve backend dependencies.
It needs no OpenAI key and makes no model calls.

See [MCP_SERVER_HANDOFF.md](docs/MCP_SERVER_HANDOFF.md) for setup/start/stop commands,
the complete tool mapping, scope/error/correlation behavior and actual verification:
**56 MCP tests + 282 existing regression tests passed**, plus real Streamable HTTP
integration across all five systems with unchanged persisted test state.

## Phase 08.2 — connected CR-017

CR-017 now supports investigation, recorded specialist findings, exact proposal
review, trusted demo approval/rejection, governed execution and independent
source readback. The existing five source apps remain available. Freeform
Concierge and other workflows remain previews.

The configured local demo is **http://127.0.0.1:5189/control/overview** when the
four local processes described in the [08.2 handoff](docs/PHASE08_2_CONNECTED_HANDOFF.md)
are running. It uses a separate source database and host metadata directory.
Opening or refreshing the app never starts a model. An explicit **Run investigation**
click uses the existing configured GPT-6 Astra runtime. No paid calls were run
for implementation verification. See the handoff for exact startup commands,
manual walkthrough, API contracts, tests, screenshots and limitations.

## Phase 08.4A — connected standard change

Use Case 1A is **CR-019**, an approved-profile package update for Helios Atlas.
It shares Requirement Change Analysis with CR-017. Exact approved applicability
permits one Validation Operations intake followed by independent readback; lab
authorization, physical work and acceptance remain downstream. No new human
approval is manufactured for this handoff. The existing CR-017 human-review path
is preserved.

See [the 08.4A handoff](docs/PHASE08_4A_HANDOFF.md) for the scenario, narrow source
contract, policy, recovery behavior, actual verification and optional manual live
command. The MCP catalog now has 26 read tools; the added standard-context read
is exposed only to the three relevant specialists on this route. Automation
triggers and Concierge replies remain previews.

Phase 08.4B adds [connected QE-004 quality recovery](docs/PHASE08_4B_HANDOFF.md):
source-owned signal/material, deterministic comparison and supply math, standard
investigation routing, exact Program Owner recovery review and independently
verified Planner task. The handoff includes isolated no-model and optional manual
live paths. Existing CR-017/CR-019 remain connected; saved event listeners,
Concierge and Delivery Readiness remain previews.


### Phase 10.2 — Visual Agent workspace

The current Overview puts the Coordinator and four specialists on a compact visual stage, with scoped run selection, recorded findings and a separate human/external handoff. See the [workspace contract](docs/PHASE10_2_AGENT_WORKSPACE.md), [handoff](docs/PHASE10_2_HANDOFF.md), [screenshots](docs/screenshots/phase10-2/README.md) and [isolated preview instructions](docs/DEMO_RUNBOOK.md#phase-102-agent-workspace-preview). Phase 10.1 persona capabilities and exact business authority remain in force.
