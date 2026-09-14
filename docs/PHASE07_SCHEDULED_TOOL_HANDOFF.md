# Phase 07 scheduled-job tool expectation correction

The saved `cr017_scheduled` investigation completed successfully but failed its
exact `get_validation_jobs` tool-name expectation. It had instead read the known,
relevant job through `get_validation_job`, with independent Planner reads and
correct pending-test/acceptance conclusions.

## Corrected eval contract

Only this case's `expected_tools` entry changes to
`relevant_validation_job_read`. The check requires:

- An observer-owned expected job identity obtained independently from the current
  source plan: job, plan, change, program and customer IDs.
- A successful GET with retained source receipt, exact requested arguments and
  returned data. The relevant job must also appear in that call's record IDs.
- Either `get_validation_job(job_id=<expected ID>)`, or
  `get_validation_jobs(change_id=<expected change>)` whose collection contains
  exactly one entry for that expected job.
- Returned job identity/scope/plan equality, `owning_system=validation`,
  `status=scheduled`, and a positive integer content version.
- For live observations, an agent read and agreement with the current plan in
  independently projected source records. Host-only reads do not substitute for
  live agent inspection.

Wrong IDs/scope/plans, failed/blocked/unknown calls, missing or empty results,
missing receipts, unrelated reads and scheduling prose alone fail the check.
The generic `source_read` class is not used. Other exact tool-name requirements
are unchanged.

The eval observation contract now retains the necessary job-read arguments/data
and expected identity. The live adapter copies them from existing saved receipts
and intake; it does not alter source projection, agent output, runtime traces or
tool names. The offline success probe adds a read-only observer GET of the current
change/plan to establish the expected job independently. Its execution logic is
unchanged. The authored offline observation is enriched with explicit mocked
receipt identities for its already-modeled scheduled job; existing business output
values are unchanged and no source fixture is changed.

## Files changed

- `coordinator/evals/phase07/graders.py` — narrow relevant-job check.
- `coordinator/evals/phase07/models.py` — observer receipt and expected-identity fields.
- `coordinator/evals/phase07/data/cases.json` — scheduled-case tool expectation only.
- `coordinator/evals/phase07/data/observations.json` — scheduled mocked read evidence only.
- `coordinator/evals/phase07/live.py` — retain existing read evidence for grading.
- `coordinator/evals/phase07/execution_probe.py` — retain independent observer evidence.
- `coordinator/tests/test_phase07_job_reads.py` — 53 new parametrized regressions.
- `docs/PHASE07_SCHEDULED_TOOL_HANDOFF.md` — this report.

## Saved live artifact regrade

Original: `.cache/phase07/eval_11ef3d160ff34cce9be5782711eb00f3`.

Separate regrade:
`.cache/phase07/scheduled-tool-fix-20260911/regrade/report.md`.

Result: **1/1 case passed; 157/157 checks passed; hard gates PASS; zero critical failures**.
Only the required-tool check's label/verdict changed. All other 156 checks are
identical to the original results. The final package, normalized business output,
original timing/usage/status metadata and recorded call names are preserved.
The actual call remains `get_validation_job`.

Hashes confirm all 20 original eval/runtime artifact files were preserved. The
new report evaluates the prior completed live run; no new model run occurred.

Command actually run:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python \
  .cache/phase07/scheduled-tool-fix-20260911/regrade_scheduled.py
```

The script refuses to overwrite its regrade directory. Its input hashes and
separate enriched observation/source records accompany the report.

## Offline verification actually run

All commands used the repository root and exited successfully. No pytest tests
failed, errored or skipped. The focused run is included in the full coordinator
count; there are **566 distinct pytest cases**, not 619.

| Command | Result |
|---|---|
| `coordinator/.venv/bin/python -m pytest -c coordinator/pyproject.toml coordinator/tests/test_phase07_job_reads.py -q --junitxml=.cache/phase07/scheduled-tool-fix-20260911/focused-tests.xml` | 53 passed |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py tests/test_phase06_execution.py -q` | 84 passed |
| `coordinator/.venv/bin/python -m pytest -c coordinator/pyproject.toml coordinator/tests -q` | 482 passed |
| `PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07` | 40/40 passed; hard gates PASS; zero critical failures |

Offline eval report:
`.cache/phase07/eval_56d17a00964a4b59972f2f390f1f4d6f/report.md`.

New tests cover singular/plural success; incorrect requested/returned identities,
scope and plan; failed/empty/missing evidence; unrelated reads; independently bound
live context; trace immutability; missing business conclusions; and preserved
false-pass, false-acceptance and approval/execution safety checks. The full suite
also passes the existing historical-snapshot/current-version, scheduled HTTP/MCP
intake, scoped-tool and Phase 06 governance regressions.

All 180 other inspected existing files retain their pre-change hashes, including
agent runtime, prompts, source processing, source APIs, permissions, Phase 06 code,
the golden fixture and saved live artifacts. All six source-variant constructions
have identical pre/post hashes. Other cases and authored business outputs are
unchanged. Evidence lives in `.cache/phase07/scheduled-tool-fix-20260911/`.

## Ready live command — not run

```sh
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_scheduled --allow-paid
```

No paid live or semantic models were run, no commit/push was performed, and no
Phase 08 work was started.
