# Phase 08.5 — Connected Stratos Concierge

Implemented from [the approved request](../prompts/08_5_CONNECTED_CONCIERGE.md).
This phase ends here; Operations is the next 08.6 slice. No Git operations, paid
model runs, working-demo resets, external messages or background schedulers were
performed. Verification uses isolated synthetic source state.

## 1. Architecture and 2. runtime reuse

The floating React Concierge posts a typed message to the existing local control
host. A bounded `Stratos Concierge` manager is defined beside the existing Agents
SDK agent definitions. It uses the configured `gpt-6-astra`, existing provider/key
loader, SDK `Agent`/`Runner`, medium reasoning setting and the coordinator timeout.
One manager turn returns a strict intent/scope/topic envelope. It has no source,
MCP, approval, execution, file or generic write tools. No alternate runtime or
permission system was introduced.

The host resolves page identifiers, re-reads source APIs through existing adapters,
and builds factual cards. Business quantities, dates, root cause and approvals are
never accepted as model-authored prose. The manager handles language routing; the
host presents the current authoritative facts and exact governed actions. This is
a deliberately bounded conversational interface, not unrestricted general chat.

## 3. Intents and 4. connected routing

| Intent | Behavior |
|---|---|
| EXPLAIN | Current source facts, evidence applicability, persisted run outcomes |
| COMPARE | Actual source-calculated validation, recovery or delivery options |
| INVESTIGATE | Existing case endpoint → `ControlHost.start` → `WorkflowService.invoke` |
| ACT | Exact proposal/decision or execution preview; text itself never confirms |
| NAVIGATE | Existing case, evidence, decision, source, workflow or run route |
| AUTOMATION_CONFIGURATION | Existing configuration shape → preview → explicit save |
| CLARIFY / UNSUPPORTED | Bounded explanation; no workflow or business mutation |

| Case | Existing route/service reused | Authority retained |
|---|---|---|
| CR-017 | Requirement Change; `ExecutionService` | Exact Engineering approval, then explicit host execution |
| CR-019 | Standard Change in Requirement Change family; `StandardHandoffService` | Only eligible, pre-authorized Validation Operations intake |
| QE-004 | Yield/Quality Recovery; `QualityRecoveryService` | Standard investigation; exact Program Owner review for Planner recovery task |
| DR-009 | Delivery Readiness; `DeliveryCommitmentService` | Exact Program Owner quantity/date approval; ERP commitment and Planner link |

Explicit “Reassess/Investigate/Run/Process/Route” messages can admit an investigation.
Ambiguous or quoted invocation language gets a separate scoped start confirmation.
The existing registry, source scope, trusted actor, invocation ID, durable claim and
replay checks apply. Repeated identical chat message IDs do not repeat model calls
or workflow admission. Run polling reads persisted metadata without model calls.
A completed/escalated runtime is not presented as verified business execution.

## 5. Context, grounding and source ownership

Context is resolved from the current Overview, program, case, workflow,
configuration, run or exact proposal route. Run/proposal identifiers are looked up
in existing metadata and bound to the installed customer/program. A different-case
request on a case page offers navigation before action. Other program routes are
rejected before source access. Overview summaries are explicitly bounded to Helios.

Current source reads always outrank conversation history. Unavailable sources,
missing evidence/dates, unknown root cause and stale proposals remain explicit.
Historical run cards identify their persisted basis. The QE/DR summary identifies
shared material IDs and does not add their independently calculated supply gaps.
Technical readiness, commercial commitment, customer acceptance and physical
shipment remain distinct. No full-delivery date or root cause is invented.

Engineering, Validation, Manufacturing, ERP and Planner retain the same source
ownership and public write boundaries. No source model, source API handler,
fixture/business document, MCP tool or source permission was changed. Chat stores
no independent authoritative business record. Source content is data: retrieved
text is not included as manager instructions, and only selected source fields
become visible cards.

## 6. Structured replies and navigation

Cards cover status, evidence, source options, exact decisions/actions, runs,
automations and navigation. Links use existing application routes; IDs in generated
routes are scoped/encoded. The browser also filters link destinations. No internal
filesystem paths or raw model responses are returned. Evidence links open CR-017’s
existing evidence workbench; other source links open their existing source pages.

## 7. Approval, execution and failures

