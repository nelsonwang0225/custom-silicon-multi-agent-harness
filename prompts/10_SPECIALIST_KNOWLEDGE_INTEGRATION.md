Continue in the existing Stratos Silicon repository after the shared Knowledge &
Evidence RAG foundation is complete.

Implement the second RAG enhancement:
SPECIALIST KNOWLEDGE RETRIEVAL INTEGRATION + EVALS + RUN PROVENANCE.

This phase should improve evidence grounding without replacing the existing
structured source tools or governance model.

Do not redesign workflows.
Do not change business authority.
Do not create separate RAG stores per agent.
Do not give the Coordinator unrestricted corpus search.
Do not activate the autonomous QE-011 trigger yet.

==================================================
1. OBJECTIVE
==================================================

Allow selected existing specialists to use the shared Knowledge Retrieval service
when unstructured procedural/document knowledge is relevant.

Target behavior:

structured source facts through MCP/API
+
unstructured institutional knowledge through RAG
+
exact document/version verification
→ specialist finding
→ coordinator synthesis
→ existing policy/human approval/execution

RAG is evidence augmentation, NOT a new decision authority.

==================================================
2. AGENTS TO INTEGRATE
==================================================

Integrate deliberately.

A. CHANGE IMPACT SPECIALIST
Use CHANGE_IMPACT profile.

Typical questions:
- Which approved change-control policy applies?
- Is this request considered standard or material?
- What engineering specification defines the requested condition?
- Are there relevant architecture/change notes?

B. VALIDATION & EVIDENCE SPECIALIST
Use VALIDATION_EVIDENCE profile.

Typical questions:
- Which approved validation procedure applies?
- What does the acceptance criteria document require?
- Which test report sections are relevant?
- What engineering review rules apply?

C. MANUFACTURING / SUPPLY SPECIALIST
Use MANUFACTURING_QUALITY profile.

Typical questions:
- What quality SOP governs held material?
- What approved investigation procedure applies?
- What does historical investigation guidance say about the observed pattern?

D. PROGRAM / COMMERCIAL SPECIALIST
Integrate narrowly using PROGRAM_COMMERCIAL profile only where document policy or
customer/program guidance is genuinely required.

Do not force RAG usage merely because the agent has access to it.

E. PROGRAM COORDINATOR
Do NOT give broad direct RAG access by default.
Coordinator consumes specialist findings and source references.

==================================================
3. WHEN TO USE RAG
==================================================

Update specialist instructions so they understand:

Use STRUCTURED tools when asking:
- what is the current lot state?
- what quantity is available?
- what order exists?
- what job is scheduled?
- what approval exists?
- what current source-system record says?

Use KNOWLEDGE RETRIEVAL when asking:
- what does the approved procedure require?
- which policy applies?
- what does the SOP say?
- what does the engineering spec define?
- what historical guidance is relevant?

Do not semantic-search operational records simply because RAG exists.

Do not exact-fetch every document before semantic discovery when the relevant
document is genuinely unknown.

==================================================
4. RETRIEVAL DECISION
==================================================

Do not force a retrieval call on every agent invocation.

The specialist should retrieve knowledge only when:

- unstructured knowledge is necessary to answer;
- procedure/policy applicability is uncertain;
- a source record references a document whose relevant section must be interpreted;
- a user asks a policy/procedure/document question;
- workflow policy requires supporting procedural knowledge.

Avoid unnecessary RAG calls that add latency/noise.

==================================================
5. RETRIEVAL + EXACT VERIFICATION
==================================================

Preferred pattern:

1. semantic search finds candidate passage/document
2. validate metadata/applicability
3. exact-fetch/verify authoritative document/version where materially relied upon
4. cite the exact source
5. reason

Do not treat vector similarity as proof of applicability.

A high retrieval score cannot override:
- wrong program
- wrong configuration
- superseded version
- unapproved draft
- effective-date mismatch

==================================================
6. SOURCE PRECEDENCE
==================================================

