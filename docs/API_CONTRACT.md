# Mock-enterprise API contract — v1.1

This is an implementation contract for generic local mocks, not a real vendor API.
Use one FastAPI service, `/api/v1` prefix, five tagged domain routers, and SQLite.
One deployment is an intentional shortcut. Domain ownership and action boundaries
remain explicit; it does not demonstrate true distributed-system isolation.

## Platform conventions
- `/health`: public local readiness and `synthetic: true`; no secret/config dump.
- `/docs` and `/openapi.json`: generated interactive API docs and machine-readable schema.
- Bind to 127.0.0.1 by default. Require explicit DEMO_MODE for mock identities.
- JSON requests/responses; typed Pydantic models; reject unexpected mutation fields.
- Stable OpenAPI operation IDs, descriptions, tags, and representative examples.
- Every domain record carries IDs, owning system, content/record version as relevant,
  scenario update timestamp, and synthetic provenance. Use fixtures as the source
  of business fields; simple typed SQLite tables are sufficient.
- List results return an `items` array. Single-record reads return a typed object.
- Mutating requests need `Idempotency-Key` and a correlation ID (server-generate the
  latter when absent). IDs and permission state are validated server-side.
- Common errors: 401 missing/unknown demo identity; 403 forbidden role or unapproved
  action; 404 missing/inaccessible resource; 409 stale/conflicting state or reused
  idempotency key with different content; 422 malformed or inconsistent input.
- Error body: `{error: {code, message, details}, correlation_id}`. Choose stable
  application error codes and test them; do not depend only on human prose.

## Local mock identities, not production authentication
Use a fixed server-side mapping from three deliberately fake local bearer tokens:
`demo-automation-local-only`, `demo-engineer-local-only`, `demo-reader-local-only`.
Document these as public role-test selectors with no identity assurance. Never use
real credentials or suggest this is secure authentication for a deployed service.

- Reader: business reads only.
- Automation: business reads, draft assessment/plan creation, approved job creation,
  approved planner update; never approvals, criteria edits, results, or read-only domains.
- Engineer: business reads and approve/reject plan decisions within the seeded policy.
- Missing or unrecognized identity: no business access.
- Each identity is scoped server-side to CUST-FML01 / PRG-A17. Do not trust a query
  parameter as authorization to retrieve another customer's records.

Do not accept `actor`, `role`, `is_admin`, or `approved: true` from request bodies as
an authority source. The future agent's tool configuration will not contain the
engineer's token. A local integration smoke script can emulate the two identities,
but must label the approval as simulated. This does not prove a real human clicked.

## Public endpoint inventory
All listed paths below are relative to `/api/v1`.

### Engineering Hub: requirements / PLM mock
| Method/path | Contract |
|---|---|
| GET `/engineering/changes/{change_id}` | Request, baseline/proposed revision refs, scope, workflow state, content version. |
| GET `/engineering/requirements/{requirement_revision_id}` | Exact revision and status; do not silently resolve latest. |
| GET `/engineering/configurations/{configuration_id}` | Exact product/hardware/software/workload applicability fields. |
| GET `/engineering/workloads/{workload_profile_id}` | Exact workload manifest and required coverage/duration. |
| GET `/engineering/procedures/{procedure_id}` | Approved procedure, eligibility, duration, criteria reference, and document link. |
| GET `/engineering/policies/{policy_id}` | Approved permission limits and action scope, read-only. |
| GET `/engineering/acceptance-criteria/{criteria_id}` | Existing criteria reference; numeric thresholds intentionally unmodeled in this scheduling phase. |
| GET `/engineering/documents?program_id=...` | Allowlisted document metadata, including requested/approved status, filtered to authorized program; no filesystem browsing. |
| GET `/engineering/documents/{document_id}` | Allowlisted document content and metadata; use stable IDs, never arbitrary file paths. |
| POST `/engineering/changes/{change_id}/plans` | Automation creates a draft impact/implementation plan, as detailed below. |
| GET `/engineering/plans/{plan_id}` | Plan content, version, digest, source snapshot and decision references. |
| POST `/engineering/plans/{plan_id}/decisions` | Engineer records an approved/rejected decision for an exact plan/version/digest. |
| GET `/engineering/decisions/{decision_id}` | Persisted decision, scope, signer identity, status, and timestamps. |

Controlled document metadata additionally supports title, product/configuration,
business owner team, effective date, superseded-by identity, applicable workflows,
and a historical flag. Historical publications use `status=historical`; this does
not grant procedure or disposition authority. Quality-owned publications remain
in the existing Engineering controlled-document endpoint. See the
[QE-004 corpus handoff](PHASE10_QUALITY_CORPUS_HANDOFF.md) for additive installation,
existing-approval compatibility and shared-index verification.

Plan-create input:
`expected_change_content_version`, `target_requirement_revision_id`,
`configuration_id`, `procedure_id`, `sample_id`, `slot_id`, `milestone_id`,
`assessment` (facts with source refs, evidence gaps, unresolved questions), and
`expected_source_versions` for applicable source inputs.
An optional `supersedes_plan_id` records revision lineage within the same change;
it neither revokes nor edits a previous decision or an already scheduled job.

