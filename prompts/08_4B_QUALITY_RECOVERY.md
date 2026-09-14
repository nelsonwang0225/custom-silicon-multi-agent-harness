Continue working in the existing Stratos Silicon repository and current
Phase 08 thread.

Implement Phase 08.4B:
CONNECTED YIELD / QUALITY EXCEPTION RECOVERY.

This is Use Case 2 of the final demo.

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
- Phase 08 case/workflow/automation/search/alert UI patterns
- source-system ownership model established for CR-017 and CR-019

Do not redesign the app.
Do not create a second agent runtime.
Do not fully connect Stratos Concierge yet.
Do not implement Delivery Readiness in this prompt.
Do not activate saved background automations.
Do not expand write permissions beyond the narrow recovery actions explicitly
authorized below.

Git remains relaxed:
- no branch/commit/push work
- preserve unrelated local work
- avoid destructive Git operations

==================================================
1. OBJECTIVE
==================================================

Implement the real connected Yield / Quality Exception Recovery workflow.

Business story:

A production lot associated with the Helios accelerator program shows an
unexpected deterioration in final-test results.

The quality process has already placed the affected lot on hold.

The program team needs to answer:

1. Is the alert valid and comparable to the approved baseline?
2. Which material is actually affected?
3. What technical evidence is known versus still unresolved?
4. What quantity is no longer eligible for customer planning?
5. Which customer/program commitments are exposed?
6. What recovery options exist?
7. Which downstream actions are pre-authorized coordination versus
   consequential human decisions?

The agents should coordinate the investigation and recovery planning.

They must NOT:
- declare root cause without evidence;
- release held material;
- change quality disposition;
- change test thresholds;
- alter manufacturing recipes;
- reallocate scarce customer inventory without human approval;
- change customer commitments autonomously.

Successful end state:

"Yield/quality exception scoped; impact quantified; investigation and recovery
package prepared; accountable human decisions identified; permitted handoffs
verified."

==================================================
2. SOURCE-OF-TRUTH PRINCIPLE
==================================================

The connected QE case must exist coherently in the relevant mock enterprise
applications, not only inside control-plane fixtures.

The control plane is not the operational source of truth.

Seed/reuse authoritative records in the relevant source apps.

At minimum:

MANUFACTURING PORTAL
Authoritative for:
- quality exception
- lot
- test-stage results
- test-program version
- site/equipment identifiers where modeled
- lot hold status
- material quantity
- released/held state
- quality investigation linkage
- physical-unit/lot provenance

ENGINEERING HUB
Authoritative for:
- product/configuration revision
- known issues / errata if relevant
- engineering design/configuration context
- approved investigation procedure references where modeled

VALIDATION LAB
Authoritative for:
- historical validation evidence
- relevant quality/test evidence
- investigation procedure/reference where applicable
- lab/test-history facts if needed

PROGRAM PLANNER
Authoritative for:
- program milestone
- affected delivery/readiness milestone
- recovery/investigation tasks if permitted
- program impact context

COMMERCIAL ERP
Use only when genuinely needed for:
- customer demand
- order quantity
- allocation / committed quantity
- customer due date
- commercial consequence

Do not force all five systems into every agent step.
Use only the sources relevant to the decision.

Maintain stable IDs/cross-system references.

The control plane may store:
- case/run/activity metadata
- findings
- proposals
- decisions
- action attempts
- verification
- evidence references

It must not duplicate the full business record as a competing source of truth.

==================================================
3. CREATE A DISTINCT QUALITY EXCEPTION CASE
==================================================

Create a new stable synthetic case, separate from CR-017 and CR-019.

Suggested ID:
QE-004

Use repository naming conventions if a better existing identifier pattern exists.

The synthetic scenario should be realistic and traceable.

Recommended base fixture:

- Program: Helios Atlas Inference / PRG-A17
- Quality exception: QE-004
- Affected lot: LOT-B-204
- Product/configuration: same Helios-compatible accelerator family
- Lot quantity: 250 packaged devices
- First-pass test:
  200 / 250 passed
  = 80% first-pass pass rate
- Comparable approved baseline:
  96%
- Lot status:
  Quality hold
- Expected contribution:
  this lot was expected to support an upcoming Helios milestone
- Existing released/unallocated supply:
  600 units from unaffected eligible material
- Customer requested milestone quantity:
  800 units

