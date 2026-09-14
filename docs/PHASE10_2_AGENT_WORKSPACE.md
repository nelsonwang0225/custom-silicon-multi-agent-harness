# Phase 10.2 — Visual Agent workspace

**Current refinement:** the [processing/idle follow-up](../prompts/10_AGENT_PROCESSING_STATES.md)
keeps the full roster visible. Only fresh, observed processing gets a blue active
station and moving colored Coordinator dots. Known unused/completed stations are
muted Idle; completion remains in task history. Stale/unknown activity stays uncertain,
with no motion. This supersedes the prior participating-only display from the
[autonomous opening](PHASE10_AUTONOMOUS_OPENING_HANDOFF.md). Explicit selections,
source authority and polling/freshness rules below remain applicable.

This is the current Agent workspace requirement, superseding static role tiles and historical Preview-only agent presentation. The [approved request](../prompts/10_2_VISUAL_AGENT_WORKSPACE.md) preserves the [Phase 10.1 capability contract](PHASE10_1_PERSONA_ACCESS.md), existing workflows, source ownership, exact approvals and reset. No workflow/runtime authority changes.

## Current monitoring refinement

The user-approved compact monitoring follow-up supersedes the tiered stage below: a Coordinator above four specialists, measured relationship lines with outward dots for freshly observed working specialists, scoped observed workload counts, latest task observation strip, and existing handoff/inspectors. See [monitoring refinement](PHASE10_MONITOR_REFINEMENT.md). Checkpoint timestamps are not duration or transition history. All authority and read contracts below remain in force.

## Original composition and exploration

Two explicitly illustrative React/Lucide prototypes were built and opened in the local browser: [A, Agent stage](screenshots/phase10-2/concepts/agent-stage.png), and [B, Agent ensemble](screenshots/phase10-2/concepts/agent-ensemble.png). [Side-by-side exploration](screenshots/phase10-2/concepts/comparison.png) and editable sources live in `phase10-2/concepts/`.

The Visualize skill was available and read, but tool discovery exposed no callable Visualize tool. The existing frontend stack was the requested fallback; no external design provider was invoked.

**Choice: Agent stage.** A focal Coordinator and four compact specialists communicate delegation and parallel participation more clearly than five equally weighted ribbon entries. The shipped stage uses a shallow layout so the handoff remains visible at 1280×800. Only the stage ships in the application; the two concepts remain developer documentation.

Agent workspace is the wider left surface on Overview; Needs attention remains on the right. The subsequent [navigation and layout refinement](PHASE10_NAV_LAYOUT_REFINEMENT.md) places Programs immediately after the Overview summary, then this pair in matching white bordered panels. This supersedes the initial placement of Programs below the stage and the initial above-the-fold expectation for that row. Preserve the existing light-blue masthead, hero and Concierge. Default content contains names, short observed state, a compact run selector and one handoff line. No role-description paragraphs, task table, percentages, healthy-agent count or synthetic progress. Native system type: 23px heading, 15px names, 13px states, 14px footer. The nodes are borderless buttons around outlined identity icons, with categorical rings and shape/text markers. Specialist nodes reflow to two columns at narrow container widths; relationship lines disappear instead of becoming ambiguous. Inspectors use the existing native dialog and keyboard behavior.

## Read contract and scope

`GET /control-api/agent-workspace?run_id=<id|all>&customer_id=CUST-FML01&program_id=PRG-A17` is a host-only **read projection**. Parameters default to the installed scope. Omitted run chooses an actual active run, otherwise the latest recorded run, otherwise known idle. `all` shows permitted active activity. The response includes scope, read timestamp/TTL, observation TTL, permitted counts, runtime/health observations, run references, five agent identities, invocation observations, findings/evidence/dependencies, source-bound handoffs and permitted links.

The existing capability resolver and Overview surface gate apply. Runs and case parents must both match the installed customer/program, and the case must be one of CR-017, CR-019, QE-004 or DR-009. Filtering occurs before sorting/counts. Unknown scopes/profiles fail closed; guessed/out-of-scope run IDs return no record. Only the operator gets View run/Operations links. Other permitted personas retain business findings, evidence and Open case. No trace IDs, raw tool payloads, model questions/rationale, tokens, private review diagnostics or chat transcripts are projected.

Sort by active first, start timestamp descending, run ID descending as a stable tie breaker. Return the latest 24 plus any active runs and the exact selected run. Counts cover all permitted runs, not merely the displayed subset. A17 scope is explicit; P01/P02 program panels say Not connected and never borrow A17 findings. The host reads the existing ActivityStore and validated checkpoint files; it creates no monitoring database and invokes neither source APIs nor models on render.

## Exact telemetry mapping