The server resolves selected resources and derives cost/timing, allowed actions,
critical source snapshot, and plan digest. It does not trust submitted cost,
qualification, predicted success, or approval fields. A well-formed, known but
ineligible selection gets a structured validation/conflict error. Unknown IDs
get 404. Limit writable actions to schedule validation and link its program plan.

Store `plan_version`, `plan_digest`, `draft/approved/rejected` state, and immutable
plan content. For a revision create a new plan, optionally referencing the earlier
plan; do not mutate an approved plan in place. Reject cross-program references.

Decision input: `decision` (approve/reject), `expected_plan_version`,
`expected_plan_digest`, and a short reason. Resolve approver identity server-side.
Check current critical source versions, eligible resources, and policy before an
approval. Scope the approval to the plan and at most the seeded approval limit.
If a decision already exists, idempotent retry returns it; conflicting subsequent
decisions require a new plan in this limited implementation. Do not update the
approved product requirement just because a test plan was authorized.

### Validation Lab: operational actions
| Method/path | Contract |
|---|---|
| GET `/validation/coverage?change_id=...` | Compute coverage and return candidate evidence with exact mismatch reasons. |
| GET `/validation/options?change_id=...` | Compute options from slots, eligibility, rates, durations, and milestone. No hard-coded best option. |
| GET `/validation/results/{result_id}` | Read immutable seeded evidence and configuration/provenance. |
| GET `/validation/samples?program_id=...` | Lab location, availability, configuration and physical-unit refs. |
| POST `/validation/jobs` | Automation submits `{plan_id, approval_id}`; derives all work from the approved plan. |
| GET `/validation/jobs?change_id=...` | Read jobs and reservations for the scoped case. |
| GET `/validation/jobs/{job_id}` | Read job, plan/approval refs, scheduling status, and reservation refs. |

`POST /validation/jobs` must validate identity, actual approval, plan digest,
critical input versions, no manufacturing restriction, procedure/configuration
eligibility, budget, and current slot/sample availability. Reserve resources and
create the job atomically within Validation Lab. Exactly one job per immutable
plan is allowed even if the caller changes its idempotency key.

No business endpoint may let automation manufacture a result, mark a scheduled
job passed, or declare customer acceptance. Seeded result records are read-only.
Result simulation is a later explicit phase, not a fake auto-pass in job creation.

Coverage uses program/customer, product revision, full configuration, model and
workload profile, required total and per-bin duration/coverage, and actual result status. Return
supported mismatch reasons such as `WRONG_PRODUCT_REVISION`, `WRONG_PROFILE`, or
`INSUFFICIENT_DURATION`; a past pass flag alone is not coverage.

Options show eligibility reasons, source refs, total cents, lab start/end,
review-ready forecast, and signed deadline slack. A qualified late option is
still qualified but misses the milestone; do not conflate these flags. Unknown
support or missing evidence is not automatically a hardware failure.

### Manufacturing Portal: read-only partner view
| Method/path | Contract |
|---|---|
| GET `/manufacturing/units/{unit_id}` | Product/revision provenance, source lot, relevant restrictions, content version, last update. |
| GET `/manufacturing/lots/{lot_id}` | Lot lineage summary, program/product revision and restriction status. |

No public mutation endpoints. Program identity and both unit/lot restrictions
must be checked when choosing a sample. Lab location/reservation is owned by the
Validation Lab, not inferred from manufacturing status. Use the fixed scenario
clock to reject manufacturing data older than the seeded 24-hour freshness policy.

### Commercial ERP: read-only business context
| Method/path | Contract |
|---|---|
| GET `/erp/orders/{order_id}` | Customer/program, quantity, immutable committed delivery time, status. |
| GET `/erp/cost-rates?program_id=...` | Effective, approved incremental cost inputs in USD cents. |

No public order, price, quantity, cost-rate or commitment mutations. Availability
comes from lab slots; rates come from ERP. No hard-coded revenue-saving output.

### Program Planner: limited coordinated writes
| Method/path | Contract |
|---|---|
| GET `/programs/{program_id}` | Program owner, customer, product/config refs and milestone refs. |
| GET `/programs/{program_id}/milestones/{milestone_id}` | Baseline, current internal forecast, dependencies, record/content versions. |
| POST `/programs/{program_id}/implementation-links` | Authorized automation creates a task/dependency and updates the internal forecast in one local transaction. |
| GET `/programs/{program_id}/implementation-links?change_id=...` | Read persisted response links/task/job refs and status. |

Implementation-link input: `plan_id`, `approval_id`, `job_id`,
`expected_milestone_record_version`. Validate the persisted matching scheduled job
and approval, exact program/milestone/scope, and immutable critical input versions.
Derive the forecast from the job and approved review duration. Do not accept a
freeform client forecast. Preserve baseline and customer commitment. Label the
forecast conditional on successful testing and review. One link per plan/job.

### Audit
GET `/audit/events?change_id=...` returns scoped mutation/denial/replay evidence:
event ID, scenario and wall-clock timestamps, domain, actor, action, outcome,
resource ID, plan/approval refs when relevant, correlation ID, request ID,
idempotency key or safe hash, and before/after version or field changes.
Do not include bearer headers or other credentials. All successful mutations
have audit records in the same local transaction as their business change.

