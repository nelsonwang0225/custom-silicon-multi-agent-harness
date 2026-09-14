# Synthetic data and enterprise UX enrichment

Current phase: version `stratos-portfolio-1`. Verification is recorded below; no AI
runtime, model call, agent harness, new deployment, dependency or Git operation was
introduced. All people, companies, observations, prices and capacity are fictional.

## Naming and operating portfolio

Supplier: **STRATOS SILICON**. Business unit: **Advanced Compute Programs**.
Primary customer: **HELIOS AI**, a fictional frontier model lab. PRG-A17 is named
Helios Atlas Inference; its stable CUST-FML01 identifier remains unchanged.

| Program | Customer / business type | Program lead | Product |
|---|---|---|---|
| PRG-A17 · Helios Atlas Inference | HELIOS AI · frontier model lab | Mara Chen | ACCELERATOR-X REV-B |
| PRG-P01 · Northstar Boreal | Northstar AI · applied model lab | Elena Park | BOREAL-N2 REV-B |
| PRG-P02 · Vela Stream | Vela Compute · cloud infrastructure | Jonas Vale | STREAM-V4 REV-B |
| PRG-P03 · Meridian Relay | Meridian Systems · networking | Rina Sol | RELAY-M3 REV-B |
| PRG-P04 · QuantaForge Prism | QuantaForge AI · inference platform | Theo Marin | PRISM-Q2 REV-B |
| PRG-P05 · Arcadia Vector | Arcadia Compute · HPC | Asha Reed | VECTOR-A6 REV-B |
| PRG-P06 · NovaGrid Ember | NovaGrid Technologies · energy edge compute | Owen Sato | EMBER-E1 REV-B |
| PRG-P07 · Atlas Motion | Atlas Robotics · industrial robotics | Lena Ortiz | MOTION-R3 REV-B |
| PRG-P08 · Horizon Pilot | Horizon Intelligence · automotive compute | Noah Kim | PILOT-H2 REV-B |
| PRG-P09 · Vela Mesh | Vela Compute · cloud infrastructure | Mira Dane | MESH-V2 REV-B |
| PRG-P10 · Arcadia Tensor | Arcadia Compute · HPC | Evan Rao | TENSOR-A2 REV-B |

No real company names were added to synthetic records. Developer/tool references
in technical documentation are not fictional business customers.

## Initial record counts

These are counts after fresh initialization/reset, before walkthrough mutations.

| Records | Count |
|---|---:|
| Suppliers / customers / programs | 1 / 9 / 11 |
| Engineering changes | 41 |
| Requirement revisions | 82 |
| Configurations / workload profiles | 26 / 22 |
| Approved procedure / criteria / policy records | 11 / 11 / 11 |
| Controlled business documents | 36 (6 authored files + 30 generated business documents) |
| Immutable plans / decisions | 30 / 27 (24 approvals, 3 rejections; 3 additional plans await review) |
| Independent validation evidence records | 113 |
| Validation jobs | 30: 20 scheduled jobs + 10 separately imported historical executions |
| Historical execution states | 5 completed / 5 engineering disposition pending |
| Reservations / samples / slots / labs | 20 / 53 / 53 / 23 |
| Manufacturing lots / serialized units | 53 / 113 |
| Customer orders / effective rates | 21 / 23 |
| Milestones / dependencies | 91 / 191 |
| Planner implementation links / tasks | 10 / 10 |
| Initial activity events | 397 |

The ten unlinked scheduled jobs intentionally expose partial follow-through.
Scheduled jobs have no generated results. Historical jobs link to independently
authored observations with matching scope and execution timestamps.

## Generation and integrity

`fixtures/seed.json` and the six allowlisted documents are the explicit golden
fixture. `src/mock_enterprise/portfolio.py` adds ten coherent program templates
using fixed IDs and scenario timestamps. There is no random or wall-clock input.
Templates describe primary exposure, repeatability, integration and clarification
packages within ten additional change categories. They are scheduling/evidence
coordination scenarios, not physical simulations of the named engineering concern.

Each program connects its customer, configuration, requirements, changes, procedure,
policy, source documents, evidence, lots/units, resources, orders and milestone gates.
Four programs additionally have distinct historical firmware/runtime configurations.
Evidence includes matching coverage, wrong revision/profile/software, short duration,
missing bins and recorded nonpassing observations. None is inferred from booking.

