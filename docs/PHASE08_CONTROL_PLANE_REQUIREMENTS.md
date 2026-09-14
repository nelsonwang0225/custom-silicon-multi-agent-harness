# Phase 08 — shared product requirements

## Current Phase 10.2 Agent workspace

The [visual Agent workspace contract](PHASE10_2_AGENT_WORKSPACE.md) supersedes static role tiles and Preview-only agent activity. Preserve the focal Coordinator/four-specialist stage, wider left placement, compact states, exact run selection and separate human/external handoff. Use existing scoped read observations, truthful freshness, persona-aware business inspectors and editable unsent Concierge drafts. The light-blue shell and Phase 10.1 capability authority remain unchanged.

## Current Phase 10.1 persona access

The [persona capability contract](PHASE10_1_PERSONA_ACCESS.md) supersedes earlier universal seven-tab navigation and display-only profile rules. Preserve the four installed identities and exact business authority. Hide unauthorized surfaces/actions, retain disabled readiness controls for authorized actors, scope queues/search/Concierge, and invalidate old persona state on switch. Scoped case facts and independently governed source-app reads remain available as documented. Phase 10.1 alone did not authorize redesign; the explicit Phase 10.2 request above now governs Agent workspace.

## Current 08.1 darker blue and minimalist refinement

The [latest visual request](../prompts/08_1_MINIMAL_DESIGN_REFINEMENT.md) supersedes the preceding pale-blue palette and boxed Overview composition. Follow the [research and handoff](PHASE08_1_MINIMAL_DESIGN_HANDOFF.md). All existing functional, source-scope, status-text, demo identity, dictation, approval and execution boundaries remain.

- Keep a visible but restrained blue gradient across masthead and Concierge. The latest follow-up keeps darker blue at both edges and a lighter blue center, with no white stop: horizontal `#6F98C2` → `#B8CFE5` → `#6F98C2`, at 0% / 50% / 100%, with dark ink. Summary uses `#9FBEDC` → `#C5D9EB` → `#9FBEDC`. Use shared semantic tokens, neutral `#F7F8FA` canvas, white content surfaces, quiet borders and native fonts. Do not copy proprietary fonts, logos, glass effects or page layouts.
- Place the existing read-context disclosure and Refresh beside the Overview title on desktop; stack them after the title on narrow screens. Preserve scenario/read timestamps, stale/unavailable warnings and reader authority disclosures.
- Preserve the source-derived large summary, counts and baseline gate. Use a slimmer labeled health mix. Program cards sit beneath their section heading without another outer card. Agent tiles and attention items also lose their redundant outer containers. Detailed source information remains accessible through existing routes/dialogs.
- Retain seven navigation destinations, functional global search/account/alerts, per-context drafts and explicit voice cleanup. Give Open chat a clear white action surface; keep the larger floating Concierge and readable preview/mic states.
- Verify with existing browser, source-app, modal, search and mocked-voice regressions; inspect desktop/narrow/zoom layouts and sampled contrast. No source/backend/model changes or later-phase work.

## Earlier 08.1 Overview, search and demo utilities refinement

The [latest request](../prompts/08_1_OVERVIEW_REFINEMENT.md) supersedes the preceding solid-navy/no-gradient treatment, Portfolio landing labels and flat metric strip. All earlier business authority, plain StatusText, readable typography, focused dialogs and explicit browser dictation rules remain. This does not authorize later slices, production authentication, autonomous work or paid calls.

