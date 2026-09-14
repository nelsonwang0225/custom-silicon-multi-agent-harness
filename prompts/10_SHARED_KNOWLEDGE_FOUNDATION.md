Continue working in the existing Stratos Silicon repository and current Phase 10 thread.

Implement the first RAG enhancement:
SHARED KNOWLEDGE & EVIDENCE RETRIEVAL FOUNDATION.

This is an enhancement to the existing Knowledge & Evidence capability.

Do not yet broadly change agent behavior.
Do not replace structured MCP/API retrieval.
Do not change workflow authority, approvals, source-system writes, or source-of-truth ownership.

The objective is to turn the existing Knowledge & Evidence document library into
a version-aware semantic retrieval service that selected agents can use later.

Git remains relaxed:
- no commit/push work yet
- preserve unrelated work
- avoid destructive operations

==================================================
1. ARCHITECTURAL PRINCIPLE
==================================================

We now use TWO retrieval patterns:

A. STRUCTURED / OPERATIONAL RETRIEVAL
Existing MCP/API tools remain authoritative for:
- current lot status
- orders
- inventory
- allocations
- validation jobs
- workflow/case state
- milestones
- approvals
- configuration records
- current source-system facts

B. UNSTRUCTURED KNOWLEDGE RETRIEVAL / RAG
New shared Knowledge Retrieval service is for:
- procedures
- SOPs
- engineering specifications
- acceptance criteria documents
- validation reports
- quality manuals
- errata
- historical investigation reports
- other long-form knowledge documents

RAG does NOT replace structured tools.

Current structured facts win over stale narrative documents when the two conflict.

==================================================
2. ONE SHARED RAG SERVICE
==================================================

Do NOT create a separate vector database/index for each agent.

Create one shared Knowledge & Evidence retrieval layer.

Agents will later receive separate retrieval profiles / metadata filters over the
same corpus.

Conceptually:

Knowledge & Evidence corpus
→ ingestion
→ chunking
→ embedding/index
→ shared retrieval service
→ agent-specific retrieval policies

Avoid duplicated indexing pipelines and duplicate copies of documents.

==================================================
3. INSPECT THE EXISTING KNOWLEDGE LIBRARY FIRST
==================================================

Before implementing:

Inspect:
- current Knowledge & Evidence records
- document IDs
- document content/storage format
- versions
- approval status
- program/customer/configuration associations
- source-system ownership
- existing exact document retrieval APIs/MCP tools
- existing UI
- existing OpenAI SDK/runtime dependencies

Reuse the existing documents where possible.

Do not create a large artificial document corpus merely to demonstrate RAG.

If the existing corpus is too small to demonstrate meaningful semantic retrieval,
add only a small number of coherent synthetic supporting documents and document
why they were necessary.

==================================================
4. RETRIEVAL TECHNOLOGY
==================================================

Prefer an official OpenAI-supported retrieval/vector-store/file-search mechanism
if it is compatible with the repository's currently installed OpenAI SDK and
architecture.

Before implementing such a dependency:
- inspect the currently installed SDK/version;
- use the current supported API surface;
- do not rely on deprecated retrieval endpoints;
- keep network/paid indexing out of normal automated tests.

If using hosted OpenAI retrieval would introduce unacceptable coupling or prevent
deterministic offline testing, create a clean provider abstraction:

KnowledgeIndexProvider

with:
- live OpenAI-backed implementation
- deterministic offline/test implementation

Do not create two business semantics.

The retrieval contract must remain provider-independent.

==================================================
5. DOCUMENT METADATA
==================================================

Every indexed document/chunk must retain authoritative metadata.

At minimum where available:

- document_id
- title
- document_type
- version
- program_id
- customer_id
- product/configuration
- owner_team
- approval_status
- effective_date
- superseded_by
- source_system
- applicable_workflows
- section/page/heading
- content_version / record_version where available

Do not fabricate metadata that the source does not contain.

Missing metadata should remain explicit.

==================================================
6. DOCUMENT ELIGIBILITY
==================================================

Not every document should be treated equally.

