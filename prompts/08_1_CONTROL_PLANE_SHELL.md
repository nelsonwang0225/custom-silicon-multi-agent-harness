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