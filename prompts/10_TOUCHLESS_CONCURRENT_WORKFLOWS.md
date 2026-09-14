Continue working in the existing Stratos Silicon repository and current Phase 10 thread.

Implement a focused AUTONOMOUS QE-011 + CONCURRENT WORKFLOW RUNS refinement.

This change has two objectives:

1. Make QE-011 a genuinely touchless autonomous background workflow that does
   not end at Program Owner approval.

2. Allow QE-011 to continue running while a user starts another connected
   workflow such as CR-017. The two workflows must remain isolated concurrent
   runs rather than one replacing, pausing, or blocking the other.

Reuse the existing:
- QE-011 Manufacturing source event
- yield_exception_recovery workflow
- shared invocation service
- Program Coordinator and existing specialists
- run/case/activity persistence
- RAG integration
- Phase 06 governance
- Agent Workspace
- Operations
- demo reset / autonomous-opening controls
- persona/capability model

Do not create:
- another workflow runtime
- another agent team
- another queue system solely for this demo
- new business authority
- a fake activity animation
- generic autonomous quality disposition
- an active production-grade scheduler/event bus

Do not change CR-017, CR-019, QE-004 or DR-009 business semantics.

No paid model calls during automated tests.
No Git packaging.

==================================================
1. QE-011 PRODUCT PURPOSE
==================================================

QE-011 exists specifically to demonstrate:

"A back-office enterprise event can trigger agents automatically, the agents can
complete routine investigation and coordination without a human initiating or
approving the work, and humans are involved only if a consequential authority
boundary is actually reached."

QE-011 should NOT duplicate QE-004's human-approval story.

QE-004 remains the quality workflow demonstrating consequential human review.

QE-011 demonstrates bounded autonomous work.

==================================================
2. CHANGE QE-011 TO A TOUCHLESS POLICY PATH
==================================================

Currently QE-011 ends at:

Program Owner decision required / Needs review.

Change the QE-011 fixture/policy so its successful canonical path requires no
new human approval.

Do NOT remove governance from yield_exception_recovery globally.

Create a deterministic QE-011-specific standard-policy route that is eligible
only because all downstream actions are pre-authorized, non-consequential
coordination actions.

Conceptually:

workflow:
yield_exception_recovery

policy route:
standard_quality_investigation_handoff

Use actual repository naming conventions.

The normal QE-004 route retains its human decision boundaries.

==================================================
3. WHAT QE-011 MAY AUTONOMOUSLY DO
==================================================

QE-011 may autonomously:

- receive the quality_exception_created source event;
- open/use the source-backed QE-011 case;
- validate the signal;
- check baseline comparability;
- retrieve Manufacturing source facts;
- retrieve approved Quality RAG knowledge where useful;
- gather related validation/engineering context;
- scope affected material;
- calculate bounded program/supply impact;
- distinguish facts, hypotheses and unresolved root cause;
- create/route an approved standard quality-investigation work item;
- create/update a standard non-consequential Planner investigation task if
  already within existing permitted planning authority;
- independently read back and verify those handoffs;
- finish the workflow.

QE-011 must NOT autonomously:

- release held material;
- change quality disposition;
- authorize non-standard rework/retest;
- change test thresholds;
- change manufacturing recipes;
- reallocate constrained inventory;
- change customer commitments;
- claim root cause without authoritative evidence;
- grant engineering/customer acceptance.

==================================================
4. QE-011 SUCCESSFUL END STATE
==================================================

The canonical QE-011 outcome should be equivalent to:

Quality exception investigated

Standard investigation routed

Handoff verified

Lot remains on hold

Root cause unresolved / under investigation where applicable

No customer commitment change

No human review required for the actions completed by this specific route

Use existing terminology where possible.

Do NOT display:
Needs review

unless the actual QE-011 source facts make the touchless route ineligible.

==================================================
5. TOUCHLESS ELIGIBILITY MUST BE DETERMINISTIC
==================================================

Do not let the model decide its own authority.

Create/reuse deterministic policy checks for QE-011.

At minimum verify:

- known standard quality-exception type;
- lot already placed on HOLD by authoritative source/rule;
- approved investigation procedure exists;
- requested actions are standard evidence-gathering / investigation-routing only;
- no release/disposition/reallocation/commitment action is proposed;
- source scope is established;
- downstream investigation owner/queue exists;
- no conflicting exception requires consequential review.