- Use shared light-blue gradient tokens for the masthead, Overview summary and concierge dock/header, with dark readable ink. Canvas `#F4F7FB`, surface white, ink `#1B2B42`, secondary `#52647A`, border `#DCE5EF`, action `#315FA9`, blue soft/mid/strong `#DDEAF7` / `#A8C7E2` / `#8AB2D4`. Brand gradient transitions through `#C8DDEE` to `#F7FAFE`; summary through `#B6D3EB`, `#E0ECF8` and white. Contrast adjustments may darken foregrounds. No animated gradients, presentation frame, global scaling or filled semantic status pills.
- Landing is **Overview**. `/overview` and `/portfolio` alias the canonical `/control/overview`; `/control` and `/control/portfolio` also remain compatible. Backend portfolio names/IDs stay unchanged. The seven destinations and Source apps destination remain. Overview has no body filters/search or hidden URL-filter selection. Programs retains detailed filtering.
- Overview explicitly displays available source records for PRG-A17, PRG-P01 and PRG-P02. One roughly 250–300px full-width summary replaces the old metric strip: program count, actual source-risk and current draft-plan counts, labeled health mix and an available next baseline gate. Cards and totals use exactly the same dataset. Unknown health stays explicit, not zero. Health is not acceptance; source baseline time is not a current commitment. Compact program tiles show name, stage, plain status and next baseline date. Long descriptions remain in details. Agent tiles show existing identities only, under one Agent roles · Preview label; responsibilities remain in their contextual dialog. At most three initial attention items retain necessary scheduling/acceptance distinctions.
- Masthead replaces the old concierge shortcut with global **Search Stratos...**, alongside alert bell, Log in/demo profile and existing source utility. Grouped keyboard-accessible search covers accessible loaded program/customer/case, plan/decision-reference, observation/document metadata and the existing workflow/agent definitions. It does not index document bodies, arbitrary files, unavailable records, host proposals or runs. Labels distinguish source records, recorded references and definitions/Preview. Case-insensitive ID/title/customer token matching preserves source scope. Always retain Open/Ask Stratos Concierge for empty, matching and unmatched queries. It opens the same instance and appends the query to a context-labeled editable draft without overwriting or sending it.
- **Demo access** selects only the existing reader/operator/engineering-approver demo profiles, not a real person. No credentials, password form or authenticated session. The control plane continues using its fixed reader API identity regardless of selected display profile. Display name/role, Demo identity, Switch profile and Exit demo are explicit. Switching/exiting clears search, overlays, read markers and concierge drafts and refreshes source reads; it grants no new server authority.
- Alerts come from open source cases with actual current draft plans, missing Planner follow-through or requested evidence gaps. Deduplicate by source scope, signal, record ID/version. Display source update time, never an invented notification time or agent attribution. Unread state is tracked in component memory for the current visit/profile. Mark read only changes presentation metadata; it cannot resolve operational work. Unavailable feeds and empty results are separate. No polling worker/model/scheduler is added.
- Concierge default dock is approximately 440×160px, expanded 544×720px capped to the viewport, with light brand gradient and readable dark text. Keep white conversation content, per-context local drafts, preview-only disabled sending, explicit browser SpeechRecognition, provider disclosure, actual listening/error state, Stop/Cancel and bounded cleanup. Search/alerts/profile popovers dismiss coherently; focused dialogs stop capture and make the page/concierge inert. Identity changes also abort capture. Never start speech or work from navigation or search input.
- Verify aliases, explicit scope/unknown counts, metadata matching/scope, Ask draft append, simulated identity/no write authority, source alerts/read markers, preserved modal and mocked speech behavior, all five source apps, typecheck/build and responsive screenshots. Capture Overview/search/alerts/demo access/expanded concierge at 1440×900, 1280×800 and narrow; inspect contrast, zoom and keyboard behavior. No paid evals, real microphone/external speech calls or live smoke. Record actual results and stop after this refinement.

## Historical 08.1 reference-led refinement and voice input


The [latest explicit request](../prompts/08_1_CONCIERGE_REFINEMENT.md) governs this implementation and subsequent slices. It supersedes the earlier near-white masthead, small typography, status pills, tiny default launcher and text-only/no-voice restriction. Older requests below remain historical context where compatible. This authorizes browser dictation input only; it does not authorize 08.2, live replies, backend changes or additional execution authority.

