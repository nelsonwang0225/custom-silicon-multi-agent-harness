Continue working in the existing Stratos Silicon repository and current project
thread.

Implement Phase 09.4:
DEMO HARNESS, STARTUP, REPRODUCIBILITY, AND FINAL-VALIDATION READINESS.

Phase 09.4 is NOT a code freeze.

Its purpose is to make the current application reliably launchable, resettable,
observable, and ready for the final manual/live validation cycle.

After 09.4, targeted functional, persona, layout, visualization, prompt,
interaction, and visual fixes discovered during Phase 09.5 are expected and
allowed.

Do not add unrelated new major product capabilities unless a demonstrated
blocking issue requires a narrowly scoped correction.

Do not run paid models automatically.
Do not perform final Git cleanup/push yet.

==================================================
1. OBJECTIVE
==================================================

Make it easy to prepare and operate the complete Stratos demo reliably.

The operator should be able to:

1. Start all required services.
2. Verify service health.
3. Reset to the canonical demo baseline.
4. Verify baseline consistency.
5. Open the application.
6. Run any canonical demo scenario.
7. Reset/replay.
8. Diagnose common failures.
9. Shut down cleanly.

Reduce setup mistakes before the final manual/live test phase.

==================================================
2. AUTHORITATIVE DEMO STARTUP
==================================================

Inspect the actual current startup architecture.

Create/refine one supported demo-start mechanism using repository conventions.

It should start only the services actually required, such as:

- mock enterprise/source services;
- MCP server if required;
- coordinator/control host;
- frontend;
- other existing runtime dependencies.

Do not launch duplicate existing processes blindly.

Detect occupied ports where practical.

Print actual local URLs.

Fail clearly when a required service cannot start.

Do not print secrets.

==================================================
3. DEMO START COMMAND
==================================================

Provide a simple documented operator command or helper.

Conceptually:

demo start

Use existing CLI/script naming conventions rather than this exact name if better.

The command should:

- check prerequisites;
- start services;
- wait for readiness;
- print URLs;
- leave current business state unchanged.

Do not automatically reset on every start.

Restarting services must preserve current demo mutations until explicit reset.

==================================================
4. DEMO PREPARE
==================================================

Provide a supported sequence equivalent to:

demo prepare

It should:

- confirm services available;
- execute the existing Phase 09.1 Full Demo Reset;
- run baseline validation;
- verify canonical cases exist;
- verify important source systems are reachable;
- verify frontend/control host availability;
- verify model configuration/credential presence without making a paid call;
- confirm background schedulers/event listeners remain inactive;
- report Demo ready only when baseline validation succeeds.

Do not duplicate reset logic.

Reuse Phase 09.1.

==================================================
5. DEMO STATUS
==================================================

Provide a lightweight operator status command / screen.

Show:

Services
- Engineering Hub
- Validation Lab
- Manufacturing Portal
- Commercial ERP
- Program Planner
- MCP/runtime
- control host
- frontend

Demo state
- baseline valid / mutated
- baseline version

Canonical cases
- CR-017
- CR-019
- QE-004
- DR-009

Model configuration
- configured / unavailable

Do not display API keys.

Background execution
- schedulers inactive
- event listeners inactive

Current running workflows if any.

==================================================
6. DEMO RESET
==================================================

Reuse existing Phase 09.1 reset implementation.

Do NOT create another reset architecture.

Expose convenient operator access to:

Full Demo Reset

and scenario resets where safe.

==================================================
7. DEMO SHUTDOWN
==================================================

Provide a clean documented stop process.

Conceptually:

demo stop

Stop only processes started by the demo harness where feasible.

Do not kill arbitrary processes on matching port without ownership checks.

==================================================
8. DEMO RUNBOOK
==================================================

Create one authoritative:

DEMO_RUNBOOK.md

or equivalent.

It should be concise enough to use during interview preparation.

Include:

Prerequisites

Startup

Prepare/reset

Login/demo personas

Canonical workflows

Source applications

Concierge

Operations

Reset between runs

Troubleshooting

Shutdown

==================================================
9. CANONICAL SCENARIO INDEX
==================================================

Document the four connected demo paths.

CR-019 — Standard Change / Touchless
Starting persona:
Program Operator

Core story:
approved procedure
→ agent investigation
→ autonomous handoff
→ verification

Ending:
Validation Operations received package
lab authority still downstream

CR-017 — Material Change
Starting persona:
Program Operator

Decision persona:
Engineering Approver

Core story:
evidence gap
→ proposal
→ approval
→ execution
→ physical result
→ evidence review

Ending:
technical validation complete
customer acceptance separate

QE-004 — Yield / Quality Recovery
Starting persona:
Program Operator

Decision persona:
actual implemented Program/Quality role

Core story:
quality exception
→ evidence
→ supply impact
→ recovery
→ human consequential decision

Ending:
governed recovery state
held material remains governed

DR-009 — Delivery Readiness
Starting persona:
Program Operator

Decision persona:
Program / Commercial Owner

Core story:
800 requested
→ 600 eligible
→ options
→ commitment decision
→ ERP/Planner verification

Ending:
exact approved commitment
remaining gap truthful

Use actual implemented role names.

==================================================
10. PERSONA QUICK REFERENCE
==================================================

Include a concise table in the runbook and, where appropriate, demo UI:

Persona
Can initiate
Can approve
Primary demo usage

Make role switching instructions obvious.

Do not imply production authentication.

==================================================
11. PRE-DEMO CHECK
==================================================

Provide a deterministic command/check that confirms:

- baseline valid;
- required source apps reachable;
- no stale executable proposal;
- no unexpected workflow currently running;
- no reset inconsistency;
- Concierge backend route available;
- frontend reachable;
- model configured;
- schedulers/listeners inactive.

No paid model call.

==================================================
12. COLD-START VERIFICATION
==================================================

Test from a clean service state:

start
→ status
→ prepare
→ baseline valid
→ Overview opens

Then:
shutdown
→ restart
→ business state persists

Then:
prepare/reset
→ baseline restored

Do not depend on a previous interactive terminal.

==================================================
13. FALLBACK PLAN
==================================================

Document honest fallback behavior if:

- OpenAI API unavailable;
- paid model times out;
- one source app fails;
- Concierge fails;
- live workflow fails.

Do not automatically substitute fake connected intelligence.

Allowed fallback:
recorded result / deterministic demonstration

ONLY when visibly labeled:

Recorded demo

or equivalent.

Provide steps to return to live mode.

==================================================
14. DEMO DATA PROTECTION
==================================================

Ensure startup/preparation does not accidentally:

- duplicate source records;
- reset historical eval artifacts;
- remove docs;
- overwrite source fixtures;
- create new paid runs;
- activate automation workers.

==================================================
15. PERFORMANCE / RESPONSIVENESS
==================================================

Investigate obvious issues that could hurt the live demo.

Review:
- initial app load;
- route chunk loading;
- large bundle advisory;
- excessive polling;
- unnecessary source reads;
- slow modal rendering.

Apply only low-risk optimizations.

Examples:
- lazy-load Operations;
- lazy-load large workflow/detail modules;
- avoid loading all trace/eval data on Overview.

Do not perform a major frontend architecture migration solely to optimize bundle size.

Record what was changed.

==================================================
16. BUNDLE-SIZE ADVISORY
==================================================

Investigate the existing ~bundle-size advisory.

If straightforward code splitting reduces it safely, implement it.

If not, document it and preserve stability.

Do not spend excessive time chasing an advisory that does not affect demo performance.

==================================================
17. CONSOLE / NETWORK CLEANUP
==================================================

Exercise canonical pages and remove avoidable:

- console warnings;
- React key warnings;
- failed asset requests;
- 404 requests;
- repeated failed polling;
- unhandled promise rejections.

Do not suppress legitimate application errors.

==================================================
18. API ERROR UX
==================================================

Ensure common failures show readable UI rather than raw stack traces.

Examples:
source unavailable
model unavailable
workflow timeout
wrong persona
stale proposal
verification mismatch

Keep technical details available in Operations.

==================================================
19. LOADING UX
==================================================

Audit actual demo transitions.

Ensure:
- workflow start;
- agent investigation;
- approval submission;
- execution;
- verification;
- Concierge response

all show a clear state.

No frozen-looking page.

Do not create fake progress percentages.

==================================================
20. OPERATIONS TROUBLESHOOTING
==================================================

Ensure runbook explains how to use Operations for:

- failed workflow;
- tool/source failure;
- partial execution;
- trace lookup;
- eval status.

Do not require terminal debugging for routine demo issues.

==================================================
21. SOURCE-APP ACCESS
==================================================

Ensure the runbook lists direct URLs/routes for:

Engineering Hub
Validation Lab
Manufacturing Portal
Commercial ERP
Program Planner

Use actual app URLs discovered from current startup configuration.

==================================================
22. LIVE-MODE PREPARATION
==================================================

Do NOT run paid models automatically.

But verify:

- required environment configuration present;
- model identifier valid according to existing configured application state;
- actual runtime can be invoked when user explicitly triggers it.

Do not expose the secret.

==================================================
23. OPTIONAL RECORDED FALLBACK DATA
==================================================

If existing recorded successful workflow outputs already exist, index/reference
them safely for fallback documentation.

Do not generate new fake successes.

Do not overwrite current source state merely to display recorded output.

==================================================
24. VISUAL DEMO MODE
==================================================

Keep a subtle indication that this is:

Synthetic demo

and current persona:

Demo identity

Avoid large warning banners across every page.

==================================================
25. AUTOMATED STARTUP TEST
==================================================

Add automated smoke where practical:

- start required test services;
- check health;
- prepare baseline;
- open main routes;
- verify canonical cases exist;
- stop services.

No paid models.

==================================================
26. FULL REGRESSION
==================================================

Run:

- source/backend;
- coordinator;
- MCP;
- offline eval suite;
- all canonical workflow regressions;
- Concierge;
- Operations;
- demo reset;
- browser E2E;
- typecheck/build.

No paid model calls.

==================================================
27. NO CODE FREEZE YET
==================================================

Explicitly document:

Phase 09.4 completes planned feature/harness work.

It does NOT freeze the repository.

Phase 09.5 will perform final manual/live validation.

Targeted code changes discovered during 09.5 are expected and allowed,
including:

- functional bug fixes;
- model/prompt/routing fixes;
- persona/authority UX improvements;
- layout simplification;
- visualization improvement;
- copy changes;
- loading/error-state fixes;
- performance fixes.

Avoid only unrelated new feature expansion.

==================================================
28. REPORT
==================================================

Report:

1. Startup architecture
2. Demo commands/helpers
3. Runbook path
4. Persona quick reference
5. Pre-demo checks
6. Reset integration
7. Fallback procedures
8. Performance improvements
9. Bundle-size result
10. Console/network cleanup
11. Tests/results
12. Cold-start verification
13. Exact local URLs
14. Known remaining issues for Phase 09.5

Stop after 09.4.

Do not run paid live-model tests or perform final Git cleanup.