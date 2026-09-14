# Shared Knowledge & Evidence retrieval foundation

Implemented from [the approved request](../prompts/10_SHARED_KNOWLEDGE_FOUNDATION.md). This is a discovery foundation, with no agent prompt, workflow-output, execution, approval, source-write or MCP permission changes. No QE-011 trigger.

## Corpus inspected

The connected A17 library exposes nine Engineering-owned controlled business documents through `get_documents` and `get_document`: DOC-BASELINE-01 (requirement v1), DOC-CONFIG-01 (configuration v1), DOC-PLAYBOOK-01 (playbook v1), DOC-POLICY-01 (policy v1), DOC-PROC-01 (procedure v2), DOC-REQUEST-01 (customer request v2), DOC-STD-POLICY-01 (standard routing policy v1), DOC-STD-PROC-01 (procedure v1), DOC-STD-REQUEST-019 (standard request v1). Seven are approved; two requested records are excluded from default discovery. Base-only source test installations have the six original documents.

Content is controlled Markdown or JSON text, served from persisted source records. All documents carry ID, type, document version, content version/hash, customer/program, owning system, status and updated timestamp. Titles are taken from a supplied title or the first Markdown heading, with a labeled ID fallback. Product/configuration, owner team, effective date, superseded-by, applicable workflows and record version remain null where structured source metadata does not provide them. Configuration identifiers mentioned in prose are retained in passages, not interpreted as an authoritative applicability field.

No production corpus documents were added. Existing material suffices for initial procedure/requirements/policy discovery. Manufacturing/quality and historical-report profiles currently have little or no eligible content; empty results are truthful. Adversarial and versioned documents exist only in isolated tests.

## Two retrieval responsibilities

Structured APIs/MCP remain authoritative for current configuration, lots, holds, orders, allocations, validation jobs, case state, milestones and approvals. Semantic discovery does not change those facts, authorize actions, or adjudicate conflicts. Current structured facts and host policy win over stale prose.

Discovery → candidate passage with immutable identity → exact source/version verification → later specialist reasoning. No search or indexing tools were added to agent/MCP registries in this slice.

## Shared architecture and providers

`src/program_coordinator/knowledge/` contains the provider-independent contract, section chunker, source adapter, eligibility policy, shared SQLite manifest/archive and retrieval audit. One `metadata/knowledge/index.sqlite3` is shared across all profiles. No per-agent index or separate ingestion pipeline. It stores immutable version/content identities and canonical chunks plus per-provider indexing receipts. The source corpus is always fetched through the existing scoped HTTP client; no fixture or source-table access exists in runtime ingestion.

`KnowledgeIndexProvider` has two implementations:

- `OfflineIndexProvider`: deterministic term/synonym cosine ranking, explicitly labeled offline in the UI. It is a network-free test/demo implementation, not a claim of neural semantic search quality.
- `OpenAIIndexProvider`: official vector-store file indexing and `vector_stores.search`, compatible with the installed coordinator OpenAI SDK **3.13.0** (Agents SDK **0.22.2**). No dependency upgrade. One hosted vector store with immutable canonical chunk files and chunk-ID attributes. Hosted ranking returns IDs/scores; the service returns canonical passages/metadata, never trusts remote snippets as authority, and filters both before provider search and after results. No Responses generation or deprecated Assistants retrieval integration.

