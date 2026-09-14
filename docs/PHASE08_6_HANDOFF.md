# Phase 08.6 — Operations and integrated verification

Implemented from [the approved request](../prompts/08_6_OPERATIONS.md). Operations
is a secondary workbench at `/control/operations`. Overview remains the landing
page. No new agents, schedulers, source permissions or workflow authority were
introduced. Phase 09 has not started.

## Architecture and existing records

The React Operations page uses thin typed GET endpoints on the existing local
control host. The host projects its existing `ActivityStore`: cases, runs,
activities, proposals, exact human reviews, action attempts, verifications,
standard handoffs, quality recovery and delivery commitment progress. Existing
`AutomationStore` configurations remain inactive. No new business source store
or trace service exists.

Initial Operations reads and explicit run refreshes reuse `ControlHost.snapshot`
and the same source-grounded cards used by Concierge. This carries current
proposal staleness and business quantities into Operations. Historical evidence
references remain identified as the recorded investigation's basis. Engineering,
Validation, Manufacturing, ERP and Planner retain ownership of business facts.

The source/backend handlers, contracts, fixtures, MCP permissions, deterministic
business policies and governed execution services are unchanged. Lightweight
polling reads existing metadata only; it never starts a model, source mutation,
reconciliation or workflow.

## New read/index adapters

All routes inherit the existing local-origin/host guards, demo-reader scope and
no-store response behavior. No browser parameter selects a filesystem path.

| GET under `/control-api` | Projection |
|---|---|
| `/operations` | Runs, source-current outcome checks, known eval summaries/history, session summaries, last source-health observations, runtime mode |
| `/operations/runs` | Persisted run state only, for lightweight polling |
| `/operations/runs/{run_id}` | Scoped run, actual participation, evidence, tools, timeline, decisions, execution/readback and current business context |
| `/operations/sessions/{session_id}` | Bounded historical visible conversation and structured confirmations |
| `/operations/health` | Explicit scoped source reads; updates only in-memory read-health observations |

The generated host schema and TypeScript declarations include these contracts.
Existing `/control/runs/{id}` routes now show the Operations detail, preserving
links from Workflows and Concierge. Case pages add a subtle latest-run link.

## Run history and state semantics

The table filters by workflow, program, case, runtime state and date range. It
shows actor, invocation source, start, duration when available, runtime state,
business outcome, decision, verification, model when available and business run ID.

Runtime completion means the investigation ended; it does not mean that a
business action succeeded. Examples covered by tests:

| Runtime | Business outcome |
|---|---|
| Completed | Escalation required |
| Completed | Waiting for human review |
| Completed | Handoff verified; lab authorization pending |
| Completed | Partial execution |
| Completed | Not verified; readback mismatch |
| Failed | Investigation incomplete, with any observed writes shown separately |

Current staleness comes from the same source read as the case workbench. Metadata
poll results are persisted observations; explicit detail refresh checks sources
again. No polling can approve, execute or repair a run.

## Run detail and business linkbacks

The detail contains the original question when its checkpoint exists, scoped
program/case, trusted demo actor, invocation source and timestamps. Separate
sections show actual agent participation, business timeline, historical evidence
versions, tool/service receipts, exact proposal and decision references, authorized
manifest, execution steps, idempotency/attempt history and independent verification.

Failure details identify stage/category, last recorded successful activity,
observed mutation and the need to inspect the governed case for retry or
reconciliation. They do not substitute a stack trace for an explanation.

For partial delivery execution, ERP commitment remains verified while Planner is
failed. For a mismatch, the ERP response can be succeeded while its independent
readback is mismatch. Expected and actual delivery quantity/date identifiers are
shown from the source plan/readback. There is no overall green success inference.

Every detail links to the program and correct business case; exact CR-017 proposals
link directly to Decisions. Source records for QE-004/DR-009 remain available via
their case workbench. Evidence links open the existing case/evidence view. Linked
Concierge sessions are reachable from the run.

## Agent, tool and trace observability

Only checkpoint-recorded specialist invocations are shown. An absent invocation
is never rendered as completed. Status, caller, concise structured result and
measured specialist duration are shown where recorded. Missing timestamps or
participation stay unavailable. Completed agents are static.

Tool/service display selects names, caller, target system, safe record identifiers,
status and measured latency. It excludes source response bodies, credentials,
headers, arbitrary arguments and hidden reasoning. Failed SDK spans remain visible
when there is no successful tool receipt. The existing safe SDK processor now
retains only allowlisted tool/role/invocation identifiers alongside its prior
redacted span metadata.

