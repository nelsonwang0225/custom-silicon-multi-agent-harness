# Phase 06 — Human Approval & Execution

Implemented only for CR-017 / CUST-FML01 / PRG-A17 and
`requirement_change_analysis` definition 1. The result is **approved validation
work scheduled and independently verified**. The change remains open/in validation;
physical results, engineering disposition, hardware adequacy and customer acceptance
remain unresolved. No Phase 07/08 work, touchless execution, additional workflow,
agent write tool, model routing, new dependency or source API permission was added.

## Baseline inspected

The source contracts already provided:

- `src/mock_enterprise/schemas.py`: immutable `Plan`, separate mutable `PlanState`,
  exact `Decision`, `JobInput`, `LinkInput`, job/reservation and link/task views.
- `domains/engineering.py`: draft-plan creation and engineer-only decisions.
  A source `Decision` is **business authorization** for that source plan; `PlanState`
  is source application state. Neither proves review of a workflow envelope.
- `domains/validation.py`, `domains/planner.py`, `approvals.py`, `snapshots.py`:
  source authority, calculated eligibility, immutable content digests, resource
  provenance, per-system transactions, source idempotency and uniqueness.
- `application/contracts.py`: `Proposal`, `DecisionBinding`, pure validators and
  separate action/verification schemas. A retained record alone grants no authority.
- `application/store.py`: atomic JSON case/run/activity index and process locking.
- `CaseHarness`: existing SDK orchestration and validated `FinalDecisionPackage`;
  JSON investigation checkpoints, no pending approval tool call or durable SDK
  session awaiting resumption. The single-agent investigator is separate.
- Source identities: three fixed public mock selectors, server-mapped to scoped
  reader/automation/engineer personas. CR-017's delegated engineer can authorize
  the approved procedure and up to 200,000 cents. This is a synthetic policy.
- Options: priority is 180,000 cents, review-ready Nov 18 20:00Z; standard misses
  the deadline; the alternate lab is unqualified. These remain source calculations.

The source, client, MCP, specialists, policy branches, workflow registry and existing
tests were inspected. All existing assertions remain unchanged. There is no Git
metadata; no branch, commit, push or history operation was performed. Pre-edit hashes
and an inspection brief are in `.cache/phase06/`.

## Architecture and pause/resume

`ExecutionService` extends the existing application boundary after `WorkflowService`
finishes its SDK investigation. The same CLI now supports proposal preparation,
inspection, human review and resume. Future interfaces should call these services;
there is no new HTTP application, chat interface or second agent runner.

The existing recommendation has an unranked list of typed options. Preparation
selects the least-cost eligible on-time option, then earliest review and stable IDs,
or accepts an explicit slot/sample pair present in the recommendation. It does not
parse recommendation prose to discover authority or arbitrary arguments. Fresh HTTP
options, coverage, available reference versions and source calculation must agree.
The source server creates the actual immutable draft; the host GETs it back and
adapts it into the exact proposal. Preparation persists its request before POST and
uses one stable idempotency key, including after a lost draft response.

The durable pause is **after a completed SDK result**, at the host workflow boundary.
The completed analysis run stays `completed` and its recommendation stays read-only.
A separate `ExecutionRecord` progresses through `proposal_ready`,
`waiting_for_approval`, `approved`/`rejected`, `resuming`, `executing`, `verifying`,
then `completed_execution` or a failure/attention state. Activity records preserve
intermediate business events, including proposal creation and approval request.