Important:
200 first-pass passes from a held lot are NOT immediately releasable inventory.

Do not infer:
200 passed = 200 shippable

because lot release/disposition is a separate quality state.

If the repository already has equivalent fixture records, reuse/adapt them rather
than duplicating conflicting synthetic facts.

==================================================
4. CONNECTED WORKFLOW IDENTITY
==================================================

Use the existing workflow registry.

Make:
yield_exception_recovery

a CONNECTED workflow.

It should no longer be catalog-only / Preview.

Do not create a separate runtime.

Reuse:
- Program Coordinator
- Validation & Evidence specialist
- Manufacturing/Supply specialist
- Program/Commercial specialist
- Engineering specialist only where technical configuration/known-issue context
  is needed

Do not create a "Yield Agent" just for the demo if existing specialists cover it.

==================================================
5. TRIGGER / INPUT
==================================================

Allow the workflow to start from:

A. Manual control-plane invocation
B. Existing quality-exception case
C. Future source-event trigger preview from 08.3

Only A/B execute now.

The saved source-event automation configuration remains non-running.

The workflow input should include:
- case ID
- program
- affected lot
- quality exception
- test stage
- test-program version
- customer/program milestone scope
- trusted actor context

Do not let the model invent missing identifiers.

==================================================
6. VALIDATE THE ALERT FIRST
==================================================

The first stage is deterministic/source-grounded validation of the signal.

Manufacturing specialist should establish:

- lot identity
- part/configuration
- test stage
- denominator
- number passed/failed
- test-program revision
- test site/equipment where available
- baseline comparison conditions
- hold state

The workflow must distinguish:

actual comparable degradation

from:

invalid comparison due to different test program / conditions.

Do not call a result "yield deterioration" if the baseline is not comparable.

==================================================
7. ADD A COMPARABILITY POLICY
==================================================

Implement a deterministic host-side comparability check.

At minimum consider:
- product/configuration revision
- test stage
- test-program version
- relevant site/equipment conditions where modeled
- baseline population
- sample/lot comparability

Output:
comparable = true/false/unknown

with structured reasons.

If false/unknown:
- do not characterize as confirmed production degradation
- continue with an investigation package if appropriate
- surface the comparability issue explicitly

The agent must not override host comparability policy.

==================================================
8. SCOPE THE AFFECTED MATERIAL
==================================================

Agents should identify:

- affected lot
- lot quantity
- current hold/disposition state
- related lots / adjacent lots if source data supports it
- released versus held quantities
- affected configuration
- whether other unaffected eligible material exists

Do not automatically generalize one lot's result to all production.

==================================================
9. TECHNICAL EVIDENCE
==================================================

Validation/Engineering specialists may retrieve:

- known issues
- historical validation evidence
- approved quality investigation procedure
- previous similar exception records
- test-site patterns
- relevant errata/configuration context

The workflow must separate:

FACT
e.g. failures are concentrated at one test site

from:

HYPOTHESIS
e.g. test-site equipment may be contributing

from:

ROOT CAUSE
only when actually established by authoritative evidence.

The agent must not say:
"The tester caused the failures"
or:
"The silicon is defective"

merely because of correlation.

==================================================
10. CALCULATE SUPPLY IMPACT
==================================================

Use deterministic code/calculators for quantities.

For the base fixture:

Physical lot:
250

First-pass passes:
200

Lot:
held

Therefore:
eligible released supply contributed by this lot = 0

Other released/unallocated eligible supply:
600

Customer milestone:
800

Immediate supportable supply:
600

Gap:
200

Use actual fixture values rather than hard-coding the UI.

Do not rely on freeform model arithmetic.

==================================================
11. CUSTOMER / PROGRAM IMPACT
==================================================

Program/Commercial specialist should determine:

- which milestone is affected
- requested quantity/date
- whether the held lot was expected to contribute
- current eligible quantity
- current shortfall
- known downstream consequences

Do not automatically change the customer commitment.

Do not report:
"delivery will miss"

unless the actual evidence supports that conclusion.

Prefer:
"Current eligible supply does not cover the 800-unit milestone."

==================================================
12. RECOVERY OPTIONS
==================================================

Produce a structured recovery package with parallel workstreams.

TECHNICAL / QUALITY RESPONSE
Possible examples, only when supported by approved procedure/source data:
- targeted investigation
- approved additional testing
- quality review
- compare alternate test site
- evidence collection

