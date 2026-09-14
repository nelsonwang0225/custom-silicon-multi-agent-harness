Continue in the existing Stratos Silicon repository and Phase 08 thread.
Implement a reference-led Phase 08.1 design refinement, plus voice INPUT for
the floating concierge. Do not rebuild the agent backend or advance through
all remaining Phase 08 slices.

Read the current frontend, applicable AGENTS.md files, Phase 08 requirements,
latest handoff and existing component/test conventions before editing.
Preserve unrelated work. No branches, commits, pushes or destructive Git work.

REFERENCE PRIORITY
1. The current Stratos screenshot shows the starting point, not the target.
2. The banking screenshots define the desired composition and visual scale:
   substantial colored masthead, clear navigation, large typography, spacious
   task panels, focused document-review dialogs and a visible floating concierge.
3. Use Stratos content and a blue palette, not banking content or green branding.

This request supersedes the earlier tiny launcher, text-only/no-voice rule,
colored status chips and almost entirely white masthead. Keep the existing
business/governance requirements.

1. DESIGN OUTCOME

Make a visible compositional improvement, not another small badge/link recolor.

At desktop size the page must have:
- a substantial deep-blue masthead;
- a visibly pale-blue page canvas;
- white content surfaces with generous internal spacing;
- much clearer title/body hierarchy;
- a prominent agent workspace;
- plain bold colored status text, NOT colored status pills;
- a substantial floating Stratos Concierge;
- working contextual in-app preview dialogs.

Use Apple-inspired hierarchy, restrained semantic color, readable system
text and progressive disclosure. Do not claim this is an official Apple
palette or that Apple prohibits badges. Removing badges is this product's
explicit preference. Do not copy native-platform behaviors blindly to the web.

Useful design/implementation references:
https://developer.apple.com/videos/play/wwdc2025/359/
https://developer.apple.com/design/human-interface-guidelines/typography
https://developer.apple.com/design/human-interface-guidelines/color
https://developer.apple.com/videos/play/wwdc2022/10001/
https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition

2. APPLY COLOR TO STRUCTURE, NOT JUST LABELS

Use these starting semantic tokens, adjusting pairs only for accessibility:
brand-deep:        #133A63
brand-action:      #1463C6
page-canvas:       #EDF4FB
surface:           #FFFFFF
surface-emphasis:  #E5EFFB
surface-agent:     #EEF0FA
text-primary:      #172B43
text-secondary:    #526477
border:            #D9E3EE
status-success:    #176B45
status-warning:    #8A5200
status-danger:     #B42318

Required application:
- Masthead: solid brand-deep, white Stratos logo/wordmark and readable controls.
- Navigation: white, with blue selected text and a clear underline.
- Canvas: visibly pale blue, not near-identical to the white cards.
- One meaningful agent/summary surface: a restrained blue/indigo tint.
- Primary buttons and links: brand-action.
- Concierge dock/header: brand-deep; expanded conversation body: white.
- Main work panels and document pages: white.

Do not turn every card a different color. No rainbow tiles, decorative
multicolor gradients, glass effects on content or blue paragraphs everywhere.
Colored surfaces and plain status text are intentionally different treatments.

Replace yellow/green/red background chips such as Validation risk, At risk,
On track, Evidence gap, and Scheduled with a reusable inline StatusText:
- semantic colored text;
- semibold weight;
- optional meaningful small icon;
- transparent background, no pill padding/border/radius.
Retain the explicit status words so color is never the only signal.
Buttons, selected controls and actual content panels may retain fills.
Render Preview/Simulated/Recorded labels as concise text, not decorative chips.
Do not remove these distinctions to make the screen cleaner.

3. FIX TYPOGRAPHY AND DISPLAY SCALE

Inspect computed CSS at 100% browser zoom. Do not use global zoom, transforms,
or screenshot scaling to make the interface look larger.