Formalize evidence precedence.

CURRENT STRUCTURED OPERATIONAL STATE
wins for current factual state.

Example:
Manufacturing Portal says LOT-B-204 = HOLD.

An old report saying:
"lot expected to release"

does not override HOLD.

CURRENT APPROVED PROCEDURE/POLICY
governs procedural interpretation.

HISTORICAL DOCUMENTS
can inform investigation but must be labeled historical.

UNAPPROVED / SUPERSEDED DOCUMENTS
must not become normative evidence unless explicitly requested for comparison.

==================================================
7. SPECIALIST OUTPUTS
==================================================

Extend specialist findings where necessary to include:

knowledge_evidence:
- document ID
- version
- chunk/section
- applicability
- approval/current state
- exact-source verification reference

Keep outputs concise.

Do not dump full retrieved passages into final coordinator responses.

The user-facing output should summarize the relevant rule and cite the source.

==================================================
8. CR-017 INTEGRATION
==================================================

Use RAG naturally in CR-017.

Example uses:
- retrieve approved long-context validation procedure
- retrieve relevant acceptance criteria section
- retrieve engineering review policy

Expected:
RAG strengthens the evidence-gap/validation-plan explanation.

Do not change the business conclusion merely because retrieval exists unless
new approved knowledge genuinely changes applicability.

Preserve:
- engineering approval boundary
- scheduling ≠ validation pass
- customer acceptance separate

==================================================
9. CR-019 INTEGRATION
==================================================

Use RAG to support why the request qualifies as a standard change.

Possible retrieval:
- standard change procedure
- approved routing policy

However, touchless eligibility remains deterministic host policy.

The agent does NOT gain authority because a retrieved paragraph says the route is
standard.

Desired story:

RAG provides institutional knowledge explaining the rule.

Host policy authorizes the bounded handoff.

==================================================
10. QE-004 INTEGRATION
==================================================

This is an especially strong RAG demo.

Use Manufacturing/Quality retrieval to find:
- quality hold/disposition SOP
- investigation procedure
- historical test-site concentration guidance

Expected answer should distinguish:

Current source fact:
LOT-B-204 is held.

Retrieved procedure:
held material remains ineligible until required disposition/review.

Historical guidance:
site concentration warrants investigation and does not establish root cause.

Agent conclusion:
do not release held material;
root cause remains unresolved.

Do not let historical RAG content establish current disposition.

==================================================
11. DR-009 INTEGRATION
==================================================

Keep RAG limited.

Operational quantity/date calculation must continue using structured tools.

Possible useful RAG:
- commitment policy
- customer-specific readiness guidance
- program delivery policy

Do not use semantic retrieval to compute:
600 / 800 / 200.

That remains deterministic.

==================================================
12. KNOWLEDGE & EVIDENCE UI
==================================================

Make RAG usage visible and intuitive.

For each document:
- Indexed
- Version
- Status
- Used by recent runs where applicable

Add a:
Used in agent runs

view or filter.

For a run, show:
Retrieved knowledge

with:
- document
- section
- version
- specialist
- why relevant
- open source

Do not surface raw embedding values.

==================================================
13. CASE / RUN UI
==================================================

On case evidence views, distinguish:

STRUCTURED SOURCE EVIDENCE
Engineering Hub / Validation Lab / Manufacturing / ERP / Planner

KNOWLEDGE EVIDENCE
Procedure / SOP / spec / report

Keep them visually related but semantically distinct.

Examples:

Operational evidence
LOT-B-204 · HOLD

Knowledge evidence
Quality SOP QP-08 v7 · Hold & disposition

This makes the hybrid architecture visible in the demo.

==================================================
14. OPERATIONS
==================================================

Add RAG retrieval visibility to Operations.

For each retrieval event show:
- specialist
- retrieval profile
- query
- docs/passages returned
- version/status
- retrieval latency
- exact-source verification state

Do not expose hidden reasoning.

Do not treat retrieval score as model confidence.