## State, versioning and retry rules
Use distinct content and workflow/record versions where necessary. The source
snapshot binds decision-relevant content, not incidental workflow status.
Recording approval must not instantly invalidate the same plan. Nor should its
own resource reservation make the later planner link appear stale.

Immediately before job creation, atomically compare expected availability/state
and reserve the actual sample and slot. External changes invalidate the plan or
require reassessment; the plan's own completed action is recognized as expected.
Planner updates validate their own target record and the existing job's provenance.

Idempotency scope: identity + method + route + key. Store request fingerprint and
original status/body with the mutation in the same transaction. After identity
and current read/access checks, return an existing matching successful result
before re-running stale preconditions; same key with changed body returns 409.
A successful replay is not a second mutation. Add a uniqueness constraint so
changing the key cannot create a second job or implementation link for the plan.

Do not use a single transaction spanning all five logical systems. If lab creation
succeeds but planner update fails, keep the job and expose incomplete follow-through.
Retry only the missing action. Tests may inject failure through internal test hooks
or mocked transport, never through a public admin route.

## Reset, runtime and verification utilities
- Local `reset-demo` CLI: fixed documented fixture, explicit confirmation/`--yes`,
  demo DB ownership marker, restrict target to configured workspace demo storage.
  Refuse non-demo DBs/symlink targets; never recursively delete arbitrary paths.
- Seeding/reset is atomic, repeatable, and restores no approvals/jobs/reservations.
- Separate test databases; tests never reset a developer's active demo by accident.
- HTTP smoke script uses local requests to a running server and reports before/after
  IDs, statuses, approvals, forecast, and immutable commitment checks. It must not
  use ORM/repository calls for business operations. It can emulate a demo engineer
  solely to test the human boundary and must print that this is scripted.
- Document setup, serve, seed/reset, test, and smoke commands in the generated README.
- Export the implemented OpenAPI schema. Optional minimal record inspector only
  after core checks pass; no frontend project in this milestone.

## Planning clarifications — v1.1

These close implementation gaps without adding business actions. The detailed
schema, transaction sequence, and verification matrix are in IMPLEMENTATION_PLAN.md.

### Discoverable sources and derived calculations
Coverage returns `items` with immutable result provenance, applicability reasons,
and a top-level `coverage_satisfied` flag. Each result binds configuration, workload,
and criteria IDs and content versions. A changed referenced version is insufficient
coverage even if the ID is unchanged. Compare the full configuration and workload
manifest; require completed/pass status, total duration and every required bin's
duration. Do not combine incomplete runs or infer acceptance from evidence coverage.
Historic result pass flags remain facts about their original runs.

Options enumerate every in-program slot/sample combination for the target procedure,
including rejected combinations and their reasons. Derive the procedure and policy
from approved records applicable to the change's target; if there is no unique match,
return a structured ambiguity/ineligibility error instead of choosing by ID.
Return embedded slot and lab records, sample/unit/lot refs, procedure and policy IDs,
rates, milestone refs, and the complete expected-source object needed to create a
plan through HTTP. No separate slot/lab CRUD endpoints are required. Results also
carry source refs retrievable through the result and engineering GET endpoints.

`expected_source_versions` is an object with `records` (a duplicate-free list of
`{resource_type, resource_id, content_version, availability_version?}`) and
`evidence_set_digest`. Resource types come from a fixed server registry. The server
requires the complete applicable source set; missing, extra, or duplicate entries
are 422 `INVALID_SOURCE_SET`, and changed values are 409 `STALE_SOURCE`.
The required set is the option's server-derived sources plus any additional typed,
authorized sources explicitly cited by the assessment. Extra uncited records are
invalid; an explicitly cited record requires its retrieved content version.
The digest covers the full scoped evidence set and its applicability inputs so a
new or changed result cannot escape detection merely because its ID was absent
from a draft. Return the object from options; clients echo it without DB access.
Evidence applicability inputs are immutable run provenance and configuration,
workload and criteria content; exclude current resource availability, workflow,
jobs and planner status so booking cannot change its own evidence digest.

`lab_start_at` is slot/setup start; `execution_start_at = lab_start_at + setup`;
`lab_end_at = execution_start_at + suite`; `review_ready_at = lab_end_at + review`.
Require `lab_end_at <= slot.ends_at` and start no earlier than scenario time.
Use half-open reservation intervals; an approved rate must cover the entire interval
(`effective_from <= lab_start_at`, `lab_end_at <= effective_to`). Freshness requires
`0 <= scenario_now - updated_at <= 1440 minutes` for both unit and lot. Reject future
partner refresh timestamps. Same-campus movement is covered by setup.

Report `resource_eligible`, `approval_eligible`, `meets_deadline`, and
`deadline_slack_minutes` separately. Signed slack is deadline minus review-ready.
For resource-ineligible options, forecast/slack/deadline flag are null, with explicit
reasons; costs and source data remain visible. A resource-eligible late option can
be drafted and approved under the policy; lateness is not a resource restriction.
A technically eligible over-budget plan may be drafted for assessment, but its
approval is denied with 403 `APPROVAL_POLICY_EXCEEDED`. No escalation workflow is
implemented. The budget limit is inclusive and applies to the selected plan's
incremental cost, not a new cumulative-program budget.

