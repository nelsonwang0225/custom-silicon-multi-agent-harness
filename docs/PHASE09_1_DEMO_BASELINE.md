# Phase 09.1 canonical demo baseline — phase09-v1

This is a developer/demo-maintenance contract, outside business retrieval. It is
implemented by `mock_enterprise.demo_management.baseline()` using the existing
`load_seed()` and the same standard, quality and delivery extension loaders as the
explicit installers. There is no second set of business facts. The fixed scenario
clock is **2026-11-16T09:00:00Z**. Baseline version `phase09-v1` is administrative;
source content, availability and record versions retain their existing meanings.

| Path | Exact initial story | Generated current state |
|---|---|---|
| CR-017 | `pending_impact_assessment`; REQ-042-V1 approved; REQ-042-V2 requested; CFG-B-01; MS-ACCEPT-01 forecast `not_reassessed_for_new_request`; evidence gap | No investigation runs, current plan, decisions, job/reservation, Planner link/task, synthetic completion/result or engineering evidence review. Customer acceptance pending. |
| CR-019 | `new`; STD-REQUEST-019 customer intake with recorded provenance; PROC-STD-01 and STD-HANDOFF-V1 approved; VALOPS-A17 open; exact CFG-B-01 / FW-2.3 / RT-4.1 / WF-LC-V1 | No run or Validation Operations intake. Ready for eligibility assessment. Lab authorization, physical testing and acceptance remain separate. |
| QE-004 | Exception `open`; LOT-B-204 `quality_hold`; OBS-QE-004 reports 200/250 passed, 50 failed; comparable BASE-FT-B-72 is 960/1000; root cause unknown | No investigation, recovery plan/decision or Planner recovery task. All 250 devices remain held and ineligible. Original order commitment unchanged. |
| DR-009 | ORD-HEL-800 requests 800 units arriving 2026-11-23T18:00:00Z; STATE-DR-009 record_version 1, current_commitment_id null; MS-HEL-800 original forecast | No run, commitment proposal/decision, partial commitment or Planner delivery link. Approved V1 technical baseline; customer technical acceptance and agreement pending. |

DR-009 arithmetic is **1,000 physical = 600 released/unallocated/eligible
(MAT-B-203 / LOT-B-203) + 250 held (MAT-B-204 / LOT-B-204) + 150 already allocated
(MAT-B-202 / LOT-B-202 / ALLOC-HEL-150 to ORD-HEL-150)**. Requested 800 minus
eligible 600 leaves **200 gap**. First-pass 200 from the held lot does not confer
release eligibility. ORD-1204 and MS-ACCEPT-01 belong to CR-017; ORD-HEL-800 and
MS-HEL-800 are the additional shared QE/DR demand, not replacements.

The primary DR-009 request uses REQ-042-V1 and CLEAR-HEL-BASE; technical_change_id
is null. Full reset removes the developer technical V2 dependency and conditional
future-supply variant, and restores the original request, allocations and logistics.
It also resets CR-017 evidence/review so an old technical-complete walkthrough cannot
contaminate the next demo. No inverse inventory arithmetic is used.

## Scope and dependency rules

Full reset restores the 69 explicitly authored baseline records and removes their
typed generated descendants, within the four scenarios. The surrounding generated
portfolio, its initial synthetic history, CR-018 and unrelated case state are
preserved. Stable baseline IDs, owners, versions, timestamps and references come
from the existing fixture loaders. Scoped current business audit events and
idempotency receipts are archived before removal. Immutable historical test results
in the baseline are restored exactly; generated downstream results are selected
through their lab-completion provenance.

Single-scenario reset selects only that case's authored records, explicit shared
inputs and typed generated descendants. Unrelated runs/source records remain.
A shared input that differs from baseline is conservatively refused with
`SHARED_DEPENDENCY_REQUIRES_FULL_RESET`. This includes QE/DR material/order/milestone
facts and shared Engineering configuration/evidence. CR-017 reset also refuses an
active DR-009 technical dependency, or a recorded CR-019 intake alongside changed
shared validation resources. A changed shared scenario clock requires full reset.
No dependency is silently added to a single-scenario reset.

QE-004 can be reset while an unchanged DR-009 commitment exists when none of their
shared material/commitment inputs needs restoration. DR-009 reset preserves QE-004
investigation/recovery state. CR-019 reset preserves CR-017 scheduling; nominated
sample availability is owned by CR-017, not changed by the standard intake.

## Mutable host state and archives

Selected cases/runs and their proposals, proposal status, decision bindings,
preparations, reviews, actions, executions/attempts, verifications, standard handoff,
quality recovery, delivery progress and business activity are removed from the
current index. Prior indices and selected source records/receipts/audit are written
as immutable local snapshots under the configured host metadata directory's
`demo-archives/reset_<id>/`. Existing `runs/<run_id>/` checkpoint/trace/report files
are left byte-for-byte intact. Archive files are developer-only, not executable
state, agent retrieval or current search results. Workflow definitions and schema
metadata remain. No arbitrary store/table wipe occurs.

Full reset archives all visible Concierge history in CUST-FML01/PRG-A17. Single-case
reset archives affected sessions (case/card/run links), preserving unrelated visible
history. Both invalidate process-local action capabilities and all current local
conversational drafts; a cross-case draft could otherwise carry stale facts. UI tabs
observe the persisted epoch and remount current views, clearing retry receipts and
voice capture while showing that old drafts/proposals/actions are no longer current.
Explicit business roles and approvals never grant reset authority.

Full reset restores the three original curated automation examples (`example_cr017`,
`example_delivery`, `example_yield`) with stable IDs and canonical configuration
metadata. Temporary configurations in the demo's customer/program scope, receipts
and configuration audit are archived. A scenario reset removes temporary configs
explicitly scoped to that case and restores its matching curated example, retaining
unrelated and broader configurations. All examples remain `configuration_preview`,
`background_execution_enabled=false`. No scheduler, listener or condition evaluator
is installed.

## Validation

The structured validator compares every selected source row with the normalized
canonical record, detects extra generated descendants, checks source foreign keys,
ownership/versions/reference content and the fixed clock, and independently derives
the DR arithmetic. It requires empty current scoped orchestration and affected
Concierge history, canonical automation examples and no stale action capabilities.
Five independent HTTP reads exercise Engineering, Validation, Manufacturing, ERP
and Planner through existing adapters; unavailable reads fail validation. Additional
per-scenario HTTP checks assert the actual source projections: missing CR-017
evidence and empty physical work, absent standard intake, held quality/comparison
math, and uncommitted delivery arithmetic/readiness. Each appears in the structured
`scenario_checks` result. Successful HTTP with incorrect business facts still fails. A second
source digest detects changes during readback. `baseline_valid` is true only when
all applicable checks pass and the reset journal has no unresolved operation.

A single-case `baseline_valid` applies to that scope. Other cases can intentionally
remain mutated. Full validation checks all four. Source/control digests establish
repeatability; reset audit IDs, epochs and wall-clock audit timestamps deliberately
change on each explicit request and are excluded from baseline identity.

Historical Phase 07 eval files—including both 4/6 failed full smoke reports, later
1/1 targeted passes and immutable reliability/trace artifacts—are never targets.
Operations keeps those as historical project verification; current demo run history
is empty after reset and the Demo controls page reports archived demo generations.
Documentation and previous handoffs are preserved.