The live control-host entry point now saves the CLI's existing `report.json`,
`tool-calls.json` and `trace-metadata.json` formats into its existing per-run artifact
directory. It binds the actual SDK trace ID to the existing run/activity index.
No parallel trace database is created. CLI execution and the existing Agents SDK
orchestrator remain intact. Trace export/platform visibility is not claimed by
this local host; correlation is through the recorded trace ID.

Older host runs that did not persist these artifacts retain unavailable fields.
An arbitrary legacy `artifact_directory` string is deliberately not dereferenced;
the adapter reads only host-owned `runs/{validated persisted run ID}` locations.

## Token and latency semantics

Input, output and total tokens come only from recorded completed generations.
Unavailable usage is null, displayed as unavailable. Model names are observed
report metadata; the configured runtime's existence is not a successful model
connectivity check. No pricing table or cost estimate was added.

Run elapsed time is the persisted investigation interval. Specialist durations
use the existing measured monotonic intervals. Per-call latency is observed; summed
model latency is labeled cumulative because specialists can overlap. Human wait
is separately derived from the first recorded approval request to its decision,
or elapsed time while that review remains open. External wait remains unavailable
when no suitable timestamps exist. Missing timestamps are not replaced with zero.

## Evals and historical integrity

The read-only server-side artifact index names six known result locations: the
original full live smoke, its historical full follow-up, the two later targeted
covered/scheduled validations, the 08.5 offline report and the integrated 08.6
report. It stores file references, not copied scorecards. Missing or malformed
results are identified as unavailable.

The original live full smoke is **4/6, FAIL**. The later full follow-up also remains
**4/6, FAIL**. `cr017_covered` and `cr017_scheduled` are separate later **1/1** targeted
records. They do not become a fictitious new 6/6 smoke. Offline counts and critical
failures are read and cross-checked against the actual case results. The current
integrated report is **112/112 with zero recorded critical failures**.

The view includes case pass/fail matrices, critical failure codes, timestamps,
model when recorded and semantic-grader availability. An absent semantic grader
stays skipped/unavailable. No live evaluation appears merely because an offline
report exists. Zero critical failures is not a claim that all reasoning is perfect.

This bounded index intentionally excludes pytest-generated failure probes and
unrelated local files. Add a reviewed stable index entry for another real eval
artifact; the browser cannot request new files or choose a directory.

## Artifact and conversation safety

File reads validate a fixed allowed root, relative components, ancestor/file
symlinks, file type/link count and size. Run checkpoints and reports must match
the persisted scope. Only explicitly selected structured fields leave the server;
raw trace/rejected outputs, hidden reasoning and unrestricted source payloads are
not served. There is no generic download or arbitrary file-read endpoint.

Concierge remains process-local for executable confirmation capabilities, with the
same expiry and role/source checks. Operations adds sanitized historical visible
turns and confirmations to the existing metadata index: at most 256 sessions,
48 turns, 96 confirmations and 96 run links per session. Recorded history contains
no executable action tokens or raw voice audio. Credentials and local path patterns
are redacted from displayed text. History is an observation, not authoritative
business state or a new long-term agent memory. Actions still re-read source facts.

A session links admitted workflow IDs, surfaced proposal cards, explicit successful
or denied confirmations and saved automation IDs. The trusted `ui_chat_` invocation
origin remains identifiable even if bounded session history has been evicted.
Older ephemeral conversations cannot be reconstructed.

## Source health, search, alerts and responsive behavior

Health begins **Unknown / not checked**. The explicit check performs one scoped
read through each existing source adapter. Results carry timestamps; after five
minutes, they are labeled stale. Failed reads remain unavailable, not green.
No uptime percentage or credential-health check is invented.

Global search includes recorded runs/trace IDs, session summaries and known eval
results, after business-case results. Search never invokes a workflow. Historical
hard eval gate failures are labeled with their actual history in Alerts; existing
case/run alerts remain in use. Overview gains no token, trace or tool-call metrics.

Tables scroll horizontally at small widths; filters and panels stack. Native
links/selects/buttons/details retain keyboard behavior. State is conveyed in text,
not color alone. Existing blue gradients, Concierge layout and business workbench
styling are retained.

## Integrated verification

The exact commands, results and changed files are in
[PHASE08_6_VERIFICATION.json](PHASE08_6_VERIFICATION.json). Browser testing is
**scripted integration testing using deterministic model doubles**, with real
local source HTTP/MCP, not paid AI inference or actual human approval.

The integrated browser journey covers Overview, Programs, all four cases,
Workflows/Automations, Decisions, Search, Alerts, Concierge, Operations, reliability
history and mobile layout. Separate isolated fixtures exercise partial execution
and mismatched readback. Assertions check:

- DR-009 has 600/800 in the case and Operations, using Concierge's shared source
  projection; the conversation retains the source-grounded delivery cards.