- **Structure and type:** deep-blue `#133A63` masthead at 72–80px, white navigation with blue selected underline, visibly pale-blue `#EDF4FB` canvas, spacious white work panels and a meaningful agent surface `#EEF0FA`. Emphasis `#E5EFFB`, action `#1463C6`, primary text `#172B43`, secondary `#526477`, border `#D9E3EE`, success `#176B45`, warning `#8A5200`, danger `#B42318`. Ordinary text needs 4.5:1 contrast; essential input outlines use the darker secondary token. These are Stratos product tokens, not an official Apple palette. Native system fonts only. At desktop 100% zoom use page titles 36–40px/700, section/dialog titles 24–28px, program titles 19–21px, body 16px, secondary 13–14px, generous 24–32px spacing and 14–18px panel radii. Do not scale the app globally to reach those sizes.
- **StatusText:** reusable plain semibold semantic text, transparent background, no pill padding, border or radius. Keep explicit health, Preview, Recorded and Simulated words. Filled actions and meaningful content panels are separate from status text.
- **Shell:** retain the seven navigation destinations and deep links. The actual masthead button **Ask Stratos Concierge** opens the same single global concierge as its dock. Opening never starts audio. Retain useful source-app access and truthful synthetic-demo context; do not add identity, security, live connectivity or notification claims. Scenario time and actual read time remain separate in the context disclosure.
- **Portfolio:** three useful scoped metrics (Programs, Needs review, At risk); unavailable host investigation telemetry is explained in the workspace, not a prominent number. Metric definitions and unknown-data behavior from the earlier refinement remain. Three source program cards share one spacious white section. A larger Agent workspace sits beside at most three attention items. Source events remain separate. Roles from the existing runtime registry appear by default as **Agent roles · Preview**, with one concise note that live activity is not connected and read-only role detail dialogs. No invented task, timer, completed result or approval CTA.
- **Case:** CR-017 has observed-state Evidence review / Human decision / Lab scheduling / Test results stages and a substantial two-column task panel. Requirements/evidence are on the left; the actual finding and next decision are on a pale-blue right surface. View evidence opens a scoped source record. A recorded approval needs the current approved source plan and its decision; scheduling needs an observed job. Evidence coverage, analysis, approval, physical results and customer acceptance remain distinct.
- **Focused dialogs:** use a reusable native web modal, approximately 960–1100px wide and at most 85dvh. Evidence uses a labeled real source-record preview on a tinted backdrop at roughly 55% and applicability/facts at 45%; no fabricated PDF or ingestion. Agent details provide a second meaningful use. Keep the header/close/footer stable, keyboard focus inside, background and concierge inert, Escape/close and original focus/scroll/filter restoration. Stop microphone capture synchronously before modality. Never stack dialogs. Stack and scroll content on mobile. Preserve source scope, ordinary React escaping and existing allowlisted document reads.
- **Stratos Concierge:** use this name in visible UI and accessibility labels. Default compact deep-blue dock is around 384px wide and 150px high, bottom-right with 24px margins, context/capability text, Open chat and an explicit mic control. A further minimized launcher remains available. Expanded nonmodal chat is around 480×680px with a deep header and white body, 21px title, 16px text, editable composer, mic/Stop/Cancel and disabled preview Send. No page shift/dimming, fake replies or backend invocation. Preserve separate route-context drafts in session memory; tabs in the same case share a draft. Respect focused page controls, native modal authority and short/visual viewports.
- **Explicit browser voice input:** runtime-detect `SpeechRecognition`/`webkitSpeechRecognition`, off by default. Before first start disclose that the browser may send audio to its speech provider; feature detection does not verify a service. Require the explicit mic action and disclosure confirmation, then browser permission. Show Listening only on actual active audio capture. Separate interim text; append final text once to the editable draft, never auto-submit. Cancel restores the original draft; Stop retains final text. Manual editing stops recognition. Abort on minimize/Escape, modal opening, route-context change, page exit/hiding and errors; reject late callbacks and never auto-restart. Hard limit 60 seconds. Handle unsupported recognition, permission denied, unavailable mic, no speech, network and interrupted service with usable typing. No raw audio retention, transcript logging, provider fallback, transcription server or claims of local/private/offline recognition. Spoken approval grants no authority.
- **Verification and stop:** automated speech checks use controlled constructors/events only, with no real microphone, external speech or paid calls. Report mocks separately from unverified user-run microphone behavior. Preserve all source apps, APIs, fixtures, runtime prompts/MCP scopes, Phase 06 authority and Phase 07 graders. Run relevant browser/type/build/source checks, inspect 1440×900, 1280×800, narrow, zoom/reflow, contrast, focus and reduced motion. Retain earlier screenshots, document actual sources/modes and stop after this refinement. Real governed replies/actions still belong to 08.5.

## Historical first 08.1 refinement — superseded where noted above


The [focused refinement request](../prompts/08_1_VISUAL_REFINEMENT.md) supersedes the original visual palette, overview density and docked-assistant interaction below. It does not authorize 08.2 or any backend/chat integration. The original request remains as historical product context.