| Display / field | Existing authoritative observation | Meaning and limits |
|---|---|---|
| Five identities | Persisted `Role` IDs: `coordinator`, `change_impact`, `validation_evidence`, `program_commercial`, `manufacturing` | Display aliases shorten names; Concierge is not a sixth specialist. |
| Active / recorded run | `RunRecord.status`, `started_at`, `completed_at`, `execution_mode`, scope/case IDs | Terminal results are historical observations, not ongoing computation. |
| Checkpoint observation | Host checkpoint file modification time after validating `CaseState` run/case/customer/program/change IDs | Host observation time, not a task duration or continuous model heartbeat. Missing/invalid/symlink/oversized checkpoints are unavailable. Maximum file size is 4 MB. |
| Coordinator activity | Running RunRecord plus `CaseState.workflow_stage` | `specialists` → With specialists (delegated, no working animation); `triage` → Scoping work; `reconcile` → Reconciling findings; `synthesis` → Preparing assessment; otherwise Investigating. |
| Specialist activity | `requested_specialists[].status`, `specialist`, `invocation_id`, typed `result_kind` | Running → Investigating; the narrow validation clarification kind → Clarifying evidence; pending → Requested; completed/failed/cancelled retain distinct categories. No inference from tool arguments or private rationale. |
| Finding / evidence / dependency | Matching `completed_assessments[].invocation_id` and typed assessment; Coordinator's recorded recommendation | Preserve each invocation separately, original source IDs/content and record versions. At most 16 evidence references and four unresolved questions per task in this compact projection. No fresh model summary. |
| Failure | Failed invocation / terminal RunRecord | Red task marker, never “agent offline.” Other completed findings remain. A terminal run cannot leave an unfinished invocation animated. |
| Participation connectors | Observed invocation caller and specialist, excluding merely pending requests | Static links only for actual Coordinator participation. No packet/transfer animation or implied universal graph. |
| Running freshness | Checkpoint observation within 90 seconds of host read (future skew over five seconds invalid) | Older active observations → uncertainty. Polling cannot turn an old checkpoint into fresh evidence. |
| Read freshness | Snapshot `read_at`, 30-second TTL | Hidden pages or expired reads stop active motion. Historical completed findings remain labeled recorded. Idle requires a current successful scope read with no active run. |
| CR-017 handoff | Existing execution record's exact proposal ID/version/digest and execution status | Waiting approval → Awaiting Engineering review; approved → Host execution pending; completed execution → Scheduling verified, physical evidence remains separate. |
| CR-019 handoff | Existing standard handoff record, verified intake ID and handoff version | Handoff verified · Lab authorization pending. Never implies scheduling, tests or acceptance. |
| QE/DR handoff | Existing recovery/commitment progress, exact plan ID/version/digest, source decision and verified execution status | Program Owner review, host execution, or verified metadata with disposition/customer agreement still pending. |
| Awaiting your review | Current source-backed shared decision summary, matching run **and exact ID/version/digest**, `needsYourReview` capability predicate | Current actor must be eligible for this exact pending decision. Otherwise informational handoff text; no new approval controls in the stage or inspector. |
| Host | Successful current adapter response | Available at the stated read time; no continuous uptime claim. |
| Model | Existing host mode and permitted completed `live_model` run metadata | Deterministic test runtime, or Not checked. Last completed model run is separate. No credential read or paid connectivity probe. |
| Sources | Existing cached explicit Operations health checks | Five sources listed separately. Fresh success requires actual Available check timestamp within 300 seconds. No checks → unknown, not 0/5 healthy; 5/5 requires five recent successes. |

The footer is a **recorded handoff**, not an authorization token. The current case/source decision remains the authority for readiness and execution. A running investigation has no completed-work handoff. Observation timestamps and source version references remain available in details; ordinary rendering never approves or executes.

## Selection, motion and interaction

Selection stays fixed during inspection. All activity aggregates active task counts only; expanded details separate each case/run, with explicit Inspect this run. Findings from different runs are never synthesized into one narrative. Completed specialists keep green checks while human/external handoff sits outside the agent group.

Only freshly observed working nodes get a restrained blue outline pulse. Delegated work, historical completion, failure, uncertainty, hidden pages and reduced-motion preferences have static equivalents. The stage and handoff announce meaningful state changes through polite live regions. Focus/Enter opens the inspector; Escape closes it and restores focus. Touch does not depend on hover.

Clicking an agent only reads existing state. Explain in Concierge navigates to the permitted case and appends one editable draft scoped to the chosen agent/run. It does not send, invoke or approve. Returning to the route does not append the same request again. Current persona remount and demo reset clear selections, dialogs, drafts and old links. In-flight requests are guarded by request serial and the existing identity lifecycle.

Selected active runs (or All with active work) refresh every three seconds while visible. Completed selections have no repeating workspace poll. Shared host run/status/outcome changes may trigger one read to discover new work; focus/visibility return and explicit Refresh can re-read. A one-shot expiry timer marks old reads uncertain without polling them indefinitely. This workspace does not replace the existing broader host read cadence or install any worker.

## Preservation and limitations

Exact business execution, human review, source APIs, fixtures, prompts, MCP permissions, SDK orchestration, eval definitions/graders and working databases are unchanged. No new agents, runtime dependencies, schedulers or paid calls. A regression check identified and corrected a pre-existing React StrictMode mount guard in Concierge send/confirmation: effect setup now re-enables the mounted guard, while real unmount still rejects late updates. This preserves the existing confirmation boundary.

Telemetry is checkpoint-level, not token streaming or a heartbeat. A long invocation with no new checkpoint becomes uncertain after 90 seconds until a newer observation arrives. The API is limited to the installed A17 workflows; the source portfolio still has three programs. Historical handoffs can differ from current case state and are labeled accordingly. No model connectivity or reasoning-quality claim follows from these offline tests.

See [handoff and verification](PHASE10_2_HANDOFF.md), [screenshots](screenshots/phase10-2/README.md), and the [runbook](DEMO_RUNBOOK.md#phase-102-agent-workspace-preview).
