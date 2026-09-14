Continue working in the existing Stratos Silicon repository and current Phase 10 thread.

Implement a focused AUTONOMOUS BACK-OFFICE DEMO enhancement.

Objective:

Demonstrate that Stratos agents can begin work from an enterprise source event
without a human clicking "Run investigation."

The demo should support:

Manufacturing source event
→ bounded event trigger
→ existing shared workflow invocation service
→ connected yield/quality workflow
→ agents investigate in the background
→ Overview / Agent Workspace shows real current activity
→ workflow stops at existing human authority boundary

This is NOT a new workflow.

Reuse the existing:
- yield_exception_recovery workflow
- Program Coordinator
- specialist agents
- shared invocation service
- case/run/activity persistence
- event/trigger configuration concepts
- Phase 06 governance
- Phase 07 evals
- Agent Workspace
- Demo reset / Demo controls
- Operations
- existing Manufacturing Portal

Do not:
- change agent authority
- change QE-004
- change DR-009
- change CR-017 / CR-019
- create a second workflow runtime
- activate all saved automations
- start agents automatically on normal app launch
- create infinite background polling
- run paid models during automated tests
- perform Git packaging

==================================================
1. CREATE A DEDICATED AUTONOMOUS-DEMO CASE
==================================================

Create a separate synthetic quality-exception case specifically for demonstrating
event-driven autonomous agent operation.

Suggested ID:
QE-011

Suggested business title:
Final-test anomaly

Use repository naming conventions if another stable ID/title fits better.

This case must be independent from QE-004 so the autonomous opening does not
mutate or contaminate the primary QE-004 demo story.

Recommended source facts:

Program:
PRG-A17 / Helios Atlas Inference

Quality exception:
QE-011

Lot:
LOT-B-219

Source:
Manufacturing Portal

Triggering condition:
new quality exception created after an abnormal final-test result

Lot status:
HOLD

Include enough realistic Manufacturing data for the existing
yield_exception_recovery workflow to investigate:
- lot
- product/configuration
- test stage
- first-pass result
- test-program revision
- baseline reference
- hold state
- relevant source version/timestamp

Keep QE-011 simpler than QE-004.

Its purpose is to demonstrate autonomous investigation, not introduce another
complex business scenario.

==================================================
2. SOURCE OF TRUTH
==================================================

QE-011 must exist as a real Manufacturing Portal business record when the event
fires.

Do not create QE-011 only as:
- a frontend fixture
- a control-plane fake card
- a fake agent activity record

Manufacturing Portal is authoritative for:
- QE-011
- LOT-B-219
- current test result
- hold status
- event version

The control plane stores only:
- event receipt
- invocation metadata
- workflow run
- findings
- downstream workflow state

==================================================
3. SOURCE EVENT
==================================================

Implement one bounded source event:

quality_exception_created

The event should contain/refer to:

- event_id
- event_version
- exception_id = QE-011
- program_id = PRG-A17
- lot_id = LOT-B-219
- source_system = Manufacturing Portal
- source record/version
- event timestamp

Do not let arbitrary event names launch arbitrary workflows.

==================================================
4. EVENT DISPATCHER
==================================================

Add the smallest possible event-trigger dispatcher.

Its responsibility is ONLY:

validated supported event
→ existing shared invocation service

Mapping:

quality_exception_created
→ yield_exception_recovery

Do not create:
- another orchestration engine
- another case runtime
- generic event scripting
- arbitrary webhook execution
- generic tool invocation

The dispatcher must call the same existing workflow path used by manual QE-004
invocation.

==================================================
5. IDEMPOTENCY / DUPLICATE PROTECTION
==================================================

One source event version must start at most one workflow run.

Use a deterministic idempotency/invocation key based on:
- source event ID
- event version
- workflow ID

Repeated delivery of the same event must NOT:
- create duplicate QE-011 cases
- create duplicate runs
- create duplicate investigation tasks

If the source event version changes legitimately, policy may allow reassessment
through a new invocation.

Document the behavior.

==================================================
6. DO NOT TRIGGER ON NORMAL APP STARTUP
==================================================

This is critical.

Opening:
- the frontend
- Overview
- Manufacturing Portal
- Operations

must NOT itself start a paid workflow.

Service restart must NOT automatically publish QE-011.

Normal demo startup must remain idle until explicitly prepared.

==================================================
7. ADD "PREPARE AUTONOMOUS DEMO"
==================================================

Use the existing Operations → Demo Controls surface.

Add a clearly labeled demo-only control such as:

Prepare autonomous opening

or:

Arm background quality event

Preferred wording:
Prepare autonomous opening

This control should:

1. Reset QE-011/event-trigger demo state.
2. Confirm the main demo environment is valid.
3. Arm exactly one synthetic Manufacturing source event.
4. Configure a short demo delay.
5. Return confirmation:
   Autonomous demo armed.

Do not start the agents directly from this button.

The button arms the BUSINESS EVENT.

The event later starts the workflow.

That distinction is central to the demo story.

==================================================
8. DEMO DELAY
==================================================

