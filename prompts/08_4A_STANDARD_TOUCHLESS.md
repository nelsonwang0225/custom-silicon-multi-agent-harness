Continue working in the existing Stratos Silicon repository and current
Phase 08 thread.

Implement Phase 08.4A:
CONNECTED STANDARD CHANGE / TOUCHLESS HANDOFF.

This is Use Case 1A of the final demo.

We are now implementing it as a REAL connected workflow, not an isolated
simulation.

Reuse the existing control-plane architecture, workflow registry, shared
invocation service, coordinator/specialists, case/run/activity persistence,
source adapters, Phase 06 governance contracts, Phase 07 eval framework,
Phase 08 case/workflow UI, and Workflows & Automations surfaces.

Do not redesign the application.
Do not create a parallel agent runtime.
Do not expand unrelated source-system permissions.
Do not implement Yield Recovery or Delivery Readiness in this prompt.
Do not fully connect Stratos Concierge yet.
Do not activate saved recurring/event/condition automations.

Git remains relaxed:
- no branch/commit/push work
- preserve unrelated local work
- avoid destructive Git operations

==================================================
1. OBJECTIVE
==================================================

Implement the connected "Standard Change / Touchless Handoff" scenario.

Business story:

Helios AI submits a change to the upcoming acceptance/validation package.

Unlike CR-017, this request does NOT introduce a new unsupported engineering
condition.

The requested workload/profile is already covered by:

- an approved validation procedure;
- the applicable current hardware/software configuration;
- existing program policy;
- defined downstream ownership;
- bounded standard routing rules.

The coordination work is still real:

request received
→ interpret request
→ compare against approved baseline
→ verify exact procedure/configuration applicability
→ identify reusable evidence and remaining required work
→ check touchless eligibility policy
→ build an execution-ready downstream package
→ route it to Validation Operations
→ verify the downstream handoff

No human approval is required before that bounded handoff because the procedure
and routing policy were approved previously.

Touchless does NOT mean:
- agent approves engineering adequacy;
- agent authorizes the physical lab;
- agent changes validation criteria;
- agent grants customer acceptance;
- agent commits delivery;
- agent bypasses policy.

Successful end state:

"Standard change package prepared and handed to Validation Operations."

NOT:

"Validation approved/passed."

==================================================
2. KEEP THIS IN THE SAME CHANGE-MANAGEMENT FAMILY
==================================================

Inspect the existing workflow taxonomy before changing anything.

Prefer representing 1A as a policy/scenario route within the existing
requirement-change workflow family rather than creating a duplicate orchestration
stack.

Conceptually:

workflow family:
requirement_change_analysis

policy path:
standard_touchless_handoff

Existing CR-017 remains:

workflow family:
requirement_change_analysis

policy path:
material_change_human_review

Use repository naming conventions rather than these exact strings where
appropriate.

The two routes must share the same coordinator/specialists and common runtime
where practical.

Do NOT build separate "touchless agents."

==================================================
3. CREATE A DISTINCT STANDARD-CHANGE DEMO CASE
==================================================

Do NOT reuse CR-017 as the touchless case.

Create a separate synthetic case/request with a stable identifier consistent
with existing fixtures.

Choose an identifier that does not collide with existing cases.

The request should be realistic but intentionally standard.

Recommended scenario:

Helios asks Stratos to add an already-approved workload/profile to the next
acceptance validation package for the existing program configuration.

The requested profile:
- already exists in the approved validation catalog/procedure;
- applies to the exact current silicon revision;
- applies to the correct software/firmware baseline;
- has an approved test method;
- has defined required inputs/samples;
- has defined Validation Operations ownership;
- requires no new engineering interpretation or non-standard test scope.

Some previous evidence may be reusable, while the approved procedure may still
require bounded downstream lab work for the nominated samples.

Do not choose a scenario whose success depends on assuming:
"smaller context must be covered because a larger one passed."

Touchless eligibility must come from explicit approved applicability data.

==================================================
4. SOURCE-SYSTEM STORY
==================================================

Use the existing five source applications.

The connected workflow should primarily use:

ENGINEERING HUB
- current requirement baseline
- configuration
- approved procedure/catalog applicability
- relevant engineering policy

VALIDATION LAB
- approved procedure
- historical applicable evidence
- downstream Validation Operations queue/intake surface
- required sample/test scope

PROGRAM PLANNER
- current program milestone/context
- downstream handoff/task linkage where permitted

COMMERCIAL ERP
Only if genuinely required for request/customer context.
Do not add ERP usage merely to increase tool count.

MANUFACTURING PORTAL
Only if sample eligibility or physical-material facts are actually necessary.
Do not force every source app into the workflow.

The workflow should use the minimum relevant systems.

==================================================
5. INPUT CONTRACT
==================================================

Define/reuse a structured input for the standard-change case including:

- program
- customer
- case/change request ID
- current requirement baseline/version
- requested validation/package change
- hardware configuration
- software/firmware version
- requested timing
- customer/source request reference

The agent must not fabricate missing input.

If required information is genuinely missing:
- stop touchless eligibility;
- request clarification or escalate according to policy.

==================================================
6. TOUCHLESS ELIGIBILITY POLICY
==================================================

Implement a deterministic host-side policy that determines whether the
workflow may use the standard touchless handoff route.

Do not allow the model alone to decide its own authority.

At minimum require:

A. Request maps to a recognized standard change type.

B. Exact approved procedure exists.

C. Procedure applies to the exact hardware/configuration revision.

D. Procedure applies to the relevant software/firmware baseline.

E. Requested operating conditions are within the explicitly approved scope.

F. No unresolved conflicting evidence invalidates applicability.

G. No open material engineering exception requires review.

H. Required downstream owner/queue is known.

I. The proposed downstream action is only the permitted standard handoff.

J. No consequential customer commitment, quality disposition or engineering
   acceptance is being requested.

Represent the eligibility result explicitly, for example:

touchless_eligible:
true / false

with structured reasons.

If any mandatory rule fails:
- do NOT continue touchlessly;
- surface the exact reason;
- transition to a review/escalation path;
- do not silently convert the case into CR-017.

==================================================
7. AGENT STEPS
==================================================

Use existing agents/specialists.

PROGRAM COORDINATOR
- owns intake/case
- interprets the requested process path
- delegates bounded work
- consolidates the package
- applies host policy result
- routes permitted handoff

CHANGE IMPACT SPECIALIST
- compare request with baseline
- identify exactly what changed
- establish whether this is a standard catalog/procedure change
- identify affected configuration/program objects

VALIDATION & EVIDENCE SPECIALIST
- locate approved procedure
- verify procedure/version applicability
- identify reusable evidence
- identify remaining required standard work
- identify Validation Operations handoff requirements

PROGRAM / COMMERCIAL SPECIALIST
- establish timing/program consequence
- check requested date against known milestone context
- avoid inventing commercial commitment

Use Supply/Manufacturing specialist only if source facts actually require it.

==================================================
8. REQUIRED AGENT CONCLUSIONS
==================================================

For the successful touchless fixture, the agent should conclude something
equivalent to:

- request matches an existing approved standard procedure;
- the procedure applies to the exact program configuration;
- no non-standard engineering decision is required before routing;
- identified existing evidence may be reused where applicable;
- specified downstream lab/operations work remains required;
- the package is eligible for standard handoff.

It must NOT conclude:

- customer acceptance granted;
- hardware qualified;
- validation passed;
- no lab work needed, unless the actual procedure explicitly says so;
- engineering approval newly granted;
- requirements waived.

==================================================
9. EXECUTION-READY HANDOFF PACKAGE
==================================================

Create a structured downstream handoff package.

Reuse existing proposal/action concepts where practical, but do not misuse the
human-approval proposal contract if no approval is required by policy.

The package should contain at minimum:

- package ID/version
- program/case
- customer request
- approved procedure/version
- applicable configuration
- evidence references
- reusable evidence
- remaining required standard tests/work
- sample/input requirements
- requested timing
- downstream owner/queue
- completion criteria
- provenance
- workflow/run reference

This should be inspectable from the control plane.

==================================================
10. PRE-AUTHORIZED HANDOFF ACTION
==================================================

Implement ONE narrowly bounded autonomous downstream action:

Route/create the standard validation-intake package for Validation Operations.

Inspect existing Validation Lab APIs/contracts first.

Use the existing appropriate intake/work-item mechanism if one already exists.

If no suitable bounded intake concept exists, add the smallest typed
Validation Operations intake/work-item contract.

Do NOT reuse "schedule validation job" if scheduling requires human/lab
authorization under the existing Phase 06 boundary.

The touchless action should mean:

"Validation Operations has received an execution-ready package."

It must NOT mean:

"the lab job is authorized/scheduled."

==================================================
11. NO HUMAN APPROVAL FOR STANDARD HANDOFF
==================================================

For the successful fixture:

The Program Operator may initiate the workflow.

The agents may complete the standard preparation and bounded handoff without
requiring Engineering Approver approval.

This is allowed ONLY because the host touchless policy verifies that:

- procedure already approved;
- configuration already covered;
- requested action is a permitted standard handoff;
- no consequential engineering decision occurs.

Do not create a fake human approval merely because CR-017 has one.

The contrast between 1A and 1B is an explicit demo requirement.

==================================================
12. DOWNSTREAM VALIDATION OPERATIONS
==================================================

Represent Validation Operations as the downstream human/operational team.

After handoff, show:

Validation Operations intake:
Received

Package:
Complete / Verified

Owner:
Actual seeded downstream role/queue

