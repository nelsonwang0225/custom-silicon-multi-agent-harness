# Phase 08.4B — Connected quality recovery

QE-004 now uses the existing WorkflowService, CaseHarness, Program Coordinator,
specialists, ActivityStore and host HTTP gateways. There is no second model
runtime, background listener or new agent write tool. The workflow is connected;
automated verification uses deterministic SDK responses across real loopback
HTTP and MCP. No paid model or semantic-grader run was performed.

## Source ownership and stable references

All additions are synthetic and installed explicitly from
`fixtures/quality_exception.json` by the developer-only `install-quality-case`
command. Original CR-017/CR-019 records, approvals, jobs and commitments are not
replaced. Existing primary order ORD-1204 (100 units) and milestone MS-ACCEPT-01
remain distinct from the additional QE customer order and milestone.

| Owning system | Authoritative records |
|---|---|
| Manufacturing | QE-004 exception and request provenance; LOT-B-204 affected lot and quality hold; LOT-B-203 alternate lot; MAT-B-204 / MAT-B-203 quantity and eligibility records; OBS-QE-004 final-test observation; BASE-FT-B-72 approved comparison population |
| Engineering | Existing CFG-B-01 / REV-B configuration; new PROC-QE-B-01 approved standard investigation procedure, tasks, queue and recovery owner |
| Validation | Existing RES-BASELINE-B historical validation result; relevant context only, never lot release evidence |
| Program Planner | Existing PRG-A17; new MS-HEL-800 readiness milestone; generated recovery-task-* record after exact human approval |
| Commercial ERP | ORD-HEL-800, quantity 800, due 2026-11-23T18:00:00Z; read-only customer demand for this milestone |

Manufacturing also owns generated investigation-*, recovery-* plan and
recovery-decision-* records. Plans contain immutable analysis/proposal snapshots;
these are historical decision artifacts, not mutable inventory records. The
Planner task links the exact plan and source-recorded decision.

The control plane stores case/run/activity, source references, typed findings and
bounded operation attempts. Its QualityProgress contains source IDs, versions,
digests, decision intent and receipt/verification state. It does not store a
replacement lot, order, observation, procedure or inventory database. Case screens
read current operational facts through source HTTP APIs. Business fixtures and
developer eval variants are never agent-accessible files or document retrieval.

## Analysis and specialist responsibilities

The shared coordinator performs source-grounded intake. Its input event is built
from Manufacturing's exception provenance, linked lot/configuration/observation,
program, milestone and order. Browser inputs cannot supply actors or business
write arguments. Source-event configuration does not initiate a run.

Manufacturing confirms the lot, restrictions, related material and comparison
context. Validation confirms the configuration and named historical evidence,
interprets the approved investigation procedure, and preserves unresolved cause.
Program/Commercial reads the milestone and ERP demand. Shared intake/calculator
context is read once; the deterministic model double confirms domain-specific
records through each specialist's existing scoped tools. There is no requirement
to call every source system in every specialist step. Engineering expertise is
available only when a concrete technical question needs it.

A single added MCP tool, `get_quality_context(exception_id)`, exposes scoped
source context and ordinary-code calculations. The catalog has 27 read tools.
No new write tool is exposed to models. Existing CR-017 and CR-019 tool policies
retain their behavior.

Comparison checks configuration revision, test stage, program version,
conditions, equipment family, sites and population; the baseline must be approved
and contain a valid, sufficient comparison population. Mismatch returns **false**;
missing conditions/baseline returns **unknown**. Neither confirms degradation.
Both can still support a source-approved standard investigation. Typed specialist
and final claims must match the host calculator; exact JSON-pointer source facts
are validated. Source changes during reads or before writes require reassessment.

Base calculation: 200 / 250 = **80%**, versus 960 / 1,000 = **96%**. Site counts
are SITE-1: 5 failures and SITE-2: 45 failures. This concentration is correlation;
root cause is null. The entire 250-device lot is held, so its 200 first-pass passes
contribute **zero** eligible released devices. Other released/unallocated supply
is **600**; milestone demand **800**; current gap **200**. The calculator uses
source quantities, disposition and configuration applicability, not UI constants.