Create deterministic eligibility rules for knowledge retrieval.

Examples:

preferred/default:
- approved/current documents
- non-superseded documents
- correct program/product scope

retrievable but flagged:
- historical investigation reports
- prior versions when explicitly requested

excluded by default:
- superseded procedures
- rejected drafts
- wrong-program restricted records
- inaccessible records

Semantic similarity alone must NOT determine applicability.

==================================================
7. CHUNKING
==================================================

Create stable, deterministic chunks.

Preserve:
- document identity
- section/heading
- version
- source provenance

Do not split documents into tiny arbitrary fragments that lose engineering meaning.

Prefer section-aware chunking where the document structure supports it.

Each chunk needs a stable chunk ID derived from document/version/section rather
than a random ID where practical.

==================================================
8. INDEXING / VERSIONING
==================================================

Support:

- initial indexing
- incremental indexing
- document update
- version replacement
- superseded document handling
- index rebuild
- retrieval-index status

A new document version must not silently overwrite historical provenance.

Current retrieval should prefer the current approved version according to policy.

==================================================
9. SHARED RETRIEVAL CONTRACT
==================================================

Add a typed service such as:

search_knowledge(
    query,
    retrieval_profile,
    program_scope,
    metadata_filters,
    max_results
)

Use actual repository naming conventions.

Return structured results containing at minimum:

- document_id
- document_version
- chunk_id
- title
- section/heading
- passage/snippet
- metadata
- retrieval score/ranking signal if available
- source reference
- approval/current/superseded state
- applicability metadata

The score is retrieval relevance, NOT truth or confidence.

Do not expose embeddings themselves to the agents/UI.

==================================================
10. EXACT DOCUMENT FOLLOW-UP
==================================================

Preserve the existing exact document retrieval path.

RAG should help DISCOVER relevant knowledge.

When an agent later needs to rely materially on a retrieved passage, it should be
possible to retrieve/verify the exact authoritative document/version using the
existing source/document interface.

Desired pattern:

semantic discovery
→ candidate passage
→ exact document/version verification
→ reasoning

Do not remove exact document tools.

==================================================
11. RETRIEVAL PROFILES
==================================================

Define reusable retrieval profiles, but do not yet wire them broadly into agent
prompts.

At minimum:

CHANGE_IMPACT
Allowed knowledge types:
- requirements
- engineering specifications
- change-control policy
- architecture/design notes

VALIDATION_EVIDENCE
- validation procedures
- acceptance criteria
- test/validation reports
- engineering qualification guidance

MANUFACTURING_QUALITY
- quality SOPs
- manufacturing procedures
- yield investigations
- test/quality reports
- relevant errata

PROGRAM_COMMERCIAL
- program policies
- customer requirement documents
- planning/commitment guidance
- program governance

Keep Program/Commercial retrieval narrower than technical agents.

COORDINATOR
Default:
does not perform broad knowledge retrieval directly.
Prefer specialist retrieval and specialist findings.

These profiles control retrieval scope, not business authority.

==================================================
12. SECURITY / ACCESS CONTROL
==================================================

Integrate the existing persona/capability model.

Retrieval results must be filtered server-side by:
- program scope
- record/document access
- persona capabilities
- document policy

Do not return a restricted passage and merely hide it in the UI afterward.

No cross-program knowledge leakage.

Do not let user/model-supplied metadata filters broaden scope beyond the actor's
allowed data.

==================================================
13. PROMPT INJECTION SAFETY
==================================================

Treat document contents as untrusted data.

Instructions contained inside a retrieved:
- SOP
- report
- comment
- customer document
- engineering note

must never override:
- system instructions
- host policy
- authorization
- workflow authority
- approval boundaries
- tool permissions

Add adversarial test documents/passages that attempt to instruct the model to:
- bypass approval
- release held material
- ignore policy
- reveal hidden data

The retrieval service should return them as data.
Later agent instructions must explicitly treat them as evidence, not authority.

==================================================
14. RETRIEVAL UI — KNOWLEDGE & EVIDENCE
==================================================