Official references inspected: [Retrieval guide](https://developers.openai.com/api/docs/guides/retrieval), [Python vector-store search](https://developers.openai.com/api/reference/python/resources/vector_stores/methods/search). SDK signatures were also inspected locally. No live provider request was made; provider behavior is verified with deterministic client doubles.

## Metadata, chunking and eligibility

Chunks retain their document metadata, section heading, ordinal and passage. No fabricated page numbers. Heading-aware sections split at paragraphs/sentences around 450 words; oversized individual sentences have a bounded word fallback. Stable chunk IDs hash document ID, document version, content version/hash, section and ordinal. Changes cannot silently reuse the same document/content version with a different body hash.

Default discovery requires approved, non-superseded records in the actor's source scope and the selected profile. Drafts, rejected documents and requests are excluded. Explicit filters can include historical reports and prior/superseded versions; results are flagged. Configuration filters fail closed when no structured configuration association exists. Effective dates, when supplied, must have arrived at retrieval time (UTC). Current-source metadata changes invalidate unsynced chunks, even if text remains the same.

Profiles:

| Profile | Permitted knowledge |
|---|---|
| CHANGE_IMPACT | Requirements, specifications, configuration/design/architecture notes, change policy, playbooks, customer requests (subject to approval eligibility) |
| VALIDATION_EVIDENCE | Procedures, acceptance criteria, test/validation reports, qualification guidance, requirements |
| MANUFACTURING_QUALITY | Quality SOPs, manufacturing procedures, yield/historical investigations, quality/test reports, errata |
| PROGRAM_COMMERCIAL | Program/customer policies and requirements, planning/commitment guidance, governance; excludes general technical procedures and reports |
| COORDINATOR | Broad retrieval denied; use specialist findings in the later integration |

Profiles narrow retrieval; they grant no business authority. Exact approved type sets are in `knowledge/models.py`.

## Index lifecycle, reset and failures

Index construction never runs at startup. Explicit sync downloads the allowlisted corpus and compares deterministic identities. Duplicate sync does not duplicate chunks/uploads. Incremental changes retain old versions; rebuild regenerates the local chunk table from the same archive without re-embedding unchanged chunks. Provider receipts persist uploaded file IDs and attachment state to recover interrupted indexing. The committed generation is published only after all chunks index successfully and a second source read agrees. Failure leaves the previous generation available subject to current-source eligibility.

Source removals/access changes are checked before ranking; provider response IDs are checked against that allowlist. A second source read after ranking rejects a concurrent source change. Source failures fail closed—no cached-source authority is substituted. Search on an empty index returns no evidence with `not_indexed`, not an answer.

Demo reset preserves reference documents and the separate index. Status validates its corpus digest on read; unchanged reference documents need no rebuild or paid re-embedding. A baseline rollback can retrieve a retained matching version; changed corpora report out-of-date until explicit sync. A real isolated host reset regression verifies retained receipts and current index status.

There is an unavoidable remote-upload interruption window before a returned file ID can be durably saved. Normal retries with saved IDs do not re-upload; an externally orphaned upload would need provider-side maintenance. Historical remote files are retained for provenance, so storage costs grow with indexed revisions.

## Access, exact verification and prompt injection

Host routes reuse `resolve_actor`, `require_surface`, the current capability projection and installed CUST-FML01/PRG-A17 scope. Reader, Engineer and Program operator can use their existing Knowledge surface; Program Owner cannot. Only the selected Program operator can invoke local index management. Exact source APIs preserve their original source-system authority.

Document access restrictions, if provided by the source, intersect the existing persona and program scope. User/model filters never expand this intersection. Current-source access is rechecked for archived chunks. Missing source ACL metadata means the document retains existing source program access; no new secret classification is invented. The source client itself remains scope restricted.

Passage text is returned as `content_trust: untrusted_evidence`. HTML/scripts are not executed; the UI renders text. Test-only passages say to bypass approval, release holds, ignore policy and reveal hidden records. They remain text, cannot call tools, and cannot modify service policy. Later agent integration must explicitly preserve this evidence-vs-instruction boundary.

`GET /control-api/knowledge/verify/{chunk_id}` retrieves current authoritative content through the existing exact source API and compares version, content version/hash and metadata. A mismatch returns `verified=false` without substituting a different document. The source API currently exposes the current version only: historical discovery is supported, but a superseded version cannot be claimed independently verified when the source no longer serves it. The UI states this limitation instead of treating an index archive as source authority.

## UI and local API

Knowledge & Evidence now shows source title/type/version/status, current/superseded state, indexed status and structured applicability. Search supports profile selection and explicit history/prior-version inclusion. Results display passage, heading, source metadata and **Semantic relevance** (ranking, never confidence/correctness). Empty and failed searches are explicit.

The existing Drawer modal is reused: exact verified document/context on the left, retrieved passage/provenance on the right; narrow screens stack them. Existing exact document library follow-up remains available. Source failures and identity/reset changes clear invalid result/inspector state. The operator-only Knowledge index administration disclosure requires a concrete reindex confirmation. Agents cannot rebuild the index.

Routes:

- `GET /control-api/knowledge`: scoped library/index status
- `POST /control-api/knowledge/search`: typed read-only discovery (query is POSTed rather than put in a URL)
- `GET /control-api/knowledge/verify/{chunk_id}`: exact current source verification
- `POST /control-api/knowledge/reindex`: explicitly confirmed offline index management, selected operator only

Live hosted reindex is CLI-only. Hosted search is enabled only by an explicit host startup flag. All normal automated runs remain offline.

Retrieval audit records query, actor, profile, permitted scope/filters, returned document/chunk IDs and versions, provider, latency and result count. It records no full document or hidden reasoning. Local storage contains canonical business text and queries; these should remain within the trusted demo host. Important authorization denials use existing host logs with fixed safe codes.

## Explicit commands

Run from the repository root. These commands ingest only the existing source HTTP corpus.

```sh
# No paid calls; use the same metadata directory as the selected host.
PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.knowledge sync \
  --source-url http://127.0.0.1:18322 \
  --metadata-dir .cache/phase09-3/phase10-2-preview/metadata

# Substitute status or rebuild for sync as needed.
# Hosted indexing: explicitly incurs provider indexing/storage usage.
PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.knowledge sync \
  --source-url http://127.0.0.1:18322 \
  --metadata-dir .cache/phase09-3/phase10-2-preview/metadata \
  --provider openai --allow-paid

# Hosted discovery after indexing (no response-generation call).
PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.knowledge search \
  --source-url http://127.0.0.1:18322 \
  --metadata-dir .cache/phase09-3/phase10-2-preview/metadata \
  --provider openai --allow-paid --profile VALIDATION_EVIDENCE \
  --query 'supplemental validation approval procedure'
```

Hosted mode uses the existing authorized `.env.local` through the existing secure loader. No key is printed. To use the hosted index from a normal host, explicitly add `--allow-paid-knowledge-search` to `program_coordinator.control_host` with the same metadata directory. That flag does not index on startup. The default host and isolated test server use deterministic offline retrieval.

Local review preview: [Knowledge & Evidence](http://127.0.0.1:5203/control/knowledge). Its existing deterministic review host was restarted with the same source/metadata directories after confirming zero active runs. No working business state was reset. Its nine-document offline index was explicitly synced, and a real HTTP search/exact-verification smoke passed.

## Next integration boundary

Next explicitly authorized slice: add a bounded specialist knowledge-discovery tool over this service, assign the four profiles, require exact-source verification before material reliance, and include document version/provenance in typed findings. Preserve structured MCP reads and all exact approval/execution boundaries. Coordinator should consume specialist findings, not broad corpus retrieval. No such agent/tool/prompt integration is included here.