- Use shared neutral tokens: canvas `#F7F8FA`, surface `#FFFFFF`, primary `#1D1D1F`, secondary `#5F6368`, border `#E3E6EB`. Blue action `#0066CC` / `#EAF3FF`; violet agent identity `#6D28D9` / `#F3EDFF`; green source-backed on-track/completed `#16794B` / `#EAF7EF`; amber waiting/risk/review `#9A5B00` / `#FFF4DF`; red actual blockers/failure `#B42318` / `#FFF0EE`. Neutral for unavailable/idle. Pair status with text. Minimum normal-text contrast 4.5:1. Native font stack; titles 30–34px, sections 18–22px, body 15–16px, supporting labels 13–14px.
- Concise overview, detail on demand: Portfolio header, scoped four-metric strip, three source focus-program cards, wider Agent activity + smaller Needs attention, collapsed gates/source activity. No invented progress. Retain complete case descriptions, evidence, decision authority and baseline/forecast/commitment distinctions in detail views. Scope all styles to `.cp-root`.
- Metrics: Programs = displayed source programs; Active investigations = unavailable until an existing safe host read interface is connected; Needs review = distinct current draft source plans on open source cases; At risk = source health in validation_risk, at_risk, manufacturing_constraint, recovery_active, blocked, waiting_on_customer. Unknown health makes At risk unavailable. Exclude illustrative entries and out-of-scope records. Waiting for a human is never computing activity. A source draft is not evidence of a reviewable host proposal.
- Prominent truthful Agent activity on Portfolio and Program. No existing source endpoint exposes host runs; show **Activity unavailable**, not zero or live activity. Optional role preview requires explicit selection, uses existing runtime role IDs/names and describes capabilities only. Source audit events stay separate. When later phases connect actual runs, distinguish running, recorded results, human wait, failure, escalation, incomplete branches and pending verification. Runtime completion alone never implies investigation success.
- One global bottom-right **Ask Stratos · Preview** launcher replaces the docked drawer and header shortcut. Open a nonmodal white floating Stratos Assistant window (~400×560 desktop), with no page resize or dimming. Drafts are per route scope and survive minimizing and same-app navigation; they are session-memory UI drafts only. Suggestions insert drafts, sending is disabled. No fake answers, model calls or workflow starts. Real governed chat integration remains **08.5**.
- Focus composer on open; Escape/minimize returns to launcher. Do not trap desktop focus. Yield when a focused page control would be obscured. Native evidence/review dialogs retain top-layer authority. Fit narrow/short visual viewports, safe areas and reduced motion; no voice or attachments.
- No paid calls, background workers, backend subsystem, new permissions, runtime/prompt/grader changes or Git operations. Verify existing routes/modes, scope/availability, drafts/focus/no-layout-shift, GET-only interactions, isolated source-app regressions, screenshots at 1440×900 and 1280×800 plus narrow/reflow. Stop after the refinement handoff.

The approved user request below governs all six slices except where superseded above. Screenshot references are composition only. Historical Phase 07 stops are superseded only for the current authorized slice.

Continue in the existing openai_aaa_takehome repository.
Implement Phase 08.1: shared product requirements, visual system, and the
control-plane shell. Do not implement all of Phase 08 in this step.

Read applicable AGENTS.md files, the frontend/backend structure, and the
latest workflow compatibility, Phase 06, Phase 07, and reliability handoffs.
Inspect actual interfaces before naming endpoints, stores, models or ports.
Preserve the existing five source-app UIs, APIs, fixtures and working state.
No branches, commits, pushes, destructive Git operations or unrelated cleanup.

FIRST: PERSIST THE PHASE 08 REQUIREMENTS

Create or update docs/PHASE08_CONTROL_PLANE_REQUIREMENTS.md and
docs/PHASE08_IMPLEMENTATION_PLAN.md using the requirements below.
These are shared requirements for every subsequent Phase 08 prompt.
Do not merely write a plan: implement the scoped 08.1 deliverables afterward.

PRODUCT

Build Stratos Silicon's custom-silicon program control plane, with Helios AI
as the existing main customer. Reuse existing program/case identifiers.
The product journey is:
attention -> evidence -> investigation -> decision -> action -> verified state.
It is not just a technical agent-monitoring dashboard.

Navigation:
Portfolio | Programs | Workflows & Automations | Decisions | Scenarios |
Knowledge & Evidence | Operations.
Cases are first-class detail pages under their programs, with deep links.
A persistent contextual assistant is available globally; it is text-only.