### Ownership, state, and exact approval
An immutable plan has `plan_version = 1` for its unique plan ID. A revision receives
a new ID and its own version 1; lineage is expressed by `supersedes_plan_id`.
Store lifecycle separately with `record_version`; plan content/digest never change.
An approval is an approved decision row: `approval_id` is that decision's ID, not
a caller assertion. There is at most one decision per plan, including rejection.

Engineering persists change workflow `pending_impact_assessment -> plan_drafted ->
approved_awaiting_scheduling` (or `plan_rejected`) for the current draft/decision.
Only engineering writes these fields. GET change/plan also derives execution state
from persisted jobs/links: `not_scheduled`, `lab_scheduled_pending_planner`, or
`scheduled_awaiting_execution`. Include per-plan statuses so alternative drafts
cannot hide a prior booking. Lab and Planner never update Engineering tables.
Read projections do not write state or pretend to complete another domain's action.
Engineering sets `current_plan_id` on draft creation (initially null). A decision
changes the case workflow only if it belongs to that current plan. Older plans keep
their own decision and execution state visible. Rejecting a scoped, exact undecided
plan does not require its resources still to be eligible; approvals do.

Draft creation and decision update Engineering record versions, never critical
content versions. Booking increments slot/sample availability versions and binds
them to the job/reservation; it does not alter their content versions. Before linking,
verify the exact job/approval and that those resources are reserved by that job with
the recorded post-booking availability versions. Exempt only this exact owned
transition; unrelated source changes remain stale. Milestone forecast/dependency
writes advance `record_version` only; baseline/scope are `content_version` inputs.

A reservation is one row binding the job, plan, slot and sample for setup/execution.
This phase conservatively reserves a sample for its one outstanding job; no release,
rescheduling, cancellation or multi-job sample calendar is exposed. Prevent both
duplicate slot use and overlapping reservations in the same lab. This is sufficient
for the single response scenario, without a general scheduler.

Planner atomically creates one link, one task and a job dependency, marks the existing
proposed-requirement dependency `validation_scheduled` (still unsatisfied), and sets
the exact derived internal forecast with `forecast_status = conditional_on_test_and_review`.
The task remains `scheduled`; no evidence result, criteria or acceptance state changes.
Expose task/dependency details in link/milestone reads so verification is HTTP-only.

### Deterministic conflicts and recovery
New successful records return 201. Matching successful idempotency replays return
the original status/body before stale-precondition checks, with a replay header.
Failed requests do not consume a key. A new key attempting a previously completed
decision/job/link returns 409 `ACTION_ALREADY_RECORDED` with the authorized existing
resource reference; a conflicting decision returns 409 `DECISION_CONFLICT`.
Clients recover through GET rather than issuing another booking. These uniqueness
checks precede preconditions invalidated by the completed action itself.

Only successful mutations commit business state, an audit entry, and idempotency
receipt together. Important denied requests roll back business work then append a
separate sanitized denial event; replays append a replay event. Unexpected write
failures never report success. DB lock exhaustion is 503 `DATABASE_BUSY`; a failure
that cannot persist its denial uses a credential-free operational log and fails closed.
Request validation errors must not echo bearer headers, arbitrary input bodies, or
unknown-field values. Unknown/inaccessible IDs return the same scoped 404 response.

Document content is loaded from the six explicit manifest paths into SQLite during
seed/reset with a content hash. Serve by ID from persisted state, not a live directory
or arbitrary path. Require exact allowlisted paths and reject symlinks or traversal;
do not serve README, developer specifications, prompts, scripts, tests or fixture JSON.
Fixture edits require a guarded reset; startup never overwrites an existing demo DB.

## Implemented response shape notes

The exported `docs/openapi.json` is generated from the implemented typed models.
Option `timing` groups `lab_start_at`, `execution_start_at`, `lab_end_at`,
`review_ready_at` and `deadline_slack_minutes`; the entire object is null when
resources are ineligible. Other eligibility flags remain separate. Jobs embed one
`reservation` in read responses, and implementation links embed their `task`.
The ERP rate list returns approved rates effective at the fixed scenario time;
options also check rate validity for the full future reservation interval.

## Source-system UI discovery additions — September 2026

The authorized UI phase adds five GETs (34 business method/path pairs: 30 GETs,
four unchanged POSTs). All require an existing demo identity and enforce its
customer/program scope. An optional `program_id` filter cannot widen authorization;
out-of-scope requests return 404. No database schema or fixture change is needed.

| GET path relative to `/api/v1` | Response |
|---|---|
| `/engineering/changes` | `Items[Change]`, existing change worklist |
| `/manufacturing/units` | `Items[Unit]`, persisted physical-unit inventory |
| `/manufacturing/lots` | `Items[Lot]`, persisted source-lot register |
| `/erp/orders` | `Items[Order]`, existing customer orders |
| `/programs` | `Items[ProgramSummary]`, existing program plus customer/supplier names, fixed `scenario_at`, and partner freshness limit in minutes |

