Continue working in the existing Stratos Silicon repository and current
Phase 08 thread.

We are now implementing Phase 08.2:
CONNECTED CR-017 CASE WORKBENCH + DECISIONS.

The current Phase 08.1 Overview shell and visual system are acceptable for
now. Do not spend time on additional cosmetic refinement unless required for
the new connected functionality.

This phase should turn the current application from a read-only shell into a
real control plane for the existing CR-017 workflow.

Do not redesign the backend.
Do not build the other future workflows yet.
Do not expand tool permissions.
Do not change Phase 06 approval/execution authority.
Do not change Phase 07 graders, prompts or reliability behavior.

Git remains relaxed:
- no commit/push work
- preserve unrelated local work
- avoid destructive operations

==================================================
1. PHASE 08.2 OBJECTIVE
==================================================

Wire the existing real CR-017 requirement-change workflow into the control-plane UI.

The user must be able to follow the actual lifecycle:

CR-017
→ investigation
→ specialist findings
→ evidence
→ recommendation
→ versioned proposal
→ human review
→ approval/rejection
→ governed execution
→ source-system readback
→ verified execution state
→ downstream validation still pending

This must use the real backend built in Phases 04–07.

Do not fake connected results.

The flagship demo path is:
Use Case 1B — material workload change requiring human review.

==================================================
2. REUSE THE EXISTING BACKEND
==================================================

Inspect and reuse:
- workflow registry
- invocation service
- case/run/activity persistence
- Program → Case → Run relationships
- specialist/coordinator outputs
- proposal/version/digest model
- trusted demo identity model
- human decision records
- ExecutionService
- approved action manifest
- Validation Lab write path
- Program Planner write path
- readback verification
- Phase 07 trace/eval metadata where useful

Do NOT create:
- another orchestration layer
- another approval model
- another execution service
- a new source-of-truth database
- browser-owned workflow state

The UI should be a presentation/control layer over the existing architecture.

==================================================
3. CONNECTED CASE DETAIL — CR-017
==================================================

Upgrade the CR-017 case page from presentation shell to a connected case workbench.

The case page should answer:

1. What changed?
2. What evidence applies?
3. What is missing?
4. What did the agents conclude?
5. What decision is required?
6. What action was approved?
7. Did the downstream systems actually change?
8. What remains unresolved?

Use actual case/run/activity/proposal/decision/action/verification records.

The page should be able to represent these states truthfully:

- not investigated
- investigation running
- investigation completed
- escalation required
- proposal ready
- waiting for human review
- approved
- rejected
- superseded
- executing
- partially executed
- verification failed
- execution verified
- waiting for physical validation results

Do not collapse all of this into one status.

==================================================
4. CASE PAGE STRUCTURE
==================================================

Use the existing modern visual system.

Recommended structure:

A. CASE HEADER
- CR-017 · Workload change
- program/customer
- current business state
- execution mode: Connected
- current freshness/read state
- owner where available

B. LIFECYCLE
Use a visual lifecycle based on actual state:

Request
→ Evidence review
→ Recommendation
→ Human decision
→ Execution
→ Verification
→ Physical validation

Only mark stages complete when supported by actual records.

Do not mark:
- scheduled = validated
- validation job created = validation passed
- verified execution = customer accepted

C. REQUEST CHANGE
Show concise before/after requirement comparison using actual CR-017 facts.

D. EVIDENCE COVERAGE
Show:
- applicable evidence
- inapplicable evidence
- evidence gaps
- source/version/applicability

Use the existing contextual evidence modal for detail.

E. AGENT FINDINGS
Show the actual specialist outputs in a concise format:
- Change Impact
- Validation & Evidence
- Program & Commercial
- other actual specialists used by the run

Show:
- finding
- status
- evidence references
- unresolved questions
- actual completion/failure state

Do not expose hidden reasoning.
Do not invent specialist outputs.

F. RECOMMENDATION / OPTIONS
Use actual approved options and actual calculated schedule/cost consequences.

