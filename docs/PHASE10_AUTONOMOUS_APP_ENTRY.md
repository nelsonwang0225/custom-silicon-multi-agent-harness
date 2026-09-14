# Phase 10 — Autonomous QE-011 app entry

> Historical handoff, superseded by [touchless QE-011 and concurrent workflows](PHASE10_TOUCHLESS_CONCURRENT_HANDOFF.md). Current behavior requires explicit Prepare; canonical QE-011 completes without a human decision.

QE-011 now demonstrates unsupervised back-office work immediately after a user
enters the Stratos control plane. The browser issues one bounded entry request,
the host schedules the existing eight-second Manufacturing event, and the existing
quality workflow performs the investigation. The workflow still stops at Program
Owner review; app entry grants no approval, execution, lot-release or commitment
authority.

## Lifecycle

1. The first control-plane mount in a browser tab reads the current demo epoch and
   posts `POST /control-api/demo/autonomous/enter`.
2. The host serializes entry requests. Idle state is prepared once; armed, running,
   completed and failed states are returned without reset or replay.
3. After eight seconds, Manufacturing publishes the immutable QE-011 event and the
   existing `yield_exception_recovery` workflow starts under its automation actor.
4. Agent Workspace shows observed Processing stations and moving dots. When analysis
   completes, it shows the recorded idle stations and Program Owner handoff.
5. A scoped/full reset cancels and drains work. The same tab does not immediately
   re-arm; a new app session or explicit Replay action starts a new opening.

Host process startup never arms or resumes QE-011. Saved generic automation
configurations remain metadata-only. In a live-model configuration, app entry can
incur one bounded workflow's model calls; deterministic verification makes none.

## Verification

- `PYTHONPATH=src:. coordinator/.venv/bin/pytest coordinator/tests/test_phase10_autonomous.py -q`
  — 20 passed.
- `npm --prefix mock_apps_ui run build` — passed.
- `npx playwright test --config playwright.autonomous.config.ts` from
  `mock_apps_ui/` — 2 passed, including automatic entry → agent processing → human
  handoff, reset/new-session replay, and reset-before-delay cancellation.

No paid model call, real speech test, approval, execution or Git operation was run.
