Continue working in the existing Stratos Silicon repository and current
Phase 08 thread.

Implement Phase 08.4C:
CONNECTED DELIVERY READINESS / COMMITMENT PLANNING.

This is Use Case 3 of the final demo.

We are implementing it as a REAL connected workflow, not a simulation.

Reuse the existing:
- control-plane shell and navigation
- workflow registry
- shared invocation service
- coordinator/specialists
- case/run/activity persistence
- source adapters
- Phase 06 proposal/decision/execution governance
- Phase 07 eval/reliability framework
- Phase 08 workflow/automation/search/alerts/decision UI
- connected CR-017, CR-019 and QE-004 source-of-truth patterns

Do not redesign the app.
Do not create a parallel runtime.
Do not fully connect Stratos Concierge yet.
Do not activate background schedulers/event listeners.
Do not expand source-system authority beyond the narrowly approved actions
described below.

Git remains relaxed:
- no branch/commit/push work
- preserve unrelated local work
- avoid destructive Git operations

==================================================
1. OBJECTIVE
==================================================

Implement the real connected Delivery Readiness / Commitment Planning workflow.

Business question:

"Can Stratos responsibly commit the requested quantity of Helios accelerators
by the requested customer date?"

The workflow must reconcile:

- customer demand
- required configuration
- technical validation/readiness
- quality disposition
- released inventory
- held material
- existing allocations
- future supply where supported
- milestone timing
- shipping/arrival timing where modeled

Agents may investigate, calculate, compare options and prepare a commitment
proposal.

Humans retain authority over:
- customer-facing quantity/date commitments
- consequential inventory reallocation
- commercial commitment changes

The system must distinguish:

physical inventory
≠ released inventory
≠ eligible supply
≠ customer-ready supply
≠ committed supply
≠ delivered supply

Successful end state:

"Evidence-backed delivery options prepared; accountable human commitment
decision captured; permitted downstream update executed and independently
verified."

==================================================
2. SOURCE-OF-TRUTH PRINCIPLE
==================================================

The connected delivery-readiness case must exist coherently across the relevant
mock enterprise systems.

The control plane is not the operational source of truth.

Use authoritative records in:

COMMERCIAL ERP
Authoritative for:
- customer order
- requested quantity
- requested delivery/arrival date
- customer/program
- existing allocation/commitment state
- existing commercial promise if modeled
- ship-to / destination if modeled

MANUFACTURING PORTAL
Authoritative for:
- physical inventory
- lot status
- quality hold/release state
- eligible/released material
- lot/configuration provenance

ENGINEERING HUB
Authoritative for:
- approved hardware configuration
- software/firmware baseline
- engineering requirement/configuration compatibility

VALIDATION LAB
Authoritative for:
- applicable validation evidence
- engineering review state where exposed
- acceptance-readiness evidence
- open validation blockers

PROGRAM PLANNER
Authoritative for:
- delivery/customer milestone
- dependencies
- forecast timing
- readiness tasks
- shipment/release milestone context where modeled

Maintain stable cross-system IDs.

The control plane may store orchestration metadata only:
case/run/activity/proposal/decision/action/verification references.

Do not duplicate a full customer order or inventory ledger into the control plane.

==================================================
3. CREATE A DISTINCT DELIVERY READINESS CASE
==================================================

Create a stable synthetic case separate from CR-017, CR-019 and QE-004.

Suggested ID:
DR-009

Use repository conventions if a better existing identifier pattern exists.

Recommended connected base scenario:

Program:
Helios Atlas Inference / PRG-A17

Customer:
Helios AI

Requested quantity:
800 units

Physical inventory:
1,000 units total

Non-overlapping inventory groups:

A. Released + correct configuration + unallocated:
600

B. Quality-held:
250

C. Released + correct configuration but already allocated to another compatible
Helios release:
150

Total physical:
1,000

Immediate eligible/unallocated supply:
600

Current quantity gap against requested 800:
200

