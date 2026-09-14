# Phase 08.3 — Workflows & Automations

The existing control plane now supports workflow discovery, explicit supported
CR-017 invocation, real run history/detail, and durable automation configuration
previews. The current blue gradient, typography, shell and source applications
are retained. [Open Workflows & Automations](http://127.0.0.1:5189/control/workflows).

**Phase 08.3 DOES NOT implement background scheduling, event listening or
condition monitoring.** Opening, refreshing, saving, editing, pausing, resuming
or deleting a configuration never starts a model or changes source business data.
No paid models were automatically run for implementation or verification.

## Reused components

- `application/registry.py` remains the executable capability source of truth.
  Its definitions, dispatch gate and supported operations are unchanged.
- The new manual route calls `ControlHost.start` and the existing
  `WorkflowService`, `ActivityStore`, installed trusted demo actors and CaseHarness.
  It does not introduce an executor, runner or model prompt.
- Existing proposal preparation, exact engineering review, Phase 06 execution and
  independent readback remain in the CR-017 case/Decisions workbench.
- Existing source-owned synthetic lab completion, read-only reassessment and
  separate engineering evidence review remain unchanged from 08.2.1.
- Existing run checkpoints, specialist findings, activity, proposal/review/action
  and verification records supply history. `RunFindings`, `References` and
  `ExecutionDetails` are reused.

## Catalog architecture and mode matrix

`application/workflow_catalog.py` adds presentation metadata over the three actual
registry definitions, plus ten product concepts. It never installs an executor.
The browser uses typed host catalog reads. Its generated fallback JSON is exported
from the same Python catalog; fallback descriptions cannot enable a launch while
the host is unavailable. A regression test detects divergence.

| Capability | Mode | Manual execution | Configuration |
|---|---|---|---|
| Requirement Change Analysis / 1B CR-017 | Connected | Existing scoped investigation; exact review remains separate | Read-only intent; all saved triggers are previews |
| Yield / Quality Exception Recovery / story 2 | Preview | Blocked | Read-only or planned proposal-only intent |
| Delivery Readiness / Commitment Planning / story 3 | Preview | Blocked | Read-only preview |
| Standard Change / Touchless Handoff / story 1A | Preview | Blocked | Read-only preview; no touchless authority |
| Specification Drift Detection | Preview | Blocked | Configuration only |
| Tapeout Readiness Review | Preview | Blocked | Configuration only |
| Platform IP / Errata Propagation | Preview | Blocked | Configuration only |
| Supply & Manufacturing Signals | Preview | Blocked | Configuration only |
| Post-Silicon Bring-Up / Errata | Preview | Blocked | Configuration only |
| Customer Commitment Review | Preview | Blocked | Configuration only |
| Portfolio Risk / Early Warning | Preview | Blocked | Configuration only |
| Scenario / Capacity Planning | Preview | Blocked | Configuration only |
| Next-Generation Requirements Harvest | Preview | Blocked | Configuration only |

There is **one Connected, zero Simulated, and twelve Preview** workflows. The
existing 1A/yield/delivery screens are story outlines, not interactive simulations;
calling them Simulated would overstate the implementation. Their canonical story
labels remain visible. Connected denotes an installed backend capability;
Simulated is reserved for actual interactive demo behavior; Preview means concept
or configuration only. A deterministic model stub is labeled explicitly in test
runs and is not presented as a simulated business workflow.

## Manual invocation and history

The workflow detail offers the current authorized program **PRG-A17 / HELIOS AI**
and existing **CR-017** change. Program operator or Engineering approver must be
selected through the existing demo profile. Read-only viewers can inspect.
The browser posts the same closed invocation contract as the existing case route:
workflow identifier/version, analyze operation, scope and an explicit `ui_*`
invocation ID. No arbitrary prompt, actor, tool or source-write arguments are accepted.

The shared service durably claims the invocation. Same-key retries across either
route recover the same run; a changed actor/body conflicts. Host admission blocks
another start while an investigation is running. The browser retains interrupted
manual-request IDs in session retry metadata and opens the actual created run.
The existing host may prepare a supported exact proposal after investigation;
source execution still requires the existing independent engineering approval.

Run history displays workflow, program/case, initiating actor and trigger,
start/completion times, runtime mode/status, business outcome and actual run ID.
A completed runtime can still mean escalation, waiting for review, rejection,
partial execution, verification failure or physical results pending. Verified
scheduling never means tests passed. Downstream validation completion still leaves
customer acceptance pending. Historical assessment bindings remain historical
when evidence changes; current-source failures remain unavailable.

Run detail shows the business question, actual Coordinator/specialist states,
public findings, source references, persisted event timeline, linked exact
proposals/reviews and execution/readback. Technical IDs and elapsed runtime are
secondary. This adapter does not expose hidden reasoning, raw trace payloads,
filesystem paths or unrecorded token counts. The Operations context link carries
the actual run ID back to this reusable detail; Operations itself remains a preview.

## Automation model and persistence

`application/automations.py` owns strict typed configuration models and an
`AutomationStore`. Records live in `automation-configurations.json` beside the
existing host metadata, separate from `workflow-index.json` and all source data.
It uses the same POSIX lock, atomic replacement, strict parse and fsync conventions.
The execution and source services never consume these records.

Each definition records ID, name, workflow, customer/program/case scope, tagged
trigger configuration, authority intent, notification preference, configured/paused
state, future safeguards, owner/demo actor, version, created/updated timestamps,
updated-by identity and seeded-example provenance. The execution mode is a literal
`configuration_preview`; background execution is a literal `false`, not editable
browser policy. Scope is bounded to the host's installed CUST-FML01 / PRG-A17
membership. CR-017 is required for connected configurations. Other workflow
concepts use program scope; illustrative story IDs are not invented source cases.

Configuration mutations require an installed operator/engineer, local origin and
existing action header. Creates have durable request receipts; update/state/delete
also compare expected versions. Exact retries return original receipts without
reverting subsequent edits. Deleted records retain receipt/tombstone history and
are not resurrected by retries or reseeding. Mutations and important denials are
recorded in configuration-only audit metadata, without raw request bodies.

Three one-time seeded examples are clearly marked: CR-017 Evidence Reassessment
(Validation result event, read only), Morning Delivery Readiness (weekdays at
7 AM America/Chicago, read only), and Yield Exception Watch (quality event, planned
proposal only). These examples do not claim any previous execution or monitoring.

## Trigger editor and authority

The focused modal progresses through workflow/scope, trigger, authority/notifications,
and review. Review lists what the future agent would do, limitations, required human
approval, scope and execution mode. Save stores configuration only.

| Trigger | Stored controls | Runtime behavior |
|---|---|---|
| Manual | Explicit invocation intent | Saving never launches; use connected workflow action separately |
| Scheduled | Daily/weekdays/weekly, weekday, time, IANA timezone, optional start date | Human-readable “Would run”; no next-run timestamp or scheduler |
| Source event | Fixed source-system/event pairs | Trigger preview; listener not active; no webhooks |
| Condition | Allowlisted field/operator/value variants | No arbitrary expression, evaluator or monitoring |
| Chat | Future Concierge intent | No freeform execution or configuration changes from chat |

Event choices cover Engineering requirement/decision updates, Validation result/job
updates, Manufacturing exception/lot changes, ERP order/commitment changes, and
Planner milestone changes. Conditions cover high milestone risk, bounded evidence/
approval/missing-validation hours, and eligible quantity below requested quantity.
Time, calendar date, timezone, event ownership, field/operator/value, thresholds and
scope are validated server-side, including direct API requests.

Future safeguards store deduplication by case/event, no automatic reopening of
resolved cases, duplicate notification suppression, and a bounded minimum recheck
interval. Event deduplication is available only for source-event configurations.
Nothing currently evaluates or enforces a recurring trigger because none executes.

CR-017 configuration authority is **read only**. Proposal-only intent is permitted
only for the clearly non-executable yield concept. Bounded execution configurations
are rejected. Saved authority cannot modify any Phase 06 policy, exact manifest,
source permission or human approval. Notifications are preferences only; there is
no sender. Configured and Paused describe configuration state, never an active worker.

## Host surface

All new routes are under `/control-api`, using the existing loopback/origin/demo
identity boundary and sanitized errors. The unchanged case read also includes
catalog/configuration metadata so the shell refreshes one coherent view.

| Method / route | Behavior |
|---|---|
| GET `/workflows`, `/workflows/{workflow_id}` | Registry-derived catalog and latest recorded run |
| POST `/workflows/{workflow_id}/runs` | Existing supported CR-017 invocation only |
| GET `/runs`, `/runs/{run_id}` | Scoped actual history and run/activity detail |
| GET `/automations`, `/automations/{automation_id}` | Scoped saved configurations |
| POST `/automations` | Create configuration with request ID |
| POST `/automations/{automation_id}/update` | Replace editable configuration with version check |
| POST `/automations/{automation_id}/state` | Pause/resume configuration with version check |
| POST `/automations/{automation_id}/delete` | Delete configuration with version check |

See [typed host OpenAPI](phase08-3-host-openapi.json). No generic tool invocation,
source write proxy, direct browser MCP, webhook ingestion or scheduler API exists.
To regenerate the browser fallback and schema:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python scripts/export_phase08_catalog.py
mock_apps_ui/node_modules/.bin/openapi-typescript docs/phase08-3-host-openapi.json -o mock_apps_ui/src/control/host-schema.d.ts
```

## Shell integration

Global metadata search finds workflows, saved configurations and actual runs with
detail links. Overview adds a concise configuration count with the preview boundary.
Alerts still use actual source/run/review/verification signals; creating a definition
adds no scheduler alert. Concierge gets workflow/automation/run context and relevant
suggested questions while replies and actions remain explicitly Preview.

## Verification and preserved working state

See [verification record](PHASE08_3_VERIFICATION.json) for actual commands, results,
changed files and preservation hashes. [Screenshots](phase08/workflows/screenshots/README.md)
cover catalog, connected detail, schedule/condition editor, review, saved list and
actual run history/detail. Browser verification is **scripted integration testing**
with deterministic model stubs and simulated demo profiles, not an AI run or an
actual human approval. All test databases and metadata are isolated.

The existing manual demo uses UI 5189, source API 18028, MCP 19084 and host 18084.
The source database, original completed investigation, approved plan, booked lab
job and verified Planner handoff are retained. The owned idle host was restarted
to load this phase, after a backup and preservation comparison. Existing
source/MCP/Vite processes kept their data and ports. The original workflow index
is byte-for-byte unchanged; cases, proposals, activity and downstream state match
the pre-change read. The original job has no physical result or engineering
evidence review yet, so its run shows **Physical result pending**. The three new
seeded records are automation configuration previews only.
The existing [08.2 launch commands](PHASE08_2_CONNECTED_HANDOFF.md) still apply.

Actual checks completed:

- Source suite: **403 passed**. Coordinator suite: **615 passed**, including the
  54 new Phase 08.3 tests. After final catalog/schema cleanup, those **54 tests
  passed again**.
- Phase 07 offline evaluation: **40/40**, no critical failures. TypeScript and
  production build passed.
- Browser coverage: **56 legacy and 8 connected checks verified** across full
  suites and targeted reruns. The last legacy full suite was 55 passed/1 failed
  after a page/context/browser closure; that check passed on targeted rerun.
  The connected suite was 6 passed/2 failed on test selectors/profile setup;
  both corrected checks passed on targeted rerun. This is not a claim of one
  clean combined 64-test invocation. Details and logs are in the verification
  record.
- The working demo passed read-only Chrome inspection with no POST requests or
  browser errors, including a 760 px viewport and 200% zoom without horizontal
  document overflow. Catalog, run, schedule, review and condition captures were
  visually inspected.

Changed implementation files are concentrated in the two new application
metadata modules, the host catalog/configuration/run routes and projections, and
the new `workflows.tsx` / `automation-editor.tsx` surfaces. Shell integration,
generated catalog/schema, focused tests, prompt archive and handoff documentation
are also updated. The verification record lists each file and screenshot; it was
built from phase-start hashes without using Git. Regression screenshots are saved
under this phase rather than overwriting prior handoff captures.

## Limits and exact next step

No paid model run, real microphone, external notification or background trigger
was exercised. Future definitions cannot execute; no source or MCP permissions,
agent prompts, approval policies, fixtures, Phase 06 implementation or Phase 07
graders were changed. Host metadata is local and file-backed, not a multi-user
production service. Configuration scope is deliberately the installed PRG-A17 host
scope, even for future portfolio concepts. No Git operations were performed.

**Stop at 08.3.** The exact next **08.4** slice is interactive scenario stories 1A
standard/touchless, 2 yield/quality recovery, and 3 delivery readiness in an isolated
simulation namespace, with explicit simulated outcomes and shared scenario entities.
Only then should those entries become Simulated. It does not authorize production
executors, source mutations or activation of these trigger configurations. A later
activation phase must install a supported workflow, independently validate authority,
resolve current scope/evidence, implement durable trigger consumption/deduplication,
and route every real invocation through the same service; saved intent alone is
never sufficient. Connected freeform Concierge remains 08.5 and Operations 08.6.

### Browser corrections verified during this slice

Configuration selects have explicit accessible names, and editor actions stay in
the dialog footer while longer forms scroll. After a mutation, the host UI waits
for any older in-flight read and fetches again before enabling another action.
The schedule test deliberately holds an old response across an edit to verify
that the next pause uses the current version. This fixes a real stale-read race;
the server's optimistic check correctly rejected the earlier stale request.
Tests also wait for successful navigation before reloading a newly saved record,
use actual accessible control names, and avoid clicking behind an open modal.
