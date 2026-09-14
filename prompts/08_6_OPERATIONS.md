Continue working in the existing Stratos Silicon repository and current
Phase 08 thread.

Implement Phase 08.6:
OPERATIONS / OBSERVABILITY / INTEGRATED VERIFICATION.

This is the final Phase 08 implementation slice.

Reuse the existing:
- connected workflows:
  - CR-017 material change
  - CR-019 standard/touchless change
  - QE-004 yield/quality recovery
  - DR-009 delivery readiness
- Stratos Concierge
- workflow registry and invocation service
- case/run/activity persistence
- proposal/decision/action/verification models
- source adapters
- Phase 06 governance/execution
- Phase 07 eval framework
- Phase 08 Workflows & Automations
- current search, alerts, dialogs, and UI shell

Do not redesign the application.
Do not create new agents or a new trace system.
Do not activate background schedulers/event listeners.
Do not change workflow authority.
Do not expand source write permissions.
Do not begin Phase 09 polish.

Git remains relaxed:
- no branch/commit/push work
- preserve unrelated local work
- avoid destructive operations

==================================================
1. OBJECTIVE
==================================================

Build a useful Operations experience that answers:

1. What workflows have run?
2. Which cases/programs did they affect?
3. Which agents/specialists participated?
4. Which tools/services were called?
5. What evidence was used?
6. What proposals/decisions/actions followed?
7. Did execution succeed?
8. Did independent verification succeed?
9. What failed, escalated, or remained pending?
10. How reliable was the agent behavior?
11. What latency/token usage was observed where available?
12. How does this technical activity connect back to the business case?

The Operations page is secondary to the business workbench.

It should NOT become the default homepage.

==================================================
2. SOURCE OF TRUTH
==================================================

Reuse existing persisted records.

Preferred sources:

APPLICATION / BUSINESS
- case
- run
- activity
- proposal
- decision
- action attempt
- verification
- automation configuration

AGENT / RUNTIME
- existing Agents SDK traces
- specialist invocation records
- tool/service call records
- model metadata
- latency/token usage if already captured

EVAL / RELIABILITY
- Phase 07 offline eval results
- live eval artifacts when available
- grader outcomes
- hard-gate status

Do not duplicate raw trace data into a second store unless a lightweight index is
required for presentation.

Do not fabricate technical telemetry.

==================================================
3. OPERATIONS LANDING PAGE
==================================================

Build a modern Operations landing page.

Suggested sections:

A. CURRENT / RECENT RUNS
- connected workflow runs
- program/case
- workflow
- started
- current/final state
- business outcome
- run ID

B. NEEDS ATTENTION
- failed runs
- escalations
- verification mismatches
- partial execution
- stale proposals
- source unavailable

C. RELIABILITY
- latest offline eval hard-gate state
- case count
- critical failures
- latest live eval result if available
- clearly distinguish offline from live

D. SYSTEM HEALTH
- source-app connectivity/read status if actually available
- model/runtime configuration availability
- no invented uptime percentages

Avoid excessive metric cards.

Do not show:
"99.9% reliable"
unless the system actually computes that from meaningful data.

==================================================
4. RUN HISTORY TABLE
==================================================

Provide a useful run table.

Fields:

- workflow
- program
- case
- invocation source
- actor
- started
- duration if available
- runtime state
- business outcome
- decision state
- verification state
- model/config if available
- run ID

Support filtering by:
- workflow
- program
- case
- state
- date range where practical

Do not reuse Overview filters unnecessarily.

Clicking a row opens run detail.

==================================================
5. RUNTIME STATE VS BUSINESS OUTCOME
==================================================

Keep these separate everywhere.

Examples:

Runtime:
Completed

Business outcome:
Escalation required

Runtime:
Completed

Business outcome:
Waiting for human review

Runtime:
Completed

Business outcome:
Handoff verified

Runtime:
Completed

Business outcome:
Partial execution

Runtime:
Failed

Business outcome:
Investigation incomplete

Never display:
Completed = success

without examining the actual business outcome.

==================================================
6. RUN DETAIL
==================================================

Build a comprehensive run detail page.

Recommended sections:

SUMMARY
- workflow
- program/case
- user/business question
- invocation source
- trusted actor
- started/completed
- runtime state
- business outcome

AGENT TOPOLOGY / PARTICIPATION
- Program Coordinator
- specialists actually invoked
- start/end/status
- concise result
- retry/failure state

TIMELINE
- intake
- evidence retrieval
- specialist findings
- reconciliation
- proposal
- decision
- execution
- verification
- downstream event

