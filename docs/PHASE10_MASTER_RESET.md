# Master demo reset

Select **Program operator**, then the small **Reset demo** icon immediately to
the right of the alerts bell. Review the short confirmation and choose **Reset
and restart**.

The host stops active work belonging to the demo, restores the canonical records
in Engineering, Validation, Manufacturing, ERP and Planner, archives current
workflow and conversation state, and verifies the restored source records over
HTTP. CR-017, CR-019, QE-004 and DR-009 return to New. CR-019 has no recorded
eligibility results or Validation intake. Northstar Boreal returns to On track.
Shared inventory, resource reservations, forecasts and downstream records use the
existing full-reset contract.

Only after verification passes, the host arms one fresh QE-011 Manufacturing
event. It arrives after eight seconds and uses the scripted two-minute opening,
with no model calls. The four main cases use the existing live model on their
next explicit investigation; reset does not launch their paid investigations.
The scripted preview retains its two-minute agent pacing; live models retain
actual execution timing. The other four cases remain ready for their normal
walkthroughs. Their policy and human approval requirements are unchanged.

The UI clears local invocation drafts and refreshes the entire page, returning
to Overview as Program operator. This synthetic persona continuity carries no
approval or source authority. Other tabs invalidate their prior views when they
observe the new demo epoch. Reloading does not duplicate the QE-011 event.

The existing `/control-api/demo/reset` request now accepts `restart_opening`,
defaulting to false. True requires full scope, explicit RESET confirmation, the
local maintainer selector and Program operator. The existing local-origin and
epoch checks apply. Active work and source-writing postprocessors are drained
under the exclusive maintenance lease before restoration. Historical trace/eval
files remain preserved. No reset is exposed as a business API or agent tool.

A failed source restore never starts QE-011. If source reset succeeds but the
configured runtime cannot start, the result reports those outcomes separately,
records the failed opening and takes the user to Demo controls for an explicit
retry. Repeating an old request cannot reset a newer generation.

Operations → Demo controls and the CLI still support a maintenance-only reset
that leaves QE-011 idle. Their behavior is unchanged.

Verification uses isolated source/host storage and deterministic agents:

- `PYTHONPATH=src:coordinator coordinator/.venv/bin/pytest coordinator/tests/test_phase10_master_reset.py coordinator/tests/test_phase09_demo_reset.py -q` — 29 passed, covering all four completed cases, replay, active source writes, active QE-011 cancellation, stale submissions, role/scope guards, reset failures and archival preservation.
- `PYTHONPATH=src:coordinator coordinator/.venv/bin/pytest coordinator/tests/test_phase10_autonomous.py -q` — 22 passed, preserving event authority, deduplication, cancellation, touchless routing and replay behavior.
- `npx playwright test --config playwright.autonomous.config.ts master-reset.spec.ts` from `mock_apps_ui` — passed. Covers completed CR-019 → master reset → four New cases, missing initial policy results, On track Northstar, retained persona, automatic processing and moving dots, reset while active, and reload deduplication.
- `npm run build` from `mock_apps_ui` — passed.

Browser screenshots are in `docs/screenshots/phase10-master-reset/`, including
1280×800, 1440×900 and 1920×1080 confirmation layouts and the restarted Overview.
The working preview was restarted to load the host change while preserving its
two existing recorded runs. It was not reset during implementation. No paid
model or real speech calls were used for verification.
