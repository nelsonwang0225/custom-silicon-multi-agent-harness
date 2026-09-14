Continue working in the existing take-home repository.

We are doing one final targeted Phase 07 reliability patch before Phase 08.

The latest six-case live smoke produced:
- 6 total
- 4 passed
- 2 failed
- zero critical failures

The two failures were:
- cr017_covered
- cr017_scheduled

Both runtimes completed safely. These are reliability/orchestration issues,
not governance or authority failures.

Do not redesign the project.
Do not expand permissions.
Do not change Phase 06 governance.
Do not build Phase 08 yet.
Do not change source-system APIs.
Do not implement new workflows.
Do not weaken graders simply to make cases pass.

Git workflow remains relaxed:
- no branch/commit/push work
- preserve unrelated local work
- avoid destructive Git operations

==================================================
1. OBJECTIVE
==================================================

Fix the two demonstrated live reliability issues with the smallest safe
changes:

A. cr017_covered
   A narrow criteria-only clarification is currently forced through the full
   ValidationEvidenceAssessment contract, causing invalid placeholder fields
   such as coverage_source_id="unused" and a resulting escalation.

B. cr017_scheduled
   The coordinator correctly understands the request as an existing-case
   status inspection, but triage classifies it as other_or_unknown, which
   triggers the host stop gate and suppresses the requested Validation and
   Program specialists.

The fixes must preserve:
- existing safety behavior
- existing approval boundaries
- strict source/reference validation
- unknown/out-of-scope stop behavior
- truthful final-state claims
- source immutability during read-only investigations

==================================================
2. FIX cr017_covered WITH A NARROW CLARIFICATION CONTRACT
==================================================

The latest live run showed:

- initial Validation specialist correctly established sufficient applicable
  evidence
- the coordinator asked a criteria-only follow-up
- that follow-up was explicitly nonblocking
- the follow-up successfully retrieved CRIT-BASE-V1
- but the runtime required the specialist to emit a full
  ValidationEvidenceAssessment
- the specialist therefore emitted placeholder coverage fields:
    coverage_status = "unknown"
    coverage_source_id = "unused"
- strict source validation correctly rejected "unused"
- the branch failed and the host escalated

Do NOT:
- accept "unused" or placeholder source IDs
- weaken source-reference validation
- repeat the full coverage investigation unnecessarily
- discard prior validated coverage
- change the sufficient-coverage fixture again
- force non-escalation when a real blocking failure occurs

Instead implement a distinct typed result for narrow Validation
clarifications.

Conceptually:

ValidationClarificationResult
- clarification_type
- question / issue being clarified
- source_facts / source references actually used
- concise finding
- whether the finding changes the prior validated coverage assessment
- whether it introduces a new blocker
- unresolved items if any

Use repository naming/conventions rather than this exact schema if better.

Requirements:

1. Criteria-only or similarly narrow follow-ups may return this clarification
   result rather than a full coverage assessment.

2. The clarification must use real source references and must remain subject
   to strict source-fact validation.

3. The previously validated full coverage assessment remains authoritative
   unless the clarification produces evidence that materially invalidates it.

4. A clarification must not be able to silently overwrite:
   - applicable evidence
   - coverage status
   - mismatch reasons
   - source provenance

5. If the clarification reveals a real material conflict, the case may still
   escalate.

6. If the clarification is nonblocking and consistent with the prior
   assessment, the coordinator should proceed without fabricating a failed
   coverage branch.

7. Persist the clarification and its provenance in case state / activity
   using existing architecture.

8. Do not introduce hidden chain-of-thought persistence.

==================================================
3. PRESERVE STRICT FULL-ASSESSMENT VALIDATION
==================================================

The existing ValidationEvidenceAssessment contract remains strict for actual
coverage investigations.

Full assessments must still require:
- valid coverage source
- applicable/inapplicable evidence
- correct source references
- supported conclusions
- existing provenance/version rules

Do not make fields optional globally just to support clarification calls.

The new narrow result exists specifically so a criteria-only follow-up does
not pretend to be a second full assessment.

==================================================
4. FIX cr017_scheduled WITH AN EXISTING-CASE STATUS ROUTE
==================================================

The latest live run showed triage produced:

classified_change_type = "other_or_unknown"

while its rationale correctly said:

"The incoming request is a read-only execution-status inspection of an
existing validation job and linked program plan, not a new workload or
requirement change."

It then requested appropriate Validation and Program specialists with known
job/plan/link IDs.

However, other_or_unknown triggers the current host stop gate, so those
specialists never ran.

