# Project instructions: mock enterprise foundation

## Current phase and purpose
Build the local, deterministic mock-enterprise APIs and five interactive source-system
UIs for a later agentic semiconductor-program-management demo. The supplier and its frontier
model lab customer are fictional. This phase is not an AI application build:
no model calls, OpenAI dependencies, API-key provisioning, paid services, or
agent implementation. Codex is the development tool, not the runtime.

## Read before work
Read README.md, docs/SCENARIO.md, docs/API_CONTRACT.md,
docs/ACCEPTANCE_TESTS.md, fixtures/seed.json, and the task's prompt file.
Business documents live in fixtures/documents/. These are proposed synthetic
scenario choices; stop and surface contradictions rather than silently changing
the scenario to make the implementation pass.

## Scope and implementation
- One Python FastAPI process, five logical system modules, file-backed SQLite.
- Use Python 3.12, uv, Pydantic, pytest, HTTPX, and Uvicorn; keep dependencies small.
- Read existing project instructions and files; preserve unrelated work. Do not
  replace an existing AGENTS.md or repository configuration without reconciling it.
- Use one React + TypeScript + Vite frontend in mock_apps_ui/ for Engineering,
  Validation, Manufacturing, ERP, and Program Planner. All business state crosses HTTP.
- Create no five separate deployments, Docker, message broker,
  cloud resources, MCP server, OpenAI SDK, or custom agent skill in this phase.
- Public business interactions use documented HTTP APIs. Future agents and their
  tools must not access database tables or fixture files directly.
- Engineering, Validation, and Program Planner have narrow authorized mutations.
  Manufacturing and ERP are read-only through public business APIs.
- Prefer clear domain handlers and validation over a generic CRUD framework.
- Local binding only; use DEMO_MODE explicitly. Mock identities are role-test
  stand-ins, NOT production authentication or proof of a real human's identity.

## Non-negotiable behavior
- Persist actual changes; do not return canned success or hard-code the best option.
- Calculate timing, money, evidence eligibility, and constraints in ordinary code.
- Store USD as integer cents; use explicit UTC scenario timestamps.
- Approval is server-recorded, role-restricted, and bound to an immutable plan,
  its version, its scope, and critical source versions. The automation role cannot
  approve itself. An approval ID alone is not authorization.
- Enforce idempotency, scoped uniqueness, optimistic concurrency, and per-system
  transactions. Do not pretend cross-system writes form one distributed transaction.
- The automation role cannot author test results, change engineering acceptance
  criteria, release manufacturing holds, or edit customer commitments.
- Preserve baseline vs forecast vs customer commitment. Scheduled is not tested;
  tested is not accepted; evidence missing is not hardware failure.
- No public reset/admin/failure-injection routes. Reset is a local CLI with a demo-DB
  guard and explicit confirmation; tests use isolated temporary databases.
- Audit mutations and important denials without logging credentials.
- Never read or print real secrets or scan unrelated personal/customer files.

## Verification and handoff
Implement tests with the code. Keep developer test expectations outside runtime
retrieval; only explicitly allowlisted business documents may be served.
A scripted smoke test must cross real local HTTP boundaries and be labeled
scripted integration testing, NOT an AI run or actual human approval.
Report commands actually run, actual results, skipped checks, limitations, and
remaining work. Do not state that a service was tested if it was only generated.
Stop after the five source-system UIs; do not expand into the agent/control-plane phase.

## Current authorization — Phase 05

The user's explicit [Phase 05 request](prompts/05_MULTI_AGENT_HARNESS.md) supersedes
the historical foundation-only prohibitions on AI/MCP work and the five-UI stop
point for this narrowly scoped phase. Preserve those foundations and the existing
`src/program_investigator/` single-agent baseline. Build the isolated read-only
`src/program_coordinator/` Agents SDK harness, with dependencies in `coordinator/`.
Use the existing authorized GPT-6 Astra API setup for bounded live verification.
All agent business access must go through the existing scoped MCP read tools and
HTTP APIs. No business write tools, execution/approval workflow, model routing,
control-plane UI, remote hosting, or additional orchestration framework is allowed.
Developer-only synthetic initialization and verification belong in
`coordinator/evals/`, are never agent-accessible, and use isolated cache storage.
The previous non-negotiable business authority, provenance and secret-handling
requirements still apply. Stop after the three read-only scenarios and handoff.

