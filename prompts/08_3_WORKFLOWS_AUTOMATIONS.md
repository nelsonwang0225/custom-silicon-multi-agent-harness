Continue working in the existing Stratos Silicon repository and current
Phase 08 thread.

Implement Phase 08.3:
WORKFLOWS & AUTOMATIONS.

We are prioritizing functionality over further visual polish for now.

Reuse the working Phase 08.2 / 08.2.1 implementation:
- connected CR-017 investigation
- proposals and decisions
- governed execution
- downstream validation result flow
- engineering review
- case/run/activity persistence
- workflow registry
- shared invocation service
- Phase 06 execution service
- Phase 07 reliability/evals
- current control-plane shell and design system

Do not redesign the app.
Do not change agent prompts or approval policy.
Do not expand source-system write permissions.
Do not build yield/delivery workflows end-to-end yet.
Do not fully connect freeform Concierge yet.
Do not create an active production scheduler or event bus.

Git remains relaxed:
- no commit/push work
- preserve unrelated local work
- avoid destructive operations

==================================================
1. PHASE 08.3 OBJECTIVE
==================================================

Turn Workflows & Automations into a functional control-plane surface where a
user can:

1. Understand which workflows exist.
2. See which capabilities are actually connected.
3. Manually launch supported workflows.
4. Inspect workflow run history.
5. Configure and save future schedule/event/condition triggers.
6. Understand what each automation would do and what authority it has.
7. Pause/edit/delete saved automation definitions.
8. See which future workflows are Simulated or Preview only.

Important:

Only existing supported CR-017 operations may actually execute.

Recurring schedules, source-event triggers and condition watches in this phase
are SAVED CONFIGURATIONS / PREVIEWS ONLY.

They must NOT run in the background.

==================================================
2. WORKFLOW CATALOG
==================================================

Use the existing workflow registry as the source of truth.

The catalog should include at minimum:

CONNECTED
- Requirement Change Analysis

SIMULATED / FUTURE
- Yield / Quality Exception Recovery
- Delivery Readiness / Commitment Planning

PREVIEW / ILLUSTRATIVE
- Standard Change / Touchless Handoff
- Specification Drift Detection
- Tapeout Readiness Review
- Platform IP / Errata Propagation
- Supply & Manufacturing Signals
- Post-Silicon Bring-Up / Errata
- Customer Commitment Review
- Portfolio Risk / Early Warning
- Scenario / Capacity Planning
- Next-Generation Requirements Harvest

Use actual registry entries where they exist.
For illustrative capabilities not in the executable registry, create
presentation/catalog metadata only.

Do not register a fake executor merely to populate the UI.

Each workflow card/row should show:

- name
- short business purpose
- execution mode:
  Connected / Simulated / Preview
- supported initiation methods
- current authority level
- relevant specialist roles
- most recent run, if any
- enabled/disabled state where applicable

Avoid long paragraphs.

==================================================
3. EXECUTION MODE MUST BE EXPLICIT
==================================================

Preserve the distinction:

CONNECTED
Real backend implementation exists.

SIMULATED
Interactive demo behavior exists, but no real agent/backend execution.

PREVIEW
Product concept/configuration only.

Do not use language such as:
Active
Monitoring
Running
Automated

unless the underlying behavior actually exists.

A saved automation definition is not an active background automation.

==================================================
4. WORKFLOW DETAIL PAGE
==================================================

Clicking a workflow opens a useful detail/workbench page.

For each workflow show:

OVERVIEW
- purpose
- connected/simulated/preview state
- supported programs/cases
- participating specialists
- allowed source systems
- allowed actions
- approval requirements

TRIGGERS
- Manual
- Scheduled
- Source event
- Condition
- Chat

Only show an initiation method as executable when actually supported.

INPUTS
- program/case scope
- relevant source context
- required identifiers

OUTPUTS
- expected analysis/result
- possible proposal/decision
- downstream handoff

AUTHORITY
Clearly state what the workflow may and may not do.

RUN HISTORY
Actual recorded runs for connected workflows.

AUTOMATIONS
Saved trigger configurations associated with this workflow.

==================================================
5. MANUAL INVOCATION — REAL CR-017
==================================================

Requirement Change Analysis must support actual manual invocation through the
existing shared invocation service.

Do not create a separate execution implementation.

For supported CR-017 initiation:

User selects:
- program
- existing case / CR-017 scope
- invocation reason/context if required

