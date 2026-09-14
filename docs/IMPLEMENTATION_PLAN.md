# Mock-enterprise implementation plan

Readiness: **PASS — ready for the scoped implementation phase.**
Reviewed September 10, 2026 against AGENTS.md, README.md, SCENARIO.md,
API_CONTRACT.md, ACCEPTANCE_TESTS.md, SOURCES.md, all three prompts, seed.json,
and all six business documents. At the planning checkpoint, no service, database, agent, UI or runtime dependency
had been created. This is plan/scenario readiness, not evidence of API correctness.

## 1. Scope and proposed file structure

One loopback-only FastAPI/Uvicorn process, five domain modules, one persistent SQLite
file. Four business mutation endpoints: draft plan, engineer decision, lab booking,
and planner link. Manufacturing/ERP remain read-only. Audit is shared infrastructure,
not a sixth business system. No remote services, AI, OpenAI dependencies, API keys,
Agents SDK, MCP, frontend, Docker, message broker or generalized CRUD framework.

Proposed layout below is a build deliverable; only the planning validator exists now.

```text
AGENTS.md                         # Preserve existing instructions
README.md                         # Working commands and phase boundaries
pyproject.toml                    # Python >=3.12,<3.13; small dependency set
uv.lock / .python-version         # Lock resolved dependencies; Python 3.12
.gitignore                        # Reconcile if one appears before build
src/mock_enterprise/
  __init__.py
  app.py                          # App factory, lifespan, five routers, errors/docs
  config.py                       # Explicit DEMO_MODE, local storage and bind guards
  clock.py                        # Fixed scenario UTC vs actual audit UTC
  auth.py                         # Fixed identity mapping and server-side scope
  db.py / schema.sql              # Connections, schema version, transactions
  seed.py / cli.py                # Validated atomic seed and guarded local reset
  schemas.py / errors.py          # Shared envelopes, refs, strict request types
  idempotency.py / audit.py       # Durable receipts; append-only scoped events
  snapshots.py                    # Typed source registry, canonical digest/freshness
  domains/
    engineering/{__init__,router,schemas,service,repository}.py
    validation/{__init__,router,schemas,service,repository}.py
    validation/coverage.py        # Pure evidence applicability calculations
    validation/options.py         # Pure timing/cost/resource eligibility calculations
    manufacturing/{__init__,router,schemas,service,repository}.py
    erp/{__init__,router,schemas,service,repository}.py
    planner/{__init__,router,schemas,service,repository}.py
scripts/
  validate_scenario.py            # Existing read-only developer validator; no runtime import
  smoke_http.py                   # Future real HTTP scripted integration test
  export_openapi.py               # Future schema export from the implemented app
tests/
  conftest.py                     # Temporary file DBs and scoped mock identities
  test_seed_reads.py / test_coverage.py / test_options.py
  test_plans_decisions.py / test_jobs.py / test_planner.py
  test_scope_denials.py / test_idempotency_concurrency.py
  test_partial_failure.py / test_persistence_reset.py
  test_audit_openapi.py
fixtures/seed.json / fixtures/documents/*.md
docs/SCENARIO.md / docs/API_CONTRACT.md / docs/ACCEPTANCE_TESTS.md
docs/IMPLEMENTATION_PLAN.md        # This planning checkpoint
docs/BUILD_HANDOFF.md              # Future actual build/verification results
docs/openapi.json                 # Future export, never a hand-written substitute
prompts/{01_PLAN,02_BUILD,03_VERIFY}.md
.demo/enterprise.sqlite3          # Future local state, ignored
.venv/ / .cache/uv/ / .tools/python/ # Future project-local tools, ignored
```

Use ordinary Python `sqlite3` and explicit SQL, with Pydantic models at input and
seed boundaries. No ORM or migration framework is needed for one initial schema.
Track a schema version; fail on unsupported existing schemas without overwriting.
FastAPI, Pydantic 2 and Uvicorn are runtime dependencies; pytest and HTTPX are test
dependencies. Resolve compatible versions under Python 3.12 and commit uv.lock
during the build. This plan does not claim a dependency combination has been tested.

