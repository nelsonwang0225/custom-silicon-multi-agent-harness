Continue working in the existing take-home repository. This is a targeted
compatibility update to accommodate the expanded control-plane direction
before continuing Phase 06.

Inspect the repository, implement the smallest necessary changes, verify
them, and report back. Do not stop at a plan unless you find a genuine
blocker or a conflict with the existing execution/approval contract.

==================================================
1. CURRENT POSITION AND SCOPE
==================================================

Our last reported checkpoint:
- Phase 04: OpenAI Runtime & Agent Tools.
- Phase 05: Multi-Agent Orchestration.
- Next: Phase 06 — Human Approval & Execution, beginning with the
  execution contract and approval boundary.
- Later: Phase 07 — Evals & Reliability.
- Later: Phase 08 — Agentic Control Plane.
- Later: Phase 09 — Demo Polish & Final Verification.

The repository is authoritative about what is actually implemented.
Do not assume that roadmap text means a capability already works.

We are continuing the existing implementation, not restarting it.

Before editing:
- Read applicable AGENTS.md files and the existing project documentation.
- Inspect git status and preserve unrelated/uncommitted work.
- Locate the current orchestration, case/run state, persistence, tools,
  approval/execution contracts, entry points, and tests.
- Identify any Phase 06 work already present.
- Establish the relevant offline test baseline.

Reuse existing models, storage, runtime, and interfaces wherever possible.
Prefer small extensions/adapters over a parallel framework.
Do not rename everything to match the conceptual terms below.

==================================================
2. UPDATED PRODUCT DIRECTION — CONTEXT ONLY
==================================================

The eventual product is a custom-silicon program control plane.

Its three primary workflow types are:
1. Requirement-change impact and validation planning.
2. Yield/quality exception impact and recovery.
3. Customer delivery readiness and commitment planning.

For this update:
- Preserve CR-017 as the existing golden-path fixture.
- Preserve the existing customer/program identifiers, evidence,
  approved option definitions, and scenario policies from the repo.
- Only the existing requirement-change investigation should execute.
- The other two workflows are catalog entries only:
  illustrative / not executable.

The eventual control-plane surfaces are:
Portfolio, Programs, Workflows & Automations, Decisions, Scenarios,
Knowledge & Evidence, and Operations, with contextual chat available
throughout.

Future initiation methods include manual requests, schedules, source
events, and chat. They should eventually call the same governed backend
service, not separate execution implementations.

Broader capabilities may be illustrated later, including configuration
readiness, evidence freshness, waivers, validation planning, capacity/cost
scenarios, and acceptance evidence packages.

Document this future direction. Do not build these UI features now.

==================================================
3. MAKE THE EXISTING WORKFLOW REUSABLE
==================================================

Inspect existing abstractions before adding anything.

The logical relationships we need are:
- A program has cases.
- A case can have multiple workflow runs.
- Each run references a workflow definition and version.
- A run may produce recommendations and versioned proposals.
- Human decisions refer to an exact proposal.
- Action attempts and verification results are separate records.

A case is not the same thing as a run.
A workflow definition is not the same thing as an execution.
A recommendation is not approval.
Approval is not execution.
Execution success is not verified business readiness.

Adapt existing models to support these distinctions where necessary.
Do not create a new table/class for every concept if existing structures
can represent them clearly.

Remove CR-017-specific assumptions from reusable orchestration or
approval logic where practical. Keep scenario-specific facts and policy
in fixtures/configuration or the appropriate domain layer.

Preserve existing entry points and structured outputs where possible.
Use backward-compatible adapters or additive fields rather than
unnecessary breaking changes.

==================================================
4. ADD OR EXTEND A SMALL WORKFLOW REGISTRY
==================================================

Use existing identifiers if equivalents already exist; otherwise use:

- requirement_change_analysis
- yield_exception_recovery
- delivery_readiness

Include sufficient metadata for future consumers:
- stable identifier and definition version
- display name and description
- implementation status
- currently supported operations
- participating specialists, using the existing agent names
- existing tool/approval-policy references
- actual execution mode

Separate current capabilities from planned capabilities.

Requirement-change analysis:
- Dispatch to the existing investigation/orchestration.
- Advertise only capabilities verified in the repository.
- Do not label the full human-approved execution flow complete merely
  because the analysis is executable.

Yield recovery and delivery readiness:
- Metadata only.
- No executor or new action permissions.
- Attempted execution must return an explicit unsupported/not-implemented
  result before invoking agents or tools.
- Do not return fabricated successful runs.

Catalog metadata must not grant tool permissions or override runtime policy.

Keep synthetic-data provenance separate from execution capability:
a real run against synthetic data is different from a simulated run.

==================================================
5. GENERALIZE THE PHASE 06 CONTRACT, NOT ITS AUTHORITY
==================================================

Inspect and preserve the existing Phase 06 contract first.

If proposal/decision objects already exist, extend them rather than
creating a competing approval mechanism.

The contract should support:
- program, case, workflow definition/version, and originating run
- proposal identifier and immutable proposal version/snapshot
- explicit proposed actions and their exact arguments
- supporting evidence references and relevant source versions
- rationale, assumptions, and preconditions
- required approval policy/role
- a separate decision record bound to that exact proposal
- separate action and verification records

Use a stable version or digest to bind a decision to the approved content.
Changing the action, target, parameters, or material supporting evidence
must not silently reuse the old authorization.

Represent stale/rejected/unapproved proposals as non-executable.

Actor identity and approval authority must come from the trusted
application context, not an LLM response or a client-supplied role string.
If the repository uses demo identities rather than real authentication,
preserve and explicitly document that limitation.