## Targeted workflow compatibility update

The [compatibility request](prompts/05_WORKFLOW_COMPATIBILITY.md) additionally
authorizes a host-only workflow registry, shared invocation boundary, persisted
case/run/activity metadata, and pure adapters around existing plan/decision
contracts. Preserve source API authority and SDK orchestration. Verification is
offline with isolated test storage; do not rerun paid models or working-demo
integrations. Yield recovery and delivery readiness remain illustrative. This
authorization does not start Phase 06 execution or the Phase 08 UI.

## Current authorization — Phase 06

The explicit [Phase 06 request](prompts/06_HUMAN_APPROVAL_EXECUTION.md) authorizes
CR-017 governed proposal/review/resume/execution and independent HTTP readback,
using the existing source Plan/Decision, Validation scheduling and Planner linking
contracts. Preserve all analysis agents and scoped MCP read tools. The host owns
trusted demo review, exact manifest enforcement and durable execution metadata.
Verification is offline, with isolated source and metadata storage; no paid model
runs, new orchestration framework, other workflows, touchless execution, Phase 07
evals, Phase 08 UI or Git operations are authorized in this phase.

## Current authorization — Phase 07

The explicit [Phase 07 request](prompts/07_EVALS_RELIABILITY.md) authorizes the
developer-only evaluation dataset, deterministic graders, reliability probes,
scorecards and optional paid CR-017 evaluation/semantic-grader entry points under
`coordinator/evals/phase07/`. This supersedes the Phase 06 prohibition on Phase 07
work only. Default verification is offline and uses isolated `.cache/phase07/`
source/metadata storage. Paid model runs require an explicit invocation; do not run
them by default. Preserve the existing SDK orchestration, prompts, source/MCP
permissions and exact Phase 06 approval/execution boundary. Yield and delivery
cases are illustrative offline observations only. No Phase 08 UI, additional
workflow execution, scheduler, customer communication or Git work is authorized.

## Targeted Phase 07 reliability correction

The [approved reliability fixes](prompts/07_RELIABILITY_FIXES.md) authorize bounded
reconciliation schemas, private rejected-review diagnostics, provenance-aware
current-source version tracking, and eval adapter/grader corrections. Preserve
the existing prompts, fixtures, source APIs, permissions, SDK orchestration and
Phase 06 approval/execution authority. Incomplete runs must remain failures.
Verification is offline with isolated storage; report before any paid live rerun.

## Final targeted Phase 07 stabilization

The [approved final stabilization request](prompts/07_FINAL_STABILIZATION.md)
authorizes a distinct narrow Validation clarification contract and a bounded
existing-case read-only status route within requirement-change analysis, including
the minimal runtime instructions and schema/routing checks needed for those two
fixes. Preserve strict full assessments, unknown/out-of-scope stops, all graders,
source/MCP permissions, fixtures and Phase 06 approval/execution authority. Use
offline regressions and isolated HTTP/MCP verification only. Preserve the original
failed live artifacts; do not automatically run paid models, implement other
workflows, start Phase 08 or perform Git operations.


## Current authorization — Phase 08.1

The explicit [Phase 08.1 request](prompts/08_1_CONTROL_PLANE_SHELL.md) supersedes
the historical Phase 08 UI prohibition only for the shared requirements, scoped
visual system, control-plane shell, Portfolio/Program/Case source reads and useful
previews. Follow [shared requirements](docs/PHASE08_CONTROL_PLANE_REQUIREMENTS.md)
and [slice plan](docs/PHASE08_IMPLEMENTATION_PLAN.md). Preserve all five source
apps, APIs, fixtures, authority and working state. No model calls, source writes,
new host execution adapters, active workers or Git operations in 08.1. Run offline
and isolated browser verification, inspect screenshots, report, then stop for
visual review before 08.2.

