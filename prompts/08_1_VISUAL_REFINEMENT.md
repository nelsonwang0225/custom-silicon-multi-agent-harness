Continue in the existing repository and current Phase 08 Codex thread.

Implement a focused Phase 08.1 visual and UX refinement.

The initial shell is a good foundation. We are refining it, not replacing
the application or advancing into the later backend/chat phases.

Use:
- the current Stratos app screenshot as the baseline;
- the earlier banking screenshots as interaction/composition references,
  especially the floating assistant in the bottom-right corner.

Do not copy their banking content, green theme, voice controls or branding.

Read the existing Phase 08 requirements, implementation plan, handoff and
current frontend components before editing.

Implement the changes, verify them in the browser, and report back.
Do not stop at a design proposal.

==================================================
1. OBJECTIVE
==================================================

The current Portfolio is too text-heavy and visually monochromatic.
Agent work is not prominent enough.
The assistant must become a floating customer-support-style chat widget.

The revised first screen should quickly answer:

1. Which programs need attention?
2. What are the agents doing or what did they most recently do?
3. What needs a human decision or follow-up?

Keep the broader program-control-plane concept.
Do not turn the homepage into a technical trace console.

==================================================
2. PRESERVE IMPLEMENTATION AND AUTHORITY
==================================================

This is primarily a presentation/component/view-model change.

Preserve:
- existing programs, case identifiers and source facts;
- five mock source-app UIs and APIs;
- workflow registry and shared invocation service;
- agent runtime, prompts and specialist roles;
- Phase 06 approval/execution authority;
- Phase 07 graders and reliability fixes;
- connected/simulated/preview distinctions;
- current routes and deep links.

Do not add:
- new agents or another orchestration framework;
- source-system write permissions;
- automatic investigations on page load;
- active schedulers, event workers or background model loops;
- live chat integration merely to demonstrate the floating window.

Reuse existing read interfaces and records when available.
If agent activity is not exposed through an existing safe read interface,
show a clearly labeled preview or unavailable state. Do not invent activity
or build a new backend subsystem for this visual refinement.

No paid model calls during implementation or testing.

No branch, commit or push work. Preserve unrelated local changes.

==================================================
3. REVISED COLOR AND TYPOGRAPHY SYSTEM
==================================================

Keep Stratos branding and the modern minimalist direction.
Add purposeful color through shared semantic tokens.

Starting palette:

canvas:          #F7F8FA
surface:         #FFFFFF
text-primary:    #1D1D1F
text-secondary:  #5F6368
border-subtle:   #E3E6EB

action:          #0066CC
action-tint:     #EAF3FF

agent-accent:    #6D28D9
agent-tint:      #F3EDFF

success:         #16794B
success-tint:    #EAF7EF

warning:         #9A5B00
warning-tint:    #FFF4DF

danger:          #B42318
danger-tint:     #FFF0EE

Adjust individual pairs if necessary to meet contrast requirements.
Use shared tokens rather than scattered hex values.

Application:
- Blue: primary actions, selected navigation and meaningful links.
- Violet: restrained agent identity/activity accents.
- Green: verified/completed steps or source-backed on-track status.
- Amber: waiting, risk or review-required states.
- Red: actual blockers, failures or critical conditions.
- Neutral: idle, unavailable, not started and ordinary metadata.

Use pale tints mainly for small badges, icon containers and selective
emphasis—not saturated full-page backgrounds or colored paragraphs.

Keep most surfaces neutral. Do not color every program differently.
No rainbow dashboard, neon effects, glassmorphism or decorative gradients.

Retain native typography:
-apple-system, BlinkMacSystemFont, system-ui, "Segoe UI", sans-serif.

Do not download or bundle Apple/OpenAI font files.

Use approximately:
- page title: 30–34px;
- section title: 18–22px;
- primary body/row text: 15–16px;
- secondary labels: 13–14px.

Do not reduce word density by shrinking fonts.
Verify normal text contrast of at least 4.5:1.
Pair status color with readable text/icons.

==================================================
4. SIMPLIFY THE PORTFOLIO STRUCTURE
==================================================

Use the existing navigation and routing. Do not redesign the entire
information architecture.

Make better use of the available desktop width:
- responsive content width up to approximately 1440px;
- consistent 24–32px desktop gutters;
- avoid a narrow central column surrounded by excessive blank space;
- preserve comfortable reading widths inside individual components.

Recommended page order:

A. Compact page header
B. Compact summary strip
C. Program overview
D. Agent activity + Needs attention
E. Upcoming gates / secondary activity

A. PAGE HEADER
- Title: "Portfolio".
- Remove decorative eyebrow copy and generic explanatory slogans.
- Consolidate scenario date, timezone, demo origin and data status into
  one quiet context area with expandable details.