This is a taxonomy/routing mismatch.

Implement a narrow structured route for:

EXISTING CASE / EXECUTION STATUS INSPECTION

Use existing repository terminology if an equivalent concept already exists.

This route should support read-only questions such as:
- What is the current status of this already-known CR-017 validation job?
- Has the approved validation work been scheduled?
- What does Program Planner currently show?
- Are results available yet?
- Is customer acceptance still pending?

==================================================
5. ROUTING RULES FOR STATUS INSPECTION
==================================================

The new route must be bounded.

It may proceed only when the host can establish enough trusted scope such as:
- existing program/case identity
- known workflow/case relationship
- known validation job / plan / implementation-link identifiers where needed
- read-only intent
- supported source-system scope

When valid:
- allow the appropriate existing specialists to run
- normally Validation and Program/Commercial
- Manufacturing only if the requested status actually requires its evidence
- Change Impact is not mandatory for a pure execution-status inspection

Do not grant new tools.

Do not create a second workflow implementation.

This remains part of the existing requirement-change case lifecycle, not a
new executable workflow.

==================================================
6. PRESERVE THE UNKNOWN / OUT-OF-SCOPE STOP GATE
==================================================

Do NOT simply allow other_or_unknown to proceed.

The current safety stop must remain for genuinely:
- unknown requests
- unsupported workflows
- missing case/program scope
- low-confidence routing
- unrelated requests
- ambiguous requests where necessary identifiers cannot be established
- requests attempting unauthorized writes/actions

Status inspection should be an explicit supported route before the unknown
stop condition.

If classification is uncertain between a supported status inspection and an
unsupported request, fail safely or seek clarification according to existing
policy.

==================================================
7. STATUS INSPECTION MUST REMAIN READ-ONLY
==================================================

The new route does NOT authorize:
- scheduling a new validation job
- changing the existing job
- granting an approval
- modifying Program Planner
- customer communication
- validation pass
- customer acceptance
- any other source write

The existing Phase 06 execution path remains the only governed way to perform
authorized CR-017 writes.

The status inspection must only observe current state.

==================================================
8. REQUIRED BUSINESS SEMANTICS FOR cr017_scheduled
==================================================

For the existing scheduled fixture, the successful investigation should be
able to establish, based on actual source reads:

- scheduling_observed = true
- existing validation job is scheduled
- relevant reservation/linkage is present
- relevant Program Planner task/link is present
- validation_coverage = pending_test_results
- validation_passed = false
- customer_accepted = false
- customer_acceptance = pending
- no new approval is granted
- no new business action is executed
- no duplicate job is created

Do not infer validation success from scheduling.

==================================================
9. STRUCTURED TRIAGE / TAXONOMY
==================================================

Inspect the existing triage schema and classification values.

Prefer the smallest clean extension, such as:
- adding a supported existing_case_status / status_inspection classification
or
- adding a separate supported intent dimension while preserving the underlying
  requirement-change workflow family

Do not overload the business meaning of existing categories if that makes the
taxonomy misleading.

The classification should make clear:

workflow family:
requirement_change_analysis / existing CR-017 case

current intent:
read-only status verification

This distinction will later help Phase 08 chat and case-detail views.

==================================================
10. REGRESSION TESTS — COVERED CLARIFICATION
==================================================

Add deterministic regressions reproducing the saved cr017_covered failure.

At minimum test:

A. Full initial coverage assessment establishes sufficient applicable evidence.

B. Coordinator requests a criteria-only clarification.

C. Clarification returns a narrow typed result using a real source receipt.

D. Prior sufficient coverage is preserved when clarification is nonblocking.

E. No placeholder/unknown source ID is accepted.

F. "unused" remains rejected if provided where a valid source reference is
   required.

G. A clarification with unsupported facts is rejected.

H. A clarification that discovers a genuine material conflict can still create
   a blocker/escalation.

I. A failed required full coverage assessment still escalates.

J. Narrow clarification does not silently mutate the earlier evidence set.

K. cr017_covered expected final behavior:
   - sufficient evidence
   - no unnecessary duplicate testing
   - no evidence-gap escalation
   - engineering review remains distinct
   - customer acceptance remains false/pending
   - no business execution

==================================================
11. REGRESSION TESTS — SCHEDULED STATUS ROUTING
==================================================

Add deterministic regressions reproducing the saved cr017_scheduled failure.

At minimum test:

A. Known existing-case read-only status request routes to supported status
   inspection rather than other_or_unknown.

B. Validation specialist runs and reads the relevant known job.

C. Program specialist runs and reads the relevant Planner records.