## Targeted Phase 08.1 visual refinement

The [approved refinement](prompts/08_1_VISUAL_REFINEMENT.md) authorizes scoped UI,
component and view-model improvements to the existing 08.1 shell. Follow the
updated shared requirements: semantic accents, concise Portfolio, prominent
truthful agent availability and a global floating Ask Stratos preview replacing
the docked assistant. Preserve source/runtime/approval/eval boundaries and all
existing routes. No paid calls, backend adapters, new agents, scheduler, live chat,
or Git operations. Real chat stays in 08.5. Verify offline and in isolated local
browser tests, report, then stop; this does not authorize 08.2.

## Current authorization — Phase 08.1 concierge refinement

The [latest explicit request](prompts/08_1_CONCIERGE_REFINEMENT.md) supersedes the
previous tiny-launcher, monochrome-masthead, status-pill and text-only rules.
Implement the reference-led blue structure, larger typography, plain StatusText,
centered source-record/agent dialogs and substantial global Stratos Concierge.
Explicit browser SpeechRecognition dictation into local editable drafts is
now authorized, with provider disclosure, permission, cleanup and bounded sessions.
Automated tests must mock speech: no real microphone, external speech or paid model
calls. Replies/actions remain Preview; preserve existing API, agent, MCP, source,
Phase 06 and Phase 07 boundaries. No backend work, Git operations or automatic
advance to 08.2. Verify, document current normative decisions and stop.

## Current authorization — Phase 08.1 Overview refinement

The [latest request](prompts/08_1_OVERVIEW_REFINEMENT.md) authorizes a lighter
shared gradient system, Overview landing/aliases, visual health summary, compact
tiles, global metadata search, source alerts and simulated demo-profile access.
Reuse existing read interfaces and profiles; retain fixed read-only control-plane
HTTP authority. Do not change agent/runtime/registry/MCP/source/Phase 06/Phase 07
contracts. Preserve disclosed explicit dictation; mock speech in all tests.
No paid calls, live smoke, production authentication, Git operations or later
slices. Verify, document the superseding design and stop.

## Current authorization — Phase 08.1 minimalist visual refinement

The [latest user request](prompts/08_1_MINIMAL_DESIGN_REFINEMENT.md) authorizes
online design research and scoped improvements to the current app's color,
composition and spacing. Slightly deepen the blue masthead/Concierge and pursue
Apple/OpenAI-inspired minimalism using the existing app. Preserve functionality,
source data, role/approval authority and explicit dictation. Run existing offline
and isolated browser checks with mocked speech; no model calls, backend changes,
Git operations or automatic advance to later phases.

## Current authorization — Phase 08.2

The [explicit Phase 08.2 request](prompts/08_2_CONNECTED_WORKBENCH.md) authorizes
thin typed local host HTTP adapters and the connected CR-017 workbench, Decisions,
trusted demo review, existing governed execution and independent readback. Reuse
WorkflowService, ActivityStore, CaseHarness and ExecutionService. Preserve source,
MCP, Phase 06 authority and Phase 07 prompts/graders/reliability. Only an explicit
manual investigation may use the existing configured model runtime. Automated
verification uses isolated state and deterministic doubles, including the 40-case
offline evaluation suite. No other workflows, generic writes, scheduler, connected
freeform chat, Phase 08.3+, commits or pushes. Stop after the 08.2 handoff.

## Current authorization — Phase 08.2.1

The [explicit downstream request](prompts/08_2_1_DOWNSTREAM_VALIDATION.md) authorizes
an explicit demo lab result arrival for an existing CR-017 job, existing-harness
reassessment, and a separate exact-evidence engineering decision. The synthetic
result belongs to Validation Lab under a distinct lab demo identity; automation
cannot author results or approve engineering adequacy. Preserve Phase 06 authority,
agent prompts, criteria, customer commitments and Phase 07 graders. No paid calls
by default, scheduler, other workflows, connected freeform Concierge or Git work.
Stop after downstream implementation and offline verification.

