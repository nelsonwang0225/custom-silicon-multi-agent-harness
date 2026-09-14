Continue working in the existing Stratos Silicon repository and current project
thread.

Implement Phase 09.2:
CROSS-WORKFLOW PRODUCT INTEGRATION AND DEMO-FLOW HARDENING.

Phase 09 is the final product-build phase.

Do not add new major product capabilities.
Do not redesign the architecture.
Do not broaden authority or permissions.
Do not activate background schedulers/event listeners.
Do not run paid models automatically.
Do not perform Git cleanup/push work yet.

Reuse all existing functionality:
- CR-017 material change
- CR-019 standard/touchless change
- QE-004 yield/quality recovery
- DR-009 delivery readiness
- Stratos Concierge
- Workflows & Automations
- Decisions
- Operations
- Demo reset/baseline controls
- source applications
- Phase 06 governance
- Phase 07 eval framework

==================================================
1. OBJECTIVE
==================================================

Harden the entire connected product as one coherent system.

The four connected demo paths must share consistent:
- programs
- cases
- source records
- workflow states
- decisions
- activities
- alerts
- search results
- Concierge context
- Operations records

Fix cross-page/state inconsistencies now rather than during the final demo.

==================================================
2. CANONICAL DEMO FLOWS
==================================================

Treat these as the canonical connected paths:

A. CR-019
Standard Change / Touchless
request
→ applicability
→ evidence
→ touchless policy
→ package
→ Validation Operations handoff
→ readback verification

B. CR-017
Material Change
request
→ agent investigation
→ evidence gap
→ proposal
→ engineering approval
→ governed execution
→ source readback
→ synthetic physical validation result
→ agent reassessment
→ engineering evidence review
→ technical validation complete
→ customer acceptance remains separate

C. QE-004
Yield / Quality Exception
quality signal
→ comparability
→ material scope
→ evidence
→ supply impact
→ investigation routing
→ recovery options
→ human consequential decision
→ permitted execution
→ readback
→ held material remains governed

D. DR-009
Delivery Readiness
customer request
→ technical readiness
→ inventory reconciliation
→ 600/800/200 calculation
→ commitment options
→ human commercial/program decision
→ ERP/Planner update
→ readback
→ remaining gap preserved

==================================================
3. CROSS-WORKFLOW SOURCE CONSISTENCY
==================================================

Audit the shared authoritative records.

Especially:
- PRG-A17
- Helios customer identity
- CFG-B-01 / relevant configurations
- shared milestones
- QE-004 held inventory used by DR-009
- CR-017 technical readiness consumed by DR-009
- shared Validation evidence
- ERP allocations/order state

There must not be contradictory representations across workflows.

Examples that must never happen:
QE-004 says lot held while DR-009 counts it as released.
CR-017 says technical review pending while DR-009 says technical readiness complete,
unless the scenario explicitly uses a different deterministic variant.

Fix underlying source/view-model mappings, not by hard-coding UI exceptions.

==================================================
4. CASE-STATE NORMALIZATION
==================================================

Ensure all four cases expose a consistent high-level case-state contract.

Examples:
- new
- investigating
- needs_review
- approved
- executing
- verification_required
- waiting_external
- completed_technical
- escalated
- partial_failure

Use existing terminology where possible.

Do not force all workflows into identical lifecycle stages.
Provide a shared semantic layer while preserving workflow-specific detail.

==================================================
5. OVERVIEW CONSISTENCY
==================================================

Ensure Overview reflects the actual current business state.

Needs attention should prioritize:
- real human decisions
- real blockers
- failed/partial execution
- stale evidence
- unresolved external dependencies

Do not treat completed autonomous handoffs as human attention items.

Avoid duplicate cards for the same underlying issue.

==================================================
6. PROGRAM PAGE
==================================================

Make the Helios program page a coherent control-plane view across all four cases.

Show:
- CR-017
- CR-019
- QE-004
- DR-009

with concise current states.

