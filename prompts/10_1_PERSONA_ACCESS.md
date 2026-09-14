Continue in the existing Stratos Silicon repository and Phase 10 thread.
Implement Phase 10.1: PERSONA-AWARE NAVIGATION, VIEWS AND ACTIONS.

Read the latest handoffs, actual demo identities, host authorization policies,
frontend routes, Concierge handlers and tests before editing. The existing
code is authoritative about implemented business authority. This is a targeted
improvement to the working product, not enterprise IAM/SSO implementation.
Preserve working demo data and historical artifacts. No Git commit/push work,
paid model calls, background schedulers or unrelated redesign.

1. PRODUCT RULE

Different personas should see different navigation and actions.

- No permission: HIDE the tab/button/action, rather than show a disabled control.
- Has permission, but prerequisites are unmet: show the action DISABLED with
  a concise reason, such as “Awaiting approval” or “Evidence changed.”
- May read a case but not approve it: show the business state and responsible
  role, not an unauthorized approval button.

Hide means not rendered or exposed through alternate menus/search/Concierge
cards. CSS hiding is not authorization. Keep enforcement server-side.

2. REUSE THE FOUR EXISTING PERSONAS

Use actual existing IDs, including these when confirmed in the repository:
- Program operator: demo-automation
- Engineering approver: demo-engineer
- Program Owner: demo-program-owner
- Read-only viewer: demo-reader

Do not create a fifth business role or rename backend roles for presentation.
The operator initiates/co-ordinates work and performs existing permitted
execution. Engineering handles existing technical approvals. Program Owner
handles existing QE recovery and DR commitment approvals. Viewer observes.

Preserve the exact per-workflow capabilities found in code. In particular:
- CR-019 bounded touchless handoff needs no new human approval.
- CR-017 plan authorization and later evidence review remain separate.
- QE approval does not authorize quality release or establish root cause.
- DR approval does not grant technical acceptance or customer agreement.
- Changing persona never approves, executes, or grants extra agent permissions.

3. TARGET NAVIGATION MATRIX

Surface                  Operator       Engineering     Program Owner    Viewer
Overview                 Show           Show            Show             Show
Programs                 Show           Show            Show             Show
Workflows & Automations  Show           Hide            Hide             Hide
Decisions                Read/track     Engineering     Program/recovery Hide
Scenarios                Show           Technical       Business         Hide
Knowledge & Evidence     Show           Show            Hide             Read
Operations               Limited        Hide            Hide             Hide

“Engineering” and “Program/recovery” mean decision-type filtering and permitted
review actions, not permission to see or operate every decision category.
“Technical” and “Business” use existing scenario categories; do not fabricate
connected scenario functionality or infer categories solely from title text.

Hiding a top-level workspace must not remove needed authorized case functions.
For example:
- Engineering can still investigate a permitted case from that case page even
  though the general Workflows workspace is hidden.
- Program Owner can inspect the evidence supporting a permitted DR/QE decision
  without a top-level Knowledge workspace.
- Viewer can see permitted case-level decision outcomes, without access to
  the dedicated Decisions queue or any mutation controls.

Use separate capabilities for surface access, scoped record reads and actions.
If a target conflicts with an existing necessary path, preserve the permitted
path through a scoped case view and document it. Do not broaden business powers.

4. SHARED CAPABILITY CONTRACT

Reuse existing host policy. Add the smallest capability projection needed for
navigation, route guards, buttons, queues, search, alerts and Concierge.
Avoid scattered role-name conditionals and competing permission tables.

The host resolves an allowed demo identity and computes effective capabilities
for the current object/scope. Never accept client-supplied capability booleans.
Enforce permissions for direct API requests, guessed IDs and alternate routes,
not just for visible controls. Unknown roles/scopes deny by default. Do not
flash restricted tabs/actions while capability data is loading. Keep the
logged-out state non-mutating; never automatically select an elevated persona.

New surface restrictions must have corresponding host protection where they
protect data, especially Operations, decision queues and Concierge sessions.
Return only permitted fields. Business summaries may remain visible even when
technical traces/session contents are restricted.

Keep role permission and workflow readiness distinct: an authorized reviewer
may still be unable to approve a stale or incomplete proposal.

5. ACTIONS AND DECISIONS

Audit all entry points: case CTA, list menu, modal footer, global search,
alerts, workflow page, keyboard actions and Concierge cards.

