# Phase 08.4C — Connected Delivery Readiness / Commitment Planning

DR-009 connects the existing coordinator to source-owned demand, technical evidence,
shared Manufacturing disposition, ERP allocations and Planner logistics. The primary
case supports a **600-unit partial commitment against an 800-unit request**. Only an
exact Program Owner approval permits the ERP commitment and matching Planner link.
Independent HTTP readback verifies each action; the remaining **200 units stay
uncommitted**, customer agreement stays pending, and delivered quantity stays zero.

## 1. Source records and 2. stable references

| Source owner | Created / reused authoritative records |
|---|---|
| Commercial ERP | New `DR-009` delivery request, `LINE-HEL-800-1` stable line reference, `STATE-DR-009` commercial version/current commitment pointer; reuse `ORD-HEL-800` (800 units, original order date). New other-release order `ORD-HEL-150` and allocation `ALLOC-HEL-150` for 150 units from `MAT-B-202`. |
| Manufacturing | Reuse QE-004's `MAT-B-203` / `LOT-B-203` (600 released) and `MAT-B-204` / `LOT-B-204` (250 held). New `MAT-B-202` / `LOT-B-202` (150 released, allocated to `ORD-HEL-150`). No copied QE hold ledger. |
| Engineering | Reuse `CFG-B-01`, approved baseline `REQ-042-V1`, `WF-LC-V1`, `CRIT-BASE-V1`; new `CLEAR-HEL-BASE` binds configuration, requirement, workload, criteria and exact evidence with a review digest. |
| Validation | Reuse `RES-BASELINE-B` for the baseline. CR-017 variants read the actual result, applicability and distinct Engineering review associated with `REQ-042-V2` / `WF-LC-V2`. |
| Program Planner | Reuse `MS-HEL-800`; new `LOG-HEL-800` with source-confirmed destination, material readiness, preparation, loading and transit. |
| Scope | Every record remains linked to `PRG-A17` / `CUST-FML01` (Helios Atlas Inference / Helios AI). |

`fixtures/delivery_readiness.json` contains only additive authoritative synthetic
source records. Developer-only variants live under `coordinator/evals/phase08_4c/`.
The optional `FUT-HEL-300` receipt exists only in the future-supply variant.

The existing `ORD-HEL-800` quantity and `committed_delivery_at` remain intact. Its
original order-level promise is distinct from the newly authorized delivery-release
commitment. The UI shows both. The new ERP commitment means Stratos authorized that
specific partial release promise; it does **not** mean Helios agreed to split delivery,
that the original 800-unit obligation disappeared, or that goods shipped.

The control-plane index stores run/case references, source digests, proposal and
decision references, durable action keys/status and readback receipts. Recorded
analysis claims are evidence, not an order/inventory ledger. Current screens and
write checks re-read source APIs. The control plane owns no authoritative full order,
material ledger, logistics plan or delivery commitment.

## 3. Connected runtime and 4. specialist reuse

`delivery_readiness` is implemented through the existing registry, WorkflowService,
CaseHarness, scoped MCP wrapper and SDK Agent/Runner path. Program Coordinator
retains ownership. Manufacturing, Validation & Evidence, and Program/Commercial
perform bounded parallel work; Change Impact is available only for a concrete
configuration question. There is no separate Delivery Agent or new runtime.

Intake resolves ERP provenance, exact order/line, customer/program, configuration,
quantity/date/destination, milestone and trusted actor. `get_delivery_context` is the
28th read-only MCP tool. The existing tool matrix gains it only on this route; other
routes retain their scoped tools. `get_delivery_records` is a host read through HTTP.
The model has no business write tools. Typed delivery claims must match the source
calculator, and cited JSON pointers must match actual source receipts.

## 5. Technical readiness and 6. supply calculation

Baseline READY requires approved Engineering scope, exact clearance, matching
configuration/workload/criteria versions and sufficient passed Validation evidence.
Technical readiness is independent of stock. In the CR-017-pending variant, eligible
supply remains 600 but customer-ready quantity is zero and proposal creation is blocked.
The completed variant reads CR-017's actual physical result and current Engineering
review; DR-009 never writes CR-017.

The delivery API exposes a bounded projection of current CR-017 facts. Its evidence
digest binds the full source Validation contract. Immutable historical snapshots and
normalized content projections are not presented as competing current records. The
original CR-017 physical-validation API and authority checks remain unchanged.

Deterministic non-overlapping calculation:

```text
physical 1,000 = released + unallocated 600 + held 250 + allocated elsewhere 150
eligible 600; requested 800; current gap 200
```

Lot restrictions, dispositions, configuration/product revision, material groups and
ERP allocation obligations are checked. Duplicate/overlapping groups or inconsistent
allocation ledgers block a proposal. Held units, wrong configurations, other allocations
and expected future receipts cannot increase current eligible supply.

