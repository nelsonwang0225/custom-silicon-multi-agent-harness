# Stratos demo runbook

The [live demo configuration](PHASE10_LIVE_RUNTIME.md) uses the existing GPT-6 Astra API runtime for CR-017, CR-019, QE-004 and DR-009. QE-011 remains a scripted, two-minute opening with real source API reads and no model calls. It starts when the control plane opens in a cleared demo and completes its approved investigation handoff without a human decision. Active agents show Processing, completed agents turn green, and unused agents stay Idle. Harness startup, refresh and reset do not call a paid model; explicit main-case investigations and Concierge sends do.

## Prepare the machine once

Use the repository root, Python 3.12, uv, Node.js/npm and a modern desktop browser. Install the existing locked environments:

```sh
uv sync --locked --python 3.12
uv sync --project mcp_server --locked --python 3.12
uv sync --project coordinator --locked --python 3.12
npm --prefix mock_apps_ui ci
```

The existing live runtime reads the authorized owner-only `.env.local` using its safe loader. `OPENAI_API_KEY` must be present and correctly formatted; the file must be a regular, single-link file owned by this user with mode 600. Do not print it, shell-source it or put its value in command arguments. The configured application model is `gpt-6-astra`. Presence checks do **not** verify API availability, quota, access or model quality.

## Start and prepare

```sh
# First use only: explicitly create a NEW dedicated demo database.
./scripts/demo init --yes

# Builds the current UI and starts four owned services. Never resets data.
./scripts/demo start
./scripts/demo status

# Explicitly review/confirm Full Demo Reset, then run every readiness check.
./scripts/demo prepare
# For a deliberately scripted reset, use: ./scripts/demo prepare --yes

# Read-only final check. Exit 0 and “Demo ready” require every gate to pass.
./scripts/demo check
```

The default isolated operator directory is `.demo/interview/`: `enterprise.sqlite3`, `metadata/`, individual service logs, `frontend/` compiled assets and process/configuration metadata. Existing working databases are not copied, changed or selected implicitly. `init` refuses any existing database. `start` leaves business state intact and does not run models; existing host startup still marks abandoned investigations as interrupted after a crash.

To resume this same demo on another day, run **start**, not init or prepare. Mutations persist until explicit reset. `start` recognizes a healthy matching owned supervisor and does not launch duplicates. Occupied ports or a locked metadata directory cause a clear refusal; the helper never kills a port's unknown owner.

The helper launches the existing source API, scoped MCP server, live control host with Phase 09.1 controls, and a Vite production preview. It builds a separate frontend output for each harness configuration, including the exact source-URL binding. It starts no scheduler, event listener, condition evaluator, broker or additional agent runtime. Detached supervision works after the invoking terminal closes.

After code changes, use `stop` then `start` to rebuild and serve the current version. Calling `start` on an already healthy owned demo is deliberately a no-op. Neither sequence resets business state.

## Exact default URLs