The six implementation slices are:
08.1 Requirements, design system, shell, portfolio/program/case views.
08.2 Connected CR-017 workbench and actual Phase 06 decisions/execution.
08.3 Workflow catalog, manual triggers and automation configuration previews.
08.4 Interactive scenario stories and broader illustrative capabilities.
08.5 Contextual chat through the same governed backend services.
08.6 Operations/evals visibility and integrated visual/functional verification.
Stop for review after each slice.

VISUAL DIRECTION — REQUIRED

Use the attached banking screenshots as composition references only:
compact branded header, clear horizontal navigation, strong page titles,
structured sections, visible process steps, contextual assistant.
Do not copy banking content, green branding, voice controls, or logos.
If screenshots are not attached in Codex, the written specification governs.

Design a minimalist, modern, OpenAI-inspired/Apple-like enterprise interface,
under Stratos branding. Do not imply OpenAI or Apple endorsement.

- Light theme: off-white canvas, white surfaces, black/charcoal primary text.
  Suggested starting tokens: canvas #F7F7F8, surface #FFFFFF, ink #171717,
  secondary text #52525B, borders #E4E4E7. Verify contrast in context.
- Black primary buttons; quiet secondary buttons. Muted status colors only
  where they convey meaning, always paired with text or an icon.
- Native system font stack:
  -apple-system, BlinkMacSystemFont, system-ui, "Segoe UI", sans-serif.
  Do not download, bundle or redistribute Apple/OpenAI font files.
- Page titles approximately 32–36px; section titles 20–24px; body 15–16px;
  supporting labels 12–13px. Prefer regular/medium/semibold, not thin text.
- Use a coherent 4/8/12/16/24/32/48px spacing scale; 10–14px surface radii;
  restrained borders and shadows. Do not make every element a rounded card.
- Compact top header, secondary horizontal navigation, responsive main
  content around 1280–1440px maximum width. No oversized marketing hero.
- Keep key decisions and program context visible without excessive scrolling.
- Use existing icons/components where appropriate. No emoji/robot branding,
  neon gradients, decorative 3D chips, glassmorphism, or animated agent swarms.
- Subtle transitions only. Respect prefers-reduced-motion.
- Keyboard navigation, visible focus, labeled controls, readable contrast,
  accessible chart descriptions, and no status communicated by color alone.
- Primary viewports: 1440x900 and 1280x800; also inspect 1920x1080, 1024px
  width and zoom/reflow. Navigation and drawers must not hide key controls.

VISUAL STORYTELLING

Use purposeful components rather than a wall of metrics:
- program lifecycle and milestone timeline;
- ranked attention/decision queue with explicit reasons;
- requirement -> evidence -> decision -> action dependency view;
- before/after requirement comparison;
- coverage/applicability matrix;
- option comparison with scope, cost, timing and owner;
- quantity breakdown and readiness gates;
- execution/readback timeline;
- evidence drawer with source, version, applicability and timestamp.
Each visual must have a question it answers and a meaningful drill-down.
No decorative charts, random data, unexplained AI scores or invented metrics.

CAPABILITY AND DATA TRUTH

Keep these separate in the model and interface:
1. Data origin: synthetic demo data.
2. Execution mode: Connected demo / Simulated / Preview only.
3. Freshness: current read / recorded result / stale / unavailable.

A recorded real run is not a fresh live run. A backend outage must not
silently replace connected data with a successful simulation.
Catalog metadata never grants execution authority.

At the end of Phase 08:
- 1B CR-017 material change: connected to the existing governed backend.
- 1A standard/touchless handoff: interactive simulation initially.
- 2 yield/quality recovery: interactive simulation initially.
- 3 delivery readiness: interactive simulation initially.
- Other lifecycle capabilities: useful, clickable previews.
- Manual supported CR-017 invocation: connected.
- Recurring schedules/events/conditions: saved previews, NOT active workers.
- Chat: connected for supported CR-017 operations; other modes clearly labeled.

Do not confuse the covered-evidence eval case with permission to implement
1A touchless execution. It still has its existing review policy.

GOVERNANCE AND ARCHITECTURE

Reuse the workflow registry, shared invocation service, case/run/activity
records, source adapters and ExecutionService. No second agent runtime,
parallel approval engine, new domain agents, or browser-owned business state.
Use existing frontend technology; avoid unnecessary migrations/dependencies.
Thin, typed host API adapters may be added in later authorized slices.
Persist new presentation/demo configuration separately from authoritative
source records; do not clone a competing operational database.
Scope CSS so existing five-app UIs do not accidentally change.

