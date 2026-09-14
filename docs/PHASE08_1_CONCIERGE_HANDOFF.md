# Phase 08.1 — reference-led design and Stratos Concierge

Historical handoff. The [current Overview handoff](PHASE08_1_OVERVIEW_HANDOFF.md) supersedes the navy treatment, Portfolio landing and masthead shortcut below. Earlier verification remains historical.

Implemented the [latest request](../prompts/08_1_CONCIERGE_REFINEMENT.md). This is the current visual/interaction direction, superseding the preceding small launcher, white masthead, status pills and text-only restriction. **Stop after this refinement.** Replies, governed chat/actions and later Phase 08 integration remain unconnected.

Open [Portfolio](http://127.0.0.1:5188/control), [Helios program](http://127.0.0.1:5188/control/programs/PRG-A17), [CR-017](http://127.0.0.1:5188/control/programs/PRG-A17/cases/CR-017), or the [five source apps](http://127.0.0.1:5188/). This review preview uses the existing isolated source service on port 18008. Port 8000 was not contacted during this refinement.

## Substantive design changes

The blue now defines the composition: an 80px solid deep-blue masthead, white navigation with a blue selected underline, a visibly pale-blue canvas, white program/work panels and a restrained indigo Agent workspace. Program cards share one spacious white section. Three scoped metrics replace the four-metric strip; unavailable investigation telemetry is explained beside the role previews. A larger agent workspace sits beside the three-item attention queue. Consequential status text wraps and retains its explicit meaning without a colored pill background.

Computed CSS at 100% zoom is 40px/700 for the page title, 26px/650 for section headings, 20px/600 for program names and 16px/400 body text; the masthead is 80px tall. The compact concierge measures 384×153px on the desktop test viewport, approximately the requested 150px height, with 24px margins. The expanded window is 480×680px, capped to the visible viewport. No global app zoom, screenshot scaling, downloaded fonts or new dependencies were used. CSS zoom is applied only in the enlarged-text test.

CR-017 now presents a source-state lifecycle and a two-column task panel: requested evidence on white, current finding and next step on pale blue. View evidence opens a centered source-record review with the recorded observation on the left and its applicability to the selected case on the right. This is an actual structured Validation record, explicitly labeled **Source record**, not an invented PDF. Additional original evidence, requirements, options, decisions and audit details remain available.

Evidence and agent details share a native modal with a stable header/footer, a dimmed/inert background, bidirectional keyboard focus wrapping, Escape/close and original focus/scroll restoration. The concierge becomes inert/hidden while a modal is open and capture is aborted synchronously before `showModal()`. A second modal request cannot create a stack. Narrow layouts stack the record and findings within the scrollable body. Opening and closing preserves the underlying case tab/filter/route; evidence identity continues to use the existing scoped query parameter.

One global **Stratos Concierge** serves the masthead and floating controls. Opening focuses the editable draft without changing page layout or starting the microphone. The default blue dock has context, real capability text, Open chat and a microphone; it can be reduced further. The nonmodal window preserves separate Portfolio/program/case drafts in component memory, and case tabs share their draft. Reloading/leaving the control app clears drafts. Suggestions insert text; Send remains disabled and no canned replies appear. The widget yields to overlapping focused page controls and fits short visual viewports.

## Displayed sources and capability truth

| Surface | Actual source and meaning |
|---|---|
| Program identities, stages, owners, health and next actions | Existing `GET /api/v1/programs`, through the fixed mock portfolio-reader persona. Default focus cards are Helios Atlas Inference, Northstar Boreal and Vela Stream; all eleven existing programs remain available. No new business fixture is shipped in the frontend. |
| Cases, metrics, milestones, recorded plans/jobs and source events | Existing `GET /api/v1/portfolio`. Metrics use the filtered source scope. Needs review counts distinct current draft plans on open cases; a draft is not a reviewable host proposal. At risk uses documented source-health values, with unknown health represented as unavailable. Baselines remain distinct from forecasts and commitments. |
| CR-017 evidence review | Scoped `CaseData.coverage.observations` in the portfolio response. Recorded `result` configuration/workload/model/criteria, runtime, context-bin exposure and source versions are shown alongside the source-calculated `sufficient`, mismatch codes and runtime comparison. Examples include RES-BASELINE-B and RES-SHORT-B. Existing Validation source links remain available. |
| Supplemental options and approved business documents | Existing scoped Validation option GET and allowlisted document interface retained. No arbitrary path or generic file endpoint. React escapes structured source text. |
| Manufacturing and ERP context | Existing read-only `/api/v1/manufacturing/units`, `/manufacturing/lots` and `/erp/orders`, unchanged. |
| Agent role tiles/details | Static descriptive UI metadata derived from `src/program_coordinator/application/registry.py`, the five `build_agent` identities in `agents.py`, and `controls.py::TOOL_MATRIX`. Coordinator, Change Impact, Validation & Evidence, Program / Commercial Impact and Manufacturing. These are **Agent roles · Preview**, with scope/responsibilities/allowed read-source descriptions. |
| Agent activity | **Not connected.** No safe host run-read interface exists in this shell. Role previews and source audit events are not live or recorded agent runs. There are no fabricated tasks, elapsed timers, results or success totals. |
| Concierge replies/actions; workflow/operations/illustrative scenario pages | Existing Preview behavior. Local drafts and optional browser dictation input only; no model run, sending, proposal, human approval, execution or scheduler. Illustrative scenarios are not executed simulations. |

The lifecycle never treats scheduled work as tested or accepted. Human decision advancement requires the current approved source plan with its recorded decision; lab scheduling requires an observed source job. Coverage and customer acceptance remain separate, and no agent is presented as an engineering approver. Current read time and scenario UTC time remain separately accessible. Multiple HTTP reads are not a distributed transaction.

## Voice input and live limitations

`dictation.ts` runtime-detects `window.SpeechRecognition` or `window.webkitSpeechRecognition`. It creates and starts a recognizer only after an explicit mic action, first-use provider disclosure and the user selecting Start dictation. Browser microphone permission remains browser-controlled. Feature presence is not proof of an operational speech service. Audio may go to the browser's speech provider; this implementation cannot assert a provider identity, offline processing, privacy or on-device recognition. See [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).

The implementation waits for `audiostart` before saying Listening, displays interim text separately, rebuilds the final result list to avoid repeated transcript segments, and inserts final text into the editable draft without submitting. Stop allows final results with a bounded three-second finish window. Cancel restores the pre-dictation draft. Manual typing stops recognition. Minimize/Escape, modal opening, context changes, page hiding/exiting and errors abort capture, remove callbacks and clear timers. Late callbacks cannot overwrite a new draft or another case. A 60-second hard limit prevents background capture; no automatic restart or fallback exists.

Permission denial, service denial, missing microphone, no speech, network failure, interruption, unsupported language, absent constructors and constructor failure retain typing and show concise recovery. No raw audio, transcript log, server transcription service, extra provider or persistent draft storage was added. Spoken “approve” remains editable text and grants no identity or execution authority. Replies/actions are still Preview, so the user cannot send this draft yet.

**Live microphone recognition was not tested.** All automated recognition was a controlled browser mock, including the single explicitly labeled listening screenshot. No actual audio capture, external speech request or paid model call occurred. An optional user-run check in the target browser is: open the concierge, press Dictate, read the disclosure, select Start dictation, grant browser permission, speak a short phrase, stop and edit the draft. Unsupported browsers should keep typing available. This is optional manual verification, not a claim that the target browser/provider has already been verified.

## Verification

All automated browser/API checks are **scripted local HTTP integration tests with isolated synthetic databases and simulated identities, not AI runs or actual human approvals**. Existing source-app tests make their normal test mutations only in unique test databases. The control-plane journey records GET-only access, no page errors and an unchanged source portfolio payload.

| Command/check actually run | Result |
|---|---|
| `npm run typecheck` in `mock_apps_ui/` | PASS |
| `npm run build` in `mock_apps_ui/` | PASS — TypeScript and Vite production build |
| Full Playwright with installed Chrome override below | **47 passed in 3.4m** — all 20 source-app regressions, 9 control browser tests, 4 view-model tests and 14 concierge/speech/modal tests |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py -q --junitxml=.cache/phase08-1-concierge/source-regression.xml` | **15 passed in 0.28s** |
| Browser-computed semantic text/background contrast | **14 semantic pairs checked, minimum 4.98:1**; essential form outlines also exceed 3:1. See [contrast measurements](phase08/concierge/contrast.json). This is sampled semantic-pair verification, not blanket accessibility certification. |
| Control HTTP receipt | GET only; source portfolio unchanged; no page errors |

Coverage includes all previous source-app journeys, scoped filtering/deep links/back/reload, stale/unavailable reads, metric scope, observed lifecycle semantics, preview/live distinction, new hierarchy/status CSS, scoped evidence/agent details, dialog focus/inertness/restore, concierge no-layout-shift/context/drafts/keyboard behavior, narrow/short/enlarged layouts and reduced motion. Controlled speech tests cover disclosure/no-start-on-open, actual active events, prefixed constructor, interim/final deduplication, spoken approval without submission, Stop/Cancel/manual editing, stale callbacks, timeout/no restart, errors/unsupported service and cleanup paths.

Early focused checks exposed a native-dialog keyboard boundary that could tab toward browser chrome; explicit first/last focus wrapping fixes it. The old launcher assertion was updated for the new dock/window behavior. Cleanup assertions now await modal/route completion rather than sampling before React commits the change. One typecheck command initially ran at the repository root, which has no such script; it was corrected to the frontend directory. No business fixture or authority assertion was relaxed to hide a failure.

Skipped: real microphone/provider verification, paid agents/semantic graders, full unchanged Coordinator/MCP/Phase 06/Phase 07 reliability suites, physical mobile keyboard devices, multi-browser/screen-reader certification and native browser zoom across platforms. Installed Chrome CSS zoom at 200%, narrow reflow and a 375×380 short viewport were tested; these are not physical iOS/Android keyboard certification.

## Screenshots and visual inspection

The [before Portfolio](phase08/concierge/screenshots/before-portfolio-1440.png) is the preserved immediately preceding refinement. Current captures are in `docs/phase08/concierge/screenshots/`. Most were captured against Playwright's isolated `http://127.0.0.1:5174` frontend/source port 18000, which stops after tests. Extra task-panel/detail review captures use the review preview at `http://127.0.0.1:5188`; they are labeled in the verification record. Both use the same frontend and synthetic source data.

| View | 1440×900 | 1280×800 / narrow |
|---|---|---|
| Portfolio with substantial compact dock | [Portfolio](phase08/concierge/screenshots/portfolio-1440.png) | [1280](phase08/concierge/screenshots/portfolio-1280.png) |
| Portfolio with expanded concierge | [Concierge](phase08/concierge/screenshots/assistant-1440.png) | [1280](phase08/concierge/screenshots/assistant-1280.png), [375px](phase08/concierge/screenshots/assistant-375.png) |
| Prominent Agent workspace and contextual details | [Agent details](phase08/concierge/screenshots/agent-details-1440.png), [Workspace](phase08/concierge/screenshots/agent-workspace-1440.png) | [1280](phase08/concierge/screenshots/agent-workspace-1280.png) |
| CR-017 lifecycle and work panel | [Case](phase08/concierge/screenshots/case-1440.png), [task panel](phase08/concierge/screenshots/case-task-panel-1440.png) | [1280](phase08/concierge/screenshots/case-1280.png) |
| Evidence source record and applicability | [Evidence](phase08/concierge/screenshots/evidence-1440.png) | [1280](phase08/concierge/screenshots/evidence-1280.png), [375px](phase08/concierge/screenshots/evidence-375.png), [375px findings](phase08/concierge/screenshots/evidence-findings-375.png) |
| Reflow | [200% concierge](phase08/concierge/screenshots/assistant-200-percent-zoom.png) | [Short viewport](phase08/concierge/screenshots/assistant-short-375.png) |
| Listening state | [**MOCKED Listening**](phase08/concierge/screenshots/MOCKED-listening-1440.png) | Controlled fake recognition events; **not live speech verification** |

Desktop Portfolio, expanded concierge, case panel, evidence/agent workspace, narrow concierge/evidence and enlarged/short viewport captures were visually inspected. The blue masthead/canvas and large panels are substantially different from the prior monochrome composition; status text remains plain. Scrolling is intentional rather than shrinking the UI to put every section above the fold. Additional Program, delivery-preview and 1920/1024/640 captures are retained.

Design references reviewed: [Apple WWDC 2025 hierarchy and structure](https://developer.apple.com/videos/play/wwdc2025/359/), [Typography](https://developer.apple.com/design/human-interface-guidelines/typography), [Color](https://developer.apple.com/design/human-interface-guidelines/color), [WWDC 2022 focused tasks](https://developer.apple.com/videos/play/wwdc2022/10001/) and [W3C modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/). Apple HIG pages expose limited text to the browsing tool; no native-platform rule or official palette is claimed. The banking images inform composition/scale only; Stratos facts, blue branding and web semantics remain intact.

## Files changed and preserved boundaries

- `mock_apps_ui/src/control/app.tsx`, `style.css`: blue shell, shared visual scale, scoped responsive/dialog/concierge styles and masthead entry point.
- `ui.tsx`, new `dialog.tsx`: reusable plain StatusText and accessible shared centered modal; the existing Drawer API is a compatibility wrapper around it.
- `portfolio.tsx`, `overview-model.ts`, `case.tsx`, `agent-activity.tsx`: three displayed scoped metrics, spacious cards, observed case stages, task panel, structured evidence review and runtime-role preview/details.
- `program.tsx`, `previews.tsx`: shared StatusText naming and inherited visual system; existing source/preview behavior retained.
- `assistant.tsx`, new `dictation.ts`: one global renamed/enlarged concierge, scoped drafts and bounded browser speech input.
- `mock_apps_ui/e2e/control-plane.spec.ts`, `control-view-model.spec.ts`, new `concierge-voice.spec.ts`: preserved route/source tests plus new visual, modal, lifecycle and mocked voice regressions.
- `prompts/08_1_CONCIERGE_REFINEMENT.md`, `AGENTS.md`, `README.md`, shared Phase 08 requirements/plan, preceding handoff supersession note and this handoff: exact request/current authorization/current entry point.
- `docs/phase08/concierge/`: new screenshots, contrast and verification receipt. Previous screenshots remain historical baselines.

A pre-edit SHA-256 inventory covers **4,591 files**. After restoring all 59 legacy screenshots, **4,574 are unchanged**, 17 have expected UI/documentation/test edits, and none are missing or unexpectedly changed. All 21 initial and 24 preceding-refinement Phase 08 screenshots, 4,096 historical Phase 07 artifacts and 192 pre-existing demo database/lock files match their prior bytes. The [verification record](phase08/concierge/verification.json) lists exact changed files, preserved scopes, captures, mock boundaries and the read-only HTTP receipt.

No source API, business schema, fixture, runtime agent/prompt, workflow registry, MCP permission, Phase 06 service, Phase 07 grader, source-app CSS, dependency/lockfile, deployment or router entry point changed. No Git command, credential read, external message, paid model, new scheduler or backend adapter was used. The source regressions and style-isolation browser checks confirm all five existing UIs remain intact.

## Exact start and verification commands

The existing preview is already running. To resume it in two terminals, use the same isolated DB (no reset):

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome'
DEMO_MODE=true DEMO_DB="$PWD/.demo/ui-e2e-07805828281946a69df329beaa1226e1.sqlite3" .venv/bin/mock-enterprise serve --port 18008
```

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome/mock_apps_ui'
MOCK_API_URL=http://127.0.0.1:18008 npm run dev -- --port 5188
```

For a new isolated synthetic preview source instead, run `.venv/bin/python scripts/serve_ui_test.py 18008` from the repository root and use the same frontend command. It creates a unique test DB; it does not reset the working database.

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome/mock_apps_ui'
npm run typecheck
npm run build
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e
```

The test suite starts isolated source port 18000 and Vite port 5174, then stops both. Source screenshot files generated by legacy tests were restored to their pre-run bytes; the new control-plane captures use their separate directory. Verification artifacts are linked above and under `.cache/phase08-1-concierge/`. No automatic progression to 08.2 or later work follows this handoff.