## Current authorization — Phase 08.3

The [explicit Workflows & Automations request](prompts/08_3_WORKFLOWS_AUTOMATIONS.md)
authorizes a registry-derived catalog, manual supported CR-017 invocation, real
run history/detail, and saved automation configuration metadata. Schedules,
source events, conditions and chat remain previews; no scheduler, listener or
condition evaluator is installed. Preserve Phase 06 and 08.2.1 authority, agent
prompts, source permissions and Phase 07 graders. Automated verification uses
isolated state and deterministic doubles; no paid model calls. No other workflow
backend, connected freeform Concierge, Operations implementation or Git work.
Stop after the 08.3 handoff; interactive scenario simulations are the next 08.4 slice.

## Current authorization — Phase 08.4A

The [explicit standard-touchless request](prompts/08_4A_STANDARD_TOUCHLESS.md)
supersedes the simulation-only next step in the 08.3 handoff. Implement CR-019 as
a connected standard route in the existing requirement-change family. Reuse the
Coordinator, three existing specialists, scoped MCP reads, WorkflowService and
ActivityStore. A deterministic host/source policy permits only a typed Validation
Operations intake; independent readback is required. This is separate from lab
authorization, scheduling, testing, engineering review and customer acceptance.
Additive source initialization is explicit and preserves the working CR-017 demo.
Automated verification uses isolated state and deterministic model doubles; no
paid model calls. Preserve original Phase 07 cases/hard gates and Phase 06 exact
human approval. No 08.4B/C, freeform Concierge, background triggers, Operations,
cosmetic redesign or Git work. Stop after 08.4A; next is 08.4B Yield / Quality
Exception Recovery when explicitly requested.

## Current authorization — Phase 08.4B

The [explicit quality recovery request](prompts/08_4B_QUALITY_RECOVERY.md) authorizes
connected QE-004 in the existing coordinator/runtime and host. Manufacturing owns
the exception/material/investigation and immutable recovery plan/decision;
Engineering owns the approved investigation procedure; Planner owns the approved
recovery task. Only standard investigation routing and exact Program Owner
approved recovery metadata are writable. No release, disposition, test changes,
allocation or ERP commitment mutation. Preserve CR-017/CR-019. Default tests are
isolated offline HTTP/MCP/SDK doubles; no paid model calls. Saved events and
Concierge remain previews. Stop after 08.4B; no 08.4C or Git work.

## Current authorization — Phase 08.4C

The [explicit delivery request](prompts/08_4C_DELIVERY_READINESS.md) authorizes
connected DR-009 through the existing coordinator, scoped reads, host governance
and isolated offline verification. Reuse QE-004 material and read CR-017 evidence
when required. A source-bound Program Owner decision may authorize only an exact
ERP delivery commitment and corresponding Planner link. Allocation review remains
analysis-only. Preserve original orders, quality disposition, validation authority,
CR-017/CR-019/QE-004 and working demo databases. No paid models, new runtime,
background execution, connected Concierge, Operations or Git work. Stop at 08.4C.

## Current authorization — Phase 08.5

The [connected Concierge request](prompts/08_5_CONNECTED_CONCIERGE.md) authorizes a
bounded conversational manager in the existing Agents SDK runtime. Reuse current
source reads, shared workflow invocation, exact approval/execution services, demo
identities, automation configuration store and voice draft UI. Ordinary chat and
dictation never approve or execute; exact structured confirmations use the existing
host boundaries. No generic writes, scheduler, external communications, Operations,
Phase 09 or Git work. Automated verification is isolated and offline; live model
smoke is optional and must be explicitly invoked. Stop after the 08.5 handoff.

## Current authorization — Phase 08.6

