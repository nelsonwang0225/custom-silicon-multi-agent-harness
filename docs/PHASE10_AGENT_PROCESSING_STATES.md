# Agent Workspace — processing and idle refinement

The [direct user request](../prompts/10_AGENT_PROCESSING_STATES.md) supersedes the
participating-only roster and green completed-station presentation. The supplied
screenshot was a completed, stale read; it did not represent active processing.

| Observed state | Station / connection presentation |
|---|---|
| Fresh processing task in an active run | Filled blue station, subtle pulse, “Processing,” moving dot on its colored Coordinator branch |
| Coordinator delegated to specialists | Muted Coordinator, “With specialists”; working specialists remain lit |
| Known unused agent | Muted station, “Idle,” “Not used in this run” or “No assigned task” |
| Completed task/run | Muted station, “Idle,” with task/run completion in secondary text and observations/details |
| Queued | “Queued,” no processing light or moving dot |
| Failed / unknown / stale | Explicit failure/uncertainty, no processing animation |

Coordinator and all four specialist stations remain visible. Idle branches retain
muted structural lines but have no stationary dots that could be mistaken for
stalled work. Active branches preserve green/amber/blue/purple role colors. There
are no specialist-to-specialist lines. Reduced-motion preference stops the pulse
and dot movement without changing observed status. Historical task/run data and
inspectors are unchanged; visual idle is scoped to the selected run, not a claim
about another selected/historical run or unobserved fleet activity.

No backend, policy, source data, model invocation, polling cadence, agent authority,
approval or demo reset behavior changed. Reading the workspace never starts work.
The existing Vite preview at [5211](http://127.0.0.1:5211/control/overview#agent-workspace)
serves this change without resetting its state.

## Verification

The existing deterministic browser suite now verifies the visible idle roster;
its new transition test samples actual dot position, compares processing/idle
colors, verifies completion removes only that branch's dot, and lights Coordinator
only for its own observed work. Existing inspector, error/stale, scope, polling,
reset/persona, keyboard, responsive and reduced-motion checks remain in use.
The autonomous browser expectations were updated for the idle fifth station.

Commands run from `mock_apps_ui/`:

```sh
STRATOS_SCREENSHOT_DIR=../docs/screenshots/phase10-agent-processing \
  npx playwright test --config playwright.workspace.config.ts
STRATOS_TEST_BROWSER=webkit \
  STRATOS_SCREENSHOT_DIR=../docs/screenshots/phase10-agent-processing/webkit \
  npx playwright test --config playwright.workspace.config.ts \
  --grep 'processing light|known idle|stale and missing|narrow, enlarged|four colored|only active colored'
npm run build
```

**Results:** 15/15 Chromium browser checks passed, 5/5 focused WebKit checks passed,
and TypeScript/Vite production build passed. Actual rendered dot movement was
verified in both engines. Logs are in
`.cache/phase10-agent-processing/`. [Processing screenshot](screenshots/phase10-agent-processing/processing-1440x900.png)
and [completed/idle screenshot](screenshots/phase10-agent-processing/completed-idle-1440x900.png)
use explicitly synthetic display fixtures over isolated deterministic HTTP runs.
They do not claim live model activity. No paid models or real speech ran.

An initial browser invocation started before revised tests were applied because
of a command-directory error. The corrected run retains the full idle roster
assertions. Multi-run completed-task counts were preserved in secondary text,
and the completed-polling check now waits for the recorded response before
measuring the no-poll interval. No permission or freshness assertion was weakened.
Full backend/MCP/eval suites were not repeated for this presentation-only change;
the previous autonomous-opening handoff records their passing baseline.