Then:
Run workflow

Requirements:
- use existing workflow identifier
- use trusted actor context
- preserve invocation id/idempotency
- prevent duplicate starts
- show actual created run ID
- navigate/link to CR-017 case/run
- preserve existing approval/execution boundaries

Do not allow manual invocation of unsupported workflow types.

If user attempts to run:
yield_exception_recovery
delivery_readiness
or a Preview workflow

show clearly:

This workflow is not connected yet.

Do not silently simulate it from a button labeled Run.

==================================================
6. RUN HISTORY
==================================================

Add a real run-history view.

Use existing case/run/activity persistence.

Show useful fields:

- workflow
- program
- case
- invocation source
- initiated by
- started
- completed / latest state
- business outcome
- proposal/decision state where relevant
- execution mode
- run ID

Keep technical trace detail secondary.

Important:
runtime completed
≠ business success

Represent:
- completed successfully
- escalation required
- waiting for review
- rejected
- partially executed
- verification failed
- physical result pending

accurately.

Clicking a run should open:
- related case
or
- a run detail page/drawer

==================================================
7. RUN DETAIL
==================================================

Provide a useful run detail experience using existing records.

Sections may include:

SUMMARY
- business question
- workflow
- program/case
- current outcome

AGENTS
- coordinator
- specialists actually invoked
- success/failure state

EVIDENCE
- key source references

ACTIVITY
- business event timeline

DECISION
- linked proposal / approval if any

EXECUTION
- linked action/verification if any

TECHNICAL DETAILS
Expandable:
- trace ID
- tool calls
- latency/token information if already recorded

Do not expose hidden chain-of-thought.

==================================================
8. AUTOMATIONS — DATA MODEL
==================================================

Create a reusable application-level automation definition model.

This is configuration metadata, NOT a background scheduler.

A saved automation should support fields such as:

- automation_id
- name
- workflow_id
- program scope
- case scope if applicable
- trigger_type
- trigger configuration
- owner/demo actor
- enabled/paused configuration state
- execution mode
- authority mode
- notification preference
- created_at
- updated_at

Use existing persistence conventions.

Keep automation configuration separate from authoritative business/source data.

Do not use these records to grant additional workflow permissions.

==================================================
9. TRIGGER TYPES
==================================================

Support configuration UX for:

A. MANUAL
Existing connected behavior where supported.

B. SCHEDULED
Examples:
- every weekday morning
- weekly readiness review
- daily program-risk check

C. SOURCE EVENT
Examples:
- new requirement revision
- validation result received
- manufacturing exception received

D. CONDITION
Examples:
- evidence becomes stale
- milestone at risk
- validation result still missing by threshold

E. CHAT
Represents that the future Concierge may invoke the workflow.

In Phase 08.3:
Scheduled, Source Event and Condition are configuration previews only.

Do not run them.

==================================================
10. SCHEDULE CONFIGURATION
==================================================

Build a polished schedule editor.

Support:
- daily
- weekdays
- weekly
- time
- timezone
- optional start date

Do not implement cron syntax as the primary user experience.

Show a human-readable summary such as:

Weekdays at 7:00 AM CT

Clearly display:

Saved configuration — background execution not enabled in this demo.

Do not show:
Next run: tomorrow 7:00 AM

unless an actual scheduler exists.

Instead show something like:
Would run: Weekdays at 7:00 AM CT

==================================================
11. SOURCE EVENT CONFIGURATION
==================================================

Allow users to configure illustrative source-event triggers based on known
source-system concepts.

Examples:

Engineering Hub
- requirement changed
- engineering decision updated

Validation Lab
- result received
- job status changed

Manufacturing Portal
- quality exception created
- lot status changed

Commercial ERP
- order/commitment changed

Program Planner
- milestone changed

Do not build arbitrary webhook ingestion.

Do not imply these events are actively monitored.

Label:

Trigger preview

or:

Configured — listener not active

==================================================
12. CONDITION CONFIGURATION
==================================================

Support bounded conditions using known business fields.

Examples:
- milestone risk becomes High
- evidence age exceeds threshold
- eligible quantity falls below requested quantity
- approval remains pending beyond threshold

Use structured field/operator/value controls.

Do not accept arbitrary executable code or expressions.

Again:

configuration only
no background evaluator

==================================================
13. AUTHORITY / EXECUTION POLICY
==================================================

Each automation must clearly show its authority.

Suggested categories:

READ ONLY
May investigate/reassess and produce findings.

PROPOSAL ONLY
May prepare a proposal but requires human approval.

BOUNDED EXECUTION
May execute only approved, policy-authorized actions.

Current CR-017 scheduled automation previews should default to:
READ ONLY

unless an existing policy explicitly supports more.

Saved automation configuration must never override Phase 06 authority.

==================================================
14. DUPLICATE / STORM PROTECTION — MODEL NOW
==================================================

Even though recurring execution is not active yet, model expected safeguards.

Show/configure concepts such as:

- deduplicate by case/event
- do not reopen resolved case automatically
- suppress duplicate notification
- minimum recheck interval

Do not build a complex event-processing platform.

Persist only the configuration required for future behavior.

==================================================
15. AUTOMATION UI
==================================================

Workflows & Automations page should have:

TOP
- concise title
- Connected / Simulated / Preview counts if useful
- New automation

WORKFLOW CATALOG
Modern card/list layout

AUTOMATIONS
Saved automation definitions

RUN HISTORY
Recent actual connected runs

Avoid walls of explanatory text.

For saved automations display:

- name
- workflow
- scope
- trigger summary
- authority
- enabled/paused CONFIGURATION state
- execution mode

Important:
Enabled configuration does not mean a worker is currently running.

Use wording such as:
Configured
Paused
Preview

rather than Active unless true.

==================================================
16. CREATE AUTOMATION FLOW
==================================================

Use a focused modal or stepper.

Suggested steps:

1. Choose workflow
2. Choose scope
3. Choose trigger
4. Define authority
5. Notifications
6. Review

Review screen should summarize:

Workflow
Program
Trigger
Authority
What the agent will do
What it cannot do
Human approvals required
Execution mode

Save automation

This stores configuration only.

==================================================
17. EDIT / PAUSE / DELETE
==================================================

Users should be able to:

- edit saved automation
- pause configuration
- resume configuration
- delete configuration

These actions modify only automation metadata.

They must not:
- cancel active source work
- revoke an existing approval
- close a business case
- mutate source systems

==================================================
18. SEED USEFUL DEMO AUTOMATIONS
==================================================

Add a small number of clearly labeled seeded examples.

Examples:

CR-017 Evidence Reassessment
Workflow:
Requirement Change Analysis

Trigger:
Validation result received

Authority:
Read only

Mode:
Preview trigger / Connected workflow

---

Morning Delivery Readiness
Workflow:
Delivery Readiness

Trigger:
Weekdays at 7:00 AM

Authority:
Read only

Mode:
Simulated / configuration preview

---

Yield Exception Watch
Workflow:
Yield / Quality Recovery

Trigger:
Quality exception created

Authority:
Proposal only

Mode:
Simulated / configuration preview

Do not claim these are actively running.

Use shared entities consistently with the demo scenarios.

==================================================
19. DEMO USE CASE ALIGNMENT
==================================================

Keep our canonical stories visible in the catalog:

1A Standard Change / Touchless
- Simulated
- eventual bounded standard downstream handoff

1B CR-017 Material Change
- Connected
- human-reviewed consequential action

2 Yield / Quality Exception Recovery
- Simulated
- human quality/allocation authority

3 Delivery Readiness
- Simulated
- human commitment/allocation authority

Do not accidentally imply Use Case 2 or 3 is executable yet.

==================================================
20. OVERVIEW INTEGRATION
==================================================

Add a concise automation/workflow signal to Overview only where useful.

Examples:
- recent workflow run
- configured automations count
- decision pending

Do not overload the landing page.

Do not show:
3 automations active

if no scheduler is running.

Use:
3 automation configurations

or equivalent.

==================================================
21. SEARCH INTEGRATION
==================================================

Global search should include:

- workflows
- automation definitions
- runs

Selecting:
workflow → workflow detail
automation → automation detail/edit
run → run detail / related case

Ask Stratos Concierge remains available as already designed.

==================================================
22. ALERTS
==================================================

Alerts may surface actual connected run states such as:

- investigation failed
- human review required
- execution verification failed

Do not generate alert entries simply because an automation configuration exists.

No:
Automation failed to run

because no scheduler is running.

==================================================
23. STRATOS CONCIERGE CONTEXT
==================================================

Do not fully wire freeform Concierge yet.

But update context and suggested questions for Workflows & Automations:

- What workflows are available?
- Which workflows are connected?
- Show recent CR-017 runs.
- What would this automation do?

