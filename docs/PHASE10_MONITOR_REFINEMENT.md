# Phase 10 — Compact agent monitor

User authorization: after research of ThingsBoard, Grafana, Datadog and Langfuse, the user requested “yes go ahead and implement the above.” This replaces the tiered Coordinator/specialist stage with equal stations, without changing business authority or telemetry contracts.

## Implementation

- Five equal agent stations on desktop; three columns in smaller panels and two on phones. Existing identity icons, categorical rings, click/keyboard inspectors and exact review handoff remain.
- Each agent displays its observed state and workload, with completed/working/requested counts derived from the selected run or permitted active runs. No utilization or percent-complete estimates.
- Latest observations shows at most five timestamped task observations, newest first, with UTC times. Hover exposes the full checkpoint description; accessible button names and click/keyboard inspectors expose the same context.
- The API supplies latest checkpoint observations, not task transition history. The strip deliberately does not imply durations, continuous monitoring or historical state intervals. Multiple tasks may share one checkpoint timestamp.
- Three footer counts cover only the explicitly labeled selection: active runs, working tasks, failed tasks. Unknown/stale/unavailable observations suppress numeric totals. Coordinator delegation is not counted as a working task. Counts describe recorded tasks, not independent infrastructure health.
- Existing three-second active polling, hidden-tab pause, read expiry, model/source health inspector and recorded-run behavior are preserved. Read times are UTC; the freshness label stays visible on narrow screens. Only freshly observed working agents pulse; reduced motion remains static.

## Changed files

Runtime: `mock_apps_ui/src/control/agent-workspace.tsx` and `agent-workspace.css`.
Verification: `mock_apps_ui/e2e-workspace/workspace.spec.ts` adds a scoped count, checkpoint timestamp, keyboard and equal-station layout check.
Documentation: this report, `PHASE10_2_AGENT_WORKSPACE.md`, `DEMO_RUNBOOK.md`, and `AGENTS.md`.

## Verification

Executed from the existing repository, using isolated deterministic HTTP test services and browser response fixtures. No paid models or real speech; no working demo reset.

- `npm run typecheck --prefix mock_apps_ui`: passed.
- `npm run build --prefix mock_apps_ui`: passed; includes TypeScript checking.
- Existing workspace browser suite: 12 passed.
- New compact monitor check: passed.
- After narrow-layout refinement, reran compact monitor and narrow/enlarged-text/reduced-motion checks.

Browser command from `mock_apps_ui/`:

```sh
STRATOS_SCREENSHOT_DIR='../docs/screenshots/phase10-monitor' \
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Users/nelsonwang/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' \
npx playwright test --config playwright.workspace.config.ts --reporter line \
--output ../.cache/phase10-monitor/results
```

Focused follow-up uses `--grep 'compact monitor|narrow, enlarged'` and output `../.cache/phase10-monitor/final-results`.

Screenshots are explicitly synthetic display fixtures, not evidence of paid model execution:

- [1440 × 900](screenshots/phase10-monitor/monitor-1440x900.png)
- [1920 × 1080](screenshots/phase10-monitor/monitor-1920x1080.png)
- [1280 × 800](screenshots/phase10-monitor/monitor-1280x800.png)
- [390 × 844](screenshots/phase10-monitor/monitor-390x844.png)

Backend/eval suites and paid live runs were not rerun for this frontend-only change. No new dependencies, APIs, writes, agents, monitoring storage, source health probes, approval actions or Git operations.

Existing local preview: http://127.0.0.1:5203/control/overview (refresh to load the revised UI). Working demo state is preserved.

## Manager connections follow-up

The user's subsequent explicit request restores Coordinator above four specialists and adds lines with flowing dots. This supersedes the equal-five-station arrangement, while preserving workload metrics, checkpoint strip and inspectors. Four muted structural lines remain visible even in recorded/idle views; these indicate manager/specialist relationships, not observed transfers. A dot animates outward only for a current running run with an observed working specialist whose recorded caller includes Coordinator. Completed, stale, unavailable and hidden states do not animate; reduced motion uses static dots. This is a categorical activity cue, not packet/tool progress.