Lab authorization:
Pending / separate

Physical testing:
Not started

Customer acceptance:
Pending

The control plane should stop at the verified standard handoff.

Do not automatically perform:
- lab authorization
- job scheduling
- physical validation
- engineering acceptance
- customer acceptance

==================================================
13. VERIFY THE HANDOFF
==================================================

After the handoff write succeeds:

Perform an independent readback through the existing source interface.

Verify:

- intake/work item exists;
- correct program/case;
- correct procedure/version;
- correct request/configuration;
- correct downstream owner;
- correct evidence/package references;
- expected status.

Separate:

ACTION_SUCCEEDED

from:

HANDOFF_VERIFIED

A successful write response alone is insufficient.

==================================================
14. IDEMPOTENCY
==================================================

Repeated run/retry must not create duplicate Validation Operations intake items.

Use existing invocation/action idempotency architecture.

Support:

- first handoff
- readback verification
- replay returns existing handoff where safe
- failed handoff retry
- unknown outcome requires reconciliation

Do not blindly repost unknown writes.

==================================================
15. TOUCHLESS FALLBACK / ESCALATION CASES
==================================================

Add deterministic variants where touchless eligibility fails.

At minimum:

A. Wrong firmware/software revision.

B. Procedure exists but does not cover requested condition.

C. Conflicting evidence.

D. Missing approved procedure.

E. Non-standard test parameter requested.

F. Engineering exception/waiver required.

G. Customer request implicitly changes acceptance criteria.

H. Downstream queue/ownership cannot be established.

Expected behavior:

touchless route stops

→ case requires review/clarification

→ zero autonomous downstream write

Do not automatically use CR-017's exact material-change proposal unless the
case actually meets that workflow contract.

==================================================
16. WORKFLOW REGISTRY / CATALOG
==================================================

Update the workflow catalog so Standard Change / Touchless is no longer merely
Preview.

Represent it truthfully.

Possible model:

Requirement Change Analysis
Connected

Supported routes:
- Standard touchless handoff
- Material change / human review

OR, if the UI requires separate catalog entries:

Standard Change / Touchless
Connected route within Requirement Change Analysis

Material Requirement Change
Connected route within Requirement Change Analysis

Do not imply there are two separate agent platforms.

==================================================
17. CASE / PROGRAM UI
==================================================

Add the new connected standard-change case to the appropriate Helios program.

Its case detail should show:

REQUEST
What the customer changed

APPLICABILITY
Approved procedure match

EVIDENCE
Reusable evidence / remaining work

POLICY
Touchless eligibility and reasons

HANDOFF PACKAGE
What goes downstream

EXECUTION
Validation Operations intake created

VERIFICATION
Readback confirmed

DOWNSTREAM
Lab authorization/testing pending

Use the existing visual system.
Do not spend significant time on cosmetic redesign.

==================================================
18. LIFECYCLE UI
==================================================

A suitable lifecycle is:

Request
→ Applicability
→ Evidence
→ Policy check
→ Package
→ Handoff
→ Verification

Then downstream:

Validation Operations
→ Lab authorization
→ Physical testing
→ result/review

The connected agent workflow completes at Verified Handoff.

Do not mark downstream lab stages complete.

==================================================
19. OVERVIEW INTEGRATION
==================================================

Surface the new case on Overview only where useful.

Examples:

Before:
Standard change · New request

During:
Standard change · Assessing applicability

After:
Standard change · Handed to Validation Operations

Do not leave it in Needs attention after verified handoff unless another human
action genuinely requires control-plane attention.

Do not alter overall program health arbitrarily.

==================================================
20. WORKFLOWS & AUTOMATIONS INTEGRATION
==================================================

Update 08.3 surfaces.

Workflow detail should explain both connected change-management routes.

Manual launch should allow selection of the standard-change case when supported.

Run history should show:

policy path:
Standard touchless

outcome:
Handoff verified

No human approval

Authority:
Bounded pre-authorized handoff

Automation previews may now reference the connected standard route, but saved
schedules/events remain configuration only.

Do NOT activate background triggers.

==================================================
21. DECISIONS PAGE
==================================================

A successful standard-touchless case should NOT create a human decision record
just to populate Decisions.

If touchless eligibility fails and human review becomes necessary, only create
a decision/proposal when the relevant workflow/policy genuinely supports one.

This absence of unnecessary approvals is part of the demo story.

==================================================
22. ALERTS
==================================================

Possible source-backed alert:

Standard change requires review

only if touchless policy fails.

A successful verified touchless handoff should generally become activity/history,
not a persistent alert demanding human action.

Do not generate noisy notifications for every agent step.

==================================================
23. SEARCH
==================================================

Global search should find:

- new standard-change case
- its workflow run
- handoff package
- Validation Operations intake where exposed

Preserve scoped access.