The program summary joins authorized existing records and explicitly allowlists its
context fields. It does not expose arbitrary DB metadata, fixture paths or developer
files. Detail contracts remain unchanged. The earlier no-frontend milestone guidance
above is historical; AGENTS.md and MOCK_APPS_UI_PLAN.md govern the authorized UI phase.

## UI follow-up: execution projection and descriptive context

`GET /engineering/changes/{change_id}` now includes `execution_state` for the
`current_plan_id`, derived from that plan's persisted job and Planner link. With
no current plan it is `not_scheduled`. Engineering's stored `workflow_state`
remains separate; Validation and Planner do not write Engineering records.
Every plan still exposes its own execution state, so an older booking remains
visible even when the current plan is a newer draft. This is a read projection.

Manufacturing `Lot` and `Unit` responses have optional `hold_details`, defaulting
to an empty list. Each detail contains `restriction`, `rationale`,
`responsible_team`, and `release_conditions` and must describe one of that
record's actual restrictions, without duplicates. ERP `Rate` responses have
optional nullable `service_name` and `service_description`. These fields are
persisted source context, not computed frontend claims or new write permissions.

New demo files include the descriptive fixture fields. Existing files remain
readable without migration/reseeding: missing optional columns return empty/null
context. No explanation is invented for an older record. Empty defaults are
excluded from critical-content hashing to preserve previously approved snapshots;
supplied descriptions remain bound critical content. The guarded local reset can
load current fixtures only when explicitly invoked against a stopped owned demo DB.

The operation inventory remains 34 (30 GETs, four POSTs). Multi-fact assessments,
multiple citations, `supersedes_plan_id` revisions, and audit drill-downs use the
existing APIs and limits. A revision receives its own ID/version/digest and fresh
decision; neither old approval nor old reservation transfers to the revision.

## Portfolio enrichment contract — stratos-portfolio-1

This additive phase has **36 business operations: 32 GETs and the same four POSTs**.
Original `demo-{reader,automation,engineer}-local-only` selectors retain their
CUST-FML01 / PRG-A17 scope. The UI selects the equivalent explicit
`demo-portfolio-{reader,automation,engineer}-local-only` personas, whose server-owned
allowlist covers the eleven seeded customer/program pairs. No request parameter
can add membership. A mutation resolves its target change/plan and narrows the
identity to that single program before source, reference and approval checks.
The approval verifier checks the persisted signer against the same server-owned
engineer identity/membership map. Merely supplying an engineer role or approval ID
still does not authorize booking. The old engineer cannot approve other programs.

| New GET | Typed behavior |
|---|---|
| `/portfolio` | `Portfolio`: authorized case review summaries, coverage, plans, jobs/links, milestones, samples, slots/labs, effective approved rates, document metadata, historical lab executions and sanitized activity. One SQLite read transaction; no fixture files, arbitrary tables, secrets or developer documents are exposed. Options remain empty here and are calculated only through the existing per-change options endpoint. |
| `/validation/history/{job_id}` | Immutable `HistoricalJob`: imported lab execution provenance, exact configuration/procedure/sample/lab, start/completion times, recorded-by/source reference and IDs of independent observations. No POST exists; it is never produced by booking. |

The existing directory endpoints accept authorized program filters or list the
caller's permitted portfolio. Coverage, options and bound source sets remain
program-local even for a portfolio identity. Cross-program resources/citations
are rejected. The original single-program reads still return their original scope.

Optional source context adds change category/owner/priority/next action, requirement
summary, manufacturing inventory state, program name/business unit/lifecycle/health/
next action, milestone owner/health/next action, and dependency owner/note.
Change intake can also represent new, customer clarification, blocked, closed and
superseded source states. Closed/superseded cases reject new drafting with 409
`CHANGE_CLOSED`; this is not a new reopen operation. The runtime plan/decision/job
state machines and allowed actions remain unchanged. Completed archive dependencies
refer to approved baseline packages, not an accepted requested revision.

Fresh databases include the immutable `validation_history` table and optional
columns. Existing files retain their data and names; missing optional context is
null/empty rather than invented. Old files without historical jobs return an empty
history in the portfolio read. Empty new context is omitted from source hashing to
preserve earlier approval bindings. No automatic migration or reseed occurs; use a
fresh file for this enrichment. A pre-enrichment schema missing the new history table
can fail the conservative guarded reset's schema-ownership check; no bypass was added.

Only six explicit authored business-document file paths can be imported. Thirty
additional business documents come from controlled program templates at initialization,
with stable IDs and hashes. They are persisted before serving; the API never renders
or retrieves developer generator code, specifications, tests or fixture JSON.

Large read responses use gzip. The UI does not compute all 25 slot/sample combinations
for every program while displaying a queue: it fetches the shared read model and
computes options for the selected case. Cross-system actions still require separate
transactions and read-back; no distributed atomicity is claimed.

## Phase 08.2.1 downstream validation extension

The implemented contract now exposes 40 business method/path pairs: 34 GETs and
six POSTs. The original four writes and their authority remain unchanged.