D. Correct singular or plural relevant-job read continues to satisfy the
   Phase 07 semantic tool expectation.

E. Current scheduled fixture produces:
   scheduling_observed = true
   validation_coverage = pending_test_results
   validation_passed = false
   customer_accepted = false

F. No source write occurs.

G. No duplicate scheduling occurs.

H. Truly unknown/unrelated request remains blocked.

I. Missing trusted case/program scope remains blocked.

J. Low-confidence unsupported routing remains blocked according to current
   policy.

K. Write request disguised as status inspection does not gain authority.

L. Wrong job ID / cross-program scope remains rejected.

M. Historical snapshots remain distinct from current source records.

==================================================
12. LIVE-FAILURE ARTIFACT REGRESSION
==================================================

Where practical, create deterministic reproductions based on the two saved
live failures without depending on paid calls.

Preserve the original live artifacts.

Do not rewrite old reports.

Use them as regression evidence if the eval framework already supports safe
replay/regrade.

==================================================
13. DO NOT CHANGE GRADERS UNLESS NECESSARY
==================================================

The latest diagnosis established the current graders correctly caught these
failures.

Do not weaken:
- escalation expectation
- scheduling_observed requirement
- pending_test_results expectation
- relevant_validation_job_read requirement
- hard governance gates

Only change an eval if implementation reveals a genuine specification error,
and report it before doing so.

==================================================
14. OFFLINE VERIFICATION
==================================================

Run at minimum:

coordinator/.venv/bin/python -m pytest \
  -c coordinator/pyproject.toml \
  coordinator/tests -q

.venv/bin/python -m pytest \
  tests/test_phase07_sources.py \
  tests/test_phase06_execution.py -q

PYTHONPATH=src \
  coordinator/.venv/bin/python -m coordinator.evals.phase07

Also run any focused new tests for:
- clarification contracts
- status-routing classification
- saved-failure reproductions

Expected before live rerun:
- all existing regressions green
- all new regressions green
- 40/40 offline evals PASS
- hard gates PASS
- zero critical failures
- Phase 06 smoke remains green
- permissions unchanged
- source APIs unchanged

==================================================
15. VERIFY PRESERVATION
==================================================

Explicitly verify that these remain unchanged unless minimally required for
the targeted fixes:

- Phase 06 approval/execution authority
- source-system write permissions
- MCP tool scopes
- five mock-app APIs
- yield_exception_recovery remains illustrative/non-executable
- delivery_readiness remains illustrative/non-executable
- CR-017 golden business facts
- prior covered-fixture consistency fix
- prior historical-snapshot/current-version fix
- prior relevant-validation-job-read grader fix

==================================================
16. DOCUMENTATION
==================================================

Update the Phase 07 reliability handoff with:

A. cr017_covered fix
- why narrow clarification required a separate contract
- how previous coverage is preserved
- how real conflicting clarification still escalates

B. cr017_scheduled fix
- new supported existing-case status-inspection route
- routing/scope requirements
- why unknown/out-of-scope requests remain blocked

C. Security/governance preservation
- no new write authority
- no approval changes
- no customer commitment changes

D. Verification results
- tests
- offline evals
- preserved hard gates

==================================================
17. FINAL REPORT
==================================================

When finished, report:

1. Baseline inspected
2. Exact cr017_covered implementation fix
3. Exact cr017_scheduled implementation fix
4. Structured contracts/taxonomy added or changed
5. Why neither fix broadens authority
6. Files changed
7. New regression tests
8. Offline verification results
9. Eval results
10. Preservation checks
11. Any remaining known reliability issues
12. Exact live commands ready to run

Do not automatically run paid live models.

==================================================
18. LIVE EXIT CHECK — DO NOT RUN AUTOMATICALLY
==================================================

After offline verification, these two targeted live cases are the only
required live checks:

PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_covered --allow-paid

PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_scheduled --allow-paid

We do NOT need another six-case live smoke if both targeted cases pass and:
- the other four cases remain previously demonstrated live passes
- all offline regressions are green
- zero critical failures are introduced

==================================================
19. STOPPING POINT
==================================================

Stop after implementation and offline verification.

Do not proceed into:
- Phase 08 control-plane UI
- contextual chat
- scheduler
- touchless change implementation
- yield workflow implementation
- delivery-readiness implementation
- Git cleanup / commit / push work

Phase 07 may be considered ready to exit after:
- cr017_covered passes the targeted live rerun
- cr017_scheduled passes the targeted live rerun
- offline evals remain 40/40
- hard governance gates remain green
- zero critical safety failures