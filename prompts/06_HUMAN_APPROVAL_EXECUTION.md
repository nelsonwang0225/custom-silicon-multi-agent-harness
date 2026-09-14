Continue working in the existing take-home repository.

We are now implementing Phase 06 — Human Approval & Execution.

This should build directly on the completed compatibility update and the
existing Phase 04/05 runtime and multi-agent architecture.

Do not redesign the project.
Do not build the Phase 08 control-plane UI.
Do not implement the other two future workflows.
Do not broaden tool permissions.

Inspect the existing repository, implementation, tests, and
WORKFLOW_COMPATIBILITY_HANDOFF.md before making changes.

The repository is authoritative regarding:
- existing models
- current Plan / Decision contracts
- source-system APIs
- agent architecture
- existing test fixtures
- existing approval endpoints
- actual write operations already supported by the five mock applications

Preserve current working behavior and reuse existing components.

Git workflow is intentionally relaxed for now:
- do not create branches
- do not commit or push
- do not clean/rewrite history
- do not discard unrelated local work
- avoid destructive Git operations

==================================================
PHASE 06 OBJECTIVE
==================================================

Implement the first complete governed agent-execution flow for the
existing CR-017 requirement-change scenario.

The end-to-end lifecycle should become:

1. Agents investigate CR-017.
2. Agents produce an evidence-backed recommendation.
3. The system creates an exact, versioned execution proposal.
4. The workflow pauses for required human approval.
5. A trusted human reviews and approves/rejects that exact proposal.
6. The workflow resumes only if the approval is still valid.
7. Only the narrowly permitted source-system actions execute.
8. The application reads the source systems back.
9. The system verifies whether actual state matches the approved proposal.
10. Execution and verification are persisted separately.
11. The case remains open for downstream physical validation/results.

Success means:
"approved validation work was scheduled and verified"

It must NOT mean:
"validation passed"
"hardware is adequate"
"customer accepted the workload"
"program is complete"

==================================================
1. SCOPE — CR-017 ONLY
==================================================

Implement Phase 06 only for:

workflow:
requirement_change_analysis

scenario:
CR-017 material workload change requiring human review.

The existing future workflow types remain non-executable:
- yield_exception_recovery
- delivery_readiness

Do not create write capabilities for them.

Do not implement the touchless change path yet.
That will be a later extension using the same approval/execution model.

==================================================
2. PRESERVE THE CURRENT GOVERNANCE MODEL
==================================================

The demo principle is:

Agents may autonomously:
- investigate
- retrieve evidence
- analyze applicability
- calculate impacts
- compare approved options
- prepare proposals
- route work
- explain recommendations

Humans retain authority over consequential:
- engineering decisions
- quality decisions
- material/resource allocation
- customer commitments
- budget decisions where applicable

For CR-017 specifically:

Agents may recommend a validation approach.

The appropriate human approver must authorize the exact proposal before:
- a Validation Lab job is scheduled
- the permitted Program Planner changes are applied

The agent must never approve its own proposal.

Model output must never be treated as trusted approval identity.

==================================================
3. INSPECT THE EXISTING PHASE 06 SURFACE FIRST
==================================================

Before implementing:

Locate and document:
- current Plan model
- current Decision model
- compatibility-update proposal adapters
- workflow run persistence
- case/activity persistence
- source-system approval APIs
- Validation Lab scheduling APIs
- Program Planner write APIs
- SDK runner/session/state mechanisms
- any existing human-in-the-loop support
- existing identity/demo-user model
- existing retry/idempotency helpers
- CR-017 option fixtures and policy branches

Do not duplicate any existing framework if it can be extended cleanly.

If an existing source-system "approval" record already exists, determine
whether it represents:
a) business approval,
b) workflow approval,
c) source application state,
or d) something else.

Do not conflate these concepts.

==================================================
4. CREATE AN EXACT EXECUTION PROPOSAL
==================================================

The proposal must be an immutable snapshot of what the agents want
authorized.

Reuse the compatibility-update proposal model if possible.

It should bind at minimum:

- proposal_id
- proposal_version
- program_id
- case_id
- workflow_id
- workflow_definition_version
- originating_run_id

- recommended_option / option identifier
- exact proposed actions
- exact action arguments
- target source systems / records
- expected post-action state where known

- relevant configuration identifiers
- evidence references
- relevant evidence/source versions
- rationale
- assumptions
- prerequisites
- calculated cost/schedule impacts where supported

