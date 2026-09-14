# Phase 08.2 — connected CR-017 workbench and Decisions

The existing CR-017 requirement-change workflow is operable through the control
plane: investigate, inspect recorded findings and evidence, review an exact
versioned proposal, approve/reject with a trusted demo actor, execute its governed
manifest, inspect independent readback and retain pending physical validation and
customer acceptance. Other workflows and freeform Concierge remain previews.

## Architecture and authority

`src/program_coordinator/control_host/` is a local FastAPI presentation adapter.
It calls the existing `WorkflowService`, registry, `ActivityStore`, `CaseHarness`,
`ExecutionService`, `SourceGateway` and `HumanDecisionGateway`. No existing source,
MCP, agent prompt, Phase06 policy/manifest or Phase07 grader/runtime file changed.
The small FastAPI/Uvicorn dependencies live in the existing coordinator environment;
its compatible AnyIO bound avoids the old Starlette deprecated-alias warning.
The root source environment and its dependency configuration remain unchanged.

Investigation admission uses WorkflowService's persisted invocation digest and
idempotency key. The HTTP host admits one active investigation in its dedicated
metadata directory; a process lock prevents a second host claiming that directory.
The browser retains only an uncertain request's retry key, never workflow state.
An explicitly clicked investigation starts an asynchronous existing service call.
A validated human-review recommendation is passed to existing proposal preparation.
Preparation uses a stable host-generated key, so a lost response can be reconciled.
An existing current proposal is not silently superseded. A deliberate reassessment
can prepare a replacement bound to the exact prior reference using the existing
supersession contract. Attempted writes still require Phase06 reconciliation.

Runs/cases/activity/proposals/reviews/actions/verification stay in ActivityStore.
Specialist summaries, tasks, status, questions and source references come from
validated, scoped `case-state.json` checkpoints or retained final synopses. The
host resolves only its own fixed `runs/<validated-run-id>/case-state.json` path;
no client path, original artifact directory, provider payload or hidden reasoning
is exposed. Missing checkpoints are labeled unavailable/not recorded.

The closed profile selector maps to the **existing server-installed** READER,
AUTOMATION and ENGINEER objects. The browser never supplies an actor object or an
arbitrary role. Investigation (which can prepare a draft) requires Program operator
or Engineering approver; the Read-only viewer cannot invoke it. The source server independently checks the fixed demo identity.
These public local stand-ins are **not production authentication**. A wrong reviewer
is rejected and audited by ExecutionService. Engineer/operator execution controls
ask the existing automation host to resume; no browser action arguments are accepted.

Every review/execution submits the entire exact ProposalRef: customer, program,
case, run, workflow, definition version, proposal ID, version and digest. The
review route retains that reference through profile changes. Missing/wrong
references are not replaced with “latest.” Freshness preflight labels stale
proposals and disables controls; the existing service rechecks during each write.
A superseded proposal links to its exact replacement, which needs its own review.

## Typed HTTP surface

All routes are under `/control-api`. See [OpenAPI](phase08-2-openapi.json) and the
generated frontend `host-schema.d.ts` for full input/output contracts.

| Method / route | Adapter behavior |
| --- | --- |
| GET `/health` | Idle readiness/mode; no key loading or model invocation |
| GET `/cases/CR-017` | Scoped cases, runs, recorded specialist projections, proposals, reviews, attempts, independent verification, activity and current-source preflight |
| POST `/cases/CR-017/investigations` | Closed requirement_change_analysis v1/analyze, CUST-FML01/PRG-A17/CR-017; explicit `ui_…` invocation key; existing service admission |
| POST `/proposals/prepare` | Existing preparation for a validated run; optional exact supersedes reference; host owns the stable preparation key |
| POST `/proposals/review` | Exact reference, approve/reject and bounded comment; existing trusted engineer review |
| POST `/proposals/execute` | Exact reference only; existing resume/reconciliation service |

Strict extra-field rejection prevents targets, arguments, prompts, credentials,
actor objects or filesystem paths. Mutations require the configured loopback
Origin and a custom action header; hostile Host/cross-site requests are denied.
Responses are not cached. There is no CORS grant, generic write proxy, arbitrary
tool/MCP endpoint, reset route or public fault injection. Vite denies developer
test/config/report paths. The frontend checks that host and source proxy URLs
refer to the same local demo before enabling the connection.

## Exact write boundary and readback

Preparation creates the existing Engineering draft plan. Engineer review records
the existing exact source decision. Those are the only pre-execution writes.
The approved manifest then performs, in its existing order:

1. POST the approved Validation job; independently GET/verify job and reservation.
2. POST the approved Planner implementation link; independently GET/verify link,
   task and milestone against the expected state and compare-and-swap version.

There are no Manufacturing, Quality, inventory, ERP or customer-communication
mutations. A returned POST is an **action result**, not a verified outcome.
ExecutionDetails displays each action ID/result/resource, expected parameters,
verification state/reference and a scoped source-app link. Definitive partial
failure retains the successful step; retry uses the existing exact keys and
checks. Unknown outcomes stay reconciliation-required. A readback mismatch never
appears as execution verified. Completed actions are re-read, not blindly replayed.

Successful execution retains `in_validation`, `approved_and_scheduled`,
`pending_test_results`, customer acceptance `pending`, hardware `unvalidated`.
It does not create a result, grant engineering acceptance or close CR-017.

## UI state mapping

The seven stages are Request, Evidence review, Recommendation, Human decision,
Execution, Verification and Physical validation. Their completion depends on
recorded evidence rather than a single green status. Source business state,
analysis state, review, write outcome and verification remain distinct.

| Record / condition | Presented state |
| --- | --- |
| No host run | Not investigated; explicit Run investigation |
| Running run | Running investigation; latest recorded specialist checkpoint, polled |
| Completed run | Last run / Recorded result; actual recommendation and options |
| Escalation policy or failed/cancelled run | Escalation required / explicit failure; no fabricated proposal |
| Draft exact proposal | Waiting for human review |
| Approved/rejected exact review | Actual reviewer/source decision and outcome |
| Stale or superseded | Disabled review/execution, clear reason/replacement link |
| Execution in progress | Executing/verifying and persisted step results |
| Partial/unknown/mismatch | Partial execution / reconciliation required / verification failed |
| Matched completed execution | Execution verified; physical results and acceptance still pending |

The case keeps before/after source requirements, applicability and the existing
contextual evidence modal. Decisions filters cover Needs review, Approved,
Rejected, Executed/Completed, Superseded/Stale and Needs attention. Overview review
counts use fresh reviewable host proposals only; unavailable is a dash. Existing
program-health rules remain unchanged. Search includes scoped runs and exact
proposal/decision IDs. Host alerts are actual pending decisions and recorded
failures. Concierge shows case/run/decision context but answers/actions remain
Preview. Speech remains explicit dictation into a draft.

Polling is every 1.5 seconds while running or submitting and 15 seconds otherwise,
plus explicit refresh/focus. Polling never starts models. Reopening a dedicated
host marks abandoned `ui_…` running metadata interrupted, without restarting a
model. Graceful shutdown cancels/records an in-flight investigation. Existing
Phase06 recovery remains responsible for partially attempted business writes.

## Manual connected demo

Current URL: **http://127.0.0.1:5189/control/overview**. This is a separate demo
from the earlier 5188 preview. Source: 18028; read-only MCP: 19084; host: 18084.
Storage: `.demo/phase08-2-connected.sqlite3` and `.cache/phase08-2/connected/`.
The processes were started and their idle HTTP/UI state was checked; there are
zero host runs and no browser POSTs in `manual-ready.json`. No paid model was run.

From the repository root, start each long-running command in a separate terminal.
If restarting, keep the existing database and metadata; do not reinitialize them.

```sh
cd /Users/nelsonwang/Documents/Personal/OpenAI/openai_aaa_takehome
uv sync --project coordinator
# First initialization only; already done for the current local demo:
DEMO_MODE=true DEMO_DB="$PWD/.demo/phase08-2-connected.sqlite3" .venv/bin/python -m mock_enterprise.cli init-demo

# Terminal 1
DEMO_MODE=true DEMO_DB="$PWD/.demo/phase08-2-connected.sqlite3" .venv/bin/python -m mock_enterprise.cli serve --port 18028

# Terminal 2
PYTHONPATH=src mcp_server/.venv/bin/python -m stratos_mcp --backend-url http://127.0.0.1:18028 --port 19084

# Terminal 3
DEMO_MODE=true PYTHONPATH=src coordinator/.venv/bin/python -m program_coordinator.control_host --port 18084 --source-url http://127.0.0.1:18028 --mcp-url http://127.0.0.1:19084/mcp --metadata-dir .cache/phase08-2/connected --ui-origin http://127.0.0.1:5189

# Terminal 4
cd mock_apps_ui
MOCK_API_URL=http://127.0.0.1:18028 CONTROL_HOST_URL=http://127.0.0.1:18084 npm run dev -- --port 5189
```