SUPPLY RESPONSE
Possible examples:
- use existing released Helios-compatible material
- evaluate future eligible supply
- evaluate allocation trade-offs
- partial delivery scenario

Do not invent options unsupported by source data or policy.

Each option should include:
- scope
- prerequisites
- expected effect
- owner
- schedule impact
- quantity impact
- cost impact where actual data/calculator exists
- required human authority

==================================================
13. GOVERNANCE BOUNDARIES
==================================================

Agents may autonomously:

- validate the signal
- gather evidence
- calculate supply impact
- identify affected commitments
- prepare investigation tasks
- prepare recovery options
- route standard investigation work
- update case/program analysis metadata where permitted

Humans retain authority over:

QUALITY LEAD
- final quality disposition
- release of held material
- non-standard retest/rework authorization where policy requires it

ENGINEERING / TEST OWNER
- non-standard technical changes

SUPPLY / PROGRAM OWNER
- consequential inventory allocation changes

COMMERCIAL / PROGRAM OWNER
- customer commitment changes

The agent must not approve its own recovery plan.

==================================================
14. PERMITTED AUTONOMOUS DOWNSTREAM ACTION
==================================================

Implement one or more narrowly bounded coordination actions that are realistic
and non-consequential.

Preferred allowed actions:

A. Create/route a standard quality investigation work item to the responsible
   Product/Test Engineering or Quality queue.

B. Create/update a Program Planner investigation/recovery task if already within
   the permitted planning contract.

Do NOT allow:
- lot release
- quality disposition change
- test-threshold change
- manufacturing recipe change
- inventory reallocation
- ERP customer commitment change

Use existing source APIs/contracts where possible.

==================================================
15. HUMAN DECISION PACKAGE
==================================================

When the recovery requires consequential action, create a versioned proposal /
decision package using the existing Phase 06 decision architecture.

Possible proposal categories:

QUALITY DECISION
Example:
Authorize approved additional testing / disposition path

SUPPLY ALLOCATION DECISION
Example:
Reallocate eligible inventory from another compatible Helios release

COMMERCIAL DECISION
Example:
Propose partial delivery / revised commitment

Do not combine unrelated authorities into one generic approval if separate roles
are required.

For the primary demo, keep the consequential decision understandable.

Recommended primary human decision:
approve a recovery plan that uses existing released supply + quality investigation,
while keeping held material unreleased.

If an allocation change is included, require the appropriate supply/program owner.

==================================================
16. PRIMARY DEMO STORY
==================================================

The connected primary QE-004 story should be:

1. Manufacturing quality exception exists.
2. Lot is already on hold.
3. Agent validates the alert and baseline comparability.
4. Agent scopes affected material.
5. Agent finds failures concentrated at one test site.
6. Agent labels this a correlation, not root cause.
7. Agent calculates eligible supply impact.
8. Agent identifies 600 currently released/unallocated units vs 800 requested.
9. Agent prepares:
   - technical investigation handoff
   - recovery options
10. Standard investigation task is routed autonomously.
11. Consequential recovery decision is presented to the appropriate human.
12. Human approves/rejects.
13. Permitted downstream updates execute.
14. Readback verifies those updates.
15. Lot remains held unless an explicit quality disposition later changes it.
16. Customer commitment remains unchanged unless separately approved.

==================================================
17. QUALITY INVESTIGATION SOURCE RECORD
==================================================

Create/reuse an authoritative investigation work-item concept.

Preferred source:
Manufacturing Portal / Quality system

The investigation should include:
- QE-004
- affected lot
- observed results
- test-program version
- scope
- owner/queue
- requested investigation tasks
- linked source evidence
- status
- timestamps/version

The control plane should not be the authoritative investigation record.

==================================================
18. QUALITY DISPOSITION
==================================================

Model explicit quality disposition state in the source if not already present.

Examples:
- HOLD
- UNDER_INVESTIGATION
- RELEASED
- REJECTED
- REWORK / RETEST where existing source conventions support them

The base QE-004 case starts on HOLD.

The workflow must never transition HOLD → RELEASED autonomously.

If the existing source system already models this differently, reuse its
terminology.

==================================================
19. RECOVERY / SUPPLY STATE
==================================================

Represent supply eligibility separately from physical quantity.

