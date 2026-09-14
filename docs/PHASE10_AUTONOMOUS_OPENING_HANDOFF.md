# Phase 10 — Bounded autonomous opening

> **Historical handoff:** the latest [touchless/concurrent refinement](PHASE10_TOUCHLESS_CONCURRENT_HANDOFF.md) restores explicit Prepare, removes the canonical QE-011 human decision, and admits independent concurrent runs. Its verification record is current; the original results below remain historical evidence.

**Later UI refinement:** the [processing/idle follow-up](PHASE10_AGENT_PROCESSING_STATES.md)
keeps unused stations visible and muted. Active processing alone gets a blue station
and moving colored dots. The original implementation/verification record below
retains its historical roster description; runtime and authority are unchanged.

The [explicit request](../prompts/10_AUTONOMOUS_OPENING.md) is implemented as one
connected event-driven demo path. Explicit preparation arms a synthetic
Manufacturing event; the event starts the existing quality workflow. Navigation,
normal startup, restart and saved generic automation configurations never launch it.
Verification uses isolated source/metadata stores, real local HTTP/MCP boundaries
and deterministic SDK doubles. **No paid models, real speech, hosted indexing or
Git operations were run. Live model quality and latency for QE-011 remain unverified.**

## 1. QE-011 source data

`fixtures/autonomous_quality_exception.json` is an explicit publication input, not
part of normal seed/startup. One source transaction creates six owned records:

| Record | Facts / ownership |
|---|---|
| QE-011 | Manufacturing final-test anomaly, PRG-A17 / CUST-FML01, CFG-B-01 |
| LOT-B-219 | Manufacturing ACCELERATOR-X / REV-B lot, quality hold |
| OBS-QE-011 | 100 tested, 88 first-pass passes, 12 failures; FT-B-7.2; two sites 44/50 each |
| MAT-B-219 | 100 physical and held, 88 first-pass passes, zero released / eligible / allocated |
| ORD-QE-011 | Separate 100-unit synthetic ERP planning demand |
| MS-QE-011 | Separate Planner milestone linked only to that demand |

Existing approved BASE-FT-B-72, PROC-QE-B-01 and RES-BASELINE-B are read references.
Ordinary quality domain code calculates 88% versus the 96% comparable baseline,
zero eligible supply and the dedicated 100-unit gap. Root cause is unknown.
A first-pass pass is not a release. No alternate supply is borrowed from QE-004.
The original program/milestone/order records, CR-017, CR-019, QE-004 and DR-009
remain unchanged. DR-009 still uses its 600 / 800 / 200 story and never depends on
QE-011. QE-011 is excluded from the four golden scenario tiles/evaluation cases.

The source records use the existing fixed UTC **scenario** chronology (November
2026). Event receipt and run times use actual UTC wall time. The timestamps have
different purposes; this synthetic demo does not represent a real incident date.

## 2. Source event contract

`enterprise_api.quality_events.QualitySourceEvent` rejects extra fields and fixes
`event_name=quality_exception_created`, `event_version=1`, `exception_id=QE-011`,
`program_id=PRG-A17`, `customer_id=CUST-FML01`, `lot_id=LOT-B-219`,
`source_system=manufacturing`, `source_record_version=1`, and `synthetic=true`.
It also carries `event_id`, `source_record_updated_at`, the source-computed
`context_digest`, and explicit UTC `event_timestamp`.

Manufacturing atomically persists the event and records in its existing SQLite
store, using the existing demo metadata row for the single immutable event. The
control plane stores a receipt, invocation/run metadata and existing workflow
findings/governance state. It does not become the source of lot or test facts.
The source read is `GET /api/v1/manufacturing/quality-events/{event_id}`, protected
by existing source identity and exception scope. There is no public publisher,
webhook, new MCP tool, new database or broker. Independent HTTP context/readback
validates the receipt before dispatch. Colliding owned IDs roll back publication.

## 3. Trigger dispatcher architecture

`control_host/autonomous.py` is a small host service, enabled only with the existing
explicit local demo-management binding. Prepare verifies that binding and the main
baseline, checks runtime readiness without a model call, saves one armed generation,
and schedules exactly one eight-second in-process wait. The waiter invokes the
source-owned synthetic publisher and then dispatches its authoritative event.