## 7. Options and timing

| Option | Base quantity / remaining gap | Authority / status |
|---|---:|---|
| Partial commitment | 600 / 200 | Executable only after exact Program Owner decision. |
| Allocation review | 150 to evaluate / 50 if moved | Analysis only. Identifies `ORD-HEL-150`, which loses those 150 units. Requires separate allocation authority; no executor installed. |
| Future supply | Absent in base | Only emitted for an actual future receipt. Variant has 300 expected units, conditional, with receipt/quality/validation prerequisites. Not current stock or a guaranteed arrival. |

`LOG-HEL-800` supplies material-ready **2026-11-18 06:00 UTC**, preparation **120 min**,
loading **60 min**, transit **2,880 min**, destination **Helios Austin receiving**.
Using elapsed UTC time: earliest ship **Nov 18 09:00**, earliest arrival **Nov 20 09:00**.
The requested and proposed commitment is **Nov 23 18:00 UTC, arrival semantics**.
Missing date, quantity, destination/logistics confirmation or durations blocks a
commitment; no fallback dates/transit times are invented. Future receipt dates have
`expected_material` semantics. Costs remain unknown. This is not a holiday/carrier
calendar or an assurance of actual shipment.

## 8. Decision authority and 9. exact writes

Program Operator may investigate and request execution of an already approved plan.
The existing trusted **Program Owner** alone reviews the quantity/date proposal. Reader,
automation, Engineer and portfolio identities cannot approve it. Demo selectors remain
role-test stand-ins, not production authentication or proof of a real human.

The immutable ERP proposal binds the exact request, full deterministic analysis,
source input/context digests, commercial head/version, order line, quantity/date,
destination, selected option, assumptions, owner and permitted actions. Review binds
that exact plan version and digest. Every consequential step checks current sources.
Inventory, technical evidence, allocation, logistics, date or commercial state changes
invalidate an old proposal/approval. Only the precise ERP transition created by that
same plan is allowed between ERP and Planner steps.

| Route | Writer | Scope |
|---|---|---|
| `POST /api/v1/erp/commitment-plans` | Automation host | One source-calculated partial commitment proposal; no customer promise yet. |
| `POST /api/v1/erp/commitment-decisions` | Program Owner | Exact immutable approve/reject decision. |
| `POST /api/v1/erp/delivery-commitments` | Automation host after approval | Exact authorized release commitment and optimistic ERP head update, in one ERP transaction. |
| `POST /api/v1/programs/delivery-links` | Automation host after ERP readback | Matching Planner commitment link for `MS-HEL-800`. |

No generic ERP CRUD, inventory reallocation, held-lot release, manufacturing-plan change,
validation authoring, customer response, shipment completion or original-order edit is
installed. Manufacturing and Engineering/Validation are read-only on this workflow.
Existing CR-019 touchless and QE-004 write boundaries are preserved.

## 10. Execution and verification

Execution persists an intent and original idempotency key before HTTP, records action
success separately, then independently GETs and matches ERP fields before Planner.
Planner has its own transaction and independent readback. Scope, plan/decision IDs,
quantity, date semantics, destination, customer agreement and allocation/delivery flags
are verified. Repeated calls do not create duplicate commitments or links.

If ERP succeeds and Planner fails, the case shows **Partial completion — ERP update
verified; Planner update incomplete**. It does not claim rollback or verified completion.
Retry reconciles the original ERP result and resumes only incomplete permitted work.
Unknown committed/uncommitted writes, missing/mismatched readback and changed sources
remain explicit failures until safe reconciliation succeeds.

## 11. UI integration

DR-009 has a connected case workbench with request, readiness gates, inventory bar/table,
allocations, timing, option comparison, exact human decision, step receipts and current
commitment. It appears in Overview, Helios program, decisions, workflow catalog/runs,
search and alerts. Five source views read their owning records through HTTP. The old
DR-009 fixture presentation was removed; its legacy URL resolves to the connected case.
Concierge has contextual delivery suggestions but remains Preview. The existing visual
system and blue gradient are retained.

Morning Delivery Readiness targets the connected workflow, while its schedule remains
configuration only: **Background scheduler not enabled**. No timer, event listener,
automatic investigation or commitment execution is running.

## 12. Evals and 13. tests

The Phase 07 runner adds `--include-delivery` without weakening original graders. All
18 new probes are critical and missing/failed observations remain in the denominator:
supply arithmetic; held exclusion; allocation exclusion; wrong configuration; technical
blocker; conditional future receipts; no autonomous commitment; exact owner; no
reallocation; stale proposal; partial completion; independent readback; missing date;
missing quantity; no double-counting; separate acceptance; shared QE hold; CR-017 state.

