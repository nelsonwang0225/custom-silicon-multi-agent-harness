Continue working in the existing Stratos Silicon repository and current project thread.

We are beginning Phase 09:
FINAL DEMO HARDENING.

Phase 09 is the last product-build phase.
Do not add new product capabilities unless they are required to make an existing
demo workflow reliable, reproducible, or understandable.

This prompt implements Phase 09.1:
DEMO RESET + REPRODUCIBILITY.

The objective is to make the full Stratos demo reliably resettable to a known,
consistent state before each walkthrough.

Preserve all existing Phase 08 functionality:
- CR-017 material change
- CR-019 standard/touchless change
- QE-004 yield/quality recovery
- DR-009 delivery readiness
- connected Stratos Concierge
- Workflows & Automations
- Decisions
- Operations
- source applications
- Phase 06 governance
- Phase 07 evals/reliability

Do not redesign the application.
Do not activate background schedulers/event listeners.
Do not change workflow authority.
Do not broaden write permissions.
Do not run paid models automatically.
Do not perform Git cleanup/push work yet.

Git remains relaxed:
- preserve unrelated work
- avoid destructive operations

==================================================
1. PHASE 09.1 OBJECTIVE
==================================================

Create a safe, explicit, deterministic demo-reset capability that restores all
connected demo scenarios to a known baseline without rebuilding the repository.

A user should be able to:

1. Start from a known demo-ready source state.
2. Run one or more demo workflows.
3. Mutate source records through the existing governed paths.
4. Reset the demo.
5. Confirm every relevant source system, control-plane record, workflow state,
   decision state, and demo UI returns to the intended baseline.
6. Repeat the demo without contamination from previous runs.

The reset must be deliberate and explicit.

Normal navigation, refresh, restart, or app launch must NOT silently reset data.

==================================================
2. DEFINE THE CANONICAL DEMO BASELINE
==================================================

Document and encode a canonical baseline for all four demo paths.

At minimum:

CR-017
- initial material-change request exists
- investigation has not yet been rerun for the fresh demo state
- no fresh proposal approval is pre-granted unless the intended starting story
  explicitly requires it
- no new validation job/result exists beyond whichever original source fixture
  is required
- customer acceptance remains pending

CR-019
- standard request exists
- touchless handoff has not yet been executed for the reset baseline
- no duplicate Validation Operations intake exists
- approved procedure/configuration/source provenance is present

QE-004
- quality exception exists
- affected lot is on hold
- base test results and comparable baseline exist
- quality investigation/recovery work has not yet been newly executed
- held material remains ineligible
- customer commitment remains unchanged

DR-009
- customer requests 800 units
- 600 are released/unallocated/eligible
- 250 are quality-held
- 150 are allocated elsewhere
- current connected commitment state matches the intended initial story
- no new partial commitment from the prior demo remains unless explicitly part
  of baseline
- technical-readiness variant is reset consistently

Concierge
- no stale draft/actions from prior scenario
- no stale approval/action cards
- conversation state reset according to documented demo policy

Operations
- historical immutable test/eval artifacts remain preserved
- new demo-run operational records are reset/archived according to policy
- historical Phase 07 live-smoke results must NOT be deleted or rewritten

==================================================
3. SOURCE SYSTEMS ARE AUTHORITATIVE
==================================================

Reset authoritative business state in the relevant mock source systems first.

The control plane must then rebuild/reconcile its derived/orchestration state.

Do not reset only frontend state.

Relevant source apps include:
- Engineering Hub
- Validation Lab
- Manufacturing Portal
- Commercial ERP
- Program Planner

Use existing fixture/install/reset architecture where possible.

Do not create a second unrelated seed mechanism if one already exists.

==================================================
4. PRESERVE HISTORICAL ARTIFACTS
==================================================

Do NOT delete or rewrite:

- historical Phase 07 eval artifacts
- historical 4/6 live smoke report
- later targeted pass artifacts
- immutable trace/eval history intended for Operations
- documentation/handoffs

