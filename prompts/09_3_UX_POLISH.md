Continue working in the existing Stratos Silicon repository and current project thread.

Implement Phase 09.3:
PRIMARY UX, PERSONA, VISUALIZATION, AND DEMO-EXPERIENCE POLISH.

Phase 09 is the final product-development phase.

This is NOT merely a cosmetic pass.

You may make meaningful UI/UX changes to existing product capabilities when
they make the demo easier to understand, operate, or explain.

Examples that are explicitly in scope:
- simplifying page layouts;
- reorganizing information hierarchy;
- reducing text;
- improving navigation;
- changing component layouts;
- improving persona/demo-identity UX;
- making approval ownership clearer;
- adding meaningful visualizations using existing source-backed data;
- improving case lifecycle visualization;
- improving agent-work visualization;
- improving evidence/options/decision presentation;
- improving Stratos Concierge interaction;
- reducing unnecessary clicks;
- improving source-system drill-down;
- improving loading, waiting, failure and stale states.

Do NOT add an unrelated new workflow, new source system, new agent framework,
new approval architecture, or other major product capability that is not needed
to make the existing demo product work well.

This is the primary polish pass, NOT a permanent UI freeze.

Phase 09.5 manual/live testing may identify additional UX, copy, visual,
persona, workflow or interaction fixes. Those later targeted corrections are
expected and allowed.

Git remains relaxed:
- no commit/push work yet;
- preserve unrelated local work;
- avoid destructive operations.

==================================================
1. OBJECTIVE
==================================================

Make the existing Stratos control plane feel like a coherent, professional,
easy-to-understand enterprise product suitable for a five-minute executive /
technical interview demo.

The user should understand within seconds:

- what is happening;
- what needs attention;
- what the agents are doing;
- which source facts matter;
- what decision is required;
- who is authorized to make that decision;
- what has actually executed;
- what remains downstream.

Prioritize clarity over information density.

Use progressive disclosure:
important business state first;
technical detail on demand.

==================================================
2. REVIEW THE ACTUAL PRODUCT BEFORE EDITING
==================================================

Inspect the current application in the browser at 1440x900.

Review at minimum:

- Overview
- Helios Program
- CR-017
- CR-019
- QE-004
- DR-009
- Workflows & Automations
- Decisions
- Operations
- Search
- Alerts
- Demo identity / persona experience
- Stratos Concierge
- evidence/source dialogs
- source-app deep links

Identify real UX problems before changing components.

Do not blindly rewrite working layouts simply because this prompt says "polish."

Document major issues found and address the ones that materially affect the
demo experience.

==================================================
3. INFORMATION HIERARCHY
==================================================

Use a consistent hierarchy throughout the product.

Priority order:

1. Business question / current outcome
2. Blocker / decision / next step
3. Important numbers or evidence
4. Agent/workflow activity
5. Source provenance
6. Technical implementation detail

Do not place trace IDs, configuration IDs, internal versions or verbose
explanations ahead of the business story.

Keep technical detail available through drill-downs.

==================================================
4. OVERVIEW
==================================================

Make Overview answer immediately:

"What is happening across Helios?"
"What needs my attention?"
"What are agents working on?"
"What decision is waiting?"

Keep the current Stratos visual direction, but improve layout if necessary.

Review whether the current hero, program cards, agent workspace and attention
area are the best composition.

You may substantially reorganize Overview if a clearer structure exists.

Suggested hierarchy:

- strong Overview heading/context;
- visual program-health summary;
- program/case status;
- prominent agent/workflow activity;
- needs-attention queue;
- concise secondary information.

Avoid walls of text.

Do not expose technical observability here.

==================================================
5. HELIOS PROGRAM PAGE
==================================================

Make the Helios program page the clearest demonstration that the control plane
coordinates multiple classes of program work.

Show the four canonical connected cases clearly:

CR-017
Material workload change

CR-019
Standard touchless change

QE-004
Yield / quality exception

DR-009
Delivery readiness

For each case show only the information useful at program level:

- short title
- workflow type
- current state
- one important fact / number when meaningful
- next decision or dependency
- clear drill-down

Examples:

CR-017
Validation evidence complete
Customer acceptance pending

CR-019
Standard handoff verified
Lab authorization downstream

QE-004
Lot held
200-unit supply exposure

DR-009
600 / 800 supportable
Commitment decision required

Use actual source-backed current state.

Remove long descriptive paragraphs from program cards.

==================================================
6. CASE-PAGE CONSISTENCY
==================================================

Create a consistent case-page grammar while preserving workflow-specific content.

Every case page should quickly communicate:

WHAT HAPPENED?
WHAT DID THE AGENTS FIND?
WHAT EVIDENCE SUPPORTS IT?
WHAT DECISION/ACTION IS NEXT?
WHAT HAS ACTUALLY EXECUTED?
WHAT REMAINS?

Use a consistent upper-page structure:

- case identifier / workflow
- large business title
- concise business question
- current-state panel
- lifecycle / progress
- primary visualization
- key action / decision

Then deeper tabs/sections below.