- Keep scenario time distinct from actual source-read freshness.
- Keep search and filters compact; clear filters appears only when useful.

B. SUMMARY STRIP
Use at most four concise metrics:
- Programs
- Active investigations
- Needs review
- At risk

Populate only from actual available records with documented definitions.
Do not equate specialist count with investigation count.
Do not count waiting-for-human work as actively computing.

If a metric is unavailable, show an unavailable state, not an invented zero.
Keep illustrative records out of connected totals unless explicitly scoped
and labeled otherwise.

C. PROGRAM OVERVIEW
Display the existing three focus programs in compact cards or rows.
Use the current source program names, not new invented replacements.

Each should show only:
- program name;
- lifecycle stage;
- explicit health/status label;
- next gate and date;
- one important blocker or next step, when present.

Move configuration IDs, revision strings, detailed ownership, provenance and
secondary descriptions into program detail/expandable metadata.

Each program should have an obvious drill-down.
Do not invent readiness percentages or progress donuts.

D. AGENT ACTIVITY + NEEDS ATTENTION
Give Agent activity a prominent position, visible in the first desktop
viewport or immediately below the program overview.

Use a wider Agent activity panel and a smaller Needs attention panel.
Do not bury agent work beneath a long list of source-system updates.

E. SECONDARY CONTENT
Keep upcoming gates as a compact timeline or dated list.
Move lengthy recent source activity lower or into an expandable section.

At 1440x900, the first screen should show program status, meaningful agent
activity, and the leading attention items without a wall of prose.

==================================================
5. REDUCE VISIBLE COPY
==================================================

Aim for roughly 40–50% less explanatory prose in the default Portfolio view.
This is a design target, not permission to remove necessary meaning.

Prefer:
- short titles;
- one-line findings;
- status chips;
- counts;
- dates;
- one clear action;
- drill-downs for explanation.

Remove repeated instructional descriptions such as:
"Source lifecycle and health, with a workspace for every program."

Consolidate repeated labels like:
"Synthetic demo data"
"Connected demo - read only"
"Current read"

Use one page-level indicator when it applies uniformly.
Keep per-item execution-mode labels where mixed content makes them necessary.
Freshness and authority details must remain available on click/focus,
not only through inaccessible hover text.

Example presentation, only when supported by the underlying record:

Before:
"CR-017 · Long-context workload acceptance evidence"
"Existing evidence does not cover the requested requirement."
"Next · Assess the requested evidence gap before engineering review."

After:
"CR-017 · Workload change"
"Evidence gap"
Action: "Inspect case"

Keep the full description in the case view.

Needs attention:
- at most three items initially;
- short title;
- one reason/status;
- reference/owner where useful;
- a truthful next action.

Do not show "Approve" or "Review proposal" when no reviewable proposal exists.

Do not delete important qualifiers:
- scheduled is not tested;
- evidence coverage is not customer acceptance;
- simulated is not connected;
- stale is not current.

Shorten those qualifiers without changing their meaning.

==================================================
6. MAKE BACKGROUND AGENT WORK VISIBLE
==================================================

Add or refine an Agent activity component using the existing coordinator
and specialist identities. Reuse runtime IDs; do not invent a new agent team.

Show task-oriented information:
- agent/specialist display name;
- program and case;
- task being performed or last completed;
- actual state;
- supported result or next dependency;
- timestamp/elapsed time when available;
- link to the related run or case.

Illustrative presentation examples, NOT claims to seed into live data:

Validation
CR-017 · Checking evidence applicability
Running

Program planning
CR-017 · Schedule impact assessed
Recorded result

Coordinator
CR-017 · Waiting for engineering review
Awaiting review

Use actual data to determine the wording and state.

A small lifecycle strip may show:
Intake -> Evidence -> Recommendation -> Human review

Only mark observed stages as completed.
Do not invent percentage progress.

If multiple specialists actually ran in parallel, the UI may show parallel
rows or branches. Do not impose a misleading single linear execution order.

TRUTHFUL STATES
- Actual running record: Running.
- Completed historical work: Recorded result / Last run.
- Waiting for a person: Awaiting review, not Running.
- No current runs: No investigations running.
- Data unavailable: Activity unavailable, not zero activity.
- Demonstration-only data: Preview or Simulated.

Do not animate idle or historical agents as though they are working.
Do not use fake typing, rotating task text or synthetic timers as live activity.
An optional illustrative view must be explicitly selected and labeled.

Source events are not agent work:
an imported engineering decision cannot be relabeled as an agent decision.

Keep raw tool calls, token counts, trace IDs and JSON inside expandable
details or Operations, not the default Portfolio.

Runtime completed does not automatically mean investigation succeeded.
Display escalation, incomplete evidence, failed branches and pending
verification accurately.

Any polling must use existing lightweight read endpoints only.
No model calls, workflow starts or writes from polling/navigation.

