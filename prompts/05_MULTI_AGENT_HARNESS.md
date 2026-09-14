Proceed to Phase 05: build the Stratos Silicon coordinator-led multi-agent orchestration layer.

We already have:

- five working Stratos Silicon mock enterprise applications
- persistent synthetic enterprise data
- deterministic HTTP APIs
- enterprise API client
- local Streamable HTTP MCP server
- GPT-6 Astra API connectivity
- OpenAI Agents SDK runtime
- a verified single-agent ProgramInvestigator baseline
- tracing
- structured investigation output
- CR-017 golden-path validation

The existing ProgramInvestigator successfully investigated CR-017 through MCP.

Do NOT remove that implementation. Preserve it as the single-agent baseline for comparison.

This phase introduces the production-oriented multi-agent harness.

==================================================
ARCHITECTURE PRINCIPLE
==================================================

Use:

COORDINATOR-LED MULTI-AGENT ORCHESTRATION
WITH BOUNDED DYNAMIC SPECIALIST COLLABORATION.

This is intentionally NOT:

- a rigid fixed pipeline
- a fully decentralized swarm
- unrestricted agent-to-agent communication

The Program Coordinator owns the overall case lifecycle.

Specialist agents may dynamically call other approved specialists when additional expertise is genuinely required, but:

- case ownership always returns to the Program Coordinator
- only the Program Coordinator produces the authoritative final case synthesis
- specialists cannot close the case
- specialists cannot approve consequential actions
- specialists cannot mutate business systems in this phase
- delegation paths must be explicitly permitted
- delegation depth and total specialist calls must be bounded

==================================================
TARGET ARCHITECTURE
==================================================

Incoming Program Change Event
            |
            v
     Program Coordinator
       Manager Agent
            |
     classify + triage
            |
     decide required work
            |
     +-------------------------+--------------------------+
     |                         |                          |
     v                         v                          v
Change Impact Agent   Validation & Evidence Agent   Program / Commercial
                                                 Impact Agent
                               |
                               |
                     when justified only
                               v
                    Manufacturing Agent

Specialists return structured findings.

Some specialist work may run in parallel.

A specialist may call another permitted specialist when the investigation discovers a dependency that genuinely requires that expertise.

All completed specialist results ultimately return to:

Program Coordinator
        |
        v
Final Decision Package
        |
        v
Policy-path determination:
- touchless eligible
- human review required
- escalation / clarification required

This phase STOPS before actual business mutations or human approval execution.

==================================================
AGENTS
==================================================

Build five agents:

1. Program Coordinator
2. Change Impact Specialist
3. Validation & Evidence Specialist
4. Program / Commercial Impact Specialist
5. Manufacturing Specialist

Use GPT-6 Astra initially for all agents unless current official guidance strongly suggests a technical compatibility issue.

Do not add model routing yet.

We will measure quality/latency/cost first and optimize models later.

==================================================
1. PROGRAM COORDINATOR
==================================================

Role:

The Program Coordinator is the manager agent and owns the case.

Responsibilities:

- intake new program/change events
- classify the request
- determine whether enough information exists to proceed
- identify customer/program scope
- determine which specialists are actually needed
- launch independent specialist work in parallel where appropriate
- invoke no specialist when no specialist analysis is necessary
- reconcile specialist results
- detect disagreement or missing information
- request additional specialist analysis when justified
- determine whether the case is:
  - eligible for touchless handling
  - requires human review
  - requires escalation / clarification
- create the final structured decision package

The Coordinator should NOT:

- become the deepest domain expert itself
- duplicate specialist investigations unnecessarily
- mechanically call every specialist
- invent facts when a specialist/source has not established them
- perform writes
- approve engineering actions
- claim validation success
- bypass MCP/source systems

The Coordinator should first perform TRIAGE.

==================================================
GENERIC INTAKE
==================================================

The Coordinator must NOT be designed specifically around CR-017.

Define a generic input model such as:

ProgramChangeEvent

Suggested fields:

- event_id
- change_id
- customer_id
- program_id
- source_system
- change_type_hint (optional)
- priority
- requested_by
- received_at
- request_summary / freeform_request
- linked_record_ids[]
- correlation_id