Agents investigate/recommend. The deterministic host enforces decisions and
exact execution. The SDK investigation currently finishes before the HOST
workflow pauses; do not describe it as SDK tool-interruption resumption.

Preserve the precise existing Phase 06 operations, identities and checks.
Do not invent additional approvers just to match a mockup. Existing demo
identity selection is NOT authenticated human identity; label that honestly.

Separate recommendation, proposal, decision, action attempt, readback,
run completion and business outcome. Runtime completed can mean escalation.
Scheduling is not testing, passing, acceptance or case closure.
Unknown/missing/stale information must remain visible, not become green/zero.
No automatic source mutations or model calls merely from navigation/polling.

SCENARIO CONSISTENCY

All views use shared entities and a consistent scenario snapshot.
Do not hard-code different dates/counts into chat, cards and case pages.
Use actual source dates for connected records. A simulation may use a fixed,
clearly shown scenario date; never rewrite signed source snapshots/digests.
Use isolated namespaces for simulations and connected records.
Mixed portfolio totals must disclose/exclude illustrative records by default.

The supplied screenshot/reference bank numbers are not our demo data.
The synthetic delivery example is 1,000 physical units: 600 released and
unallocated, 250 held, 150 allocated to another compatible Helios release.
800 requested implies a 200-unit supply gap. Supply eligibility does not
establish technical/customer readiness when CR-017 evidence is still pending.

VERIFICATION POLICY — EVERY PHASE 08 SLICE

Run relevant automated component, backend, integration and browser regressions
with isolated test data and deterministic model stubs. Preserve the existing
40-case offline eval hard gates and Phase 06 behavior when integrations change.
No paid agent/semantic runs by default; no repeated six-case live smoke gate.
The two targeted live cases passed after stabilization. Preserve the earlier
4/6 failed smoke report; do not turn it into a fresh six-case pass in the UI.

Use existing Playwright/browser configuration, including the installed-Chrome
override if needed. Do not blindly regenerate existing screenshot baselines.
Capture and inspect new screenshots, fix clipping/overlap/unreadable text,
and report limitations honestly if visual/browser inspection is unavailable.
No hidden secrets, private reasoning, local-file exposure or fabricated traces.

At the end of every slice report:
implemented scope; files changed; actual connected/simulated/preview matrix;
commands/results/skips; screenshots; preservation checks; limitations;
exact local launch URL/commands from this repo; and the next slice.
Do not declare later slices complete or continue automatically.

IMPLEMENT 08.1 NOW

Build the shared components, responsive shell and functioning navigation.
Start the assistant launcher/drawer as a clearly labeled UI preview only.
Build Portfolio, Program and Case layouts first, not technical Operations.

Portfolio:
- title "Program portfolio" and concise context;
- at most four compact summary metrics, derived from displayed records;
- prominent "Needs attention" queue with reason, owner and next step;
- approximately three program rows/cards at distinct lifecycle stages;
- milestone timeline and a secondary recent-activity section.
Keep Helios as the main program. Reuse other programs if present; otherwise
Nova Gen 2/pre-tapeout and Atlas Gen 1/production ramp are illustrative examples.

Program:
- customer/configuration/lifecycle context and freshness;
- next gate, risks and decision queue;
- case list with CR-017 and labeled illustrative 1A/QE-004/DR-009 entries;
- technical/validation/supply/commitment sections with connected drill-downs.
Do not invent a real backend case merely to populate a card.

Case:
- business question, owner, execution mode and actual outcome;
- lifecycle strip separating analysis, review, scheduling and physical results;
- summary, evidence, options/decisions and activity sections;
- substantive evidence drawers and links to the existing source apps.
Read existing records where safe adapters already exist. Otherwise clearly
mark presentation data as preview, not as a connected case that succeeded.

Other navigation destinations should open useful preview/detail layouts,
not dead links or empty "coming soon" pages. Deeper behavior belongs to the
later slice. Keep simulated traces explicitly simulated.

08.1 acceptance:
- portfolio -> Helios -> CR-017 -> evidence is navigable;
- secondary illustrative programs are explorable;
- deep-link reload/back navigation and filters work;
- assistant opens/closes without covering actions or losing focus;
- no source writes or paid model calls occur;
- existing five-app routes and styles still work;
- screenshots at 1440x900 and 1280x800 are visually inspected.
Stop after the 08.1 report so the visual direction can be reviewed.

