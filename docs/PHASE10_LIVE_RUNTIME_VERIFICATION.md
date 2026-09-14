# Live runtime verification

Verified against the existing configured `gpt-6-astra` model on September 12,
2026 (local time). The four main cases used real Responses API calls and scoped
MCP/HTTP source access in a newly isolated demo dataset. QE-011 ran concurrently
with its scripted Coordinator and all four specialists.

| Case | Model responses | Source tool calls started | Model-run duration | Result |
| --- | ---: | ---: | ---: | --- |
| CR-017 | 21 | 36 | 201.4 s | Completed analysis; Engineering review required |
| CR-019 | 11 | 12 | 114.4 s | Completed; standard intake handoff independently verified |
| QE-004 | 10 | 10 | 111.6 s | Completed; Program Owner review required |
| DR-009 | 9 | 16 | 110.7 s | Completed; Program Owner review required |
| QE-011 | 0 | 8 observed reads | Scripted minimum 60 s | Standard quality handoff verified |

All 51 recorded model responses returned HTTP 200 with the configured model.
Recorded usage totals 515,850 tokens across all model calls, including repeated
input context. Actual usage and latency are observations of this check, not
promises for later runs. No human approval, governed execution, lab result,
hold release or customer acceptance was performed.

Artifacts: [sanitized verification summary](../.cache/phase10-live/verify_4d90fa7ddeb3496a8ee524727060d96a/verification.json).
Each referenced run directory contains its existing report, exact source calls,
checkpoint and sanitized SDK trace metadata. Local trace IDs are not a claim of
verified Platform trace export.

Commands and outcomes:

- `PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_live.verify --run-paid`
  completed all five runs. Its initial final-wait condition consulted the saved
  event status instead of the computed status; the probe process was stopped
  after confirming all runs completed. That polling condition was corrected.
  No paid rerun was needed.
- `PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_live.verify --summarize .cache/phase10-live/verify_4d90fa7ddeb3496a8ee524727060d96a`
  returned success from the persisted live reports and verified handoff metadata.
- `pytest coordinator/tests/test_phase10_live_runtime.py`: 3 passed. Covers fixed
  case routing, no scripted fallback, missing-key scripted opening, immutable
  saved modes and simultaneous trace isolation. Model boundaries are mocked.
- Existing master-reset and opening-pacing tests: 8 passed. Autonomous,
  workspace and touchless concurrency tests: 47 passed.
- Operations regression tests: 12 passed, including the adjusted explicit
  configuration/store arguments in the live metadata test. No paid calls.
- `npx playwright test --config=playwright.autonomous.config.ts master-reset.spec.ts`:
  1 passed using the isolated offline browser fixture. Reset, five-case replay,
  active processing and moving dots were checked.
- `npm run build`: passed (TypeScript and Vite production build).
- Actual browser inspection at port 5211 showed **Next investigation: Live AI**
  for CR-019 while its previous result remained **Scripted demo**, and QE-011
  continued to show **Scripted demo**. The two original run IDs were preserved
  across switching the host; the working demo was not reset.

The default demo host and explicitly live preview now install the same runtime.
The preview remains at `http://127.0.0.1:5211/control/overview`. Existing reviews
and downstream steps remain separate. Paid downstream CR-017 reassessment and
Concierge conversation smoke were not repeated in this targeted runtime change.
