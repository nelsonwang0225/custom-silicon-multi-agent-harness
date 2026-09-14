# Two-minute QE-011 opening with the full team

The [direct follow-up](../prompts/10_MINUTE_FULL_TEAM_OPENING.md) asks for all five
agents to participate. A later direct follow-up increases the opening to two minutes
and removes internal demo-mode and pacing labels from the Agent workspace.

## Behavior

The existing deterministic preview now runs these stages after the separate
eight-second Manufacturing source-event delay:

| Stage | Minimum demo time | Visible work |
|---|---:|---|
| Coordinator triage | 12 seconds | Processing / Scoping work |
| Four parallel specialists | 84 seconds | Four Processing stations and four colored moving dots; Coordinator With specialists |
| Coordinator reconciliation | 12 seconds | Processing / Reconciling findings |
| Coordinator synthesis | 12 seconds | Processing / Preparing assessment |

The investigation lasts at least 120 seconds; source reads, indexing/retrieval and
handoff verification add their actual duration. The workspace omits internal
demo-mode, pacing, selected-task and active-investigation labels. Completed agents
return to Idle, dots stop when specialist work ends, and reduced motion remains
respected. The Coordinator stays blue while managing delegated work and lights
up during its own phases.

This pacing belongs only to the deterministic demo runner. The live Agents SDK
path retains actual model timing and existing budgets; no redundant model calls,
minimum paid latency or fake live progress were introduced. Checkpoint metadata
carries the explicit pacing value, defaulting to zero for older/real runs, and
the host exposes it only for deterministic QE-011.

## Full-team work and authority

Coordinator already owned triage, reconciliation and synthesis. Its QE-011
instructions now request all four existing specialists in parallel. Change
Impact independently reads the source-linked Engineering configuration, checks
the procedure binding and requested action scope, and distinguishes standard
investigation routing from a technical change. Its assessment and source
references must appear in the final synthesis. QE-011 analysis completeness
requires all four roles; an omitted or failed assessment cannot qualify as
complete. QE-004 retains its three-domain default and Program Owner review.

No new agent, tool, model, permission or business action was added. QE-011 still
performs only the approved Manufacturing investigation handoff with independent
readback. Material stays held; root cause, disposition and customer commitments
retain their existing authority. Reset cancels the awaited pacing, so no delayed
completion or write can survive reset. Other cases remain independently runnable.

## Replay

An existing completed opening remains historical. In **Program operator →
Operations → Demo controls**, use **Replay autonomous opening**, then open
Overview. Full demo reset followed by an Overview reload also starts the new
opening. Restarting the preview loads code without resetting records.

## Verification

Verification is scripted integration testing with isolated databases and
deterministic agents over local HTTP/MCP. No paid model calls, real microphone
access or Git operations.

| Check | Command actually run | Result |
|---|---|---|
| Pacing, participation, entry, concurrency and QE-004 regression | `PYTHONPATH=src:. coordinator/.venv/bin/pytest -q coordinator/tests/test_phase10_opening_pacing.py coordinator/tests/test_phase10_autonomous.py coordinator/tests/test_phase10_touchless_concurrency.py coordinator/tests/test_phase08_4b_quality.py --basetemp=.cache/phase10-minute-opening-tests` | 49 passed |
| Timed opening and replay | In `mock_apps_ui/`: `npx playwright test --config playwright.autonomous.config.ts` | Timed run asserts elapsed processing ≥120 seconds |
| Workspace regression | In `mock_apps_ui/`: `npx playwright test --config playwright.workspace.config.ts` | 15 passed |
| Typecheck/build | In `mock_apps_ui/`: `npm run build` | Passed after final CSS change |

Browser checks observed Coordinator Processing during triage, all four moving
specialist branches, distinct Coordinator reconciliation/synthesis, then a
verified touchless handoff with no decision. Reset/reload deduplication, concurrent
CR-017, reduced motion, stale observations and cancellation still pass.
Inspected [triage](screenshots/phase10-minute-opening/coordinator-triage-1440.png),
[all four specialists](screenshots/phase10-minute-opening/concurrent-1440.png) and
[Coordinator review](screenshots/phase10-minute-opening/coordinator-review-1440.png)
screenshots. The autonomous suite also captured completed layouts at 1440, 1920,
1280 and 390 widths.

Regenerated the isolated host OpenAPI and TypeScript declarations. Restarted only
the owned preview backend on port 18421 (UI 5211), after confirming its current
investigation had completed; health reports `deterministic_test`. Its existing
source records and recorded opening were preserved. Replay loads the new full-team
pacing. No working-demo reset was needed for this change.

Paid model latency/reasoning, broad source/MCP regressions and production load
were not rerun for this focused change. The shared harness and full-team
completeness rules were verified offline; live model compliance with the updated
instructions was not measured.