Demo reset concerns the current demo/business/runtime state, not historical
verification evidence.

If Operations needs to distinguish current-demo history from historical project
verification, add explicit categorization rather than deleting evidence.

==================================================
5. RESET CONTROL-PLANE ORCHESTRATION STATE
==================================================

Define exactly which mutable orchestration records reset.

Potential reset candidates:
- demo cases/runs generated after baseline
- proposals
- decisions
- execution attempts
- verification records
- current activity timeline
- Concierge demo sessions
- automation configs if designated demo-created
- transient alerts/read-state

Preserve:
- workflow definitions
- source-system records belonging to baseline
- eval artifacts
- static configuration
- schema/version metadata

Do not delete arbitrary records by table-wide wipe unless the store is
explicitly isolated to demo mutable state.

Use scoped identifiers/namespaces.

==================================================
6. RESET SOURCE-SYSTEM MUTATIONS
==================================================

Restore mutations created by connected workflows.

Examples:

CR-017
- remove/reset demo-created validation jobs/reservations
- reset Planner links/tasks created by governed execution
- reset downstream synthetic validation result/review if generated during demo
- restore decision/proposal state to baseline

CR-019
- remove/reset demo-created Validation Operations intake
- preserve approved Engineering procedure/source records

QE-004
- remove/reset investigation/recovery tasks created during demo
- restore lot hold state and baseline quality-exception state
- restore supply/customer state

DR-009
- revert demo ERP commitment updates
- revert demo Planner commitment/readiness updates
- restore allocations and quantities to baseline
- restore 600/800/200 baseline arithmetic

Use authoritative baseline snapshots/fixtures rather than inverse arithmetic
where possible.

==================================================
7. SHARED CROSS-WORKFLOW CONSISTENCY
==================================================

Pay special attention to shared records.

Examples:
- QE-004 held material is also used by DR-009.
- CR-017 technical-readiness state may affect DR-009.
- shared PRG-A17 milestone records may be referenced by multiple workflows.
- source IDs such as lots, orders, configurations and milestones must remain
  consistent after reset.

Do not reset one scenario in a way that makes another scenario contradictory.

Create explicit dependency ordering where required.

==================================================
8. RESET MODES
==================================================

Provide at least two reset scopes:

A. FULL DEMO RESET
Restores all four connected demo scenarios and current control-plane mutable
state to the canonical baseline.

B. SINGLE-SCENARIO RESET
Supports at minimum:
- CR-017
- CR-019
- QE-004
- DR-009

Single-scenario reset must detect shared dependencies.

If resetting one case would create inconsistent shared business state, either:
- safely reset the required shared dependency too and explain it
or
- refuse and instruct the user to use Full Demo Reset.

Do not silently corrupt cross-scenario consistency.

==================================================
9. USER INTERFACE
==================================================

Add a restrained demo-management entry point.

Preferred location:
- demo/profile menu
or
- Operations / Demo controls
or
- another existing admin/demo-only surface

Do not place a giant Reset button on Overview.

Possible UI:

Demo controls

Reset scenario...
- CR-017
- CR-019
- QE-004
- DR-009

Reset full demo

Each reset should show:
- what will be reset
- what will be preserved
- affected source systems
- whether shared dependencies are included

Require explicit confirmation.

==================================================
10. DO NOT CONFUSE RESET WITH BUSINESS ACTION
==================================================

Reset is a demo/developer operation.

It is NOT:
- an agent tool
- a source-system business workflow
- an approval action
- a Concierge authority

The agents must not be able to invoke demo reset.

Concierge may explain where demo controls are, but must not execute reset.

Do not expose reset through MCP.

==================================================
11. HOST/API BOUNDARY
==================================================

If an API is required, create a narrow demo-management host endpoint/service.

Requirements:
- demo mode only
- explicit allowed scenario IDs
- server-side scope validation
- no arbitrary table/database reset
- no arbitrary filesystem access
- clear result summary