Dispatch accepts only the supported contract, currently armed generation/epoch and
source-matching version/digest. It has no arbitrary event-to-workflow routing,
generic tool execution, event polling or user script. An old, changed, forged,
unsupported or unarmed event fails closed. Errors are visible; there is no automatic
retry or reassessment. Process interruption does not replay the timer or agent run.

## 4. Existing workflow invocation

The mapping is exclusively `quality_exception_created → yield_exception_recovery`.
The dispatcher calls the same `ControlHost.start → WorkflowService → CaseHarness
→ QualityRecoveryService` path used by manual QE-004. The quality service accepts
QE-004 or QE-011 explicitly and obtains each context through source HTTP. Existing
Coordinator, Manufacturing, Validation evidence and Program & Commercial agents,
scoped MCP reads, policy checks, activity persistence, source transactions and
independent readback remain in use. There is no second runtime or mock live path.

A source context is rechecked at invocation admission. The existing one-active-run
admission rule remains: an unrelated active run causes refusal, not an implicit
queue or cancellation. Opening a case, polling a run or inspecting Operations has
no model invocation side effect. QE-011 has no manual “Run investigation” button.

## 5. Idempotency

The invocation key is `ui_event_` plus a deterministic digest of
`[event_id, event_version, yield_exception_recovery]`. The existing durable workflow
claim and admission lock handle simultaneous or later redelivery. One event version
claims at most one run and the existing source idempotency prevents duplicate
investigation/plan/task records. Repeated source publication with the same ID
returns its original immutable event. A different ID cannot overwrite it.

Only event/source version 1 is supported in this slice. Version 2 does **not** launch
reassessment. Explicit reset and preparation create a fresh event ID; the previous
receipt, workflow state and source artifacts are archived by existing reset logic.
Older invocation hashes preserve compatibility by omitting absent new trigger fields.

## 6. Agent Workspace

Overview uses existing run-state polling and persisted checkpoint observations.
An internal pending-event read hint temporarily selects the existing active polling
cadence; it displays no pre-event business activity and never calls a model.
Before publication an empty workspace says “No active investigation.” A new active
run becomes the automatic selection, while an explicit user run selection is kept.

Only agents with actual task participation appear beneath the Coordinator. The
observed QE-011 double invokes three specialists; Change impact is absent. Colored
Coordinator branches and dots animate only for fresh, working tasks in an active
run. Idle, completed, failed and stale activity stops moving. Reduced motion is
honored; there are no specialist-to-specialist connections or architectural legend.
Counts and observations retain their selected-run scope and provenance.

The demo control’s Open Overview link scrolls to Agent Workspace for pacing.
The shared polling lifetime was corrected so completion cannot leave workspace
reads incorrectly marked as an identity change. Needs attention omits QE-011 during
investigation and shows its own source quantities when the handoff is ready.

## 7. Human handoff

The connected workflow routes permitted standard investigation metadata and prepares
an exact recovery plan, then waits for **Program Owner** review. The business view
shows QE-011 / Final-test anomaly and the workspace says “Awaiting Program Owner
review.” Operations exposes the actual state. Completed agents no longer appear busy.

Automation cannot approve its own plan. Existing immutable plan/version/digest,
current source and actor checks apply to QE-011 too. A separate explicit Program
Owner decision may authorize the existing Planner recovery metadata operation;
this still does not release material, change quality disposition, test criteria,
recipe, allocation or customer commitments. Quality disposition remains a separate
Manufacturing/Quality authority. The event path never issues review or execute calls.

## 8. Controls, reset and replay

Operations → Demo controls provides **Prepare autonomous opening** and **Reset
autonomous opening**. These demo-only actions require the existing Program operator
profile, maintainer marker, allowed Origin/action header, exact current epoch, local
source binding and guarded storage. Mock identities are not production authentication.
Prepare resets only QE-011, validates the four-case baseline, arms one event and
returns “Autonomous demo armed.” It does not directly call the workflow.

`GET /control-api/demo/autonomous` reports Idle, Armed, Event emitted, Workflow
running, Human handoff ready or Failed. The same observation appears in harness
status/readiness. Demo state is separate from business quality state.