Do not double-count inventory groups.

Use actual source fixtures if equivalent records already exist.

==================================================
4. KEEP TECHNICAL READINESS SEPARATE FROM SUPPLY
==================================================

The workflow must not assume that supply eligibility proves customer readiness.

Model/read distinct dimensions:

SUPPLY ELIGIBILITY
- released
- correct part/configuration
- unallocated or appropriately available
- not quality-held

TECHNICAL READINESS
- applicable validation evidence
- correct configuration/software
- engineering review state
- no unresolved acceptance blocker

COMMERCIAL READINESS
- authorized quantity/date commitment
- permitted allocation
- customer-facing promise state

A unit may be supply-eligible but not technically cleared.

The base fixture may choose either:

A. technical readiness complete, to emphasize quantity planning

or

B. technical readiness pending due to CR-017, to demonstrate cross-workflow
dependency

Preferred implementation:
support both variants.

Primary demo path should be easy to understand:
technical/configuration requirements complete, while quantity is short.

A second variant should demonstrate:
600 supply-eligible but technical acceptance still pending because CR-017 is open.

==================================================
5. CONNECTED WORKFLOW IDENTITY
==================================================

Make:

delivery_readiness

a CONNECTED workflow in the existing registry.

Reuse:
- Program Coordinator
- Program/Commercial specialist
- Manufacturing/Supply specialist
- Validation & Evidence specialist
- Change/Engineering specialist only where configuration compatibility requires it

Do not create a separate "Delivery Agent" if existing specialists cover the work.

==================================================
6. INPUT CONTRACT
==================================================

The connected workflow input should include:

- case ID
- program
- customer
- order ID
- requested quantity
- requested customer date
- required product/configuration
- destination / shipping context if modeled
- trusted actor
- relevant milestone/order references

Do not let the model invent missing quantity/date/configuration fields.

If key commercial input is missing:
- mark readiness incomplete
- request clarification / escalate
- do not fabricate a commitment

==================================================
7. RESOLVE THE EXACT CUSTOMER COMMITMENT
==================================================

Program/Commercial specialist should establish:

- exact order line
- quantity requested
- required date
- whether date means ship date or arrival date
- destination if relevant
- required configuration
- current commitment state
- existing customer allocation

Do not silently treat:
material available date
as
customer arrival date.

Use explicit date semantics.

==================================================
8. TECHNICAL READINESS CHECK
==================================================

Validation/Engineering specialists should determine:

- required configuration
- applicable evidence
- engineering review state
- open validation gaps
- unresolved exceptions/waivers
- whether the customer requirement is technically ready

Output a structured result such as:

technical_readiness =
READY / BLOCKED / CONDITIONAL / UNKNOWN

with reasons and evidence.

Do not let the model declare READY without source-backed evidence.

==================================================
9. ELIGIBLE SUPPLY CALCULATION
==================================================

Use deterministic code/calculators.

For the base scenario:

physical_total = 1000

held = 250

allocated_elsewhere = 150

released_unallocated_eligible = 600

requested = 800

immediate_gap = 200

Do not use freeform model arithmetic.

Use source records to derive categories.

The calculation must avoid:
- double-counting
- counting held material
- counting material allocated elsewhere
- counting wrong configuration
- counting unverified future receipts as current supply

==================================================
10. INVENTORY BREAKDOWN
==================================================

Represent inventory with explicit categories.

At minimum:
- physical total
- held
- allocated
- released/unallocated
- configuration mismatch if any
- eligible supply

If future receipts exist:
show separately as:
future expected supply

not as current eligible inventory.

==================================================
11. FUTURE SUPPLY
==================================================

If source data supports future lots/receipts:

capture:
- quantity
- expected date
- confidence/state
- release prerequisites
- configuration
- whether quality/validation is complete

Do not present a planned future receipt as guaranteed.

Use terms such as:
Expected
Conditional
Unconfirmed