==================================================
24. STRATOS CONCIERGE CONTEXT
==================================================

Do not fully connect freeform Concierge yet.

Add contextual suggestions for the case:

- Why was this change eligible for touchless handling?
- What evidence was reused?
- What was handed to Validation Operations?
- What remains downstream?

If replies remain Preview, keep that explicit.

==================================================
25. HOST/API SURFACE
==================================================

Add only narrow typed application interfaces necessary for:

- read/create standard-change case fixture
- run requirement-change workflow with standard route
- read touchless eligibility
- read handoff package
- create permitted Validation Operations intake
- read/verify intake

Do NOT expose:

- generic Validation Lab write
- arbitrary job scheduling
- approval bypass endpoint
- generic tool invocation
- direct browser MCP access
- arbitrary procedure override

==================================================
26. EVALS / RELIABILITY
==================================================

Extend Phase 07 with new deterministic cases for the standard route.

At minimum:

1. Exact approved procedure/configuration → touchless eligible.

2. Applicable existing evidence recognized.

3. Required downstream work not mistaken for validation pass.

4. No unnecessary human approval.

5. Correct bounded handoff executes.

6. Handoff readback verifies.

7. Duplicate invocation does not duplicate handoff.

8. Wrong software version → touchless blocked.

9. Wrong hardware revision → blocked.

10. Missing procedure → blocked.

11. Conflicting evidence → blocked/escalated.

12. Non-standard parameters → blocked.

13. Customer acceptance never auto-granted.

14. Lab authorization never auto-granted.

15. Agent cannot change criteria to make case eligible.

16. Unknown source/evidence → no fabricated eligibility.

17. Existing CR-017 human-review behavior unchanged.

Preserve existing Phase 07 cases and hard gates.

==================================================
27. AUTOMATED TESTS
==================================================

Run:

- source/backend tests
- coordinator tests
- new standard-change tests
- Phase 06 governance regressions
- Phase 07 offline eval suite including new cases
- frontend/component tests
- Playwright E2E
- type check
- production build

No paid model calls in automated tests.

Use isolated fixtures.

Verify no mutation to the working CR-017 demo state.

==================================================
28. BROWSER E2E
==================================================

Test:

1. Open Overview.

2. Open standard-change case.

3. Start connected investigation as Program Operator.

4. Agent specialists analyze.

5. Touchless policy returns eligible.

6. No engineering approval step appears.

7. Handoff package appears.

8. Agent performs bounded Validation Operations handoff.

9. Readback verifies intake.

10. Case shows Handed to Validation Operations.

11. Lab authorization remains pending.

12. Physical validation remains pending.

13. Customer acceptance remains pending.

14. Repeat invocation does not duplicate intake.

15. Run an ineligible variant → zero handoff write and review/escalation shown.

==================================================
29. OPTIONAL LIVE CHECK
==================================================

Provide exact instructions/command for one manual connected live-model run of
the successful standard case.

Do not run automatically.

We want eventually to verify that the actual model correctly:

- interprets the standard request;
- uses applicable evidence;
- does not invent a gap;
- does not request unnecessary approval;
- respects touchless host policy.

==================================================
30. DEMO STORY DOCUMENTATION
==================================================

Update Phase 08 documentation with the final Use Case 1 story:

1A Standard Change / Touchless
- customer requests approved-scope validation update
- agents interpret and verify applicability
- existing policy authorizes bounded preparation/handoff
- agents assemble package
- Validation Operations receives it
- handoff verified
- downstream lab authority retained by humans

1B CR-017 Material Change
- unsupported material request
- agents investigate
- human engineering approval
- governed execution
- physical validation
- engineering evidence review

Make the contrast explicit.

==================================================
31. FINAL REPORT
==================================================

Report:

1. Exact scenario implemented
2. Agent/runtime components reused
3. Touchless eligibility policy
4. Handoff package contract
5. Exact new write boundary
6. Downstream team/ownership
7. UI changes
8. Registry/workflow changes
9. Eval cases added
10. Tests/results
11. Connected/simulated/preview matrix
12. Manual live demo command/path
13. Paid models not automatically run
14. Known limitations
15. Exact next Phase 08.4B step

==================================================
32. STOPPING POINT
==================================================

Stop after 08.4A.

Do NOT continue into:

- 08.4B Yield / Quality Exception Recovery
- 08.4C Delivery Readiness
- fully connected Stratos Concierge
- active background scheduler/event listeners
- Operations implementation
- Phase 09 polish
- Git cleanup/push

08.4A is complete when a real connected standard-change case can demonstrate:

customer request
→ multi-agent investigation
→ deterministic approved-procedure applicability check
→ touchless eligibility
→ execution-ready package
→ pre-authorized Validation Operations handoff
→ independent handoff verification
→ no unnecessary human approval
→ downstream lab/testing/customer acceptance still pending