Do not expose generic "reset database" APIs.

If possible, reuse existing fixture installer/reset code internally.

==================================================
12. IDEMPOTENCY
==================================================

Reset must be idempotent.

Running Full Demo Reset twice should produce the same final baseline.

Running a scenario reset on an already-reset scenario should succeed safely or
return Already at baseline.

No duplicate seed records.

No changing stable IDs unnecessarily.

==================================================
13. BASELINE INTEGRITY CHECK
==================================================

After reset, run deterministic validation of the canonical baseline.

Create a structured baseline check covering at least:

CR-017
expected initial status

CR-019
no touchless intake yet

QE-004
lot held
expected baseline test data
expected supply impact

DR-009
physical 1000
held 250
allocated 150
eligible 600
requested 800
gap 200

Shared source versions/references
expected source ownership

Control-plane state
no stale approval/action state

Concierge
clean demo session state

Return:
baseline_valid = true/false

with discrepancies.

==================================================
14. DEMO STATE VERSION
==================================================

Add a small explicit baseline/demo-state version if useful, for example:

demo_baseline_version:
phase09-v1

Do not overload source business versions.

This may help reset tooling and troubleshooting.

Document it clearly.

==================================================
15. RESET + RESTART
==================================================

Test reset across service restarts.

Required behavior:

reset
→ stop/restart host/source app services
→ baseline remains valid

and:

mutate demo
→ restart
→ mutations persist
→ explicit reset
→ baseline restored

Restart must not itself reset state.

==================================================
16. DEMO LAUNCH PREPARATION
==================================================

Provide a simple documented pre-demo sequence:

1. Start source apps.
2. Start control host.
3. Start frontend.
4. Run Full Demo Reset.
5. Run baseline validation.
6. Open Overview.

Do not yet build the final Phase 10 launch script unless a small helper naturally
belongs to reset verification.

If a reset CLI is useful, provide it.

Example conceptual commands:
demo reset
demo verify

Use repo conventions rather than inventing arbitrary command names.

==================================================
17. SCENARIO-SPECIFIC EXPECTED BASELINES
==================================================

Document exact initial user-facing states.

CR-017:
Material change / evidence gap requiring investigation.

CR-019:
Standard change ready for touchless eligibility assessment.

QE-004:
Quality exception open; lot on hold; investigation not yet completed.

DR-009:
Delivery readiness case open; 600/800 supportable; commitment not yet changed.

Use actual implemented terminology.

This becomes the Phase 09 demo baseline contract.

==================================================
18. CONCIERGE RESET BEHAVIOR
==================================================

Full reset should clear demo conversational state that could confuse the next
walkthrough.

Preserve product configuration.

Clear or archive:
- current demo conversation messages
- pending action previews
- stale contextual drafts where appropriate

Do not delete historical Operations records unless explicitly categorized as
resettable demo session state.

Single-scenario reset should invalidate stale action cards for that case.

If the user currently has a stale proposal open in chat after reset:
show that it is no longer current.

==================================================
19. ALERTS / SEARCH / OPERATIONS AFTER RESET
==================================================

Verify:

Alerts:
only baseline-real alerts appear.

Search:
finds baseline records and does not return deleted duplicate mutable objects as
current.

Operations:
current demo state distinguishes reset baseline from historical project artifacts.

Decisions:
no stale executable proposal remains after reset.

==================================================
20. AUTOMATION CONFIGURATIONS
==================================================

Decide explicitly whether seeded automation configurations are part of baseline.

Recommended:
preserve the curated 08.3 example configurations as baseline configuration.

Reset user-created/demo-created temporary automation configs if appropriate.

No saved configuration should become active.

Document the choice.

==================================================
21. FAILURE SAFETY
==================================================

Reset should fail safely.

If one source system cannot reset:
- do not claim baseline valid
- report partial reset
- identify affected subsystem
- require retry/reconciliation