The [Operations request](prompts/08_6_OPERATIONS.md) authorizes thin read projections
of existing run/activity, governed execution, SDK metadata and eval artifacts,
bounded visible Concierge history, source-read health and integrated offline/browser
verification. Preserve all workflow authority, source permissions, historical eval
truth and working demo state. No paid models, new agents/traces, active schedulers,
Git operations or Phase 09 work. Stop after the integrated Phase 08 handoff.

## Current authorization — Phase 09.1

The [explicit reset request](prompts/09_1_DEMO_RESET.md) authorizes canonical
four-scenario demo restoration, a guarded local host demo-management boundary,
scoped orchestration reconciliation/archival, explicit UI/CLI confirmation and
deterministic baseline/restart verification. This supersedes the earlier no-reset
HTTP rule only for this host-only demo operation; no source business or MCP reset
tool is authorized. Preserve historical eval/trace artifacts, governed business
authority, existing workflows and unrelated state. Verification is isolated and
offline with model/speech doubles. No paid models, schedulers, Git cleanup/push,
redesign or Phase 09.2 work. Stop after the Phase 09.1 handoff.

## Current authorization — Phase 09.2

The [explicit product integration request](prompts/09_2_PRODUCT_INTEGRATION.md)
authorizes cross-workflow source/view-model consistency, a shared semantic case
state, coherent Overview/Program/Decisions/search/alerts/Concierge/Operations
projections, existing source deep links and reset/refresh/partial-failure hardening.
Preserve all four workflows, source authority, exact approvals, SDK orchestration,
historical eval evidence and Phase 09.1 reset. Verification is isolated and offline
with deterministic model/speech doubles. No new major capabilities, paid models,
background triggers, expanded permissions, architecture redesign or Git work.
Stop after the Phase 09.2 handoff; Phase 09.3 requires a new explicit request.


## Current authorization — Phase 09.3

The [explicit primary UX polish request](prompts/09_3_UX_POLISH.md) authorizes
browser-led information hierarchy, navigation, persona/demo-identity clarity,
source-backed case and agent visualizations, decision/evidence presentation,
Concierge interaction and accessible loading/error states across existing
capabilities. Preserve source data, real trusted roles, exact approvals, SDK
orchestration, all four workflows, reset and historical eval truth. Verification
is isolated and offline with model/speech doubles; inspect the actual browser
before editing UI and verify 1440×900, 1920×1080 and 1280×800 layouts. No paid
models, new major capabilities, background triggers, new approval architecture,
commits/pushes or destructive work. Stop after 09.3; later manual validation may
authorize further targeted UX fixes.

## Current authorization — Phase 09.4

The [explicit demo harness request](prompts/09_4_DEMO_HARNESS.md) authorizes a
supported local startup/status/prepare/check/stop helper, safe process ownership,
reuse of Phase 09.1 reset and baseline verification, an authoritative demo runbook,
presence-only model configuration checks and low-risk performance/error/loading
corrections. Preserve all source data, exact authority, existing runtime and
historical artifacts. Test cold start, persistence, reset and full regressions in
isolated storage without paid models or real speech. Do not reset working demo
state, substitute fake live intelligence, activate workers, perform Git cleanup
or start Phase 09.5. Stop after 09.4; this is not a code freeze and targeted fixes
discovered during later manual/live validation remain expected.


## Current authorization — Phase 09.5

The [explicit final validation request](prompts/09_5_FINAL_VALIDATION.md) authorizes
manual application validation, one paid golden-path analysis for each connected
case, required downstream reassessment, a small paid Concierge smoke set, and
targeted retests after diagnosed failures. Reuse the existing authorized model
configuration without exposing secrets. Use a dedicated clean demo session and
the existing prepare/reset/check harness; preserve unrelated working state and
historical live artifacts. Targeted functional, runtime, persona, visual, copy,
loading and replay corrections are allowed when justified by observed problems.
Preserve source ownership, exact approvals and all offline hard gates. Real browser
dictation may be checked once if available; voice never approves or auto-sends.
No new major capabilities, background execution, Git cleanup/push or slides.
Stop after the final 09.5 report for human review; do not declare a code freeze.