Show a clear comparison between available validation approaches where those
records exist.

Do not invent option values.

G. HUMAN DECISION
When a reviewable proposal exists, show the exact proposal and required review.

H. EXECUTION + VERIFICATION
After approval, show:
- authorized actions
- execution result
- source-system IDs
- readback verification
- partial failure if applicable

I. DOWNSTREAM STATE
Clearly state:
- validation job scheduled or not
- physical testing status
- validation coverage status
- engineering review status
- customer acceptance status

==================================================
5. RUN A REAL CR-017 INVESTIGATION FROM THE APP
==================================================

Add a user action such as:

Run investigation

or:

Reassess CR-017

This must call the existing shared workflow invocation service.

Do not create a frontend-only simulation.

Requirements:
- use the existing workflow identifier
- preserve duplicate invocation protection
- show meaningful loading/running state
- do not trigger multiple runs from double clicks
- expose the resulting run ID
- refresh case data after completion
- surface runtime failure/escalation truthfully

Do not automatically run the workflow merely by opening the page.

Do not run paid agents in automated tests.
Use deterministic test doubles.

The manually clicked connected demo may use the actual configured OpenAI runtime.

==================================================
6. LIVE AGENT ACTIVITY
==================================================

Connect the current Agent workspace to actual run state where available.

When a CR-017 run is executing, show:
- Program Coordinator
- actual specialist(s) invoked
- current/last known task state
- completed/failed/waiting status

Do not fabricate token-by-token progress.

If the backend only exposes completed activities rather than real-time streaming,
show:
- Running investigation
- latest recorded activity
- refresh/poll lightweight application state

Do not imply real-time streaming if it is polling.

Do not start models through polling.

When no run exists:
- show available agent roles as Preview, as today

When a completed run exists:
- show Last run / Recorded result, not Running

==================================================
7. BUILD THE DECISIONS EXPERIENCE
==================================================

Make Decisions a real connected page.

Use actual Phase 06 proposal/decision records.

The Decisions page should support:

Tabs or filters:
- Needs review
- Approved
- Rejected
- Executed / Completed
- Superseded / Stale

For each decision show:
- case/program
- proposal version
- recommendation
- required approver role/policy
- created time
- material impact summary
- current state

Clicking a decision opens a detailed review experience.

Use a route or a large contextual dialog depending on existing architecture.
Do not hide consequential information in a tiny popover.

==================================================
8. HUMAN REVIEW SCREEN
==================================================

For an actual CR-017 proposal, show:

- proposed option
- rationale
- evidence supporting the proposal
- material assumptions
- cost impact
- schedule impact
- exact proposed actions
- source systems affected
- proposal version/digest
- required review policy
- actual demo reviewer identity

Available actions:
- Approve
- Reject
- Request revision only if supported by the existing backend

Do not invent request-revision persistence if backend support does not exist.

Before approval, make the exact action manifest clear.

Example:
Validation Lab
→ schedule approved validation job

Program Planner
→ create/update approved linked planning records

No generic "Approve AI" button.

==================================================
9. TRUSTED DEMO IDENTITY
==================================================

Reuse the existing Phase 06 trusted demo actor model.

The top-right demo access/profile selection may control which allowed demo actor
is active.

However:
- browser role selection alone is not authority
- server/application must validate the trusted actor
- wrong role must remain rejected
- no arbitrary role string from the client
- do not imply production authentication

Display:
Demo identity

where appropriate.

If approval is rejected due to role mismatch, show the actual reason clearly.

==================================================
10. APPROVAL MUST BIND THE EXACT PROPOSAL
==================================================

The UI must submit the exact:
- proposal ID
- proposal version/digest
- case/program scope
- trusted actor context

Do not approve:
"whatever the current recommendation is."

If a proposal becomes stale or superseded:
- disable approval
- label it clearly
- link to the current proposal if available

Do not silently upgrade approval to a newer proposal version.

