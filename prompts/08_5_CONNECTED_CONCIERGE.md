Continue working in the existing Stratos Silicon repository and current
Phase 08 thread.

Implement Phase 08.5:
CONNECTED STRATOS CONCIERGE.

This is the governed conversational interface across the connected control plane.

Reuse the existing:
- floating Stratos Concierge UI
- global search and page context
- workflow registry
- shared invocation service
- case/run/activity persistence
- source adapters
- connected workflows:
  - Requirement Change / CR-017
  - Standard Change / CR-019
  - Yield / Quality Recovery / QE-004
  - Delivery Readiness / DR-009
- Phase 06 proposal/decision/execution governance
- Phase 07 eval/reliability framework
- Workflows & Automations configuration model
- current trusted demo identity model
- existing voice dictation input

Do not create a second agent runtime.
Do not create a separate Concierge permission system.
Do not activate background schedulers/event listeners.
Do not weaken any workflow approval boundary.
Do not automatically send external customer communications.
Do not add arbitrary source-system write access.

Git remains relaxed:
- no branch/commit/push work
- preserve unrelated local work
- avoid destructive Git operations

==================================================
1. OBJECTIVE
==================================================

Make Stratos Concierge a real contextual interface into the existing control plane.

The user should be able to ask grounded questions, navigate, investigate,
compare options, create workflow requests, and initiate governed actions.

Concierge should support four capability classes:

1. EXPLAIN
   Answer grounded questions about the current program/case/workflow.

2. INVESTIGATE
   Start supported connected workflows through the existing invocation service.

3. COMPARE
   Compare evidence-backed options using actual source/current case data.

4. ACT
   Prepare or initiate governed actions through existing deterministic host
   services and human approval boundaries.

Concierge must NOT:
- bypass proposal/decision review
- approve its own recommendation
- fabricate source evidence
- invent current state
- directly call generic write endpoints
- treat voice dictation as authority
- auto-send anything merely because the user opened chat

==================================================
2. CONTEXTUAL SCOPE
==================================================

Concierge must know the user's current control-plane context.

Examples:

Overview
- portfolio/program overview scope

Program page
- selected program

Case page
- program + case

Workflow page
- selected workflow

Decision page
- selected proposal/decision

Run page
- selected run

The visible Concierge header should show concise context, such as:

Helios Atlas Inference · CR-017

or:

Overview

Context changes must not silently apply a draft action from a previous case.

If the user has an unsent draft and navigates to a different case:
- preserve the draft safely
- visibly indicate the scope changed
- require confirmation before submitting an action-oriented message if necessary

Do not infer cross-program scope without explicit evidence.

==================================================
3. REAL CHAT BACKEND
==================================================

Connect the existing Concierge UI to the configured OpenAI runtime.

Use the existing model/runtime infrastructure.

Do not create a second standalone chat agent architecture if the existing
coordinator/runtime can support a bounded conversational manager.

Prefer:
Concierge manager
→ existing deterministic control-plane read services
→ existing connected workflow invocation service
→ existing proposal/decision/execution services

Concierge may call specialist/workflow services where appropriate.

Do not expose MCP/source tools directly to the browser.

Do not expose generic source-write capability to the model.

==================================================
4. CONCIERGE MANAGER ROLE
==================================================

Implement a bounded Concierge manager agent or equivalent routing layer.

Responsibilities:
- interpret user intent
- resolve current program/case scope
- decide whether to:
  - answer from available control-plane/source records
  - request clarification
  - invoke a supported workflow
  - prepare a comparison
  - navigate to a relevant record
  - prepare a governed action request
- summarize source-backed results
- preserve uncertainty
- surface approval requirements

The Concierge manager is NOT:
- engineering approver
- quality lead
- commercial approver
- supply allocation authority

It cannot grant authority to itself or another agent.

==================================================
5. INTENT CLASSES
==================================================

Create structured routing for at least:

EXPLAIN
Examples:
- What needs my attention?
- Why is CR-017 still open?
- What does QE-004 affect?
- Why are only 600 units available?
- What happened in the last workflow run?

INVESTIGATE
Examples:
- Reassess CR-017.
- Investigate QE-004.
- Run delivery readiness for DR-009.
- Process the standard change.