Initialization validates typed rows, duplicate IDs, foreign keys, program/customer
scope, unit/lot/sample lineage, exact historical snapshots, exposure arithmetic,
historical job observations and dependency states. Historical plan scopes, costs,
timing and snapshots are calculated with the ordinary domain rules; decisions bind
those immutable plans. The initializer labels these records as authored synthetic
history, not actual human decisions or a claim that an HTTP script ran. Subsequent
HTTP operations use the normal role, exact-approval, freshness, idempotency and
transaction controls. The history passes live source checks and can be continued
through the ordinary APIs.

Golden-focused unit tests explicitly load the authored fixture. The additional
portfolio tests initialize the full default environment, and all browser tests run
against the expanded default through real HTTP. Two guarded resets on an isolated
file reproduce the identical business rows and initial events. The running-service
reset lock is still tested. No active user database was reset or migrated.

## CR-017 invariants

- Requested REQ-042-V2 stays requested; REQ-042-V1 remains approved.
- ACCELERATOR-X REV-B / CFG-B-01, model, firmware, runtime, criteria and workload
  scope are unchanged: 480 total minutes, 160 per bin, same three target bins.
- Three initial golden observations remain insufficient; missing evidence is not
  declared a hardware failure.
- The same nine combinations yield two technically eligible choices: standard is
  $0 and 28 hours late; priority is $1,800 and 22 hours before the baseline.
- The delegated limit remains $2,000, with exact immutable plan/source/resource
  binding and explicit engineer approval. Operator self-approval is denied.
- Booking creates one scheduled job/reservation. Planner creates one link/task.
  It does not execute a test, author a result, release a hold or accept a product.
- Baseline remains November 19, 2026 at 18:00 UTC. Priority forecast is November 18
  at 20:00 UTC. ERP commitment remains November 23 at 18:00 UTC.

## UI changes and integration behavior

| Application | Delivered operating UI |
|---|---|
| Launcher | HTTP-sourced Stratos branding, Advanced Compute Programs, compact current Helios case, deadline, distinct decision/execution, next responsible role and linked four-stage flow; five application links. |
| Engineering | 41-case queue, customer/program/priority/state/search filters, priority/deadline or update sorting, 12-row pagination, owner/updated/product/next-action columns. CR-017 is naturally discoverable through Helios/high priority/search; no ID-specific queue pinning. Full comparison, multi-fact/citation drafting, source previews, exact decisions, revision lineage and expanded activity remain. |
| Validation | Portfolio scheduled-job queue, separate execution history with observed-result links, 53-sample register and 53-slot calendar, customer/program/status/lab/product-configuration filters, case-specific options and scheduling. Existing reservations and missing Planner links remain explicit. A fully booked case shows existing work instead of a dead new-booking form, while uncertain writes retain their retry control. |
| Manufacturing | 113 units / 53 lots with customer/program, product/revision, inventory state, independent restrictions, freshness and genealogy; searches/filters and persisted rationale/team/release conditions. Read-only. |
| ERP | 21 customer orders with quantities, product, program and authoritative commitment; customer/program/state/search filters. 23 effective approved rates have descriptive service labels and exact integer-cent amounts. Read-only. |
| Planner | Eleven-program table with lead, lifecycle, health and next action; all 91 milestones are navigable, including gates without a change case. Baseline, conditional forecast and customer commitment stay separate. Dependencies link to source previews or jobs. Multiple case workspaces use expandable sections; activity shows provenance and integration details. |

Decision and execution are separate. Displayed next actions derive from current
plans/jobs/links where available; initial descriptive next-action text cannot hide
completed scheduling or a missing Planner link. Existing revised-plan approval and
source-binding controls remain. Closed/superseded changes cannot be reopened by
drafting. Status colors distinguish risk, restriction, scheduling and completion.

The UI imports no business fixtures. It receives business state through HTTP, using
the same APIs available to scripted clients. A new transaction-consistent `/portfolio`
read avoids eager option computation for every case; existing case endpoints supply
current details and selected options. Gzip reduces transport cost. Persona changes,
refresh, tab focus and successful writes retrieve canonical state. No business
records are saved to browser storage; only persona, unfinished forms and retry
metadata persist there.

API additions are two GETs (`/portfolio`, `/validation/history/{id}`), additive
context fields and an immutable historical-job table. The same four business POSTs
remain. Portfolio identities have explicit server-owned program/customer membership;
legacy selectors remain golden-case scoped. See [API_CONTRACT.md](API_CONTRACT.md).

## Actual verification

Baseline, before edits:

| Command | Result |
|---|---|
| `TMPDIR="$PWD/.cache/tmp" .venv/bin/pytest -q` | 197 passed in 37.10s |
| `PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix mock_apps_ui run test:e2e` | 16 passed in 41.3s |
| `npm --prefix mock_apps_ui run typecheck` | PASS |
| `npm --prefix mock_apps_ui run build` | PASS; 1.29s |

Final checks:

| Command / check | Actual result |
|---|---|
| Full backend command above | **214 passed in 48.06s**, zero failures/skips; 17 new portfolio regressions |
| `.venv/bin/python scripts/validate_scenario.py` | PASS: original 42-record / 110-reference / six-document / nine-option checks and six corruption probes, plus expanded deterministic graph, counts, FK and live plan-snapshot checks |
| Frontend typecheck / production build | **PASS**; 1,764 modules, 493.60 kB JavaScript (149.15 kB gzip), 20.04 kB CSS; Vite build 1.20s |
| Full browser command above | **20 passed in 2.1m**, zero failures/skips; includes all five apps and both viewport sizes |
| Manual in-app browser | All five apps inspected; operator draft → explicitly selected engineer approval → operator reservation → Planner link → refresh/reopen completed on a separate isolated file |
| Independent HTTP write | Browser integration script links an existing surrounding-program job through the unchanged Planner POST, replays the exact key and verifies the persisted task after UI refresh/reload; evidence unchanged |

The suite covers unauthorized approval, unapproved/wrong-scope booking, stale sources,
revisions requiring new approval, duplicate clicks/retries, lost committed responses,
partial follow-through, protected ERP/manufacturing/criteria/results, and backend
failures without invented success. Cold failure visits across all five apps show no
frontend fixture fallback. Browser tests capture sanitized method/path/status data;
no bearer values are written to receipts.

Development checks exposed and fixed the original single-engineer signer assumption,
missing exact accessible labels, ambiguous one-record test selectors once queues
contained many records, and stale next-action/empty-activity presentation. Early
failing development runs are not counted as passing runs. The final validation
commands and logs are the evidence, not earlier completion claims.

Logs: `.cache/data-enrichment-baseline-*.log`,
`.cache/data-enrichment-backend-final.log`,
`.cache/data-enrichment-browser-complete.log`,
`.cache/data-enrichment-typecheck-final.log`, `.cache/data-enrichment-build-final.log`,
`.cache/data-enrichment-scenario-final.log`. HTTP receipts:
`.cache/data-enrichment-api-receipt.json`, `.cache/ui-review-scripted-api.json`.
Network evidence: `.cache/data-enrichment-browser-network.json`,
`.cache/ui-review-network.json`.

The final filter regression confirms that changing customer/program clears the
previous lab/configuration selection instead of silently retaining an invisible
filter. A runtime-source search found no fixture imports or hard-coded CR-017,
customer ID, Stratos or Helios business records in `mock_apps_ui/src`.

## Previews and manual receipt

