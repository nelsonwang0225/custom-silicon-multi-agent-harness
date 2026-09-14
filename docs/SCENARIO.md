# Proposed synthetic scenario contract — v1.1

Everything in this file is fictional demo input, not a statement about any real
semiconductor supplier or frontier model lab. Names, workload sizes, timing, cost,
and approval limits are proposed defaults to review in Prompt 1. They are not
benchmarks or evidence that a real chip can run the workload.

## Customer story
STRATOS SILICON supplies a custom inference accelerator to HELIOS AI.
The program is in pilot validation before an initial acceptance milestone.
The lab requests additional evidence for a longer-context inference workload.
The supplier must identify the evidence gap, compare approved lab options, secure
SME approval, schedule the work, and keep the internal program plan consistent.

The request changes evidence coverage, not physical circuitry. The outcome of the
new workload test is unknown. Authorization to investigate is not a claim that the
silicon meets the requested performance or acceptance criteria.

## Main identifiers
| Entity | ID |
|---|---|
| Supplier | SUP-001 |
| Frontier model lab | CUST-FML01 |
| Program | PRG-A17 |
| Accelerator | ACCELERATOR-X |
| Current product revision | REV-B |
| Target lab configuration | CFG-B-01 |
| Requirement baseline / proposal | REQ-042-V1 / REQ-042-V2 |
| Change request | CR-017 |
| Existing / requested workload | WF-LC-V1 / WF-LC-V2 |
| Approved supplemental procedure | PROC-LC-02 |
| Suitable test sample / component | SAMPLE-B-017 / UNIT-B-017 |
| Source lot | LOT-4491 |
| Acceptance milestone | MS-ACCEPT-01 |
| Customer order | ORD-1204 |

## Workload change
The same synthetic model bundle MODEL-LAB-07, firmware FW-2.3, runtime RT-4.1,
quantization configuration QFMT-1, memory configuration MEM-1, and single-device lab
configuration remain in scope.

- WF-LC-V1: context bins 8,192 and 32,768 input tokens, concurrency 4 across the
  configured test system, 1,024 output tokens per request, 120-minute total suite.
- WF-LC-V2: context bins 32,768, 65,536 and 131,072 input tokens, the same concurrency
  and output length, 480-minute total suite spanning all three bins.
- This is 480 minutes for the suite, NOT 480 minutes per bin. The seeded procedure
  specifies 160 minutes per target bin. Existing acceptance limits remain unchanged.
- A maximum context number alone does not establish coverage: use the exact approved
  profile, hardware/software configuration, result status, and required duration.

Seed evidence includes a baseline-profile pass on REV-B, a target-profile pass on
REV-A, and a short target-profile run on REV-B. None satisfies the complete target
obligation for CFG-B-01. The service must derive this from the data, not from IDs.
Results bind the configuration, workload, and unchanged criteria content versions
used in the historical run; looking up a revised record cannot rewrite that history.
Record `updated_at` values describe source refresh/import time, not configuration
creation or procedure effective time. The seeded versions existed for the historical
runs. The target workload existed before the customer requested it as a requirement.

## Scenario clock and schedule
Use fixed scenario time 2026-11-16T09:00:00Z. Do not let wall-clock passage make the
recording expire. Audit logs may separately record actual wall-clock timestamps.
Time calculations use elapsed UTC hours, with a deliberately simplified 24/7
engineering-review calendar. Resource movement inside the same lab campus is
included in the setup allowance. There is no external shipping step in this case.

Acceptance evidence/review deadline: 2026-11-19T18:00:00Z.
Customer order delivery commitment: 2026-11-23T18:00:00Z (read-only).
Each candidate test takes 120 minutes setup + 480 minutes execution + 240 minutes
engineering review. Lab reservation covers setup+execution; review follows it.
`starts_at` means reservation/setup start. Execution starts 120 minutes later.
The whole reservation must fit within the slot; intervals are half-open [start, end).
Rates must be approved and effective for the whole reservation interval. Partner
freshness is checked at fixed scenario time, not the future reservation date.

