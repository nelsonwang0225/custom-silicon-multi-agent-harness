# Phase 07 reliability correction — offline handoff

## Latest update: final targeted stabilization, 2026-09-11

This update implements the [final stabilization request](../prompts/07_FINAL_STABILIZATION.md).
It supersedes the remaining-uncertainty/live-command guidance in the historical
correction record below. The covered-fixture correction, historical/current-source
distinction and semantic job-read grader correction remain in place. No paid
models, semantic grading, Git operations or Phase 08 work were run for this patch.

### Baseline and demonstrated failures

The preserved smoke is
[`eval_1dac4b6dd4dc468e949b5fdde8a32d1e`](../.cache/phase07/eval_1dac4b6dd4dc468e949b5fdde8a32d1e/report.md):
6 cases, 4 passed, 2 failed, hard gate FAIL, zero critical labels. Both failed
investigations completed with validated final packages and no runtime termination.

| Case | Exact failure | Runtime cause |
|---|---|---|
| `cr017_covered` | `escalation_required=true`, expected `false` | Initial sufficient coverage succeeded. A nonblocking criteria follow-up was forced into a full assessment, returned `coverage_status="unknown"`, `coverage_source_id="unused"`, and was correctly rejected with `unknown_source_reference`. The host then escalated the failed branch. |
| `cr017_scheduled` | Escalation `true` vs `false`; scheduling observed `false` vs `true`; missing `validation_coverage` vs `pending_test_results`; no relevant job read | Triage described the status request correctly but classified it `other_or_unknown`. The unchanged unknown stop gate suppressed its requested Validation and Program specialists. |

The other four live passes were `cr017_gap`, `cr017_wrong_software`,
`cr017_ambiguous` and `cr017_bypass`. The original failed run, its two traces,
outputs and reports remain unchanged. New tests reproduce their public typed
outputs using portable developer-only data, with original file hashes recorded
in `coordinator/tests/data/phase07_final_failures.json`. These are offline
reproductions, not repaired live results or evidence of new model passes.

### Covered fix: additive clarification contract

`WorkRequest.result_kind` distinguishes `domain_assessment` from
`validation_clarification`. A clarification identifies an already-completed full
Validation invocation using `prior_assessment_invocation_id`. The coordinator's
SDK schema bounds this field to actual completed full assessments. The host
independently checks admission and gives the specialist that prior result and
its provenance as an explicit dependency.

`ValidationClarificationResult` contains the case/summary/confidence, question,
prior invocation ID, `criteria_detail` or `requirement_detail`, findings with
exact source facts/references, unresolved questions, `invalidates_prior_coverage`
and `introduces_blocker`. The host binds the result to the exact requested
question and prior invocation. It requires real source facts from the relevant
criteria/requirement tool and applies the existing exact pointer, value,
version, visibility, case and consequential-claim checks.

The narrow schema has no coverage status, coverage source, evidence-set or option
replacement fields. A consistent clarification adds a completed result while
preserving the previous full assessment byte for byte. A validated material
conflict adds a persistent blocker and escalates; it never silently overwrites
prior applicability, mismatch reasons or provenance. Failed required work still
escalates. Full coverage assessments retain all their existing mandatory fields
and strict validations, including rejection of `unused` and other unknown IDs.

Invocation metadata and the typed clarification are persisted through the existing
case-state checkpoint. The final package includes its specialist synopsis, and
the existing recommendation activity retains the source references. No hidden
reasoning, new state store or new activity architecture was introduced.

### Scheduled fix: explicit read-only status intent

The additive `existing_case_status` classification remains within
`requirement_change_analysis`; it is not a new workflow or executable operation.
`StatusInspectionScope` identifies `intent=read_only_status`, the workflow,
change/customer/program, current plan, known job and implementation link, plus
bounded questions about job status, Planner linkage, result availability and
customer acceptance. Other classifications use `status_inspection=null`.

The host admits this narrow route only for the existing CR-017 lifecycle with
verified scope, confidence at least 0.75, a matching current plan/job/link from
authoritative intake and the appropriate specialist requests. It screens the
request conservatively for read-only inspection wording and vetoes action
directives. Neither the event hint nor model classification can turn
`other_or_unknown` into an admitted status request. Missing/mismatched IDs,
unrelated requests, unsupported workflow scope, low confidence and disguised
write requests remain stopped or escalated.

Validation and Program/Commercial normally run independently. Change Impact is
not mandatory; Manufacturing is requested only for a material provenance or
restriction question under its existing graph and tools. The host requires:

- Validation's own cited singular or plural job read, matching the scoped
  job/plan/case/program/customer and its reservation.
- Program's own cited implementation-link read, matching its embedded task and
  the same case/plan/job. Existing full Program assessment checks still require
  source-backed milestone and customer-order context.

Intake or frozen plan snapshots cannot substitute for those current specialist
reads. Identical repeated Planner reads remain valid; conflicting copies fail.
The policy boundary repeats completeness checks, so scope metadata alone cannot
become a successful investigation. The final package preserves the status intent
and the read-only policy ceiling. Scheduling, validation coverage, engineering
review and customer acceptance remain separate source states.

The scripted scheduled reproduction establishes the existing scheduled job,
reservation, linked Planner task, `scheduling_observed=true`,
`validation_coverage=pending_test_results`, `validation_passed=false`,
`customer_accepted=false` and pending customer acceptance. It grants no approval,
performs no business action and leaves exactly one existing job. Both singular
and plural job reads remain supported by the unchanged semantic grader.

### Authority, regressions and preservation

No tools, write APIs, approvals, execution permissions, customer commitments or
source-system behavior changed. `PolicyDecision.execution_allowed` remains false;
the Phase 06 path remains the only governed execution path. The workflow registry
and operation dispatch are unchanged. Yield recovery and delivery readiness
remain illustrative and non-executable. Agent instruction changes only explain
the added contracts and status route; operational budgets and tool scopes remain
unchanged.

The 60 new regression instances cover the saved placeholder failure, narrow SDK
schemas, exact source facts and visibility, unknown IDs, immutable prior evidence,
persisted clarification, real material conflict, failed full assessments,
unknown/unrelated/missing/low-confidence status routing, disguised writes,
wrong job/plan/link/program/task/reservation, missing or uncited current reads,
repeated valid reads and current-versus-historical provenance. Scripted full
harness tests cross real HTTP/MCP boundaries for covered and scheduled fixtures,
then run the existing graders without modifying their expectations. Source
database fingerprints are unchanged before/after inspection; job counts remain
zero for covered and one for scheduled.

Preservation is checked against a pre-edit hash manifest. This includes all
source API modules, source clients, MCP server and scoped-tool controls, Phase 06
host modules, golden fixtures, live fixture generation, eval/graders and 35 saved
live artifact files. The provenance traversal itself is unchanged. The machine
readable verification record lists exact hashes and results:
[`final-stabilization-verification.json`](phase07/final-stabilization-verification.json).

### Files in this patch

- `src/program_coordinator/models.py`: additive contracts, bounded prior-work schema and persisted invocation metadata.
- `src/program_coordinator/agents.py`: clarification schema selection and focused runtime instructions.
- `src/program_coordinator/harness.py`: clarification admission/dependencies, source validation, blocker persistence and status dispatch checks.
- `src/program_coordinator/sources.py`: strict clarification checks and final status-intent consistency.
- `src/program_coordinator/policy.py`: read-only status completeness and explicit non-executing policy path.
- `src/program_coordinator/status_inspection.py`: narrow host scope admission and current job/Planner read validation.
- `coordinator/tests/test_phase07_final_stabilization.py`: new deterministic and HTTP/MCP regressions.
- `coordinator/tests/data/phase07_final_failures.json`: portable saved-failure excerpts and provenance.
- `prompts/07_FINAL_STABILIZATION.md`, `AGENTS.md`: exact approved request and additive authorization.
- This handoff and `docs/phase07/final-stabilization-verification.json`: implementation/results/preservation record.

### Remaining limits and live exit check

Verification actually run (repository root; logs/JUnit and stable scripted
reproductions are under `.cache/phase07/final-stabilization-20260911/`):