If actual replies are still preview-only, keep that explicit.

Do not let Concierge save/execute automations yet unless that behavior is
already implemented through the same deterministic configuration API.

==================================================
24. OPERATIONS LINKAGE
==================================================

Prepare clean deep links from workflow runs to the future Operations view.

Do not fully build Operations yet.

Run detail should be reusable later in 08.6.

==================================================
25. API / HOST SURFACE
==================================================

Add thin typed host interfaces only as needed for:

- list workflow definitions
- read workflow definition
- start supported workflow
- list runs
- read run/activity
- list automations
- create automation config
- update automation config
- pause/resume configuration
- delete automation config

Validate all input server-side.

Do not expose:
- generic tool invocation
- generic source write
- arbitrary scheduling code
- arbitrary condition expressions
- direct browser MCP access

==================================================
26. AUTOMATED TESTS
==================================================

Add tests covering at least:

A. Connected workflow registry displays correct mode.

B. Unsupported workflows cannot execute.

C. Manual CR-017 invocation uses shared invocation service.

D. Duplicate invocation protection remains intact.

E. Run history reflects real persisted runs.

F. Runtime completion does not automatically display business success.

G. Saved schedule configuration does not execute.

H. Saved event trigger does not register an active listener.

I. Saved condition does not run automatically.

J. Automation authority cannot exceed workflow policy.

K. Program scope validation works.

L. Wrong/cross-program case rejected.

M. Edit/pause/delete affect only automation metadata.

N. Search finds workflow/automation/run.

O. Alerts do not imply nonexistent scheduler execution.

P. Simulated/preview workflows remain non-executable.

Q. CR-017 Phase 06 and 08.2 behavior remains intact.

R. CR-017 downstream 08.2.1 behavior remains intact.

S. Phase 07 offline evals remain 40/40.

==================================================
27. BROWSER / E2E TESTING
==================================================

Test:

1. Open Workflows & Automations.

2. Open Requirement Change Analysis.

3. Launch supported CR-017 workflow manually.

4. Open resulting run.

5. Open related case.

6. Create a scheduled automation configuration.

7. Confirm it is labeled configuration/preview and does NOT execute.

8. Edit it.

9. Pause it.

10. Resume configuration.

11. Delete it.

12. Create source-event preview.

13. Create condition preview.

14. Try running Yield Recovery → blocked/not connected.

15. Try running Delivery Readiness → blocked/not connected.

16. Search for workflow, run and automation.

Use deterministic model stubs in automated testing.

No paid model calls.

==================================================
28. VISUAL REQUIREMENTS
==================================================

Use the current Phase 08 visual system.

Do not spend significant time redesigning the whole app.

Prioritize:
- clear status/mode distinctions
- compact cards
- readable trigger summaries
- clear authority labels
- useful run-history table
- focused automation modal

Connected / Simulated / Preview should be obvious but not visually noisy.

Capture screenshots for:
- workflow catalog
- connected workflow detail
- automation creation
- automation list
- run history/detail

==================================================
29. DOCUMENTATION
==================================================

Update Phase 08 docs with:

- workflow catalog architecture
- manual invocation path
- automation configuration model
- trigger types
- authority model
- scheduler/event-listener limitation
- run-history semantics
- connected/simulated/preview definitions
- future activation path

Explicitly state:

Phase 08.3 DOES NOT implement background scheduling, event listening or
condition monitoring.

==================================================
30. FINAL REPORT
==================================================

When complete report:

1. Existing components reused
2. Workflow catalog implemented
3. Manual invocation behavior
4. Run-history behavior
5. Automation model
6. Trigger configuration behavior
7. Authority enforcement
8. Connected vs simulated vs preview matrix
9. Files changed
10. Tests/results
11. Screenshots/local URL
12. No paid models automatically run
13. Known limitations
14. Exact next 08.4 step

==================================================
31. STOPPING POINT
==================================================

Stop after Phase 08.3.

Do NOT continue into:
- active scheduler
- source-event listener
- condition watcher
- 1A workflow backend
- yield workflow backend
- delivery-readiness workflow backend
- connected freeform Concierge
- Operations implementation
- Phase 09 visual polish
- Git cleanup/push

Phase 08.3 is complete when the app supports:

workflow discovery
→ manual supported invocation
→ real run history
→ saved automation configuration
→ schedule/event/condition previews
→ authority visibility

without pretending that unimplemented background automation is running.