If any rule fails:
- stop touchless execution;
- surface review/escalation;
- zero unauthorized autonomous write.

This fallback behavior should remain possible even though the canonical demo case
is touchless.

==================================================
6. REMOVE THE PROGRAM OWNER DECISION FROM THE NORMAL QE-011 PATH
==================================================

For canonical QE-011:

Do not create a Program Owner proposal/decision merely because QE-004 normally
does.

The case should move:

event-triggered investigation
→ standard investigation handoff
→ verification
→ autonomous workflow complete

The Decisions page should not contain a fake QE-011 human decision.

Operations should clearly show:

Policy path:
Touchless / standard quality investigation

Human approval:
Not required for executed actions

==================================================
7. AUTONOMOUS OPENING PACING
==================================================

Preserve:

Prepare autonomous opening
→ delayed Manufacturing event
→ QE-011 workflow starts

Do not trigger agents from ordinary app startup.

Do not introduce fake sleep inside model/tool execution simply to keep the
workflow visibly active.

The event delay may remain the controlled demo pacing mechanism.

If the real workflow completes before the user sees it, Agent Workspace should
show its newly completed recorded outcome truthfully.

Do not fake running state.

==================================================
8. CONCURRENT WORKFLOW REQUIREMENT
==================================================

QE-011 must NOT block CR-017 or any other independent workflow from starting.

Expected:

Run A:
QE-011
event-triggered
yield_exception_recovery

and simultaneously:

Run B:
CR-017
user-triggered
requirement_change_analysis

Both may be RUNNING concurrently.

One run must not:
- overwrite another run's state;
- reuse another run's proposal;
- merge evidence;
- merge specialist activity;
- block initiation simply because another workflow is active.

Each run retains its own:

- run_id
- case_id
- workflow_id
- invocation source
- source/evidence scope
- agent invocations
- activities
- proposals/decisions
- action state
- trace/provenance

==================================================
9. DO NOT MODEL AGENTS AS SINGLE EXCLUSIVE HUMAN WORKERS
==================================================

The existing specialist definitions are reusable model configurations.

For example, Validation & Evidence may participate concurrently in:

QE-011 Run A

and

CR-017 Run B

as separate invocations.

Do not impose:
"Validation agent is busy, wait for it to finish"

unless there is an actual configured shared resource constraint.

Concurrency belongs to workflow/run execution, not an exclusive ownership model
of an agent persona.

==================================================
10. USE EXISTING PARALLEL EXECUTION WHERE POSSIBLE
==================================================

Inspect the current invocation/runtime implementation before changing it.

If independent workflow invocations already support concurrent execution, preserve
that architecture and fix only any UI/application-level serialization.

If the current host accidentally serializes all runs globally, introduce the
smallest bounded concurrency support necessary for multiple independent runs.

Prefer:
- async tasks / existing worker execution model
- isolated persisted run state
- bounded concurrency

Do NOT introduce Kubernetes, Kafka, Temporal, Celery or a new distributed queue
just for the take-home.

Document the current demo concurrency limitation honestly.

==================================================
11. CONCURRENCY LIMIT
==================================================

Do not make concurrency unbounded.

For the local demo, choose a small safe configurable limit if one does not
already exist.

Example:
max_concurrent_workflow_runs = 3 or 4

Use actual implementation judgment.

If the limit is reached:
- additional workflows queue or return a clear bounded-capacity state;
- do not silently fail;
- do not lose the invocation.

Do not invent a production-grade scheduler.

==================================================
12. SHARED BUSINESS-STATE SAFETY
==================================================

Parallel reasoning is allowed.

Consequential writes must still protect shared state using existing:

- source-version checks;
- proposal freshness;
- idempotency;
- action manifests;
- readback verification.

Do not globally lock the whole application simply because two runs coexist.

If independent runs touch unrelated records:
allow concurrency.

If a future run attempts a conflicting consequential update:
existing stale/version policy should reject/reassess appropriately.

QE-011 should use isolated material so it does not mutate the QE-004 / DR-009
golden-path records.

==================================================
13. AGENT WORKSPACE — MULTIPLE ACTIVE RUNS
==================================================

Upgrade Agent Workspace to represent concurrent runs clearly.