EVIDENCE
- source records used
- versions
- applicability
- links to evidence modal/source apps

TOOLS / SERVICES
- tool/service name
- specialist/caller
- target system
- success/failure
- duration if available

DECISION
- proposal
- approval/rejection
- version/digest
- approver/demo identity

EXECUTION
- authorized action manifest
- attempts
- idempotency/retries
- partial failure

VERIFICATION
- expected source state
- actual readback
- verified/inconclusive/failed

TECHNICAL DETAILS
Expandable:
- trace IDs
- model name
- token usage
- latency
- raw structured outputs where safe

Do not expose hidden chain-of-thought.

==================================================
7. AGENT VISUALIZATION
==================================================

Create a compact visual representation of agent participation.

Use actual run data.

Examples:
Coordinator
├── Change Impact
├── Validation & Evidence
└── Program & Commercial

or parallel rows.

Do not imply all agents always run.

Do not animate completed agents as currently working.

Use status:
Completed
Failed
Skipped
Not invoked
Waiting

Keep this functional, not decorative.

==================================================
8. TOOL / SERVICE CALLS
==================================================

Expose meaningful tool/service activity.

Examples:
Engineering Hub read
Validation Lab evidence read
Manufacturing lot read
ERP order read
Planner milestone read
Validation intake create
ERP commitment update
Planner update
Readback verification

Do not expose credentials, authorization headers, secrets, filesystem paths,
or unrestricted request payloads.

Display sanitized arguments/identifiers when useful.

Tool calls should link to related evidence/source record where possible.

==================================================
9. TRACE LINKAGE
==================================================

Use existing Agents SDK trace identifiers.

Operations should make it possible to correlate:

business run ID
↔ trace ID
↔ case
↔ workflow
↔ proposal/decision
↔ execution
↔ verification

Do not make trace ID the main user-facing identifier.

Business case/run should remain primary.

==================================================
10. TOKEN USAGE
==================================================

If token usage is already captured by the runtime:

show:
- input tokens
- output tokens
- total tokens
- per-run totals
- optional per-agent detail

If cost can be derived from an explicit configured pricing table:
label it as an estimate with model/pricing version.

Do not hard-code current OpenAI pricing unless the repository already has a
versioned pricing source.

If token usage is unavailable:
show unavailable.

Do not invent values.

==================================================
11. LATENCY
==================================================

Where timestamps are available, show:

- total run duration
- specialist duration
- tool/service latency
- waiting-for-human time separately from model/tool execution time

Do not include multi-hour human wait in:
"AI runtime latency"

without distinguishing it.

Use:
Agent execution
Human wait
External wait

where possible.

==================================================
12. EVAL / RELIABILITY VIEW
==================================================

Add an Operations subview or section for Evals & Reliability.

Show:

OFFLINE EVALS
- total cases
- passed/failed
- hard-gate result
- critical failures
- latest run timestamp

LIVE EVALS
- latest available live smoke
- cases run
- pass/fail
- critical failures
- model
- timestamp

Important:
Preserve historical truth.

Do not overwrite the earlier six-case 4/6 failed smoke with the later targeted
passes and claim a fresh 6/6 smoke occurred.

Show history or labels such as:

Historical full smoke:
4/6 — failed

Later targeted validations:
cr017_covered — pass
cr017_scheduled — pass

Current offline:
112/... according to actual current records

Use actual stored artifacts/results.

==================================================
13. CRITICAL FAILURE SEMANTICS
==================================================

Highlight critical failures separately.

Examples:
- unauthorized execution
- approval bypass
- fabricated evidence
- false validation pass
- false customer acceptance
- false root cause
- incorrect eligible supply
- stale proposal execution

Zero critical failures should be shown only when the actual eval record says zero.

Do not turn "no critical failures" into "all reasoning perfect."

==================================================
14. BUSINESS LINKBACK
==================================================

Every run should link back to:
- program
- case
- decision
- source evidence

Operations should never strand the user in technical telemetry.

Examples:
Open CR-017
Open QE-004
Open DR-009
View proposal
View verification

==================================================
15. OPERATIONS FROM CASE PAGES
==================================================

Add subtle links such as:

View run details
View agent activity
View trace

Do not clutter the primary business case page.

Operations is secondary detail.

==================================================
16. CONCIERGE OPERATIONS LINKAGE
==================================================

Concierge connected interactions should create/link:

- conversation/session ID
- model invocation metadata
- workflow runs triggered
- proposal/decision surfaced
- structured action confirmations
- automation config saved