The Coordinator must be able to handle different change types.

Do not assume every request concerns validation.

==================================================
CHANGE CLASSIFICATION
==================================================

Create an extensible but bounded taxonomy such as:

- validation_requirement_change
- workload_profile_change
- runtime_firmware_change
- power_thermal_requirement
- performance_acceptance_change
- manufacturing_constraint
- program_schedule_change
- customer_acceptance_change
- other_or_unknown

The model performs semantic classification.

Return a structured TriageDecision containing fields such as:

- classified_change_type
- confidence
- rationale
- specialists_required[]
- missing_information[]
- risk_level
- proposed_workflow
- likely_policy_path

Do not allow classification alone to authorize execution.

If confidence is low or required information is missing:

- request clarification
or
- escalate

rather than forcing specialist work.

==================================================
SPECIALIST AGENT 1:
CHANGE IMPACT
==================================================

Purpose:

Determine:

WHAT CHANGED?
WHAT DOES IT AFFECT?

Primary responsibilities:

- compare baseline and proposed requirements
- identify relevant product/configuration
- identify affected program scope
- identify relevant engineering records
- identify milestones/dependencies potentially affected
- identify customer/program relationships
- preserve source IDs and versions
- distinguish confirmed impact from possible impact

Do NOT:

- decide whether validation evidence is sufficient
- select a validation option
- approve anything
- perform writes

Return a typed:

ChangeImpactAssessment

Suggested fields:

- change_type
- requirement_delta
- affected_scope[]
- confirmed_impacts[]
- possible_impacts[]
- unaffected_scope[]
- missing_information[]
- source_references[]
- confidence

==================================================
SPECIALIST AGENT 2:
VALIDATION & EVIDENCE
==================================================

Purpose:

Determine:

DO EXISTING RESULTS COVER THE REQUEST?
IF NOT, WHAT APPROVED OPTIONS COULD CLOSE THE GAP?

Responsibilities:

- inspect validation coverage
- inspect historical evidence
- reject evidence from wrong revisions/configurations/workloads
- identify gaps
- inspect test procedures
- evaluate resource eligibility
- inspect available samples
- evaluate lab/test options
- use tool-provided cost/timing facts
- identify unresolved technical questions
- distinguish evidence gap from product failure

Do NOT:

- invent test criteria
- calculate authoritative eligibility independently of deterministic tools
- approve a plan
- claim a scheduled job passed
- perform writes

Return:

ValidationEvidenceAssessment

Suggested fields:

- coverage_status
- evidence_gaps[]
- applicable_evidence[]
- inapplicable_evidence[]
- eligible_options[]
- ineligible_options[]
- technical_constraints[]
- unresolved_questions[]
- source_references[]
- confidence

==================================================
SPECIALIST AGENT 3:
PROGRAM / COMMERCIAL IMPACT
==================================================

Purpose:

Determine:

WHAT DOES THIS MEAN FOR PROGRAM EXECUTION AND CUSTOMER COMMITMENTS?

Responsibilities:

- inspect program milestones
- inspect dependencies
- inspect customer commitments
- inspect approved cost inputs
- distinguish:
  - baseline
  - internal forecast
  - external/customer commitment
- identify schedule exposure
- identify relevant program owners
- identify commercial/program implications supported by actual records

Do NOT:

- alter committed dates
- invent revenue impact
- calculate "money saved" unless an authoritative tool provides such data
- determine engineering acceptance
- perform writes

Return:

ProgramCommercialAssessment

Suggested fields:

- affected_milestones[]
- dependencies[]
- customer_commitments[]
- schedule_exposure[]
- cost_context[]
- owners[]
- risks[]
- unresolved_questions[]
- source_references[]

==================================================
SPECIALIST AGENT 4:
MANUFACTURING
==================================================

Purpose:

Provide focused manufacturing provenance/restriction analysis when needed.

Responsibilities:

- inspect unit provenance
- inspect lot provenance
- identify active restrictions/holds
- inspect freshness of manufacturing records
- explain release/review conditions when present
- identify whether a proposed sample/resource is currently usable

Do NOT:

- release holds
- change routes
- change manufacturing state
- diagnose physical root cause without evidence
- infer yield
- perform writes

Return:

ManufacturingAssessment

Suggested fields:

- units[]
- lots[]
- active_restrictions[]
- provenance_findings[]
- freshness_findings[]
- release_conditions[]
- unresolved_questions[]
- source_references[]

==================================================
SPECIALIST TOOL ACCESS / LEAST PRIVILEGE
==================================================

DO NOT give every specialist all MCP tools.

Use least-privilege MCP tool access.

Suggested boundaries:

Change Impact:
- Engineering Hub
- selected Program Planner reads
- selected ERP/program context if needed

Validation & Evidence:
- Validation Lab
- relevant Engineering procedure/configuration/workload reads
- selected Manufacturing reads where appropriate
- cost/timing data through approved deterministic tools

Program / Commercial:
- Program Planner
- Commercial ERP
- minimal Engineering context necessary for linking the change

Manufacturing:
- Manufacturing Portal
- minimal validation/sample context when required

Program Coordinator:
Prefer specialist outputs over directly using all source-system tools.

The Coordinator may retain a very small set of high-level case/intake tools where justified, but should not duplicate deep specialist tool access.

Document the final tool matrix explicitly.

==================================================
BOUNDED SPECIALIST-TO-SPECIALIST COLLABORATION
==================================================

Specialists may request other specialist expertise, but only through an explicit collaboration graph.

Start with permitted relationships conceptually such as:

Program Coordinator:
→ Change Impact
→ Validation & Evidence
→ Program / Commercial Impact
→ Manufacturing

Change Impact:
→ Validation & Evidence when requirement impact raises an evidence/qualification question
→ Program / Commercial Impact when change impact creates milestone/commitment questions

Validation & Evidence:
→ Manufacturing when a sample/lot restriction/provenance issue requires dedicated analysis
→ Program / Commercial Impact when validation timing/cost creates schedule implications

Program / Commercial Impact:
→ Change Impact when program impact depends on unresolved requirement scope

Manufacturing:
→ no downstream specialist initially unless a clear justified requirement emerges

Do not create unrestricted all-to-all delegation.

Enforce:

- maximum delegation depth
- maximum specialist invocations
- prevention of repeated identical delegation
- cycle/loop prevention
- timeout limits
- structured specialist outputs
- centralized final synthesis

Case ownership ALWAYS returns to Program Coordinator.

==================================================
PARALLELISM
==================================================

Support parallel specialist execution where tasks are independent.

For example:

CR-017 can launch:

- Change Impact
- Validation & Evidence

in parallel after triage.

Program / Commercial analysis may also run concurrently once sufficient identifiers are known.

Do not parallelize work with unresolved dependencies purely for speed.

Use deterministic/code-driven orchestration around parallel execution where appropriate.

Document which steps are:

MODEL-DRIVEN

versus

CODE-DRIVEN.

==================================================
HYBRID ORCHESTRATION
==================================================

Use a hybrid architecture.

MODEL-DRIVEN decisions may include:

- semantic classification
- determining which expertise is required
- interpreting evidence
- deciding whether another specialist would add value
- synthesizing specialist findings

CODE-DRIVEN controls must include:

- allowed specialist graph
- max delegation depth
- max specialist calls
- timeouts
- retries
- required specialist outputs
- schema validation
- loop prevention
- execution-policy enforcement
- case-state transitions

Do not rely on prompts alone for runtime safety.

==================================================
SHARED CASE STATE
==================================================

Introduce application-owned case state.

Do not rely only on model conversation history.

Create a typed CaseContext / CaseState containing appropriate fields such as:

- case_id
- correlation_id
- customer_id
- program_id
- input event
- triage decision
- requested specialists
- completed specialist assessments
- pending specialist work
- source/version references
- workflow stage
- risk/policy classification
- unresolved questions
- final package status

The application is authoritative for workflow state.

Models consume only the context needed for their current task.

==================================================
STRUCTURED OUTPUTS
==================================================

Every agent must use typed structured outputs.

Do not pass specialist freeform prose to the Coordinator as the primary contract.

Use:

TriageDecision
ChangeImpactAssessment
ValidationEvidenceAssessment
ProgramCommercialAssessment
ManufacturingAssessment
FinalDecisionPackage