Both Full Demo Reset and scoped QE-011 reset cancel and await the pending timer and
QE-011 run. In-flight synchronous source publication/postprocessing is drained
before source reset; Python thread cancellation alone is not treated as completion.
A reset already waiting for publication prevents a new workflow from launching.
Existing reset archives/removes only owned source and generated workflow records,
reconciles metadata, removes the event and advances the epoch. Pending writes/cards,
reads, selections and Concierge drafts become stale. Scoped autonomous resets
preserve the selected demo persona; full reset retains its existing sign-out behavior.
Unrelated active work is not cancelled. A reset failure remains visible and requires
explicit recovery. CLI `./scripts/demo reset --scope QE-011` uses the same boundary.

Replay: prepare → wait for handoff → scoped reset → prepare again. Exactly one
current run remains after the second opening; the previous run is archived. Neither
normal restart nor navigation re-arms it.

## 9. RAG

The existing optional Manufacturing/Quality retrieval profile can use the approved
hold SOP, approved excursion procedure and labeled historical investigation guidance.
No new corpus, provider, vector store or automatic indexing was added. Source facts,
exact document versions and policy remain authoritative. Retrieval failure is not
invented knowledge and does not prevent the event from launching.

Deterministic integration explicitly indexes allowlisted business documents, queries
all three Quality knowledge paths, and verifies PRG-A17/profile/run/case provenance
and exact source versions. The four original conclusions remain unchanged with
retrieval enabled. Developer acceptance fixtures and this report are not indexed.

## 10. Operations and workflow catalog

Run History and Operations identify **Manufacturing source event**, event name,
ID/version, QE-011, actual participating agents, observable tools/RAG and final
human handoff. They expose no hidden reasoning. QE-011 source links open its actual
Manufacturing Portal detail. The event run is not labeled “User initiated.”

The quality workflow now says its bounded QE-011 source event is connected.
Manual QE-004 remains connected. Saved generic source-event, schedule and condition
configurations remain configuration-only; their background activation is unchanged.
No DR-009 scheduled runner or broad event listener was installed. QE-011 is not an
additional freeform Concierge launch/approval capability; use its case and Operations.

## 11. Verification

| Check | Actual result |
|---|---|
| Source/backend suite | 494 passed |
| Full coordinator suite | 836 passed |
| Additional partial-reset regression (added after full-suite collection) | 1 passed |
| MCP suite | 56 passed |
| Canonical offline workflow/Concierge evals | 112/112 passed, no critical failures |
| Shared retrieval gates / canonical comparison | 15 passed, all four conclusions unchanged |
| Quality corpus | 12/12 gates passed, 14 underlying test observations |
| Browser journeys | 21 passed: 14 workspace, 2 autonomous, 4 knowledge, 1 reset |
| TypeScript / Vite production build | Passed |

Focused runs overlap these suites and are not added to the unique totals. Source,
coordinator and MCP test commands used separate cache storage. The final partial-reset
regression independently verifies error response epoch invalidation, disarm and
explicit recovery. The initial two coordinator failures and other corrected checks
remain recorded in the manifest; final results above are the successful reruns.

See [the verification manifest](PHASE10_AUTONOMOUS_VERIFICATION.json) for exact
commands, final results and prior failures. Tests cross real local HTTP/MCP and SDK
boundaries using deterministic model/speech doubles. They are scripted integration
testing, not a paid AI run or evidence of an actual human approval.

The new source/host coverage includes atomic publication and rollback, authority,
delay without direct invocation, startup/navigation idle, exact event scope,
authoritative mismatch/stale context, concurrent redelivery, real participation,
review only after completion, self-approval denial, exact human review, scoped/full
reset during work, reset during source publication, repeat reset and replay,
source baseline preservation and scoped RAG. Existing suites/eval hard gates remain.

The browser journey covers the complete requested sixteen-step demo, then an
additional pre-event cancellation/navigation check. It inspects the source portal,
case, Operations/RAG and responsive 1440×900, 1920×1080, 1280×800 and 390×844 layouts.
Workspace regressions cover stale/failed/idle motion, selection, hidden-page polling,
keyboard inspection, reduced motion, persona and reset. Existing reset and knowledge
browser journeys are also run. [Screenshots](screenshots/phase10-autonomous/) are
explicitly deterministic test evidence.

## 12. One optional paid live demonstration — not run

Use an existing supported dedicated demo, its configured model credentials and the
[runbook](DEMO_RUNBOOK.md). After code changes, stop/start that owned demo to rebuild
its production preview; startup alone stays idle. Do not run two hosts on one store.