1. Open Overview and select **Log in → Program operator** (a demo identity).
2. Inspect CR-017; use **View evidence** to inspect exact applicability.
3. Click **Run investigation**. This explicit action uses the existing configured
   GPT-6 Astra key/runtime and can incur model usage. Loading/refreshing never does.
4. Follow the run ID and recorded activity. Inspect actual specialist findings,
   gaps, calculated options and recommendation after completion.
5. Open **Review exact proposal**. Inspect costs, dates, assumptions, references,
   policy, immutable digest and ordered action manifest.
6. Switch the profile to **Engineering approver**. The exact review URL stays open.
7. Approve or reject. Rejection cannot execute; approval binds this exact version.
8. Click **Execute approved proposal**. Inspect both action receipts and independent
   readbacks. Follow source links to Validation and Planner if useful.
9. Return to CR-017. Confirm scheduled work, pending physical results/engineering
   disposition, pending customer acceptance and unvalidated hardware adequacy.

On connection loss, refresh first. Use the same exact review/prepare request or
**Reconcile / resume exact proposal**, letting the existing service decide whether
only a read or a safe remaining write is allowed. Do not manually reset a demo to
hide a partial outcome. The real model may fail or escalate; the UI retains that
result without inventing a proposal.

## Verification and screenshots

All automated investigation outputs are developer-only deterministic CaseHarness
model doubles. Source mutations/readback cross real HTTP in browser tests. These
are **scripted integration tests, not an AI run or actual human approval**.
`coordinator/evals/phase08_2/serve.py` owns a fresh source DB and metadata per test;
its CLI-only fault modes never enter production routes or runtime retrieval. It
refuses occupied ports and shuts down its owned source process.

Commands and final outcomes are recorded in the verification table below. The
[verification receipt and complete code file inventory](PHASE08_2_VERIFICATION.json)
include the exact test counts, overlapping targeted checks and protected-file audit. All
original source/Phase06/Phase07 fixtures, prompts and graders remain unchanged.
Historical screenshots are preserved; rerun source/shell screenshots go under
`docs/phase08/connected/regression-*`.

| Verification | Result |
| --- | --- |
| Root source/backend pytest | 392 passed, including 69 Phase06 execution regressions |
| Coordinator pytest | 556 passed; final host guard checks: 15 passed (14 overlap the full suite) |
| Phase07 offline evaluations | 40/40, hard gate PASS; no critical failures |
| Existing browser/component/voice/source-app suite | 56 covered: 53 passed initially, all 3 regressions fixed and passed on targeted rerun |
| Connected HTTP/browser scenarios | 3 passed: exact success, Planner partial failure, readback mismatch |
| Typecheck and production build | Passed |

```sh
.venv/bin/python -m pytest -q --basetemp=.cache/phase08-2/source-pytest
(cd coordinator && .venv/bin/python -m pytest tests -q --basetemp=../.cache/phase08-2/coordinator-pytest-final)
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07 --mode offline --output .cache/phase07/phase08-2-offline-20260912
# Eval output must be a new directory; choose a new suffix when rerunning.
(cd mock_apps_ui && PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e)
(cd mock_apps_ui && PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npx playwright test -c playwright.phase08.config.ts)
(cd mock_apps_ui && npm run typecheck && npm run build)
```

[The screenshot directory](phase08/connected/screenshots/) contains before-run,
recorded running, completed findings/options, exact review, approval, verified
execution, partial execution and mismatch states, plus the real configured
runtime still idle. Every automated screenshot is named `test-double`. Full-page,
viewport and detailed readback captures make state and source IDs inspectable.
The configured-runtime idle capture does not claim a model investigation.

## Limitations and next step

This host is local, single-process and dedicated to CR-017. It is not production
authentication or a general workflow execution API. There is no token streaming,
background schedule/event worker, connected freeform chat or new source-write
capability. Older external CLI runs may have only retained final synopses when
no checkpoint exists inside this host's owned run directory. Metadata/readback
polling is appropriate to this bounded demo, not a portfolio-scale architecture.
The UI does not manufacture a completed physical test or downstream acceptance.
Paid live reasoning, optional semantic grading and the six-case live smoke were
not exercised. No commits or pushes were performed.

The next planned 08.3 slice is catalog/manual invocation and saved schedule/event/
condition previews, with no active scheduler. It is not implemented here and needs
the next explicit request. Phase 08.2 stops at this handoff.