## Current authorization — Phase 10.1

The [explicit persona request](prompts/10_1_PERSONA_ACCESS.md) authorizes the shared
host capability projection, persona-aware navigation and actions, scoped queues,
Operations/session protection and identity-switch isolation. Preserve existing
per-workflow authority, source-app boundaries, maintenance reset and historical
artifacts. Follow the [current contract](docs/PHASE10_1_PERSONA_ACCESS.md). Verify
with isolated offline source/host/MCP/eval/browser checks and mocked speech. No
paid models, Git work, schedulers or Agent Workspace redesign. Stop at 10.1.


## Current authorization — Phase 10.2

The [visual Agent workspace request](prompts/10_2_VISUAL_AGENT_WORKSPACE.md) authorizes two local concept explorations, the selected agent-centered stage, a minimal scoped read-only telemetry adapter, business inspectors and an editable contextual Concierge draft. Follow [the workspace contract](docs/PHASE10_2_AGENT_WORKSPACE.md); retain Phase 10.1 capabilities and all source/runtime/approval/reset authority. Verify with isolated deterministic HTTP/browser fixtures and the current offline regressions. No paid model calls, new agents, monitoring store, workers, external provider, Git work or unrelated redesign. Stop after the 10.2 handoff.

## Targeted Phase 10 navigation and Overview refinement

The [navigation icon request and direct Overview follow-up](prompts/10_NAVIGATION_ICONS.md) authorize decorative Lucide icons in the existing persona-aware navigation metadata, Programs immediately after the Overview summary, and the Agent workspace/Needs attention row below Programs with matching panel treatment. Preserve route/tab order, capability filters, business/runtime/Concierge behavior and data. Verify relevant navigation/persona/workspace browser checks, responsive screenshots, typecheck and build. No new dependencies, paid calls, backend work or Git operations; stop after this cosmetic refinement.


## Targeted Phase 10 compact agent monitor

The user approved implementing the researched five-station monitor: equal agent stations, observed workload counts, a checkpoint observation strip, and freshness/health details. This supersedes the tiered stage presentation only. Preserve scoped HTTP telemetry, exact approvals, inspectors, persona/reset isolation and polling lifecycle. No new backend, monitoring store, paid calls or Git operations. See docs/PHASE10_MONITOR_REFINEMENT.md.

The subsequent user-approved manager-connections refinement restores Coordinator above four specialists, with structural lines and outward dots for observed active specialist work. It supersedes the equal-row arrangement only. Preserve recorded/stale distinctions, reduced motion, existing scoped telemetry and approval authority.

The latest user follow-up explicitly authorizes continuous decorative dot flow on all four manager connections, including recorded views, and semantic connection colors. Keep the visible relationship-animation caption, truthful agent states, and reduced-motion support. This supersedes the earlier activity-gated connector-motion rule only.

Latest user refinement: distinguish manager branches with green/amber/blue/purple, stop flow during idle/completed/stale observations, and show only specialist permission edges defined in controls.py GRAPH as static directional connections. Display metadata grants no authority; preserve runtime delegation guards and reduced motion.


Latest explicit visual simplification: remove all specialist-to-specialist lines, the connection legend and the Specialist connections disclosure. Retain four colored Coordinator branches with continuously moving decorative dots, including idle/recorded views. This supersedes the prior idle-stop and permission-edge presentation only; agent statuses, workload and authority remain unchanged. Reduced motion stops animation.

## Current authorization — Shared Knowledge retrieval foundation

The [explicit foundation request](prompts/10_SHARED_KNOWLEDGE_FOUNDATION.md) authorizes one shared version-aware Knowledge & Evidence retrieval service, provider-independent offline/OpenAI indexing, scoped profile/eligibility policies, exact-source follow-up, index lifecycle, read-only search UI and developer/operator index controls. Follow [the foundation contract](docs/PHASE10_KNOWLEDGE_FOUNDATION.md). Preserve structured source/MCP authority, all four workflows, prompts, approvals, source writes and reset. No paid calls in verification, broad agent integration, QE-011 trigger or Git operations. Stop after this foundation.