| New operation | Contract |
|---|---|
| GET `/validation/changes/CR-017/physical-validation` | Typed source projection of the current scheduled job, result, applicability and separate engineering review history |
| GET `/validation/jobs/{job_id}/completion` | Immutable synthetic lab provenance, including exact plan/result/criteria versions and simulated vs wall-clock time |
| POST `/validation/jobs/{job_id}/synthetic-result` | Distinct `demo-lab-local-only` selector; existing scheduled CR-017 job and exact plan digest required; no client-authored result data |
| POST `/engineering/changes/CR-017/evidence-reviews` | Engineer selector; exact current evidence digest, decision and reason; separate from plan execution approval |

Paths are relative to `/api/v1`. Both writes retain required Idempotency-Key,
transactional audit/receipts, scoped uniqueness and immutable output records.
Job GET responses gain a nullable `completion` without mutating the scheduled job.
The original result format and coverage checks are reused. A matching immutable
source lab event admits the explicitly later simulated completion time; ordinary
future evidence is still rejected. Conflicting observations within that new campaign
cannot satisfy coverage through an any-pass shortcut.

The versioned evidence-review policy `CR017-ENGINEERING-EVIDENCE-V1` requires the
trusted engineering role and exact complete applicable CR-017 evidence. The decision
binds current requirement/configuration/workload/criteria/procedure versions,
result version/content, lab completion, approved plan, full evidence-set digest and
review policy. Changed bindings make previous decisions historical/stale. Source
engineering review is independently authorized; the control-plane adapter further
requires a recorded successful reassessment. No customer acceptance, requirement
promotion, manufacturing, commitment, scheduling or Planner write is authorized by
this new decision. See [downstream handoff](PHASE08_2_1_DOWNSTREAM_HANDOFF.md) and
[generated OpenAPI](openapi.json).

## Phase 08.4A standard Validation Operations intake

The additive CR-019 installation exposes five narrowly typed source operations:

| Method | Path under `/api/v1` | Meaning |
|---|---|---|
| GET | `/engineering/standard-changes?program_id=PRG-A17` | Scoped installed request discovery; empty on older demos |
| GET | `/engineering/changes/{change_id}/standard-context` | Exact approved request, procedure, policy, configuration, evidence and owner context |
| GET | `/validation/changes/{change_id}/intakes` | Scoped immutable intake collection |
| POST | `/validation/changes/{change_id}/intakes` | Automation role only: one complete standard package receipt |
| GET | `/validation/intakes/{intake_id}` | Independent source readback |

POST requires `StandardIntakeInput`: exact `HandoffPackage` and current
`expected_context_digest`, plus the existing idempotency header. The source
rechecks every mandatory policy condition inside its transaction and reconstructs
the entire expected package. Unknown fields, altered scope/authority, stale
context and ineligible requests are rejected. Immutable intake uniqueness is
(program, change, request content version). Existing role/scoping/audit rules
apply. This does not create a plan, approval, lab job, reservation or Planner task.

Intake state is `received`, package `complete`, lab authorization `pending`,
physical testing `not_started`, customer acceptance `pending`. Package contains
procedure/version, exact configuration/conditions, reusable evidence with hashes,
remaining work/inputs/samples, requested timing, owner/queue, completion criteria,
source digest/version bindings and original workflow/case/run references.

The control host admits CR-019 through the existing requirement-change family:
`POST /control-api/cases/CR-019/investigations` or the catalog manual-run route,
with the closed StartRequest and Program operator/Engineering approver demo
profile. GET case/run views expose eligibility, package and durable handoff state.
Typed `/control-api/standard-handoffs/reconcile` and `/retry` accept only run ID
and expected host version. Unknown/interrupted outcomes are read-only reconciled;
a new invocation cannot bypass them. Known failed actions can retry only after a
fresh exact policy check. The browser supplies no procedure overrides or tools.

The sole added MCP tool is read-only `get_standard_change_context(change_id)`.
It is available to Change Impact, Validation & Evidence and Program/Commercial
only after source intake identifies the standard route. Agents never receive
intake-write tools. The host performs the single permitted source write.

## Phase 08.4B additive quality contract

[Quality recovery handoff](PHASE08_4B_HANDOFF.md) documents the exact source records,
roles and boundaries. Current OpenAPI includes two scoped quality GETs (`context`
and `records`) and four narrow POSTs for investigation, immutable recovery plan,
Program Owner decision and approved Planner task. No inventory, release or ERP
write API is added. `enterprise_api.quality_models` is the shared contract;
`quality_policy.analyze` provides deterministic comparison and supply values.

## Phase 08.4C additive delivery contract

Current OpenAPI adds `GET /api/v1/erp/delivery-requests/{delivery_id}/context` and
`/records`, plus four narrow POSTs: `/erp/commitment-plans`,
`/erp/commitment-decisions`, `/erp/delivery-commitments`, `/programs/delivery-links`.
There are 57 business operations: 42 GET and 15 POST. The shared typed contract is
`enterprise_api.delivery_models`; deterministic gates are in `delivery_policy`.
The context is a scoped source aggregate, including a bounded current CR-017
projection whose evidence digest binds the full existing physical-validation contract.
Only get_delivery_context is added to the read-only MCP catalog (28 tools).