Paths follow measured button positions and resize with their content. Narrow layouts use two specialist columns with lower-row paths routed around the upper agents. No backend, authority, data or polling changes.

Verification: production build (including typecheck), existing workspace suite with updated hierarchy assertions and flow/reduced-motion/stale assertions. Screenshots are saved separately under `docs/screenshots/phase10-connections/` to preserve the previous monitor captures.

Manager-connections verification result: all 13 workspace browser tests passed (40.6s); production build/typecheck passed. Desktop 1280×800 and narrow 390×844 screenshots were visually inspected, including connector alignment and lower-row routing. [Desktop capture](screenshots/phase10-connections/parallel-1280x800.png) · [Narrow capture](screenshots/phase10-connections/monitor-390x844.png).

## Continuous colored relationship flow

The latest explicit user request supersedes activity-gated connector motion: all four branches now have continuously outward-moving dots, including recorded views. A visible “Relationship animation · Status shown on each agent” caption separates this decorative motion from business telemetry. Actual agent status, workload, stale-read handling and authority remain unchanged. Reduced motion stops the dots. Staggered phases keep the four branches visibly distinct.

Colors follow state: green completed, blue working, amber queued/delegated, red failed, slate unknown/idle/not-invoked/cancelled. Structural line colors match their dots at reduced opacity. A new browser check samples actual offset-distance changes on all four branches and verifies reduced-motion behavior.

Continuous-flow verification: production build/typecheck passed; 13 existing browser checks passed. The new test confirmed all four dots actually change offset-distance, then caught an incorrect test expectation that all four CR-019 specialists completed (the fixture correctly has three). Corrected the assertion to derive the completed count from that selected fixture. An initial focused rerun used the repository root and failed on the suite's relative provenance path; rerun from `mock_apps_ui/` as required. Runtime behavior needed no correction. Colored desktop screenshot visually inspected. No paid calls or working-state resets.

## Distinct branches, idle stop and specialist permissions

The latest request assigns stable branch colors: Change impact green, Validation amber, Program/commercial blue and Manufacturing purple. Colors distinguish branches; node status remains separately labeled. All four manager dots move only while a current permitted run in the selected scope is running and the read is fresh. Idle/completed/stale/hidden reads stop the dots, as does reduced motion.

Dashed directional specialist connections mirror `src/program_coordinator/controls.py::GRAPH` exactly: Change impact → Validation and Program/commercial; Validation → Manufacturing and Program/commercial; Program/commercial → Change impact. Manufacturing has no outbound edge. These are permitted relationships, not proof of invocation; there are no moving dots on these permission edges. An expandable textual list provides accessible direction labels. Runtime remains the authority and enforces depth/cycle/scope restrictions. The frontend metadata does not grant permissions.

Verification includes a direct AST comparison of the runtime GRAPH against displayed edges, production build/typecheck and the workspace suite. Screenshots use isolated synthetic test observations under `docs/screenshots/phase10-peer-links/`. No backend/runtime/authority changes, paid calls, Git operations or working demo reset.

Final branch/peer verification: 14 browser tests passed (42.0s), build/typecheck passed, and the five-edge runtime comparison passed. Desktop and mobile captures were visually inspected. Existing tests cover stale observations, idle stops, reduced motion, persona isolation, keyboard inspectors, scoped counts and actual moving-dot offsets.


Latest explicit visual simplification: remove all specialist-to-specialist lines, the connection legend and the Specialist connections disclosure. Retain four colored Coordinator branches with continuously moving decorative dots, including idle/recorded views. This supersedes the prior idle-stop and permission-edge presentation only; agent statuses, workload and authority remain unchanged. Reduced motion stops animation.