Support a bounded short delay so the presenter can prepare/open Overview.

Suggested:
5–10 seconds

Use one documented default, e.g. 8 seconds.

This is demo orchestration only.

Do not expose arbitrary scheduling code.

After the event fires:
- mark the event as emitted
- invoke exactly once
- do not continuously repeat

==================================================
9. EVENT ORIGIN MUST BE VISIBLE
==================================================

The workflow run should clearly record:

Invocation source:
Manufacturing source event

Event:
quality_exception_created

Case:
QE-011

Do not display:
User initiated

for this run.

Operations and Run History must make the event origin explicit.

==================================================
10. REAL AGENT WORK
==================================================

Once the event invokes yield_exception_recovery, reuse the REAL connected workflow.

The workflow should:
- validate the source signal
- retrieve relevant Manufacturing records
- use appropriate specialists
- retrieve RAG quality knowledge if now available
- begin investigation
- calculate/program impact where supported
- prepare findings

Do not fabricate fake step timers or fake activity simply for the Overview.

The Agent Workspace must reflect actual persisted run/activity state.

==================================================
11. AUTONOMY BOUNDARY
==================================================

The background workflow may autonomously:

- receive/open the case
- validate the event
- gather source evidence
- retrieve knowledge
- analyze comparability
- scope affected material
- calculate impact
- route permitted standard investigation work
- prepare a recommendation / decision package where applicable

It must NOT autonomously:

- release held material
- change quality disposition
- change test thresholds
- change manufacturing recipe
- reallocate constrained inventory
- change customer commitment
- approve its own recovery plan

When accountable human authority is reached:

stop / wait

and surface:

Human decision required

==================================================
12. AGENT WORKSPACE INTEGRATION
==================================================

The new visual Agent Workspace must support this story.

After QE-011 fires, Overview should visually show the actual participating agents
and their observed activity.

The agents remain the protagonists.

Example only — use real runtime state:

Program Coordinator
Reconciling findings · QE-011

Manufacturing
Scoping LOT-B-219

Validation
Checking quality procedure

Program & Commercial
Assessing milestone impact

Do not hard-code these exact labels if the actual run differs.

Display actual participating agents only.

Do not imply all agents are always running.

==================================================
13. BEFORE EVENT FIRES
==================================================

If Overview opens before the event delay elapses:

Agent Workspace should truthfully show:

No active investigation

or the current real state.

It must not show QE-011 as running before the source event actually fires.

Optionally show a subtle demo-only indicator under Demo Controls, not on the
business Overview:

Autonomous event armed

Do not fake business activity.

==================================================
14. WHEN EVENT FIRES
==================================================

Overview should update through existing lightweight run-state polling.

Do not start model calls from polling.

When QE-011 starts:

Agent Workspace should transition to actual running state.

Needs Attention should NOT immediately ask for human action while autonomous
investigation is still underway.

==================================================
15. HUMAN HANDOFF
==================================================

When QE-011 reaches its existing policy boundary:

show a clear handoff such as:

QE-011
Investigation complete
Awaiting Program Owner

or the actual relevant role according to implemented policy.

Do not keep completed agents visually "working."

This is the key narrative:

Agents started automatically.
Agents completed routine investigation.
Human enters only for accountable judgment.

==================================================
16. KEEP QE-011 OUT OF THE MAIN GOLDEN CASES
==================================================

QE-011 is a background/autonomy demonstration case.

It must not alter:
- QE-004 baseline
- DR-009 600/800/200 story
- CR-017
- CR-019
- shared customer commitments

Use isolated lot/supply records where needed.

Do not make DR-009 depend on QE-011.

==================================================
17. RAG INTEGRATION
==================================================

If the Quality RAG corpus is now present:

Allow the Manufacturing/Quality specialist to retrieve:
- approved hold/disposition SOP
- approved excursion procedure
- relevant historical investigation guidance

This is a good opportunity to demonstrate:
structured Manufacturing facts
+
RAG institutional knowledge

Do not make RAG mandatory for the event to launch.

Retrieval failure should not create fake knowledge.

==================================================
18. DEMO RESET
==================================================

Extend Phase 09 demo reset cleanly.

FULL DEMO RESET must:
- cancel/disarm pending QE-011 event
- stop/reset demo trigger metadata
- restore/remove QE-011 source records according to baseline design
- archive/reset current QE-011 workflow state
- invalidate stale action cards
- return Agent Workspace to baseline

Add a scoped reset:

Reset autonomous opening

or QE-011 reset.

Reset must be idempotent.

No delayed event may fire AFTER reset.

==================================================
19. REPLAY
==================================================

The presenter must be able to:

Prepare autonomous opening
→ event fires
→ agents run
→ reset autonomous opening
→ prepare again
→ event fires again exactly once

No duplicate residual runs.

==================================================
20. DEMO STATUS
==================================================

Extend demo status/preflight with:

Autonomous opening:
Idle / Armed / Event emitted / Workflow running / Human handoff ready / Failed

This is demo-management state, not a business quality status.

Keep it primarily in Demo Controls / operator tooling.