Use the native stack:
-apple-system, BlinkMacSystemFont, system-ui, "Segoe UI", sans-serif.
No font downloads or redistribution of Apple/OpenAI assets.

Desktop targets in CSS pixels:
- Page title: 36-40px, weight 700, line-height around 1.15.
- Section/dialog title: 24-28px, weight 600-700.
- Program/card title: 19-21px, weight 600.
- Key number or decision outcome: 30-36px where justified.
- Body: 16px, weight 400, line-height 1.45-1.6.
- Secondary information: 13-14px, readable contrast.
- Navigation/buttons: 14-16px.

Titles must clearly outweigh descriptions. Do not bold every sentence.
Use shorter descriptions rather than tiny fonts. Avoid long all-caps eyebrows.
Allow text enlargement and wrapping; never truncate a consequential status.
Use 4.5:1 contrast for ordinary text and adequate non-text control contrast.

Use a responsive content width around 1280-1360px on large desktops with
24-40px gutters. Keep text blocks comfortably narrower inside panels.
Use consistent 24-32px card padding, 24-32px section gaps and 14-18px radii.
Do not squeeze all content above the fold; scrolling is preferable to tiny UI.

4. REBUILD THE SHELL'S VISUAL HIERARCHY

Masthead: approximately 72-80px desktop height.
Left: existing Stratos mark and Program control plane context, in white.
Center: an actual "Ask Stratos Concierge" button/command field that opens the
same floating concierge. It is not a fake search bar and does not start audio.
Right: existing useful controls such as Source apps and actual demo context.
Do not add "Secure session", live connectivity, notifications or authenticated
identity claims that the implementation cannot support.

Keep the existing seven navigation destinations and deep links intact.
Use approximately 48-52px navigation height with readable spacing.
Consolidate demo/freshness metadata into a quiet context line/details control.
Keep scenario time separate from actual read time.

5. PORTFOLIO: SHOW THE SITUATION, NOT A REPORT

Retain existing program identities and facts.
Use a large Portfolio title, compact filters and at most 3-4 useful metrics.
Metrics come from actual scoped records. Missing data is not zero.
Do not present unavailable agent telemetry as a prominent numerical metric;
explain connection status in the agent workspace instead.

Program overview:
- three spacious program cards/rows in one white section;
- title, stage, plain colored status, next gate and one next step;
- important labels visibly larger than metadata;
- move raw configuration IDs, verbose caveats and full provenance into details.

Main work area:
- a larger Agent workspace alongside a smaller Needs attention queue;
- no more than three attention items initially;
- short finding, owner/reference and one truthful next action;
- no approval CTA unless a reviewable proposal actually exists.

Agent workspace:
- connected current activity when available;
- last recorded work clearly labeled as recorded, not running;
- otherwise useful agent-role tiles derived from the existing registry,
  explicitly labeled "Agent roles · Preview";
- a concise note when live activity is not connected, rather than a large
  empty error card with several repetitive sentences;
- role tiles may open a read-only detail dialog showing responsibilities,
  sources and scope, without inventing a live task or result.

Do not fabricate agent activity, success counts, timers or live animations.
Do not relabel source-system events as agent decisions.
Do not start models/workflows by navigating, refreshing or polling.

6. USE THE REFERENCE'S TASK-REVIEW PATTERN ON CASE PAGES

For CR-017, reuse the reference composition with semiconductor content:
- a clearly scoped case heading;
- a lifecycle strip based only on observed states;
- a substantial two-column work panel;
- left: evidence/requirements summary;
- right: the actual finding or next decision on a pale-blue surface;
- one supported primary action, such as View evidence.

Possible stage labels are Evidence review -> Human decision -> Lab scheduling
-> Test results. Use the repository's actual state mapping, not a hard-coded
success sequence. Parallel investigations need not be forced into a linear run.

Do not show an agent as approving engineering work. Preserve distinctions among
analysis complete, escalation, approval, scheduled, tested and accepted.
Apply the shared visual changes to Program and other existing pages without
inventing later-phase functionality.