Do not silently leave half-reset business state while displaying success.

If practical, use staged reset + final validation rather than pretending a
distributed transaction exists.

==================================================
22. AUDIT
==================================================

Record a small demo-management audit event:

- reset type
- requested scenario
- timestamp
- demo actor
- result
- affected source systems
- baseline validation result

Keep this separate from business-case activity.

Do not make it appear that an operational agent reset the program.

==================================================
23. SECURITY
==================================================

Reset controls must not:
- be exposed as public production capability
- accept arbitrary record IDs
- enable generic source writes
- bypass schema validation

Use explicit demo-mode guard/configuration.

If demo mode is off:
reset endpoint/control unavailable.

==================================================
24. TESTS — FULL RESET
==================================================

Automate:

A. Start from mutated all-scenario state.

B. Full reset.

C. All canonical source facts restored.

D. All current proposals/actions reset correctly.

E. Shared QE/DR inventory state consistent.

F. Historical eval artifacts preserved.

G. Automation baseline correct.

H. Concierge current session clean.

I. Baseline validator PASS.

J. Second full reset produces identical state.

==================================================
25. TESTS — SCENARIO RESET
==================================================

For each:
- mutate scenario
- reset scenario
- verify baseline
- verify unrelated scenarios preserved

Test shared-dependency behavior explicitly.

Examples:
- resetting QE-004 cannot make DR-009 inventory contradictory
- resetting CR-017 dependency handles DR-009 readiness safely

==================================================
26. TESTS — FAILURE / RESTART
==================================================

Test:
- source reset failure
- partial reset
- baseline validator failure
- retry
- restart persistence
- no implicit reset on restart

==================================================
27. PRESERVE ALL EXISTING REGRESSIONS
==================================================

Run:
- source/backend tests
- coordinator tests
- MCP tests
- all offline evals
- CR-017
- CR-019
- QE-004
- DR-009
- Concierge
- Operations
- browser E2E
- typecheck/build

No paid models.

Do not rerun full live smoke.

==================================================
28. BROWSER E2E
==================================================

Test a realistic sequence:

1. Full reset.
2. Open Overview.
3. Verify baseline.
4. Run CR-019 touchless handoff.
5. Run QE-004 workflow.
6. Run DR-009 workflow / proposal.
7. Mutate CR-017 through connected execution.
8. Confirm UI changes.
9. Full reset.
10. Confirm all four cases return to baseline.
11. Refresh/restart host.
12. Baseline remains.
13. Search/alerts/Decisions/Operations show consistent reset state.

Use deterministic model stubs.

==================================================
29. DOCUMENTATION
==================================================

Create/update Phase 09 handoff with:

- canonical baseline
- source-system reset order
- shared dependencies
- full vs single-scenario reset
- demo-mode security boundary
- exact commands/UI path
- baseline validation rules
- automation-config policy
- Concierge reset behavior
- preserved historical artifacts
- limitations

==================================================
30. FINAL REPORT
==================================================

Report:

1. Baseline definition
2. Reset architecture
3. Source systems reset
4. Control-plane state reset
5. Shared dependency handling
6. Demo UI/CLI controls
7. Idempotency
8. Baseline validator
9. Restart behavior
10. Security/demo-mode guard
11. Historical artifact preservation
12. Files changed
13. Tests/results
14. Browser verification
15. Exact pre-demo reset instructions
16. Known limitations
17. Exact Phase 09.2 starting point

==================================================
31. STOPPING POINT
==================================================

Stop after Phase 09.1.

Do NOT continue into:
- Phase 09.2 golden-path walkthrough/fixes
- live paid-model smoke
- final visual polish
- Git cleanup/push
- slides/storytelling

Phase 09.1 is complete when:

mutated demo
→ explicit reset
→ authoritative source baseline restored
→ control-plane orchestration reconciled
→ cross-workflow consistency restored
→ baseline validator passes
→ reset is repeatable after restart

without deleting historical reliability/eval evidence.