The workspace must NEVER merge specialists from different workflow runs into one
graph.

DEFAULT SELECTION PRIORITY

When the user has not explicitly selected a run:

1. most recently started active permitted run;
2. another active permitted run;
3. human-handoff/current-outcome run;
4. most recent recorded run;
5. idle state.

If the user manually selects a run:
keep it selected while it remains accessible, even if another run starts.

When live work exists and the user is viewing a historical run:
show an obvious control:

Back to live activity

==================================================
14. ACTIVE-RUN SELECTOR
==================================================

When multiple workflow runs are active:

Show a compact visual indicator such as:

2 active investigations

and a run selector.

Example entries:

QE-011
Source event · Running

CR-017
User initiated · Running

Use actual data.

Do not display full implementation IDs as the primary label.

Selecting QE-011 displays only QE-011 agents/tasks.

Selecting CR-017 displays only CR-017 agents/tasks.

==================================================
15. AGENT WORKSPACE QE-011
==================================================

While QE-011 is running, the workspace should make the autonomous story obvious.

Display:

QE-011 · Final-test anomaly

Invocation:
Source event

Actual participating agents and their real current/last observed task states.

Do not hard-code all four specialists if fewer actually ran.

When the workflow completes autonomously:

transition to:

QE-011 · Handoff verified

Recorded result

or equivalent.

Do not show Needs review.

==================================================
16. CR-017 WHILE QE-011 RUNS
==================================================

Explicitly verify this user flow:

1. Prepare autonomous opening.
2. QE-011 event fires.
3. QE-011 workflow is running.
4. User navigates to CR-017.
5. User starts CR-017 investigation.
6. CR-017 begins immediately subject only to bounded concurrency capacity.
7. QE-011 continues.
8. Agent Workspace shows 2 active investigations.
9. User can switch between run visualizations.
10. Each run reaches its own independent outcome.

CR-017 must NOT wait for QE-011 merely because the same specialist definitions
are used.

==================================================
17. OVERVIEW / NEEDS ATTENTION
==================================================

While QE-011 is autonomously running:

Agent Workspace:
show live work.

Needs Attention:
do NOT show QE-011 unless human action is actually required.

After QE-011 touchless completion:
generally move it to recent autonomous activity/history, not Needs Attention.

If the touchless policy fails:
then Needs Attention may show the legitimate review/escalation.

==================================================
18. RECENT AUTONOMOUS WORK
==================================================

Where the current Agent Workspace design supports it, show a compact recent outcome:

QE-011
Quality investigation handoff verified

Source event

timestamp

Keep it concise.

Do not add a second large run-history table to Overview.

==================================================
19. OPERATIONS
==================================================

Operations must represent concurrent runs independently.

Verify it shows:

QE-011
Invocation source = source event

CR-017
Invocation source = manual / UI

with separate:
- traces
- specialists
- tool calls
- RAG retrieval
- decisions
- actions
- outcomes

No cross-run mixing.

==================================================
20. CONCIERGE
==================================================

Concierge should be able to answer:

"What are the agents working on?"

If two runs are active:
return both with correct cases/states.

"What's happening with QE-011?"

→ source-grounded QE-011 state.

"Start CR-017 investigation."

→ shared invocation service starts CR-017 even while QE-011 runs, subject to
configured bounded concurrency.

Concierge must not cancel/replace QE-011 to make room.

==================================================
21. DEMO RESET / REPLAY
==================================================

Extend/reset behavior to handle concurrent workflow state safely.

Full Demo Reset:
- disarm autonomous event;
- prevent delayed event after reset;
- reconcile/clear current QE-011 demo runs;
- reconcile current other demo runs according to existing reset policy;
- restore baseline;
- clear invalid run selection.

Autonomous reset:
- reset QE-011 event/run state;
- must not delete unrelated CR-017 history/state improperly.

Test reset while:
- event armed
- QE-011 running
- QE-011 + CR-017 both running
- QE-011 completed

Use deterministic test doubles.

==================================================
22. DEMO CONTROLS
==================================================

Update autonomous-demo status if necessary:

Idle
Armed
Event emitted
Workflow running
Touchless handoff verified
Failed / escalated

Remove:
Human handoff ready

from the canonical QE-011 touchless success path.

Keep it for policy-failure variant if relevant.