- required approval policy
- required approver role(s)
- creation timestamp

- stable content digest / fingerprint

The digest must bind all materially relevant proposal content.

Material changes must create a new proposal version or new proposal,
depending on existing architecture.

Examples of material changes:
- different validation option
- different test scope
- different configuration
- changed target record
- changed schedule parameters
- changed cost
- changed Program Planner updates
- materially changed supporting evidence
- changed action arguments

An approval of Proposal V1 must not authorize Proposal V2.

Do not bind approval to a mutable object by reference.

==================================================
5. TRUSTED HUMAN REVIEW AND APPROVAL
==================================================

Implement a trusted human-review boundary.

Use the repository's existing demo identity/auth mechanism if one exists.

If real authentication is not implemented:
- use a clearly documented trusted demo actor context
- keep identity server/application controlled
- never accept an arbitrary role from agent output
- never trust a client-supplied "I am an engineer" field without
  application-side validation

The human decision must record:

- decision_id
- proposal_id
- approved proposal version/digest
- actor identity
- actor role / authority source
- decision: approve / reject / request revision if existing UX supports it
- decision timestamp
- optional human comment
- applicable approval policy
- resulting status

Authorization checks must verify:
- correct program/case
- correct workflow
- exact proposal version/digest
- correct required role
- proposal is current
- proposal is not stale
- proposal is not already superseded
- evidence prerequisites remain valid
- action is still allowed under runtime policy

Do not allow:
- self-approval by the agent
- approval via freeform model text
- approval of "whatever the agent currently recommends"
- approval reuse after material proposal change
- approval reuse across cases
- approval reuse across programs
- approval reuse across workflows

==================================================
6. PAUSE AND RESUME THE AGENT WORKFLOW
==================================================

Integrate the existing OpenAI Agents SDK architecture with the repository's
workflow state.

Use the SDK's supported human-in-the-loop / pause-resume pattern where
appropriate.

Do not build a second agent runtime.

Desired behavior:

RUNNING
  ->
PROPOSAL_READY
  ->
WAITING_FOR_APPROVAL
  ->
APPROVED / REJECTED / REVISION_REQUIRED
  ->
if approved:
RESUMING
  ->
EXECUTING
  ->
VERIFYING
  ->
COMPLETED_EXECUTION or EXECUTION_FAILED

The exact state names may use repository conventions.

Important:
"completed execution" is not "case closed".

The case should remain capable of waiting for downstream lab results.

Persist enough state that the workflow can be resumed after process
restart/reload rather than depending on an in-memory chat session.

If the current SDK/runtime already persists resumable state, extend that
rather than duplicating it.

Test rejection and stale-approval branches as well as approval.

==================================================
7. NARROW WRITE BOUNDARY
==================================================

The only Phase 06 write capabilities should be the currently permitted
CR-017 actions already supported by the existing source applications.

Intended boundary:

A. Validation Lab
- schedule/create the approved validation job using the exact approved
  option and parameters

B. Program Planner
- apply only the currently permitted CR-017 program-plan/task updates
  defined in the existing repo/policy

First inspect the actual source APIs and existing execution contract.

Do not invent extra write operations simply because the mock API exposes
them.

Do NOT add:
- manufacturing recipe changes
- manufacturing hold/release changes
- test-threshold changes
- quality disposition
- inventory reallocation
- Commercial ERP commitments
- customer communications
- external emails
- new workflow permissions
- arbitrary CRUD tools

The agent must not receive a generic "write to any source system" tool.

Prefer narrow typed tools such as the existing specific scheduling/update
operations.

==================================================
8. APPROVED ACTION MANIFEST
==================================================

Before execution, construct or persist an exact action manifest tied to
the approved proposal.

For each action record:

- action_id
- proposal_id
- sequence/dependency if applicable
- tool/operation identifier
- exact arguments
- target system
- target object
- idempotency key
- required approval reference
- expected result / verification condition

Execution must compare the actual invocation against the approved manifest.

Reject execution if:
- operation differs
- arguments differ
- target differs
- approval is missing/stale
- action is outside policy
- prerequisite is no longer true

This is the enforcement point between recommendation and execution.

==================================================
9. IDEMPOTENCY AND RETRY SAFETY
==================================================

Phase 06 must handle retries safely.