All 95 offline cases passed (original + standard + quality + delivery), with zero critical
failures. Source/coordinator/MCP and browser results, actual commands, corrected initial
failures, file inventory and hashes are recorded in `PHASE08_4C_VERIFICATION.json`.
The scripts use real local HTTP/MCP and deterministic SDK response doubles: **scripted
integration testing**, not a paid AI run or actual human approval. Runtime model quality
and the optional semantic grader have not been measured in this phase.

## 14. Connected / simulated / preview matrix

| Capability | State |
|---|---|
| CR-017 requirement change | Connected; existing exact Engineering governance and downstream evidence review. |
| CR-019 standard change | Connected; existing narrowly policy-authorized touchless Validation Operations intake. |
| QE-004 quality recovery | Connected; existing investigation/recovery with separate Quality disposition. |
| DR-009 delivery readiness | Connected; exact Program Owner commitment and ERP/Planner readback. |
| Nine other catalog workflows | Preview; no connected executor. |
| Delivery allocation review / future receipt options | Source-backed analysis only; no reallocation or future promise executor. |
| Concierge / Operations | Preview. |
| Schedules and event/condition configurations | Inactive background behavior. |
| Offline model responses | Deterministic doubles, explicitly labeled in test mode. No workflow is labeled Simulated. |

## 15. Manual demo and later live path; 16. paid models

The current working demo database was **not installed into or reset**. Start an isolated
scripted demo, which creates a new cache database each time:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase08_4c.serve
```

In a second terminal:

```sh
cd mock_apps_ui
MOCK_API_URL=http://127.0.0.1:18042 CONTROL_HOST_URL=http://127.0.0.1:18087 npm run dev -- --port 5178
```

Open `http://127.0.0.1:5178/control/programs/PRG-A17/cases/DR-009`, log in as Program
operator, run connected delivery analysis, inspect 600 / 800 / 200 and the proposal,
switch to Program Owner, approve, execute and inspect ERP/Planner readback. After a full
page reload, log in again before a further action. Restart the isolated fixture with
`--variant technical_blocked`, `technical_complete`, `future_conditional`,
`wrong_configuration`, `partial_failure` or `stale_proposal` for those demonstrations.
Additional source/host variants cover held-material disposition changes, a 600-unit
request, missing quantity/date/logistics and duplicate inventory.

For one later **explicit paid live model run**, reuse the already-authorized model setup.
Stop only the source service owning the selected local demo DB before its additive install;
do not launch a competing service on occupied ports. For the default `.demo/enterprise.sqlite3`:

```sh
DEMO_MODE=true PYTHONPATH=src .venv/bin/python -m mock_enterprise install-delivery-case
DEMO_MODE=true PYTHONPATH=src .venv/bin/python -m mock_enterprise serve --port 18008
```

Start the existing scoped reader MCP and existing live host in separate terminals:

```sh
PYTHONPATH=src mcp_server/.venv/bin/python -m stratos_mcp --port 19082 --backend-url http://127.0.0.1:18008 --program-id PRG-A17 --customer-id CUST-FML01
DEMO_MODE=true PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.control_host --source-url http://127.0.0.1:18008 --mcp-url http://127.0.0.1:19082/mcp --metadata-dir .cache/phase08-4c/live-metadata --port 18082 --ui-origin http://127.0.0.1:5188
```

Point Vite at those ports:

```sh
cd mock_apps_ui
MOCK_API_URL=http://127.0.0.1:18008 CONTROL_HOST_URL=http://127.0.0.1:18082 npm run dev -- --port 5188
```

Open DR-009 and click **Run connected delivery analysis** once. Check scoped tool receipts,
actual specialist findings, deterministic calculator values, exact dates and the human
boundary. Starting the server alone does not invoke a paid model. No model credentials
were inspected or printed and **no paid models were run automatically**.

## 17. Limitations and 18. exact next step

This is a local synthetic source environment with mock identities. Engineering clearance
is for the specified evidence scope, not customer technical acceptance. The executable
path authorizes a partial release promise and links it; it does not reserve new stock,
reallocate, fulfill shipment, obtain customer consent or settle the remaining gap. Option B
and future supply remain analysis-only. Logistics use source-confirmed elapsed durations;
carrier calendars, costs and physical fulfillment are not modeled. Current-source digest
checks conservatively require reassessment after material changes. The shared source
runtime performs per-system transactions, not a distributed transaction.

Stop at **08.4C**. The next slice, only on explicit request, is **08.5: connect Stratos
Concierge to the existing scoped investigation/invocation and case/run contracts while
preserving exact human review and execution boundaries**. No active scheduler, Operations,
Phase 09 polish, Git cleanup, branch, commit or push was performed.