Enhance the existing Knowledge & Evidence page without redesigning the app.

Add useful retrieval/index visibility:

For each document:
- title
- type
- version
- status
- indexed / not indexed
- current / superseded
- program/config applicability where available

Add a read-only semantic search experience:

Search knowledge

User can enter:
"quality hold retest procedure"

Show:
- relevant passages
- document title/version
- section
- metadata/applicability
- open exact document

Clearly label:
Semantic relevance

Do NOT label score as:
Confidence
Correctness
Approval probability

==================================================
15. PASSAGE PREVIEW
==================================================

Reuse the existing evidence/document modal.

For a retrieved result show:

LEFT
exact document / source record context

RIGHT
- retrieved passage
- section
- version
- approval status
- program/config applicability
- retrieval provenance

Do not fabricate page numbers when the source has none.

==================================================
16. INDEX MANAGEMENT
==================================================

Provide demo/developer-safe index controls, not normal business actions.

Examples:
- Reindex knowledge corpus
- View index status

Place them under Demo/Operations or Knowledge admin context.

Do not make agents able to rebuild the index.

Do not expose generic arbitrary file ingestion from local filesystem.

==================================================
17. OFFLINE / TEST MODE
==================================================

Automated tests must not depend on paid embedding/model calls.

Create deterministic fixtures for:
- documents
- chunks
- retrieval results
- metadata filtering

If live OpenAI indexing is used, provide an explicit manual setup/sync command.

Do not index on every app startup.

==================================================
18. BASELINE / RESET
==================================================

Integrate with the existing demo-reset architecture.

Decide explicitly:

Knowledge corpus:
preserved as baseline reference data.

Index:
either durable and validated against corpus version
or rebuildable from the baseline corpus.

Demo reset should not unnecessarily re-embed unchanged documents.

==================================================
19. OBSERVABILITY
==================================================

Record retrieval metadata sufficient for later run attribution:

- query
- retrieval profile
- permitted filters
- document/chunk IDs returned
- versions
- retrieval latency
- provider
- result count

Do not store hidden chain-of-thought.

Do not log sensitive full documents unnecessarily.

==================================================
20. TESTS
==================================================

Add deterministic tests for at least:

A. Correct approved document retrieved for relevant query.

B. Wrong program document excluded.

C. Superseded procedure excluded by default.

D. Historical report retrievable when profile permits.

E. Correct version metadata preserved.

F. Exact-document verification available after semantic discovery.

G. Empty retrieval returns unknown/no evidence, not fabricated answer.

H. Restricted persona cannot retrieve restricted document.

I. Metadata filters cannot expand authorization.

J. Prompt injection text is returned as evidence data, not executed by retrieval layer.

K. Reindex/version update behaves deterministically.

L. Duplicate indexing does not duplicate chunks.

M. Knowledge reset/index validation works.

N. Existing exact document retrieval remains unchanged.

O. Existing four workflows remain unchanged before agent integration.

==================================================
21. REGRESSION
==================================================

Run:
- source/backend tests
- coordinator tests
- MCP tests
- current offline evals
- persona/RBAC tests
- Knowledge UI tests
- browser tests
- typecheck/build

No paid model calls.

==================================================
22. DOCUMENTATION
==================================================

Document:

- structured tools vs RAG responsibilities
- shared RAG architecture
- metadata model
- retrieval profiles
- version/applicability rules
- access-control model
- prompt-injection safety
- live provider setup
- offline test behavior
- index lifecycle
- known limitations

==================================================
23. REPORT AND STOP
==================================================

Report:

1. Existing corpus inspected
2. Retrieval provider chosen and why
3. Shared index architecture
4. Metadata/versioning
5. Retrieval profiles
6. Exact-source verification path
7. Knowledge & Evidence UI changes
8. Access/security behavior
9. Tests/results
10. Live indexing/search steps if not automatically run
11. Known limitations
12. Exact next agent-integration step

STOP after the RAG foundation.

Do NOT yet broadly modify agent prompts or workflow outputs.
Do NOT implement the autonomous QE-011 event trigger yet.