The tools' documented mechanics support this choice: [Python sqlite3 transaction
control](https://docs.python.org/3.12/library/sqlite3.html#transaction-control),
[Pydantic configuration](https://docs.pydantic.dev/latest/api/config/),
[FastAPI generated docs](https://fastapi.tiangolo.com/tutorial/first-steps/), and
[uv projects](https://docs.astral.sh/uv/guides/projects/). These sources support
implementation mechanics; all business rules here are synthetic project decisions.

## 2. Database and data model

Use prefixed, domain-owned typed tables, not one table of unvalidated JSON blobs.
IDs are stable TEXT keys; retain existing IDs. Each business entity has ownership,
synthetic provenance, program/customer scope directly or through an enforced FK,
positive `content_version`, and explicit UTC `updated_at`. Use TEXT UTC timestamps
and Python aware datetimes, INTEGER cents/minutes/versions, integer booleans with
CHECK constraints. Reject boolean/fractional/negative monetary input. New IDs can
be UUID-based; fixed scenario time controls calculations, not ID uniqueness.

| Owner | Tables and relationships |
|---|---|
| Engineering | suppliers, customers, configurations, workload_profiles, requirement_revisions, changes, procedures, acceptance_criteria, approval_policies, documents, plans, plan_states, decisions |
| Validation | results, labs, slots, samples, jobs, reservations |
| Manufacturing | lots, units; unit.source_lot_id -> lot; sample.unit_id -> unit |
| ERP | orders, cost_rates; slot.rate_id -> rate; program/change/milestone -> order |
| Planner | programs, milestones, dependencies, implementation_links, tasks |
| Platform | demo_metadata, idempotency_receipts, audit_events |

Use child tables for FK-bearing lists (procedure/lab supported configurations,
lab supported procedures, policy procedures/actions) and workload/result bins.
Map seeded milestone dependencies into typed dependency rows. Derive program
milestone IDs from the milestone relation. JSON is appropriate for immutable
assessment text, typed source snapshots and audit diffs, with schema validation.
Product, revision, model bundle, firmware, runtime, memory, quantization and campus
are shared labels, not new product/catalog services. Validate equality where they
join records. Customer/supplier names resolve from the seeded identity records.

Important record shapes:

- `plans`: ID, scope, change ID, optional supersedes ID, immutable `plan_version=1`,
  normalized assessment, selected target/config/procedure/sample/slot/milestone,
  policy ID, derived cents/currency, setup/execution/review times, deadline/slack,
  actions, full source snapshot, evidence-set digest, plan digest, creator/time.
  The assessment is part of the plan, not another independent workflow/table.
- `plan_states`: plan ID, `draft|approved|rejected`, `record_version`, decision ref.
  `decisions`: immutable approve/reject, plan ID/version/digest, signer identity,
  policy/version, reason, exact scope/actions/resources/cost/source binding, time.
  `approval_id` is the ID of an approved decision; no separate bearer capability.
- `results`: immutable observed fields plus captured configuration, workload and
  criteria IDs/content versions. Exact version matching pins full manifests;
  configuration changes cannot retroactively rewrite a historical run. Store the
  captured configuration/workload fields at import for intelligible read-back.
  This phase has only seed version 1 and no public revision/history authoring.
- `jobs`: immutable plan/approval/digest refs, scope, config/procedure/workload/sample,
  slot/lab/cost, start/setup/execution/end/review times, `status=scheduled`, reservation
  ref, creation time. `reservations`: one row per job with slot AND sample,
  half-open interval, pre/post availability versions and immutable owner provenance.
- `implementation_links`: scope, plan/approval/job/milestone/task refs, derived
  forecast, applied milestone before/after record versions, status `linked`.
  `tasks`: scheduled supplemental-validation task; deadline and job/review dependency.
  `milestones`: immutable baseline/scope content; mutable forecast/status and record
  version. Existing requirement dependency stays unsatisfied after scheduling.
- `documents`: six manifest records plus persisted Markdown content and SHA-256.
  Internal import path is not an API input or a filesystem browsing capability.
- `demo_metadata`: schema/seed version, seed+document digest, scenario clock/ID,
  demo ownership marker and reset generation. Not exposed as unrestricted config.

Database constraints backstop handlers: foreign keys on every connection; composite
program+ID uniqueness/FKs for scoped references; requirements unique by program,
requirement ID and revision; one decision per program/plan; one job per program/plan;
one reservation per job, unique slot and sample while outstanding; one link per
program/plan and per program/job; one task per link; unique dependency kind/target
within its milestone. Enforce same-lab interval overlap rejection under the write
lock. All selected resources must belong to the same program/customer relationship.

For the bounded scheduling phase the sample remains reserved for its one outstanding
job. No release or second nonoverlapping sample booking is modeled. This deliberate
conservative rule avoids inventing execution/cancellation or a reusable scheduler.

Enable FK enforcement before transactions. Use short `BEGIN IMMEDIATE` business
write transactions, parameterized SQL and bounded busy timeout; map lock exhaustion
to 503. Explicit transaction control must be configured for Python 3.12 rather than
relying on driver defaults. Create/close a connection in the synchronous domain
operation; do not share one module-global connection across request threads.
One Uvicorn worker suffices. SQLite serialization is local safety, not distributed
isolation. Cross-domain reads may use the caller's connection for a consistent
check; each mutation writes only its owned business tables plus audit/receipts.

## 3. Endpoint architecture and source discovery

Implement the API_CONTRACT.md inventory as written: 29 business method/path pairs
(25 reads, four POSTs), plus public `/health`, `/docs`, `/openapi.json`.
Five tagged domain routers under `/api/v1`; audit is an authenticated platform
route. All business reads require the fixed server identity and program/customer
scope. Responses use typed single objects or `items` lists, stable operation IDs,
synthetic provenance, explicit versions, and actionable error codes.

| Domain | Read coverage | Mutations |
|---|---|---|
| Engineering Hub | Change, exact requirement/configuration/workload/procedure/policy/criteria, document list/content, plan, decision | POST change plans; POST plan decisions |
| Validation Lab | Computed coverage/options, result, samples, jobs and individual job with reservation details | POST jobs |
| Manufacturing Portal | Unit and source lot, including independent restrictions/refresh times | None |
| Commercial ERP | Order/commitment and effective approved cost rates | None |
| Program Planner | Program, milestone/dependencies, implementation links with task details | POST implementation-links |
| Shared audit | Scoped change events | None |

Routers validate transport types and identity; services implement narrow domain
actions; repositories issue explicit owned-table SQL. Cross-domain readers expose
typed records to services. Future clients use these HTTP APIs, never these internal
reader interfaces, SQLite, fixtures or the developer validator.

The caller can discover the entire plan input through HTTP: read the change and
exact revisions, request coverage/options, inspect source records/documents, then
echo the chosen option's resources and expected-source object. Options embed the
otherwise undiscoverable lab/slot records and procedure/policy selection. The plan
response supplies its version/digest; decision supplies approval ID; jobs/links GETs
supply persisted resource/task/dependency details. No extra CRUD endpoints needed.

Options return all nine slot/sample combinations, including ineligible ones. Derive
the unique approved procedure/policy from target applicability; fail explicitly if
none or multiple apply. Do not rank by seeded ID or return an authoritative "best"
option. Sorting may be stable for presentation, but cannot determine eligibility.

| Value | Deterministic calculation/check |
|---|---|
| Setup start | Slot.starts_at, no earlier than scenario_now |
| Execution start | Setup start + 120 minutes |
| Reservation end | Execution start + 480 minutes; must fit slot |
| Review ready | Reservation end + 240 elapsed minutes |
| Signed slack | (milestone.baseline_at - review_ready_at) in integer minutes |
| Cost | Referenced approved ERP rate.incremental_cost_cents, USD |
| Rate validity | Entire [reservation start,end) lies within rate interval |
| Resource eligibility | Procedure/config/lab support, sample/unit/lot product and revision, no unit or lot restriction, fresh source data, same campus, available slot/sample and no conflict |
| Approval eligibility | Resource eligibility AND approved policy/action scope AND cost <= limit |
| Deadline | Resource-eligible forecast <= baseline deadline; separate from qualification |

Ineligible combinations return null forecast/slack/deadline flag with reasons.
Late valid options remain eligible. An over-budget technically valid draft can be
persisted but cannot receive the seeded engineer's approval; return policy escalation
required without building an escalation system. Cost limit is per exact plan.

Coverage compares scope, product/revision, full pinned config/model/workload manifests,
criteria binding, completed/pass status, required bin membership, total >=480 minutes
and every required bin >=160 minutes. Require internal observed-duration coherence;
never sum separate incomplete results. No approved equivalence record is present.
Return all applicable mismatch reasons. An evidence gap does not assert failure,
and coverage satisfaction would still not assert engineering/customer acceptance.

Assessment input is structured facts with typed source refs, claimed gaps and
unresolved questions. Check refs/scope and persist authored text as such. Store the
server's computed coverage/options alongside it; free text cannot override eligibility,
cost, success, baseline or authority. Reject unknown mutation fields recursively.

## 4. Read/write permission matrix

| Action | Reader | Automation | Engineer |
|---|---|---|---|
| Scoped business reads and audit | Yes | Yes | Yes |
| Create immutable draft assessment/plan | No | Yes | No |
| Approve/reject exact plan | No | No | Yes, seeded policy |
| Create job/reservation | No | Approved plan only | No |
| Create planner link/task/forecast | No | Matching approved job only | No |
| Edit criteria/results, baseline, ERP or manufacturing | No | No | No |
| Reset through HTTP | No route | No route | No route |

Use the three deliberately public local token selectors from API_CONTRACT.md;
identity-to-role-to-CUST-FML01/PRG-A17 mapping is server-owned. Never trust role,
actor, approved flags, query scope or an approval ID alone. Require `DEMO_MODE=true`
and bind 127.0.0.1; these identities do not establish real human identity. The later
automation adapter must never receive the engineer selector. The eventual smoke
script may emulate it only with the required simulated-identity label.

Authorize program membership before exposing referenced IDs or cached responses.
Unknown and inaccessible records share 404; an out-of-scope list query cannot widen
access. Missing/unknown selectors return 401; recognized role violations return 403.
No catch-all filesystem route, raw SQL route or generic mutation method exists.
Unsupported mutation paths return 404/405; documented POST bodies reject extra keys.

## 5. Approval and state machine

Separate three axes: immutable plan content/version/digest, mutable Engineering
decision workflow, and execution state derived from each domain's persisted outputs.
Scenario timestamps stay fixed at 2026-11-16T09:00:00Z; version/event sequence orders
operations sharing that timestamp. Wall-clock audit time is a separate field.

| Action | Checks | Atomic owned writes | Read-back state |
|---|---|---|---|
| Draft | Automation scope; expected change/source versions; internally consistent target; technically eligible resources | Engineering plan+assessment, draft state, change current_plan_id/workflow/record_version; audit+receipt | Plan draft; execution not_scheduled |
| Approve | Engineer; exact plan version/digest; fresh critical sources/resources; approved policy; allowed spend/actions | Decision, plan state/record_version, current change workflow/record_version; audit+receipt | Approved; approved_awaiting_scheduling |
| Reject | Engineer scoped to exact plan/version/digest, no prior decision; current resource eligibility is unnecessary for a refusal | Immutable rejection, plan state and current change workflow/record_version; audit+receipt | Rejected; cannot schedule |
| Book | Automation; actual matching approved decision; critical sources and availability still match | Validation job+reservation, slot/sample available->reserved and availability_version increments; audit+receipt | lab_scheduled_pending_planner |
| Link | Automation; exact approval/job/resources; critical content current; expected milestone record version | Planner link+task+job dependency, proposed-evidence dependency state, conditional forecast, milestone record_version; audit+receipt | scheduled_awaiting_execution |

Change.current_plan_id is initially null, set on drafting; decisions on another
draft cannot overwrite the current draft's workflow. GET change returns all per-plan
decision/execution refs, making previous scheduled work visible even with a later
draft. GET plan computes execution state via read-only domain interfaces. No lab or
planner transaction writes Engineering state. No GET performs reconciliation writes.

Plans are immutable from creation, including drafts. Every new plan has a new ID
and version 1; optional same-change supersedes_plan_id preserves lineage only.
No edit, revocation or cancellation endpoint is introduced. One decision per plan;
conflicting later decisions need a new plan. The digest is SHA-256 of canonical,
schema-versioned JSON: sorted object keys, normalized UTC and integer amounts,
sorted set-valued refs/actions, and deterministic Unicode encoding. It includes
the plan ID/version/scope, assessment, selected resources/actions, computed cost/time
and source snapshot. It excludes decision/workflow fields, request metadata and
wall-clock audit time. Digest identifies content; server-side authorization enforces
permission. A hash alone is not a signature or human identity proof.

Critical source records include the change content; baseline and proposed requirement;
applicable configs/workloads/criteria; approved procedure and policy; referenced
business documents; selected sample/unit/lot/slot/lab/rate; program, milestone baseline
and order commitment; and evidence-set applicability inputs. Include all typed
assessment sources as well. Return a complete duplicate-free registry-typed source
list from options; clients may add an explicitly cited source only by retrieving
its version, and the server derives the corresponding complete set at plan creation.
Omission/unknown extras cannot narrow freshness checks. The evidence-set digest
includes sorted scoped results and pinned applicability sources, detecting new
results as well as updates. Persist full relevant content plus hashes and versions
so a source edit without a proper version increment is also detected on execution.
Evidence digest inputs exclude current availability, change workflow, jobs and
planner status. They bind immutable run provenance and configuration/workload/
criteria content, avoiding a digest change caused by the plan's own reservation.

`expected_source_versions` example shape (IDs/values are illustrative, list omitted):

```json
{
  "records": [
    {"resource_type": "validation.sample", "resource_id": "SAMPLE-B-017",
     "content_version": 1, "availability_version": 1}
  ],
  "evidence_set_digest": "<sha256 supplied by options>"
}
```

The abbreviated example is deliberately not a valid full plan request. Define the
registry in OpenAPI for every actual resource type, and expose the complete required
source object with options. Missing/extra/duplicate entries -> 422 INVALID_SOURCE_SET;
version/digest mismatch -> 409 STALE_SOURCE. Source snapshots include critical status
(e.g. approved procedure), restrictions and partner refresh times, but exclude
incidental change workflow and milestone forecast record version.

### Why approval and booking do not invalidate themselves

1. Draft/decision update Engineering `record_version`; change `content_version=1`
   and immutable plan_version/digest remain unchanged. Approval checks critical
   content, never its own new workflow status as an old source precondition.
2. Booking compares slot/sample content and availability versions under the SQLite
   write lock. A successful first booking records 1->2 availability versions with
   the exact job/reservation owner, leaving content versions at 1.
3. Planner still compares all critical content, evidence digest and partner freshness.
   For these two availability fields only, it requires the recorded post-booking
   version and exact owner/interval instead of original "available" state. It does
   not waive freshness for an arbitrary changed sample or another job's reservation.
4. Planner checks caller expected milestone.record_version, initially 1, and increments
   it to 2 while baseline/content_version remain unchanged. A matching successful
   retry returns its original receipt before this now-stale expected version check.
5. A competing forecast-only update requires reading the new record version and
   retrying the missing link, if critical content still matches. Changed deadline,
   configuration, policy, restriction, procedure, rate or evidence requires a fresh
   plan/approval for unexecuted actions. A stale-after-booking case preserves the
   job, reports incomplete follow-through and needs reassessment; no hidden cancel
   or automatic reapproval is offered. A superseding plan does not inherit that job.

## 6. Idempotency, uniqueness and partial failure

Require Idempotency-Key on every POST; normalize/limit length and use a hash in audit.
Accept bounded `X-Correlation-ID` or generate one, and generate a unique request ID
per attempt. Receipts key on resolved identity ID + HTTP method + concrete canonical
route including path IDs + key. The request fingerprint covers typed canonical
business input including expected versions; it excludes credentials and correlation
metadata. Preserve list order unless the schema defines that list as a set.

Transaction sequence: authenticate/authorize scope; parse strict request; acquire
write transaction; check receipt; reject changed fingerprint with 409
IDEMPOTENCY_KEY_REUSED; return a matching prior success before stale preconditions;
check semantic uniqueness; resolve/recheck sources; apply owned writes; insert audit
and receipt with original response body/status; commit. Concurrent copies serialize
at this point. Do not store failures as successful receipts or consume their keys.

First successful POST returns 201. An exact-key replay returns the same status and
body with an Idempotency-Replayed header and current request/correlation headers;
it adds a replay audit event but no second business mutation. A new-key duplicate
decision/job/link returns 409 ACTION_ALREADY_RECORDED with authorized existing GET
reference, or DECISION_CONFLICT for a different decision. Check duplicate ownership
before availability/record preconditions changed by the prior success. Separate plan
IDs are allowed alternatives, but resource constraints still prevent conflicting
bookings. Do not invent text-level plan deduplication or an active-plan quota.

The four mutations are four transactions. If a lab response is lost after commit,
retry its same key or retrieve jobs by change to recover the existing booking. If
Planner fails, roll back every Planner change and keep lab job/reservation/audit/
receipt. GET plan/change shows lab_scheduled_pending_planner; retry only the link
with current milestone record version if needed. No cross-system transaction,
background worker, message broker or compensation engine is needed.

Stable application errors include INVALID_REQUEST (422), INVALID_SOURCE_SET (422),
RESOURCE_INELIGIBLE (422), STALE_SOURCE (409), RESOURCE_CONFLICT (409),
STALE_MILESTONE (409), APPROVAL_REQUIRED (403), APPROVAL_POLICY_EXCEEDED (403),
DECISION_CONFLICT (409), ACTION_ALREADY_RECORDED (409), IDEMPOTENCY_KEY_REUSED (409),
FORBIDDEN_ROLE (403), UNAUTHENTICATED (401), NOT_FOUND (404), DATABASE_BUSY (503),
and INTERNAL_ERROR (500). Use the contract error envelope with safe typed details.
No SQL, paths, credentials or echoed unvalidated bodies appear in errors/logs.

## 7. Audit/event model

Append-only audit table with monotonic sequence and event ID, scenario and actual
UTC timestamps, synthetic flag, domain, actor identity ID/role, action/outcome,
authorized customer/program/change scope, resource refs, plan/approval/job/link refs,
request/correlation IDs, hashed idempotency key, and bounded before/after field or
version diffs. Explicitly distinguish create/approve/reject/book/link, denied,
failed and replay events. Never record Authorization headers or arbitrary body text.

Commit successful mutation events and receipts in the same owned transaction.
On expected denial roll back any business work, then append a sanitized denial in
a fresh short transaction. Unauthenticated/unresolvable events have null actor/case
where appropriate and are not exposed through another customer's case. Attribute
known scoped denials without trusting claimed IDs as scope. If DB failure prevents
audit persistence, return failure and emit sanitized operational diagnostics; do not
claim an audit exists or a write succeeded.

Normal SQL paths cannot update/delete audit rows, decisions or immutable plan content;
add SQLite guards/triggers as defense in depth and tests for handler write ownership.
Audit is append-only for a demo generation, not tamper-proof against someone with
the local database file. Guarded reset is the explicit destructive local exception.
No event sourcing or external logging service is required.

## 8. Seed, persistence and reset strategy

Store the developer demo only beneath workspace `.demo/`. Runtime opens an existing
marked DB without reloading fixtures; if absent, explicit local initialization
validates and creates it. Validate all seed references, units, versions, timestamp
logic and exactly six document paths before changing persistent state. Insert seed
rows and document contents/hash atomically, resolving FK cycles with a deliberate
load order/deferred checks. Validate foreign_key_check before commit.

Proposed commands during the build are `uv run mock-enterprise init-demo`,
`uv run mock-enterprise serve`, and `uv run mock-enterprise reset-demo --yes`.
These commands do not exist yet. Require explicit DEMO_MODE for all three and
document the fixed default path. Use argparse rather than adding a CLI dependency.

Reset checks: configured path is under the resolved workspace demo storage; every
target/parent component is nonsymlink; target is a regular file with one hard link;
ownership/schema/scenario marker matches; explicit prompt confirmation or --yes;
server is stopped. Use a process lifetime advisory lock shared by serve/reset to
reject reset against a running service (a stale PID file alone is insufficient).
No arbitrary fixture argument, arbitrary reset path, recursive deletion or HTTP reset.

Perform reset in an exclusive SQLite transaction using a fixed schema/seed routine:
drop/recreate only known demo tables/triggers inside that transaction and reload
the canonical fixture/documents, checking FKs before commit. Any failure rolls back
the original DB. Refuse unexpected database schema objects instead of deleting them.
This also reconciles immutable-row guards without adding a persistent public bypass.
Initial creation uses the same seed routine on an empty owned target. Do not replace
a live SQLite file or casually remove WAL/journal sidecars.

Reset clears plans/decisions/jobs/reservations/tasks/links, workflow changes, receipts
and audit events; restores slot/sample/version/forecast values and all seeded records.
Restored business state matches seed; metadata may record a new reset generation.
Audit immutability is bounded by this deliberately destructive reset. Reset twice
must produce equal business state. Tests use separate temporary file databases via
internal test configuration, never the developer default or a public admin route.

For build-time tooling, set UV_CACHE_DIR and UV_PYTHON_INSTALL_DIR to project-local
`.cache/uv` and `.tools/python` if Python installation is needed; keep .venv local.
Do not modify user-level settings or scan for keys. No installation was performed
during planning. A Python 3.12 executable was not found on PATH; build setup must
provision/verify one and run all implementation checks on it.

## 9. Testing and implementation sequence

Implement tests with each increment, using ACCEPTANCE_TESTS.md as the detailed exit
contract. The planning validator is an independent static check, not runtime code
and not a substitute for testing implemented handlers. Keep expected option answers,
positive synthetic evidence and failure hooks only in scripts/tests, outside the
business-document allowlist. Source files cannot be retrieved through the service.

| Build increment | Deliverables | Required proof before advancing |
|---|---|---|
| A: data/read APIs | Python 3.12/uv setup, schema/seed, identity/scope, all 25 business GETs, coverage/options, docs | Seed integrity; all reads across five systems; full/insufficient/per-bin/config-version coverage; option math and input renaming/reordering; scope isolation; business state unchanged by reads |
| B: owned writes | Immutable drafts/decisions, atomic booking, atomic planner action and derived execution status | Unapproved blocked; engineer policy checks; successful real persistence; approval and reservation do not stale their next action; exact source discovery through HTTP |
| C: concurrency/recovery | Durable keys/uniqueness, stale checks, audit, guarded reset | Same/new-key duplicates; changed-key content; lost response; simultaneous requests; stale content/availability; partial planner rollback/recovery; audit/receipt atomicity; protected state and document isolation |
| D: executable handoff | HTTP smoke, OpenAPI export, README commands, BUILD_HANDOFF.md | pytest on Python 3.12; real local HTTP end-to-end; process restart against same DB; guarded reset twice; schema inventory/error examples match implementation |

Detailed edge cases: missing/unknown/reader identity; automation self-approval;
forged or cross-plan approvals; changed immutable digest; malformed/extra fields;
cross-program IDs; held lot on an otherwise available sample; stale unit independently
from lot; age exactly 1440 minutes and just older; future partner timestamp;
full-suite duration but one short bin; altered model/runtime/profile/criteria version;
new evidence after planning; exact-fit/short slot; overlapping lab interval;
rate boundaries and $0; exactly 200,000 cents and 200,001 cents; qualified late option;
competing milestone updates; unauthorized cached-response replay; concurrent requests
using different DB connections; failure before/after local commit; DB lock timeout;
reset symlink/hard-link/non-demo/out-of-root/active-server rejection; malformed document
allowlist and attempted developer-file retrieval. Unmodeled future result publishing,
real performance measurements and customer acceptance are excluded.

The live smoke uses HTTPX against an actually running loopback Uvicorn server and
must print exactly the required label:

```text
SCRIPTED MOCK-SYSTEM INTEGRATION TEST — NO AI INFERENCE; ENGINEER IDENTITY IS SIMULATED.
```

Smoke sequence: verify clean seed through HTTP; read all domains and source versions;
derive/compare options; create draft; demonstrate unapproved booking denial; use the
simulated engineer identity for the exact decision; book one job/reservation; link
one planner task; GET exact plan/decision/job/link/milestone/order/audit; replay and
new-key duplicate checks; exit nonzero on mismatch. Verify forecast is conditional,
requirement V1 remains approved/V2 requested, milestone baseline and ERP commitment
unchanged, and no new results. Driver code may start/stop a server or invoke the
local CLI for lifecycle tests, but all business operations/assertions use HTTP.

Separate test-only transport/internal hooks simulate lost replies and Planner failure;
no public failpoint route. Restart the actual server and read the same records over
HTTP, then stop/reset/restart and read the original baseline. In-process TestClient
alone does not meet live HTTP proof. Export OpenAPI from the implemented app, check
unique operation IDs, request/error schemas and route inventory, and record actual
commands/counts/skips/limitations in the future BUILD_HANDOFF.md.

## 10. Corrections and resolved ambiguities

All names, workload bins, suite duration, rate amounts, authority limit, slot dates,
milestone deadline and customer commitment were retained. No preferred option or
successful target result was added to business retrieval.

| File(s) | Correction or explicit interpretation | Why it is safe |
|---|---|---|
| seed.json (schema 1.1) | Add historical configuration/workload content-version bindings and criteria ID/version to all three results | Existing records already describe those runs; pins the original context without creating coverage |
| seed.json | Add `status=approved` to POLICY-APP-01 | Policy and contract already call it approved; removes reliance on an implicit status |
| seed.json, SCENARIO.md | Milestone.updated_at becomes 09:00Z from 08:30Z | Its pending REQ-042-V2 dependency cannot predate receipt of that requirement; baseline/forecast dates unchanged |
| SCENARIO.md, procedure business document, API contract | Rename ambiguous "Test start" to reservation/setup start; define execution start and interval boundaries | Existing ten-hour slots and fourteen-hour review forecasts already include setup |
| SCENARIO.md | Explain source refresh/import time versus historical effective existence | Historical runs may precede a source refresh and the formal change request; the target manifest existed beforehand |
| API_CONTRACT.md, this plan | Embed lab/slot/source versions in options; define evidence-set digest and complete source inputs | Closes HTTP discovery and freshness gaps without new endpoints or fixture access |
| API_CONTRACT.md, this plan | Separate content/workflow/availability versions; derive cross-domain execution state; define ownership and planner dependency transition | Avoids self-induced staleness and cross-domain writes masquerading as one transaction |
| API_CONTRACT.md, this plan | Define approval ID, immutable version 1 per plan ID, decision uniqueness, late/over-budget behavior, new-key conflict and recovery | Makes existing exact-plan approval and uniqueness rules executable without an escalation workflow |
| API_CONTRACT.md, this plan | Persist allowlisted documents; one outstanding sample reservation; per-generation audit/reset semantics | Makes bounded scheduling, immutable retrieval/audit and deterministic reset compatible |
| ACCEPTANCE_TESTS.md | Add regression requirements for each resolved ambiguity and concurrency boundary | Checks changed contracts without claiming any runtime checks have run |
| README.md | Link planning checkpoint and validator, retain unimplemented status | Handoff is distinguishable from an implemented service |

Fixture changes are pre-implementation authoring corrections, so entity content
versions remain initial version 1 and documentary revision labels remain unchanged.
The seed schema is bumped to 1.1. There is no deployed state or existing approval to
invalidate. Future content edits after initialization must use proper versions and
guarded seed/reset, never silently rewrite persisted records.

No blocker remains. Known simplifications are fixed scenario time, 24/7 review,
same-campus setup, public role-test selectors, one local database and one outstanding
job per sample. Existing result pass booleans are synthetic observations; numerical
criteria, hardware simulation, result authorship, acceptance and release are out of
scope. Later stale-after-booking changes may require manual reassessment because
cancellation/rebooking is deliberately absent.

## 11. Actual planning validation and handoff

Commands run from the project root during this phase:

| Command/check | Actual result |
|---|---|
| `pwd` and `rg --files` (excluding dependency/cache directories) | Inspected the starter files; no application code initially present |
| `cat` for all named specifications, seed, six business documents and three prompts | Reviewed full contents; long reads repeated where output was truncated |
| `git status --short && git log -3 --oneline` | Exit 128: directory is not a Git repository; log did not run |
| `command -v python3 python3.12 uv git` | python3, uv and git found; python3.12 not on PATH |
| `python3 --version`; `uv --version`; `git --version` | Python 3.9.6; uv 0.7.6; Git 2.50.1 |
| `ls -la` | Confirmed local starter layout and absence of repository configuration |
| `python3 scripts/validate_scenario.py` | Exit 0: 42 records, 110 resolved references, six allowlisted documents, three insufficient results, nine computed slot/sample combinations; six corruption probes rejected |
| `python3 -m json.tool fixtures/seed.json > /dev/null` | Exit 0: corrected seed is valid JSON |
| Inline standard-library Python checks (`ast`, `re`, `pathlib`) | Exit 0: 29 business method/path pairs (25 GET, four POST); validator parses; Markdown fences balanced and local links resolve |

Validator expected eligible outcomes: STANDARD review Nov 20 22:00Z, -1680 minutes
slack, 0 cents; PRIORITY review Nov 18 20:00Z, +1320 minutes, 180000 cents. Both use
SAMPLE-B-017; the other seven combinations are resource-ineligible. Partner records
are 30 scenario minutes old and all selected rates cover their reservations.

The validator uses only the standard library and supports the available Python 3.9
for planning. It does not write files, create a DB, call services or implement APIs.
Corruption probes are in-memory copies; corrected fixtures remain unchanged.
Manual contract review covers authority/state transitions and prose consistency;
this is a design check, not a simulated implementation test.

Not run because the service is intentionally unimplemented: dependency resolution
or installation, Python 3.12 execution, pytest API tests, Uvicorn startup, live HTTP,
OpenAPI export, runtime concurrency/permissions/persistence/reset proof. No Git diff
is available because this folder is not a Git repository. No new Git repository or
files outside the project were created. The next authorized phase is prompts/02_BUILD.md;
stop here until that implementation is requested.

## Build reconciliation

The scoped API implementation is now complete. See [BUILD_HANDOFF.md](BUILD_HANDOFF.md)
for actual verification results, exact commands and remaining limits. The build
uses one explicit module per domain and shared typed infrastructure instead of
separate router/schema/repository files for each small domain. The fixed model
registry generates per-entity typed SQL columns and scoped scalar foreign keys.
Small validated collections use JSON columns rather than separate child tables;
seed import and domain handlers validate their references. These changes reduce
boilerplate while preserving the reviewed API boundaries, state transitions,
approval binding, transaction ownership and uniqueness behavior. The original
sections above record the pre-implementation plan, not current unimplemented status.

## Phase 08.4A — connected standard handoff

Implemented distinct CR-019 within the existing requirement-change family.
The approved standard policy verifies exact applicability, reusable evidence,
remaining work and ownership. The host creates only an immutable Validation
Operations intake and confirms it by independent source readback. Durable
idempotency/reconciliation and typed case/run/UI projections are added without
new agent orchestration or fake human approval. Existing CR-017 critical source
scope is preserved across the additive installation. Lab/testing/acceptance and
all background automation stay downstream/inactive.

See [08.4A handoff](PHASE08_4A_HANDOFF.md) and its verification record. The 08.3
proposal for simulation-only 08.4 is superseded by the explicit connected 08.4A
request. Next is 08.4B Yield / Quality Exception Recovery only on explicit request.