based on actual source state.

==================================================
12. DATE / DELIVERY CALCULATION
==================================================

Use deterministic scheduling/date logic.

Where the source model supports it, account for:
- material readiness
- preparation
- shipment/loading
- transit
- arrival date

Do not fabricate transit times.

If exact logistics timing is not modeled:
state that the commitment is quantity-ready but arrival date still requires
logistics confirmation.

Do not invent a customer arrival date merely to complete the demo.

==================================================
13. PRIMARY DEMO STORY
==================================================

Primary DR-009 story:

1. Helios requests 800 units.
2. ERP shows 1,000 physical units across relevant inventory.
3. Agents reconcile Manufacturing state.
4. 250 are quality-held.
5. 150 are already allocated to another Helios release.
6. Only 600 are currently eligible/unallocated.
7. Technical readiness is checked separately.
8. Agents conclude:
   full 800-unit commitment is not currently supportable.
9. Agents prepare evidence-backed options.
10. Human Program/Commercial owner reviews the commitment proposal.
11. Approved permitted downstream updates execute.
12. ERP/Planner readback verifies the authorized commitment.
13. Customer commitment changes only after human approval.

==================================================
14. DELIVERY OPTIONS
==================================================

Produce structured options based on source facts.

Recommended base options:

OPTION A — PARTIAL DELIVERY
Commit 600 units on supported timing.
Remaining 200 pending future eligible supply/customer agreement.

OPTION B — ALLOCATION REVIEW
Evaluate whether 150 currently allocated units can be moved.
Must show:
- impacted existing obligation
- resulting remaining 50-unit gap
- required allocation authority

OPTION C — WAIT FOR FUTURE ELIGIBLE SUPPLY
Use a future receipt only if a real source record exists.
Show date/confidence/prerequisites.

Do not fabricate Option C if no future supply is modeled.

A valid outcome may be:

"No currently supportable full-delivery plan."

The agent must be allowed to say that.

==================================================
15. HUMAN DECISION BOUNDARY
==================================================

Human approval is required before changing:

- customer-facing quantity
- customer-facing date
- inventory allocation
- commercial commitment

Agents may:
- calculate
- compare
- recommend
- draft
- prepare internal proposal

Agents may NOT:
- commit 600 units automatically
- promise future 200 units
- reallocate the 150 units
- update customer promise without approval

==================================================
16. DECISION ROLES
==================================================

Use existing trusted demo identity architecture.

Potential roles:

PROGRAM / COMMERCIAL OWNER
- approve customer-facing commitment proposal

SUPPLY / PROGRAM OWNER
- approve consequential allocation changes

If repository role names differ, reuse existing trusted roles.

Do not invent role strings only in the client.

Program Operator may initiate/reassess.
Program Operator is not automatically authorized to change customer commitments.

==================================================
17. VERSIONED COMMITMENT PROPOSAL
==================================================

Reuse Phase 06 proposal/decision architecture.

Proposal should bind:

- DR-009
- exact order
- requested quantity/date
- technical-readiness evidence versions
- supply/inventory snapshot versions
- selected option
- quantity to commit
- proposed date
- allocation implications
- Planner changes
- ERP changes
- assumptions
- proposal version/digest
- required authority

Material change in:
inventory
technical readiness
allocation
date
or selected option

must invalidate/revise the proposal.

Old approval must not silently authorize new facts.

==================================================
18. PERMITTED WRITE BOUNDARY
==================================================

Implement only the exact, narrow connected writes required for an approved
delivery commitment.

Inspect existing ERP/Planner APIs first.

Preferred permitted actions after human approval:

COMMERCIAL ERP
- update/create the bounded customer commitment/allocation record for the exact
approved quantity/date if an appropriate contract already exists

PROGRAM PLANNER
- update the corresponding delivery/readiness milestone/task or commitment link

Do not add generic ERP CRUD.

