Continue working in the existing Stratos Silicon repository after the completed
RAG specialist-integration work.

Implement a focused QE-004 KNOWLEDGE CORPUS COMPLETION.

This is not a RAG architecture change.

Do not:
- modify workflow authority;
- modify agent permissions;
- change source-system state;
- change QE-004's canonical business facts;
- create another vector store;
- add new agents;
- change approval boundaries;
- implement QE-011 yet.

The objective is to add a small realistic Quality/Manufacturing knowledge corpus
so QE-004 can demonstrate useful RAG retrieval instead of truthfully returning
no knowledge evidence.

==================================================
1. ADD THREE COHERENT KNOWLEDGE DOCUMENTS
==================================================

Add three synthetic but realistic documents to the existing authoritative
Knowledge & Evidence corpus.

Use existing document schemas, storage, versioning, source ownership and
indexing infrastructure.

Do not add these only as test fixtures or UI-only records.

A. QUALITY HOLD & DISPOSITION SOP

Suggested title:
Quality Hold & Disposition SOP

Suggested stable ID:
DOC-QA-HOLD-01
or repository-conforming equivalent.

Business role:
Approved governing procedure / SOP

Owner:
Quality / Manufacturing

Status:
Approved

Current version:
v1 unless repository conventions require another value.

Program/product applicability:
PRG-A17 and the relevant Helios accelerator family/configuration where appropriate.

Document should establish, in realistic plain language:

- Material on quality hold is not eligible for customer allocation, shipment,
  or release until the required disposition process is complete.
- First-pass passing units inside a held lot do not become released inventory
  merely because they passed the initial test.
- Standard investigation activities may occur while the lot remains held.
- Final release/reject/rework/retest disposition remains owned by the authorized
  quality role according to policy.
- Agents or automated systems do not independently release held material.

Do not add arbitrary manufacturing standards or claims unsupported by our
fictional scenario.

B. FINAL-TEST EXCURSION INVESTIGATION PROCEDURE

Suggested title:
Final-Test Excursion Investigation Procedure

Suggested stable ID:
DOC-QA-EXCURSION-01

Business role:
Approved investigation procedure

Status:
Approved

Document should establish:

- Confirm the affected lot, product/configuration and test stage.
- Verify the result denominator and first-pass statistics.
- Confirm test-program revision before comparing to a baseline.
- Check whether site/equipment/test conditions are comparable.
- Scope related lots only when evidence supports doing so.
- Failure concentration at a particular site/equipment is an investigation
  signal, not automatically a confirmed root cause.
- Non-standard retest/rework or disposition requires the appropriate human
  authority.
- Investigation should preserve traceability to lot, test program and evidence.

C. HISTORICAL TEST-SITE CONCENTRATION INVESTIGATION

Suggested title:
Historical Investigation — Test-Site Concentration

Suggested stable ID:
DOC-QA-HIST-01

Business role:
Historical investigation report

Status:
Historical / closed / non-normative according to current repository taxonomy.

Document should describe a prior fictional case where:

- failures were concentrated at one test site;
- the team investigated tester/equipment, test program and material;
- the concentration itself did not establish root cause;
- additional evidence was required before corrective action;
- the historical result must not be treated as governing current procedure.

The document should explicitly distinguish:
historical precedent
from
current approved policy.

==================================================
2. METADATA / RETRIEVAL CONFIGURATION
==================================================

Populate real metadata using the existing RAG model.

At minimum:
- document_id
- title
- document_type
- owner_team
- approval/lifecycle status
- version
- program_id where applicable
- product/configuration applicability
- effective date if supported
- superseded status
- applicable workflow:
  yield_exception_recovery
- permitted retrieval profile:
  MANUFACTURING_QUALITY

Do not make the historical document appear current/approved.

Ensure the approved SOP/procedure are eligible as normative knowledge.

==================================================
3. INDEX THROUGH THE EXISTING RAG PIPELINE
==================================================

Use the existing shared Knowledge Retrieval service and index lifecycle.

Do not create:
- another vector store
- agent-specific index
- a parallel retrieval implementation

Ensure:
- documents are chunked deterministically;
- metadata is preserved;
- current approved docs are indexed;
- historical document is retrievable under the Manufacturing/Quality profile;
- duplicate reindexing does not duplicate chunks.

If live OpenAI vector-store indexing requires an explicit manual sync, provide
the command but do not run paid/network indexing automatically unless the
existing process is already authorized and free of paid model calls.

Offline tests should use the deterministic retrieval provider.

==================================================
4. QE-004 RETRIEVAL EXPECTATIONS
==================================================

Update/add deterministic retrieval tests so the Manufacturing/Quality specialist
can retrieve these documents for QE-004.

Expected queries/results:

Query:
"What policy governs held material and shipment eligibility?"

Expected:
Quality Hold & Disposition SOP

Query:
"How should a final-test excursion be investigated?"

Expected:
Final-Test Excursion Investigation Procedure

Query:
"What does prior experience say about failures concentrated at one test site?"