## Recovery and exact write boundary

The standard procedure supports evidence collection and a Product/Test
Engineering investigation queue. The recovery package compares that work with a
released-supply planning option, preserving the unresolved gap. Options include
scope, prerequisites, effect, owner, planned timing, quantity impact, unknown cost
and required authority. An allocation-tradeoff variant identifies harm to another
commitment, but provides no allocation executor.

| Source HTTP POST | Actor | Effect |
|---|---|---|
| `/api/v1/manufacturing/quality-investigations` | Automation | Create one source-defined investigation with exact lot, observation, program revision, evidence, tasks and queue |
| `/api/v1/manufacturing/recovery-plans` | Automation | Create an immutable, source-version-bound recovery proposal after investigation exists |
| `/api/v1/manufacturing/recovery-decisions` | Program Owner | Record approve/reject for the exact plan ID, version, digest and current source context |
| `/api/v1/programs/recovery-tasks` | Automation | Record one Planner recovery task after the exact authorized approval |

The primary human decision authorizes **recovery planning metadata using existing
released supply as context**, with investigation and the shortage still open. It
does not itself ship, reserve or allocate those units. The Program Owner public
local demo selector is separate from Engineering approver and Automation. These
are role-test personas, not production authentication or actual human approvals.

No endpoint permits quality disposition, held-lot release, thresholds, recipes,
nonstandard retest authorization, inventory reallocation or ERP commitment edits.
Quality lead, Engineering/Test, Supply/Program and Commercial authorities remain
separate. Original Phase 06 scheduling/Planner execution stays CR-017-only.

Each source write uses role checks, scoped foreign keys, a per-system transaction,
idempotency receipts, uniqueness and immutable records. The host persists an
attempt before HTTP and separately records action success and independent source
readback. Unknown outcomes are reconciled before retry with the original key.
Review and execute bind exact source plan references. Stale source input, rejection,
read failure and verification mismatch remain visible; no cross-system transaction
is claimed. Final verification confirms the lot/order inputs are unchanged.

## Product integration

- QE-004 case under Helios: comparison context, physical/eligible quantity visual,
  site evidence, unresolved cause, recovery options, exact review, handoff and
  independent verification.
- Overview and Program surface the source-backed exception and exposure. Recovery
  review becomes an attention item only after a plan exists; automated routing is
  not presented as a human approval request.
- Decisions uses actual source plans/decisions; Workflow catalog and run history
  show connected QE runs. Search finds the case, lot, evidence, work items, plans,
  decisions and runs. Alerts reflect source exception and host failures/review.
- Source views are available at `/<system>/quality/QE-004`, where system is
  `manufacturing`, `engineering`, `validation`, `programs` or `erp`.
- Concierge contextual suggestions remain explicit Preview replies.

| Capability | State |
|---|---|
| CR-017 exact approval/execution | Connected, preserved |
| CR-019 standard intake | Connected, preserved |
| QE-004 quality recovery | Connected |
| Automated model responses in test runs | Deterministic test doubles; real source HTTP/MCP |
| Yield Exception Watch | Saved configuration; connected workflow; trigger listener not active |
| Delivery Readiness / DR-009 | Preview only |
| Freeform Concierge / Operations | Preview only |

## Verification and manual paths

See `PHASE08_4B_VERIFICATION.json` for exact commands, results and file inventory.

| Verification | Result |
|---|---|
| Source API regressions | 458 passed |
| Complete coordinator suite, including Phase 06 and 08.4A | 650 passed |
| Final quality / Phase 07 runtime rerun | 28 passed |
| MCP discovery, scopes and HTTP integration | 56 passed |
| Offline evals, including 14 critical connected QE probes | 77 / 77; hard gates PASS |
| Browser / component scenarios | 68 unique scenarios passed across base, connected, CR-019 and three QE variants |
| Typecheck and production build | Passed; main JavaScript chunk has a 506.24 kB size advisory |