| Option | Reservation/setup start | Review-ready forecast | Incremental cost | Eligibility |
|---|---|---|---|---|
| SLOT-STANDARD | Nov 20 08:00Z | Nov 20 22:00Z | $0 | Qualified setup, but 28 hours after the acceptance deadline |
| SLOT-PRIORITY | Nov 18 06:00Z | Nov 18 20:00Z | $1,800 | Qualified setup, 22 hours before the acceptance deadline |
| SLOT-UNQUALIFIED | Nov 17 06:00Z | Not eligible for selection | $600 | Lab does not support the required approved configuration |

Money is stored as integer USD cents. Cost inputs come from ERP rate records and
availability from lab records. Planning must compute completion and eligibility,
not return a prewritten recommendation. The early option is a feasible response
under the synthetic assumptions, conditional on successful testing and engineering
review. This is not a guaranteed delivery outcome or revenue-saving calculation.

## Permissions and approval assumption
One demo engineering approver is delegated authority to authorize this approved
supplemental procedure and incremental lab spend up to $2,000. This is a simplifying
fictional policy, NOT a universal engineering-approval model. More expensive or
out-of-policy options require escalation; automation cannot approve them.

The approver approves the exact plan, configuration, sample, slot, permitted actions,
source snapshot, and cost. Approved plans are immutable; revisions require a new
approval. A job request must use an actual persisted approval record.

## Baseline state
CR-017 is pending impact assessment; REQ-042-V1 remains the approved requirement.
REQ-042-V2 is a requested revision, not automatically an approved product baseline.
There are no approved implementation plans, approvals, new lab jobs, reservations,
or change-response tasks. The acceptance milestone retains its original baseline.
No seed document contains a canned recommended option or claims a target test passed.
The milestone's pending proposed-evidence dependency is recorded at request receipt
(09:00Z); it flags assessment work and does not approve REQ-042-V2.

### Descriptive context added for the UI follow-up

The existing engineering hold on LOT-4492 is described as a pending pilot-lot
traceability review, owned by Pilot Manufacturing Engineering. Release requires
an authorized disposition in the manufacturing source system; this phase exposes
no release action. This fictional administrative rationale does not assert a
hardware failure. The restriction and sample eligibility are unchanged.

ERP rates now describe standard, priority and alternate lab reservations, including
setup and test execution. Names do not override lab qualification or guarantee an
outcome. Amounts, effective dates, timing and approval policy are unchanged.
The enriched lot and rates use content version 2 in new fixture generations.
Older running databases retain their original source records and may lack this
optional descriptive context; startup never overwrites them.

## End state for this phase
1. An impact assessment and immutable implementation plan have been persisted.
2. A role-authorized demo human decision authorizes a supplemental validation plan.
3. Exactly one scheduled lab job and resource reservation exist for that plan.
4. A planner task/dependency points to the job and the change.
5. The internal conditional forecast reflects the selected option; the baseline
   acceptance date and ERP customer commitment are unchanged.
6. Read-back verifies the exact records. Mutation audit entries connect case, plan,
   approval, job, and planner update.
7. The case is scheduled/awaiting execution, NOT tested, qualified, or customer-accepted.

## Deliberate phase boundaries
No chip redesign, physical simulation, wafer dispatch, MES mutations, ERP order
changes, new acceptance criteria, result authoring by automation, real customer
connections, or claim of yield recovery. A later lab-service simulator can publish
clearly labeled synthetic results, but result simulation is not required to pass
this foundation milestone.

## Authorized portfolio enrichment — Stratos portfolio v1

This section supersedes the earlier single-program dataset scope; the golden
CR-017 business obligation and calculations above remain unchanged.

**STRATOS SILICON / Advanced Compute Programs** supplies custom accelerators and
advanced compute products. **HELIOS AI** is its fictional frontier-model-lab
customer for PRG-A17, now named Helios Atlas Inference. Existing stable IDs retain
compatibility; `CUST-FML01` is an identifier, not a second customer.

The surrounding portfolio has ten additional programs for eight other fictional
customers in cloud infrastructure, networking, inference platforms, HPC, energy
edge computing, robotics and automotive compute. No real company is represented.
See [DATA_ENRICHMENT_HANDOFF.md](DATA_ENRICHMENT_HANDOFF.md) for the full directory.