Expected:
Historical Test-Site Concentration Investigation

The historical report must be identified as historical/non-normative.

==================================================
5. QE-004 REASONING EXPECTATION
==================================================

Do not change the QE-004 operational facts.

Manufacturing Portal remains authoritative for:
- LOT-B-204
- lot status = HOLD
- lot quantity
- first-pass results
- current quality state

RAG adds institutional knowledge.

Expected combined conclusion:

- LOT-B-204 remains excluded from eligible supply because the authoritative
  source says HOLD and the approved SOP confirms held material cannot be released
  before disposition.
- 200 first-pass passing units do not become shippable while the lot remains held.
- Test-site concentration warrants investigation.
- Historical site-concentration precedent does NOT establish current root cause.
- Root cause remains unresolved unless current authoritative evidence establishes it.
- Human quality authority remains required for disposition.

The business conclusion should remain consistent with the existing QE-004 flow.

==================================================
6. SOURCE PRECEDENCE TESTS
==================================================

Add explicit tests proving:

A. Current Manufacturing Portal HOLD state outranks historical narrative.

B. Approved SOP is normative procedural knowledge.

C. Historical investigation is supporting context only.

D. Historical result cannot release the current lot.

E. Historical result cannot establish QE-004 root cause.

F. Requested/draft knowledge cannot override approved procedure.

G. Superseded procedures remain excluded from current normative retrieval.

==================================================
7. UI
==================================================

Update Knowledge & Evidence using the existing design.

The new documents should appear with clear roles such as:

Quality Hold & Disposition SOP
Approved

Final-Test Excursion Investigation Procedure
Approved

Historical Investigation — Test-Site Concentration
Historical

Preserve:
Indexed
Current source version
or appropriate retrieval/index state.

Do not label the historical document Approved.

Where recent-run provenance is available, QE-004 should be able to show these
under "Knowledge evidence" separately from Manufacturing source evidence.

==================================================
8. CASE / OPERATIONS PROVENANCE
==================================================

For QE-004, where the current RAG integration supports it, display/retrieve:

Structured operational evidence:
LOT-B-204 · HOLD

Knowledge evidence:
Quality Hold & Disposition SOP
Final-Test Excursion Investigation Procedure
Historical Test-Site Concentration Investigation

Show:
- document ID/version
- lifecycle/approval status
- relevant section
- retrieval profile
- exact-source verification

Do not show vector embeddings.

==================================================
9. CONCIERGE
==================================================

Ensure the existing connected Concierge can answer grounded questions such as:

"What does the approved quality procedure say about the held lot?"

Expected:
- retrieve approved Quality Hold SOP;
- cite document/version;
- combine with current LOT-B-204 HOLD state;
- explain that held material remains unavailable;
- do not grant disposition authority.

Question:
"Did the test site cause QE-004?"

Expected:
- use historical document only as context;
- explain that concentration is not sufficient evidence of root cause;
- do not assert causality.

==================================================
10. EVALS
==================================================

Add focused RAG eval cases covering:

1. approved hold SOP retrieved correctly
2. approved excursion procedure retrieved correctly
3. historical investigation retrieved and labeled historical
4. current HOLD + SOP produces correct ineligible-supply conclusion
5. historical site pattern does not become root cause
6. historical doc does not override current source state
7. wrong program/config doc excluded
8. superseded doc excluded
9. missing retrieval remains unknown
10. prompt injection in a quality document cannot override policy
11. exact-source verification succeeds
12. QE-004 canonical business conclusion remains unchanged

Preserve all existing RAG gates and workflow evals.

==================================================
11. REGRESSION
==================================================

Run:
- knowledge/RAG tests
- source tests
- coordinator tests
- MCP tests
- QE-004 tests
- all offline evals
- Concierge tests
- Knowledge UI/browser tests
- Operations provenance tests
- typecheck/build

No paid/live model calls by default.

Report exact counts and any skips.

==================================================
12. OPTIONAL LIVE RAG CHECK
==================================================

Provide, but do not automatically run, one small live retrieval smoke for QE-004:

A. Retrieve approved hold/disposition SOP.
B. Retrieve historical site-concentration report.
C. Confirm exact-source verification.
D. Confirm live Manufacturing HOLD state remains authoritative.
E. Confirm final conclusion does not claim root cause or release authority.

Provide exact command/path.

==================================================
13. DOCUMENTATION
==================================================

Update the RAG handoff with:

- new Quality corpus
- document roles/status
- metadata
- retrieval behavior
- source precedence
- QE-004 hybrid evidence example
- eval coverage
- optional live verification command

==================================================
14. STOPPING POINT
==================================================

Stop after this focused QE-004 corpus enhancement.

Do not implement:
- QE-011 event trigger
- new workflow logic
- approval changes
- new vector store
- Git packaging

Report:
- documents added
- metadata
- indexing status
- retrieval results
- QE-004 before/after conclusion
- tests/evals
- live check instructions
- known limitations