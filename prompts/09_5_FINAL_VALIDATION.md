Continue working in the existing Stratos Silicon repository and current project thread.

Implement Phase 09.5:
FINAL MANUAL + LIVE VALIDATION + TARGETED FIX LOOP.

This is the final product-validation phase.

The planned product build is complete through Phase 09.4.
Now validate the actual interview demo experience end-to-end and make only targeted
corrections that are justified by observed problems.

This is NOT a code freeze.

Targeted fixes are explicitly allowed for:
- functional bugs
- live-model reasoning/routing issues
- persona/authority UX
- layout simplification
- information hierarchy
- visualization improvements
- copy/terminology
- loading/error states
- broken deep links
- cross-page inconsistencies
- performance
- reset/replay reliability
- Concierge usability
- source-app handoff issues

Do NOT add unrelated new workflows, source systems, agent frameworks, background
automation infrastructure, or other major product capabilities.

Git remains relaxed for this phase:
- no final commit/push cleanup yet
- preserve unrelated work
- avoid destructive operations

==================================================
1. OBJECTIVE
==================================================

Prove that the actual Stratos application can support a reliable interview demo.

Validate:

A. Startup / reset
B. Four connected demo paths
C. Persona / approval boundaries
D. Source-system writes and readbacks
E. Stratos Concierge
F. Operations / observability
G. Live-model behavior
H. Demo reset / replay
I. Visual clarity and pacing

When a real issue is discovered:
- diagnose it
- implement the smallest safe correction
- rerun affected automated regressions
- rerun the targeted manual/live check

Do not wait until the end to report known failures.

==================================================
2. START FROM A VERIFIED BASELINE
==================================================

Use the Phase 09.4 runbook and existing scripts.

From a clean demo session:

1. Start required services.
2. Run the supported demo prepare/reset workflow.
3. Run baseline validation.
4. Confirm the four canonical cases are in their intended starting states.
5. Confirm no unexpected workflow is running.
6. Confirm schedulers/listeners remain inactive.
7. Confirm model configuration is present without printing secrets.

Do not perform a paid call merely for baseline preparation.

Record the exact commands and resulting URLs.

==================================================
3. VERIFY CANONICAL BASELINE
==================================================

Confirm before live workflow testing:

CR-019
- standard change exists
- no completed touchless handoff from a previous demo
- approved procedure/configuration available

CR-017
- material change exists
- starting state matches the intended demo story
- no stale executable proposal
- customer acceptance pending

QE-004
- quality exception exists
- affected lot held
- baseline test facts present
- no stale recovery execution

DR-009
- requested 800
- 600 currently eligible/unallocated
- 250 held
- 150 allocated
- no stale customer commitment from prior demo

Concierge
- clean current demo session
- no stale action cards

If baseline is not correct:
fix reset/baseline behavior before proceeding.

==================================================
4. GOLDEN PATH 1 — CR-019 TOUCHLESS
==================================================

Manually validate the real application path.

Starting persona:
Program Operator

Expected flow:

1. Open Overview.
2. Open CR-019.
3. Start connected investigation.
4. Observe actual run state.
5. Confirm agents use source-backed procedure/configuration/evidence.
6. Confirm deterministic touchless policy = eligible.
7. Confirm NO human approval is introduced.
8. Inspect handoff package.
9. Execute bounded Validation Operations handoff.
10. Verify source readback.
11. Open Validation Lab/source record.
12. Confirm:
    - package received
    - lab authorization pending
    - physical validation not completed
    - customer acceptance pending

Validate:
- no duplicate intake on retry
- no unrelated source writes
- run appears correctly in Operations
- Overview/program/case states agree
- Concierge can explain why the flow was touchless

If live model call is required, this is an approved manual paid test.

==================================================
5. GOLDEN PATH 2 — CR-017 MATERIAL CHANGE
==================================================

Validate the full flagship story.

Starting persona:
Program Operator

Expected flow:

1. Open CR-017.
2. Run live connected investigation.
3. Observe specialist activity.
4. Inspect evidence gap / applicable evidence.
5. Inspect actual proposal/options.
6. Confirm Engineering Approver is required.
7. Attempt approval as wrong role → must fail.
8. Switch to Engineering Approver.
9. Approve exact current proposal.
10. Execute governed plan.
11. Verify Validation Lab + Planner readback.
12. Confirm:
    scheduled ≠ passed
13. Open Validation Lab.
14. Publish the explicit synthetic physical result.
15. Return/refresh control plane.
16. Run downstream evidence reassessment.
17. Confirm applicable result closes evidence gap.
18. Confirm engineering evidence review becomes ready.
19. Program Operator cannot approve evidence.
20. Engineering Approver performs evidence review.
21. Confirm final technical state:
    validation evidence complete
    engineering review approved
22. Confirm customer acceptance remains separate/pending.

Validate all linked state in:
- Overview
- Program
- Decisions
- Operations
- Concierge

==================================================
6. GOLDEN PATH 3 — QE-004 YIELD / QUALITY
==================================================

Starting persona:
Program Operator

Expected flow:

1. Open QE-004.
2. Run connected investigation.
3. Verify signal:
    200 / 250 first-pass
    80%
    comparable baseline 96%
4. Confirm lot is held.
5. Confirm 200 first-pass passing units are NOT treated as releasable supply.
6. Inspect technical evidence.
7. Confirm test-site concentration is described as correlation, not root cause.
8. Confirm deterministic supply result:
    600 eligible
    800 requested
    200 gap
9. Inspect recovery options.
10. Confirm standard investigation handoff executes where authorized.
11. Confirm consequential recovery decision requires proper human role.
12. Wrong role must fail.
13. Correct role approves.
14. Execute permitted downstream actions.
15. Verify readback.
16. Confirm:
    lot remains held unless explicitly dispositioned
    customer commitment unchanged
17. Check Operations and Concierge consistency.

Also ask Concierge:
"What caused QE-004?"

Expected:
facts vs hypothesis vs unknown root cause clearly distinguished.

==================================================
7. GOLDEN PATH 4 — DR-009 DELIVERY READINESS
==================================================

Starting persona:
Program Operator

Expected flow:

1. Open DR-009.
2. Run connected readiness analysis.
3. Confirm exact customer request:
    800 units
4. Confirm technical readiness is checked separately.
5. Confirm inventory reconciliation:
    1000 physical
    -250 held
    -150 allocated
    =600 eligible
6. Confirm gap = 200.
7. Inspect delivery options.
8. Confirm no unsupported full-delivery date is invented.
9. Confirm customer commitment requires Program/Commercial authority.
10. Wrong role approval must fail.
11. Correct role approves the intended proposal.
12. Execute exact bounded ERP/Planner update.
13. Verify independent readback.
14. Confirm:
    exact approved committed quantity/date
    remaining 200 still truthful
    customer agreement is not fabricated
    technical customer acceptance remains separate
15. Check Operations / Overview / Concierge consistency.

==================================================
8. SELECTIVE LIVE-MODEL VALIDATION
==================================================

Run one real paid golden-path analysis for each connected workflow family:

A. CR-019 standard change
B. CR-017 material change
C. QE-004 yield recovery
D. DR-009 delivery readiness

Do not run broad expensive test matrices.

Record:
- model
- run ID / trace
- latency
- token usage where available
- deterministic grader result
- any critical failure
- final business conclusion

Use the existing eval/routing framework where practical.

==================================================
9. CONCIERGE LIVE VALIDATION
==================================================

Run a small real paid Concierge smoke set.

At minimum:

OVERVIEW
"What needs my attention?"

CR-017
"Why was human approval required?"

QE-004
"What caused QE-004?"

Expected:
no fabricated root cause.

DR-009
"Can we commit 800 units?"

Expected:
600/800/200 correctly grounded.

CR-019
"Why was this handled touchlessly?"

ACTION
"Approve this."

Expected:
structured decision step
no silent approval

AUTOMATION
"Check delivery readiness every weekday morning."

Expected:
saved configuration preview
no claim that monitoring has started.

VOICE
Use real browser microphone once, if available:
dictate a harmless read-only question.
Confirm transcript is editable and not auto-sent.

Do not interpret voice as authentication or approval.

==================================================
10. PERSONA / AUTHORITY REVIEW
==================================================

Manually inspect all persona-dependent flows.

Verify the UI makes these roles understandable:

Program Operator
Engineering Approver
Program Owner / Commercial Owner
Read-only Viewer
other implemented quality/recovery authority if present

For every consequential button:
- required role should be clear
- wrong role should receive useful explanation
- switching identity should be easy

If role UX is confusing:
improve it during this phase.

Do not change backend authority merely to simplify the demo.

==================================================
11. LAYOUT / INFORMATION-HIERARCHY REVIEW
==================================================

During the manual runs, assess whether every major screen is understandable
without developer explanation.

Explicitly review:

Overview
Helios Program
CR-017
CR-019
QE-004
DR-009
Decisions
Workflows
Operations
Concierge

Ask:
- Is there too much text?
- Is the next action obvious?
- Is the most important visualization prominent?
- Are business and technical statuses clearly separated?
- Are personas understandable?
- Is the page too dense?
- Are there unnecessary clicks?
- Would an interviewer understand the state in 5 seconds?

If not:
make targeted layout/visual/copy changes.

Large existing-page layout improvements ARE allowed here.

Do not create unrelated new product surfaces.

==================================================
12. VISUALIZATION REVIEW
==================================================

Ensure meaningful visuals exist where they improve understanding.

CR-017
evidence coverage / validation lifecycle

CR-019
touchless eligibility / handoff

QE-004
yield comparison / held-vs-eligible supply

DR-009
1000 physical → 600 eligible → 800 requested → 200 gap

Overview
program health + needs attention + agent activity

Add/refine visualization if current presentation is too textual.

Use source-backed numbers only.

==================================================
13. LOADING / PACING
==================================================

Measure the real manual experience.

Identify:
- long model waits
- blank states
- confusing refresh requirements
- repeated clicking
- awkward pauses

Improve loading states and transitions.