==================================================
11. GOVERNED EXECUTION FROM THE UI
==================================================

After successful approval, expose the supported execution action.

Use the existing ExecutionService.

The browser must NOT call source-system write APIs directly.

Desired sequence:

human approves
→ backend validates approval
→ exact action manifest executes
→ Validation Lab write
→ readback verification
→ Program Planner write
→ readback verification
→ execution result persisted

Use the actual existing ordering/policy.

Do not expand the write boundary.

Prohibited:
- manufacturing changes
- quality disposition
- inventory reallocation
- ERP commitment
- customer communication
- arbitrary source CRUD

==================================================
12. SHOW EXECUTION PROGRESS TRUTHFULLY
==================================================

Show explicit stages such as:

Approved
Executing
Validation job created
Validation job verified
Planner updated
Planner readback verified
Execution verified

For partial failure:
- show which action succeeded
- show which action failed
- show that safe retry/reconciliation is required

Do not replay completed actions accidentally.

Unknown outcome must remain:
Outcome unknown / reconciliation required

Do not show green success merely because a POST returned 200.

==================================================
13. READBACK VERIFICATION
==================================================

Surface the Phase 06 verification results.

For Validation Lab:
- job ID
- approved option/configuration
- expected parameters
- source verification state

For Program Planner:
- relevant link/task/milestone
- expected state
- source verification state

Provide a View source record action using the existing contextual modal or
source-app deep link.

Keep:
Action succeeded
distinct from
Verification succeeded

==================================================
14. CURRENT BUSINESS STATE
==================================================

After Phase 06 successful execution, show something equivalent to:

Validation plan:
Approved and scheduled

Execution:
Verified

Validation coverage:
Pending test results

Engineering review:
Pending / according to actual records

Customer acceptance:
Pending

CR-017:
In validation

Use actual repository terminology/data.

Never infer:
- validation passed
- hardware adequate
- customer accepted

from execution.

==================================================
15. OVERVIEW INTEGRATION
==================================================

Make Overview reflect actual CR-017 state when available.

Needs attention:
- CR-017 should link to the connected case

Needs review:
- count actual reviewable proposals
- do not infer review count from program risk

Agent workspace:
- reflect connected run state/last run where safely available

Alerts:
- real pending decision / failed execution / verification issues may appear
- do not fabricate alerts

Program health:
- use the existing defined program-health rule
- update only from the authoritative/displayed records

Do not create broad automatic recalculation logic outside existing view-model rules.

==================================================
16. SEARCH INTEGRATION
==================================================

Make the global search find:
- CR-017
- its proposal/decision where exposed
- evidence records
- recorded runs

Selecting:
- case → case workbench
- decision → decision review
- evidence → scoped evidence dialog
- run → related case/activity view

Preserve scope and preview/connected labels.

No new external search service.

==================================================
17. STRATOS CONCIERGE — THIS PHASE
==================================================

Do NOT fully connect freeform chat yet; that remains Phase 08.5.

However, update Concierge context so it can see:
- current program/case title
- whether a connected CR-017 run exists
- whether a decision is pending

Suggested questions may be contextual:
- Why is CR-017 blocked?
- Show the evidence gap.
- What decision is pending?

If chat responses remain preview-only, keep that explicit.

Do not fabricate a connected answer.

Do not let Concierge bypass the Decisions flow.

Voice input remains dictation into draft only.

==================================================
18. EMPTY / FAILURE / STALE STATES
==================================================

Build the connected UX for real-world states.

Support:
- no run yet
- run failed
- escalation required
- proposal not yet created
- proposal stale
- no authorized reviewer
- approval rejected
- execution partial failure
- verification mismatch
- source unavailable
- stale data

Do not only design the happy path.

==================================================
19. BACKEND / API ADAPTERS
==================================================

If the current frontend lacks safe access to the required existing application services,
add thin typed host adapters.

Prefer endpoints/services such as:
- read case
- start supported workflow
- read runs/activity
- read proposal/decision
- submit trusted review
- execute approved proposal
- read execution/verification