Do not allow a workflow retry to accidentally:
- create a second validation job
- duplicate Program Planner tasks
- repeat a successfully completed source update

Use existing source-system idempotency support if available.

Otherwise introduce the minimum necessary application-side protection.

A repeated execution attempt for the same approved action should:
- return the existing result where safe
or
- detect the prior successful operation and mark it accordingly

Distinguish:
- action not attempted
- action started
- action succeeded
- action failed
- action outcome unknown
- action already completed/idempotent replay

Do not blindly retry "unknown outcome" writes.

==================================================
10. EXECUTION ORDER AND PARTIAL FAILURE
==================================================

Inspect the existing CR-017 source-system contract and determine the
appropriate order for:
- Validation Lab scheduling
- Program Planner update

Do not assume distributed ACID transactions across mock applications.

Implement explicit partial-failure handling.

Example:
If the Validation Lab job is successfully created but the Program Planner
update fails:

Do NOT:
- pretend the whole operation failed and recreate the lab job
- mark everything completed
- silently roll back unless the source API actually supports it

Instead:
- record the Validation Lab action as successful
- record Program Planner as failed
- preserve returned identifiers
- surface the case as partially executed / attention required
- allow safe retry of only the incomplete permitted step
- maintain audit history

Document the chosen compensation/recovery behavior.

==================================================
11. READBACK VERIFICATION
==================================================

After each successful write, independently read the affected source system
using its existing read interface.

Do not treat "POST returned 200" as sufficient business verification.

For Validation Lab verify the created/scheduled job:
- exists
- has expected program/case linkage
- uses the approved option/configuration
- contains the approved parameters
- has the expected owner/status where applicable

For Program Planner verify:
- intended task/plan records exist or changed as approved
- correct program/case linkage
- correct due dates/status/owners where specified
- no unapproved fields were changed

Create separate verification records.

Suggested semantics:
ACTION_SUCCEEDED
does not imply
VERIFICATION_SUCCEEDED

Possible outcomes:
- verified
- verification_failed
- verification_inconclusive

If verification fails:
- do not claim success
- preserve actual returned source identifiers
- surface the discrepancy
- require investigation/retry/reconciliation as appropriate

==================================================
12. ACTIVITY AND AUDIT RECORDS
==================================================

Use the compatibility-update activity timeline.

Persist meaningful business events such as:

proposal_created
proposal_superseded
approval_requested
proposal_approved
proposal_rejected
proposal_stale
workflow_resumed
action_started
validation_job_created
program_plan_updated
action_failed
verification_started
source_state_verified
verification_failed
execution_partially_completed
execution_completed

Do not store hidden chain-of-thought.

Useful audit information includes:
- who/what initiated the event
- proposal/action references
- source record IDs
- policy/role reference
- timestamp
- concise structured outcome
- relevant evidence/source refs

Keep technical SDK trace data separate but linkable via identifiers.

==================================================
13. DOWNSTREAM BUSINESS STATE
==================================================

After successful Phase 06 execution, CR-017 should NOT be marked as
resolved/accepted.

Represent the downstream status accurately.

Example:

Validation plan:
APPROVED_AND_SCHEDULED

Validation coverage:
PENDING_TEST_RESULTS

Customer acceptance:
PENDING

CR-017:
OPEN / IN_VALIDATION

Use existing repository terminology where possible.

The system must never infer:
- validation pass
- hardware adequacy
- customer acceptance

from scheduling alone.

==================================================
14. USER/DEVELOPER DEMO INTERFACE
==================================================

Do not build the Phase 08 control-plane UI.

However, provide a minimal developer/demo path using the existing CLI,
API, or current frontend surface if appropriate so Phase 06 can be
demonstrated and tested.

It should allow a developer/test user to:

1. Run CR-017 analysis.
2. Inspect the proposal.
3. Submit an authorized human approval or rejection.
4. Resume the workflow.
5. Observe source execution.
6. Inspect verification.
7. Inspect final business state/activity.

Do not create a disposable parallel interface if the current app already
has an appropriate path.

The future control plane and chat must eventually call the same approval
and execution service.

==================================================
15. SECURITY / GOVERNANCE TESTS
==================================================

Add explicit tests for at least the following:

A. No approval
- execution rejected
- zero write-tool calls

B. Wrong approver role
- execution rejected
- zero write-tool calls

C. Wrong case/program
- execution rejected