No SDK `RunState` is fabricated and no in-memory chat is required. There is no
interrupted model tool call to approve here: specialist/Coordinator tools remain
read-only. `resume` loads the persisted proposal, review, source decision and action
states, then performs deterministic source execution without another model call.
The [official SDK results/state guide](https://developers.openai.com/api/docs/guides/agents/results)
distinguishes completed `final_output` from pending tool `interruptions` and
`to_state()`; the installed `openai-agents==0.22.2` state implementation was inspected.
This implementation uses the completed-result boundary. If future work adds a
model-owned consequential tool, its SDK interruption must be separately persisted
and gated by this same service; that is not implemented or needed for Phase 06.

```mermaid
sequenceDiagram
    participant D as Developer / trigger
    participant W as WorkflowService + existing SDK harness
    participant E as ExecutionService / ActivityStore
    participant H as Trusted demo reviewer
    participant G as Engineering HTTP API
    participant L as Validation HTTP API
    participant P as Planner HTTP API
    D->>W: CR-017 analysis
    W->>W: Coordinator + scoped specialists
    W->>E: Persist validated recommendation
    E->>G: Create immutable calculated draft; GET back
    E->>E: Persist exact proposal / manifest; pause
    H->>E: Approve or reject exact version + digest + scope
    E->>E: Persist trusted review intent
    E->>G: Exact plan decision as engineer; GET decision
    E->>E: Bind source decision to reviewed envelope
    D->>E: Resume (may be a new process)
    E->>E: Validate current proposal, policy, evidence and approval
    E->>L: Exact approved scheduling request
    E->>L: Independent GET job / reservation
    E->>E: Separate verification record
    E->>P: Exact approved job link + Planner CAS
    E->>P: Independent GET link / task / milestone
    E->>E: Separate verification; completed_execution
    E-->>D: Case in validation; wait for physical results
```

## Exact proposal and human authority

The existing `Proposal` is extended additively with creation time, ordered typed
manifest and complete Planner milestone before-image. Empty new fields preserve
legacy proposal digests. The envelope binds program/customer/case/workflow/version/
originating run, immutable source plan/version/digest, selected option/configuration/
procedure/sample/slot, integer USD cost, UTC schedule, evidence/source snapshots,
rationale, assumptions, prerequisites and required policy/role.

SHA256 canonical JSON binds all of those fields. Every use recomputes both envelope
and source-plan digests and regenerates the manifest from the source plan. Nested
mutation is detected even though Python's outer frozen model cannot freeze a nested
dictionary. Material revisions create a new source plan ID, increment the envelope
version, retain lineage and mark the preceding execution proposal superseded.
Existing source decisions and source plans remain immutable. Revision after an
attempted consequential action is deliberately blocked pending reconciliation.

The CLI review command is a **trusted local demo actor boundary**, using fixed
host-installed contexts aligned with the existing source identity map. It accepts
an explicit decision and exact proposal reference; it has no role/actor override.
`ExecutionService` accepts only the actual host-installed identity objects, not an
arbitrary object with matching fields. Source Engineering independently validates
the engineer selector. The engineer capability is never installed in agents or MCP.
These public selectors are role tests, **not real authentication or proof of a
particular human**. A person running the documented review command performs the
trusted demo review; automated tests label that same persona as simulated.

A `HumanReview` intent is persisted before contacting Engineering, with proposal
reference, actor, authority source, policy/version, approve/reject, comment and UTC
recording time. The source decision reason includes the exact envelope digest.
After POST, an independent GET must match before creating `DecisionBinding` and
marking the review approved/rejected. A pre-existing source approval cannot be
adopted as envelope review. A lost review response resumes the same intent/key.
A pending review may be superseded before any execution attempt; any late source
decision still belongs only to the old proposal and cannot authorize the replacement.

Execution checks the complete scope, current source change/plan, current envelope,
review decision and binding, signer, policy, source versions/evidence set, resource
eligibility and exact Planner before-image. Source handlers independently check
content digests, freshness and reservation ownership in their write transactions.
A race after the host's reads is therefore still denied by the source system.

## Exact write boundary

| Operation | Authority / effect |
|---|---|
| `create_implementation_plan`: POST `/engineering/changes/CR-017/plans` | Host automation prepares a source-calculated immutable draft; no scheduling authority |
| `record_plan_decision`: POST `/engineering/plans/{id}/decisions` | Trusted human-review host only; exact source plan and reviewed envelope binding |
| `schedule_validation_job`: POST `/validation/jobs` | After approved manifest validation only; one job plus its source reservation |
| `link_approved_validation_plan`: POST `/programs/PRG-A17/implementation-links` | After verified scheduling only; one task/link/dependency and conditional forecast |

The last two are the only consequential execution actions agents' recommendations
can cause. No agent directly receives any of these mutation capabilities. The
existing `EnterpriseClient` and all 25 MCP tools stay read-only. The HTTP adapter
lives in `program_coordinator/infrastructure/`; application logic depends on an
injected source adapter and imports no HTTP client or SDK runtime.

Still prohibited: manufacturing recipe/hold/release/quality changes, test results or
thresholds/criteria edits, inventory allocation, ERP/customer commitments,
communications/email, arbitrary CRUD, touchless CR-018 execution, yield recovery
and delivery readiness. Source APIs and OpenAPI remain unchanged.

## Manifest, retry and partial failure

Each manifest entry has action ID, sequence/dependency, operation, system, route,
exact body template, stable source key, approval reference and expected result.
Only two references are resolved: `$approval.id` from this exact recorded review,
and `$schedule.resource_id` from this proposal's verified scheduling step. These
references and the full Planner CAS integer are approved before execution. No
model text, latest recommendation or newly supplied job ID can fill them.

The service regenerates and compares the manifest, resolves a typed `JobInput` or
`LinkInput`, checks any requested invocation for exact operation/target/arguments,
and persists the resolved request and `started` attempt before the POST. A global
local execution lock serializes review/revision/resume without holding a JSON
transaction over HTTP; competing processes get `EXECUTION_BUSY`. Process death
releases the operation lock and leaves durable started markers.

Action states distinguish not attempted, started, succeeded, failed, unknown and
already completed. Attempts are historical records with source/request IDs and
outcomes. Verification is a separate collection; a successful POST does not imply
a matched verification. Identical source keys and scoped source uniqueness prevent
duplicate jobs/tasks. Succeeded steps are GET-verified on resume, never POSTed again.

- A failed preflight read records attention required and preserves verified steps.
  A definite rejected write records failure; retry repeats only the incomplete
  step and exact request/key, after all authorization checks.
- A timeout, 5xx, malformed successful response or crash after `started` is an
  unknown outcome. The service reads the source plan and the referenced job/link,
  then independently verifies it. A matching resource becomes `already_completed`.
- If an unknown outcome cannot be established by readback, it remains
  `attention_required`. **No blind retry** is offered. There is no cancellation,
  compensating rollback or inferred absence guarantee. Developer/source-owner
  reconciliation is required; a generic force/retry override was not added.
- If scheduling succeeds and Planner fails, the job and reservation survive, the
  failed step and IDs remain visible, and the execution is partially complete.
  A transient definite failure can retry Planner alone. If source content or the
  exact Planner CAS/before-image changes, the old proposal becomes stale. The
  service will not silently change CAS arguments; a partially executed stale plan
  needs manual reconciliation, not automatic new scheduling or compensation.

## Independent verification and downstream state

After scheduling, GET the job/reservation and compare scope, plan and approval,
plan digest, option/configuration/procedure/workload, sample, slot, lab, cost,
all timing/review parameters, scheduled status and exact reservation provenance.
The source schema has no job owner field; no owner is invented.

After linking, GET the link/task and milestone separately. Check exact plan/job/
approval/program/change linkage, task identity/name/status/forecast, milestone
version transition and the expected dependency/conditional forecast changes.
The entire milestone is compared with the approved before-image plus the permitted
changes, including owners and baseline. Optional fields use source schema defaults.
Each verification stores matched/mismatch/inconclusive, source references,
recording timestamp and a concise observation. Failed/inconclusive verification
preserves successful action receipts and source IDs, stops further work and
requires investigation or a fresh readback.

Successful end state:

| Meaning | Persisted value |
|---|---|
| Execution | `completed_execution` |
| Case | `in_validation` (still open) |
| Validation plan | `approved_and_scheduled` |
| Coverage | `pending_test_results` |
| Hardware adequacy | `unvalidated` |
| Customer acceptance | `pending` |
| Existing source execution state | `scheduled_awaiting_execution` |

Engineering's baseline requirement, requested revision status, test observations,
manufacturing records and ERP commitment are unchanged. Original baseline dates
remain distinct from the conditional forecast. No pass/acceptance flags can be set
in the verification contract. The original read-only recommendation remains an
analysis artifact; execution does not rewrite it to claim approval or testing.

## Activity and storage

The existing `workflow-index.json` gains typed preparations, review intents,
execution records and attempts; proposals, decision bindings, verifications and
activity remain in their existing collections. Atomic replacement and fsync retain
metadata across process restart. The source SQLite file is never opened by runtime
application code. Developer-only tests/initialization use isolated storage.

Activity includes proposal creation/supersession, approval request/decision/staleness,
resume, action start/success/failure/unknown/reconciliation, verification start/
result, partial completion and completion. Events record trusted actor or host
identity, source IDs, policy/reference/digest, UTC time and the originating run/trace.
No hidden reasoning or credential values are stored. Technical SDK checkpoints and
trace artifacts remain separate. An analysis crash before its final output retains
the pre-existing conservative `running` claim behavior; Phase 06 does not reconstruct
an interrupted investigation. Recovery described here starts at the durable proposal
boundary.

## Developer demonstration

Use the existing CLI; `DEMO_MODE=true` is required for Phase 06 source access.
Run from the repository root. The scripted verification starts and stops its own
source server and creates a fresh `.cache/phase06/http-*/` database and metadata:

```sh
TMPDIR="$PWD/.cache/tmp" .venv/bin/python coordinator/evals/verify_phase06.py
```

It runs the **existing** coordinator/specialist harness with deterministic test
outputs, then uses real HTTP and separate CLI processes for preparation, denied
pre-approval execution, simulated human approval, source restart, execution,
readback and replay. It is not a paid AI run or authenticated human review.
`phase06_offline_analysis.py` is a developer-only fixture bridge in `coordinator/evals/`;
neither verification script is runtime retrieval or an agent-accessible tool.

An optional later live smoke, against fresh isolated source/MCP services, is:

```sh
# PAID model analysis: deliberately NOT run during Phase 06 verification.
DEMO_MODE=true PYTHONPATH=src coordinator/.venv/bin/python -m program_coordinator \
  --event coordinator/scenarios/human_review.json \
  --invocation-id cr017-live-06 --metadata-dir .cache/phase06/live/activity \
  --mcp-url http://127.0.0.1:9010/mcp --source-url http://127.0.0.1:8000 \
  --prepare-execution --preparation-id cr017-live-proposal-06

# Inspect persisted runs and full proposals without model calls.
DEMO_MODE=true PYTHONPATH=src coordinator/.venv/bin/python -m program_coordinator \
  --phase06 inspect --metadata-dir .cache/phase06/live/activity
```

The analysis output returns the exact proposal reference. Read the full proposal,
including cost, schedule, manifest and uncertainty. The same CLI supports:

```sh
# Substitute the exact inspected values, not "latest". All reference fields
# are required for review and resume. Run these as separate intentional steps.
DEMO_MODE=true PYTHONPATH=src coordinator/.venv/bin/python -m program_coordinator \
  --phase06 review --decision approve --comment 'Reviewed exact proposed validation work.' \
  --metadata-dir .cache/phase06/live/activity \
  --run-id RUN_ID --case-id CASE_ID --proposal-id PLAN_ID \
  --proposal-version 1 --proposal-digest EXACT_DIGEST

# Use --decision reject instead to exercise the non-executing rejection branch.
# With the same exact reference/metadata options, run --phase06 resume, then
# --phase06 inspect to observe attempts, readback, activity and downstream state.
```

For an existing completed analysis, use `--phase06 prepare --run-id RUN_ID
--preparation-id STABLE_ID`; optional `--slot-id` and `--sample-id` select a typed
eligible option. A material revision uses a new preparation ID and the full old
reference with `--supersedes-proposal-id OLD_PLAN_ID`. It cannot reuse approval.
No CLI command approves whatever is currently recommended. Source URLs remain
loopback-only and redirects are disabled. The host source URL must refer to the
same synthetic enterprise generation investigated by MCP; version/option checks
fail closed on observed differences, but no cross-service deployment identity
attestation exists in this local demo.

## Limitations and next phase

Public mock selectors and a trusted local CLI are not production identity assurance.
Metadata is private local JSON, not tamper-proof storage against the machine owner.
One local operation lock and one JSON index suit this demo, not a distributed
service. There is no distributed source snapshot/transaction or global rollback.
Source transaction checks remain essential for races and critical content hashes.
Unknown absent outcomes and CAS drift after partial execution require manual
reconciliation. No auto-expiry, scheduler, notifications, job cancellation,
physical test execution/result simulation, acceptance or case-closure path exists.
No live-model proof was produced in this implementation phase.

The exact next Phase 07 step is to define the reliability/evaluation specification
for this now-implemented lifecycle: datasets/graders for grounded proposals,
approval-policy violations, stale evidence, interruption/retry recovery and truthful
execution/verification claims. Run the small optional live smoke separately when
wanted. Phase 07 evaluation infrastructure itself has not been started. There is
no blocker to the bounded deterministic Phase 06 path.

## Verification and changed files

Final command results, counts and complete changed-file inventory are recorded
below after verification; machine-readable details are in `.cache/phase06/verification.json`.

| Changed/new file | Purpose |
|---|---|
| `src/program_coordinator/application/contracts.py` | Additive proposal creation time, manifest and milestone before-image; legacy digest preservation |
| `src/program_coordinator/application/models.py` | Extend existing activity event vocabulary |
| `src/program_coordinator/application/store.py` | Reuse metadata index for typed execution records; independent process operation lock |
| `src/program_coordinator/application/demo_identity.py` | Fixed trusted host demo contexts matching existing source identities |
| `src/program_coordinator/application/execution_models.py` | Exact references, preparations, review intents, execution steps/attempts and downstream state |
| `src/program_coordinator/application/execution_policy.py` | Fixed action manifest, reference resolution and independent expected-state comparisons |
| `src/program_coordinator/application/execution.py` | Shared preparation, review, safe resume, enforcement, recovery and verification service |
| `src/program_coordinator/application/execution_cli.py` | Phase 06 operations in the existing CLI; no model/key calls |
| `src/program_coordinator/infrastructure/__init__.py` | Host infrastructure package boundary |
| `src/program_coordinator/infrastructure/source_gateway.py` | Typed local HTTP mutations and existing read-client adapter; separate human capability |
| `src/program_coordinator/__main__.py` | CLI flags/dispatch and optional prepare-and-pause after existing analysis or replay |
| `tests/test_phase06_execution.py` | 69 deterministic governance, source transaction, recovery, verification and boundary tests |
| `coordinator/tests/test_phase06_cli.py` | Eight offline CLI/analysis-replay integration checks |
| `coordinator/evals/phase06_offline_analysis.py` | Developer-only bridge through existing CaseHarness and specialist test doubles |
| `coordinator/evals/verify_phase06.py` | Real local HTTP and CLI process/restart smoke in fresh isolated cache storage |
| `prompts/06_HUMAN_APPROVAL_EXECUTION.md` | Exact authorized user request retained outside runtime retrieval |
| `AGENTS.md` | Add Phase 06 authorization without replacing historical constraints |
| `README.md` | Current capability summary and handoff link |
| `coordinator/README.md` | CLI path and interpretation of host execution versus read-only agents |
| `docs/WORKFLOW_COMPATIBILITY_HANDOFF.md` | Mark historical handoff and link current Phase 06 work |
| `docs/MULTI_AGENT_HARNESS_HANDOFF.md` | Preserve historical agent evidence and link current continuation |
| `docs/HUMAN_APPROVAL_EXECUTION_HANDOFF.md` | This architecture, demo, failure semantics and verification handoff |

All nine modified pre-existing files are listed above; thirteen files are new.
No files were removed. Hash comparison confirms existing tests, business source/
OpenAPI, fixtures, enterprise client, MCP server/tools, source UI, single-agent
baseline, coordinator specialists/runner/policy and workflow registry are unchanged.
No lockfile/dependency change was made.

The required A–Q governance coverage is in `tests/test_phase06_execution.py`:
A/B zero writes without approval or with wrong/forged reviewer; C exact scope;
D tampering; E/H revised and superseded proposals; F material evidence/source
changes; G rejection; I/J/K action/argument/target/operation enforcement; L/M
normal writes once and replay; N partial source-transaction failure and recovery;
O independent mismatch/inconclusive verification; P durable review/crash/restart;
Q illustrative workflows. Additional tests cover unknown outcomes, lost responses,
external approvals, touchless denial, source races, CAS drift, protected records,
no redirects/retries and concurrent execution exclusion.

Final verification commands (all from the repository root):

| Check | Command/Test | Result | Evidence |
|---|---|---|---|
| Source + runtime + governance | `TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q tests runtime_checks/test_openai_connection.py --tb=short` | PASS: 388 | `.cache/phase06/source-final.log`; 319 existing + 69 new tests |
| Coordinator + CLI | `TMPDIR="$PWD/.cache/tmp" coordinator/.venv/bin/python -m pytest -c coordinator/pyproject.toml coordinator/tests -q --tb=short` | PASS: 179 | `.cache/phase06/coordinator-final.log`; 171 existing + 8 new tests |
| MCP regression | `TMPDIR="$PWD/.cache/tmp" mcp_server/.venv/bin/python -m pytest -c mcp_server/pyproject.toml mcp_server/tests -q --tb=short` | PASS: 56 | `.cache/phase06/mcp.log`; implementation unchanged |
| Single-agent baseline | `TMPDIR="$PWD/.cache/tmp" investigator/.venv/bin/python -m pytest -c investigator/pyproject.toml investigator/tests -q --tb=short` | PASS: 39 | `.cache/phase06/investigator.log`; implementation unchanged |
| Scripted localhost lifecycle | `TMPDIR="$PWD/.cache/tmp" .venv/bin/python coordinator/evals/verify_phase06.py` | PASS: one job and one Planner link | `.cache/phase06/http-smoke-final.log`; per-command JSON, source restart and readback |
| Python compile | `coordinator/.venv/bin/python -m compileall -q src/program_coordinator coordinator/evals/phase06_offline_analysis.py coordinator/evals/verify_phase06.py` | PASS: exit 0 | Tool output; compiled final implementation |
| Locked environment compatibility | `UV_CACHE_DIR="$PWD/.cache/uv" uv pip check --python coordinator/.venv/bin/python` | PASS: 46 packages compatible | Tool output; no dependency changes |
| UI type check | `npm --prefix mock_apps_ui run typecheck` | PASS: exit 0 | Existing UI source unchanged |
| UI build | `npm --prefix mock_apps_ui run build` | PASS: 1,764 modules | Build exit 0; generated build cache refreshed |
| Preservation | SHA256 comparison against `.cache/phase06/before-hashes.json` | PASS | `.cache/phase06/file-changes.json`; no existing assertion changed |
| Paid/live-model smoke | Not run | SKIPPED by request | No key loading or paid model calls; no live-model proof claimed |
| Browser UI E2E | Not rerun | SKIPPED | No UI change; existing source/UI backend tests and type/build checks passed |
| Python lint/type checker | Not configured | NOT AVAILABLE | No new tooling/dependency introduced |

Prior development iterations found and fixed expected-state normalization for
optional milestone dependency fields, the placement of the host HTTP adapter,
preparation-replay status reporting, and attention reporting for a read failure
between completed and pending actions. Source immutability and existing assertions
were preserved. Final verification is deterministic/offline; the real HTTP smoke
uses simulated human identity and deterministic analysis outputs. The optional
paid live smoke remains separate, as requested.

Final totals: **662 passed, 0 failed, 0 skipped in pytest**. This comprises
585 existing regression tests and 77 new Phase 06 tests (69 source/application
governance checks and eight Coordinator CLI checks). The last combined source
suite passed 388 tests in 82.59 seconds; Coordinator passed 179 in 3.17 seconds;
MCP passed 56 in 11.89 seconds; ProgramInvestigator passed 39 in 1.48 seconds.

The final scripted HTTP run produced one job and one Planner link, two write
attempts and four matched verification records (including explicit replay
readback). It exercised source-server restart and fresh CLI processes. The
per-command receipts, proposal, review, execution, inspection, source logs and
report are retained at `.cache/phase06/http-4a9ded1d16734f3a8e319d1cf3d0117a/`.
No model call, authenticated human approval, physical test or acceptance claim
was part of this proof. Phase 06 is complete at this bounded stopping point.
