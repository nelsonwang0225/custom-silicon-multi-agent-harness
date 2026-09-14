# Phase 08.1 visual refinement

Historical handoff. The [current concierge refinement handoff](PHASE08_1_CONCIERGE_HANDOFF.md) supersedes this visual design, tiny launcher, status pills and text-only restriction. The preserved checks below describe the earlier implementation, not the current result.

Implemented the [focused refinement](../prompts/08_1_VISUAL_REFINEMENT.md). This supersedes the initial shell's monochrome palette, verbose Portfolio and docked assistant. **Stop here. No 08.2 work, live chat, scheduling, paid model calls or Git operations.**

Open the existing local preview: [Portfolio](http://127.0.0.1:5188/control), [Helios program](http://127.0.0.1:5188/control/programs/PRG-A17), [CR-017](http://127.0.0.1:5188/control/programs/PRG-A17/cases/CR-017), [five source apps](http://127.0.0.1:5188/). It still uses the isolated source service on 18008, with the existing `.demo/ui-e2e-07805828281946a69df329beaa1226e1.sqlite3`. The working service on 8000 was not contacted during this refinement. The original handoff retains launch/resume instructions.

## Design and behavior

- Compact Portfolio title and filters, followed by Programs / Active investigations / Needs review / At risk. Filters and metric counts share the same scope; Clear filters appears only when useful. Definitions are keyboard-accessible disclosures. Unknown health produces an unavailable risk total. Historical or out-of-scope drafts are excluded.
- Three source focus-program cards show the existing name, lifecycle, explicit health, earliest open baseline gate/date and source next action. Configuration, revision and owner remain in program detail. All eleven source programs and current URLs remain available.
- Agent activity appears directly below the program cards, beside a smaller three-item attention queue. On Program it sits beside the next gate. Source audit events are separately titled and collapsed on Portfolio. The old static Program stage strip was removed; it did not establish observed agent progress.
- Neutral surfaces, blue actions/navigation, restrained violet agent identity, green source-backed on-track status, amber risk/review/wait, red actual blockers/rejection. All colors use scoped shared tokens. Body text remains 15–16px, secondary labels 13–14px, page titles 32px; no downloaded fonts or dependencies.
- One expandable context area distinguishes scenario time from actual read time, origin, freshness and read-only authority. Refresh retains stale records honestly after errors. Upcoming gate baseline/forecast details and source activity remain available on demand.
- One global **Ask Stratos · Preview** launcher opens a 400×560 desktop floating **Stratos Assistant**. It does not change main layout or dim the page. Context-specific drafts survive minimize/reopen and control-plane navigation. Case tabs share a draft; Portfolio, each program and each case have separate drafts. Drafts live only in component memory and are cleared on reload/leaving the control app.
- Suggestions insert editable text. Sending is disabled; Enter cannot submit a model request or start work. Opening focuses the composer, Escape/minimize returns to the launcher, and desktop focus remains nonmodal. Chat yields when a page control would be obscured; the collapsed launcher also moves above an overlapping focused control. Native evidence dialogs stay in the top layer and hide chat until dismissed. Short/visual viewport sizing, safe-area insets, scrollable conversation and reduced motion are supported.

The default Portfolio main-text proxy decreased **421 → 196 whitespace-delimited words (53.4%)**. Measurement uses `main.innerText` under the same default filters/disclosure state; it includes labels/select option text and excludes header/chat. This is a density comparison, not a precise prose-only metric. No source record text was edited.

| Before | After in overview | Detail retained |
|---|---|---|
| CR-017 · Long-context workload acceptance evidence; explanatory reason and next-step sentences | CR-017 · Workload change / Evidence gap / Inspect case | Full requested scope, reason, next step and evidence on CR-017 |
| Source lifecycle and health, with a workspace for every program | Program overview | Lifecycle/health chip and real program drilldown |
| Repeated demo, current-read and scenario labels | Connected demo · Current read disclosure | Origin, scenario UTC time, actual read timestamp, freshness and authority |
| Source updates competing with the attention queue | Recent source activity disclosure | Original audit domain, action, outcome and timestamp |

## Agent activity and mode truth

There is **no existing safe host HTTP run-read interface** in this shell. `WorkflowService` / `ActivityStore` remain host-side and untouched. The current `/portfolio` endpoint contains source records and audit events; it is not agent activity. Consequently **Activity unavailable** and **Active investigations: Unavailable** are intentional. The UI does not claim that zero investigations exist, a specialist is running, or a completed run succeeded.

Explicitly selecting **Preview agent roles** displays descriptive capabilities with the existing `coordinator`, `change_impact`, `validation_evidence`, `program_commercial` and `manufacturing` role IDs and exact `build_agent` display names. These are not assigned tasks, simulated runs or recorded results; no timestamp, elapsed time or progress is fabricated. The shared requirements specify truthful waiting, historical, escalated, failed/incomplete and verification states for later actual run integration.

| Surface | Actual behavior / mode |
|---|---|
| Portfolio, Program, source Case, options and evidence | Existing HTTP GETs; Connected demo, read only; current/stale/unavailable reads and recorded observations remain distinct |
| Agent activity / active investigations | Unavailable; no run-read adapter or polling added |
| Agent role preview | Explicit opt-in Preview; static capabilities only |
| Ask Stratos | Preview; local editable drafts; no sending, answers or model connection |
| 1A, QE-004, DR-009 and workflow/operations previews | Existing separately labeled Preview only behavior retained; no executed simulation implied |
| Approval, execution, customer acceptance | Existing source/host authority retained; no approval or execution control added |

Real governed chat integration still belongs to **08.5**. A source draft counted in Needs review does not establish a reviewable host proposal. Scheduling remains distinct from testing and acceptance, evidence coverage from customer acceptance, and runtime completion from a successful investigation.

## Changed files

- `mock_apps_ui/src/control/app.tsx`: consolidated context and global assistant mount; removed header/docked assistant.
- `mock_apps_ui/src/control/assistant.tsx` (new): floating preview, per-context drafts, focus/overlay/visual-viewport behavior.
- `mock_apps_ui/src/control/agent-activity.tsx` (new): truthful unavailable state and opt-in runtime-role capability preview.
- `mock_apps_ui/src/control/overview-model.ts` (new): scoped metric definitions, source health classification, compact attention wording and next-gate selector.
- `mock_apps_ui/src/control/portfolio.tsx`, `program.tsx`: compact program cards, prominent activity, shorter attention queue and detail disclosures.
- `mock_apps_ui/src/control/ui.tsx`, `style.css`: shared semantic badges/tokens/type/controls and responsive floating layout. Case views inherit these styles without deleting any case evidence/decision detail.
- `mock_apps_ui/e2e/control-plane.spec.ts`, `control-view-model.spec.ts` (new): preserved journey/authority assertions; replaced obsolete docked-layout assertions with floating behavior and added scope, availability, viewport and focus regressions.
- `prompts/08_1_VISUAL_REFINEMENT.md`, `AGENTS.md`, `docs/PHASE08_CONTROL_PLANE_REQUIREMENTS.md`, `docs/PHASE08_IMPLEMENTATION_PLAN.md`, `docs/PHASE08_1_HANDOFF.md`, `README.md`: exact request, bounded authorization, normative design update, current entry point and historical-handoff supersession.
- This handoff and `docs/phase08/refinement/`: new captures, contrast and verification artifacts. Prior screenshot baselines are retained.

No source API, business schema, source fixture, runtime prompt, specialist implementation, MCP permissions, Phase 06 service, Phase 07 grader, dependency/lockfile, router entry point, source-app style or deployment configuration was changed.

## Verification

All browser/API checks are **scripted local HTTP integration tests using isolated synthetic databases and simulated identities, not AI runs or actual human approvals**. The original source-app regressions perform their existing authorized test mutations only in a unique isolated test DB. The control-plane journey records GET-only access and an unchanged source portfolio payload.

| Command / check | Result |
|---|---|
| `npm run typecheck` in `mock_apps_ui/` | PASS |
| `npm run build` in `mock_apps_ui/` | PASS: TypeScript + production Vite build, no new dependencies |
| `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e -- e2e/control-plane.spec.ts e2e/control-view-model.spec.ts` | Initial focused run: 11 passed in 55.7s |
| Full `npm run test:e2e` with the same Chrome executable | **32 passed in 3.0m**: all 20 original source-app regressions, 9 control browser tests and 3 view-model tests |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py -q --junitxml=.cache/phase08-1-refinement/source-regression.xml` | 15 passed in 0.47s |
| Semantic contrast calculation from browser-computed CSS tokens | 9/9 text/background pairs exceed 4.5:1; minimum 4.92:1; details in `contrast.json` |
| Read-only browser receipt | No business writes or page errors; source portfolio before/after identical |

Coverage includes default/all/search/empty scopes; current vs obsolete/closed/superseded plans; waiting states never counted as active; missing/unknown data; source scheduling/rejection/acceptance distinctions; real evidence/deep links/back/reload; no-layout-shift; per-scope drafts; preview-only sends; focus/Escape/dialog precedence; launcher collision; mobile/short viewport; enlarged text/reflow; reduced motion; all five original app routes and computed style isolation.

Completed/recorded/escalated **agent runs cannot be rendered or tested as connected records in this slice**, because no safe run-read interface exists. We verify the unavailable state and that source events / role previews are never presented as running or successful agent investigations. No fabricated run adapter or successful trace was added solely to satisfy a test.

Skipped: paid models and graders, full Coordinator/MCP/Phase 06 and Phase 07 reliability suites (unchanged), physical mobile keyboard devices, cross-browser/screen-reader certification and native browser zoom across platforms. CSS zoom at 200%, narrow reflow and a short 375×380 viewport are tested in installed Chrome; these do not claim real iOS/Android keyboard certification. No visual rendering is substituted for an actual browser assertion.

One build command was initially issued from the repository root, which has no build script; it was corrected to `mock_apps_ui/`. No test assertion or fixture was weakened to conceal a failure.

## Screenshots and exact URLs

Captures are new files under `docs/phase08/refinement/screenshots/`. Baseline is from `http://127.0.0.1:5188/control`; final test captures use the isolated Playwright frontend at **http://127.0.0.1:5174** with source port 18000. That test server stops after tests. The equivalent review preview remains **http://127.0.0.1:5188** with source port 18008.

| View / exact test path | 1440×900 | 1280×800 |
|---|---|---|
| `http://127.0.0.1:5174/control` | [Portfolio](phase08/refinement/screenshots/portfolio-1440.png) | [Portfolio](phase08/refinement/screenshots/portfolio-1280.png) |
| Same URL, Ask Stratos open | [Floating chat](phase08/refinement/screenshots/assistant-1440.png) | [Floating chat](phase08/refinement/screenshots/assistant-1280.png) |
| `http://127.0.0.1:5174/control/programs/PRG-A17` | [Program + activity](phase08/refinement/screenshots/program-1440.png) | [Program + activity](phase08/refinement/screenshots/program-1280.png) |
| `http://127.0.0.1:5174/control/programs/PRG-A17/cases/CR-017` | [Case](phase08/refinement/screenshots/case-1440.png) | [Case](phase08/refinement/screenshots/case-1280.png) |
| Case URL + `?tab=evidence&evidence=RES-SHORT-B` | [Evidence](phase08/refinement/screenshots/evidence-1440.png) | [Evidence](phase08/refinement/screenshots/evidence-1280.png) |

Also captured: [before Portfolio](phase08/refinement/screenshots/before-portfolio-1440.png), [375px chat](phase08/refinement/screenshots/assistant-375.png), [short mobile viewport](phase08/refinement/screenshots/assistant-short-375.png), [200% chat](phase08/refinement/screenshots/assistant-200-percent-zoom.png), [200% case](phase08/refinement/screenshots/case-200-percent-zoom.png), and 1920/1024/640 reflow plus the existing DR-009 preview at both desktop sizes. Primary Portfolio, Program, Case, floating chat, narrow chat and enlarged/short viewport screenshots were visually inspected. No text-size reduction was used to reduce density.

## Preservation and stopping point

A new pre-edit hash inventory covers 459 existing files, including source/runtime/test/fixture files, five-app code, prior screenshots and pre-existing demo databases. All 59 legacy screenshots were restored byte-for-byte after the run; 21 earlier Phase 08 screenshots remain unchanged. Of the new inventory, 448 files are unchanged and 11 have expected UI/documentation edits, with no missing or unexpected changes. All pre-existing demo database files match their pre-edit hashes. An additional 2,277 historical Phase 07 files match the earlier pre-Phase-08 inventory. [verification.json](phase08/refinement/verification.json) records these results and changed files; reports/receipts are under `.cache/phase08-1-refinement/`. No Git commands, existing DB resets, credential reads, external messages or port 8000 requests occurred in this refinement.

The source read snapshot and unrelated services retain their existing limitations: separate HTTP reads do not form a distributed transaction, source timestamps are not agent timestamps, and UI freshness is not renewed evidence eligibility. Activity and real chat remain unavailable until their separately authorized future integration. The floating preview and concise composition are the current design; later prompts must not restore the docked drawer.