==================================================
21. OPERATIONS
==================================================

Operations should show:

QE-011 run

Invocation source:
Source event

Event ID/version

Workflow:
Yield / Quality Exception Recovery

Actual agents invoked

Tool/RAG activity

Final workflow state

Human handoff if reached

No hidden reasoning.

==================================================
22. WORKFLOWS & AUTOMATIONS
==================================================

Now that one real event trigger exists, update the relevant workflow display truthfully.

Yield / Quality Exception Recovery

Manual:
Connected

Source event:
Connected for bounded quality_exception_created demo trigger

Do NOT imply all source-event automations are live.

Saved generic event configurations remain configuration-only unless explicitly
connected.

Label scope carefully.

==================================================
23. NO GENERAL BACKGROUND SCHEDULER
==================================================

This implementation is intentionally narrow.

Do not activate:
- all saved event configs
- scheduled DR-009 automation
- generic condition watches
- generic event polling across every source system

We are proving one real event-driven pattern.

==================================================
24. EVENT IMPLEMENTATION
==================================================

Prefer an in-process/demo trigger service integrated with the existing source
application rather than a production event bus.

Do not introduce Kafka, RabbitMQ, cloud queues, or another large infrastructure
dependency solely for this demo.

The design should still make the production evolution obvious:

enterprise event bus/webhook
→ same trigger dispatcher
→ same workflow invocation service

Document that future path.

==================================================
25. AUTOMATED TESTING
==================================================

No paid model calls.

Use deterministic workflow/model doubles.

Test at least:

A. Prepare autonomous opening does not directly start workflow.

B. Event fires after configured delay.

C. Source event creates/uses authoritative QE-011 record.

D. Event invokes yield_exception_recovery exactly once.

E. Duplicate event delivery does not duplicate run.

F. App startup does not start event.

G. Frontend navigation does not start event.

H. Reset before event cancels/disarms it.

I. Reset after event removes current demo state safely.

J. Delayed event cannot fire after reset.

K. Replay works.

L. Agent Workspace reflects actual run state.

M. Human handoff appears only when workflow reaches that state.

N. QE-004/DR-009/CR-017/CR-019 unchanged.

O. Existing governance unchanged.

P. RAG retrieval remains scoped.

Q. Saved generic automation configurations remain inactive.

==================================================
26. BROWSER TEST
==================================================

Test the full demo behavior with deterministic agents:

1. Full Demo Reset.
2. Open Overview:
   no QE-011 running.
3. Operations → Demo Controls.
4. Prepare autonomous opening.
5. Return to Overview before event fires.
6. Confirm no fake agent activity.
7. Event fires.
8. QE-011 appears.
9. Agent Workspace shows real participating agents.
10. Workflow progresses.
11. Human handoff appears.
12. Open QE-011.
13. Open Operations run.
14. Reset autonomous opening.
15. Confirm QE-011/current activity cleared.
16. Replay successfully.

==================================================
27. OPTIONAL LIVE DEMO CHECK
==================================================

Provide exact steps for one paid live QE-011 autonomous demo.

Do NOT run automatically.

Manual sequence should be simple:

./scripts/demo prepare
Prepare autonomous opening
Open Overview
wait for source event
observe real agent workflow

Record expected API usage risk.

Do not trigger this automatically during demo startup.

==================================================
28. VISUAL / PACING REVIEW
==================================================

The event should be easy to follow visually.

Do not overload Overview with technical event metadata.

Business view:
QE-011 · Final-test anomaly
Agents investigating

Operations:
event details / invocation source

Agent Workspace:
actual participating agents

Human handoff:
separate and obvious

Use restrained motion only if the underlying work is actually running.

==================================================
29. TALK-TRACK SUPPORT
==================================================

Update demo documentation with a concise opening story:

"A quality exception arrived from the manufacturing system before I opened the
control plane. That enterprise event automatically started our existing
Yield / Quality Recovery workflow. The agents can investigate and prepare the
response autonomously. When they reach a consequential decision, the workflow
stops and brings in the accountable human."

Do not claim this is continuously running in production.

Describe it as:
a bounded connected event-driven demo path.

==================================================
30. FINAL REPORT
==================================================

Report:

1. QE-011 source data added
2. Source event contract
3. Trigger dispatcher architecture
4. Workflow invocation reuse
5. Idempotency
6. Agent Workspace integration
7. Human handoff
8. Demo controls/reset/replay
9. RAG usage if applicable
10. Operations integration
11. Tests/results
12. Manual live steps
13. API-cost safeguards
14. Known limitations
15. Production evolution path

==================================================
31. STOPPING POINT
==================================================

Stop after the autonomous background-event demo is implemented and verified
offline/browser.

Do not:
- activate all saved automations
- implement the DR scheduled runner
- add another workflow
- perform Git packaging

Success means:

explicit demo preparation
→ synthetic Manufacturing enterprise event
→ real existing yield workflow starts without human invocation
→ actual agents investigate
→ Overview visualizes real work
→ workflow reaches existing human authority boundary
→ reset/replay works reliably