`fixtures/seed.json` and six authored documents retain the golden inputs.
`src/mock_enterprise/portfolio.py` adds deterministic program templates with stable
IDs under version `stratos-portfolio-1`; it uses no random generator or current
wall-clock input. Each program has four requirement pairs/campaign packages,
current and historical configurations, observations with distinct applicability,
lots/units/samples, two orders, rates, resources and nine milestone gates.
The surrounding concerns describe evidence coordination under approved synthetic
procedures; they do not implement a physical power/thermal/latency simulation.

Initial surrounding history includes 30 immutable plans, 27 decisions, 20 future
scheduled jobs/reservations, ten Planner links/tasks and ten separately imported
historical executions. The historical executions refer to independently authored
result records; booking never creates or modifies observations. Some programs
have full matching historical coverage, others have real gaps in the synthetic
inputs. Neither coverage nor a completed historical job asserts product/customer
acceptance. The completed archive gates refer only to approved baseline packages;
no requested requirement is silently completed or promoted.

397 initial activity records identify source imports and authored synthetic plan
history. Their fixed import timestamps are labeled separately from actual HTTP
mutation audit recording times. These are synthetic source records, not claims of
real staff actions or of an integration script having run. Subsequent real local
HTTP writes still record audit and idempotency receipts transactionally.

Manufacturing holds retain rationale, team and release conditions. The backend
still blocks any recorded restriction; “validation only” does not confer a new
permission to bypass the restriction. No release, execution, result-writing or
commitment-editing endpoint has been added. Historical lab records are immutable.

Only new initialized files or an explicit guarded reset receive this portfolio.
Startup never upgrades, enriches, renames or overwrites an existing database.

## Phase 05 isolated administrative example

The explicit Phase 05 request authorizes a second, low-risk synthetic case and an
incomplete intake. These additions live only in a newly initialized
`.cache/multi-agent-demo/<name>/enterprise.sqlite3`; default fixture initialization
and existing databases remain unchanged. `coordinator/evals/prepare_demo.py` adds
three explicitly allowlisted business documents, CR-018, PROC-BASE-01 and
POLICY-BASE-01. It adds no test result, approval, reservation, job or Planner write.

CR-018 requests preparation of an **internal reference packet** for existing
FW-2.3 / RT-4.1 / CFG-B-01 / WF-LC-V1 baseline evidence. Its baseline and target
both reference the already approved REQ-042-V1. This is an administrative evidence
reference change, not a new firmware/configuration or engineering requirement.
The added procedure describes the historical 120-minute baseline suite, 60 minutes
per bin, allowing the existing deterministic coverage endpoint to assess that
exact baseline. RES-BASELINE-B already supplies the evidence; no result is invented.

DOC-COORD-POLICY-01 is a clearly synthetic, source-recorded policy for this narrow
administrative workflow. It permits only preparing existing evidence, with zero
incremental cost, unchanged approved requirements and sufficient authoritative
coverage. It permits **no business mutations or customer communication**.
POLICY-BASE-01 grants no scheduling actions. All consequential changes still need
the existing exact-plan engineer authorization; CR-017 remains unchanged and uncovered.

The incomplete event has no change/customer/program identity, firmware revision or
requested acceptance date. It remains an intake event, not an invented source-system
change record. The Coordinator must clarify/escalate without retrieving unscoped data.

## Phase 08.4A additive standard package case

CR-019 is a separate Helios request (HELIOS-PACKAGE-2026-11-019) to add the
explicitly approved WF-LC-V1 profile to the upcoming PRG-A17 acceptance validation
package. Both requirement references remain REQ-042-V1; this does not promote
CR-017's proposed requirement. Exact configuration: CFG-B-01 v1, ACCELERATOR-X
REV-B, MODEL-LAB-07, one device, FW-2.3, RT-4.1, QFMT-1, MEM-1. Conditions are
8,192 and 32,768 tokens, concurrency 4, 1,024 output tokens, a 120-minute suite
and 60 minutes per bin. PROC-STD-01 v1 and STD-HANDOFF-V1 explicitly approve this
scope. Applicability is never inferred from a smaller/larger-context comparison.