Three legacy browser assertions still expected Yield to be Preview. The corrected
tests passed in targeted reruns; the verification record retains the original
results and their corrections. Final QE browser runs cover comparable,
incomparable and no-alternative-supply scenarios, search, alerts, Overview, actual
run history, decisions, source views, exact role checks and mobile overflow.
The [primary case capture](screenshots/phase08-4b/comparable.png),
[incomparable capture](screenshots/phase08-4b/incomparable.png), and
[no-supply capture](screenshots/phase08-4b/no_alternative_supply.png) show source
readback after the scripted human-role review. Prior-phase captures were restored.

The Phase 07 extension contains 14 critical QE checks: comparable/incomparable
signal, correlation restraint, held-material exclusion, 600/800/200 arithmetic,
release and quality authority, allocation authority, unchanged commitment,
standard routing, wrong scope, fabricated/missing evidence and truthful final
source disposition. Original eval cases and hard-gate graders remain in place.
Variants include changed program revision, missing conditions/evidence, no alternate
supply, allocated alternate supply and mid-case source changes. Fault probes cover
unknown committed/uncommitted outcomes and failed/mismatching readback.

For a repeatable local browser demonstration with **no paid model**, from repo root:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase08_4b.serve
```

In a second terminal:

```sh
cd mock_apps_ui
MOCK_API_URL=http://127.0.0.1:18041 CONTROL_HOST_URL=http://127.0.0.1:18086 npm run dev -- --port 5177
```

Open `http://127.0.0.1:5177/control/programs/PRG-A17/cases/QE-004`. Log in as
Program operator, run investigation, inspect the routed work and recovery plan,
switch to Program Owner, approve/reject the plan, and execute the approved task.
Refresh Manufacturing and Planner source views. The lot stays held and customer
commitment unchanged. `--variant incomparable` or `--variant no_alternative_supply`
selects an isolated alternate scenario when starting the fixture server.

For a later **explicit paid connected model run**, use the existing authorized
runtime and configuration, without printing credentials. Stop only the source
service owning the chosen demo DB before its additive install. For the repository's
default `.demo/enterprise.sqlite3`:

```sh
DEMO_MODE=true PYTHONPATH=src .venv/bin/python -m mock_enterprise install-quality-case
DEMO_MODE=true PYTHONPATH=src .venv/bin/python -m mock_enterprise serve --port 18008
```

Start the existing scoped reader MCP and live control host in separate terminals:

```sh
PYTHONPATH=src mcp_server/.venv/bin/python -m stratos_mcp --port 19082 --backend-url http://127.0.0.1:18008 --program-id PRG-A17 --customer-id CUST-FML01
DEMO_MODE=true PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.control_host --source-url http://127.0.0.1:18008 --mcp-url http://127.0.0.1:19082/mcp --metadata-dir .cache/phase08-4b/live-metadata --port 18082 --ui-origin http://127.0.0.1:5188
```

Point Vite at those source/host ports:

```sh
cd mock_apps_ui
MOCK_API_URL=http://127.0.0.1:18008 CONTROL_HOST_URL=http://127.0.0.1:18082 npm run dev -- --port 5188
```

Open QE-004 and explicitly click **Run connected investigation** once. Only that
invocation loads the existing model setup. Check recorded source references,
comparison, correlation restraint, arithmetic, human boundary and readback. Do
not launch another service over occupied ports; existing demo DBs are never reset
by this handoff. No paid run was executed during implementation.

## Limits and next step

The source environment is synthetic and local. The comparison policy is an exact
context match, not statistical process qualification. Site concentration cannot
establish physical cause. Cost and completion timing remain unknown where sources
do not model them. The workflow routes work; it does not run tests or close the
investigation. The primary recovery task records planning only, not inventory
allocation, shipment or quality disposition. Prose checks are defense in depth;
live model reasoning and optional semantic grading remain unmeasured.

The existing running demo was not reset. Explicit installation/restart is required
for a demo database that does not yet contain QE-004; isolated verified browser
fixtures already contain it. Stop at 08.4B. The next authorized slice, only when
requested, is **08.4C Delivery Readiness**: connect readiness and eligible supply to
source-owned customer demand and separate consequential commitment/allocation
review. No 08.4C execution, event listener, connected freeform chat, Operations,
Phase 09 polish, branch, commit or push was implemented.