Preserve useful:
- source references
- record IDs
- content versions
- confidence/uncertainty
- unresolved questions

==================================================
FINAL DECISION PACKAGE
==================================================

The Program Coordinator should return a typed:

FinalDecisionPackage

Suggested fields:

- case_id
- customer
- program
- classified_change_type
- change_summary
- affected_scope[]
- specialist_findings[]
- confirmed_facts[]
- evidence_gaps[]
- available_options[]
- relevant_constraints[]
- program_impact[]
- risks[]
- unresolved_questions[]
- recommended_next_step
- policy_path
- requires_human_review
- escalation_reason
- source_references[]

policy_path should support:

- touchless_eligible
- human_review_required
- escalation_required

IMPORTANT:

In this phase, "touchless_eligible" means that policy/evidence indicate the workflow could proceed autonomously in a later execution phase.

DO NOT execute any business writes yet.

==================================================
GUARDRAILS
==================================================

Add meaningful guardrails.

INPUT / CASE GUARDRAILS:

- valid case/change identity
- valid customer/program scope
- unsupported or malformed event detection
- request completeness check

OUTPUT GUARDRAILS:

Reject or flag outputs that claim:

- validation passed without authoritative result
- customer acceptance without authoritative record
- physical root cause without sufficient evidence
- customer commitment changed
- approval granted when none exists
- action executed when no write occurred

Require:

- source-backed factual claims where applicable
- mandatory structured fields
- unresolved ambiguity to remain explicit

TOOL GUARDRAILS:

Preserve MCP/source-system scoping.

Validate tool responses before injecting them into agent context.

Do not allow arbitrary IDs from another customer/program to silently enter the case.

Important:

Guardrails are defense-in-depth.

Existing Stratos APIs remain the authoritative permission boundary.

==================================================
BOUNDED EXECUTION
==================================================

Add operational limits such as:

- max coordinator turns
- max specialist calls
- max nested delegation depth
- tool-call timeouts
- bounded retries
- explicit termination conditions

Prevent runaway agent loops.

Record when a run terminates because a limit was reached.

==================================================
TRACING / OBSERVABILITY
==================================================

Enable Agents SDK tracing across the entire multi-agent case.

The trace should make it possible to inspect:

- Coordinator run
- classification/triage
- specialist calls
- parallel branches
- specialist-to-specialist delegation
- MCP calls
- guardrail outcomes
- structured outputs
- final Coordinator synthesis

Propagate case/correlation IDs where possible through:

agent trace
→ specialist call
→ MCP call
→ enterprise API request

Do not expose credentials or sensitive configuration.

Document how the trace can be inspected in the OpenAI Platform.

==================================================
THREE DEMONSTRATION SCENARIOS
==================================================

Design the harness to support at least three different input scenarios through the SAME Coordinator entry point.

Do not create separate hard-coded orchestration logic per case.

SCENARIO A — TOUCHLESS ELIGIBLE

Create or select a synthetic case representing a low-risk, well-bounded change where:

- change category is understood
- required evidence exists or approved procedure is clear
- deterministic policy rules would permit autonomous follow-through
- no consequential engineering judgment is required

Example direction:
runtime/firmware compatibility or another already-authorized validation change.

The Coordinator should:
- classify
- call only needed specialists
- return policy_path = touchless_eligible

No write occurs in this phase.

SCENARIO B — HUMAN REVIEW

Use existing CR-017:

Helios AI
long-context validation requirement
evidence gap
schedule/cost tradeoff
engineering review required

Expected policy path:

human_review_required

Specialist work may run in parallel.

Dynamic Manufacturing analysis may occur when restrictions require it.

SCENARIO C — ESCALATION / INSUFFICIENT EVIDENCE

Create or select a synthetic case where:

- intake is incomplete
OR
- evidence conflicts materially
OR
- request falls outside supported categories/policy

Coordinator should:

- avoid unnecessary specialist calls where possible
- explicitly identify missing/contradictory information
- return policy_path = escalation_required

This scenario demonstrates that the Coordinator can stop rather than hallucinate a solution.

==================================================
COORDINATOR FLEXIBILITY
==================================================

The Coordinator must support:

- zero specialists
- one specialist
- multiple specialists
- parallel specialist calls
- dynamic specialist-to-specialist delegation