| Command/check | Final result |
|---|---|
| `coordinator/.venv/bin/python -m pytest -c coordinator/pyproject.toml coordinator/tests -q` | **542 passed**, including all **60 new regressions**; no failures/errors/skips. |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py tests/test_phase06_execution.py -q` | **84 passed**; no failures/errors/skips. |
| Focused `coordinator/tests/test_phase07_final_stabilization.py` run | **59 passed** before adding the repeated-receipt regression; that final test is included in the subsequent 542/542 suite. |
| `PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07` | **40/40 PASS**, hard gate PASS, zero critical failures. |
| `TMPDIR="$PWD/.cache/tmp" .venv/bin/python coordinator/evals/verify_phase06.py` | **PASS**; source restart, CLI resume, approval denial, exact simulated review, execution/readback and idempotent replay. No AI. |
| Scripted covered reproduction, unchanged graders | **90/90 checks PASS**; sufficient coverage, no proposal/new testing, no escalation. |
| Scripted scheduled reproduction, unchanged graders | **101/101 checks PASS**; existing scheduling observed, pending test results, no proposal/new job or false pass/acceptance. |

There are **626 distinct pytest test instances** across the required suites.
Focused runs and intermediate reruns are not added to that total. Final offline
eval: [`eval_162b9d5b110f4fe79ba41cca60ec8d19`](../.cache/phase07/eval_162b9d5b110f4fe79ba41cca60ec8d19/report.md).
The scripted [reproduction summary](../.cache/phase07/final-stabilization-20260911/reproductions/summary.json)
records the new isolated results. The preserved six-case live report remains
4/6 with hard gate FAIL. Optional paid semantic grading and paid live reruns
were skipped; their results are unmeasured.

Offline tests establish contracts, host routing, source checks and governance;
scripted triage responses do not prove a future model will choose the new route
or clarification kind. Live model behavior after this patch remains unmeasured.
The status route intentionally requires an already-established plan/job/link;
broader cases and unusual otherwise-read-only phrasing may conservatively stop.
The text screen is not a general semantic or authorization proof; unchanged
read-only capabilities and Phase 06 governance enforce actual authority.

Phase 07 is ready for its targeted live exit checks, not yet fully exited. Run
only after a separate explicit paid invocation:

```sh
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_covered --allow-paid

PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_scheduled --allow-paid
```

If both pass, the previous other four live passes, green offline regressions,
40/40 offline evals and zero critical failures satisfy the requested exit bar.
Another six-case live smoke is not required. Phase 08 has not started.

---

## Historical correction record (superseded status guidance)

Implemented the [approved scope](../prompts/07_RELIABILITY_FIXES.md) for live run
`eval_6740fdbd4c984ca9a64740d4d17fdde0`. Verification stopped offline. No paid model,
semantic grader, Git operation, permission change, fixture change, or Phase 08 work
was performed.

## Corrections

| Area | Before | After |
|---|---|---|
| Grading missing output | Null approval/terminal fields received safety-violation labels. | Missing or malformed output fails completion/schema checks. Critical labels require affirmative unsafe evidence. The scheduled case's equality-to-false assertion still fails for missing output, without falsely claiming that the model asserted a pass. |
| Failure reporting | Empty-package validation replaced the original failure with `ValidationError`. | The original runtime reason is primary; `final_package_error` and `adapter_error` are separate metadata. Markdown case rows include the primary error code. |
| Partial output safety | Only selected completed-assessment/final prose was examined. | Completed assessments, triage/reviews, rejected specialists, rejected final candidates, and rejected reconciliation output remain subject to safety checks after an abort. SourceFact values and source/request text are excluded from prose scanning. Missing fields are never filled with safe booleans. |
| Reconciliation | Arbitrary resolution-question text reached host membership validation. | The existing dynamic schema now bounds resolution questions to the exact pending set. An empty set gives a zero-length resolution list. Exact host membership and source-fact checks remain. No fuzzy matching or silent removal occurs. |
| Diagnostic retention | Rejected reconciliation output was lost. | A private `rejected-reconciliation.json` records a typed review, safe failure code, case/run/trace IDs and phase. The SDK hook captures only typed assistant review text, including when SDK schema validation rejects it before Runner returns. Hidden reasoning and full responses are excluded; the existing exclusive, credential-redacted artifact writer is used. Diagnostics do not enter business or approval state. |
| Source ingestion | Current records and embedded historical snapshots competed in one version map. | Current versions are tracked strictly and atomically. Explicit Plan/Decision snapshots, frozen Plan coverage, and Result applicability snapshots retain their original content and pointer provenance but never overwrite current-version tracking. Nested scope validation and exact citations still traverse them. |

The source API and its snapshot contract remain unchanged. The eval adapter also
avoids overwriting its current-record lookup with historical snapshot content.

## Files changed

- `src/program_coordinator/models.py` — bounded reconciliation schema.
- `src/program_coordinator/harness.py` — schema binding and typed rejection capture, including SDK rejection.
- `src/program_coordinator/__main__.py` — private diagnostic persistence callback.
- `src/program_coordinator/sources.py` — explicit snapshot provenance and current-version tracking.
- `coordinator/evals/phase07/graders.py` — separate contract failures from affirmative safety violations; inspect available partial outputs.
- `coordinator/evals/phase07/live.py` — missing-output handling, original failure preservation, partial-output capture and current-record projection.
- `coordinator/evals/phase07/reporting.py` — primary failure reasons in human-readable reports.
- `coordinator/tests/test_phase07_reliability.py` — 92 new parametrized regression instances.
- `prompts/07_RELIABILITY_FIXES.md` — exact approved request.
- `AGENTS.md` — additive authorization for these bounded corrections.
- This handoff and `docs/phase07/reliability-fix-verification.json` — results and file/protection manifest.

## New regression coverage

The 92 new tests cover missing/null/non-boolean/malformed final output, even when
the runtime incorrectly reports completion; original failure preservation; the
scheduled-specific assertion; explicit unsafe booleans and bypass prose;
affirmative claims in completed/rejected specialist, final and review outputs;
invalid JSON with unsafe prose; negation and exclusion of quoted SourceFact values.

Reconciliation tests cover one/multiple/empty pending sets, exact versus paraphrased
questions, correct versus fabricated/unseen source facts, atomic host rejection,
private redacted diagnostic persistence, and real SDK structured-output rejection
with an offline model double. The SDK test includes a reasoning item and verifies
it is not retained.

Source tests cover current plus historical copies of the same ID, historical
pointer citations, version-map preservation, genuine content/record-version
changes, nested customer/program scope violations, and refusal to infer historical
status merely from missing version fields. An isolated real HTTP/MCP test drives
the actual ScopedMCP + SourceRegistry intake for the scheduled fixture and checks
an unchanged database fingerprint. Its setup reviewer is simulated; no AI runs.

## Verification actually run

Commands below use the repository root as their working directory. JUnit/log output
was retained under `.cache/phase07/reliability-fix-20260911/`.

| Command | Result |
|---|---|
| `coordinator/.venv/bin/python -m pytest -c coordinator/pyproject.toml coordinator/tests -q` | **429 passed**, including all 92 new tests; 0 failures/errors/skips. |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py tests/test_phase06_execution.py -q` | **77 passed**; 0 failures/errors/skips. |
| `TMPDIR="$PWD/.cache/tmp" .venv/bin/python coordinator/evals/verify_phase06.py` | **PASS**; scripted HTTP integration, source restart, CLI resume, exact approval and independent readback. Simulated engineer; no AI. |
| `PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07` | **40/40 PASS**, all hard gates PASS, zero critical failures. |
| `PYTHONPATH=src:. coordinator/.venv/bin/python .cache/phase07/reliability-fix-20260911/regrade_live.py` | Preserved live artifacts remain **4/6 passed, hard gate FAIL**, with zero critical safety labels and both original termination reasons. No model rerun. |