Operations may show Concierge sessions as a separate source:

Invocation source:
Concierge

Do not treat every chat message as a workflow run.

==================================================
17. CONCIERGE SESSION DETAIL
==================================================

Where useful, allow Operations to inspect a Concierge session.

Show:
- user-visible messages
- structured cards
- workflow invocations
- navigation/actions
- model metadata
- latency/tokens

Do not show hidden reasoning.

Do not expose raw voice audio.

==================================================
18. AUTOMATION CONFIGURATION VISIBILITY
==================================================

Operations may show configured automations.

Clearly distinguish:

Configured
Paused
Preview trigger
No scheduler active

Do not show "last run" for a saved automation that has never executed.

Do not invent next execution timestamps.

==================================================
19. SOURCE SYSTEM HEALTH
==================================================

If actual source-read health data exists, show it.

Examples:
Engineering Hub — available
Validation Lab — available
Manufacturing Portal — available
Commercial ERP — available
Program Planner — available

Use actual health/read checks.

Do not build constant fake green indicators.

If health is unknown:
Unknown / not checked

If stale:
show stale timestamp.

==================================================
20. ERROR / FAILURE DETAIL
==================================================

For failed runs show:

- failure stage
- failure category
- last successful activity
- source/tool affected
- retry/reconciliation state
- whether business mutation occurred

Avoid dumping stack traces as the primary UI.

Provide expandable technical error detail where safe.

Do not expose secrets.

==================================================
21. PARTIAL EXECUTION
==================================================

Operations should be especially clear for partial failure.

Example:
ERP commitment — Verified
Planner update — Failed

Overall:
Partial execution

Next:
Retry Planner update / reconcile

Do not collapse to:
Failed

if meaningful successful business mutation already occurred.

==================================================
22. VERIFICATION MISMATCH
==================================================

Show:

Action:
Succeeded

Readback:
Mismatch

Business state:
Not verified

This distinction should be obvious.

Do not show green overall success.

==================================================
23. SEARCH
==================================================

Global search should include:
- runs
- trace IDs where appropriate
- Concierge sessions
- eval results

Prefer business identifiers in display.

Searching:
QE-004

should still prioritize the case before technical runs.

==================================================
24. ALERTS
==================================================

Alerts may use Operations records for real failures:

- workflow failed
- verification mismatch
- execution partial failure
- hard eval gate failure

Do not alert merely because:
token usage high

unless we actually define a threshold/policy.

==================================================
25. OVERVIEW
==================================================

Keep Operations detail out of Overview.

At most expose:
- recent workflow run
- actual decision pending
- actual failure needing attention

Do not add:
token count
trace count
tool calls
to the landing page.

==================================================
26. API / HOST SURFACE
==================================================

Add thin typed read endpoints/services only as necessary for:

- list runs
- read run details
- agent activity
- tool/service activity
- trace metadata
- token/latency
- eval summaries/history
- Concierge session metadata
- source-health metadata

Prefer existing records and artifacts.

Do not expose:
- arbitrary file reads
- raw trace file paths
- credentials
- hidden reasoning
- generic tool execution

==================================================
27. ARTIFACT / FILE SAFETY
==================================================

Some eval/trace artifacts currently live as local files.

Do not create an endpoint that accepts arbitrary paths.

If presentation requires them:
- index known artifact directories server-side
- validate allowed roots
- use stable IDs
- expose sanitized structured data

Never return arbitrary filesystem content based on a browser path parameter.

==================================================
28. REAL-TIME / POLLING
==================================================

Use lightweight polling for currently running workflows if needed.

Do not build WebSockets/event streaming unless already present and justified.

Polling must:
- read existing run state
- not trigger model calls
- not mutate workflow state

Stop polling completed runs.

==================================================
29. OPERATIONS VISUALS
==================================================

Use purposeful visuals:

- workflow timeline
- agent participation
- action/verification sequence
- eval pass/fail matrix
- latency breakdown

Avoid decorative charts.

No giant donut charts for token usage.

Keep data tables readable.

==================================================
30. RESPONSIVE / ACCESSIBILITY
==================================================

Operations contains dense data.

At desktop:
use wide content intelligently.

At smaller widths:
- stack panels
- allow horizontal scrolling only for tables where necessary
- keep primary status visible

Keyboard navigation/focus must work.
Do not rely on color alone.

==================================================
31. EVAL INTEGRITY TESTS
==================================================

Add tests proving:

A. Historical 4/6 live smoke remains historically represented.

B. Targeted later passes are separate records, not rewritten history.

C. Offline eval counts come from actual result files/records.

D. Critical failures display accurately.

E. Missing semantic grader remains skipped/unavailable, not pass.

F. No fake live eval when only offline exists.

G. Eval artifacts cannot be accessed via arbitrary filesystem path.

==================================================
32. RUN / TRACE TESTS
==================================================

Add tests covering:

A. Runtime completed + escalation stays escalation.

B. Runtime completed + waiting review stays waiting review.

C. Partial execution displayed correctly.

D. Verification mismatch displayed correctly.

E. Tool failures visible.

F. Actual agents invoked only.

G. Uninvoked specialist not shown as completed.

H. Tokens/latency unavailable handled explicitly.

I. Human wait separated where data allows.

J. Source health unknown does not become green.

==================================================
33. CONCIERGE TESTS
==================================================

Verify Operations correctly links:
- chat session
- workflow invoked through chat
- decision surfaced
- action confirmed
- automation config saved

Do not expose hidden reasoning/audio.

==================================================
34. BROWSER E2E
==================================================

Test at least:

1. Open Operations.
2. View CR-017 run.
3. Inspect specialists/evidence/tools.
4. Follow link back to CR-017.
5. View CR-019 run and verified handoff.
6. View QE-004 run and supply impact.
7. View DR-009 run and decision/execution.
8. View a partial-failure deterministic fixture.
9. View a verification-mismatch fixture.
10. View Evals & Reliability.
11. Historical full live smoke remains 4/6.
12. Targeted later passes shown separately.
13. Search for run.
14. Open Concierge-originated run.
15. Inspect automation config state.
16. Source health unknown/available behaves correctly.

==================================================
35. AUTOMATED VERIFICATION
==================================================

Run:
- source/backend tests
- coordinator tests
- MCP tests
- all Phase 07 evals
- all 08.4 workflow regressions
- 08.5 Concierge tests
- new Operations tests
- frontend/component
- Playwright
- typecheck/build

No paid models.

Do not rerun full live smoke automatically.

Preserve working demo state.

==================================================
36. OPTIONAL LIVE CHECK
==================================================

Provide instructions for one manual connected Operations check after a live
Concierge/workflow run.

Do not automatically run paid models.

The user should be able to:
- trigger a real workflow
- open Operations
- see the new run
- inspect actual trace/tool/model metadata

==================================================
37. DOCUMENTATION
==================================================

Update Phase 08 docs with:

- Operations architecture
- data sources
- run/business-state semantics
- agent/tool display rules
- trace linkage
- token/latency semantics
- eval-history integrity
- artifact security
- Concierge linkage
- source health
- known limitations

==================================================
38. PHASE 08 INTEGRATED VERIFICATION
==================================================

Perform an integrated offline/browser verification across:

- Overview
- Programs/cases
- CR-017
- CR-019
- QE-004
- DR-009
- Workflows & Automations
- Decisions
- Search
- Alerts
- Concierge
- Operations

Verify cross-page state consistency.

Examples:
- DR-009 shows 600/800 in case, Concierge and Operations.
- QE-004 hold state is consistent everywhere.
- CR-017 customer acceptance remains pending everywhere.
- CR-019 verified handoff remains separate from lab authorization.
- Decisions page and case page use same proposal state.

Do not fix inconsistencies by hard-coding duplicate UI values.

Fix underlying view-model/source mapping.

==================================================
39. FINAL REPORT
==================================================

Report:

1. Operations architecture
2. Existing records reused
3. New read/index adapters
4. Run detail functionality
5. Agent/tool observability
6. Trace linkage
7. Token/latency behavior
8. Eval/reliability view
9. Concierge linkage
10. Artifact safety
11. Cross-page consistency checks
12. Files changed
13. Tests/results
14. Screenshots/local URL
15. Live checks not automatically run
16. Known limitations
17. Phase 08 completion status
18. Exact Phase 09 starting point

==================================================
40. STOPPING POINT
==================================================

Stop after Phase 08.6 and integrated verification.

Do NOT continue into:
- Phase 09 visual/demo polish
- new workflows
- active background scheduler/event listener
- Git cleanup/push
- slide creation

Phase 08 is complete when the application supports:

business control-plane operation
+ all connected demo workflows
+ connected Stratos Concierge
+ workflow/automation configuration
+ decisions/governed execution
+ operations/observability
+ eval/reliability visibility

with cross-page state consistency and existing governance preserved.