Operator viewing CR-017:
- may see “Awaiting Engineering review”;
- must not see Approve/Reject engineering buttons;
- may execute an already-approved manifest only if existing policy allows it.

Engineering viewing CR-017:
- sees applicable Approve/Reject controls on the exact current proposal;
- does not gain DR commercial approval.

Program Owner:
- sees existing QE/DR decision controls;
- does not gain engineering evidence approval or lot release.

Viewer:
- no investigate, handoff, approve, execute or automation-save controls;
- explanatory Concierge Q&A is allowed only as supported by current policy.
  A permitted Q&A model call is not permission to start a business workflow.

Do not merge approval and execution confirmations. Maintain exact proposal,
version, actor and current-state checks at each actual mutation.

6. ROLE SWITCHING AND STATE SAFETY

Make the active name/role obvious in the existing selector. Keep concise
“Demo identity” disclosure: these public selectors do not authenticate a person.
Do not add passwords, OAuth, an IdP or pretend authenticated sessions.

On persona switch:
- recompute navigation, actions and permitted queues;
- move to Overview if the current route is no longer permitted;
- close inaccessible dialogs and stop their polling;
- invalidate scoped queries/search caches and stale action previews;
- prevent late responses for the old persona from repopulating the new view;
- scope or replace the visible Concierge session so restricted old content or
  action cards do not carry across personas;
- stop voice capture and preserve drafts only where their content/scope remains
  appropriate. Never auto-send after switching.

Preserve immutable approvals already made by the previous human. Switching
persona does not revoke a valid approval, cancel a run or change attribution.
Revalidate the current actor before any NEW request/action.

7. OVERVIEW, SEARCH, ALERTS AND CONCIERGE

Keep program health based on the same authoritative facts for every persona.
Change relevance/order, not facts:
- Operator: investigations, handoffs and operational blockers.
- Engineering: engineering reviews ready for that role.
- Program Owner: recovery/commitment decisions and business exposure.
- Viewer: permitted program status and recorded outcomes.

“Needs your review” counts only current reviewable proposals for that actor.
A dependency owned by another role can be shown as informational status, not
as an unauthorized approval CTA. No invented counts to populate an empty queue.

Filter search, alerts, quick actions and Concierge BEFORE returning restricted
content or placing it in the model's context. An unavailable Operations tab
must not be bypassed by “show me another person's chat transcript.”

Concierge must show only allowed action cards. A request outside authority
receives a short explanation and permitted navigation, without performing it.
Persona switching remains an explicit demo UI interaction, never an agent tool.

8. DEMO CONTROLS AND SOURCE-APP BOUNDARY

Keep reset available through the existing demo-maintenance gate and CLI.
Do not lose this operator function by hiding Operations, or give every persona
reset permission as a workaround. Preserve its deliberate confirmation and
keep it inaccessible to agents/Concierge.

Audit Source apps links and embedded previews for scoped access. Do not claim
this change secures independently accessible mock source apps unless they
actually enforce the same checks. Document that environment boundary; do not
silently build a five-app authentication migration.

9. VERIFICATION

Use isolated deterministic test data, not the user's active walkthrough state.
Test all four personas against every navigation destination and action family.
Include:
- unauthorized actions absent, but unmet-prerequisite actions disabled;
- direct denied API/deep-link requests rejected, with zero business writes;
- operator cannot approve engineering or commitment decisions;
- engineering cannot approve DR/QE decisions outside its policy;
- Program Owner cannot approve engineering evidence or release held material;
- viewer cannot invoke workflows through UI, API or Concierge;
- existing permitted investigation/execution paths still work;
- identity switch invalidates drafts/action payloads and late scoped responses;
- search/alerts/Concierge do not leak restricted data or controls;
- valid existing approvals/history remain intact;
- demo reset and all four workflow regressions remain usable;
- no automatic approval/execution from persona switching.

Run relevant host/source/coordinator tests, Concierge and Operations tests,
current offline eval gates, browser checks, typecheck and build. Report actual
counts and skips, without double-counting overlapping suites. No paid runs.

10. REPORT AND STOP

Update requirements, capability matrix and runbook. Include exact implemented
business authority versus presentation access, changed files, tests, limits,
and one Overview screenshot per persona plus Engineering and DR decision views.
Report any remaining source-app/demo-identity limitations honestly.

Stop after 10.1. Do not implement the Agent Workspace redesign yet.