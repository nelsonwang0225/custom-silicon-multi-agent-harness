Continue in the existing Stratos Silicon repository and Phase 08 thread.
Implement a focused Overview, masthead and Concierge refinement. Inspect the
current components, routes, read APIs, identity model, tests, AGENTS.md and
Phase 08 requirements before editing. Reuse the current implementation.

REFERENCE PRIORITY
- Screenshot 1: the current Stratos application to improve.
- Screenshot 2: the lighter blue visual language, modern composition, top
  search, notification bell and profile control.
- Screenshot 3: the strong overview hierarchy and large visual summary panel.
- Screenshot 4: the current tiles whose descriptions should be simplified.

Borrow those design patterns, not the banking data, stock chart, arbitrary
progress percentages, pink/yellow status pills or decorative outer mockup frame.
The application must fill its browser normally, not shrink inside a presentation.

Implement and verify the changes; do not stop at a design proposal.
No branches, commits, pushes, destructive operations or unrelated cleanup.

1. SCOPE AND SUPERSEDING REQUIREMENTS

Rename the landing experience from Portfolio to Overview.
Replace the solid dark-navy masthead/Concierge treatment with a coordinated
lighter-blue-to-white gradient system. Add global search, top-right account
access and alerts. Make Overview more visual and substantially less wordy.

This supersedes the earlier solid navy and no-gradient directions. It does
NOT supersede the requirements for plain colored status text, readable type,
truthful execution modes, contextual dialogs, or the existing voice-input flow.

Preserve agent prompts, runtime, workflow registry, source business data,
MCP scopes, Phase 06 approval/execution authority and Phase 07 graders.
No new autonomous workflows, production authentication system, background
agent loops, recurring schedulers or paid model calls in this slice.
Use existing read interfaces. Small additive presentation/search adapters are
allowed where necessary, but do not change source APIs or expand access.

2. LIGHTER BLUE VISUAL SYSTEM

Use shared tokens, not scattered CSS overrides. Starting palette:
- canvas: #F4F7FB
- surface: #FFFFFF
- ink: #1B2B42
- secondary text: #52647A
- border: #DCE5EF
- action: #315FA9
- blue-soft: #DDEAF7
- blue-mid: #A8C7E2
- blue-strong: #8AB2D4
- success: #176B45
- warning: #8A5200
- danger: #B42318