This update may add typed contracts and pure validation functions.
It must NOT introduce new source-system write tools or approval endpoints
just to demonstrate the generic model.

If Phase 06 execution is not implemented, leave it unimplemented.
If some execution is already implemented, preserve its existing checks
and permissions; do not bypass or broaden them.

Do not infer permission from a mock API endpoint merely existing.
Confirm permitted actions against the repo's approved execution contract.

Our intended narrow execution boundary remains approved Validation Lab
scheduling and permitted Program Planner updates, subject to the exact
existing contract. Do not add manufacturing holds/releases, test-criteria
changes, inventory reallocations, ERP commitments, or external messages.

A verified scheduling action proves that a job was scheduled.
It does not prove the test passed or the customer accepted the product.

Preserve existing SDK state/resumption mechanisms where present.
Do not build a second agent runner or duplicate SDK execution state.

==================================================
6. REUSE A PERSISTED ACTIVITY TIMELINE
==================================================

Inspect existing case histories, run logs, and storage first.

Add or adapt a minimal activity record so future UI/chat can retrieve
business activity by program, case, and run.

Useful fields include:
- event ID and timestamp
- program/case/run references
- event type
- trusted actor/source
- related proposal/action references where applicable
- concise structured details and evidence/source references

Record only events that actually occurred.
Do not manufacture approval, execution, or verification events for
unimplemented capabilities.

Keep business activity distinct from technical traces, but link their
identifiers where the existing runtime supports it.

Use the current persistence approach. No message broker, event-sourcing
platform, or infrastructure replacement is needed.

Store audit facts and concise explanations, not hidden chain-of-thought
or secrets.

==================================================
7. EXPOSE ONE REUSABLE INVOCATION BOUNDARY
==================================================

Wrap or adapt the current orchestration through a small service boundary
that future UI, CLI, chat, scheduler, and event handlers can share.

Conceptual inputs:
- workflow identifier
- program/case scope
- trigger/source metadata
- trusted actor context
- invocation/correlation identifier

Use repository naming and architecture conventions.
Do not add a new HTTP server merely to create this boundary.

The service must:
- validate the workflow and program/case scope
- reject illustrative/unknown workflows explicitly
- preserve existing tool restrictions and guardrails
- dispatch requirement-change analysis to the existing implementation
- persist/link the actual run and its activity
- avoid duplicate starts for the same invocation identifier

A deliberate rerun may use a new invocation identifier.
Repeated runs should not automatically create duplicate business cases.

Future trigger metadata must not grant extra authority.
Document future caller contracts, but do not build a scheduler,
event listener, chat endpoint, streaming layer, or notification service.

==================================================
8. REQUIRED VERIFICATION
==================================================

Use deterministic fixtures/mocks and isolated test storage.

Do not automatically run paid model calls or external integrations.
Do not reset the user's demo data or mutate the five source applications'
business records during verification.

Persisting test case/run/proposal/activity metadata in isolated storage
is allowed.

Run the relevant existing offline suite plus tests covering:

A. Regression
- Existing CR-017 entry points still work in offline tests.
- Existing scenario/policy branches retain their expected behavior.
- Specialist/tool scopes and guardrails have not broadened.

B. Registry and dispatch
- All three workflow definitions are discoverable.
- Only implemented operations are advertised.
- Illustrative workflows fail explicitly with zero agent/tool calls.
- Unknown identifiers fail clearly.

C. Case/run relationships
- Repeated runs can remain attached to the same case.
- Program/case mismatches are rejected.
- Duplicate invocation IDs do not start duplicate investigations.

D. Proposal/decision contract
- A decision is bound to the exact proposal version/content.
- Modified proposals or material evidence changes cannot reuse approval.
- Rejected, stale, missing-approval, wrong-scope, and wrong-role cases
  are rejected by the relevant contract validators.
- Test these as contracts/validators when execution is not implemented;
  do not create a write executor solely to satisfy these tests.

E. Persistence and state
- Case/run/proposal/activity records reload correctly.
- Recommendation, approval, action outcome, and verification remain
  distinguishable after persistence.
- Analysis completion cannot be interpreted as customer acceptance.

F. Permission preservation
- No new source-system write tools are exposed to agents.
- No new chat/scheduler entry point bypasses the service boundary.
- Existing five-app interfaces and API contracts remain unchanged.

Run existing lint/type checks where available.
Report actual commands and results, including skips and pre-existing
failures. Do not weaken tests or assertions to obtain a pass.

Offline verification does not prove live-model behavior.
State explicitly which live checks were not rerun.

==================================================
9. DOCUMENTATION, REPORT, AND STOPPING POINT
==================================================

Update the existing architecture/handoff documentation with:
- the actual object/relationship mapping
- registry and invocation service interfaces
- proposal/approval invariants
- persisted activity approach
- current versus illustrative capabilities
- the future control-plane direction
- the exact remaining Phase 06 work

Use existing documentation conventions and paths.
Do not mark Phase 06 or Phase 08 complete.

Finish with:

1. Baseline found
   What actually existed, including any Phase 06 implementation.

2. Changes made
   Exact files changed and why; existing components reused.

3. Capability and permission matrix
   For each workflow: implemented operations, execution mode,
   actual tool access, and approval requirements.

4. Verification report
   Check | command/test | result | evidence.
   Distinguish passed, failed, skipped, and not implemented.

5. Remaining work
   The next specific step in Phase 06, plus any blockers.

Stop after this compatibility update and verification.
Do not continue into write-tool implementation, the two additional
workflows, Phase 07, or the Phase 08 control-plane UI.