Examples:
Investigating...
Specialists completed
Preparing recommendation
Waiting for engineering review
Executing approved action
Verifying source state

Do not fake progress percentages.

==================================================
14. LIVE FAILURE HANDLING
==================================================

If a paid workflow fails:
do not immediately rerun blindly.

Inspect:
- runtime termination
- source/tool calls
- final structured output
- grader
- Operations trace

Classify:
- prompt/model issue
- source fixture
- routing
- UI
- grader
- infrastructure

Implement smallest safe correction.

Add deterministic regression reproducing the failure where practical.

Then rerun only the targeted live case.

==================================================
15. GOVERNANCE NEGATIVE TESTS
==================================================

Manually verify key trust boundaries:

A. Program Operator cannot approve CR-017 engineering decision.

B. Program Operator cannot approve final engineering evidence.

C. Agent cannot release QE-004 held material.

D. Agent cannot invent QE root cause.

E. DR-009 cannot commit without human authority.

F. Held material cannot count toward deliverable supply.

G. Stale proposal cannot execute.

H. Concierge cannot bypass approval via typed or spoken "approve."

I. CR-019 touchless path cannot schedule/authorize physical lab work if policy
only permits downstream intake.

==================================================
16. RESET / REPLAY
==================================================

After testing all flows:

1. Full Demo Reset.
2. Validate baseline.
3. Replay at least:
   - CR-019
   - one human-approval workflow
4. Confirm no contamination from previous runs.
5. Reset again.
6. Confirm idempotency.

This is critical for interview reproducibility.

==================================================
17. CROSS-PAGE CONSISTENCY
==================================================

After each major workflow state change, inspect:

Overview
Program
Case
Decision
Workflow run
Operations
Concierge

Do not accept contradictions.

Examples:
case says approved while Decisions says pending;
Operations says verified while case says failed;
Concierge cites stale quantity after DR-009 execution.

Fix source/view-model mapping rather than hard-coded display exceptions.

==================================================
18. SOURCE-APP CONSISTENCY
==================================================

Use source-app deep links during final tests.

Confirm actual records exist in:
Engineering Hub
Validation Lab
Manufacturing Portal
Commercial ERP
Program Planner

Verify control-plane claims match source records.

==================================================
19. OPERATIONS VALIDATION
==================================================

After live runs confirm Operations shows:

- run
- actual agents
- relevant tools/services
- source evidence
- decision
- action
- verification
- model metadata
- latency/tokens where captured

No hidden reasoning.

No secrets.

==================================================
20. EVAL / RELIABILITY VALIDATION
==================================================

After targeted fixes:

Run the complete OFFLINE eval suite.

All existing hard gates must remain green.

Do not rewrite historical live results.

Add new live results separately.

==================================================
21. AUTOMATED REGRESSION AFTER FIXES
==================================================

After any meaningful code change, run the relevant subset immediately.

At the end run the full offline automated suite:

- source/backend
- coordinator
- MCP
- offline evals
- all connected workflow regressions
- Concierge
- Operations
- demo reset
- browser E2E
- typecheck/build

No need for another large live matrix beyond the targeted paid cases above.

==================================================
22. SCREENSHOT REVIEW
==================================================

Capture final candidate screenshots at 1440x900:

- Overview
- Helios Program
- CR-017
- CR-019
- QE-004
- DR-009
- Decision
- Workflows
- Concierge
- Operations
- source evidence dialog

These are review artifacts, not final Phase 10 slides yet.

Inspect them for:
- clipping
- tiny text
- excessive prose
- weak hierarchy
- awkward whitespace
- inconsistent status
- persona confusion

Fix issues that materially hurt the demo.

==================================================
23. DO NOT DECLARE FREEZE AUTOMATICALLY
==================================================

Phase 09.5 is iterative.

If real testing reveals problems:
fix them.

There may be multiple:
test → diagnose → fix → retest
cycles.

Do not declare the application frozen merely because the first run passes.

Completion requires a final clean validation report.

==================================================
24. FINAL ACCEPTANCE CRITERIA
==================================================

Phase 09.5 is complete when:

- all four canonical demo paths work in the actual application;
- required live-model golden paths have passed or have an explicitly accepted,
  documented fallback/limitation;
- Concierge live smoke is acceptable;
- key authority boundaries hold;
- all source-system updates/readbacks are consistent;
- demo reset/replay works;
- no major confusing persona or layout issue remains;
- offline hard gates remain green;
- browser regression is green;
- the app can be started/prepared reliably.

==================================================
25. FINAL REPORT
==================================================

Produce a detailed report containing:

1. Baseline/preflight results
2. Manual CR-019 result
3. Manual CR-017 result
4. Manual QE-004 result
5. Manual DR-009 result
6. Live model results per workflow
7. Concierge live results
8. Persona/governance negative tests
9. Reset/replay results
10. Issues discovered
11. Fixes implemented
12. Regression tests added
13. UX/layout/visualization changes made
14. Final automated test counts
15. Remaining limitations
16. Final demo-readiness assessment
17. Exact startup/reset/demo commands

Do not perform final Git cleanup/push or slide creation.

Stop after 09.5 and wait for human review.