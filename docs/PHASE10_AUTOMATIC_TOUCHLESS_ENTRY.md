# Automatic QE-011 opening and full agent roster

Subsequent [one-minute full-team refinement](PHASE10_MINUTE_FULL_TEAM_OPENING.md)
adds Change Impact participation and explicitly paced stages to the deterministic
preview. The verification below records this earlier three-specialist version.

The [latest direct request](../prompts/10_AUTOMATIC_TOUCHLESS_ENTRY.md) supersedes
explicit Prepare and the participating-only QE-011 graph. The preceding
[touchless/concurrency implementation](PHASE10_TOUCHLESS_CONCURRENT_HANDOFF.md)
still owns policy, handoff verification and independent concurrent workflows.

## Findings and behavior

Confirmed: the previous implementation deliberately required Prepare, and the
browser filtered Change Impact out of QE-011 when it had no tasks. The complete
runtime team was always one Coordinator plus four specialists. An older recorded
QE-011 Program Owner handoff remains a historical outcome; new code does not
rewrite it. The UI identifies that legacy result and explains how to replay.

The control plane now posts one local demo-entry request after its connected
source/host reads are ready. No login or launch click is needed. The host checks
the demo epoch, recovery journal, isolated QE-011 baseline and runtime readiness,
then arms the existing eight-second Manufacturing event. The entry request has
no case/action inputs and no reset or approval authority. Source facts still
determine touchless eligibility; the canonical run routes and independently
verifies the standard investigation without creating a human decision.

Concurrent tabs/entry requests serialize through a narrow entry lock, holding
the existing shared request lease so reset can drain entry before restoring state.
Normal reads and persona switching remain available during entry checks.
They return the same armed/running/completed opening. Entry never resets source
records or retries a failed/completed run. Other workflows retain the existing
three-run admission limit and separate run/task/evidence state.

All five stations stay visible for every selected run. Unused or completed agents
show Idle; completed task history remains available. Only fresh, observed active
specialists show Processing and moving colored branch dots. Reduced motion and
stale observations stop animation. An armed-event message explains the initial
eight-second interval before any agent actually starts.

## Reset to the initial state

1. Select **Program operator** in the demo identity menu.
2. Open **Operations → Demo controls**.
3. Under **Restore baseline**, select **Full demo · All demo cases**.
4. Click **Review reset…**, type **RESET**, then click **Confirm demo reset**.
5. Confirm **Baseline valid**. If another workflow is active, the existing full
   reset policy asks you to wait for it to settle and retry.
6. Open Overview and reload to start the next automatic QE-011 opening. You can
   also use **Replay autonomous opening** in Demo controls.

Full reset archives current scoped demo work, restores the baseline, disarms
QE-011 and clears stale selection/drafts. Historical verification is preserved.
The current document does not automatically re-arm after reset, even when routes
or personas remount. A fresh document can start a cleared opening. Opening Demo
controls directly also leaves it idle for inspection/reset. Scoped autonomous
reset preserves CR-017 and other unrelated history.

Opening a live-configured demo may use the existing authorized model API. The
local review preview uses deterministic test agents and is labeled Test runtime.
No artificial model delay or fake processing state was added to the live runtime.

## Existing preview compatibility

The preserved preview database predated three optional quality-policy columns.
Reads supplied their defaults, but event publication failed before starting any
agent. The stopped-demo quality installer now adds those known columns
idempotently without reseeding or changing existing business records.

Applied this additive update to the owned local review preview on port 5211 after
backing up its source database and checking that no investigation was active.
An exact before/after comparison confirmed existing business records were
unchanged. Only the failed QE-011 opening was cleared for this verification;
no full demo reset was performed on the working preview.

Reloading Overview without logging in then armed the event automatically. The
browser showed all five agents, with Validation, Program & commercial and
Manufacturing Processing while Change impact remained Idle. Run
`run_a5842c6ac20c4d229c3dec8fb5e86868` reached
`touchless_handoff_verified`; all stations returned to Idle. This was the
deterministic test runtime, not a paid model run. Independent source HTTP readback
confirmed one investigation and zero recovery plans, decisions or recovery tasks;
100 units remain held and root cause remains unknown.

## Verification

Automated verification uses isolated test databases and deterministic SDK/workflow
doubles over local HTTP/MCP; the additional existing-preview check is described
above. These are scripted integration tests, not paid AI runs or actual human
approval. No paid calls or Git operations were performed.

| Check | Actual result |
|---|---|
| `PYTHONPATH=src:. coordinator/.venv/bin/pytest -q coordinator/tests/test_phase10_autonomous.py coordinator/tests/test_phase10_touchless_concurrency.py --basetemp=.cache/phase10-entry-followup-final` | 32 passed |
| `PYTHONPATH=src:. .venv/bin/pytest -q tests/test_autonomous_quality.py tests/test_quality_recovery.py --basetemp=.cache/phase10-entry-legacy-source` | 38 passed, including legacy database compatibility |
| From `mock_apps_ui/`: `npx playwright test --config playwright.workspace.config.ts` | 15 passed |
| From `mock_apps_ui/`: `npx playwright test --config playwright.autonomous.config.ts` | 3 passed, including automatic entry, concurrent investigations, reset/reload, and full reset UI |
| From `mock_apps_ui/`: `npm run build` | Typecheck and Vite build passed |

The workspace's initial idle fixture was updated to disable automatic entry;
opening-enabled behavior is verified in the autonomous browser suite. A direct
Demo-controls visit now suppresses auto-entry through the pre-login redirect,
and the test explicitly navigates to controls after choosing Program operator.
Two existing test assertions now read source snapshots once rather than once per
record; they retain the same complete before/after comparison.

[Concurrent processing screenshot](screenshots/phase10-auto-entry/concurrent-1440.png)
shows all four specialists, an Idle Change Impact station, three Processing
stations and two independent active runs. Responsive completed-state screenshots
cover 1440, 1920, 1280 and 390 widths; the workspace suite checks reduced motion,
unknown/stale observations, task completion and actual dot displacement.

Source/MCP business contracts, RAG policy and live agent instructions did not
change in this follow-up; their prior broad checks are recorded in the linked
touchless handoff. Paid live execution, model reasoning quality and production
load testing were not repeated.