Do not mechanically run the same graph for every case.

Capture which specialists were requested and why.

==================================================
BASELINE COMPARISON
==================================================

Keep the existing single-agent ProgramInvestigator implementation intact.

For CR-017, compare:

SINGLE-AGENT BASELINE

vs

MULTI-AGENT HARNESS

Measure safely:

- business correctness
- specialist/tool calls
- latency
- model usage/tokens
- total agent turns
- MCP calls
- source coverage
- output completeness

Do not claim multi-agent is automatically better.

Document whether specialization improves:
- trace clarity
- modularity
- eval isolation
- reliability
- tool least-privilege

and what cost/latency tradeoff it introduces.

==================================================
EVALUATION HOOKS
==================================================

Do not build the full Phase 07 eval system yet.

But design the agents so each can be evaluated independently.

Create initial lightweight behavioral checks for:

Change Impact:
- correct requirement delta
- correct affected scope
- no unsupported validation conclusion

Validation:
- correct coverage
- rejects wrong revision evidence
- respects manufacturing restrictions
- correct eligible/ineligible options

Program / Commercial:
- distinguishes baseline / forecast / commitment
- uses authoritative cost/schedule records
- does not invent financial impact

Manufacturing:
- recognizes holds/restrictions
- preserves provenance
- no unauthorized release recommendation

Coordinator:
- calls appropriate specialists
- avoids unnecessary specialists
- handles conflicting/missing information
- does not contradict specialist evidence
- returns correct policy path
- produces complete final schema

==================================================
MODEL / COST STRATEGY
==================================================

Use GPT-6 Astra for all agents initially.

Record:

- model calls
- latency
- safe token/usage metadata

Do NOT implement model routing yet.

We will decide later whether simpler specialists can use a cheaper/faster model based on measured performance.

==================================================
NO BUSINESS WRITES
==================================================

This phase remains read-only.

Do NOT expose or call MCP tools for:

- creating plans
- approving plans
- scheduling validation jobs
- linking Program Planner
- updating ERP
- updating Manufacturing

Phase 06 will introduce human approval and authorized execution.

==================================================
TESTING
==================================================

Add offline/unit tests for:

- all five agent definitions
- structured schemas
- tool access matrix
- collaboration graph
- delegation-depth enforcement
- cycle prevention
- max-call limits
- shared case state
- parallel orchestration
- guardrails
- malformed specialist output
- missing specialist
- timeout/failure behavior
- no write-capable tools available

Run existing regression tests.

Then perform live Astra runs for:

- touchless scenario
- CR-017 human-review scenario
- escalation scenario

Use the real MCP server and real Stratos source-system APIs.

Do not run excessive paid calls.

For each scenario, record:

- triage result
- specialists invoked
- parallel branches
- specialist-to-specialist calls
- MCP tool calls
- final policy path
- structured output validity
- latency/usage
- trace ID / trace inspection location
- whether any unexpected business mutation occurred

Verify persisted business state remains unchanged.

==================================================
DOCUMENTATION
==================================================

Create:

docs/MULTI_AGENT_HARNESS_HANDOFF.md

Include:

1. Architecture diagram
2. Program Coordinator instructions/role
3. Specialist roles
4. MCP tool-access matrix
5. Allowed specialist collaboration graph
6. Model-driven vs code-driven orchestration
7. Case-state model
8. Guardrails
9. Execution limits
10. Structured schemas
11. Parallelism behavior
12. Three scenario results
13. CR-017 single-agent vs multi-agent comparison
14. Tracing approach
15. Tests and actual results
16. Safe cost/latency/token metrics
17. Known limitations
18. What Phase 06 will add

Do not add:
- business write tools
- human approval execution
- final control-plane UI
- model routing
- remote MCP hosting
- another orchestration framework such as LangChain, LangGraph, CrewAI or AutoGen

Use the OpenAI Agents SDK as the orchestration framework.

Preserve the existing ProgramInvestigator single-agent baseline.

Stop when the coordinator-led multi-agent harness is working reliably across the three scenarios.

Finish with:

MULTI-AGENT HARNESS STATUS: PASS, PARTIAL, or BLOCKED