“Approve it” and dictated “approve this” prepare the same exact decision preview.
The user must click **Submit approval**. Approved plans require another explicit
**Execute approved plan** confirmation. A missing proposal prompts investigation;
chat does not fabricate a proposal or silently execute a recommendation.

The browser sends only an opaque action ID, original context and `confirmed: true`.
The server holds the exact proposal/version/digest or typed configuration and calls
the same existing endpoint handler used by the workbench. That handler rechecks
trusted role, exact scope, freshness, current source state, immutable approval,
idempotency and independent readback. Model/browser fields cannot construct a
trusted actor or choose source operations/arguments. Wrong-role, stale, superseded,
expired and changed-context actions fail. Partial/unknown execution outcomes remain
failures or reconciliation work; a lost reply is retried through existing receipts.

Local origin/host protections are unchanged. Demo profiles remain role-test
stand-ins. The existing identity-switch reset is preserved: changing profile clears
chat/drafts and microphone state while retaining the route; the new reviewer asks
for a fresh current proposal preview.

## 8. Automation configuration

Weekday/time/timezone and quality-watch requests use the existing 08.3 contract and
`AutomationStore`. The preview states scope, read-only authority, trigger, timezone
and inactive background execution. Missing schedule cadence/time asks for details;
CT resolves to America/Chicago. **Save configuration** uses the existing handler
and idempotent store. It explicitly says background execution is not enabled.
Saving never activates a scheduler, listener, condition evaluator or workflow.

## 9. Voice and 10. UI integration

The existing click-to-dictate implementation is preserved: explicit consent,
editable transcript, no autosend, no authentication and cleanup on stop, cancel,
minimize, modal opening, route/profile change and unmount. Sending is disabled while
dictating. Search inserts its query in the scoped draft and never sends it.

Concierge stays floating/nonmodal with no page shift, existing gradients, responsive
sizing and modal precedence. New cards scroll in the conversation region. Prior-page
drafts are preserved separately and a scope-change notice is visible. Old-context
action buttons are disabled until the original context is restored. A response can
be stopped; any workflow already admitted remains independent and visible in Runs.

## 11. A–Q evaluation coverage

The additive `--include-concierge` extension retains every original Phase 07 hard
gate and denominator. A–Q cover grounding, cross-case summary, four-way routing,
unsupported actions, no self-approval, wrong role, stale execution, voice authority,
source injection, missing evidence, root-cause restraint, quantity/date accuracy,
eligible/ineligible touchless routing, escalation truthfulness, inactive automation,
acceptance/commitment separation and no private reasoning. Failed/missing probes
remain critical failures. SDK factory/runner tests use a stub client, never a key or
network model request. Deterministic hosts without an explicitly installed manager
double fail closed rather than defaulting to a paid manager.

## 12. Verification

Exact commands, results and changed files are in
[PHASE08_5_VERIFICATION.json](PHASE08_5_VERIFICATION.json). The completed source and
coordinator suites, full offline evaluation, MCP suite, final focused regressions,
frontend typecheck/build and browser matrices are recorded there. Browser runs are
**scripted integration testing with deterministic model responses**, not AI runs
or actual human approval. Paid live inference and browser-provider speech service
quality were not measured.

| Verification | Result |
|---|---|
| Source/backend | 483 passed |
| Full coordinator suite | 681 passed |
| Final host/workflow checks | 81 passed |
| Final Concierge checks | 13 passed, including A–Q and SDK boundary tests |
| MCP | 56 passed |
| Combined offline evaluation | 112 passed; zero critical failures |
| Browser matrix | 76 unique tests passed; 23 voice/search checks repeated after the focus fix |
| TypeScript and production build | Passed; existing 511.91 kB main-chunk advisory remains |

Representative captures: [Overview](screenshots/phase08-5/overview.png),
[quality](screenshots/phase08-5/quality.png),
[wrong role](screenshots/phase08-5/wrong-role.png),
[execution preview](screenshots/phase08-5/execution-preview.png),
[standard intake](screenshots/phase08-5/standard-handoff.png),
[inactive configuration](screenshots/phase08-5/automation-saved.png),
[mobile draft](screenshots/phase08-5/mobile-draft.png).

## 13. Optional live smoke — not run