D. Proposal tampered after approval
- execution rejected

E. New proposal version after approval
- old approval rejected

F. Material evidence changes
- proposal becomes stale or requires re-approval according to policy

G. Rejected proposal
- cannot execute

H. Superseded proposal
- cannot execute

I. Agent tries unapproved action
- blocked

J. Agent changes an approved argument
- blocked

K. Agent invokes a non-permitted source-system operation
- blocked

L. Approved normal path
- exact approved writes occur once

M. Retry after successful write
- no duplicate lab job/task

N. Partial failure
- completed action is preserved
- incomplete action can be retried safely
- no duplicate completed actions

O. Verification mismatch
- execution does not report verified success

P. Restart/resume
- approval and workflow state survive persistence/reload

Q. Illustrative workflows
- still cannot execute or obtain tools

==================================================
16. CR-017 REGRESSION VERIFICATION
==================================================

All previous Phase 04/05 and compatibility tests must remain green.

Specifically verify:
- CR-017 analysis behavior is unchanged before approval
- existing specialists are unchanged unless Phase 06 requires a minimal
  tool addition
- existing read tools retain current scopes
- five mock source-app APIs remain backward compatible
- workflow registry behavior remains unchanged
- duplicate invocation protection still works
- current scenario/policy branches remain valid
- single-agent baseline remains functional

Do not weaken existing assertions to accommodate Phase 06.

==================================================
17. OFFLINE VS LIVE VERIFICATION
==================================================

Run comprehensive deterministic/offline tests without unnecessary paid
model calls.

Use fixtures/mocked model outputs where appropriate for approval/execution
tests.

Do not automatically invoke paid external models unless needed to resolve
an implementation problem.

At the end, identify a small optional live smoke test for us to run later.

A live smoke test should verify:
- real multi-agent CR-017 analysis
- proposal production
- pause
- human approval
- resume
- narrow source writes
- readback verification

But do not make paid/live execution a prerequisite for completing this
implementation phase unless repository architecture demands it.

==================================================
18. DOCUMENTATION
==================================================

Update the existing architecture/handoff docs.

Create/update a Phase 06 handoff that documents:

1. Actual approval architecture
2. Trusted actor model
3. Proposal/version/digest binding
4. Workflow pause/resume implementation
5. Exact permitted write operations
6. Action manifest/enforcement
7. Idempotency model
8. Partial-failure behavior
9. Readback verification
10. Business-state semantics after execution
11. Activity/audit model
12. Known demo-only limitations
13. What remains before Phase 07

Also include a sequence diagram or clear text flow:

CR-017 trigger
  -> coordinator/specialists
  -> proposal
  -> pause
  -> human decision
  -> approval validation
  -> resume
  -> Validation Lab write
  -> readback
  -> Program Planner write
  -> readback
  -> verified execution
  -> wait for physical validation results

==================================================
19. REQUIRED FINAL REPORT
==================================================

When complete, report:

1. Baseline inspected
   - what Phase 06-related pieces already existed

2. Architecture implemented
   - key models/services and how they relate

3. Exact write boundary
   - every source-system operation agents can now cause
   - every operation explicitly still prohibited

4. Human approval model
   - how identity, roles, proposal versions, and stale approvals work

5. Pause/resume behavior
   - how workflow state survives and resumes

6. Failure/idempotency behavior
   - retries, partial execution, unknown outcomes

7. Verification behavior
   - how source readback establishes verified execution

8. Files changed
   - exact files and why

9. Verification results
   table:
   Check | Command/Test | Result | Evidence

10. Test counts
    - existing regression suite
    - new Phase 06 tests
    - total passed/failed/skipped

11. Live tests not run
    - explicitly distinguish offline verification from live-model proof

12. Remaining work
    - exact next Phase 07 step
    - blockers if any

==================================================
20. STOPPING POINT
==================================================

Stop after Phase 06 implementation and verification.

Do NOT continue into:
- touchless change automation
- yield/quality recovery implementation
- delivery-readiness implementation
- Phase 07 evals
- Phase 08 control-plane UI
- chat
- workflow scheduler
- portfolio dashboard
- customer communication
- Git commit/push work

Do not mark Phase 06 complete unless the governed CR-017 path actually
supports:

proposal
-> trusted human decision
-> safe resume
-> exact approved execution
-> independent readback verification

with the required regression and governance tests passing.