Connect relevant dependencies visually where useful:
QE-004 → DR-009 supply
CR-017 → DR-009 technical readiness

Do not add decorative dependency lines without real underlying relationships.

==================================================
7. DECISIONS CONSISTENCY
==================================================

Ensure Decisions contains only genuine human decisions.

Examples:
- CR-017 validation authorization
- CR-017 engineering evidence review
- QE-004 recovery / program decision
- DR-009 commitment decision

CR-019 successful touchless handoff should NOT create a fake human decision.

Ensure:
- proposal versions
- reviewer identity
- current/stale state
- execution linkage

are consistent with case pages.

==================================================
8. WORKFLOWS CONSISTENCY
==================================================

Workflow catalog should truthfully show all connected capabilities.

At minimum:
- Requirement Change Analysis — Connected
  - standard touchless route
  - material human-review route
- Yield / Quality Exception Recovery — Connected
- Delivery Readiness / Commitment Planning — Connected

Remove outdated Preview/Simulated labels for workflows now actually connected.

Saved schedules/events remain configuration-only.

==================================================
9. SEARCH CONSISTENCY
==================================================

Global search should resolve all canonical IDs:
CR-017
CR-019
QE-004
DR-009

and related:
- runs
- decisions
- evidence
- source records
- automation configs

Prioritize business objects over technical artifacts.

==================================================
10. ALERT CONSISTENCY
==================================================

Deduplicate alerts.

Alerts should represent actionable changes, not every source event.

No stale alerts after reset or completed action.

Mark-read remains presentation-only.

==================================================
11. CONCIERGE CONSISTENCY
==================================================

Ensure Concierge receives consistent context across:
Overview
Program
Case
Decision
Workflow
Operations

The same question should not produce contradictory business state depending on page.

Concierge must prefer current authoritative state over old conversation state.

==================================================
12. OPERATIONS CONSISTENCY
==================================================

Ensure every connected workflow can be traced:
case
↔ run
↔ agents
↔ evidence
↔ proposal
↔ decision
↔ action
↔ verification

No orphan runs/decisions for the canonical demo.

==================================================
13. SOURCE-APP DEEP LINKS
==================================================

Audit deep links into:
Engineering Hub
Validation Lab
Manufacturing Portal
Commercial ERP
Program Planner

Where exact-record deep linking exists, use it.

Where not supported, open the relevant source app with stable context.

Do not add arbitrary URL/query execution.

==================================================
14. LOADING / REFRESH BEHAVIOR
==================================================

Standardize:
loading
refreshing
running
waiting for human
waiting for external source
failed
stale

Do not show blank cards or ambiguous spinners.

Polling must not trigger model calls.

==================================================
15. PARTIAL FAILURE
==================================================

Ensure each workflow has a clear partial-failure experience where applicable.

Examples:
CR-017 scheduling succeeds / Planner fails.
DR-009 ERP succeeds / Planner fails.
QE investigation created / Planner recovery task fails.

Show exactly what succeeded and what remains.

==================================================
16. DEMO RESET INTEGRATION
==================================================

After Full Demo Reset:
all four workflows/pages/search/alerts/Concierge/Operations must reflect baseline
without manual browser storage clearing.

Test stale tabs where practical:
a case page open before reset should refresh into current state and invalidate stale
action controls.

==================================================
17. AUTOMATED VERIFICATION
==================================================

Run the full existing offline suite:
- source
- coordinator
- MCP
- offline evals
- control-plane/backend
- browser E2E
- typecheck/build

Add cross-workflow consistency tests.

No paid models.

==================================================
18. REPORT
==================================================

Report:
1. Cross-workflow inconsistencies found/fixed
2. Source mappings corrected
3. Overview/program/case consistency
4. Decisions/workflows/search/alerts consistency
5. Concierge consistency
6. Operations linkage
7. Reset integration
8. Files changed
9. Tests/results
10. Remaining known product-level issues

Stop after 09.2.
Do not continue automatically into 09.3.