## Current authorization — Specialist knowledge integration

The [explicit integration request](prompts/10_SPECIALIST_KNOWLEDGE_INTEGRATION.md) authorizes bounded specialist retrieval profiles, exact-source verification, concise findings, run/Concierge provenance, Knowledge/case/Operations projections and offline retrieval/business-conclusion evals. Preserve the shared index, structured source authority, existing policy and human approval boundaries. No paid calls by default, arbitrary ingestion, unrestricted Coordinator search, autonomous QE-011 trigger or Git operations. Stop after this integration.

## Current authorization — QE-004 knowledge corpus completion

The [focused corpus request](prompts/10_QE004_KNOWLEDGE_CORPUS.md) authorizes three
controlled Quality publications, additive source metadata/installation, existing
shared-index sync, exact-source provenance and narrow Concierge applicability
fixes. Preserve operational facts, workflow and agent permissions, approval and
disposition authority, and the four-column document library. Verification is
isolated and offline across source, MCP, coordinator, RAG, workflow and browser
checks. Hosted indexing/search and model calls remain manual opt-ins. No new store,
agent, workflow, QE-011 trigger or Git work. Stop after this corpus enhancement.

## Current authorization — Bounded autonomous opening

The [explicit autonomous demo request](prompts/10_AUTONOMOUS_OPENING.md) authorizes
one manually armed, delayed Manufacturing quality_exception_created event for
isolated QE-011 / LOT-B-219. Reuse the shared yield workflow, source authority,
agents, RAG, activity, human review, Operations and demo reset. Normal startup and
navigation stay idle; generic saved automations stay inactive. Verify offline with
deterministic agents and isolated browser state. No paid calls during verification,
new runtime, general scheduler, main-case changes or Git packaging. Stop after the
bounded event path, reset/replay and handoff are verified.

## Targeted Phase 10 processing / idle visualization

The [latest direct user follow-up](prompts/10_AGENT_PROCESSING_STATES.md) authorizes
showing the full Coordinator/specialist roster with muted Idle stations, distinct
Processing color only for observed active work, and moving dots only on active
branches. Completed task history remains available. This supersedes the prior
participating-only display. Preserve unknown/stale distinctions, exact authority,
existing polling and reduced motion. Verification uses deterministic browser
fixtures; no paid models, business mutations, scheduler or Git operations.

## Targeted Phase 10 live demo runtime

The user's latest explicit live request authorizes the existing configured model
and API credential for CR-017, CR-019, QE-004 and DR-009, preserving all source,
MCP, approval and execution boundaries. QE-011 remains the scripted 60-second
opening. Follow docs/PHASE10_LIVE_RUNTIME.md. Use the existing live SDK path,
truthful per-run mode attribution and no scripted fallback on model failures.
Bounded paid verification is authorized for this change in isolated storage;
normal automated tests remain offline. Preserve the current demo source state
when changing its launch configuration. No Git operations or expanded authority.

## Targeted Phase 10 autonomous app entry

The [latest explicit request](prompts/10_AUTONOMOUS_APP_ENTRY.md) authorizes the
bounded QE-011 opening to arm once when a user enters the control plane, without a
human launch action. The host must serialize and deduplicate concurrent entries;
service startup remains idle, same-session reset does not loop, and a new session
or explicit replay can start a cleared opening. Preserve the eight-second source
event, real existing agents/telemetry, Program Owner handoff, reset/failure states
and all business authority. Saved generic automations remain inactive. Verification
is isolated and deterministic; no paid models, scheduler, broad listener or Git work.

## Targeted Phase 10 touchless QE-011 and concurrent workflows