Program Owner approval binds the immutable ERP plan/version/digest, quantity/date
and current source context. ERP commitment and state-head update are atomic within
ERP; the matching Planner link is a separate transaction after ERP readback. Both
have idempotency, scope/uniqueness constraints, audit and exact-field verification.
No generic ERP editing or reallocation/release/validation/acceptance mutation exists.
See [source routes, ownership and decision semantics](PHASE08_4C_HANDOFF.md).

### Phase 08.5 Concierge host boundary

Concierge uses the existing local `/control-api` host (not a source-system API).
`POST /concierge/messages` admits a bounded conversational turn; repeated identical
session/message IDs replay it. `GET /concierge/{session}/{message}` polls without a
model call. `POST /concierge/{session}/{message}/cancel` stops the response where
possible; already admitted workflows remain independent. `GET /concierge-runs/{run}`
reads scoped persisted run metadata only.

`POST /concierge/{session}/actions/{action_id}` accepts only the original context
and `confirmed: true`. The host resolves a short-lived server-held exact reference
and invokes the same existing review/execution/configuration handler. Neither
browser nor model chooses source write arguments or actor roles. Origin checks,
trusted demo identities, source freshness, immutable approvals, idempotency and
independent readback remain unchanged. See the generated
[host OpenAPI](phase08-3-host-openapi.json) and [08.5 handoff](PHASE08_5_HANDOFF.md).

### Phase 08.6 — Operations read projections

The local control host adds typed GET `/operations`, `/operations/runs`,
`/operations/runs/{run_id}`, `/operations/sessions/{session_id}` and
`/operations/health` under `/control-api`. These project existing host metadata,
scoped source reads, allowlisted SDK artifacts and known Phase 07 eval files.
No browser path parameter can select a filesystem artifact. Metadata-only run
polling performs no model calls or workflow/source writes. Initial/detail reads
reuse source-current workbench state; health checks are explicit timestamped reads.
Sanitized historical Concierge turns/confirmations use a bounded field in the
existing metadata index, without executable action tokens. See
[architecture, exact semantics and limits](PHASE08_6_HANDOFF.md).

## Phase 09.1 — Explicit local demo management

The optional loopback host exposes GET `/control-api/demo`, `/demo/preview`,
`/demo/verify` and the separately guarded POST `/demo/reset` when explicitly
configured in demo mode. The reset request is restricted to four canonical cases
or `full`, literal `RESET`, and the current demo epoch. No source business or MCP
reset operation exists. Source path ownership, current HTTP binding, maintenance
leases, scoped restoration/archival and independent baseline validation are
required. Normal startup never restores data. See the [reset boundary and command
contract](PHASE09_1_HANDOFF.md), [baseline](PHASE09_1_DEMO_BASELINE.md) and
[enabled-host OpenAPI](phase09-1-host-openapi.json). Earlier no-host-reset rules
above remain historical business API restrictions; this is an explicit developer
maintenance exception, not changed workflow authority.


## Phase 09.2 — Shared current product projections

The existing GET `/control-api/cases/CR-017` aggregate adds `case_summaries`,
`decision_summaries` and `dependencies`. They are read projections over the existing
scoped HTTP source and host snapshots; no mutation capability or approval is
conferred by a summary, link, state label or decision ID. Original workflow detail
contracts remain intact. Current source availability/freshness takes precedence
over historical successful run observations.

`CaseSummary.state` is one of `new`, `investigating`, `needs_review`, `approved`,
`executing`, `verification_required`, `waiting_external`, `completed_technical`,
`escalated`, `partial_failure`, `stale`, `failed`, or `unavailable`. Workflow-specific
`detail`, `next_action`, authority `boundary`, source availability, semantic
attention/priority, stable issue key, run/decision references and existing links
accompany it. Successful CR-019 intake is `waiting_external` with no human attention
item; downstream lab authority remains separate. `completed_technical` applies only
to current exact Engineering evidence approval and never grants customer acceptance.

Decision summaries contain real human review requirements/records only, with exact
proposal version/digest, reviewer/source-decision IDs, current binding, run,
execution state and exact existing review URL. Engineering evidence decisions bind
the exact evidence digest and have `version: null`; no plan revision is invented. CR-019 intake has no invented decision. All Decisions
filters apply to all four supported human decision kinds. Operations run/index
reads add nullable `current_case_state`, `current_case_label`, and
`source_checked_at`; these distinguish current case state from the particular run's
historical outcome. Metadata-only polling cannot manufacture a fresh source read.

Dependencies use actual shared Manufacturing record IDs and the delivery request's
configuration, requirement revision and optional technical-change binding. The
primary DR-009 request is approved V1, independent of CR-017 requested V2; a V2
variant requires CR-017's current exact Engineering review. See
[the generated host schema](phase09-2-host-openapi.json) and
[the product integration handoff](PHASE09_2_HANDOFF.md).

## Phase 10.1 control-host presentation capabilities

