# Phase 08.1 — darker blue, quieter layout

> Latest gradient follow-up: retain darker blue edges with a softer light-blue center; no white stop. Masthead and Concierge use `linear-gradient(90deg, #6F98C2 0%, #B8CFE5 50%, #6F98C2 100%)`; the summary uses `#9FBEDC` → `#C5D9EB` → `#9FBEDC`. This supersedes both the white-centered trial and the earlier one-direction stops below. `npm run build` passed, including TypeScript. Read-only browser checks at 1440×900 and 375×812 found no overflow or page errors; desktop was visually inspected. No full regression rerun or live microphone check for this CSS-only adjustment. [Current desktop](phase08/blue-gradient/overview-1440.png) · [Narrow](phase08/blue-gradient/overview-375.png) · [Check record](phase08/blue-gradient/verification.json).

Implemented the [requested refinement](../prompts/08_1_MINIMAL_DESIGN_REFINEMENT.md) in the existing app. [Open the local preview](http://127.0.0.1:5188/control/overview). The changes are presentation-only; search, demo profiles, alerts, voice drafts, source reads and business authority retain their existing behavior.

## Research and design decisions

Apple recommends consistent use of color, sufficient contrast, and text or symbols alongside semantic color. Its typography guidance uses size and weight to establish hierarchy and discourages unnecessary typeface variation. These principles support the retained native font, readable dark ink and plain named statuses. [Apple Color](https://developer.apple.com/design/human-interface-guidelines/color), [Apple Typography](https://developer.apple.com/design/human-interface-guidelines/typography).

OpenAI's UI guidance recommends restrained color, platform fonts, consistent spacing, clear action hierarchy and outlined iconography. That document governs apps embedded in ChatGPT; here it is a design reference, not a requirement to adopt ChatGPT's architecture or exact components. [OpenAI UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines).

The resulting Stratos design uses a slightly deeper blue as requested, a more neutral page, fewer nested containers and quieter dividers. The retained gradient is a deliberate Stratos choice. No Apple/OpenAI branding, proprietary fonts, screenshots, decorative imagery, libraries or assets were imported. Online research was limited to public design guidance.

- Masthead and Concierge now share `#6F98C2` → `#92B1D1` → `#CBDCEE`. This replaces the previous `#8AB2D4` start and near-white end. Dark ink remains `#1B2B42`.
- The summary uses `#9FBEDC` → `#D4E3F1` → `#F2F6FA`; the canvas is neutral `#F7F8FA`. Shared gradient, radius, border and shadow tokens keep the system consistent.
- The Overview title and existing source-read disclosure/Refresh share a desktop row and stack on mobile. Opening the disclosure still shows the original scenario time, actual read time, freshness and authority.
- The real-data summary keeps its counts and baseline gate, with a slimmer labeled health bar. No values, health semantics or scope selectors changed.
- Program cards sit directly beneath the Programs heading. Their nested gate separators and the section's outer card are removed. Agent and attention sections also lose their redundant outer boxes; the coordinator still has restrained emphasis and roles remain visibly Preview.
- Concierge retains its larger dimensions and per-context drafts. A white Open chat action and softer shadow clarify its controls. Minimize, explicit microphone consent, cleanup and preview-only sending are preserved.

## Verification

These are **scripted local browser/HTTP checks using isolated synthetic databases and simulated identities**, not AI runs or real human approvals.

| Check actually run | Result |
|---|---|
| `npm run typecheck` in `mock_apps_ui/` | PASS |
| `npm run build` | PASS — TypeScript and Vite, 1.18s Vite build |
| Full installed-Chrome Playwright suite | Initial full run: **55 passed, 1 search timing failure (4.8m)**. After correcting the navigation wait, that test passed **3/3 repeats (11.1s)**. All 56 scenarios have passing results across these runs; the full suite was not repeated after the test-only wait correction. |
| `node .cache/phase08-1-minimal/visual-check.mjs` | PASS — no horizontal overflow at 1920, 1440, 1280 or 375px; source disclosure fits at 1280/375. All 12 sampled text pairs exceed 4.5:1 (minimum 4.72:1). [Measured values](phase08/minimal/visual-check.json). |
| Source authority and artifact preservation | PASS — 4,681 of 4,693 inventoried files unchanged; exactly 12 expected UI/test/documentation edits. Restored 103 prior screenshots. No missing/unexpected changes. [Verification record](phase08/minimal/verification.json). |

The browser suite covers all five source apps, scoped current data, route compatibility, source outages, search, alert read markers, fixed-reader demo selection, agent/evidence dialogs, keyboard focus, CSS isolation, 200% CSS zoom, short/narrow views and mocked speech. Screenshot destinations changed to the new `minimal` directory; no business assertions were relaxed. The initial full run passed 55 tests and timed out in one search test: it entered a new query before the preceding evidence-dialog URL transition completed. The test now explicitly waits for dialog removal and the evidence route before typing. The failure trace is preserved under `.cache/phase08-1-minimal/first-full-failure/`. An initial anchored grep selected no tests because Playwright matches the full title; the corrected unanchored command below runs the intended test. A formatting check also caught one newly lengthened capture-receipt path; it was formatted and rechecked. The source context component was moved without changing its reads or labels.

Skipped: paid calls/evals, six-case live smoke, real microphone/external speech, unchanged backend pytest/Coordinator/MCP/Phase 06/07 suites, physical device/keyboard checks and cross-browser/screen-reader certification. Contrast checks sample actual palette pairs; they are not a full accessibility audit. The new header/context layout is also checked with the disclosure open at 1280px and 375px.

Screenshots were visually inspected for the deeper blue, simpler card hierarchy, readable text, popup controls and narrow-screen clipping. The wide desktop, expanded Concierge, search, alerts, Demo access and open source-context views retain the expected hierarchy.

## Screenshots

[Before at 1440](phase08/minimal/screenshots/before-1440.png) · [After at 1440](phase08/minimal/screenshots/overview-1440.png) · [Wide desktop](phase08/minimal/screenshots/overview-1920.png) · [Agent workspace](phase08/minimal/screenshots/workspace-1440.png).

| View | 1440×900 | 1280×800 | 375×812 |
|---|---|---|---|
| Overview | [Desktop](phase08/minimal/screenshots/overview-1440.png) | [Laptop](phase08/minimal/screenshots/overview-1280.png) | [Narrow](phase08/minimal/screenshots/overview-375.png) |
| Search | [Desktop](phase08/minimal/screenshots/search-1440.png) | [Laptop](phase08/minimal/screenshots/search-1280.png) | [Narrow](phase08/minimal/screenshots/search-375.png) |
| Alerts | [Desktop](phase08/minimal/screenshots/alerts-1440.png) | [Laptop](phase08/minimal/screenshots/alerts-1280.png) | [Narrow](phase08/minimal/screenshots/alerts-375.png) |
| Demo access | [Desktop](phase08/minimal/screenshots/demo-access-1440.png) | [Laptop](phase08/minimal/screenshots/demo-access-1280.png) | [Narrow](phase08/minimal/screenshots/demo-access-375.png) |
| Concierge | [Desktop](phase08/minimal/screenshots/concierge-1440.png) | [Laptop](phase08/minimal/screenshots/concierge-1280.png) | [Narrow](phase08/minimal/screenshots/concierge-375.png) |

Additional captures include [demo profile](phase08/minimal/screenshots/profile-1440.png), source-context disclosures, preserved evidence dialogs and CSS-zoom reflow. `MOCKED-listening-1440.png` is explicitly generated from controlled speech events; no microphone was used.

## Changed files and boundaries

- `mock_apps_ui/src/control/style.css`: shared deeper-blue tokens, neutral canvas, quieter surfaces, card/summary/Concierge spacing and responsive title/context layout.
- `ui.tsx`, `app.tsx`, `portfolio.tsx`: extract the existing `SourceContext` display and place it beside Overview; retain it in the shell for other routes. Same HTTP identity, timestamps, error handling and refresh callback.
- `assistant.tsx`: presentation class on Open chat only; no speech/runtime changes.
- Three existing browser specs: capture paths move to `docs/phase08/minimal/` and its receipt cache.
- Current request, shared requirements, plan, README and AGENTS.md record the latest design direction; this handoff and visual evidence document it.

Backend, source business data, agent prompts/runtime, workflow registry, MCP scopes, Phase 06 approval/execution, Phase 07 graders, dependencies and source-app styles remain unchanged. No Git operations or later-phase work.

## Exact local commands

The preview uses the existing isolated source DB. To restart without reseeding it, run in separate terminals:

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome'
DEMO_MODE=true DEMO_DB="$PWD/.demo/ui-e2e-07805828281946a69df329beaa1226e1.sqlite3" .venv/bin/mock-enterprise serve --port 18008
```

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome/mock_apps_ui'
MOCK_API_URL=http://127.0.0.1:18008 npm run dev -- --port 5188
```

Verification:

```sh
cd '/Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome/mock_apps_ui'
npm run typecheck
npm run build
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e
```

The corrected search/navigation regression was repeated with:

```sh
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e -- e2e/overview.spec.ts --grep 'search groups' --repeat-each=3
```

Playwright starts isolated source port 18000 and frontend 5174, then shuts them down. Supplemental read-only screenshots use preview 5188/source 18008. The design pass ends here.