==================================================
7. REPLACE THE DRAWER WITH FLOATING CHAT
==================================================

The primary assistant entry point must be a persistent bottom-right
floating launcher, like a customer-support widget.

This replaces the current header-only/docked-drawer interaction.

COLLAPSED
- A compact rounded launcher labeled "Ask Stratos" with a chat icon.
- Fixed to the bottom-right, approximately 24px from desktop edges.
- Blue primary treatment, with optional restrained violet icon detail.
- Visible across control-plane pages.
- No green "online" indicator unless a real connection state supports it.
- Preview status remains explicit while chat is not connected.

OPEN
- Clicking opens a floating chat window above the page.
- Approximately 380–420px wide and 520–600px high on desktop.
- Bound size/position to the viewport.
- Rounded white surface, clear border and restrained shadow.
- Do NOT push, resize or shift the main page.
- Do NOT dim the page or create a desktop full-screen modal.
- Do NOT navigate to a separate chatbot page.

WINDOW CONTENT
- Header: "Stratos Assistant".
- Context: Portfolio, or current program/case.
- Preview/connection state.
- Minimize/close control.
- Scrollable conversation area.
- Composer area and concise suggested questions.

Suggested questions:
- "What needs attention?"
- "What are the agents working on?"
- "Explain this case."

Show suggestions only when relevant to the current scope.

CAPABILITY
This step implements the floating interaction and preview UI.
Do not build Phase 08.5 chat integration now.

Reuse any existing preview behavior truthfully.
Draft typing and suggested-question insertion may work.
If sending is not connected, make that explicit and do not fabricate a live
model answer or pretend an investigation was launched.

One global assistant instance only.
Remove the prominent duplicate header button, or make any retained shortcut
open the exact same floating instance.

Keep draft/context state coherent across navigation.
Do not silently apply a previous case's draft action to another case.
Minimizing must not discard a draft.

ACCESSIBILITY / RESPONSIVENESS
- Clear accessible labels and keyboard controls.
- Opening places focus appropriately.
- Escape/minimize closes the window and returns focus to the launcher.
- Nonmodal desktop chat must not trap the user away from the page.
- Ensure keyboard-focused page controls are not completely obscured.
- Respect the app's overlay hierarchy; do not cover active approval dialogs.
- On narrow screens, fit within viewport and safe areas.
- Keep composer accessible when the mobile keyboard appears.
- Respect reduced motion.
- No voice, microphone, audio, attachments or additional chat features.

==================================================
8. APPLY SHARED REFINEMENTS CONSISTENTLY
==================================================

Apply the shared color, type, chip, button and floating-assistant system
across the existing Portfolio, Program and Case views.

Do not rebuild every page or add later-phase workflow behavior.
Do not remove evidence, decision or verification detail from the underlying
case. Use progressive disclosure.

Scope styles to the control plane so the five source apps do not change.

Update:
- docs/PHASE08_CONTROL_PLANE_REQUIREMENTS.md
- the Phase 08 implementation plan/handoff

Explicitly record:
- the new accent palette;
- concise overview/detail-on-demand approach;
- prominent truthful agent activity;
- floating chat replacing the docked drawer;
- real chat integration still belonging to 08.5.

This prevents later prompts from restoring the older design.

==================================================
9. VERIFICATION AND STOPPING POINT
==================================================

Use the existing frontend/component/Playwright setup.
Run relevant regression tests, type checks and production build.
Run relevant backend/view-model tests if data mappings change.
Do not weaken assertions or rewrite unrelated screenshot baselines.

Test:
- navigation, filters and deep links still work;
- metrics reflect actual scoped records;
- missing activity is not represented as zero or live activity;
- recorded agent work is not shown as currently running;
- completed-but-escalated runs are not shown as successful investigations;
- source events remain distinct from agent events;
- assistant opens, minimizes and preserves draft/context correctly;
- opening chat does not shift the desktop layout;
- chat does not launch models/workflows or bypass authority;
- preview/simulated states remain distinguishable;
- existing source-app routes/styles still work.

Capture and visually inspect:
1. Portfolio with launcher collapsed.
2. Portfolio with floating chat open.
3. Program page with agent activity.
4. Case page showing evidence/decision status.
5. Narrow-viewport chat behavior.

Verify at 1440x900 and 1280x800, plus a narrow viewport.
Check enlarged text/reflow, keyboard focus and reduced motion.
Fix clipped text, tiny labels, overlap and broken scrolling before reporting.

Report:
- files changed;
- screenshots and exact local URL;
- before/after design changes;
- copy reduction examples;
- where agent activity comes from;
- actual versus preview behavior;
- tests run/results/skips;
- remaining limitations.

Stop after this refinement.
Do not automatically continue into 08.2, live chat or workflow scheduling.