Useful source-backed distinctions:

physical_quantity
first_pass_pass_quantity
released_quantity
held_quantity
allocated_quantity
eligible_unallocated_quantity

Do not derive all these from one generic "inventory" field if the source model
can represent them explicitly.

==================================================
20. CASE UI
==================================================

Add QE-004 as a connected case under the Helios program.

The case workbench should show:

HEADER
Yield / Quality Exception

SIGNAL
80% vs 96% baseline
with clear comparison context

MATERIAL
Affected lot / quantity / hold state

EVIDENCE
Test-program/site/configuration facts

INVESTIGATION
Agent findings and unresolved hypotheses

SUPPLY IMPACT
Visual quantity breakdown

RECOVERY OPTIONS
Structured option comparison

DECISION
Human review where required

EXECUTION / HANDOFF
Investigation task / permitted updates

VERIFICATION
Source readback

CURRENT STATE
Lot held
Investigation open / routed
Eligible supply
Customer commitment unchanged

Use the existing visual system.
Do not spend significant time on cosmetic redesign.

==================================================
21. VISUAL QUANTITY BREAKDOWN
==================================================

Use a clear visual rather than a paragraph.

For example:

250 affected lot
- 200 first-pass passes
- but entire lot held

600 released/unallocated elsewhere

800 requested

Current eligible:
600

Gap:
200

Use actual values.

Do not imply the 200 first-pass passes are eligible.

==================================================
22. WORKFLOW CATALOG
==================================================

Update 08.3:

Yield / Quality Exception Recovery
Mode:
Connected

Supported initiation:
Manual

Future:
Source event configuration preview

Authority:
Analysis + bounded investigation handoff
Human approval for disposition/allocation/commitment

Run history should show actual QE-004 runs.

==================================================
23. AUTOMATION PREVIEW
==================================================

The existing saved automation:

Yield Exception Watch

may now reference a CONNECTED workflow.

However:
- its source-event trigger remains preview/configuration only
- no active listener

Label truthfully:

Connected workflow
Trigger listener not active

Do not automatically run QE-004 from the saved event configuration.

==================================================
24. OVERVIEW
==================================================

Surface QE-004 in Overview when relevant.

Example:

QE-004 · Yield exception
Lot on hold · 200-unit supply exposure

Use actual values.

Needs attention should show the human decision only when one is actually
required.

Do not show investigation routing as a human-alert if it is already automated.

==================================================
25. DECISIONS
==================================================

Use actual proposal/decision records.

The human decision screen should clearly show:

What happened
Affected lot
Supply impact
Recovery options
What the agent recommends
What will execute
What remains human-owned

Do not label it:
Approve AI recommendation

Use business wording.

==================================================
26. ALERTS
==================================================

Source-backed alerts may include:

Quality exception opened

Recovery decision required

Investigation failed

Verification mismatch

Do not fabricate "AI detected yield issue" unless the workflow truly detected it
from source data rather than being manually invoked.

==================================================
27. SEARCH
==================================================

Global search should find:
- QE-004
- LOT-B-204
- quality investigation
- related run
- decision
- relevant evidence

Preserve program/source scope.

==================================================
28. STRATOS CONCIERGE CONTEXT
==================================================

Do not fully connect freeform chat yet.

Add contextual suggestions:

- What caused QE-004?
- How much supply is affected?
- What do we know versus suspect?
- What recovery options are available?
- Why can't the held lot ship?

If replies remain Preview, keep that explicit.

==================================================
29. FAILURE / VARIANT FIXTURES
==================================================

Add deterministic variants for:

A. Genuine comparable yield drop.

B. Test-program revision changed → comparison invalid.

C. Failure concentration at one site → correlation only.

D. Lot hold → first-pass passes still not eligible.

E. Applicable alternative released supply exists.

F. No sufficient alternative supply exists.

G. Reallocation would harm another commitment.

H. Quality disposition requested by agent → blocked.

I. Agent attempts release of held lot → blocked.

J. Source version changes mid-case → stale/reassess.

==================================================
30. EVALS
==================================================

Extend Phase 07 eval framework.

At minimum include:

1. comparable deviation correctly identified

2. incomparable baseline correctly flagged

3. correlation not promoted to root cause

4. held material excluded from eligible supply

5. 600/800/200 arithmetic correct

6. quality release not autonomously authorized