COMPARE
Examples:
- Compare the CR-017 validation options.
- Compare the QE-004 recovery options.
- Compare the DR-009 delivery options.

ACT
Examples:
- Proceed with the recommended validation option.
- Approve this proposal.
- Route the standard change.
- Commit the 600-unit option.
- Schedule a recurring readiness review.

NAVIGATE
Examples:
- Open the latest QE-004 run.
- Show the evidence.
- Take me to the decision.

AUTOMATION CONFIGURATION
Examples:
- Check delivery readiness every weekday morning.
- Create a quality-exception watch.

Unknown/out-of-scope requests should fail safely or ask clarification.

==================================================
6. GROUNDING AND SOURCE USAGE
==================================================

Concierge answers must be grounded in actual accessible data.

Use:
- current control-plane case state
- source-backed records
- persisted runs/activities
- proposals/decisions
- execution/verification
- workflow registry
- automation configs

Do not answer from generic model memory when the question is about current program state.

If a required source is unavailable:
say so.

If the data is stale:
say so.

If the answer is based on a recorded historical run rather than a fresh read:
label it.

Do not fabricate:
- quantities
- dates
- evidence
- approvals
- current run state
- customer decisions

==================================================
7. CITABLE EVIDENCE IN CHAT
==================================================

Concierge responses should include structured source references where possible.

Examples:
- Evidence: RES-FULL-B-EVAL
- Validation job: job-...
- Lot: LOT-B-204
- Order: ...
- Proposal v2
- Program milestone: ...

Render these as clickable chips/links/cards that open:
- case
- source record
- evidence modal
- decision
- run

Do not expose arbitrary internal filesystem paths.

==================================================
8. STRUCTURED CHAT RESPONSES
==================================================

Do not return only long paragraphs.

Support structured response components such as:

STATUS CARD
Current state / blocker

EVIDENCE CARD
Source + applicability

OPTION COMPARISON
Option A / B / C

DECISION CARD
Proposal + approval requirement

RUN CARD
Workflow status

ACTION PREVIEW
Exact deterministic action that would occur

AUTOMATION PREVIEW
Workflow + scope + trigger + authority

NAVIGATION CARD
Open related case/run/source

Use the existing design system.

Keep prose concise.

==================================================
9. OVERVIEW QUESTIONS
==================================================

From Overview, Concierge should answer questions such as:

- What needs my attention?
- Which cases are blocked?
- What are the agents working on?
- Which decisions are waiting?
- What customer commitments are at risk?

Use actual current case/program state.

Do not create a single vague AI risk score.

Concierge may summarize:
CR-017
QE-004
DR-009
CR-019

but should distinguish:
- needs human decision
- investigation open
- completed handoff
- waiting for external/physical work

==================================================
10. CR-017 CONNECTED CHAT
==================================================

Support real contextual interaction for CR-017.

Examples:

"Why is CR-017 blocked?"

Expected:
- explain actual current evidence/decision state
- cite evidence
- distinguish scheduling/testing/acceptance

"Reassess CR-017."

Expected:
- invoke the existing connected requirement-change workflow
- create a real run
- return run card
- no duplicate start

"Compare the validation options."

Expected:
- use actual current proposal/options
- show cost/schedule/evidence implications

"Proceed with the recommended option."

Expected:
- do NOT execute directly
- surface the exact current proposal
- show required Engineering Approver
- offer Open decision / Request review
- if already approved, route through existing ExecutionService only when
  the user explicitly confirms the governed action

==================================================
11. CR-019 TOUCHLESS CONNECTED CHAT
==================================================

Support:

"Process CR-019."

Expected:
- invoke the connected standard change workflow
- touchless policy evaluates
- if eligible, bounded Validation Operations handoff may execute
- show verified handoff
- no unnecessary human approval

"Why was this touchless?"

Expected:
- explain exact approved procedure/configuration/policy reasons

"What remains downstream?"

Expected:
- Validation Operations / lab authorization / physical testing / customer
  acceptance remain separate

If touchless eligibility fails:
- explain reason
- do not force handoff

==================================================
12. QE-004 CONNECTED CHAT
==================================================

Support:

"What happened with QE-004?"