The source API contracts above are unchanged. The separate local control host now exposes `GET /control-api/capabilities` and a role-filtered `GET /control-api/decisions`. See the [persona contract](PHASE10_1_PERSONA_ACCESS.md) and [generated host OpenAPI](phase10-1-host-openapi.json).

The host resolves `X-Stratos-Demo-Profile` against its four existing installed identities; anonymous reads use a non-mutating reader view. Unsupported profiles/scopes return 403. Workspace reads for workflows/configurations, runs and Operations require their projected surface. Concierge reads/cancel/confirmation and retained Operations transcripts require the recorded owning actor, in addition to surface permission where applicable. A public demo selector is not authentication.

The four scoped case reads continue to return business state and exact evidence/decision outcomes, with trace identifiers removed and non-operator workspace configuration excluded. Source/MCP access, immutable approval and execution contracts are unchanged. Capability booleans are output only; mutation handlers still validate actual actor, object, source versions and readiness.

## Phase 10.2 — Read-only Agent workspace

`GET /control-api/agent-workspace` projects existing scoped run/checkpoint/activity and cached health metadata. It uses the Phase 10.1 capability resolver and installed `CUST-FML01` / `PRG-A17` case allowlist. Optional `run_id` selects an exact permitted run or `all`; omitted selects active work, then latest recorded work. Optional scope parameters must match the installed scope. This endpoint cannot initiate model/source probes, writes, approval or execution. See [field/state/freshness mapping](PHASE10_2_AGENT_WORKSPACE.md) and [OpenAPI snapshot](phase10-2-host-openapi.json). Business inspectors omit technical payloads and expose Operations links only through existing capability authority.

## Phase 10 — bounded autonomous Manufacturing event

The [autonomous-opening request](../prompts/10_AUTONOMOUS_OPENING.md) adds exactly
one read-only business endpoint: `GET /manufacturing/quality-events/{event_id}`.
It returns strict `QualitySourceEvent`, requires existing bearer identity/program
scope, and exposes the source-owned immutable QE-011 receipt. Public business
operations are now 58; the number of POST operations and agent tools is unchanged.
No public source publication/reset route or event MCP tool is added.

The contract fixes `quality_exception_created`, version 1, QE-011, PRG-A17,
CUST-FML01, LOT-B-219 and `source_system=manufacturing`; it carries event ID, UTC
publication time, source version/update time, context digest and synthetic provenance.
Extra fields, arbitrary event/workflow names and unsupported versions are rejected.
Source records and the event are committed atomically by the explicit local demo
publisher. The dispatcher independently reads the event and current context over HTTP,
then invokes the existing quality workflow with a durable event/version/workflow key.
This event is provenance, not authorization to approve or release anything.

Demo-management-only host routes are GET /control-api/demo/autonomous and
POST /control-api/demo/autonomous/{enter,prepare,reset}, with {expected_epoch}.
The latest direct follow-up restores /enter: any scoped local demo viewer may
signal app entry; the host arms only a cleared QE-011 opening after checking its
baseline, epoch, journal and runtime readiness. Entry never resets records or
replays non-idle state. Concurrent tabs serialize and share one event. Source
publication retains its fixed QE-011 scope and existing automation actor; entry
does not grant a viewer any business write or approval capability.
Origin/action, source binding, DEMO_MODE/storage and epoch guards remain.
Prepare/reset additionally require operator/maintainer authority. Prepare resets
only QE-011, checks the golden baseline and arms one eight-second event. Host
process startup alone remains idle. Source publication and workflow cancellation drain
before scoped reset; full reset retains the existing busy refusal for unrelated
active work and succeeds once it settles.

QualityContext includes the existing approved investigation_destination procedure
for QE-011, establishing its real queue/owner binding without a new queue store.
QualityProcedure optionally carries an approved StandardQualityPolicy, exact
exception/lot/type/action/task and active queue/owner binding. QE-011 has typed
exception_type and requested_actions; its context includes conflicting open
exceptions. These inputs are included in the context digest. Both the host and
Manufacturing investigation POST enforce the deterministic rule. The only
touchless write is the existing Manufacturing QualityIntent investigation route.
No release, disposition, Planner recovery or commitment authority is added.

Canonical completion is handoff_verified, policy_route
standard_quality_investigation_handoff. Autonomous status is
touchless_handoff_verified; ineligibility is escalated. No canonical recovery
proposal or decision exists. Historical exact plans remain source-owned.

The shared host admits distinct cases concurrently, default 3, configured with
STRATOS_MAX_CONCURRENT_WORKFLOW_RUNS (1–8). Capacity returns 409
WORKFLOW_CAPACITY_REACHED without claiming the invocation; retry the same key.
Same-case work returns RUN_ALREADY_RUNNING; exact idempotent replays retain the
original run. Workspace responses carry workflow_id and invocation_source and
select exactly one permitted run. Generic saved automations remain inactive.
See [current entry/roster handoff](PHASE10_AUTOMATIC_TOUCHLESS_ENTRY.md),
[touchless/concurrency handoff](PHASE10_TOUCHLESS_CONCURRENT_HANDOFF.md) and
[generated contract](phase10-autonomous-host-openapi.json).
