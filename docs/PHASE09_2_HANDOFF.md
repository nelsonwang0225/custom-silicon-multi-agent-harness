# Phase 09.2 — Cross-workflow product integration

Implemented from [the explicit request](../prompts/09_2_PRODUCT_INTEGRATION.md).
The four existing workflows now share current case and decision projections across
the product. This slice adds no workflow, business write, agent, scheduler or
execution authority. Phase 09.3 has not started. Working demo databases were not
reset or migrated during verification.

## Inconsistencies corrected

| Area | Finding and resulting behavior |
|---|---|
| Current case state | Independent page summaries mixed source status, run completion and business outcome. One typed semantic projection now supplies each canonical case's state, detail, next step, boundary and attention reason. Workflow detail remains available. |
| Overview | Review counts covered only CR-017, and separate workflow sections duplicated cases/issues. Counts now include every current human decision; the directory labels its separate source-plan draft count explicitly; attention is deduplicated and prioritizes failure, human review, staleness, blockers and unresolved external work. Successful CR-019 intake creates no human attention item. |
| Program | Generic Engineering case rows omitted QE/DR and duplicated CR-019. One connected row per canonical case now shows current state, real source dependencies and the next gate's relevant case action. Original ERP orders remain individually identified. |
| Decisions | Three independent lists bypassed global filters. A single human-decision projection now applies every filter to validation authorization, Engineering evidence review, recovery and delivery commitment. Exact versions/digests, source decision, reviewer and execution linkage remain visible. |
| Activity / catalog | Program activity used only the latest CR-017 run and described connected idle scope as Preview. It now selects the latest actual run across all four cases, links its exact run detail, and shows Connected · Idle when appropriate. Requirement Change Analysis history includes its standard route. Existing registry-derived connected modes and inactive trigger disclosures are preserved. |
| Search / source links | CR-019 could appear twice; technical artifacts could precede the case; a material search could open the wrong lot context. Canonical case IDs are deduplicated and ranked first, with related source terms retained. Manufacturing material opens its exact lot and Validation intake opens its exact intake. |
| Alerts | Host and source alerts could represent the same underlying case, and completed CR-017 evidence work remained an attention item. Shared stable issue keys deduplicate canonical case alerts; current completion/reset clears the old issue. Mark-read is still presentation-only. |
| Concierge | Current business summaries differed from page-specific historical observations. Grounded status cards use the same current semantic facts on Overview, Program, Case, Decision, Workflow and Operations; existing context resolution and structured confirmation boundaries remain. |
| Operations | Exact CR-017 proposal links omitted the digest; current-source enrichment was incomplete for other workflows; metadata polling could overwrite refreshed case state. Exact links now include the digest, and index/detail expose current case state with its source-read time separately from each recorded run outcome. |
| Reset / refresh | Workflow-specific session retry keys survived an epoch change. Known CR-017/CR-019/QE/DR invocation keys now clear with the existing reset epoch. Navigation, focus, polling and manual refresh update shared reads; loading, refreshing and stale/unavailable states remain explicit. |

## Authoritative source mapping

No scenario fixture or source business API was changed. The shared host projection
reads the existing scoped HTTP interfaces; it does not read database tables or
fixtures. Developer-only initialization/failure injection remains isolated in tests.

- **Program/customer/configuration:** PRG-A17, CUST-FML01 / HELIOS AI and CFG-B-01
  retain their existing source identities. Program context lists the separate
  original orders ORD-1204, ORD-HEL-150 and ORD-HEL-800 with source deep links,
  instead of implying the 100-unit order is the delivery request's 800-unit scope.
- **Quality → delivery:** shared Manufacturing material IDs are intersected from
  both current contexts. MAT-B-204 remains 250 held units with zero eligible
  unallocated quantity in both. Recovery routing never releases that material.
  DR-009 continues to calculate 600 eligible of 800 requested, leaving 200.
- **Technical scope:** the canonical DR-009 request is REQ-042-V1 / CFG-B-01,
  independent of CR-017's requested V2. The Program view says so explicitly. Only
  a delivery request actually bound to CR-017 creates that technical dependency;
  the tested V2 variant waits for current exact Engineering evidence approval and
  becomes unready again when critical source criteria change.
- **Validation:** current coverage is read through the existing coverage API;
  applicable historical evidence is not hard-coded as a missing-evidence gap.
  Scheduled, tested, applicable, Engineering-approved and customer-accepted remain
  separate. A prior verified standard intake stays historical if its approved
  applicability later changes; it does not authorize new work.
- **Deep links:** existing Engineering change, Validation result/intake/job,
  Manufacturing lot/quality, ERP order/delivery and Planner program/milestone
  routes remain. Aggregate source pages retain their stable case context where
  no individual-record route exists. No arbitrary URL/query action was added.

## Shared state and canonical paths

The existing host case aggregate adds `case_summaries`, `decision_summaries` and
`dependencies`; see [OpenAPI](phase09-2-host-openapi.json). These fields confer no
approval or execution authority. Source availability and critical-version checks
outrank old successful run observations. Current source data can make an old
proposal stale without rewriting its immutable history.