The [latest request](prompts/10_TOUCHLESS_CONCURRENT_WORKFLOWS.md) supersedes automatic app entry and the canonical QE-011 human-review outcome. Restore explicit Prepare plus delayed event; allow only source-policy-qualified standard Manufacturing investigation routing and verified touchless completion. Keep consequential QE-004/CR-017 authority intact. Reuse the existing runtime for bounded independent concurrent runs, isolated activity/evidence, single-run workspace graphs and scoped reset. Verify source/host/MCP/RAG/eval/browser boundaries with deterministic doubles. No paid calls, general scheduler, new queue/runtime, expanded business authority or Git packaging.

## Current follow-up — Automatic touchless entry and full roster

The [latest direct request](prompts/10_AUTOMATIC_TOUCHLESS_ENTRY.md) supersedes
explicit Prepare and participating-only QE-011 display. Entering the local demo
arms one eight-second event automatically; all four specialists remain visible
with unused roles Idle. Preserve touchless QE-011, active-only animation,
concurrency, exact business authority and failure/replay truth. Entry deduplicates
across tabs and never resets records; reset leaves the current page at baseline
until reload or explicit Replay. Explain full reset without resetting working
data merely to answer the question. Verify offline with isolated deterministic
agents and browser fixtures; no paid calls or Git operations.

## Current follow-up — One-minute full-team opening

The [latest duration/full-team request](prompts/10_MINUTE_FULL_TEAM_OPENING.md)
authorizes explicit 60-second pacing of the deterministic QE-011 preview, visible
Coordinator phases, and a concrete Change Impact configuration/procedure scope
assessment through existing read permissions. QE-011 completeness now requires
all four specialists; preserve QE-004 and other workflows. Pacing must be disclosed
as scripted demo activity; live model latency remains observed. Preserve reset,
concurrency, touchless investigation authority and active-only animation. Verify
offline plus a timed browser opening; no paid model calls or Git work.

## Latest direct follow-up — Two-minute workspace presentation

The user's latest request supersedes the one-minute duration and visible pacing
disclosure. QE-011 deterministic processing now lasts at least two minutes. Remove
the Demo pacing, duration, Scripted agents, Selected task, Scripted demo and active
investigation metadata from the Agent workspace for every case. Preserve truthful
agent states, full-team participation, active animation, reset, source authority
and actual live-model latency. Verification remains offline; no paid model calls
or Git work.

## Approved Option B presentation implementation

The [explicit Option B selection](prompts/10_OPTION_B_RETHINK.md) authorizes the
workflow-first control-plane composition from the 13 September design review,
with the dark-to-light blue gradient, All programs links, real-record All status
filters and existing icons/agent visualization. Preserve all current source,
runtime, role, approval, execution and reset boundaries. Prototype state selectors
must not simulate state in the live app. Verify with isolated deterministic UI
checks and read-only live inspection; no paid models or working-demo reset.


## Current authorization — Five source-system UI redesign

The [explicit source-system redesign request](prompts/10_SOURCE_SYSTEM_REDESIGN.md)
authorizes research-led, category-specific frontend redesign of Stratos PLM,
Stratos TestOps, Stratos MES, Stratos ERP and Stratos ProgramOps. Internal system
names, URLs, API schemas, IDs, source ownership, workflow/agent/MCP/RAG behavior,
approvals, calculations, reset and automation semantics remain unchanged. The
main control-plane design is outside this scope. Verify with isolated offline
source/coordinator regressions and browser checks at 1440×900, 1920×1080 and
1280×800; capture before/after screenshots. No paid model calls or working-demo
reset. See docs/SOURCE_SYSTEM_REDESIGN.md for implementation and verification.

## Targeted CR-017 validation final check

The [approved final-check request](prompts/10_CR017_VALIDATION_FINAL_CHECK.md)
authorizes the interactive conceptual chip comparison in the existing Stratos
TestOps CR-017 publication panel. Source-backed scope and a clearly labeled
simulated passing-result preview precede the unchanged explicit lab publication.
Preserve API/approval/result authority, all other workflows and the control plane.
Verify targeted isolated browser/publication checks; no paid calls or demo reset.
