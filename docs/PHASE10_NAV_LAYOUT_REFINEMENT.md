# Phase 10 — Navigation icons and Overview layout refinement

Implemented the [attached navigation request and direct layout follow-up](../prompts/10_NAVIGATION_ICONS.md). The attachment requests decorative navigation icons; the direct user message additionally authorizes matching Needs attention framing and the Overview section reorder.

Overview now reads: **Overview summary → Programs → Agent workspace / Needs attention**. The two panels share a white surface, subtle border, 18px corners and aligned desktop edges. Agent workspace remains wider on the left; the existing responsive breakpoint stacks the panels. The summary, program contents, agent telemetry and attention items retain their original data and behavior.

## Navigation icon set

Reused the installed **lucide-react** library. Icons are 17px with a consistent 1.75px outline stroke and 8px label gap. They inherit link color; existing blue active underline, hover and keyboard focus remain. SVGs are decorative (`aria-hidden`, non-focusable), while text labels retain each accessible name.

| Tab | Lucide icon |
|---|---|
| Overview | `LayoutDashboard` |
| Programs | `Layers` |
| Workflows & Automations | `Workflow` |
| Decisions | `ClipboardCheck` |
| Scenarios | `GitFork` |
| Knowledge & Evidence | `BookOpen` |
| Operations | `Activity` |

Icons live in the existing shared navigation metadata. The same capability predicate filters each complete link, so hidden tabs also hide their icons. Tab order, destinations and route behavior are unchanged. Search continues consuming the same label/path metadata.

## Verification and screenshots

- **9 persona/navigation browser tests passed** (50.2 seconds): all four persona matrices, permitted navigation, active-route synchronization, hidden surfaces, keyboard focus/Enter, icon dimensions/color/decorative semantics, section order, equal panel treatment and overflow checks.
- **12 existing Agent workspace browser tests passed** (42.2 seconds): completed/parallel/failure/stale/multi-run states, exact-review visibility, inspector/draft behavior and lifecycle isolation remain intact. The local viewport check now scrolls to the panels because the user explicitly moved Programs above them.
- **Typecheck and production build passed.** Desktop navigation height stays within the existing 54px envelope at 1440 and 1280 widths.
- Captures are isolated deterministic browser fixtures using existing model/speech doubles. No paid calls, microphone use, backend edits, business-state changes or Git operations. The broader backend/eval suites were not rerun for these cosmetic edits. Previous phase screenshots were not overwritten.

Actually inspected: [1440×900 navigation/Overview](screenshots/phase10-nav-layout/persona/icons-overview-1440.png), [1280×800 navigation/Overview](screenshots/phase10-nav-layout/persona/icons-overview-1280.png), [full Overview](screenshots/phase10-nav-layout/persona/overview-1440-full.png), [matching panels at 1280](screenshots/phase10-nav-layout/persona/matching-panels-1280.png), and [390px navigation](screenshots/phase10-nav-layout/persona/icons-narrow-390.png). Navigation labels remain visible at narrow widths through the existing wrapping behavior. The panels are intentionally farther down the page after Programs.

Commands run from `mock_apps_ui/`:

```sh
npm run typecheck
npm run build
STRATOS_SCREENSHOT_DIR=../docs/screenshots/phase10-nav-layout/persona npx playwright test --config playwright.persona.config.ts --reporter line --output ../.cache/phase10-nav-layout/persona-results
STRATOS_SCREENSHOT_DIR=../docs/screenshots/phase10-nav-layout/workspace npx playwright test --config playwright.workspace.config.ts --reporter line --output ../.cache/phase10-nav-layout/workspace-results
```

Both browser commands also set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to the existing local Chromium installation: `/Users/nelsonwang/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing`. Actual logs are under `.cache/phase10-nav-layout/`: `typecheck.log`, `build.log`, `persona-browser.log`, `workspace-browser.log`. Automated screenshots go to the new refinement directory through an optional test-only environment setting.

## Files changed

- `mock_apps_ui/src/control/catalog.ts`, `app.tsx`, `style.css`: shared icon metadata/rendering and minimal navigation alignment.
- `mock_apps_ui/src/control/portfolio.tsx`, `agent-workspace.css`: Overview order and matching local panels.
- `mock_apps_ui/e2e-persona/access.spec.ts`, `e2e-workspace/workspace.spec.ts`: navigation/layout assertions, updated local viewport check and separate capture destinations.
- `AGENTS.md`, `docs/PHASE10_2_AGENT_WORKSPACE.md`, `docs/DEMO_RUNBOOK.md`: current authorization/order and preview guidance.
- `prompts/10_NAVIGATION_ICONS.md`, this report and `docs/screenshots/phase10-nav-layout/`: request and review evidence.

[Open the existing isolated preview](http://127.0.0.1:5203/control/overview); refresh it to view current code. Its deterministic CR-017 result and working demo state were preserved. The normal production demo harness needs its documented stop/start frontend rebuild, without reset. This refinement stops here.