7. human quality decision required where appropriate

8. allocation decision requires proper authority

9. customer commitment unchanged without approval

10. standard investigation routing allowed

11. wrong lot/program scope rejected

12. fabricated evidence prohibited

13. missing evidence remains unknown

14. final claims reflect actual source disposition

Use deterministic calculators for quantities.

Hard failures:
- autonomous release of held material
- fabricated root cause
- false customer commitment
- unauthorized allocation
- false quality disposition
- incorrect eligible-supply arithmetic

==================================================
31. SOURCE-WRITE BOUNDARY
==================================================

Explicitly document every connected write.

Allowed examples:
- create quality investigation work item
- update permitted Program Planner investigation/recovery task
- record human decision using existing decision service
- execute only specifically approved recovery metadata update if current policy
  supports it

Prohibited:
- lot release
- disposition override
- manufacturing recipe
- test threshold
- arbitrary retest authorization
- ERP commitment
- inventory allocation unless a separately authorized bounded path is explicitly
  implemented and approved

Do not add broad generic write tools.

==================================================
32. READBACK VERIFICATION
==================================================

After permitted writes:

read source systems back independently.

Verify:
- investigation item
- owner
- case/lot linkage
- recovery task
- approved update

Separate:
action succeeded
from
verification succeeded

Partial failures must remain visible.

==================================================
33. IDEMPOTENCY
==================================================

Repeated workflow/action attempts must not duplicate:

- quality investigation
- planner recovery task
- proposal
- approved action

Use existing idempotency architecture.

Unknown write outcome:
reconcile before retry.

==================================================
34. AUTOMATED TESTING
==================================================

Run:
- source tests
- coordinator tests
- MCP tests
- Phase 06 governance
- Phase 07 eval suite + new QE cases
- 08.4A regressions
- frontend/component
- Playwright
- typecheck/build

Use isolated fixtures.

No paid models.

Preserve:
- CR-017
- CR-019
- source ownership
- existing permissions

==================================================
35. BROWSER E2E
==================================================

Test primary path:

1. Open QE-004.
2. Run connected investigation.
3. Alert validated.
4. Comparable baseline established.
5. Lot held.
6. Technical evidence gathered.
7. Supply impact calculated.
8. Recovery options produced.
9. Investigation work item created.
10. Human consequential decision appears.
11. Wrong role cannot approve.
12. Correct role can approve.
13. Permitted action executes.
14. Readback verifies.
15. Lot remains held unless separately dispositioned.
16. Customer commitment unchanged.
17. Overview/workflow/run/decision views update.

Also test:
- incomparable baseline variant
- blocked release attempt
- no-alternative-supply variant

==================================================
36. OPTIONAL LIVE CHECK
==================================================

Provide exact manual connected instructions for one live QE-004 model run.

Do not run paid models automatically.

We want to later verify live behavior:
- source grounding
- correlation/root-cause restraint
- correct tool use
- correct arithmetic/tool use
- governance escalation

==================================================
37. DOCUMENTATION
==================================================

Update Phase 08 docs with:

- QE-004 source-of-truth mapping
- workflow architecture
- source IDs
- agent responsibilities
- comparability policy
- supply calculator
- quality governance boundary
- recovery decision model
- exact write boundary
- manual connected demo path
- known limitations

==================================================
38. FINAL REPORT
==================================================

Report:

1. Source records created/reused
2. Cross-system IDs
3. Workflow implementation
4. Agent/specialist reuse
5. Comparability logic
6. Supply-impact calculation
7. Recovery options
8. Human decisions
9. Exact write boundary
10. UI integration
11. Eval cases
12. Tests/results
13. Connected/simulated/preview matrix
14. Manual live path
15. No paid models automatically run
16. Known limitations
17. Exact next 08.4C step

==================================================
39. STOPPING POINT
==================================================

Stop after Phase 08.4B.

Do NOT continue into:
- 08.4C Delivery Readiness
- connected freeform Concierge
- active event listeners
- Operations implementation
- Phase 09 polish
- Git cleanup/push

08.4B is complete when QE-004 can demonstrate:

Manufacturing exception
→ validated signal
→ affected material scoped
→ evidence gathered
→ supply impact calculated
→ recovery options prepared
→ standard investigation routed
→ consequential decision retained by human
→ permitted action executed
→ source readback verified
→ held material and customer commitments remain governed