==================================================
7. WORKFLOW-SPECIFIC VISUALIZATIONS
==================================================

Increase meaningful visualization where it helps comprehension.

Do NOT create generic charts merely for decoration.

CR-017
Prefer:
- before/after requirement comparison;
- evidence applicability / coverage visualization;
- validation lifecycle;
- decision → execution → physical result relationship.

CR-019
Prefer:
- applicability / touchless-policy checklist;
- evidence reuse;
- package → Validation Operations handoff;
- clear boundary showing where automation stops.

QE-004
Prefer:
- test result vs comparable baseline;
- physical lot vs eligible quantity;
- held-material visualization;
- supply impact;
- facts vs hypotheses vs unresolved root cause.

DR-009
Prefer:
- 1,000 physical
  - 250 held
  - 150 allocated
  = 600 eligible
- requested 800
- gap 200;
- separate technical-readiness gates;
- structured delivery-option comparison.

Use actual calculated/source-backed data.

No invented AI readiness score.

==================================================
8. AGENT WORK VISUALIZATION
==================================================

Make agent orchestration visually understandable.

Users should be able to see:

Program Coordinator

and only the specialists actually involved in the current workflow.

Represent:
- running;
- completed;
- failed;
- waiting;
- not invoked

truthfully.

Where actual parallel specialist execution exists, visualize that sensibly.

Do not animate old runs as though agents are currently working.

Keep raw tool calls in Operations.

On business pages show:
- agent role;
- task;
- concise finding;
- evidence link;
- state.

==================================================
9. PERSONA / DEMO IDENTITY EXPERIENCE
==================================================

Review and improve the current demo-identity UX substantially if necessary.

The personas matter to the demo story and must be easy to understand.

At minimum make these roles clearly differentiated where they exist:

PROGRAM OPERATOR / PROGRAM LEAD
Can:
- initiate investigations;
- coordinate cases;
- inspect evidence;
- prepare work.

Cannot automatically:
- approve engineering adequacy;
- release held material;
- change customer commitments unless specifically authorized.

ENGINEERING APPROVER
Owns consequential engineering decisions such as:
- CR-017 validation authorization where policy requires;
- completed validation evidence review.

PROGRAM / COMMERCIAL OWNER
Owns:
- customer-facing delivery commitment decisions;
- relevant commercial/program approvals.

QUALITY / APPROPRIATE RECOVERY OWNER
Owns:
- consequential quality disposition where implemented.

Reuse actual trusted identities and role policies in the repository.
Do not invent client-only role authority.

==================================================
10. PERSONA SELECTOR / LOGIN EXPERIENCE
==================================================

The current top-right demo-access experience should make the active persona
obvious.

Improve it if needed.

The user should immediately know:

Signed in as / Demo identity:
Name
Role

and understand what that role can do.

Provide a concise role-description view.

When an action is disabled because of authority, do not merely gray it out.

Show an actionable explanation such as:

Engineering Approver required
Switch demo identity

where appropriate.

Allow switching personas with minimal friction.

Do not implement fake passwords or claim production authentication.

Keep visible:
Demo identity / synthetic environment

without making it visually dominant.

==================================================
11. DISABLED ACTIONS
==================================================

Audit all disabled buttons.

A disabled control must communicate WHY it is disabled.

Examples:

Run investigation
Requires Program Operator or Engineering Approver

Approve evidence
Requires Engineering Approver

Commit option
Requires Program / Commercial Owner

Physical validation
Waiting for Validation Lab result

Where useful provide:
Switch identity
Open dependency
View decision

Do not create dead gray buttons with hidden requirements.

==================================================
12. DECISIONS UX
==================================================

The Decisions experience should communicate in seconds:

- what the decision is;
- why it matters;
- what the agent recommends;
- what evidence supports it;
- exact business consequences;
- what will happen if approved;
- who can approve.

Use business terminology.

Never:
Approve AI

Prefer:
Approve validation plan
Approve engineering evidence
Approve recovery plan
Approve 600-unit commitment

Show exact role requirement clearly.

==================================================
13. COPY SIMPLIFICATION
==================================================

Audit all UI copy.

Reduce repetitive explanatory text substantially.

Prefer:
- short title;
- one-line finding;
- status;
- number/date;
- action.

Move detailed explanations into:
- evidence modal;
- details panel;
- agent details;
- Operations.

Remove developer-oriented copy from default business views.

Avoid phrases that sound like system documentation.

==================================================
14. TERMINOLOGY GUIDE
==================================================

Standardize terminology globally.

Examples:

Needs review
Awaiting external result
Awaiting engineering review
Executing
Verified
Partial execution
Escalated
Validation complete
Customer acceptance pending
Handoff verified
Lot held
Commitment decision required

Do not alternate between several words for the same state.

Do not use:
Done
Success
Complete

without the correct scope.

==================================================
15. STRATOS CONCIERGE
==================================================

Review the connected Concierge experience end-to-end.

Make it feel like a useful operating assistant rather than a developer demo.

Improve where necessary:

- window size;
- spacing;
- typography;
- structured cards;
- citation/source links;
- suggested prompts;
- action confirmations;
- workflow-run cards;
- loading indicators;
- errors;
- persona/authority messaging.

Keep it floating.

Do not bypass underlying governance.

Replies should be concise by default.

Do not flood the conversation with implementation details.

==================================================
16. GLOBAL SEARCH
==================================================

Review search interaction.

Make results easy to scan.

Prioritize:
Cases
Programs
Decisions
Evidence
Workflows

over technical run artifacts.

Keep Ask Stratos Concierge available.

Technical objects may appear in secondary groups.

==================================================
17. ALERTS
==================================================

Make alerts concise and actionable.

Avoid repeated or low-value notifications.

Each meaningful alert should answer:
what changed?
what needs attention?

Example:
CR-017 · Engineering review ready

not:
Validation result event received from API

==================================================
18. WORKFLOWS & AUTOMATIONS
==================================================

Now that all canonical workflows are connected, audit execution-mode labels.

Connected:
- Requirement Change Analysis
  - standard route
  - material route
- Yield / Quality Recovery
- Delivery Readiness

Background schedule/event/condition configurations remain NOT active.

Present this globally rather than repeating long limitation text on every item.

Use concise labels such as:

Connected workflow
Schedule configured · runner inactive

==================================================
19. OPERATIONS
==================================================

Keep Operations technically useful, but organize business state first.

Default run view:
- business outcome;
- workflow/case;
- agents;
- decision/execution/verification.

Technical trace, tokens, latency and tool calls:
expandable.

Do not redesign Operations into another business homepage.

==================================================
20. MODALS / EMBEDDED WINDOWS
==================================================

Standardize:
- evidence;
- source record;
- agent detail;
- decision review;
- demo controls.

Use consistent:
- width;
- heading scale;
- close control;
- body spacing;
- footer;
- focus behavior.

Use large two-column dialogs where they help focused comparison/review.

Do not use modals for ordinary navigation.

==================================================
21. LOADING / RUNNING STATES
==================================================

Make live workflow execution understandable.

When a real agent run begins:
show:
- workflow started;
- current stage;
- actual agents as their activity is recorded;
- elapsed time if meaningful;
- cancel only if genuinely supported.

Do not show an indefinite generic spinner.

Do not fabricate per-token agent progress.

==================================================
22. EMPTY / STALE / ERROR STATES
==================================================

Review all important states.

Examples:
- no investigation yet;
- no decision;
- source unavailable;
- stale proposal;
- partial execution;
- verification mismatch;
- Concierge backend unavailable;
- no current agent activity.

Make next action obvious.

==================================================
23. NAVIGATION / CLICK REDUCTION
==================================================

Audit the canonical workflows.

Reduce unnecessary clicks where safely possible.

Examples:
- case → decision should be direct;
- decision → evidence should be direct;
- run → case should be direct;
- evidence → source system should be direct.

Do not merge consequential confirmation steps merely to reduce clicks.

Governance confirmation remains explicit.

==================================================
24. ACCESSIBILITY
==================================================

Preserve:
- keyboard operation;
- visible focus;
- dialog focus management;
- meaningful labels;
- sufficient contrast;
- reduced motion;
- readable text at zoom.

Color is not the only status indicator.

==================================================
25. DESKTOP DEMO OPTIMIZATION
==================================================

Primary visual review:

1440x900
1920x1080

Also maintain usable:
1280x800

Do not optimize by shrinking typography.

Use available screen width more effectively if pages feel cramped or too empty.

==================================================
26. VISUAL REVIEW
==================================================

Capture and inspect screenshots for:

- Overview
- Helios Program
- CR-017
- CR-019
- QE-004
- DR-009
- Decisions
- Workflows
- Concierge
- Operations
- persona selector
- major evidence modal

At 1440x900.

Do not declare completion from TypeScript/build alone.

Fix visible:
- clipping;
- awkward whitespace;
- tiny labels;
- inconsistent spacing;
- poor hierarchy;
- confusing states.

==================================================
27. AUTOMATED TESTING
==================================================

Run relevant:
- frontend/component tests;
- browser E2E;
- typecheck;
- production build.

If view-model/source mappings change:
run relevant backend tests.

Preserve all existing workflow/governance tests.

No paid model calls.

==================================================
28. DOCUMENTATION
==================================================

Update Phase 09 handoff with:
- terminology guide;
- persona model;
- major UX/layout decisions;
- visualization rules;
- canonical demo screenshots;
- remaining UX limitations.

==================================================
29. FINAL REPORT
==================================================

Report:

1. UX issues found
2. Layout changes
3. Copy reductions
4. Visualization improvements
5. Persona/authentication UX improvements
6. Disabled-action improvements
7. Concierge improvements
8. Decision improvements
9. Navigation/click reductions
10. Files changed
11. Screenshots
12. Tests/results
13. Remaining issues for final manual validation

Stop after 09.3.

This is the primary polish pass, not a permanent UI/code freeze.
Later Phase 09 manual/live testing may identify further targeted changes.