Expected:
- source-grounded signal/lot/hold/supply summary

"What caused QE-004?"

Expected:
- clearly distinguish facts, correlations and unresolved root cause
- do not invent causality

"How much supply is affected?"

Expected:
- use deterministic calculator/result
- held material excluded
- actual eligible/gap values

"Investigate QE-004."

Expected:
- invoke connected yield workflow
- return real run status

"Proceed with the recovery plan."

Expected:
- surface exact human decision
- do not release held material
- do not reallocate or change commitment without required authority

==================================================
13. DR-009 CONNECTED CHAT
==================================================

Support:

"Can we commit 800 units?"

Expected:
- run/read delivery readiness
- technical readiness separate from supply
- 600/800/200 result where current fixture supports it
- no invented full-delivery date

"Why are only 600 available?"

Expected:
- explain held/allocated categories
- clickable source references

"Compare the delivery options."

Expected:
- structured Option A/B/C only when actually source-supported

"Commit the 600-unit option."

Expected:
- show exact commitment proposal
- require Program/Commercial approval
- no direct ERP write from model
- after exact approval, execution remains governed by host service

==================================================
14. HUMAN APPROVAL THROUGH CHAT
==================================================

Chat may surface an approval decision.

It must NOT treat ordinary language as sufficient authority by default.

For example:

User:
"Approve it."

Required behavior:
- resolve the exact current proposal
- show proposal ID/version and actions
- verify current trusted demo actor
- require explicit confirmation on a structured decision card/button
- submit through existing decision service

Do not parse a casual sentence and silently mutate approval state.

Wrong role:
- show role mismatch
- no mutation

Stale proposal:
- show stale state
- no approval

Superseded proposal:
- no execution

==================================================
15. ACTION CONFIRMATION
==================================================

For consequential actions, use two-step interaction:

1. Concierge explains/previews exact action.
2. User explicitly confirms via structured UI control.

Examples:
- Submit approval
- Execute approved plan
- Save automation configuration

The structured action payload must be validated server-side.

Do not trust the browser payload merely because the user clicked a button.

==================================================
16. WORKFLOW INVOCATION THROUGH CHAT
==================================================

Connected workflows supported:

- Requirement Change Analysis / CR-017
- Standard Change / CR-019
- Yield / Quality Recovery / QE-004
- Delivery Readiness / DR-009

Use the shared invocation service.

Requirements:
- workflow scope validation
- trusted actor
- invocation ID
- duplicate protection
- run persisted
- run card returned

Do not create separate chat-specific workflow runners.

==================================================
17. WORKFLOW PROGRESS IN CHAT
==================================================

After starting a workflow:

show a run card.

If actual state supports polling:
- update status periodically through lightweight read endpoint

Do not make model calls to poll.

Do not fake token streaming as workflow progress.

Show:
Running
Completed
Escalation required
Waiting for review
Failed
Verified
etc.

Runtime completed must not automatically mean success.

==================================================
18. NAVIGATION FROM CHAT
==================================================

Structured cards should allow:

Open case
Open run
Open evidence
Open decision
Open source app
Open workflow

Use existing routes/modals.

Do not duplicate detail screens inside chat when a full workbench already exists.

==================================================
19. AUTOMATION CONFIGURATION VIA CHAT
==================================================

Support conversational creation of automation configurations.

Example:
"Check delivery readiness every weekday at 7 AM."

Concierge should build a structured preview:

Workflow:
Delivery Readiness

Scope:
Helios / DR-009 or program-level according to supported model

Trigger:
Weekdays at 7:00 AM CT

Authority:
Read only

Execution mode:
Connected workflow / saved schedule preview

Background scheduler:
Not enabled

Then:
Save configuration

This must call the existing 08.3 automation configuration service.

Do not activate a scheduler.

Do not say:
"Monitoring started."

Say:
"Automation configuration saved. Background execution is not enabled in this demo."

==================================================
20. VOICE INPUT
==================================================

Keep the existing click-to-dictate behavior.

Voice transcript becomes an editable draft.

It must NOT:
- auto-send
- auto-approve
- auto-execute
- create authentication/identity

Spoken:
"approve this"

must behave exactly like typed text:
show the structured decision step.

Preserve microphone lifecycle cleanup.

