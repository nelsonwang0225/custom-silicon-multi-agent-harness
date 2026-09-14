Continue in the existing Stratos Silicon repository AFTER the persona-aware
access update is complete. Implement Phase 10.2: VISUAL AGENT WORKSPACE.

Read the current Overview, role/capability model, Operations telemetry,
agent/run/activity records, screenshots and latest design requirements first.
Preserve the connected workflows, data, approvals, reset tools, Concierge and
existing light-blue Stratos shell. No new agents, workflow authority, paid model
calls, background workers or Git commit/push work.

1. CREATIVE BRIEF

THE AGENTS MUST BE THE PROTAGONISTS.
Keep the section named “Agent workspace.” Do not replace it with a generic
case queue, another Needs attention list, or five paragraphs about architecture.

The current grid says what agents exist. The new component must visually show:
- which agents are doing work;
- what each is doing, in a few words;
- which agent needs attention;
- where completed agent work is waiting for a human or external system.

Create a calm, modern, minimalist visual experience that is readable within
three seconds. Use spatial hierarchy, icons, categorical state rings and
selective motion instead of explanatory paragraphs.

2. USE VISUALIZE AND DESIGN JUDGMENT

Use @Visualize (visualize@openai-bundled) for concept exploration IF the actual
tool is available in your environment. Discover and invoke it; do not merely
claim to have used it. Do not guess nonexistent skill paths or tool APIs.

If unavailable, create small local prototypes with the existing frontend
stack and inspect them in the browser. This is a valid fallback; report it.
Do not add a new external provider, large graph library, or runtime dependency
solely to imitate Visualize. Do not send project secrets or real records to a
visual-design tool; use explicitly illustrative fixtures for exploration.

Explore TWO concise compositions before choosing:
A. Agent stage: a focal Coordinator with four compact specialist nodes around
   or below it, highlighting the agents actually involved in the selected work.
B. Agent ensemble/ribbon: a clean horizontal or shallow-grid arrangement with
   the active agent(s) emphasized and one short contextual work caption.

Use your imagination in composition and transitions. Improve on this brief
when a clearer visual solution exists. Do not just recolor the old cards.
Choose one, implement it, and save both concept previews with a short rationale.
Do not wait for a new prompt between exploration and implementation unless
there is a genuine blocker. Do not ship both competing layouts or a design lab.

3. COMPACT COMPONENT STRUCTURE

Prefer a wider Agent workspace on the left, Needs attention on the right.
Adjust the local Overview grid if necessary, not the entire application.

HEADER
Agent workspace | concise actual runtime/telemetry state or detail icon.
No explanatory subtitle paragraph.

SCOPE
A compact selector for All permitted activity / a specific active or recorded
run when necessary. Default to an actual active run when one exists; otherwise
last recorded work or a known idle state. Clearly label historical selection.
Never silently switch the selected run while the user is inspecting it.

MAIN VISUAL
The existing Program Coordinator and four existing specialist identities:
Change Impact, Validation & Evidence, Program & Commercial, Manufacturing.
Use real backend IDs; short display aliases are allowed with full names in
accessible labels/details. Do not create a new team or add Concierge as a sixth
workflow specialist merely because it can initiate work.

Each agent: meaningful icon + short name + categorical state. When working,
include one short task phrase and case reference, for example:
“Validation · Checking evidence · CR-017.”
This is example copy, NOT an instruction to invent an active task.

FOOTER
At most one useful handoff/outcome line, such as:
“CR-017 · Awaiting Engineering review.”
or “CR-019 · Handoff verified.”
Only from actual records. An authorized action may link to the decision/case.
Do not duplicate the full Needs attention queue.

Default copy target: roughly 50-70 words including names/status/context, excluding
expanded detail. Use this as a clarity budget, not a reason to hide critical
qualifiers or shrink typography. No static descriptions of agent responsibilities.

4. AGENT VISUAL STATES

Use shape/icon/text as well as color. No colored background status pills.
Categorical rings are NOT completion-percentage gauges.

Running: blue outlined/ring emphasis and restrained motion if enabled.
Completed task: small green check, labeled as the selected run's result.
Waiting for review/external work: pause/handoff symbol on the WORK state.
Failed invocation: red error marker tied to that task/run, not “agent offline.”
Not invoked: neutral outline for a selected run.
Idle: only when current telemetry establishes no active work in that scope.
Unavailable/stale: neutral uncertainty indicator; stop active animation.

When agents finish and the host waits for human review, do not show the model
as still computing or label every specialist as waiting. Keep completed agent
results visible and place the handoff outside the agent group.

A failure in one invocation does not establish that the whole agent service is
unavailable. An idle agent definition is not a continuously running daemon.

5. RELATIONSHIPS, PARALLEL WORK AND MOTION

Make collaboration visible without producing an engineering network diagram.
A few connectors may show actual coordinator-to-specialist participation for a
selected run. Active-transfer animations require corresponding observed events.
Static grouping must not imply every connection was used.

Respect real parallel work; do not impose a false serial execution order.
Do not blend agent outputs from different runs into one apparently coherent run.
For multiple concurrent runs, use a compact selector or “2 active tasks” on the
relevant agent with drill-down, not an unreadable tangle of edges.