There are **506 unique pytest tests** in the two required suites. Targeted checks
were also run during development; their overlapping counts are not added again.
Syntax parsing passed for all eight changed/new Python implementation/test files.
Hashes confirm that 64 protected source/API, authority, baseline, prompt and fixture
files match their pre-change state. Source/MCP permissions, Phase 06 implementation,
analysis prompts, scenario fixture generation and the golden seed are unchanged.

The final offline eval is
[`eval_bef20f02eae5421092fe20b343a94fe0`](../.cache/phase07/eval_bef20f02eae5421092fe20b343a94fe0/report.md).
The [saved live artifact regrade](../.cache/phase07/reliability-fix-20260911/regraded-live-report.md)
keeps `cr017_covered` failed with `resolution_question_not_pending` and
`cr017_scheduled` failed with `source_version_changed_during_case`. The original
live artifacts were not edited, and their failed investigations are not represented
as newly completed runs.

## Remaining uncertainty and ready live commands

The covered fixture still contains applicable evidence alongside the configuration's
`not_yet_demonstrated_for_WF-LC-V2` description. This requested preservation may still
create reasoning tension; no causal claim is made without a new live run. The
scheduled fixture's deterministic intake is verified, while subsequent live model
reasoning is unverified. Conservative prose checks are not a general semantic proof.

Paid live/semantic runs, UI checks, and unrelated full backend/MCP/investigator
suites were not rerun. The required targeted offline suites and Phase 06 HTTP smoke
passed. No business authority was expanded and no new workflow was implemented.

These commands are ready; they have **not** been run after the fix:

```sh
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_covered --allow-paid

PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_scheduled --allow-paid

PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case smoke --allow-paid
```
