# Phase 07 covered-fixture correction

The fresh `cr017_covered` live investigation completed with a valid final package,
but escalated an unexplained conflict between sufficient applicable evidence and
the configuration's `not_yet_demonstrated_for_WF-LC-V2` description. The failed
artifact remains unchanged at
`.cache/phase07/eval_be5424f03b1240948e988eba77091c9e`.

## Exact change

Only the `covered` synthetic source variant now sets `CFG-B-01.validation_support` to:

> Applicable completed evidence for WF-LC-V2 is recorded in RES-FULL-B-EVAL; engineering review remains pending.

This is an existing free-text field. The description is set before source
initialization; no response is patched after initialization and no API/schema is
changed. `RES-FULL-B-EVAL` keeps its completed historical status, pass flag,
2026-11-15T12:00:00Z completion time, 480-minute duration and three 160-minute bins.
The correction does not create another result or execute validation.

The initializer binds configuration, workload and criteria snapshots to the same
source records and content versions. In the new isolated fixture generation,
configuration content version 1 and the results' version-1 bindings agree.
Existing databases and historical live artifacts are not rewritten.

## Business state and regression evidence

- `RES-FULL-B-EVAL` remains the only satisfying result, with no mismatch reasons.
- Every result's configuration/workload/criteria snapshot equals its referenced
  source record, with matching content versions and no `STALE_EVIDENCE_BINDING`.
- The old contradictory support description is absent from covered coverage data.
- Engineering review remains pending; `REQ-042-V2` is still `requested`, the change
  remains `pending_impact_assessment`, and the milestone dependency is still
  `pending_assessment`. The ERP order remains `open`.
- There are no plans, decisions, new jobs, reservations, links or tasks. The public
  change response remains `not_scheduled`, with no current plan. Existing completed
  evidence confers neither engineering approval nor customer acceptance.
- An offline assessment built from actual HTTP receipts retains
  `human_review_required` with execution disallowed when only engineering review
  remains. Adding a material disagreement still produces `escalation_required`.
  This tests deterministic policy behavior, not live model reasoning.
- Real local HTTP/MCP fixture checks preserve the 25 read-only tool catalog and
  unchanged source database fingerprints. The gap and wrong-software cases still
  reject insufficient/inapplicable evidence.
- Pre/post hashes show the golden seed and all five other variant constructions
  unchanged. All 178 other inspected existing files, including prompts, policies,
  orchestration, graders, source/MCP code, Phase 06 code and prior live artifacts,
  retain their pre-change hashes.

## Files changed

1. `coordinator/evals/phase07/live_source.py` — covered-only description.
2. `tests/test_phase07_sources.py` — seven new parametrized test instances checking
   exact variant isolation, snapshot bindings and separate business states.
3. `coordinator/tests/test_phase07_runtime.py` — stronger covered HTTP/policy checks
   within the existing parametrized live-source integration test; no model calls.
4. `docs/PHASE07_COVERED_FIXTURE_HANDOFF.md` — this report.

## Verification actually run

Commands used the repository root. All exited successfully; no pytest tests failed,
errored or skipped. The focused run overlaps the required source suite and is not
added to the total of **513 distinct pytest cases**.

| Command | Actual result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase07_sources.py -q --junitxml=.cache/phase07/covered-fixture-fix-20260911/focused-source-tests.xml` | 15 passed |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py tests/test_phase06_execution.py -q` | 84 passed |
| `coordinator/.venv/bin/python -m pytest -c coordinator/pyproject.toml coordinator/tests -q` | 429 passed |
| `PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07` | 40/40 passed; hard gates PASS; zero critical failures |

Offline eval report:
`.cache/phase07/eval_5e538ca12ed048caa901a73ad658aa9b/report.md`.
Pre-change file copies, hash manifests, scope comparison and focused JUnit evidence:
`.cache/phase07/covered-fixture-fix-20260911/`.

## Ready live command — not run

```sh
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_covered --allow-paid
```

Paid live models and the optional semantic grader were not run. The contradictory
fixture value is removed, but the corrected fixture's live reasoning/escalation
outcome remains unverified. No Phase 08 work was performed.