Do NOT automatically:
- release held material
- override quality disposition
- change manufacturing plan
- change validation status
- reallocate inventory unless a separately approved allocation action is included
and bound to the exact proposal

If ERP does not currently support a safe bounded commitment update, add the
smallest typed contract needed.

==================================================
19. ALLOCATION CHANGE
==================================================

If Option B is implemented as an executable alternate path:

Treat reallocation as a separate consequential action.

The proposal must identify:
- inventory allocation being changed
- current owner/release
- affected quantity
- downstream obligation affected
- remaining shortfall
- required approver

Do not hide reallocation inside a generic "approve delivery" action.

It is acceptable for the primary demo to keep Option B analysis-only while
Option A is executable.

Prefer simplicity and governance over excessive write scope.

==================================================
20. EXECUTION
==================================================

After exact human approval:

use existing ExecutionService patterns.

Sequence should be explicit.

Example:
1. validate proposal/current source versions
2. perform approved ERP commitment update
3. independent ERP readback
4. perform approved Planner update
5. independent Planner readback
6. persist verification
7. update case state

Use existing transaction/idempotency principles.

Do not rely on browser-side direct writes.

==================================================
21. PARTIAL FAILURE
==================================================

Handle:

ERP write succeeds
Planner write fails

without:
- duplicating ERP commitment
- pretending whole action rolled back
- marking verified success

Show:
ERP update verified
Planner update failed
Partial completion — reconciliation required

Allow safe retry of only incomplete permitted steps.

==================================================
22. READBACK VERIFICATION
==================================================

Independently verify:

ERP
- order
- quantity
- committed date
- allocation state if changed
- customer/program linkage
- proposal/reference

Planner
- milestone/task
- delivery/readiness state
- quantity/date where modeled
- linkage to DR-009/proposal

Separate:
ACTION_SUCCEEDED
from
VERIFICATION_SUCCEEDED

==================================================
23. CURRENT BUSINESS STATE
==================================================

Use truthful states.

Before decision:
Requested:
800

Currently supportable:
600

Gap:
200

Commitment:
Decision required

After approved partial commitment:
Committed:
600

Remaining:
200 uncommitted / pending supply plan

Customer agreement:
pending if the workflow only records an internal commitment proposal

If the ERP record represents an actual authorized customer commitment,
label accordingly based on the source model.

Do not automatically claim:
customer accepted split delivery

unless there is a separate customer-response source record.

==================================================
24. CUSTOMER ACCEPTANCE VS COMMERCIAL COMMITMENT
==================================================

Keep these separate.

Technical customer acceptance of the accelerator/workload:
one concept

Commercial delivery commitment:
another concept

Do not reuse:
customer_accepted

to mean:
customer delivery date was committed.

Use explicit labels.

==================================================
25. CROSS-WORKFLOW DEPENDENCY
==================================================

Integrate CR-017 / engineering readiness where appropriate.

Add a deterministic variant:

DR-009 supply:
600 eligible

but CR-017 technical evidence:
still pending

Expected:
supply_eligible = 600
customer_ready = false/conditional
commitment proposal blocked or conditional according to policy

Another variant:
CR-017 engineering review complete
→ delivery readiness can proceed

Do not mutate CR-017 merely by running DR-009.

Read its authoritative current state.

==================================================
26. QE-004 DEPENDENCY
==================================================

Use QE-004 held-material state as a real dependency where practical.

The 250 held units should come from the quality/manufacturing state established
by QE-004 or a coherent shared source record.

Do not maintain:
QE-004 says lot held
while DR-009 independently says same lot released.

Use shared authoritative Manufacturing records.

If QE-004 later changes disposition in a future scenario, DR-009 should reflect
that on reassessment.

==================================================
27. CASE UI
==================================================

Add DR-009 as a connected case under Helios.

Case workbench should include:

REQUEST
800 units / requested timing

TECHNICAL READINESS
configuration/evidence/review state

SUPPLY
visual quantity breakdown