Suggested masthead/Concierge gradient:
linear-gradient(110deg, #8AB2D4 0%, #C8DDEE 55%, #F7FAFE 100%)

Suggested Overview summary-panel gradient:
linear-gradient(110deg, #B6D3EB 0%, #E0ECF8 65%, #FFFFFF 100%)

Adjust exact colors for legibility, but keep the visible light-blue-to-white
transition. Use dark ink on these lighter surfaces; white text must not fade
into their pale end. Use solid deeper-blue primary buttons where needed.

Apply the coordinated treatment to the masthead, Overview summary and
Concierge dock/header. Keep conversation content and ordinary cards white.
A quiet blue cast near the top of the page may fade into the neutral canvas.
Do not use animated gradients, rainbow panels, heavy glass blur or pink washes.

Keep status labels transparent: colored semibold text, optionally an icon.
No yellow, green or red filled pill backgrounds. Color alone is insufficient:
retain words such as At risk, On track, Pending review and Preview.

Use the native system-font stack. No font downloads or redistribution.
Keep page titles around 36-40px, section titles 24-28px, card titles 18-21px,
body 15-16px, and secondary labels 13-14px at 100% browser zoom.
Do not shrink text to fit more content. Use readable contrast and clear focus.

3. MASTHEAD AND NAVIGATION

Desktop masthead:
LEFT: Stratos logo/wordmark and brief product context.
CENTER: global search, replacing the current Ask Stratos Concierge button.
RIGHT: alert bell, account/profile control, and compact existing utility access.

Use approximately 72-80px height, balanced spacing and a 480-600px search field
when space allows. Use a dark logo variant on the light gradient if needed.
Do not reorder, recreate or remove the existing source-app destination.

Navigation becomes:
Overview | Programs | Workflows & Automations | Decisions | Scenarios |
Knowledge & Evidence | Operations

Rename visible landing-page labels, breadcrumbs, document title, accessibility
labels and search navigation entries consistently.
Preserve old /portfolio deep links through an alias or redirect using the
existing router. Do not rename backend portfolio concepts or source IDs.
Programs remains the detailed program-list/filtering destination.

4. FUNCTIONAL APP-WIDE SEARCH

Move the page-level Search programs or customers field into the masthead.
Placeholder: Search Stratos...
Optional shortcut hint: Cmd/Ctrl+K, only if it does not conflict with existing UI.
Do not leave a duplicate search field on Overview.

Search should find accessible app destinations and available record metadata:
- programs and customers;
- cases and their identifiers;
- workflow definitions;
- existing proposals/decisions;
- available evidence/knowledge records;
- agent definitions and recorded runs where exposed.

Use the actual available dataset and safe existing read interfaces. Do not
pretend an unloaded document body, unconnected system, or hidden record has
been searched. State coverage concisely in results/details where relevant.
No new vector service, external search provider, unrestricted file indexing,
new model calls or arbitrary URL/file reads.

Use a keyboard-accessible result popover/command panel with grouped results.
Each result has a concise title, object type and program/case context as needed.
Keep preview/simulated records distinguishable from connected records.
Selection opens the proper route or the existing contextual evidence dialog.
Avoid exact-name-only matching: support ordinary case-insensitive ID/title
and customer matching, while preserving scope and permission filtering.

ALWAYS include an Ask Stratos Concierge option:
- Empty query: Open Stratos Concierge.
- Nonempty query: Ask Stratos Concierge about "<query>".
- No results: retain this option without claiming no information exists anywhere.

Selecting it opens the same floating Concierge and inserts the query into its
editable draft, with explicit context. It must not auto-send or execute work.
If a draft exists, do not silently overwrite it. Keep chat capability truthful:
a preview assistant remains preview even when opened through search.
Search input never acts as a command executor.

5. TOP-RIGHT ACCOUNT ACCESS AND ALERTS

Implement useful interactions, not decorative icons.

ACCOUNT
Use an account icon and Log in label while no identity is selected.
Reuse existing real authentication only if already present and applicable.
Otherwise open a polished modal titled Demo access, clearly explaining that
this selects a demo profile and does not authenticate a real person.
Use existing allowed demo identities and the current access model.
After selection, show initials/avatar and a profile menu with name, role,
explicit Demo identity status, switch-profile and exit-demo controls.
Use initials or existing licensed assets, not invented employee photographs.

Do not create password fields, collect credentials, mint pretend authenticated
sessions or grant permissions from a browser role string. Demo selection must
not become proof of approval authority. Preserve every server-side Phase 06
check and the current read-only boundary where applicable.
Update or clear scoped UI/search/chat state on identity changes so one context
cannot silently carry into another.

ALERTS
Add an accessible bell icon opening a compact alerts panel.
Derive entries from available source-backed signals such as open blockers,
actual review requests, failed runs or missing Planner follow-through.
Do not fabricate pending approvals or say an agent detected a source signal
when no agent actually did.

Each alert: short title, program/case, actual recorded time if available,
and an Inspect action. Deduplicate by stable source identity/version.
Show an unread count only when unread state is actually tracked.
Mark read may update presentation-only metadata; it must not resolve the case,
approve anything or modify an operational record.
If the feed is unavailable, say so. If there are no alerts, show an empty state.
No fake notifications, automatic model polling or new background workers.

6. OVERVIEW: A LARGE VISUAL SUMMARY, NOT ANOTHER METRIC STRIP

Remove Focus programs and All lifecycle stages filters from Overview entirely.
Keep appropriate filtering on Programs. Do not simply hide Overview filters
while retaining an invisible selection. Define the Overview scope explicitly
in the view model and keep totals consistent with the programs displayed.

Recommended hierarchy:
A. Overview title and a quiet scenario/data-context control.
B. A prominent full-width visual summary panel.
C. Compact program cards.
D. Agent workspace alongside Needs attention.
E. Secondary gates/history through details or lower-page content.

REPLACE the old flat Programs / Needs review / At risk strip with the summary
panel. Do not show the same large metrics in both places.

SUMMARY PANEL
- Approximately 250-300px high on desktop, responsive rather than rigid.
- Light-blue-to-white gradient, generous padding, strong number/title hierarchy.
- Left: primary program count with concise context; smaller actual At risk and
  Needs review counts below.
- Right: a clear program-health visual derived from the same displayed programs,
  such as a labeled segmented horizontal bar for On track / At risk / Unknown.
- Include a compact next-gate/date callout if supported by the actual records.
- One clear View programs action; a real review-queue link only where useful.

The screenshot's 3 programs, 2 at risk and 0 reviews are current examples,
not constants. Derive every displayed count and graphic from actual records.
Needs review counts decision objects, not risk-colored program cards.
Unknown/missing data is not zero. Historical baseline dates must not be
presented as current commitments or an artificial "today" timeline.

Do not copy the banking financial chart. No invented time series, arbitrary
67% completion, guessed business savings or agent performance metrics.
Use a labeled empty/unavailable state when a truthful visualization is not
possible. A program-health mix is not a technical acceptance score.

7. SIMPLIFY THE PROGRAM, AGENT AND ATTENTION TILES

Program tiles should show only:
- program name;
- short lifecycle stage;
- plain colored status;
- Next gate date, marked baseline/forecast where applicable;
- an obvious click target/chevron.

Remove these kinds of sentences from Overview tiles:
- Assess the new customer evidence request.
- Reconcile sustained-load evidence with the requested memory profile.
- Review the extended-load reservation with platform engineering.
Move them to program/case detail rather than deleting source information.
Move long gate descriptions and configuration/revision strings into detail.

Use the existing Helios Atlas Inference, Northstar Boreal and Vela Stream
records and names unless the actual repository provides an updated source.
Do not invent alternate customer programs just for visual variety.

Agent workspace:
- keep the actual coordinator and specialist identities;
- use a concise static coordinator/specialist arrangement or compact tile grid;
- default tile content: icon, name and real state when available;
- remove repeated role-description sentences from the landing page;
- clicking opens the existing agent-details modal.
When only role definitions are available, use one visible Agent roles · Preview
label and do not imply the agents are currently working. Keep live connection
limitations accessible without a large error paragraph dominating the page.
No simulated moving task counters, activity pulses or invented traces.

Needs attention:
- show at most three initial items;
- case ID + short title;
- one meaningful status, with at most a short necessary qualifier;
- owner only where useful, plus Inspect.
Keep essential distinctions: evidence covered does not mean accepted; scheduled
with missing Planner follow-through does not mean verified execution.
Do not replace every detail with an ambiguous red/amber dot.

8. LARGER, LIGHTER STRATOS CONCIERGE

Use the same gradient family as the masthead, not the current navy block.
Dark readable title/controls on the light gradient; white conversation surface.
Retain the exact visible name Stratos Concierge.

At desktop 100% zoom target approximately:
- compact dock: 420-460px wide, 150-175px high;
- expanded window: 520-560px wide, up to 720px high;
- constrain both to viewport dimensions with 20-24px safe margins.

Compact dock should contain a clearly readable title, current scope, concise
capability/mic state, Open chat and the real microphone control.
Expanded window should have larger messages, comfortable composer spacing,
visible close/minimize, context and actual preview/connection status.

Keep it floating and nonmodal: no page shift, no dimmed page just for chat.
Allow minimizing so users can access content behind it. Avoid covering focused
controls; contextual task modals take precedence and make the concierge inert.
Use a viewport-fitting layout on small screens, not desktop dimensions.

Preserve existing real voice-input behavior, permission/error states and
click-to-dictate. Microphone off by default; no auto-send, voice approval or
new Realtime/voice-output integration. No fake listening indicators.
Preserve drafts safely. Opening through search uses this same instance.

9. CONTINUITY, ACCESSIBILITY AND DATA HONESTY

Preserve the contextual evidence/agent dialogs already implemented.
Use modals for focused tasks, not every navigation action.
Search/profile/alerts overlays need coherent focus and dismissal behavior;
avoid stacking multiple popovers or leaving a microphone active behind a modal.

Keep synthetic data, preview, recorded and current read states distinguishable.
A successful host runtime may still have an escalation or incomplete business
outcome. Do not turn those into green success to improve the screenshot.
No business mutation from UI navigation, alerts, search or profile selection.
Scope shared CSS so existing five source-app interfaces remain unchanged.

Use a responsive main container up to approximately 1440px, with 24-40px
gutters where space allows; avoid the current narrow-column appearance.
Use computed CSS sizing, never global zoom/scale hacks.
Maintain readable contrast, keyboard access, meaningful control labels and
reduced-motion behavior. Do not rely on hover-only access to important detail.

10. VERIFY AND REPORT

Run relevant component, presentation-adapter and browser regressions, type
checks and production build. Use the existing installed-browser override.
No paid evals, microphone capture, external speech calls or six-case live smoke.
Use mocks for voice and model-dependent states, labeled honestly.

Required tests:
- /overview works; existing /portfolio links remain compatible;
- Overview has no old filters or duplicate body search;
- global search finds known IDs/titles, groups results and enforces scope;
- unrelated/unavailable records are not fabricated in search;
- Ask Concierge works for empty, matching and unmatched queries without auto-send;
- demo account access is visibly simulated and does not create authority;
- alerts have correct sources/counts, and mark-read does not resolve business work;
- hero numbers/health graphic use the same dataset, including unknown states;
- agent-role previews are not shown as current live work;
- larger concierge fits the viewport, preserves drafts and voice cleanup;
- existing source apps, dialogs and deep links still work.

Capture and visually inspect at 1440x900, 1280x800 and a narrow viewport:
1. Overview with gradient masthead, hero, compact tiles and larger Concierge.
2. Global search with grouped results and Ask Concierge visible.
3. Alert panel.
4. Demo access/profile interface.
5. Expanded Concierge.
6. Narrow-screen layout and overlay behavior.

Compare against the references. Passing TypeScript is not visual completion.
The revision must visibly replace the old metric strip, remove descriptions,
lighten the masthead/Concierge, and implement the new top-right interactions.

Update Phase 08 requirements/handoff so later prompts preserve these choices.
Report files changed, screenshots, exact preview URL/start commands, test
results/skips, search coverage, demo-auth limits, alert sources, data mappings,
and confirmation of unchanged backend authority.
Stop after this refinement. Do not continue automatically into later phases.