Reuse the already-configured source/MCP/control-host processes and existing metadata
location from the 08.4C launch. Restart the control host with its **same** arguments
to load this code; do not initialize/reset the working source database. The prior
08.4C documented host invocation is:

```sh
DEMO_MODE=true PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.control_host --source-url http://127.0.0.1:18008 --mcp-url http://127.0.0.1:19082/mcp --metadata-dir .cache/phase08-4c/live-metadata --port 18082 --ui-origin http://127.0.0.1:5188
```

Use the actual existing metadata directory if your current host was started with a
different one. Startup does not call a model or provision credentials. Vite must
point `MOCK_API_URL` to that same source and `CONTROL_HOST_URL` to that host.

The six-message smoke is explicitly paid and must be invoked manually:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase08_5.live_smoke --host-url http://127.0.0.1:18082 --ui-origin http://127.0.0.1:5188 --allow-paid --output .cache/phase08-5/live-smoke-manual
```

It checks Overview, CR-017 evidence, QE-004 cause uncertainty, DR-009 readiness,
approval preview and CR-019 policy explanation. It never sends investigation,
approval or execution confirmations. The output directory must be new. Each result
records model, latency, tokens, intent/classification, service calls, visible cards
and a deterministic routing gate. A manual semantic review remains required: compare
cards to current sources and check uncertainty, authority and independent acceptance.
Do not treat a routing pass as proof of live semantic quality.

Offline verification commands:

```sh
.venv/bin/python -m pytest tests -q --basetemp=.cache/phase08-5/source
coordinator/.venv/bin/python -m pytest coordinator/tests -q --basetemp=.cache/phase08-5/coordinator
mcp_server/.venv/bin/python -m pytest mcp_server/tests -q --basetemp=.cache/phase08-5/mcp
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07 --include-standard --include-quality --include-delivery --include-concierge --output .cache/phase07/phase08-5-full
npm --prefix mock_apps_ui run typecheck
npm --prefix mock_apps_ui run build
```

Browser commands run inside `mock_apps_ui`, with the installed browser:

```sh
export PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Users/nelsonwang/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
npx playwright test --config playwright.concierge.config.ts
npx playwright test --config playwright.config.ts
npx playwright test --config playwright.phase08.config.ts
npx playwright test --config playwright.standard.config.ts
QUALITY_VARIANT=comparable npx playwright test --config playwright.quality.config.ts
DELIVERY_VARIANT=base npx playwright test --config playwright.delivery.config.ts
```

The recorded browser matrix also covers quality incomparable/no-alternative-supply
and delivery technical-blocked/future-conditional/wrong-configuration/partial-failure/
stale-proposal variants. All use isolated storage and real local HTTP/MCP boundaries.

## 14. Connected / simulated / preview matrix

| Surface | State |
|---|---|
| Concierge manager | Connected to configured SDK/model; offline doubles for verification |
| CR-017, CR-019, QE-004, DR-009 | Connected to existing source and governed host services |
| Demo profiles and synthetic lab event | Explicit demo stand-ins, not real identity or physical lab work |
| Browser voice | Browser dictation; editable draft only |
| Saved schedules/events/conditions/chat configurations | Persisted configuration; no background execution |
| Other catalog workflows and Operations | Preview only |

## 15. Persistence, limits and 16. next phase

Conversation state is bounded and process/session-only: up to 256 server turns,
24 browser turns, four simultaneous manager requests, four recent same-context
visible turns passed to the manager, 256 pending actions and 30-minute action expiry.
Reload, identity switch or leaving the control-plane app clears browser history;
host restart clears ephemeral chat references. Existing workflow runs, approvals,
executions and automation configurations remain durable in their existing stores.
No raw audio, credentials, hidden reasoning, SDK response objects or unrestricted
long-term memory are stored by chat. Model tracing is disabled for manager calls;
only safe model/usage/latency and service hooks are retained for 08.6.

Current facts are read at response time; separate source reads are not a distributed
transaction. Every consequential confirmation independently revalidates. Scope is
limited to the installed Helios cases. The manager selects intent/topic; concise
business summaries are deterministic source projections, not arbitrary freeform
answers. Unrecognized invocation wording requires a button confirmation. Existing
read/configuration services do not run unattended monitoring. Live model quality
and external speech recognition require the optional manual checks.

The next requested slice is **08.6 Operations / observability**. It has not begun.