==================================================
23. AUTOMATION / EVENT UI
==================================================

Workflows & Automations should truthfully state:

Yield / Quality Exception Recovery

Manual initiation:
Connected

QE-011 quality_exception_created source event:
Connected demo trigger

Other saved source-event configurations:
Not active / configuration only

Do not imply a general production event fabric exists.

==================================================
24. EVALS
==================================================

Add deterministic evals for QE-011 touchless behavior:

A. Canonical QE-011 eligible for standard autonomous investigation.

B. Approved Quality SOP retrieval supports investigation.

C. Lot remains HOLD.

D. Root cause not fabricated.

E. Standard investigation handoff permitted.

F. No Program Owner decision created.

G. No quality release.

H. No customer commitment change.

I. Handoff verified.

J. Ineligible variant escalates with zero autonomous consequential action.

Also add concurrency-focused deterministic tests where appropriate:
- independent run context preserved;
- no source/evidence cross-contamination;
- one run completion doesn't mark another complete.

==================================================
25. CONCURRENCY TESTS
==================================================

Add focused tests:

A. QE-011 can be running when CR-017 starts.

B. Both have different run IDs.

C. Shared specialist definition can have invocations in both runs.

D. Run state remains isolated.

E. Activities remain isolated.

F. Tool receipts remain scoped.

G. Agent Workspace selector lists both.

H. Switching selected run changes topology/tasks correctly.

I. No merged agent graph.

J. Completing QE-011 does not complete/pause CR-017.

K. CR-017 human approval remains independent.

L. Duplicate QE event still starts one run only.

M. Concurrency limit is enforced safely.

N. Reset handles concurrent state.

==================================================
26. NO PAID CALLS IN AUTOMATED TESTS
==================================================

Use controlled workflow/model doubles.

Do not run simultaneous paid-model tests automatically.

Provide optional live steps afterward.

==================================================
27. OPTIONAL LIVE CONCURRENCY CHECK
==================================================

Provide exact manual steps, but do not run automatically:

1. Full Demo Reset.
2. Prepare autonomous opening.
3. Open Overview.
4. Wait for QE-011 event-triggered workflow to begin.
5. Confirm Agent Workspace shows QE-011 running.
6. Navigate to CR-017.
7. Start live CR-017 investigation.
8. Return to Overview.
9. Confirm 2 active investigations.
10. Switch between QE-011 and CR-017.
11. Observe independent progress.
12. Confirm QE-011 finishes touchlessly.
13. Confirm CR-017 continues to its normal human decision.

Document expected API usage.

==================================================
28. PRODUCTION-NARRATIVE DOCUMENTATION
==================================================

Document clearly:

The demo supports bounded local concurrent workflow runs.

Production evolution would place the invocation layer behind a durable
queue/worker architecture with horizontal scaling, rate limiting, backpressure
and resource-specific concurrency controls.

Do not claim production-grade distributed scheduling is implemented.

==================================================
29. REGRESSION
==================================================

Run relevant:

- source tests
- coordinator tests
- MCP
- RAG tests
- offline evals
- QE-004 regressions
- CR-017 regressions
- autonomous-event tests
- Agent Workspace tests
- Concierge tests
- Operations
- demo reset
- browser E2E
- typecheck/build

No paid model calls.

==================================================
30. FINAL REPORT
==================================================

Report:

1. Why QE-011 no longer requires human review
2. Deterministic touchless policy
3. Exact autonomous write/handoff boundary
4. QE-011 end state
5. Concurrency implementation
6. Concurrency limit
7. Workflow-state isolation
8. Agent Workspace multi-run behavior
9. Overview / Needs Attention behavior
10. Operations / Concierge behavior
11. Reset/replay
12. Tests/evals
13. Optional live concurrency steps
14. Current local-demo limitations
15. Production scaling path

==================================================
31. STOPPING POINT
==================================================

Stop after this focused refinement.

Do not implement:
- production distributed queue infrastructure
- active generic scheduler
- more event-driven workflows
- Git packaging

Success criteria:

QE-011 source event
→ autonomous yield workflow
→ real agents investigate
→ standard non-consequential handoff
→ verification
→ no human decision required

WHILE independently:

CR-017 can start and run concurrently
→ separate run context
→ separate agent invocations
→ no waiting for QE-011
→ existing CR-017 human governance preserved.