| Path | Meaning of its successful connected outcome |
|---|---|
| CR-019 | Verified Validation Operations intake; `waiting_external` with no new human decision/attention item. Lab authorization, scheduling and physical work are downstream. |
| CR-017 | Exact authorization → separately verified Validation/Planner actions → synthetic lab arrival → reassessment → distinct exact Engineering evidence review. Only then `completed_technical`; customer acceptance remains pending. |
| QE-004 | Standard investigation plus exact Program Owner approved recovery metadata, verified independently. Further investigation/disposition is external; held material remains governed. |
| DR-009 | Exact Program Owner approved ERP commitment plus Planner link, verified independently. The remaining supply gap and customer agreement remain separate. |

Shared states include new, investigating, needs_review, approved, executing,
verification_required, waiting_external, completed_technical, escalated,
partial_failure, stale, failed and unavailable. Workflow-specific detail is retained.
A failed or incomplete new run cannot silently inherit a previous successful outcome.

Partial writes remain per-system transactions. CR-017 displays each Validation and
Planner action; QE displays investigation and recovery-task progress; DR displays
ERP and Planner progress. A verified first step remains visible when the second
fails. Existing exact-plan reconciliation/retry controls remain responsible for
continuation. Readback mismatch stays unverified; there is no blind retry or
cross-system rollback claim.

Decisions defaults to genuine pending human review. Approved, Rejected, Executed /
Completed, Superseded / Stale and Needs attention filters apply across all human
workflows. QE/DR links select the exact recorded plan; an unknown selected plan
cannot silently fall back to a different actionable plan. CR-017 authorization
links include version and digest. Engineering evidence review binds the evidence
digest and source signer identity; it has no synthetic proposal version. Its approval
does not imply customer acceptance.

Operations retains case ↔ run ↔ actual agent/tool/evidence observations ↔ exact
proposal/decision ↔ action ↔ verification links. Nullable current-case fields and
source-check time distinguish current state from recorded runtime history. Missing
SDK metadata remains unavailable. Metadata polling never invokes a model or
pretends to re-read source state. Recorded readback mismatches retain their specific
label when current-case facts refresh.

## Reset and walkthrough

Restart your existing local host against the same source and metadata storage to
load the additive projection contract; no initialization or reset is required.
Keep the [Phase 09.1 startup/reset procedure](PHASE09_1_HANDOFF.md) and
[canonical baseline](PHASE09_1_DEMO_BASELINE.md). No launch/reset command changed.
Use Operations → Demo controls → Full demo → Review reset… → type RESET → Confirm
demo reset → Verify baseline. Normal startup never resets state. The tested reset
journey also retains historical evaluation truth and inactive automation settings.

A deterministic product walkthrough is available through
`mock_apps_ui/playwright.product.config.ts`; its services use unique
`.cache/phase09-2/browser/` storage. The test starts all four supported paths,
checks three actual human decisions, executes DR-009, compares Concierge current
facts across six contexts, follows exact source/decision links, checks search and
alerts, then resets while a second tab holds an old CR-017 proposal and retry keys.
The stale tab returns to the baseline and loses the old action controls without
manual browser storage clearing. The existing reset browser test separately proves
mutations survive service restart and the reset baseline survives another restart.

## Verification and files

Actual commands, results, initial failures/corrections, skipped checks and every
changed file are recorded in [PHASE09_2_VERIFICATION.json](PHASE09_2_VERIFICATION.json).
All business-path testing is **scripted integration testing**, with isolated local
HTTP/MCP, deterministic model doubles and simulated demo approvals. Speech is
mocked. No paid model, semantic grader, real microphone or external speech provider
was invoked. Historical live eval failures retain their original truth.

| Executed verification | Result |
|---|---|
| Source suite | 483 passed |
| Full coordinator suite | 724 passed |
| Final focused integration/contract suites | 56 passed and 19 passed; overlapping regressions, including both subsequently added tests |
| MCP suite | 56 passed |
| Offline evaluation families | 112/112 passed; zero critical failures; paid semantic grader skipped |
| Existing browser suite, connected variant matrix, reset and new product journey | 81 unique cases passed across full runs and affected-file reruns; 3 intentional Operations variant skips |
| Typecheck and production build | Passed; existing >500 kB entry-bundle advisory |

Earlier failed attempts are retained with their reasons in the verification report.
All 666 pre-existing PNG artifacts were restored byte-for-byte; fresh regression
captures of historical phases are kept separately under `.cache/phase09-2/`.

Inspected product captures: [Program baseline](screenshots/phase09-2/program-baseline.png),
[Overview review queue](screenshots/phase09-2/overview-review.png),
[Decisions](screenshots/phase09-2/decisions.png), and
[reset baseline](screenshots/phase09-2/reset-baseline.png).

## Remaining product limits

- Cross-system reads are independent observations, not a distributed snapshot.
  Explicit source availability, timestamps, critical-version revalidation and the
  existing exact action boundary remain necessary. Historical run outcomes may
  differ from the separately labelled current case state.
- The current connected scope remains the four canonical PRG-A17 cases. Other
  portfolio records retain existing source-derived views. Technical dependency
  variants are test fixtures; the working demo's approved V1 request was not changed.
- No scheduler, event listener, condition evaluator or production authentication is
  introduced. Saved triggers are configuration-only; model invocation remains an
  explicit existing action. Automatic polling makes no paid calls.
- Existing bounded Operations history/artifact visibility and demo archive retention
  limits remain. There is no general historical archive restoration UI.
- The existing production bundle-size advisory remains. This slice does not attempt
  visual redesign, code splitting or Phase 09.3 polish.

Stop after Phase 09.2. No Git operation, paid live smoke, new execution capability
or later-phase work was performed.