Use actual repo conventions/names.

Do not expose:
- generic source-system write proxy
- arbitrary tool invocation endpoint
- direct browser MCP access
- arbitrary filesystem access
- agent prompt modification APIs

Validate all client input server-side.

==================================================
20. SECURITY / GOVERNANCE UI TESTS
==================================================

Add browser/integration tests for at least:

A. Run investigation starts one supported workflow.

B. Double-click/replay does not duplicate invocation.

C. Unsupported workflow cannot execute.

D. Approval absent → execute disabled/rejected.

E. Wrong reviewer → approval rejected.

F. Stale proposal → approval rejected.

G. Superseded proposal cannot execute.

H. Approved exact proposal can execute.

I. Browser cannot alter approved action arguments.

J. Partial failure is displayed correctly.

K. Readback mismatch is not displayed as success.

L. Scheduling is not displayed as validation pass.

M. Customer acceptance remains pending.

N. Browser never receives generic write authority.

==================================================
21. AUTOMATED VERIFICATION
==================================================

Run:
- frontend/component tests
- relevant backend/API tests
- Phase 06 execution regressions
- Phase 07 offline eval suite
- Playwright/browser E2E
- type checks
- production build

Use isolated test state.

No paid agent calls in automated tests.

Preserve:
- 40/40 offline evals
- Phase 06 governance
- targeted Phase 07 reliability behavior
- five source-app interfaces

No need to run the six-case live smoke.

==================================================
22. MANUAL CONNECTED DEMO CHECK
==================================================

Provide exact instructions for a manual connected CR-017 walkthrough.

The intended manual sequence:

1. Open Overview.
2. Inspect CR-017.
3. Run connected investigation.
4. Watch/refresh agent activity.
5. Review actual findings/evidence.
6. Open the generated proposal.
7. Switch/select the correct demo reviewer.
8. Approve.
9. Execute the approved proposal.
10. Observe actual Validation Lab and Planner writes.
11. Observe readback verification.
12. Confirm CR-017 remains pending physical results/customer acceptance.

Do NOT automatically run paid models during implementation unless explicitly authorized.

==================================================
23. SCREENSHOTS / VISUAL REVIEW
==================================================

Capture and inspect:
1. Connected CR-017 case before investigation.
2. Connected agent investigation state.
3. Completed evidence/recommendation state.
4. Decision review screen.
5. Approved/executing state.
6. Verified execution state.
7. Failure/partial-failure state using deterministic fixture.

Use the current visual system.
Do not spend significant time restyling the entire app.

==================================================
24. DOCUMENTATION
==================================================

Update Phase 08 requirements/handoff with:
- connected CR-017 UI architecture
- host adapter/API surface
- run state mapping
- proposal/decision mapping
- exact approval boundary
- execution/readback mapping
- UI truth semantics
- manual connected demo commands
- known limitations

Clearly distinguish:
Connected CR-017
from
Simulated future workflows.

==================================================
25. FINAL REPORT
==================================================

Report:

1. Actual connected functionality implemented
2. Existing backend components reused
3. Host/API adapters added
4. Exact UI actions now supported
5. Approval/governance preservation
6. Exact connected write boundary
7. Files changed
8. Tests/results
9. Screenshots
10. Manual demo instructions and local URL
11. Paid/live behavior not automatically exercised
12. Known limitations
13. Next authorized Phase 08.3 step

==================================================
26. STOPPING POINT
==================================================

Stop after Phase 08.2.

Do NOT implement:
- yield workflow backend
- delivery-readiness backend
- touchless change backend
- recurring scheduler/event workers
- fully connected freeform Concierge
- Phase 08.3+
- Phase 09 polish
- Git commit/push work

Phase 08.2 is complete only when the existing CR-017 path can be operated
through the application as:

investigate
→ inspect evidence
→ review exact proposal
→ trusted human decision
→ governed execution
→ independent verification
→ truthful downstream status