| Surface | URL |
|---|---|
| Overview | [127.0.0.1:5188/control/overview](http://127.0.0.1:5188/control/overview) |
| Helios Program | [127.0.0.1:5188/control/programs/PRG-A17](http://127.0.0.1:5188/control/programs/PRG-A17) |
| Engineering Hub | [127.0.0.1:5188/engineering](http://127.0.0.1:5188/engineering) |
| Validation Lab | [127.0.0.1:5188/validation](http://127.0.0.1:5188/validation) |
| Manufacturing Portal | [127.0.0.1:5188/manufacturing](http://127.0.0.1:5188/manufacturing) |
| Commercial ERP | [127.0.0.1:5188/erp](http://127.0.0.1:5188/erp) |
| Program Planner | [127.0.0.1:5188/programs](http://127.0.0.1:5188/programs) |
| Operations / reset controls | [Operations](http://127.0.0.1:5188/control/operations) · [Demo controls](http://127.0.0.1:5188/control/operations/demo) |
| Source API health | [127.0.0.1:8000/health](http://127.0.0.1:8000/health) |
| MCP readiness / tools endpoint | [127.0.0.1:9000/ready](http://127.0.0.1:9000/ready) · [MCP](http://127.0.0.1:9000/mcp) |
| Control host health / no-call readiness | [127.0.0.1:18082/control-api/health](http://127.0.0.1:18082/control-api/health) · [Readiness](http://127.0.0.1:18082/control-api/readiness) |

`start`, `status` and `check` print the actual URLs. All binding is loopback-only. A local Vite preview is a demo service, not production hosting.

## Another port set or an existing working demo

Global options go **before** the subcommand and are saved in the chosen harness directory. Later commands need only `--state-dir`.

```sh
./scripts/demo --state-dir .demo/another-demo \
  --source-port 18231 --mcp-port 19231 --host-port 18230 --ui-port 5195 init --yes
./scripts/demo --state-dir .demo/another-demo start
./scripts/demo --state-dir .demo/another-demo prepare --yes
./scripts/demo --state-dir .demo/another-demo stop
```

For an **existing** source/metadata pair, first stop its known manually started services using their original terminals. Then pass its actual `.demo/` paths with `--source-db` and `--metadata-dir` to `start`; omit `init`. No automatic adoption, migration, reseeding or reset occurs. Do not run two configurations against the same source database. If the existing source lacks later installed schemas, follow its original additive installation handoff while stopped; do not use a foundation reset to repair an integrated demo.

An older quality demo may lack the optional QE-011 standard-policy columns. With
its services stopped, the existing `install-quality-case` command now adds those
columns while preserving records. For example, for the default harness database:

```sh
DEMO_MODE=true DEMO_DB=.demo/interview/enterprise.sqlite3 PYTHONPATH=src \
  .venv/bin/python -m mock_enterprise.cli install-quality-case
```

Use the actual selected database path, then restart its services. A full reset
does not repair an older schema. See the [verified compatibility update](PHASE10_AUTOMATIC_TOUCHLESS_ENTRY.md#existing-preview-compatibility).

## Pre-demo checks and reset

`status` is an informational report; `check` returns nonzero unless all checks pass. `--json status` and `--json check` provide structured results. They confirm:

- Four required services and five scoped source-system reads are reachable.
- Phase 09.1 `phase09-v1` baseline is valid, all four cases exist, and reset reconciliation is clear.
- No stale/unverified decision or currently running workflow/host task/Concierge turn remains.
- The actual Concierge adapter is installed; model/credential configuration is present without a model request.
- Generic schedulers, event listeners and condition evaluators are not installed. The separate autonomous-opening status reports its one app-entry/replay event.
- Services match the selected harness ownership/configuration.

“Mutated or unavailable” after a walkthrough is expected until reset; it is not evidence that the workflow failed. Inspect the listed discrepancies. `prepare` invokes the **existing Phase 09.1 CLI and HTTP reset**, including its preview, exact epoch, explicit confirmation, dependency checks, archives and independent baseline readback. It does not duplicate reset logic.

```sh
./scripts/demo reset --scope full         # interactive RESET confirmation
./scripts/demo reset --scope CR-019       # only when existing dependency checks allow
./scripts/demo check
```

For a fresh walkthrough, select **Program operator**, click the small **Reset demo**
icon beside the alerts bell, then **Reset and restart**. This stops active demo
work, restores the five source systems and shared facts, archives current runs
and decisions, clears drafts, and returns to Overview with the same demo persona.
CR-017, CR-019, QE-004 and DR-009 are **New**. CR-019 has no investigation,
policy results or Validation intake; Northstar Boreal is **On track**. QE-011
automatically starts after eight seconds, using the scripted opening. The four
main cases remain ready for their normal walkthroughs; their approvals still apply.

For maintenance without automatically starting QE-011, use **Operations → Demo
controls → Full demo → Review reset → type RESET → Confirm demo reset → Verify
baseline** (or the CLI above). Supported scenario scopes are CR-017, CR-019,
QE-004, DR-009 and QE-011. Shared dependencies may refuse a scenario reset; use
Full Demo Reset. Historical eval/trace artifacts, documents and authored fixtures
are preserved. Source restore and host reconciliation remain separate commits;
a partial reset must be explicitly reconciled. The master control starts QE-011
only after baseline verification succeeds. If the runtime cannot start, the UI
reports the successful reset separately and opens Demo controls for an explicit retry.

## Autonomous back-office opening and concurrent investigations

The [current deterministic preview](PHASE10_MINUTE_FULL_TEAM_OPENING.md) uses
explicit two-minute processing sequence after the event delay: Coordinator scoping,
four parallel specialist assessments, then Coordinator review and synthesis.
Change Impact checks Engineering configuration/procedure scope. The four main
cases use the real model and retain actual model timing. Existing
recorded openings must be explicitly replayed to show the new behavior.

Entering the control plane automatically arms QE-011 in a cleared demo; no login
or launch click is needed. After the eight-second event delay, the existing
scripted opening investigates and verifies the standard handoff autonomously.
All four specialist stations remain visible; unused agents are Idle. A completed
opening stays recorded across reloads until reset. Restart the owned demo after
code changes to rebuild its preview; preserve unrelated stores.

Optional live concurrency check (not run by automated verification):

1. Full Demo Reset; confirm baseline/readiness. The master reset cancels active
   demo runs and drains pending source writes before restoring the baseline.
2. Reload **Overview** to enter the next cleared demo and arm QE-011 automatically.
3. Select **Program operator** if you want to start CR-017 or inspect Operations.
4. After eight seconds, confirm QE-011 is investigating from a **Source event**.
5. Navigate to CR-017 and click **Run investigation**.
6. Return to Overview; confirm **2 active investigations** while both remain active.
7. Switch between QE-011 and CR-017. Each graph contains only that run's tasks.
8. QE-011 finishes with **Quality investigation handoff verified**. It has no
   recovery decision and does not appear in Needs attention.
9. CR-017 reaches its existing Engineering review independently.
10. Inspect each run in Operations for its invocation, specialists, evidence,
    actions and independent outcome.

If a live workflow finishes quickly, inspect its recorded result. No artificial
execution delay keeps a live run on screen. QE-011 alone uses the eight-second
event delay plus the explicit two-minute presentation sequence.

**Reset autonomous opening** cancels/drains QE-011 and clears its owned records,
preserving unrelated CR-017 state/history. The same page stays at baseline after
reset; reload Overview or click **Replay autonomous opening** to start again.
Refresh/new tabs join an existing opening without replay. Interrupted work requires explicit recovery.
Generic saved event/schedule configurations remain inactive.

Default capacity is **3 concurrent workflows**, configurable before host start via
STRATOS_MAX_CONCURRENT_WORKFLOW_RUNS (1–8). Capacity denial preserves the request
key for explicit retry; there is no waiting queue. Specialists are reusable
configurations instantiated separately for each run. Source version checks,
idempotency, approval manifests and independent readback remain authoritative.

Each automatically started live QE-011 and manually launched CR-017 can make multiple existing
Coordinator/specialist API requests, plus optional hosted retrieval requests if that
provider is configured. Existing per-run budgets apply separately. Concurrent
usage can increase peak API rate and cost; no new aggregate dollar cap is installed.
Automated checks use doubles and make no paid calls. Indexing is a separate explicit
operator action. See [implementation, verification and limitations](PHASE10_TOUCHLESS_CONCURRENT_HANDOFF.md).

Talk track: “A Manufacturing event started a routine investigation. The agents
validated its scope and routed the approved investigation without a human decision.
CR-017 runs independently and brings in Engineering at its consequential boundary.”

## Personas and switching

Use **Log in** / the active **Demo identity** in the upper-right header. The selector shows each existing role and actor ID. There is no automatic elevated selection or contextual approval shortcut. These public synthetic selectors do not authenticate a real person.

| Persona | Navigation | Business authority |
|---|---|---|
| Program operator (`demo-automation`) | All seven workspaces; scoped Operations and own chats | All four investigations; permitted preparation and exact approved execution. No human approvals. |
| Engineering approver (`demo-engineer`) | Overview, Programs, technical Decisions/Scenarios, Knowledge | All four case investigations; CR-017 exact plan and separate evidence review; CR-017 execution and CR-019 intake recovery. No QE/DR approval or execution. |
| Program Owner (`demo-program-owner`) | Overview, Programs, recovery/commercial Decisions and business Scenarios | Existing CR-017/QE/DR case investigation, exact QE/DR review and approved execution. No CR-019 intake, Engineering review, or material release. |
| Read-only viewer (`demo-reader`) | Overview, Programs, Knowledge | Scoped facts, recorded decision outcomes and explanatory Concierge Q&A. No business workflow or mutation. |

The [full matrix](PHASE10_1_PERSONA_ACCESS.md) distinguishes endpoint authority from presentation. The generic workflow endpoint remains operator/engineering; use scoped case pages for Program Owner. Engineering retains its existing configuration-save authority through scoped Concierge despite the hidden Workflows workspace. Saving configurations never activates a trigger.

Unauthorized buttons are absent. Authorized actions awaiting approval/current evidence remain disabled with a reason. Engineering reviews CR-017 from its Decisions queue. Program Owner reviews QE/DR from its queue or case. Operator tracks those decisions and executes only when the existing policy permits. Viewer reads the same business facts through Programs; it has no dedicated queue.

Changing persona clears scoped forms, search state, voice capture, drafts and visible Concierge history. A disallowed current route redirects to Overview. Existing approvals and admitted runs persist with original attribution. Start a fresh exact action preview after switching; another persona's action token cannot be reused. Switch only through the explicit selector; Concierge cannot switch roles.

For reset, select **Program operator**, then use **Operations → Demo controls** with the existing maintenance confirmation. The CLI remains available through its separate maintenance gate. Source apps retain independent demo selectors and source permission checks; this is not a five-app authentication migration.

## Four canonical paths

Start from Helios and open the case. **Run investigation** and **Send message** invoke the configured paid runtime only when the operator explicitly uses them. None of the harness checks clicks those controls. For a repeatable initial story, use Full Demo Reset between paths.

| Path | Personas | Walkthrough and truthful ending |
|---|---|---|
| **CR-019 — Standard / touchless** | Program operator | Approved procedure → investigation → policy-bounded package/intake → independent verification. Validation Operations received the package; lab authorization/testing remain downstream. |
| **CR-017 — Material change** | Program operator → Engineering approver | Evidence gap → proposal → exact validation approval → governed scheduling/Planner execution → separate explicit demo lab result → reassessment → exact Engineering evidence review. Technical validation can complete; customer acceptance remains separate. |
| **QE-004 — Yield / quality recovery** | Program operator → Program Owner | Exception → comparable evidence → supply impact → recovery proposal → exact consequential metadata decision → readback. Held material remains held until separate source-owned disposition; no release is exposed. |
| **DR-009 — Delivery readiness** | Program operator → Program Owner | 800 requested → 1,000 physical minus 250 held and 150 allocated = 600 eligible → timing/technical gates → options → exact commitment approval → ERP/Planner verification. The remaining 200-unit gap and original order obligation remain visible. |

For CR-017 physical results, open the existing job in Validation Lab and use its explicitly labeled lab demo action. This is a distinct synthetic lab identity, not automation result authoring. Return to the case to reassess the recorded result, then switch to Engineering approver for exact evidence review. Scheduled work is not tested work; a recorded test is not Engineering/customer acceptance.

## Concierge and Operations

Open the floating **Stratos Concierge**. Check its case/program context before sending. Dictation is optional, explicitly permissioned, editable and browser-provider based. Chat or dictation alone never approves or executes; existing structured confirmation and required personas still apply. Cancellation stops the response, not an already admitted workflow.

For routine diagnosis, use **Operations**, select the run, then inspect business outcome, last activity, tool/source observations and execution/readback details. Expand technical detail for the run/trace IDs and model metadata. A completed runtime is not a completed business case. Use **Evals & Reliability** for historical hard gates, including the preserved failed live runs; absent semantic grading remains unmeasured.

## Troubleshooting and fallback

| Symptom | Operator response |
|---|---|
| Port occupied / different owner | Use `status`, identify the known original terminal or choose another saved port set. Do not kill an arbitrary PID or port. |
| Missing Python/dependencies/build failure | Follow setup above; inspect `build.log` or the named service log under the selected state directory. Restart after correction. |
| Model unavailable / timeout | Check no-call configuration status and Operations. Do not repeatedly submit or assume a paid call succeeded. Review current run/source state before an explicit retry. Credential presence does not prove provider access. |
| Source app fails | Refresh its source page and Operations source health. Treat current authority as unavailable. Restore the source service before reviewing/retrying consequential actions. |
| Concierge fails | Keep the readable error; inspect Operations/conversation history and use direct case navigation. No fake answer is substituted. |
| Failed investigation | Inspect its last activity and failure category in Operations. Review the current case before an explicit new invocation. |
| Wrong persona / stale proposal | Use the required existing identity, or refresh/open the exact current decision. Never replace a missing proposal silently. |
| Partial execution / verification mismatch | Open the exact case/run and use existing reconcile/readback controls. Do not create a second approval or repeat a write blindly. |
| Partial reset | Open Demo controls and explicitly retry/reconcile the pending scope or full reset. Do not bypass the persisted maintenance barrier. |
| Workspace chunk fails to load | A readable failure panel offers **Reload workspace** or **Return to Overview**. Business state remains persisted. |

If live demonstration cannot continue, explicitly announce **“Recorded demo”** and open the [Phase 09.3 screenshot gallery](screenshots/phase09-3/README.md). Those captures are labeled deterministic scripted integration fixtures, not live intelligence. They do not overwrite current source state. Operations also indexes historical recorded live outputs: targeted `cr017_covered` and `cr017_scheduled` passed, while the original full smoke failed. Do not present the latter as success or imply recorded live success for all four cases. See [the recorded fallback index](PHASE09_4_RECORDED_FALLBACK.md).

Return to live mode by closing the recorded material, restoring services/configuration, running `status`, and explicitly using the case workbench. Use `prepare` only if a new baseline walkthrough is intended. The helper never switches runtime mode automatically.

## Shutdown

```sh
./scripts/demo status     # Check for active work; let it settle when possible.
./scripts/demo stop
```

Stop verifies supervisor PID, process identity and ownership token, then the supervisor terminates only its tracked child process groups. It never kills by port. In-flight investigations may become interrupted; inspect Operations after restart. Source state, exact receipts and metadata remain persisted. If the supervisor was externally killed and ownership cannot be proven, the command refuses to signal anything; inspect its recorded children/logs and stop only the confirmed original processes manually.

## Verification and limits

See [Phase 09.4 handoff](PHASE09_4_HANDOFF.md), [verification manifest](PHASE09_4_VERIFICATION.json) and [cold-start evidence](PHASE09_4_COLD_START.json) for actual results. Tests use isolated storage; workflow/speech tests use deterministic doubles. The startup smoke uses the real live adapter but never invokes it. No paid API call, actual human approval or real microphone was tested. Final manual/live timing, long model prose and real browser speech remain Phase 09.5 work.


## Phase 10.2 Agent workspace preview

The workspace shows the installed Coordinator and four specialists, active or recorded run selection, invocation findings and a separate human/external handoff. A green check means that selected task completed; it does not authorize execution or establish hardware/customer acceptance. Inspect an agent for exact evidence versions and run attribution. Only permitted personas see View run. Explain in Concierge opens an editable draft; Send and exact action confirmation remain separate. Source/model health detail is observational, never a paid health probe.

The review preview created during 10.2 uses isolated deterministic doubles and no real microphone. It is not the working demo or a paid agent run. To launch/restart this same fixture from the repository root, use two terminals (stop only your own previous processes before reusing these ports):

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve \
  --root .cache/phase09-3/phase10-2-preview \
  --port 18321 --source-port 18322 --mcp-port 19322 \
  --ui-origin http://127.0.0.1:5203
```

```sh
cd mock_apps_ui
MOCK_API_URL=http://127.0.0.1:18322 CONTROL_HOST_URL=http://127.0.0.1:18321 npm run dev -- --port 5203
```

Open [the isolated Overview](http://127.0.0.1:5203/control/overview). The prepared review preview contains one deterministic CR-017 result awaiting Engineering review. A fresh fixture directory starts with known idle metadata on first use. Explicitly select Program operator and investigate a case to generate a deterministic recorded result. It preserves this fixture's data on restart. Standard CR-019 ends at verified Validation Operations handoff with lab authorization pending; CR-017 ends at a separate Engineering decision. Production harness start/check does not fabricate this activity. To inspect the new UI against your existing live demo without resetting it, use its normal `stop`/`start` rebuild procedure above; do not initiate paid analyses as a health check.

Reproduce both archived illustrative concepts separately, outside the production app:

```sh
node mock_apps_ui/node_modules/vite/bin/vite.js --config docs/phase10-2/concepts/vite.config.mjs
```

Open [the concept comparison](http://127.0.0.1:5205/preview.html). These are explicitly illustrative shapes/states, never live telemetry. See [fixture screenshots and review notes](screenshots/phase10-2/README.md) for parallel, failure, stale, multiple-run and accessibility states.


## Current Phase 10 cosmetic refinement

Primary navigation now pairs each permitted text label with a decorative Lucide outline icon. Existing routes, ordering and persona filters are unchanged. Overview reads in this order: summary, Programs, then the wider Agent workspace on the left and Needs attention in a matching panel on the right. At narrow widths the panels stack. See [icons, screenshots and verification](PHASE10_NAV_LAYOUT_REFINEMENT.md). The existing isolated preview on port 5203 serves these edits; refresh that page. A normal demo harness needs its documented stop/start rebuild to pick up frontend edits, without reset.

### Compact Agent workspace monitor

The [compact monitor refinement](PHASE10_MONITOR_REFINEMENT.md) supersedes the tiered stage: five equal stations, observed task counts and a latest-checkpoint strip. Counts follow the selected run or permitted active scope. UTC checkpoint labels are observations, not task durations or a full transition history. Existing inspectors, recorded handoffs, stale-read behavior and three-second active refresh remain. Preview at http://127.0.0.1:5203/control/overview when the existing review service is running.

The subsequent manager-connections refinement places Coordinator above its four specialists. Dots flow toward freshly observed working specialists; structural lines and static dots remain for inactive/recorded work. Reduced motion suppresses dot movement. Metrics and inspector behavior are unchanged.

Latest visual follow-up: dots continuously flow on all four branches as a labeled relationship animation, even for recorded results. Status colors and agent labels remain source-derived; motion is not evidence of live work. Reduced motion stops the dots.

Current connection behavior supersedes continuous idle animation: manager branches have distinct green/amber/blue/purple identity colors and move only for a fresh active scope; idle/completed/stale views stop. Dashed arrows show the five allowed specialist invocation relationships from runtime GRAPH; expand Specialist connections for their directions. These permission links are static and do not prove an invocation occurred.


Latest explicit visual simplification: remove all specialist-to-specialist lines, the connection legend and the Specialist connections disclosure. Retain four colored Coordinator branches with continuously moving decorative dots, including idle/recorded views. This supersedes the prior idle-stop and permission-edge presentation only; agent statuses, workload and authority remain unchanged. Reduced motion stops animation.

### Shared Knowledge retrieval foundation

See [architecture, policies, commands and limits](PHASE10_KNOWLEDGE_FOUNDATION.md). Open [Knowledge & Evidence](http://127.0.0.1:5203/control/knowledge), select a retrieval profile, search and inspect a passage beside its exact verified source. The review preview has an explicitly built nine-document offline index. Normal startup does not index. New isolated sessions start unindexed; select Program operator → Knowledge index administration → Reindex knowledge corpus → Confirm reindex. Other Knowledge personas can search/read but cannot reindex. The index survives demo reset and validates against the current source corpus. OpenAI indexing/search requires the documented explicit paid opt-in; no agent uses RAG yet.

### Specialist knowledge integration

See [hybrid retrieval, profiles, provenance and optional live smoke](PHASE10_KNOWLEDGE_INTEGRATION.md). Index explicitly, then manually invoke an existing investigation. Knowledge usage is optional and appears in Knowledge & Evidence, case evidence and Operations when actually recorded. “Used in agent runs” includes host-validated citations, not every search candidate. Refresh knowledge activity after a run completes. The default index remains deterministic/offline; `--allow-paid-knowledge-search` explicitly selects the hosted index in the normal host or existing analysis CLI. No startup indexing, workflow authority changes or QE-011 trigger.

### QE-004 quality corpus

The [quality corpus handoff](PHASE10_QUALITY_CORPUS_HANDOFF.md) supersedes the earlier
nine-document count and missing-quality-knowledge limitation. The review preview
now has 12 indexed documents, including two approved quality procedures and one
historical non-normative report. Select Manufacturing quality; enable historical
reports for prior site-concentration context. Current Manufacturing HOLD and
root-cause evidence retain authority. New demo initialization includes the documents;
existing databases use the explicit `install-quality-knowledge` command while
stopped, then the existing shared-index sync. Exact offline/hosted smoke commands
and the verified preservation of preview state are in the handoff.