RES-BASELINE-B is reusable historical profile evidence. SAMPLE-B-017 remains
nominated for standard confirmation work after separate lab authorization. The
intake does not reserve the sample, remove a prior reservation or book capacity.
VALOPS-A17, owned by Atlas Validation Operations, receives the complete package.
Requested package timing is 2026-11-18T18:00:00Z, ahead of the existing milestone
baseline; neither forecast nor customer commitment changes.

Source installation is explicit and additive via `install-standard-case`, with
three allowlisted business documents and `fixtures/standard_change.json`.
The agent workflow stops at verified intake. Testing, engineering result review
and customer acceptance remain pending. Developer-only negative variants live
outside runtime retrieval under `coordinator/evals/phase08_4a/`.

## Additive connected QE-004 scenario (Phase 08.4B)

The explicit [quality recovery request](../prompts/08_4B_QUALITY_RECOVERY.md)
adds source-owned final-test exception QE-004, LOT-B-204, comparable 200/250 versus
960/1000 results, a complete lot quality hold, and 600 eligible units from LOT-B-203.
ORD-HEL-800/MS-HEL-800 are a separate additional 800-unit demand/milestone under
PRG-A17. They do not replace CR-017's ORD-1204/MS-ACCEPT-01. See the
[source map and boundaries](PHASE08_4B_HANDOFF.md). These additions live only in the
explicit Engineering/Manufacturing/ERP/Planner source installation; developer
variants are isolated and do not change the primary fixture.

## Additive connected DR-009 scenario (Phase 08.4C)

[Delivery readiness](PHASE08_4C_HANDOFF.md) reuses ORD-HEL-800/MS-HEL-800 and the
shared QE-004 Manufacturing material. New MAT-B-202/LOT-B-202 has 150 released units
allocated to ORD-HEL-150, so physical 1,000 = eligible 600 + held 250 + allocated 150.
The 800-unit request leaves a 200-unit gap. The primary scope is the approved V1
Engineering baseline; independent CR-017 pending/complete variants exercise V2.
ERP owns DR-009 provenance, exact demand, destination, requested arrival and the
versioned release-commitment head; Planner owns LOG-HEL-800 confirmed durations.
An approved 600-unit release commitment does not erase the original order-level
800-unit obligation/date, constitute customer agreement, reserve/reallocate stock,
or ship goods. Future 300-unit receipts exist only in a conditional developer variant.
Install additively with the local `install-delivery-case` CLI; no running demo reset
or public fixture/reset route. Full IDs, ownership and variant semantics are in the handoff.

## Phase 10 — separate autonomous opening (QE-011)

The [focused touchless request](../prompts/10_TOUCHLESS_CONCURRENT_WORKFLOWS.md)
supersedes the earlier QE-011 human-handoff and app-entry behavior. Explicit
Prepare arms one eight-second Manufacturing event. Publication adds only QE-011,
LOT-B-219, OBS-QE-011, MAT-B-219, ORD-QE-011, MS-QE-011 and the dedicated approved
PROC-QE-011-STD. Existing golden-case facts are unchanged.

LOT-B-219 is ACCELERATOR-X REV-B / CFG-B-01 at packaged final test with FT-B-7.2:
88/100 passed, two sites each 44/50, versus the comparable 96% BASE-FT-B-72.
All 100 units remain held and ineligible; its independent 100-unit demand has a
100-unit gap. Root cause is unresolved. A passing first attempt is not release.
Source scenario timestamps remain fixed November 2026; event/run timestamps are actual UTC.

The existing yield_exception_recovery agents perform scoped investigation.
A deterministic source/host policy permits only routing the approved investigation
tasks to the procedure-bound active Quality queue and owner. Independent HTTP
readback verifies that work item and unchanged protected inputs. Canonical QE-011
creates no recovery plan, Program Owner decision or Planner recovery task.
Planner recovery work remains an exact-human-approval capability, so no new
Planner authority is inferred. QE-004 retains that human-review story.

Ineligible source scope, type, hold, procedure, action, queue, baseline/evidence or
conflicting exception escalates without handoff. RAG is supporting knowledge,
never authority. QE-011 may run alongside CR-017, with separate run contexts.
Reset/replay remains scoped and explicit; startup and navigation stay idle.
See [implementation and validation](PHASE10_TOUCHLESS_CONCURRENT_HANDOFF.md).