Do not invent dotted progress, percentage complete, countdowns, throughput,
AI confidence, or claimed time saved. No spinning orbiting robots or moving
packets without event evidence. Respect reduced motion and provide static
states that communicate all the same meaning.

6. WHAT HEALTH REALLY MEANS

Use the existing Operations/read-health metadata. Keep these distinct:
- host/service availability;
- model configured or last observed successful model invocation;
- source-system health and freshness;
- active work and failures.

A configured API key or idle queue does not prove “all agents online.” No paid
health probe merely for rendering Overview. Show “Configured,” “Last checked,”
“Not checked” or “Unavailable” when that is what the records support.
Expose detail on click without filling the panel with infrastructure text.
If 5/5 sources are available, that must come from five actual sufficiently
recent checks. No data is unknown, not zero or healthy.

7. INTERACTION AND PROGRESSIVE DETAIL

Click/focus an agent to open an existing-style inspector/dialog containing:
- agent identity;
- selected task/case/run and whether current or recorded;
- one concise latest recorded finding;
- supporting evidence references;
- failure or next dependency;
- permitted Open case / View run / Explain in Concierge actions.

Overview stays visual. Raw tool payloads, trace IDs, token data and architecture
remain in Operations. No hidden chain-of-thought or fabricated “thinking” text.

A persona without Operations access can still get an allowed business-level
agent inspector; hide the Operations link and omit restricted technical data.
Selecting an agent does not call a model or start a workflow. Explain in
Concierge opens a contextual editable draft; sending remains explicit.
Do not invent a separate “start this agent” API.

8. IMPLEMENT WITH EXISTING TELEMETRY

Reuse persisted run, invocation, activity, source and verification records.
Add a minimal read-only view adapter if needed, not another monitoring store.
Return a role/scope-filtered snapshot containing what the view actually needs:
agent identity, task/run references, observed state, short task label, observation
and read timestamps, permitted detail links, and real dependencies.

Preserve exact version/provenance and run attribution. Prefer deterministic
mapping from known event types to short labels; no model summarization loop.

If current telemetry cannot show a fine-grained stage, show “Investigating”
rather than inventing one. Stop polling completed selections and pause heavy
polling for hidden pages. Guard against stale/out-of-order responses.

After persona change or demo reset, clear invalid selections and old agent
results. Do not keep old approved-action links alive in the inspector.

9. RBAC AND OVERVIEW INTEGRATION

Use the previously implemented capability contract, not new role conditionals.
Show only permitted cases/runs/findings, including counts and tooltip content.
The same actual work may be visible to several authorized personas; do not
change operational facts to personalize the display.

“Awaiting your review” only appears when the active actor can review that exact
proposal. Otherwise show the permitted informational state “Awaiting Engineering”
or equivalent with no unauthorized action.

Do not give agents approval authority in the visualization. Host execution and
human review are distinct from model participation. CR-019's pre-authorized
handoff remains different from CR-017's human-reviewed execution.

10. VISUAL STYLE

Keep the current light-blue masthead/Concierge gradient and Overview identity.
Use a white or very subtly tinted workspace surface with generous spacing,
outlined icons, native system type, dark readable text and restrained accents.
No new font assets, rainbow nodes, heavy card borders, status-pill fills or
competing gradients inside the workspace.

Avoid tiny labels: approximately 20-24px section heading, 15-16px agent names,
13-14px state/task text. Use a responsive layout and readable mobile fallback.
Preserve keyboard focus, semantic labels, accessible state announcements and
reduced-motion support. Pointer hover cannot be the only way to read details.
Use DOM/SVG within the existing stack, not a screenshot as the live component.

11. TEST AND VISUALLY INSPECT

Use deterministic isolated fixtures to render these states, without changing
the user's demo records or creating fake live telemetry:
- ready but no runs;
- two specialists actually working in parallel;
- selected run complete and waiting for Engineering review;
- a failed specialist with partial findings preserved;
- missing/stale telemetry;
- multiple concurrent runs without cross-run mixing;
- CR-019 verified handoff, lab authorization still pending;
- read-only persona with no operational/approval CTAs;
- persona switch/reset invalidating old detail/action state.

Test field/count provenance, freshness, sorting, polling lifecycle, access
filtering and zero model/write calls on render/selection. Preserve workflow,
Concierge, reset and current offline eval regressions. Run focused backend tests
for adapter changes, component/browser tests, typecheck and build.

Capture and actually inspect screenshots at 1440x900 and 1280x800, plus narrow
layout, enlarged text and reduced motion. Capture idle, running, human-handoff,
error and expanded inspector states. Mark fixture-driven captures as such;
these screenshots are not proof of a fresh paid agent run.

Acceptance test: without reading a paragraph, can someone identify the agents,
see who is working, identify a problem, and locate the human handoff? If the
result is still five static role-description tiles or a task table, revise it.

12. REPORT AND STOP

Deliver the implemented workspace, concept previews, final screenshots, short
choice rationale, exact telemetry mapping, tests/results/skips, changed files,
known limitations and actual local preview instructions.
State whether Visualize was really available and used, or a local prototype
was used instead. Update requirements/runbook so later edits retain the
agent-centered design and persona-aware behavior.

Stop after this improvement. No paid live matrix, Git packaging or unrelated
product changes. Later walkthrough feedback can still drive targeted revisions.