ALLOCATIONS
what is already committed elsewhere

DELIVERY TIMING
supported timing / conditional timing

OPTIONS
structured commitment comparison

DECISION
human Program/Commercial review

EXECUTION
ERP / Planner updates

VERIFICATION
readback state

CURRENT COMMITMENT
what is actually committed vs still pending

Use current design system.
Do not spend significant time on cosmetic redesign.

==================================================
28. VISUAL QUANTITY BREAKDOWN
==================================================

Use an easy-to-understand visual.

For example:

1,000 physical
-250 held
-150 allocated
=600 eligible

Requested:
800

Gap:
200

Do not use a circular progress score that implies generic readiness.

If technical readiness is blocked:
show that as a separate readiness gate, not baked into inventory arithmetic.

==================================================
29. READINESS GATES
==================================================

A compact readiness panel may show:

Configuration
Ready / blocked

Validation evidence
Ready / blocked / conditional

Quality
Ready / held

Supply
600 / 800

Allocation
Gap

Timing
Supported / conditional

Commercial approval
Pending / approved

Each gate must derive from actual records.

Do not create a mysterious overall AI score.

==================================================
30. WORKFLOW CATALOG
==================================================

Update 08.3:

Delivery Readiness / Commitment Planning
Mode:
Connected

Initiation:
Manual

Future schedule:
configuration preview only

Authority:
Analysis + proposal
Human approval for commitment/allocation

Run history should show DR-009 runs.

==================================================
31. AUTOMATION PREVIEW
==================================================

Morning Delivery Readiness may now reference the connected workflow.

Its schedule remains NOT ACTIVE.

Show:

Connected workflow
Schedule configuration saved
Background scheduler not enabled

Do not run automatically.

==================================================
32. OVERVIEW
==================================================

Surface DR-009 appropriately.

Example:
DR-009 · Delivery readiness
600 / 800 currently supportable
Commitment decision required

If technical readiness blocks the case:
show the more important blocker instead.

Avoid duplicating the same information across multiple cards.

==================================================
33. DECISIONS
==================================================

Add real commitment proposal(s).

Decision view should show:

Customer/order
Requested quantity/date
Technical readiness
Eligible supply
Existing allocations
Options
Recommendation
Exact approved commitment
Affected source systems
What requires separate approval

Use business wording.

Not:
Approve AI

==================================================
34. ALERTS
==================================================

Potential real alerts:

Delivery commitment decision required

Technical readiness blocks delivery proposal

ERP/Planner verification mismatch

Do not fabricate:
customer rejected
shipment late
unless source data exists.

==================================================
35. SEARCH
==================================================

Global search should find:

DR-009
order ID
customer
delivery proposal
related run
decision
inventory/lot where in scope

Preserve authorization and scope.

==================================================
36. STRATOS CONCIERGE CONTEXT
==================================================

Do not fully connect freeform chat yet.

Add suggestions:

- Can we commit 800 units?
- Why are only 600 units available?
- What is blocking the remaining 200?
- Compare the delivery options.
- Is technical readiness complete?

Keep Preview label until 08.5.

==================================================
37. SOURCE-WRITE BOUNDARY
==================================================

Document all connected writes.

Allowed only after exact human approval:
- bounded ERP commitment update
- bounded Planner delivery/readiness update
- separately authorized allocation update if implemented

Prohibited:
- quality release
- inventory fabrication
- manufacturing changes
- validation changes
- arbitrary commercial record edits
- customer communication unless separately implemented later

==================================================
38. VARIANT FIXTURES
==================================================

Add deterministic variants:

A. Base 600/800 gap.

B. Technical evidence incomplete despite 600 supply eligible.

C. Future receipt exists but date is conditional.

D. Wrong configuration inventory exists physically but is ineligible.

E. Held material becomes released after authoritative quality change.

F. Allocation replan would damage another commitment.

G. Requested 600 units → fully supportable.