==================================================
15. STRATOS CONCIERGE
==================================================

Concierge may use the same shared Knowledge Retrieval service for explanatory
questions.

Examples:
"What does the quality SOP say about held material?"
"Why was CR-019 eligible for standard routing?"

Concierge retrieval must remain persona/scope filtered.

Concierge cannot use RAG to bypass a workflow or approval.

For current operational state, Concierge should still call/read structured current
state rather than answer solely from documents.

==================================================
16. EVALS — RETRIEVAL QUALITY
==================================================

Extend the eval framework.

At minimum test:

A. Correct approved procedure retrieved.

B. Wrong-product document not used.

C. Superseded procedure not used as current normative source.

D. Historical report labeled historical.

E. Retrieval passage cites correct document/version.

F. Exact authoritative document verification performed where required.

G. High semantic score does not override applicability mismatch.

H. Empty retrieval remains unknown.

I. Agent does not fabricate policy when retrieval returns nothing.

J. Current structured HOLD overrides narrative expected-release text.

K. Prompt injection in retrieved doc does not override policy.

L. Restricted persona cannot receive restricted passage.

M. Coordinator does not independently broaden retrieval scope.

N. Agent does not semantic-search for simple operational quantities when an exact
structured tool exists.

O. Retrieval failure does not cause false business conclusion.

==================================================
17. BUSINESS-CONCLUSION REGRESSION
==================================================

Run current canonical workflow evals before/after RAG integration.

We want to identify whether RAG changed conclusions.

Explicitly report changes for:

- CR-017
- CR-019
- QE-004
- DR-009

For each material change classify:

EXPECTED
approved knowledge legitimately changed available evidence

UNEXPECTED
retrieval noise or prompt regression

Do not silently accept changed conclusions.

==================================================
18. LIVE RETRIEVAL SMOKE
==================================================

Provide an optional manual paid/live smoke.

Do not run automatically.

Recommended cases:

CR-017
retrieve validation procedure and cite relevant section

QE-004
retrieve hold/disposition SOP and historical investigation guidance

Concierge
"What does the approved quality procedure say about this held lot?"

Record:
- provider
- documents retrieved
- versions
- specialist
- latency
- token usage if applicable
- resulting conclusion

==================================================
19. PERFORMANCE
==================================================

Avoid excessive retrieval calls.

Cache/index appropriately using existing architecture.

Do not cache current operational business state inside the RAG system.

Measure retrieval latency where available.

Do not re-embed unchanged documents per workflow run.

==================================================
20. SECURITY
==================================================

Preserve:
- persona-aware document access
- program scope
- no arbitrary file access
- prompt-injection resistance
- no secrets in logs
- no unrestricted corpus dump through Concierge

Documents remain evidence, not instructions.

==================================================
21. TESTING
==================================================

Run:
- knowledge retrieval tests
- source/backend tests
- coordinator
- MCP
- current offline evals + RAG evals
- persona/RBAC
- Concierge
- Operations
- browser E2E
- typecheck/build

No paid model calls by default.

==================================================
22. DOCUMENTATION
==================================================

Update architecture docs with the final hybrid retrieval story:

Structured operational systems
→ MCP/API tools

Unstructured institutional knowledge
→ Shared RAG service

Agent retrieval profiles
→ domain-specific knowledge scope

Exact version verification
→ provenance/applicability

Host policy + humans
→ authority

Document:
- specialist mappings
- retrieval rules
- source precedence
- eval coverage
- Knowledge UI
- live setup
- limitations

==================================================
23. FINAL REPORT
==================================================

Report:

1. Agents integrated
2. Retrieval profiles used
3. Workflow-specific RAG usage
4. Structured-vs-RAG decision rules
5. Exact source verification
6. UI changes
7. Operations changes
8. Eval cases added
9. Business conclusions before vs after
10. Tests/results
11. Optional live commands
12. Known limitations

Stop after this RAG integration.

Do NOT implement the QE-011 autonomous background trigger in this prompt.