7. ADD CONTEXTUAL IN-APP WINDOWS

Implement a reusable accessible dialog using existing components or native
web facilities, not a new windowing framework or external browser window.
Use it for focused tasks, not all navigation.

Required working example: View evidence.
- Opens inside the app, centered over a dimmed background.
- Approximately 960-1100px wide, constrained to viewport width and 85dvh.
- Clear header/title, visible close control and stable footer/actions.
- Left approximately 55%: readable document/source-record preview on a light
  tinted backdrop. Right approximately 45%: relevant facts, applicability,
  version, finding, and supported next actions.
- Use an actual available document through approved source interfaces.
- If the evidence is a structured record rather than a PDF, render a labeled
  "Source record" view. Do not invent a PDF, attachment or extracted finding.
- Opening a preview is read-only and does not grant approval.

Add at least one other meaningful contextual dialog, such as Agent details
or Case summary. An option comparison may use this pattern where actual option
records exist; otherwise keep it clearly preview-only.

Do not add upload ingestion because the banking reference happens to show it.
Do not expose arbitrary local paths or build a generic file-fetch endpoint.
Escape/sanitize source content and preserve program/case access scope.

Modal behavior:
- background and floating concierge inert while the modal is active;
- proper dialog name, focus placement/trap, Escape/close, and focus restoration;
- preserve underlying filters, scroll and route;
- stop microphone capture before opening a modal;
- no nested modal stacks;
- mobile layout stacks preview and details with usable scrolling.
Normal program/case navigation still uses routes, not modals for everything.

8. RENAME AND ENLARGE THE FLOATING ASSISTANT

Use the name "Stratos Concierge" throughout visible UI and accessibility labels.
Update old Ask Stratos / Stratos Assistant labels and related tests/docs.
Do not rename backend agents merely to rename the interface.

Compact desktop state:
- a substantial floating concierge card, approximately 360-400px wide and
  120-150px tall, rather than a tiny pill;
- fixed bottom-right with 24px margins;
- deep-blue surface, white title, concise context and real capability state;
- clear Open chat and microphone controls;
- the microphone control explicitly starts dictation; opening chat alone does not.
Allow further minimizing where necessary, but preserve a discoverable launcher.

Expanded state:
- floating nonmodal window approximately 480px wide and 640-700px high,
  capped to the available viewport;
- no layout shift or background dimming;
- deep-blue header, white readable conversation body, generous spacing;
- 20-22px concierge title and 16px message text;
- context line for Portfolio or current program/case;
- minimize/close, scrollable messages, editable composer, microphone and Send;
- relevant suggested questions that insert into the draft.

Use one global concierge instance. The masthead and floating controls open it.
Preserve draft and context safely; do not apply a previous case's action to a
new case. Avoid obscuring active controls and respect the modal overlay layer.

Preserve actual chat capability: if replies/actions are still preview-only,
state that clearly. Voice input may work before backend replies are connected.
Do not generate canned responses while labeling them as live intelligence.

9. IMPLEMENT REAL VOICE INPUT, NOT A DECORATIVE MIC

Scope: explicit click-to-dictate into an editable chat draft.
This is not a full voice-call agent, voice output, always-on listening or a
new Realtime backend. Real chat/action integration remains its existing phase.

Reuse an existing implemented dictation facility if present. Otherwise add a
small browser SpeechRecognition adapter with runtime feature detection, using
SpeechRecognition/webkitSpeechRecognition where actually supported.
Do not assume support from the browser name or that recognition is local.

Behavior:
- microphone off by default;
- start only after the user explicitly presses the mic and grants permission;
- display Listening only while recognition is actually active;
- show real interim/final transcription and an obvious Stop/Cancel control;
- preserve the existing draft and avoid duplicating interim/final text;
- final transcript is editable and is NEVER automatically submitted;
- user must press Send, using the existing chat capability and authority;
- spoken "approve" is not authenticated approval or an execution instruction;
- stop/clean up on minimize, close, modal opening, route-context change,
  page exit and errors; no background auto-restart;