```sh
./scripts/demo stop       # only the owned demo selected by this harness
./scripts/demo start      # rebuild, start services; no model calls
./scripts/demo prepare    # explicit full-reset confirmation and readiness check
./scripts/demo status
```

Open the printed Overview URL, log in as Program operator, and go to Operations →
Demo controls. Optionally use the existing explicit Knowledge indexing control first
if its index is not current; this is separate from event preparation. Click
**Prepare autonomous opening**, read the live-runtime cost disclosure, then
**Open Overview →**. Before eight seconds there is no QE-011 agent activity. After
the source event, watch the actual connected investigation and eventual Program
Owner handoff; actual latency/failures depend on the existing API runtime. Inspect
QE-011 and its Operations run for source, agent/tool/RAG and event provenance.
Do not approve/execute for the autonomous opening story. Reset autonomous opening
when finished. A second preparation is a separate paid run.

`./scripts/demo prepare` does not arm this event by itself. The explicit UI control
is necessary. No paid verification was silently triggered as part of implementation.

## 13. API-cost safeguards

One preparation permits one event and one bounded invocation. Repeated reads,
navigation, redelivery and restart do not create another paid run. The control
shows a live-runtime disclosure. Configuration checks inspect credential presence
without printing it or sending a model request. Existing limits remain: default
12 turns per specialist invocation, 10 Coordinator turns, 8 specialist calls,
depth 2, one reconciliation round, 80 tool calls, 45-second tool timeout,
300-second specialist timeout and 900-second run timeout. Configured values may
differ within the existing bounds; this is not a fixed dollar spending cap.

A Coordinator plus three specialists can make multiple model requests. Existing
bounded SDK retries/reconciliation may consume usage. Optional hosted retrieval
uses existing explicitly configured services. Do not promise a cost, instantaneous
completion or production reliability. Inspect actual usage metadata where available;
missing usage is unknown. Reset stops local orchestration but cannot refund an API
request already sent. There is no new automatic retry after trigger failure.

## 14. Known limitations

- One fixed case, event/version, scope and eight-second delay; no generalized reassessment.
- The one-shot timer is in-process. Host interruption fails visibly and requires
  explicit reset/preparation; it is not a durable scheduler or production listener.
- A changed main demo baseline must be explicitly restored before preparation.
  Preparation cannot silently repair/reset the four golden stories.
- Existing single-run admission may reject an event when another investigation starts
  during its delay. It does not queue or interrupt that unrelated work.
- The source demo publisher requires a verified local source/storage binding. It is
  deliberately unavailable through agent tools or public business writes.
- Model output, live latency and API cost have not been validated for QE-011. Offline
  doubles exercise actual orchestration/checkpoints but are not live-model evidence.
- Polling displays observed checkpoints, not continuous model internals or utilization.
  Missing/stale workload remains unknown. Event emitted may be brief in the UI.

## 15. Production evolution and talk track

A production integration would replace the explicit synthetic publisher/timer with
an authenticated enterprise webhook or durable event bus/outbox consumer. It would
validate a versioned contract and tenant scope, then use the same dispatcher and
shared workflow invocation boundary. Durable delivery acknowledgments, a unique
persistent event/version/workflow claim, retries/dead letters, worker leases,
observability and real identity are necessary additions. Business approvals,
source-owned policy, exact manifests and independent readback would remain.
This slice does not implement those infrastructure capabilities.

> A quality exception arrived from the manufacturing system before I opened the
> control plane. That enterprise event automatically started our existing Yield /
> Quality Recovery workflow. The agents can investigate and prepare the response
> autonomously. When they reach a consequential decision, the workflow stops and
> brings in the accountable human.

Prepare and wait at least eight seconds before opening Overview when using the
first sentence literally. Alternatively open it immediately to show the idle-to-active
transition. Describe this as a **bounded connected event-driven demo path**, not a
continuously operating production system. Stop here; no other saved automations,
scheduler, workflow family or Git packaging is authorized by this implementation.

## Review preview left running

[Open the deterministic preview](http://127.0.0.1:5211/control/overview). It uses only
`.cache/phase09-3/phase10-autonomous-review-20260912-a`, was independently checked as
Idle with zero runs, and does not replace/reset the user's working demo. Log in as
Program operator → Operations → Demo controls to exercise the no-paid-model opening.
The test-mode disclosure is visible. The preview is not a live AI demonstration.