## Interface findings for 08.1

- Existing React 19 / TypeScript / Vite app; source routes remain unchanged. Control plane lives at `/control`.
- Existing source GET `/api/v1/portfolio` supplies typed cases, coverage, milestones and audit observations. GET `/api/v1/programs` supplies names, customer, lifecycle and scenario time; inventory/order GETs support contextual drill-downs.
- Existing portfolio reader selector is a public mock identity, not authentication.
- No HTTP adapter currently exposes WorkflowService, ActivityStore or ExecutionService. Do not read their local artifacts in the browser. Connected host work is reserved for 08.2.
- Eleven existing source programs are available. Use Helios Atlas Inference (PRG-A17), Northstar Boreal (PRG-P01, qualification), Vela Stream (PRG-P02, integration review) as the default focus; allow all programs to be explored. Do not invent Nova/Atlas source programs.
- Source cases reuse source change IDs; these are not fabricated host CaseRecord IDs. Illustrative entries have a separate `preview-` URL namespace.
- Source CR-017 order ORD-1204 remains 100 units. The 1,000/600/250/150/800 delivery example belongs only to the DR-009 illustrative namespace.
- A current HTTP read reports transport freshness separately from historical source timestamps. It is never proof that physical evidence is recent or a model ran.

## Phase 08.2 — current connected authorization

The [08.2 request](../prompts/08_2_CONNECTED_WORKBENCH.md) supersedes earlier
read-only-shell restrictions for **CR-017 only**. The current visual system stays
in place. The [08.2 handoff](PHASE08_2_CONNECTED_HANDOFF.md) is the implementation,
authority, API, verification and manual-run reference.

The control host delegates investigation to WorkflowService/CaseHarness and
proposal preparation, exact review, execution and independent readback to the
existing ExecutionService. ActivityStore and existing checkpoints retain state.
No second workflow, approval or execution model is introduced. Browser inputs
contain closed CR-017 invocation fields or exact ProposalRef objects; they cannot
supply tool targets, source request arguments, roles, prompts or filesystem paths.
The installed demo actor map and the existing source services enforce authority.

Overview review counts now mean fresh reviewable **host proposals**, not draft
source plans or program risk. Agent activity is recorded/polled state. Searches
include scoped runs and exact proposal/decision references. Concierge can display
this context but replies/actions remain Preview and voice remains dictation only.
A source/host configuration mismatch disables the connection. An unavailable
host is unknown, not zero. A successful POST is not verified readback; scheduling
is not a test pass, engineering acceptance, hardware adequacy or customer acceptance.

Only explicit investigation clicks may invoke the existing configured model.
Automated checks use isolated source storage and developer-only model/fault
doubles. The five source apps and all source/MCP/Phase06/Phase07 authority remain
intact. Stop after 08.2; 08.3+ is not implemented by this request.

## Current authorization: Phase 08.2.1 downstream validation

The [downstream request](../prompts/08_2_1_DOWNSTREAM_VALIDATION.md) authorizes only
CR-017 synthetic lab result arrival, explicit existing-agent reassessment and a
separate exact-evidence engineering decision. See the
[implemented handoff](PHASE08_2_1_DOWNSTREAM_HANDOFF.md). The source-owned lab action
is explicit and demo-only; agents do not physically test hardware or author results.
Scheduling, physical completion, criteria pass, applicability, engineering approval
and customer acceptance remain separate. Customer acceptance/commitment are not
changed. Preserve existing visual design and Phase 06 authority. No paid runs by
default, other workflows, scheduler, connected freeform Concierge or later slice.

## Implemented Phase 08.3 boundary

[Workflows & Automations](PHASE08_3_WORKFLOWS_HANDOFF.md) now uses the installed
registry and existing invocation/history services. Actual CR-017 runtime and its
business outcome are separate. Configuration metadata supports structured schedules,
source events, conditions, manual intent and future chat, with bounded authority,
versioned edits and durable retries. Configured/Paused never means a running worker.
Phase 08.3 DOES NOT implement background scheduling, event listening or condition
monitoring. Yield, delivery and standard-change remain Preview until interactive
simulations exist. No configuration can override Phase 06 or 08.2.1 authority.
