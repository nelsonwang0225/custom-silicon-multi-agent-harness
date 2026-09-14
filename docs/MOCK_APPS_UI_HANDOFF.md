# Current portfolio enrichment handoff

The data-volume and enterprise-UX phase is documented in
[DATA_ENRICHMENT_HANDOFF.md](DATA_ENRICHMENT_HANDOFF.md). It supersedes the older
single-program counts and preview addresses below. Nine fictional customers and
eleven programs now populate all five source systems; CR-017 keeps its exact
approval/scheduling behavior. The expanded queues, filters, milestone navigation,
historical-execution views and source-bound workflows use real HTTP records.

**UI AND API INTEGRATION READINESS: PASS.** Current enrichment verification:
214 backend tests passed in 48.06s; 20 browser tests passed in 2.1m; scenario/data
validation, frontend typecheck and production build passed. The full manual CR-017
workflow and a separate scripted HTTP write were verified through refresh/reopen.
All five apps were reviewed at 1440×900 and 1280×800 using isolated databases;
the user's active database was not reset. No AI runtime was added or run.

Fresh enriched walkthrough: [5183](http://127.0.0.1:5183/).
Completed manual example: [5182](http://127.0.0.1:5182/).
The linked handoff contains final tests, record counts, screenshots at both desktop
sizes, commands, database paths, limitations and the short human walkthrough.
Earlier evidence remains below as a historical record; it is not a current test claim.

---

# Mock application UI handoff — follow-up improvements

**UI AND API INTEGRATION READINESS: PASS.** Follow-up implemented September 10,
2026 from the user's attached review. This section describes the current result;
the earlier review, IDs and evidence are preserved below as historical context.

## Requested changes delivered

| Review item | Implementation and verification |
|---|---|
| Contradictory Engineering status | The case header/worklist separates current-plan decision from derived execution. The change detail API now exposes current-plan `execution_state`; jobs/links determine it without cross-domain writes. Tests cover unbooked, booked/pending Planner, linked, and an older booking beside a newer draft. |
| Validation options dead end after booking | “Work already scheduled” links to the real job and its Planner record, explains the one-outstanding-job sample reservation, and preserves visibility of earlier-plan bookings. No prominent draft action appears when no resource is eligible. Partial Planner follow-through remains the next action. |
| Launcher orientation | HTTP-derived case summary, workload request, baseline evidence deadline, distinct decision/execution, linked Assess → Approve → Schedule → Update Planner stages, and next action/responsible role. After linking, it says execution/review remain pending. |
| Richer human authoring | Up to 30 facts and 20 citations per fact, plus multiple gaps/questions under the existing API limits. Add/remove controls, explicit source selection, source previews, persisted unfinished forms, and exact retry metadata. Earlier single-fact forms remain readable. Document previews prioritize the actual document; plan review previews the immutable captured source, not a substituted live version. |
| Plan revision workflow | “Create revised plan” copies assessment text/citations, requires explicit resource reselection, submits `supersedes_plan_id`, shows lineage and changed scope/assessment/sources, and requires fresh approval. The browser test approves an initial plan, creates a revision, proves the old approval cannot book it (403), then records a separate exact-plan approval. The earlier plan is unchanged. |
| Integration activity visibility | Expandable Engineering/Planner events show request/correlation IDs, safe idempotency hash, affected resource, before/after field changes, and links to recorded decision, job and Planner record. Anchors reveal the actual destination. Denials/replays remain distinguishable. |
| Manufacturing / ERP context | Persisted optional hold rationale, responsible team and release conditions; persisted rate service names/descriptions. The supplied fictional context is consistent with existing restrictions and amounts. The APIs remain read-only. Older databases explicitly report absent descriptions. |

No AI calls, agent harness, new business workflow, external service, dependency,
public mutation endpoint or Git operation was introduced. Existing approval,
idempotency, concurrency, per-system transaction and evidence controls remain.
The descriptive fixture additions are explicitly documented in SCENARIO.md and
API_CONTRACT.md; six allowlisted business documents and scenario calculations are
unchanged. Optional descriptive columns exist in new databases; existing files are
readable without automatic migration. Empty defaults do not invalidate old signed
source snapshots, and supplied context remains protected by source binding.

## Actual checks for this follow-up

| Command/check | Actual result |
|---|---|
| `TMPDIR="$PWD/.cache/tmp" .venv/bin/pytest -q` | **197 passed in 34.28s**, zero failures/skips. Four added follow-up regressions cover derived state, prior bookings, legacy-file approval compatibility and protected descriptive context. |
| `.venv/bin/python scripts/validate_scenario.py` | PASS: 42 records, 110 references, six documents, nine options, six rejected corruption probes. |
| `npm --prefix mock_apps_ui run typecheck` | PASS. |
| `npm --prefix mock_apps_ui run build` | PASS; 1,762 modules; 480.11 kB JS / 19.13 kB CSS before compression; build completed in 1.04s. |
| `PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix mock_apps_ui run test:e2e` | **16 passed in 38.8s**, zero failures/skips. All successful workflow writes crossed real local HTTP. |
| Focused browser follow-up `... run test:e2e -- enhancements.spec.ts` | Two passed in 11.0s after the source-control label fix. Multi-fact creation, revision/fresh approval, source preview HTTP/error handling, context and both desktop sizes. |
| Manual in-app browser | Inspected the fresh launcher and live source preview, and the preserved scheduled case's separate decision/execution labels, booked-options guidance and expanded Planner event. The existing database's new API projection reports `scheduled_awaiting_execution`. |
| Preserved preview restart | Seven HTTP snapshots matched after restart (allowing only the newly added derived execution field). The original database's SHA-256 was **identical**. No reset, migration or business mutation was performed on that file. |

The first full backend run found one overlap-test fixture that cleared a hold but
left its newly supplied explanatory detail behind. Its isolated setup now clears
both; the overlap-conflict assertions remain unchanged. The initial browser check
found an exact-label lookup ambiguity on the citation select; an explicit accessible
label fixes the control. Typechecks caught an unknown-value JSX condition and a
comparison component referencing a generated type name that had separate input/output
variants; both were corrected before the final passing type/build checks. A stylesheet command initially used the
wrong relative directory and was rerun in the correct directory. Screenshot review
then moved document content ahead of metadata and compacted the revision comparison.
These failed development checks are not counted as passes.

Logs and receipts: `.cache/ui-followup-backend.log`,
`.cache/ui-followup-browser.log`, `.cache/ui-followup-typecheck.log`,
`.cache/ui-followup-build.log`, `.cache/ui-followup-scenario.log`,
`.cache/ui-followup-preserved-preview.json`. The browser suite also regenerates
`.cache/ui-review-network.json` and `.cache/ui-review-scripted-api.json` for the
separate scripted API write/refresh check. No authorization headers are recorded.

## Two separate previews

| State | UI | API docs | Isolated database |
|---|---|---|---|
| Fresh walkthrough; zero plans/jobs | [Clean launcher](http://127.0.0.1:5181/) | [18011](http://127.0.0.1:18011/docs) | `.demo/ui-e2e-5b154254af134d14b47d6ec7beec42ac.sqlite3` |
| Preserved scheduled/linked example | [Scheduled launcher](http://127.0.0.1:5180/) | [18010](http://127.0.0.1:18010/docs) | `.demo/ui-e2e-14c9e98da0e4469b94a79e155290fbc0.sqlite3` |

The clean preview was created using `.venv/bin/python scripts/serve_ui_test.py 18011`,
which calls the guarded initialization command on a new unique path. Its frontend:
`MOCK_API_URL=http://127.0.0.1:18011 npm --prefix mock_apps_ui run dev -- --port 5181`.
Creating a separate file preserved the scheduled example without resetting it.
The clean file has the new descriptions; the preserved older file correctly lacks
optional descriptions that were never present in its persisted records.

To resume the clean file after stopping its owned process, use:

```sh
DEMO_MODE=true \
  DEMO_DB="$PWD/.demo/ui-e2e-5b154254af134d14b47d6ec7beec42ac.sqlite3" \
  .venv/bin/mock-enterprise serve --port 18011
# Separate terminal:
MOCK_API_URL=http://127.0.0.1:18011 npm --prefix mock_apps_ui run dev -- --port 5181
```

For a deliberate repeat, stop only this clean preview's API, then invoke the
existing guarded local reset **with its explicit file**, never the default working DB:

```sh
DEMO_MODE=true \
  DEMO_DB="$PWD/.demo/ui-e2e-5b154254af134d14b47d6ec7beec42ac.sqlite3" \
  .venv/bin/mock-enterprise reset-demo --yes
```

That reset is documented for the user; it was not run on either retained preview.
The backend suite independently exercises reset/lifecycle controls in isolated files.
The user's `.demo/enterprise.sqlite3` was not reset or mutated. Preview availability
is a point-in-time verification, not background monitoring.

## Short human walkthrough

1. Open the clean launcher. Read the request/deadline and inspect the customer document,
   historical evidence, Manufacturing hold context and ERP service descriptions.
2. Use **Open next step**, explicitly select **Program operator**, choose resources,
   add facts/citations, expand a source, and create an immutable draft.
3. Explicitly select **Engineering approver**, inspect the captured sources, scope,
   cost and timing, acknowledge the exact plan and record the simulated decision.
4. Before booking, optionally use **Create revised plan**. Reselect resources, edit
   the copied assessment and save. Inspect its lineage/changes; record a fresh
   approval. Previous approval never transfers. No cancellation/release workflow exists.
5. As operator, schedule the exact approved plan and complete its missing Planner link.
   Refresh/reopen the launcher, Engineering case and Validation options. They should
   show existing scheduled work; evidence remains incomplete and the ERP commitment
   and baseline deadline remain distinct from the conditional forecast.
6. Expand an Engineering or Planner **Event details** row, inspect before/after fields
   and request IDs, and follow the actual job/decision/Planner links.

## Follow-up screenshots and limits

Screenshots are developer artifacts outside business retrieval. Follow-up captures
cover the launcher, scheduled case/options, multi-fact form, revision comparison,
activity details, hold and ERP rates at **1440×900 and 1280×800**. Scheduled-state
images preserve the exact viewport; form/revision/context images are full-page
captures taken at those viewport sizes. The tests assert no page-wide horizontal
overflow. The complete five-app screenshots from the earlier matrix are regenerated
by the suite as well.

| Follow-up screen | 1440 width | 1280 width |
|---|---|---|
| Clean case summary | [Launcher](ui_screenshots/followup-launcher-clean-1440.png) | [Launcher](ui_screenshots/followup-launcher-clean-1280.png) |
| Scheduled case summary | [Launcher](ui_screenshots/followup-launcher-scheduled-1440.png) | [Launcher](ui_screenshots/followup-launcher-scheduled-1280.png) |
| Corrected Engineering status | [Change](ui_screenshots/followup-change-scheduled-1440.png) | [Change](ui_screenshots/followup-change-scheduled-1280.png) |
| Existing-work options | [Options](ui_screenshots/followup-options-scheduled-1440.png) | [Options](ui_screenshots/followup-options-scheduled-1280.png) |
| Multiple facts and source preview | [Form](ui_screenshots/followup-assessment-1440.png) | [Form](ui_screenshots/followup-assessment-1280.png) |
| Revision comparison | [Revision](ui_screenshots/followup-revision-1440.png) | [Revision](ui_screenshots/followup-revision-1280.png) |
| Expanded audit details | [Activity](ui_screenshots/followup-activity-1440.png) | [Activity](ui_screenshots/followup-activity-1280.png) |
| Manufacturing rationale | [Hold](ui_screenshots/followup-hold-1440.png) | [Hold](ui_screenshots/followup-hold-1280.png) |
| ERP service descriptions | [Rates](ui_screenshots/followup-rates-1440.png) | [Rates](ui_screenshots/followup-rates-1280.png) |

Coverage remains desktop Chromium and the in-app browser. Firefox, Safari, mobile,
screen-reader sessions, load testing and production hosting were not run. The
production bundle was built; browser interaction used Vite development servers.
Supplier/customer citation previews use the name returned by the program directory;
plan review shows their full captured source. A revision with no eligible resources
cannot be submitted, and never cancels/releases earlier bookings. No AI run or actual
human approval is claimed by the scripted tests.

---

# Earlier independent review — historical record

**UI AND API INTEGRATION READINESS: PASS.** Independently reviewed September 10,
2026. This report supersedes the earlier completion claims and preview status.

All five apps were opened in a real browser against an isolated file-backed API.
The manual computer-use workflow persisted an operator draft, an explicitly selected
simulated engineer decision, one job/reservation, and one Planner link/task. This is
mock-system integration verification, **not an AI application run or actual human
approval**. No AI calls, agent harness, new business use cases, business endpoints,
dependencies, fixture changes, schema migrations or Git operations were introduced.
The user's working database was never initialized, reset, or mutated by this review.

## Fixes from this review

| Finding | Correction and regression evidence |
|---|---|
| A successful draft POST followed by a denied canonical GET exposed **Revise request after denial**, permitting a second draft | Retry metadata records that the POST was confirmed and retains the exact original body/key across reloads. Only a definitive 4xx denial of an unconfirmed POST allows revision. A new browser regression failed on the original code and passes after the fix. |
| An unknown server error code could also expose request revision | HTTP status participates in recovery decisions. Unknown 500 responses keep **Retry same request**, disable a new draft, and show no success. |
| Overlapping focus/visibility refreshes could discard a mutation's refreshed snapshot; a conservative first fix then reported a false refresh failure | Superseded refreshes await the newest refresh's outcome. A deterministic browser regression holds the first HTTP read and triggers a newer focus refresh. Both the automated check and manual draft recovery pass. |
| A mismatched sample displayed the target configuration as though it were the sample's own configuration | Options now display the actual sample configuration and a separate target configuration. SAMPLE-A-010 correctly displays CFG-A-01 against target CFG-B-01. |
| “Approval unavailable” could match the positive “available” styling | Negative states take priority and positive status matching is explicit. Unavailable approval, late timing and an unreassessed forecast are visibly distinguished. |
| Manufacturing detail assigned “engineering hold” to any restriction; ERP repeated a literal quantity unit | Restriction labels and quantity units now render from returned records. The shell uses a neutral “Source systems” label rather than a hard-coded supplier name. |
| Planner squeezed a four-column schedule next to its form at 1280px | The schedule spans the workspace width. Baseline, conditional forecast and ERP commitment remain separately labeled. When there is no work to link, a meaningful empty/completed state replaces the dead form. |
| Long option labels, excess comparison spacing, flush-left restriction text and awkward status wrapping reduced readability | Shorter disabled-option labels, compact requirement rows, padded restriction sections, protected heading actions, and readable status wrapping. Validation options now link directly to draft authoring. |
| Unknown domain subpages silently rendered a default/blank page; unknown milestones rendered a program heading without a record | Explicit not-found states in all five domains. Deep-link regressions verify no unrelated record is substituted. |
| Loading and retry copy blurred reads, saves and unfinished requests | Read failures ask for refresh; active writes say “Saving and verifying”; retained retries identify a mismatched selected persona. No automatic persona switching. |

Implementation is in `mock_apps_ui/src/`. Regression coverage is in
`mock_apps_ui/e2e/review.spec.ts` and the expanded `workflow.spec.ts`.
The isolated test-server supervisor now returns from its shutdown signal handler
to the original process wait, avoiding a reentrant wait deadlock. It also ignores
repeated shutdown signals. `tests/test_ui_test_server.py` verifies clean shutdown
of its own isolated process group. Business handlers and authorization controls
are unchanged.

## Applications and HTTP boundary

| App | Verified business interactions | HTTP sources and writes (under `/api/v1`) |
|---|---|---|
| Engineering Hub | Search/filter change worklist; compare requirement revisions; inspect configuration, evidence and controlled documents; author an assessment; inspect immutable scope and audit; approve/reject as engineer | Changes, requirements, configurations, workloads, criteria, procedures, policies, documents, plans, decisions, audit. POST change plans and exact-plan decisions. |
| Validation Lab | Inspect evidence mismatches and historical results; compare eligibility/cost/timing; search samples; inspect slot calendar and reservations; schedule approved work | Coverage, options, samples, jobs; Manufacturing provenance. POST jobs. |
| Manufacturing Portal | Filter units by revision/restriction; follow unit/lot genealogy; inspect independent restrictions and source freshness | Unit and lot list/detail records. No public writes. |
| Commercial ERP | Search orders/rates; inspect order quantity, customer and commitment; inspect effective rate dates | Orders and cost rates. No public writes. |
| Program Planner | Search programs; inspect baseline/forecast/commitment, dependencies and linked tasks; complete missing Planner follow-through | Programs, milestones, jobs, implementation links, orders, audit. POST implementation links. |

There are still **34 business operations: 30 GETs and four POSTs**. Some details use
canonical records embedded in list responses rather than another identical detail
request. Mutations explicitly read their persisted record back before confirming
success. No reset/admin/failure-injection route was added.

Evidence that business state is sourced through HTTP:

- Runtime source inspection found no seed/fixture imports, scenario IDs/dates/cost
  constants, localStorage business cache or IndexedDB store in `src/` (generated
  TypeScript declarations excluded). Business fields are accessed from typed API
  records. Static app names, navigation, labels and explanations are presentation.
- A separately scripted HTTP POST created a plan while the browser was open.
  Refresh exposed its actual ID; opening it showed the exact text
  **“Scripted API check: customer requested additional workload evidence.”**
  The script's successful replay returned the same record; changed-body key reuse
  returned 409 and a reader write returned 403.
- Browser response records are saved to `.cache/ui-review-network.json`: method,
  path/query, status and replay marker only. Authorization headers are not logged.
  They show real reads across all five systems, draft/decision/job/link requests,
  a 201 job replay, and the deliberate test-only 503 Planner response.
- Cold-load outage checks cover every app and render no scenario records. A real
  process outage was also performed on the separate manual-review API: Refresh
  labeled retained records as stale; reload showed unavailable data, with no
  invented success. Recovery fetched the persisted records again.

The workspace snapshot is in memory. `sessionStorage` holds the explicit persona,
unfinished forms and exact retry metadata only. The tab notification carries a
refresh signal, not business records. The backend serves only six allowlisted
business documents; developer tests, screenshots and reports remain outside that
retrieval boundary.

## Manual workflow actually completed

The review used browser computer controls, with separate operator and engineer tabs,
on API **18010** and UI **5180**. It inspected CR-017, the customer request document,
the baseline/requested workload, evidence applicability, eligible options, a held
manufacturing unit/lot, the ERP order and the Program Planner baseline.

The operator selected SLOT-PRIORITY / SAMPLE-B-017 and authored a sourced fact,
evidence gap and unresolved question. Nothing was preselected. A separate tab
started as viewer; **Engineering approver** was explicitly selected before reviewing
and recording the decision on that exact immutable plan. The operator then scheduled
its job, inspected the confirmed reservation and missing Planner notice, and linked
it in Planner. Plan, job, evidence and Planner pages were refreshed/reopened.

| Persisted manual-review resource | ID |
|---|---|
| Plan | `plan-0e64cfb2f66e46aaa7bd3060d91fff68` |
| Simulated approval | `decision-298f1f55c31f4438aaf27c1272aab01e` |
| Scheduled job | `job-57162648d7e643feb9542d4f67cd3c5e` |
| Reservation | `reservation-3da99703932340a181b93c512f2448d2` |
| Planner link | `link-a2e72ab339a446389c65f130e8666476` |
| Scheduled task | `task-412a777bc40e4c168c71af33e88e8d6a` |

The review API was stopped and restarted **against the same file**, without reset.
All nine recorded HTTP snapshots matched exactly after restart, including audit.
The draft retry recovered its original ID; the database has one plan, approval,
job/reservation and link/task. Receipts are in
`.cache/ui-review-manual-before-restart.json`.

Final state is `scheduled_awaiting_execution`. Review-ready forecast is
**Nov 18, 2026, 20:00 UTC**, conditional on testing and engineering review.
Baseline evidence deadline remains **Nov 19, 2026, 18:00 UTC**; ERP commitment remains
**Nov 23, 2026, 18:00 UTC**. Requested coverage remains incomplete. No new test
result, product qualification, baseline approval or customer acceptance was created.

## Integrity and failure checks

| Check | Actual evidence |
|---|---|
| Unauthorized approval and role separation | Operator approval control disabled; direct automation approval receives 403. Separate engineer tab defaults to viewer and requires explicit persona selection. Pending retries cannot run under a different persona. |
| Unapproved/rejected booking | Invented approval is rejected (404); a recorded rejection cannot book (403). Only currently eligible, approved unscheduled plans are selectable. |
| Duplicate clicks, retries and immutable requests | Booking double-click issues one request. The first committed reply is deliberately dropped, then reload/retry recovers one job using the same key. Changed-body key reuse is 409; a new-key duplicate points to the existing job. |
| Stale state | Browser submits a deliberately stale source version; the real API returns `STALE_SOURCE`, creates no plan, and the form preserves its text for explicit revision. A real stale milestone request returns 409. Backend regressions mutate isolated critical sources and verify approval/booking denial. |
| Partial follow-through | A test-only Planner transport 503 preserves the real scheduled job and missing-link notice through reload. Retrying only Planner with the same key creates one link/task. Backend fault injection separately proves task/link/dependency/forecast transaction rollback while the lab booking survives. |
| Protected data | End-to-end reads compare ERP order, Manufacturing units/lots and evidence before/after the workflow. Baseline/requested requirement statuses remain distinct. POSTs to protected records return 405; the backend suite covers additional forbidden routes/fields and concurrency. |
| No fabricated test results | Job and task remain scheduled; coverage payload is unchanged. Result detail still reports the short run as a historical pass with insufficient duration for the requested obligation. |
| Errors after a committed write | A read-back denial retains the original retry even after reload. Unknown 500s and cold/cached read failures do not report success or enable a second draft. |

Successful workflow responses are never stubbed. Browser fault injection is limited
to deliberate error responses, a stale outgoing request and dropping an actual
committed booking response. Database corruption/reset/transaction-failure tests use
isolated pytest storage. No destructive check uses the user's working database.

## Commands and actual results

Run from the project root unless otherwise indicated. Tested runtimes: Python
3.12.10, Node 24.13.1, uv 0.7.6. Existing lockfiles and dependencies are preserved.

| Command/check | Result |
|---|---|
| `TMPDIR="$PWD/.cache/tmp" .venv/bin/pytest -q` | **193 passed in 34.91s**, zero failures/skips; includes isolated real-HTTP lifecycle and supervisor shutdown tests. Initial review baseline passed 192 in 29.36s. |
| `.venv/bin/python scripts/validate_scenario.py` | PASS: 42 records, 110 references, six documents, nine options, six rejected corruption probes. Static scenario validation; not an API run. |
| `npm --prefix mock_apps_ui run typecheck` | PASS (`tsc --noEmit`). |
| `npm --prefix mock_apps_ui run build` | PASS; 1,759 modules; 459.86 kB JS / 15.08 kB CSS before compression. |
| `PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix mock_apps_ui run test:e2e` | **14 passed in 31.0s**, zero failures/skips; includes all five apps, both desktop sizes, real workflow, external API visibility, failure/retry and stale-state checks. |
| Focused `PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix mock_apps_ui run test:e2e -- review.spec.ts` | **Eight passed in 20.0s**; recovery/status/stale-state regressions and desktop form screenshots. |
| Focused `TMPDIR="$PWD/.cache/tmp" .venv/bin/pytest -q tests/test_ui_test_server.py` | **One passed in 0.96s**; isolated process-group shutdown regression. |
| Manual computer-use workflow and HTTP restart comparison | PASS on isolated API/UI 18010/5180; all nine snapshots persisted exactly. |
| PNG dimension inspection and visual review | Five apps at actual 1440×900 and 1280×800 viewport sizes, plus full-page workflow/form images. |

Logs: `.cache/ui-review-pytest.log`, `.cache/ui-review-e2e.log`,
`.cache/ui-review-regression.log`. Separate scripted HTTP receipt:
`.cache/ui-review-scripted-api.json`. Playwright's HTML report is
`mock_apps_ui/playwright-report/index.html`.

Unsuccessful development checks are not counted as passes: the new read-back test
reproduced the original revision defect; a first refresh-race fix failed recovery;
and a stale-form test initially used an exact label lookup that no longer resolved
on the disabled populated textarea. It now asserts the accessible textbox's value.
The first two required application corrections; the last corrected the selector
without removing the state assertion. Intermittent supervisor teardown diagnostics
led to the signal-handler correction and dedicated regression; the final full run
shut down cleanly. The Vite serving-allow-list diagnostic is expected: a browser test
requests the developer test source and asserts that it is blocked with 403.
Formatting commands initially used the wrong working directory and were rerun
successfully inside `mock_apps_ui/`.

## Screenshots reviewed

`docs/ui_screenshots/` contains developer artifacts, not business evidence. Viewport
files have the exact requested width **and height**; full-page files preserve the
rest of scrollable details. All ten primary viewport images were visually inspected
for clipping, readability, hierarchy and status meaning. No document-wide horizontal
overflow was detected. Detailed forms, option comparison, reservation, approved plan
and linked Planner were also inspected.

| Application | 1440×900 viewport | 1280×800 viewport |
|---|---|---|
| Engineering | [Change](ui_screenshots/engineering-1440-viewport.png) | [Change](ui_screenshots/engineering-1280-viewport.png) |
| Validation | [Evidence](ui_screenshots/validation-1440-viewport.png) | [Evidence](ui_screenshots/validation-1280-viewport.png) |
| Manufacturing | [Inventory](ui_screenshots/manufacturing-1440-viewport.png) | [Inventory](ui_screenshots/manufacturing-1280-viewport.png) |
| ERP | [Order](ui_screenshots/erp-1440-viewport.png) | [Order](ui_screenshots/erp-1280-viewport.png) |
| Planner | [Milestone](ui_screenshots/programs-1440-viewport.png) | [Milestone](ui_screenshots/programs-1280-viewport.png) |

Full-page details: [draft at 1280](ui_screenshots/draft-1280.png),
[draft at 1440](ui_screenshots/draft-1440.png),
[options at 1280](ui_screenshots/options-1280.png),
[options at 1440](ui_screenshots/options-1440.png),
[approved plan](ui_screenshots/engineering-approved.png),
[reservation](ui_screenshots/validation-reservation.png),
[linked Planner](ui_screenshots/programs-linked.png).
The primary screenshot test runs after recovery tests, so the change worklist may
already contain test drafts. These are actual persisted test records, not baseline
screenshots or rendered fixtures.

## Preview and short human walkthrough

The retained **isolated review preview** uses:

- [Engineering](http://127.0.0.1:5180/engineering)
- [Validation](http://127.0.0.1:5180/validation)
- [Manufacturing](http://127.0.0.1:5180/manufacturing)
- [ERP](http://127.0.0.1:5180/erp)
- [Program Planner](http://127.0.0.1:5180/programs/PRG-A17)
- [API docs](http://127.0.0.1:18010/docs)

Database: `.demo/ui-e2e-14c9e98da0e4469b94a79e155290fbc0.sqlite3`.
The retained preview is already scheduled/linked. Inspect its records rather than
trying to reuse the reserved sample. This review makes no claim about older
processes at 8000/5173. Preview availability is a point-in-time check.

To resume the retained review file after stopping these services:

```sh
DEMO_MODE=true \
  DEMO_DB="$PWD/.demo/ui-e2e-14c9e98da0e4469b94a79e155290fbc0.sqlite3" \
  .venv/bin/mock-enterprise serve --port 18010
# Separate terminal:
MOCK_API_URL=http://127.0.0.1:18010 npm --prefix mock_apps_ui run dev -- --port 5180
```

To walk through fresh state, stop only those review servers, then run
`.venv/bin/python scripts/serve_ui_test.py 18010`; it initializes a **new unique**
review database and prints its path. Start Vite with the command above. No reset
of any existing database is needed. Use Ctrl-C to stop each owned terminal.
The automated browser suite owns separate 18000/5174 servers, refuses port reuse,
and retains unique test databases for inspection.

1. Engineering → CR-017: read the request document, compare workloads, and inspect
   historical evidence. Visit the Manufacturing hold and ERP commitment.
2. Explicitly select **Program operator** → **Draft assessment**. Choose a qualified
   option, enter a fact and supporting source, evidence gap and open question.
   Create the immutable draft and review its computed timing/cost.
3. Open that plan in a new tab, explicitly select **Engineering approver**, enter
   a reason, acknowledge review, and record approval. Mock selectors do not prove
   a real engineer's identity.
4. Return to the operator tab → Validation → Jobs queue. Select the exact approved
   plan and schedule it. Open the job and verify its reservation.
5. Follow **Link this scheduled job** to Planner; select it and link. Refresh/reopen
   the plan, job and milestone. Check the conditional forecast, preserved baseline
   and ERP commitment, and still-unsatisfied evidence obligation.
6. On an interrupted reply, **Retry same request**. If Planner is missing after a
   successful booking, complete only Planner. A definitive stale denial calls for
   explicit revision/reassessment; approval of an old plan does not transfer.

## Limits and checks not executed

This remains one local FastAPI service and one React frontend, with a small scoped
workspace and public mock identity selectors. It is not production authentication.
A full workspace refresh issues multiple HTTP reads; any failed source prevents new
writes until refresh succeeds. There is no background polling or pagination.

Verification covers the in-app desktop browser and Playwright Chromium, including
the two requested desktop sizes. Firefox, Safari, mobile devices, screen-reader
sessions, production hosting, load testing and real enterprise systems were not
executed. The production bundle was built; interactive tests used Vite's development
server. These are explicit coverage limits, not claims of additional testing.

No cancellation/rescheduling, test execution/result generation, baseline promotion,
customer acceptance, ERP editing, manufacturing hold release or new escalation
workflow exists. Source changes after booking can require manual reassessment; the
app preserves the booked job. No scenario contradiction was found or silently
resolved by altering business data. The agent/control-plane phase remains out of
scope.