- QE-004 hold state is visible in the source-derived case/run context; no release
  is inferred from investigation or recovery routing.
- CR-017 customer acceptance remains separate and pending; runtime completion
  does not approve the proposal or complete validation.
- CR-019 handoff verification is separate from lab authorization/testing/acceptance.
- Decisions and case pages use the existing exact proposal/decision state.
- Historical 4/6 failures remain separate from the later targeted passes.
- Unknown source health becomes available only after successful actual reads.

The source/backend, full coordinator, MCP, all existing Phase 07 offline cases,
08.4 workflow variants, 08.5 Concierge, new Operations regressions, TypeScript,
production build and Playwright checks are recorded in the verification file.

| Verification | Actual result |
|---|---|
| Full source/backend suite | 483 passed |
| Full coordinator suite | 692 passed |
| Final Operations + Concierge regressions | 24 passed, including 11 Operations tests |
| Final Operations-only check after evidence-link mapping | 11 passed |
| Full MCP suite | 56 passed |
| Integrated Phase 07 offline evaluation | 112/112; hard gate PASS; zero critical failures |
| Browser/component checks across all configurations | 79 passed |
| TypeScript and production build | Passed; existing 511.91 kB chunk advisory |

The full coordinator run preceded two additional Operations tests; the final
focused checks cover those additions. The browser total counts 76 existing checks
and three new Operations fixture journeys. Each Operations variant deliberately
skips the test for the other fixture type. Initial browser failures are retained
in the logs: the CR-019 handoff section was restored in the new run page, and two
quality search assertions were updated for the business-identifier-first label.
Their corrected reruns passed. Earlier Operations test timing/assertion failures
and their successful reruns are also retained.

Preservation verification found all 71 protected source/fixture/authority files
unchanged. All 655 prior screenshot files match their pre-change hashes after
restoring captures regenerated by regression tests; those newly regenerated
captures remain separately under `.cache/phase08-6/regenerated-captures/`.
The exact change manifest contains 43 files, including seven new screenshots,
with no deleted files.

Screenshots: [Operations](screenshots/phase08-6/operations.png),
[CR-017 run](screenshots/phase08-6/cr017-run.png),
[delivery run](screenshots/phase08-6/delivery-run.png),
[partial execution](screenshots/phase08-6/partial.png),
[mismatched readback](screenshots/phase08-6/mismatch.png),
[reliability](screenshots/phase08-6/reliability.png),
[mobile](screenshots/phase08-6/mobile.png).

## Manual connected check — not run automatically

1. Restart the existing control host with its **same** source/MCP URLs, metadata
   directory and UI origin so it loads these routes. Keep the working source DB.
   Do not initialize/reset it or substitute a new metadata directory.
2. Open [the existing local Operations URL](http://127.0.0.1:5188/control/operations).
   Read existing history first. The screen itself makes no model calls.
3. If you choose to make a paid live call, select an allowed demo profile and
   explicitly ask Concierge to investigate one of the installed cases, or use the
   existing workflow launch. This uses the already-configured model; no new setup
   or credential entry is needed. Existing exact review/execution boundaries apply.
4. Open the resulting run from Concierge or Operations. Confirm the business case,
   actual invoked specialists/evidence, saved tool receipts and SDK trace ID. Expand
   Technical details to inspect observed model, tokens and latency. Follow the case
   link and compare current business state.

No paid live smoke or browser-provider speech service was automatically run.
Isolated verification servers are stopped after tests. The test preview port 5180
is temporary; 5188 above is the user's existing app URL, not a claim its backend
was restarted by this phase.

## Known limitations and Phase 09 starting point

Operations is scoped to the current host metadata directory and installed Helios
workflows, not a cross-host telemetry warehouse. Older missing tool/usage data is
not recoverable. SDK trace export is not verified. Health is a timestamped read
observation, not monitoring or uptime. Business source reads are independent, not
a distributed snapshot; consequential actions still revalidate through existing
services. Session retention is bounded and shared by the existing local demo
reader scope, which is not production authentication. Extra eval artifacts need
a reviewed server-side index entry.

The existing production bundle-size advisory remains; no new dependency was added.
No active scheduler, event listener, new workflow, slide creation or Git work was
performed. Historical source fixtures, business authority and prior captures are
preserved.

Phase 08's implementation is complete after the recorded integrated checks:
business workbench + four connected workflows + governed Decisions/execution +
connected Concierge + saved automation configuration + Operations/reliability.
The exact next starting point is **Phase 09 visual/demo polish**, only on a new
explicit request: review this verified integrated journey and screenshots, then
refine presentation/demo pacing without inventing business state or telemetry.
There is no automatic continuation into Phase 09.