- impose a reasonable short session limit such as 60 seconds.

Handle unavailable recognition, denied permission, no microphone, no speech,
network failure and service interruption with concise recovery and typed input.
Feature availability does not prove a working recognition service.

Explain before first use that browser speech recognition may send audio to
its provider. Do not claim offline/on-device/private processing unless verified.
Do not retain raw audio or add audio/transcript logging or provider fallbacks
without explicit disclosure. Keep draft storage consistent with existing policy.

Do not add a new transcription server/provider in this slice if browser support
is absent. Keep typing usable and report that limitation. Do not pretend voice
works by animating an unconnected microphone.

No real microphone capture, external speech calls or paid models in automated
tests. Test with controlled recognition mocks, and clearly distinguish mocked
verification from an optional user-run microphone check in the target browser.

10. PRESERVE THE PRODUCT'S TRUST BOUNDARIES

No changes to agent prompts, workflow authority, Phase 06 approval/execution,
MCP scopes, source APIs, business fixtures or Phase 07 graders.
No new autonomous jobs, manufacturing changes, customer commitments or writes.
No model calls merely to populate the screen.
Use actual source data, recorded results or explicitly labeled previews.
Do not turn a missing connection into a green "idle" or "all clear" state.
Do not expose secrets, arbitrary filesystem contents or hidden reasoning.
Scope CSS to the control plane; preserve the five existing source-app UIs.

11. VERIFY IN THE BROWSER BEFORE DECLARING COMPLETE

Use the existing build/component/Playwright setup and installed-browser override.
Run relevant tests, type checks and production build. Preserve existing tests;
update visual baselines only for deliberately changed control-plane views.

Test at least:
- status text has no colored badge background but retains readable meaning;
- computed title/body sizes satisfy the intended hierarchy at 100% zoom;
- portfolio navigation, filters, deep links and source facts still work;
- agent preview/recorded/current states are not confused;
- evidence and agent-detail dialogs show the correct scoped object;
- modal focus, close, Escape, background inertness and state restoration;
- concierge opens without page shift and uses the new name everywhere;
- drafts/context survive minimize safely;
- dictation permission, interim/final text, cancel, timeout and error states;
- unsupported speech recognition retains typed input;
- no recording on load and no auto-send/approval from voice;
- microphone cleanup on all closing/context-change paths;
- no unintended model calls or source writes;
- existing source apps remain intact.

Inspect screenshots at 1440x900 and 1280x800, plus a narrow mobile viewport.
Verify zoom/reflow, keyboard access, contrast and reduced-motion behavior.

Required screenshots:
1. Portfolio with colored masthead and compact Stratos Concierge.
2. Portfolio with expanded concierge.
3. CR-017 task panel and lifecycle.
4. Evidence preview modal with document/record and details.
5. Narrow-screen concierge/modal layout.
A mocked listening screenshot must be explicitly marked as mocked in the report.

Compare the images to the references. If it still looks like the previous
monochrome layout with recolored links, the visual task is NOT complete.
Fix layout, hierarchy and color coverage, not just tokens or test assertions.

12. DOCUMENT, REPORT AND STOP

Update the Phase 08 requirements and handoff with these superseding decisions:
colored masthead/surfaces; no status pills; larger typography; contextual
modals; Stratos Concierge; larger floating widget; explicit voice input.
Keep later chat/approval/backend integration scope honest.

Report:
- files changed and exact local preview URL/start commands;
- before/after screenshots and substantive design changes;
- actual sources for displayed program/agent/evidence information;
- connected versus recorded versus preview capabilities;
- voice provider/browser path, tested states and unverified live behavior;
- automated results, manual visual checks and limitations;
- confirmation that existing backend authority and source apps are unchanged.

Stop after this refinement. Do not run paid evals or proceed automatically
to Phase 08.2 or later slices.