| Purpose | UI | API | Isolated database |
|---|---|---|---|
| Fresh enriched portfolio; CR-017 awaits assessment | [5183](http://127.0.0.1:5183/) | [18013 docs](http://127.0.0.1:18013/docs) | `.demo/ui-e2e-a9c8efba8d1c4747aca6c13c9ff52201.sqlite3` |
| Completed manual Helios example | [5182](http://127.0.0.1:5182/) | [18012 docs](http://127.0.0.1:18012/docs) | `.demo/ui-e2e-ce438293683544e0ad64914c78deef13.sqlite3` |

Final read-only health checks returned ready from both APIs and HTTP 200 from both
UIs. Fresh CR-017 has zero plans/jobs/links; the completed example has exactly one
of each. The fresh portfolio GET took 0.210s locally and used gzip transport for
3,290,605 decompressed bytes. This is a point-in-time local check, not a load test.
Receipt: `.cache/data-enrichment-preview-check.json`. The fresh preview is open in
the in-app browser.

Created with `.venv/bin/python scripts/serve_ui_test.py 18013` (or `18012`) and
`MOCK_API_URL=http://127.0.0.1:18013 npm --prefix mock_apps_ui run dev -- --port 5183`
(or `18012` / `5182`). Both bind to loopback. To resume a retained file, set its
explicit `DEMO_DB` and `DEMO_MODE=true`, then run `.venv/bin/mock-enterprise serve
--port 18013`; run the matching Vite command separately. Do not initialize over it.

Manual receipt `.cache/data-enrichment-manual-ui.json` records:

- Plan `plan-830ea6d383cf4f76912215c2e16cdca4` (two authored facts).
- Decision `decision-c77d7df6dd9948c693b03ec6057ddddc`, signer `demo-portfolio-engineer`.
- Job `job-3fefaef5449b4a6e90ff1f97560da978`.
- Reservation `reservation-c63dee7a931140afa75309fad9123aaa`.
- Link `link-184bbf6888994f1eb64c04f8754b6041`.
- Task `task-5eb66c475fdc4e299345a9f381535009`.

Those UI writes add one plan, decision, job/reservation, link/task and four events
to the initial portfolio. The fresh preview retains exactly the count table above.
No reset was performed on either retained preview or `.demo/enterprise.sqlite3`.
Older 5180/5181 files were preserved; their data was not renamed or enriched.
An intermediate development preview was stopped and replaced by a newly initialized
file; no existing file was reset.

## Screenshots and human walkthrough

Real Chromium captures reviewed at **1440×900 and 1280×800**, including scroll/overflow
checks. Queue captures preserve the exact viewport, with internal scrolling tables.

| Screen | 1440×900 | 1280×800 |
|---|---|---|
| Launcher | [Image](ui_screenshots/enrichment-launcher-1440.png) | [Image](ui_screenshots/enrichment-launcher-1280.png) |
| Engineering queue | [Image](ui_screenshots/enrichment-engineering-queue-1440.png) | [Image](ui_screenshots/enrichment-engineering-queue-1280.png) |
| Validation jobs | [Image](ui_screenshots/enrichment-validation-jobs-1440.png) | [Image](ui_screenshots/enrichment-validation-jobs-1280.png) |
| Historical execution | [Image](ui_screenshots/enrichment-validation-history-1440.png) | [Image](ui_screenshots/enrichment-validation-history-1280.png) |
| Manufacturing | [Image](ui_screenshots/enrichment-manufacturing-register-1440.png) | [Image](ui_screenshots/enrichment-manufacturing-register-1280.png) |
| ERP | [Image](ui_screenshots/enrichment-erp-orders-1440.png) | [Image](ui_screenshots/enrichment-erp-orders-1280.png) |
| Planner portfolio | [Image](ui_screenshots/enrichment-program-portfolio-1440.png) | [Image](ui_screenshots/enrichment-program-portfolio-1280.png) |

Existing follow-up screenshots also cover rich assessment, revisions, scheduled
state, activity, hold and rate details. Test screenshots may include earlier actions
in that test run; they are developer artifacts outside runtime retrieval.

1. Open 5183. In Engineering filter Customer to HELIOS AI or search CR-017. Notice
   the other active programs and cases when filters are cleared.
2. Inspect the exact requirement comparison, customer request, evidence mismatch
   reasons, Manufacturing hold and ERP order/rates.
3. Explicitly select Program operator. Draft an assessment with multiple facts,
   relevant source citations, gaps and questions; choose an eligible resource pair.
4. Explicitly select Engineering approver. Review scope, sources, cost and timing,
   acknowledge the exact immutable plan and record the simulated decision. A revised
   plan has its own identity and requires fresh approval.
5. Return to Program operator and schedule the approved job. Follow its missing
   Planner action, select that scheduled job and create the implementation link.
6. Refresh/reopen Engineering, Validation options and Planner. Verify the same job,
   separate approval/execution, conditional forecast, unchanged baseline/commitment
   and still-open evidence obligation. No result is invented.
7. Explore another customer's jobs, historical observations, lots/orders and all
   milestone gates. Expand source and activity details to inspect provenance.

## Limitations and checks not executed

This remains a local deterministic mock with public role selectors, not production
authentication or real staff approval. Program health and historical observations
are authored synthetic inputs, not telemetry or predicted outcomes. No agent or
physical test ran. Numerical acceptance thresholds, engineering/customer acceptance,
cancellation, resource release and execution/result authoring remain out of scope.
The original conservative reservation model allows one outstanding job per sample.

The supported review is desktop Chromium and the in-app browser. Firefox, Safari,
mobile, assistive-technology sessions, production deployment and sustained concurrent
load testing were not run. Browser tests use Vite development servers; the production
bundle was built and typechecked. Portfolio reads were measured locally and browser
navigation is bounded in tests; this is not a production performance benchmark.

Old databases retain original names/context and are not automatically migrated. A
pre-enrichment database missing the historical-job table may fail the conservative
reset schema check; create a fresh named file instead of bypassing the guard. The
review never resets or mutates the user's active file.

No remaining blockers for the requested desktop mock-app enrichment phase.

UI AND API INTEGRATION READINESS: PASS

SYNTHETIC DATA & UX ENRICHMENT STATUS: PASS