H. ERP commitment source changes during proposal → proposal stale.

I. Planner update partial failure.

J. Missing requested date.

==================================================
39. EVALS
==================================================

Extend Phase 07 eval framework.

At minimum evaluate:

1. 1000 physical ≠ 1000 deliverable

2. held 250 excluded

3. allocated 150 excluded

4. eligible = 600

5. requested = 800

6. gap = 200

7. no double counting

8. technical readiness separate from supply

9. future receipt not guaranteed

10. unsupported full-delivery date not invented

11. commitment requires human approval

12. allocation change requires proper authority

13. stale proposal rejected

14. approved quantity/date matches exact proposal

15. verification mismatch not reported as success

16. customer acceptance not conflated with commercial commitment

17. QE-004 hold state respected

18. CR-017 state respected

Critical failures:
- false deliverable quantity
- held inventory counted as available
- autonomous customer commitment
- unauthorized reallocation
- fabricated delivery date
- false technical readiness
- stale proposal execution

==================================================
40. AUTOMATED TESTING
==================================================

Run:
- source tests
- coordinator tests
- MCP tests
- Phase 06 governance regressions
- Phase 07 evals + new delivery cases
- CR-017 regressions
- CR-019 regressions
- QE-004 regressions
- frontend/component
- Playwright
- typecheck/build

No paid models.

Use isolated fixtures.

Preserve current working demo states.

==================================================
41. BROWSER E2E
==================================================

Primary path:

1. Open DR-009.
2. Run connected analysis.
3. Resolve exact 800-unit request.
4. Technical readiness checked.
5. Inventory reconciled.
6. 600 eligible / 800 requested / 200 gap shown.
7. Options produced.
8. Commitment proposal created.
9. Wrong role cannot approve.
10. Correct Program/Commercial owner approves.
11. Exact ERP commitment executes.
12. Planner update executes.
13. Independent readback verifies.
14. Case shows exact current commitment.
15. Remaining 200 stays uncommitted unless separately supported.
16. QE held material remains excluded.
17. Customer acceptance is not falsely changed.

Also test:
- CR-017 technical blocker variant
- future receipt conditional variant
- partial failure
- stale proposal
- wrong-configuration inventory

==================================================
42. OPTIONAL LIVE CHECK
==================================================

Provide exact manual instructions for one live DR-009 model run.

Do not automatically run paid models.

Later live verification should test:
- evidence grounding
- correct source usage
- calculator usage
- no invented quantity/date
- appropriate human decision boundary

==================================================
43. DOCUMENTATION
==================================================

Update Phase 08 docs with:

- DR-009 source-of-truth mapping
- IDs/cross-system references
- readiness architecture
- supply calculation
- date semantics
- proposal/approval
- ERP/Planner execution
- QE/CR-017 dependencies
- write boundary
- eval coverage
- manual demo path
- limitations

==================================================
44. FINAL REPORT
==================================================

Report:

1. Source records created/reused
2. Cross-system IDs
3. Connected workflow implementation
4. Agent/specialist reuse
5. Technical-readiness policy
6. Eligible-supply calculator
7. Delivery options
8. Decision authority
9. Exact writes
10. Verification
11. UI integration
12. Eval cases
13. Tests/results
14. Connected/simulated/preview matrix
15. Manual live path
16. No paid models automatically run
17. Known limitations
18. Exact next Phase 08.5 step

==================================================
45. STOPPING POINT
==================================================

Stop after Phase 08.4C.

Do NOT continue into:
- fully connected Concierge
- active background scheduler
- Operations implementation
- Phase 09 polish
- Git cleanup/push

08.4C is complete when DR-009 can demonstrate:

customer request
→ technical readiness assessment
→ inventory/quality/allocation reconciliation
→ deterministic supportable quantity/date
→ commitment options
→ exact human commitment decision
→ governed ERP/Planner execution
→ independent readback
→ truthful remaining gap
→ no unauthorized allocation or customer promise