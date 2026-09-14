# Phase 08.1 — Overview, global search and demo utilities

Implemented the [latest request](../prompts/08_1_OVERVIEW_REFINEMENT.md). This supersedes the previous navy masthead, Portfolio landing, metric strip and masthead concierge shortcut. Plain StatusText, contextual dialogs, disclosed click-to-dictate and all business authority boundaries remain. **Stop after this refinement; no later slice is started.**

Open [Overview](http://127.0.0.1:5188/overview). The canonical route is [http://127.0.0.1:5188/control/overview](http://127.0.0.1:5188/control/overview). `/portfolio`, `/control` and `/control/portfolio` remain compatible aliases. [Programs](http://127.0.0.1:5188/control/programs) retains its detailed filters. All five [source applications](http://127.0.0.1:5188/) and existing program/case/evidence links remain available.

## Visual and interaction changes

Shared light-blue-to-white gradient tokens now coordinate the masthead, Overview summary and larger Stratos Concierge. Dark ink keeps labels legible on the light surfaces; ordinary cards/conversation content remain white. The page fills the browser with a main container up to 1440px and responsive gutters. Typography remains native and readable: desktop page title 40px, sections 26px, program titles 20px, body 16px. No global app zoom, outer mockup frame, downloaded font, stock chart or invented progress percentage was added.

Overview replaces the old strip with one large visual summary: actual program count, source risk/current-review counts, a labeled health mix and the earliest available open baseline gate. Program tiles now contain just name, stage, plain health and baseline gate date. Long next-action and gate descriptions remain on Programs/program/case views. Agent tiles retain the actual coordinator/specialist names and open the existing responsibility/source/scope dialog. One Agent roles · Preview label and a connection disclosure replace repeated descriptions. The three-item attention queue retains meaningful evidence, acceptance and missing-Planner distinctions.

Global search replaces the masthead shortcut. Results group destinations, programs/customers, cases, workflows, plans/decision references, evidence/knowledge and agent definitions. Case-insensitive token matching supports IDs, titles and customer context. Keyboard navigation, Cmd/Ctrl+K, Escape, outside dismissal and focus restoration are supported. Search cannot execute commands. Its persistent Open/Ask Stratos Concierge option works for empty, matching and unmatched queries. A query appends to the existing route-scoped editable draft with a visible origin/context label; it does not overwrite, send or execute. A queued request is rejected if its route context has changed.

The larger floating concierge uses the same gradient family: approximately 440×160px compact and 544×720px expanded on desktop, capped to available space with responsive margins. It remains nonmodal and does not shift the page. Search, alerts and profile popovers share dismissal behavior; focused task dialogs retain native modality and stop capture before opening. The existing provider disclosure, permission checks, actual audio-active listening state, interim/final deduplication, Stop/Cancel, 60-second bound and cleanup remain. Cleanup now leaves an inactive unsupported-browser message intact instead of replacing it with a generic “microphone off” message. No live microphone/provider test was performed.

## Data mappings and scope

| Display | Actual mapping / limitation |
|---|---|
| Overview program set | `overviewProgramIds` explicitly selects available source PRG-A17, PRG-P01 and PRG-P02 records from `GET /api/v1/programs`. URL query filters do not secretly change Overview. All totals, health segments, program cards and attention items use this same set. Missing programs are not invented. |
| Programs, cases and metadata | Existing fixed-reader HTTP reads: `/api/v1/portfolio`, `/programs`, `/manufacturing/units`, `/manufacturing/lots`, `/erp/orders`. Source state remains current/stale/unavailable. No source read API was added or altered. |
| Health mix | Source on_track/completed, existing risk-health classifications, and explicit unknown. Counts form the visual segments; this is source program health, not technical acceptance or agent performance. Unknown health makes the At risk total unavailable. Empty/unavailable source data is separate from a measured zero. |
| Needs review | Distinct current draft source plans on open cases, using the existing `overviewMetrics` selector. Historical/superseded/closed drafts and risk-colored cards are not counted as current reviews. These are source plans, not proof of a reviewable host proposal. |
| Next gate | Earliest open baseline milestone among the displayed source programs. Labels say Baseline; no date is represented as a current customer commitment or an artificial “today” timeline. |
| Search business metadata | Loaded source programs/customer metadata, scoped `CaseData.change`, its source plans and recorded decision references, `CaseData.coverage.items[].result`, and allowlisted document metadata from the portfolio response. Program/customer membership is checked on case/plan joins. Selection opens existing program/case/options/evidence/document routes or dialogs. |
| Search definitions | Existing presentation catalog extracted to `catalog.ts`, matching the unchanged workflow registry; existing `agentRoles` names/IDs/responsibilities matching the unchanged runtime roles. These results are labeled Definition/Preview. |
| Not searched/connected | Document bodies, arbitrary files/URLs, hidden or unavailable records, host proposal envelopes and agent runs. The result panel explicitly states metadata/definition coverage and availability. No vector service, external search, indexing server, model call or new host read adapter. |
| Agent workspace | Existing role definitions only, visibly Preview. No running state, elapsed time, historical run, result or performance claim is fabricated. Source events remain separate. |

React renders escaped source text. Search never fetches a user-supplied path or URL; all targets are constructed from the existing scoped metadata and routes. No browser role string grants source permissions. Backend portfolio concepts/IDs, prompts, agent runtime, workflow registry, MCP scopes, source fixtures/APIs, Phase 06 approval/execution and Phase 07 graders are unchanged.

## Demo access and alerts

There is no applicable production authentication system. **Log in** therefore opens **Demo access**, explicitly saying that selection does not authenticate a real person or authorize approval. The existing allowed profile labels from `api.ts::personas` are Read-only viewer, Program operator and Engineering approver, corresponding to the server-owned public demo identities in `core.py`. No employee photograph, password field, credential collection or authenticated-session token is added.

After selection, initials open a profile panel with name, role, Demo identity, Switch profile and Exit demo. In this control plane all network access continues using the fixed mock portfolio reader, even when the display profile is operator/approver. No mutation UI becomes enabled. Switching or exiting remounts the read-only presentation, clears search/overlays/read markers/concierge drafts, aborts capture, returns to Overview and refreshes the same scoped source reads. Source-app persona selection and all server-side approval checks remain separate and unchanged. Guest Overview reads also use that fixed demo reader; Log in is not represented as a security barrier.

Alerts derive from open accessible source cases, selecting actual missing Planner follow-through, current draft-plan review, or requested evidence gap signals. They are source signals, never agent detections. Stable keys combine program/case, signal kind, source record ID and content version. Entries show the source record's `updated_at`, explicitly labeled Source updated, plus Inspect. The current source snapshot yields 26 alerts across the full accessible workspace; this number is calculated, not a constant or an Overview-only count.

Unread state is a component-memory set for this visit/profile. Individual and all-read actions update only that set; they cannot resolve a case, approve a plan, change evidence or write operational state. A new source record version has its own unread identity. Identity change/reload clears presentation read markers. API failure produces Alerts unavailable; no current signals produces an empty state. No model polling or background worker was added.

## Verification and limitations

All browser/API checks are **scripted local HTTP integration tests with isolated synthetic databases and simulated identities, not AI runs or real human approvals**. Existing source-app tests make their normal authorized test mutations only in unique temporary demo databases. The control-plane receipt confirms GET-only access, unchanged source portfolio state and no page errors. The new alerts test independently compares the source portfolio before/after marking read, and profile tests verify that all authorization headers remain the fixed reader.

| Actual command/check | Result |
|---|---|
| `npm run typecheck` in `mock_apps_ui/` | PASS |
| `npm run build` in `mock_apps_ui/` | **PASS** — TypeScript and Vite production build (1.23s) |
| Full Playwright using the installed Chrome override | **55 passed in 3.8m** — 20 source-app, 9 control, 4 view-model, 14 voice/modal and 8 new Overview tests |
| Additional focused speech/context regression | **9 passed in 28.0s** after final edits — all 8 Overview checks plus new mocked search/demo-access capture cleanup; 56 unique passing browser tests overall |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py -q --junitxml=.cache/phase08-1-overview/source-regression.xml` | **15 passed in 0.34s** |
| Sampled computed colors/type/gradient endpoints | **14 sampled pairs pass**, minimum 5.15:1; masthead 80px, summary 280.58px, compact concierge 440×161px. [Computed values](phase08/overview/contrast.json); this is not a full accessibility audit. |

Coverage includes aliases, consistent Overview scope, absent old filters/strip/descriptions, grouped ID/title/customer search, source-scope joins, unavailable metadata, empty/matching/unmatched Ask flows, safe draft append, simulated profile resets, unchanged read authority, alert dedup/read state and unchanged business records, unknown-health/review mapping, preserved case/evidence/agent dialogs, source outages and all five original source-app journeys. Existing mocked dictation tests retain permission, interim/final, error, timeout, cancellation, no-auto-send and cleanup coverage. The additional mock test exercises search and Demo access capture cleanup and identity draft reset directly.

The first focused run had 31 passes and four failures: a generic cleanup message obscured unsupported dictation, the masthead grid overflowed at CSS zoom, an old test targeted the replaced All programs link, and Escape lost its target after Mark all read removed the focused button. These were corrected through guarded cleanup, wrapping layout, the actual View programs target and shared popover Escape/focus handling. No business fixture or authority assertion was relaxed. Initial commands issued from the wrong working directory were corrected before verification.

Skipped: paid models/evals, six-case live smoke, real microphone/external speech, full unchanged backend Coordinator/MCP/Phase 06/Phase 07 reliability suites, cross-browser/screen-reader certification and physical mobile keyboard testing. CSS zoom at 200%, narrow/short viewports, focus and reduced-motion checks are scripted approximations, not physical-device certification. Browser SpeechRecognition may use its provider; no offline/on-device/private guarantee is made. Sending, host activity, new approval/execution UI and schedulers remain unconnected.

## Screenshots and visual review

[Before](phase08/overview/screenshots/before-1440.png) is the preserved prior navy design. Current captures use the isolated Playwright frontend on `http://127.0.0.1:5174`, source port 18000. The review preview remains `http://127.0.0.1:5188`, source port 18008. Extra profile/contrast captures use that review preview. The newly referenced screenshots were not attached to this message; the explicit written composition/palette requirements and existing application were the implementation reference.

| View | 1440×900 | 1280×800 | 375px narrow |
|---|---|---|---|
| Overview and compact concierge | [Overview](phase08/overview/screenshots/overview-1440.png) | [Overview](phase08/overview/screenshots/overview-1280.png) | [Overview](phase08/overview/screenshots/overview-375.png) |
| Global grouped search | [Search](phase08/overview/screenshots/search-1440.png) | [Search](phase08/overview/screenshots/search-1280.png) | [Search](phase08/overview/screenshots/search-375.png) |
| Source alerts | [Alerts](phase08/overview/screenshots/alerts-1440.png) | [Alerts](phase08/overview/screenshots/alerts-1280.png) | [Alerts](phase08/overview/screenshots/alerts-375.png) |
| Demo access | [Demo access](phase08/overview/screenshots/demo-access-1440.png) | [Demo access](phase08/overview/screenshots/demo-access-1280.png) | [Demo access](phase08/overview/screenshots/demo-access-375.png) |
| Expanded concierge | [Concierge](phase08/overview/screenshots/concierge-1440.png) | [Concierge](phase08/overview/screenshots/concierge-1280.png) | [Concierge](phase08/overview/screenshots/concierge-375.png) |

Also captured: the selected [demo profile](phase08/overview/screenshots/profile-1440.png). Also retained: evidence/agent workspace and case captures, enlarged/short concierge and reflow images. `MOCKED-listening-1440.png` uses controlled speech events only and is **not a live recognition check**. Desktop and narrow Overview, search, alerts, Demo access, expanded concierge and modal/reflow images were inspected for hierarchy, clipping, contrast and accessible controls. Mobile Demo access spacing was tightened after inspection. Long landing-page descriptions were removed, not shrunk; detailed source content remains accessible.

## Files and preservation

- `mock_apps_ui/src/control/masthead.tsx` (new): functional global search, source alert panel, demo access/profile and coherent overlay handling.
- `presentation-model.ts` (new): explicit Overview scope, health mix, scoped metadata search and deduplicated source-alert selectors; pure presentation only.
- `catalog.ts` (new), `previews.tsx`: extract/reuse the existing frontend workflow definitions and navigation; no backend registry edits.
- `app.tsx`, `main.tsx`: Overview navigation/title/aliases, fixed-reader profile presentation reset and same-instance concierge request. Main router changes add only aliases; source-app routing is preserved.
- `portfolio.tsx`, `agent-activity.tsx`: large real-data summary, compact program/agent tiles, shared agent detail dialog and preserved directory filters.
- `assistant.tsx`, `dictation.ts`: safe search draft append/context guard, coordinated overlay Escape and inactive-voice message preservation. Existing voice behavior and authority remain.
- `style.css`, `program.tsx`, `case.tsx`: shared gradient palette, larger widget, responsive utilities and Overview breadcrumb labels. CSS remains scoped to `.cp-root`.
- `mock_apps_ui/e2e/overview.spec.ts` (new), existing control/voice tests: new adapters/utility/identity/alert/visual checks, updated intentional UI expectations and preserved legacy behavior.
- Exact prompt, AGENTS.md, README, Phase 08 shared requirements/plan, prior handoff supersession note, this handoff and `docs/phase08/overview/` verification/captures.

A pre-edit SHA-256 inventory covers **4,606 files**. After restoring all 59 legacy source-app screenshots, **4,589 are unchanged**, 17 have expected UI/documentation/test edits, and none are missing or unexpectedly changed. The 4,096 historical Phase 07 artifacts and 200 pre-existing demo database/lock files retain their bytes. Prior Phase 08 captures are also preserved. The [verification record](phase08/overview/verification.json) lists exact changes, preserved scopes, screenshots, actual commands and the read-only HTTP receipt.

No source API/data/schema/fixture, runtime prompt/agent, workflow registry, MCP permission, Phase 06 execution, Phase 07 grader, dependency/lockfile or source-app stylesheet changed. No Git commands, working database resets, credential reads, external messages, production login, paid calls or new scheduler. Port 8000 was not contacted.

## Exact local start commands

The review preview is already running. To resume it without resetting its isolated DB, use separate terminals:

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome'
DEMO_MODE=true DEMO_DB="$PWD/.demo/ui-e2e-07805828281946a69df329beaa1226e1.sqlite3" .venv/bin/mock-enterprise serve --port 18008
```

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome/mock_apps_ui'
MOCK_API_URL=http://127.0.0.1:18008 npm run dev -- --port 5188
```

For a new isolated source DB instead, run `.venv/bin/python scripts/serve_ui_test.py 18008` from the repository root. The same frontend command applies.

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome/mock_apps_ui'
npm run typecheck
npm run build
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e
```

The final focused command, run after the last code edits, was:

```sh
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e -- e2e/overview.spec.ts e2e/concierge-voice.spec.ts --grep 'Overview|global search|Ask Concierge|demo access|source alerts|unavailable search|presentation adapters|required responsive'
```

Playwright starts isolated source port 18000 and Vite port 5174, then stops them. Legacy screenshots generated by those tests are restored from their pre-run copy; new captures are kept separately. This refinement ends here.