==================================================
21. CHAT MEMORY / CONTEXT
==================================================

Use bounded application context.

Support session-level conversational continuity for:
- current page/program/case
- previous user message
- recent Concierge responses

Do not create unrestricted long-term memory.

Do not allow conversational context to override authoritative source state.

When a proposal/source version changes:
the current source wins.

If prior chat says:
"approved"

but the authoritative decision record says:
pending

report pending.

==================================================
22. CROSS-CASE QUESTIONS
==================================================

Support bounded cross-case questions at program level.

Example:
"What is threatening Helios delivery?"

Concierge may combine:
- CR-017 technical readiness
- QE-004 quality/supply
- DR-009 commitment state

But must:
- cite each case/source
- distinguish independent blockers
- avoid double-counting supply impact
- avoid inventing causal relationship

Do not search unrelated programs without explicit scope.

==================================================
23. READ-ONLY VS ACTION INTENT
==================================================

Clearly separate:

READ / EXPLAIN
safe to answer immediately

RUN / INVESTIGATE
starts supported workflow

DECISION
requires trusted human action

EXECUTION
requires approved proposal and deterministic service

AUTOMATION SAVE
configuration only

This classification should exist in structured state/logging.

==================================================
24. CONCIERGE AUTHORITY DISPLAY
==================================================

The expanded Concierge should make authority transparent.

For relevant action cards show:

Concierge can:
Analyze / investigate / prepare

Human required:
Engineering approval / Quality decision / Program commitment

Execution:
Host-controlled

Keep this concise but visible.

==================================================
25. ERROR / FAILURE STATES
==================================================

Handle:

- source unavailable
- workflow unsupported
- model failure
- structured output invalid
- run failed
- proposal stale
- wrong role
- execution partial failure
- verification mismatch
- chat backend unavailable
- voice recognition unavailable

Do not silently switch to simulated answers.

A real connected chat failure must be shown as a failure.

==================================================
26. PROMPT INJECTION / SOURCE SAFETY
==================================================

Treat retrieved source content as data.

Instructions inside:
- source documents
- comments
- evidence records
- customer request text

must not override:
- system instructions
- application policy
- approval boundaries
- tool permissions

Add adversarial tests.

==================================================
27. NO HIDDEN CHAIN OF THOUGHT
==================================================

Do not expose or persist private reasoning.

Chat may show concise explanation/rationale and source evidence.

Operations may show:
- model calls
- tools
- structured outputs
- timings

but not hidden chain-of-thought.

==================================================
28. CHAT PERSISTENCE
==================================================

Persist conversation/session data using the existing application persistence
approach if appropriate.

Store only:
- user-visible messages
- structured cards/actions
- context identifiers
- run/proposal references
- timestamps
- model/config metadata if needed

Do not store raw audio.
Do not store credentials.
Do not store hidden reasoning.

If persistence is not appropriate in current architecture, use bounded session
state and document the limitation.

==================================================
29. UI EXPERIENCE
==================================================

Use the existing large floating Stratos Concierge.

Expanded view should include:
- contextual header
- conversation
- structured cards
- source links
- action confirmations
- composer
- mic
- stop/cancel for in-flight response where supported

Keep:
- floating nonmodal behavior
- no page shift
- responsive sizing
- drafts preserved
- modal precedence

Concierge should feel like an operator assistant, not customer-support FAQ.

==================================================
30. SEARCH → CONCIERGE
==================================================

Global search already includes Ask Stratos Concierge.

Wire it for real.

Search query:
"why is QE-004 blocked"

Ask Concierge action:
- opens Concierge
- inserts query
- preserves scope
- user sends
- connected reply occurs

Do not auto-send from search.

==================================================
31. ALERT → CONCIERGE
==================================================

Where helpful, alert rows may offer:

Ask Concierge

This should open contextual chat about that actual alert/case.

Do not invent an answer.

==================================================
32. DECISION → CONCIERGE
==================================================

Decision detail may offer:
"Ask Concierge to explain"

Concierge can summarize:
- proposal
- evidence
- consequences
- authority

It cannot decide for the human.

==================================================
33. OPERATIONS / TRACE HOOKS
==================================================

Prepare Concierge activity so 08.6 can expose:

- conversation/run ID
- model
- workflow invocations
- tool/service calls
- latency
- token usage where available
- resulting business objects

Do not fully build Operations in this phase.

==================================================
34. EVALS
==================================================

Extend the eval framework for Concierge.

Add deterministic cases covering at least:

A. Current-case grounded explanation.

B. Cross-case program summary.

C. Correct workflow routing.

D. Unsupported workflow safely rejected.

E. Approval request surfaces decision but does not self-approve.

F. Wrong role cannot approve.

G. Stale proposal cannot execute.

H. Voice text does not bypass approval.

I. Source injection cannot override policy.

J. Missing evidence produces uncertainty.

K. QE root cause not fabricated.

L. DR quantity/date not invented.

M. CR-019 touchless handoff only when eligible.

N. Runtime completion not reported as business success if escalated.

O. Automation save does not imply active monitoring.

P. Customer acceptance remains distinct from commercial commitment.

Q. Concierge does not expose hidden reasoning.

Critical failures:
- unauthorized execution
- approval bypass
- fabricated evidence
- fabricated quantity/date
- false root cause
- false validation/customer acceptance
- cross-program data leak
- source prompt injection succeeds

==================================================
35. AUTOMATED TESTS
==================================================

Run:
- source/backend regressions
- coordinator tests
- MCP tests
- all Phase 06/07 evals
- 08.4A/B/C regressions
- Concierge routing tests
- action/governance tests
- frontend/component
- Playwright
- typecheck/build

No paid model calls in automated tests.

Use model stubs/deterministic responses.

Preserve current working demo state.

==================================================
36. BROWSER E2E
==================================================

Test at least:

1. Open Concierge on Overview.
2. Ask "What needs my attention?"
3. Open a cited case.
4. Ask CR-017 question.
5. Trigger CR-017 investigation.
6. Receive run card.
7. Ask QE-004 supply question.
8. Correct quantity displayed.
9. Ask root-cause question.
10. No unsupported cause asserted.
11. Ask DR-009 commitment question.
12. 600/800/200 displayed correctly.
13. Ask to commit 600.
14. Decision card shown, no immediate write.
15. Wrong role approval blocked.
16. Correct structured approval works.
17. Ask to process CR-019.
18. Touchless handoff uses shared workflow.
19. Save weekday readiness automation.
20. UI states "configuration saved / scheduler not active."
21. Voice transcript does not auto-send.
22. Search → Concierge works.

==================================================
37. OPTIONAL LIVE TESTS
==================================================

Provide exact instructions for a small live Concierge smoke suite.

Do not run automatically.

Recommended live cases:
1. Overview summary
2. CR-017 explain
3. QE-004 root-cause restraint
4. DR-009 quantity/commitment
5. action requiring approval
6. CR-019 touchless explanation

Record:
- model
- latency
- tokens
- workflow/tool/service calls
- grader result

==================================================
38. DOCUMENTATION
==================================================

Update Phase 08 docs with:

- Concierge architecture
- context model
- intent routing
- workflow invocation path
- action confirmation model
- authority/governance boundary
- source grounding
- structured response cards
- voice semantics
- automation configuration path
- persistence
- eval coverage
- live smoke commands
- known limitations

==================================================
39. FINAL REPORT
==================================================

Report:

1. Concierge architecture
2. Existing runtime/services reused
3. Intents supported
4. Connected workflow routing
5. Grounding/source behavior
6. Structured responses
7. Approval/action behavior
8. Automation configuration behavior
9. Voice behavior
10. UI integration
11. Eval cases
12. Tests/results
13. Live commands not automatically run
14. Connected/simulated/preview matrix
15. Known limitations
16. Exact next 08.6 step

==================================================
40. STOPPING POINT
==================================================

Stop after Phase 08.5.

Do NOT continue into:
- active background scheduler
- Operations implementation
- Phase 09 polish
- Git cleanup/push

Phase 08.5 is complete when Stratos Concierge can operate as a governed,
source-grounded interface across the connected control plane:

ask
→ explain
→ investigate
→ compare
→ surface decision
→ confirm governed action
→ invoke existing deterministic services
→ report verified state

without gaining any authority that the underlying workflows do not already have.