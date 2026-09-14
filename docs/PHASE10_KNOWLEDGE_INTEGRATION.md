# Specialist knowledge integration

Implemented from [the approved integration request](../prompts/10_SPECIALIST_KNOWLEDGE_INTEGRATION.md), on the [shared retrieval foundation](PHASE10_KNOWLEDGE_FOUNDATION.md).

Confirmed starting points: four existing domain specialists, SDK manager orchestration, exact MCP document reads, one shared source-backed knowledge index, host-owned approval/execution services and nine controlled Engineering documents. The current corpus has no quality SOP or historical investigation report. No new business documents, policies or scenario facts were authored to hide that gap. The open question of live model retrieval quality remains for an explicitly paid smoke; all verification in this slice is offline.

## Hybrid retrieval and authority

Current operational systems → existing scoped MCP/API tools → source-backed facts.

Unstructured institutional knowledge → one shared retrieval service → fixed specialist profile → candidate passage → exact source/version verification → concise specialist evidence → Coordinator synthesis.

Host policy and the appropriate human role retain authority. Retrieval cannot approve, schedule, release held material, establish root cause, accept evidence, commit quantities, or trigger background work. Structured facts govern current state; approved current procedures govern procedural interpretation. Historical reports are contextual evidence, never current disposition or normative policy. Similarity is ranking, never confidence.

## Agents and retrieval decisions

| Specialist | Fixed profile | Intended use |
|---|---|---|
| Change Impact | CHANGE_IMPACT | Change policy, engineering requirements/specification and architecture scope |
| Validation & Evidence | VALIDATION_EVIDENCE | Procedure, acceptance criteria and engineering review explanations |
| Manufacturing / Supply | MANUFACTURING_QUALITY | Hold/investigation SOPs and explicitly requested historical guidance |
| Program / Commercial | PROGRAM_COMMERCIAL | Narrow customer/program/routing policy explanations |
| Coordinator | No knowledge tools | Consume specialist findings and their verified citations |

Change Impact and Validation now include the existing `policy` document type; Change Impact includes `standard_routing_policy`. Program/Commercial remains narrower than the technical profiles. All profiles still share the same index, eligibility rules and exact-source interface.

Instructions distinguish procedural/document questions from current lot state, inventory, order quantities, jobs, approvals, dates and coverage. Retrieval is optional. Unknown relevant documents are discovered before exact follow-up; a known exact document can still use the existing MCP path. No documents are prefetched or re-embedded per run.

Two SDK function tools are attached only to permitted specialist invocations:

- `search_specialist_knowledge(query, why_relevant, include_historical)` — fixed host identity, scope and profile; at most three searches and six candidates per search.
- `verify_specialist_knowledge(chunk_id)` — accepts only a candidate returned to that invocation; at most eight verifications. No index management or arbitrary ingestion capability.

Both consume the existing total tool-call budget. Search failures and empty results return no evidence with a bounded status. Required domain work continues to use its existing failure/uncertainty rules. No failure creates an approval or a policy conclusion.

The model cannot set its profile, identity or program. Shared workflow findings can feed business case/proposal surfaces, so specialist retrieval additionally excludes role-restricted documents. Those documents remain available only through authorized persona-owned library/Concierge retrieval; their text cannot be laundered into shared workflow summaries. Explicit product/configuration applicability must match trusted context; unknown source metadata remains unknown and requires exact interpretation. Drafts, rejected documents, future-effective procedures and superseded versions remain excluded by default. Specialist tools do not expose a prior-version override. Retrieved text and exact document text remain untrusted evidence; embedded commands grant no permissions.

## Findings and exact verification

Assessments add an optional bounded `knowledge_evidence` list. Each entry carries document ID/version, chunk/section, profile, program/configuration, approval/current/historical state, relevance purpose, a host-issued verification ID and an exact source receipt.

The verifier reuses the existing source document path through `KnowledgeService.verify`. The harness registers the returned document context in its existing SourceRegistry, enabling exact JSON-pointer facts and citations. Search results alone do not mint a factual receipt. The host rejects invented, modified, unverified or other-invocation evidence and rechecks the source before accepting a finding. A passage is marked cited only after the assessment passes the existing source/domain validation.

Coordinator receives concise findings and citations, not unrestricted retrieval tools. Final prose should cite document ID, version and section without dumping passages. Existing structured claim checks and policy ceilings remain active.

## Workflow-specific behavior and comparison

| Case | Knowledge contribution | Preserved business conclusion |
|---|---|---|
| CR-017 | Supplemental validation procedure and engineering review/change policy | Evidence gap; conditional options and Engineering review. Scheduling is not a test pass or customer acceptance. |
| CR-019 | Approved standard package procedure and routing policy | Deterministic host policy alone permits the bounded Validation Operations handoff. |
| QE-004 | Manufacturing profile is integrated; the current corpus returns no eligible quality knowledge | Held material stays held/ineligible; site concentration does not establish root cause; existing investigation/recovery authority remains separate. |
| DR-009 | Optional narrow delivery/customer policy, when needed | Structured calculators retain 600 eligible / 800 requested / 200 gap. No RAG call is scripted for that calculation. |

The canonical comparison runs each case before/after through the same CaseHarness, real local source HTTP and MCP, and explicit deterministic model doubles. It compares policy path, review requirement, authority claims, quality/delivery claims, coverage and eligible options. All four conclusions are unchanged. There are no EXPECTED or UNEXPECTED material conclusion changes in the measured offline runs. This does not establish live model reasoning quality.

## Provenance and UI

Retrieval events live in the same shared knowledge database, alongside the existing index/search audit. There is no per-agent store. Events retain run/case/invocation or owning Concierge session, specialist/profile, query, explicit relevance purpose, provider, latency, returned document/chunk versions/status and exact verification/citation state. They contain metadata, not full passages or hidden reasoning. Queries/relevance descriptions are redacted with the existing safe observability projection.

Knowledge & Evidence adds “Used in agent runs,” per-document recent-use labels and retrieval activity. Refreshing activity updates both the activity view and document filter. Versioned passage links reuse the split exact-document/passage modal. Each case has a distinct Knowledge evidence section alongside current structured evidence. Operations run detail shows profile, query, provider, latency, returned sections and verification status. New exact knowledge receipts are omitted from the separate structured-evidence list to avoid double categorization.

The event and passage endpoints recheck the current persona and source document access. Removed/restricted documents suppress the entire associated event, including its query. Changed source metadata marks historical provenance as changed. Concierge query history is private to its owning persona. Run/session records archived by demo reset are not projected as current usage; the durable index and provenance archive are retained.

Concierge's existing manager routes explicit procedural/document questions to the shared service. The host selects a bounded domain profile, verifies at most three returned passages and shows source text with citations beside current source facts. No second synthesis agent or new authority was introduced. Program Owner has no Knowledge surface, so it receives no knowledge passages. Cached Concierge and Operations history cards recheck source access/version on read. Persisted visible history omits the passage body and retains the reference instead.

## Offline evals and regressions

The [A–O manifest](../coordinator/evals/phase10_knowledge_integration/cases.json) maps all 15 requested retrieval gates to executed tests. The runner reads actual JUnit outcomes, rejects missing/skipped/failed gates, then runs the four canonical comparisons. Adversarial/historical/wrong-product documents exist only in isolated tests. They are never runtime corpus additions.

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_knowledge_integration

PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode offline --include-standard --include-quality --include-delivery --include-concierge
```

The original Phase 07 graders and cases remain unchanged. A deterministic browser fixture explicitly scripts optional knowledge calls around the existing model doubles; it is labeled scripted integration testing, not live intelligence or human approval.

## Optional paid/live smoke — not run

First explicitly index the shared corpus using the [foundation setup commands](PHASE10_KNOWLEDGE_FOUNDATION.md#explicit-commands). Use the same source URL and metadata directory for indexing and agent runs. Nothing indexes on startup.

Example CR-017 manual invocation against the existing local review ports:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator \
  --event coordinator/scenarios/human_review.json \
  --source-url http://127.0.0.1:18322 --mcp-url http://127.0.0.1:19322/mcp \
  --metadata-dir .cache/phase09-3/phase10-2-preview/metadata \
  --allow-paid-knowledge-search
```

This existing CLI is an explicit paid analysis command. The new flag selects hosted retrieval; it does not index or authorize business writes. Existing model configuration/secure key loading is reused. Without the flag, knowledge ranking is deterministic offline even when the deliberately invoked analysis model is live.

For QE-004, use an existing source-derived QE-004 event with `--workflow-id yield_exception_recovery` and the same options. The current nine-document corpus lacks a quality SOP/history report: a useful positive retrieval smoke needs an explicitly curated, source-owned document addition first. Until then, the correct retrieval outcome is no eligible knowledge, not an invented SOP.

For Concierge, start the normal control host with `--allow-paid-knowledge-search`, select a Knowledge-capable persona and explicitly send “What does the approved validation procedure require for CR-017?” or the requested quality-procedure question. The latter currently demonstrates the empty-evidence behavior. Ordinary sends cannot approve or execute.

After an explicitly live run, inspect Operations and the existing private run report: provider, specialist, retrieved documents/versions, verification state and latency are in retrieval events; actual model token usage is in the existing report/Operations usage fields. Compare the final conclusion to the canonical result. Provider search does not return model token usage and no value is invented.

## Limits and stop point

Offline retrieval is deterministic term/synonym ranking, not neural semantic quality. Hosted indexing/search and live model selection/reasoning have not been exercised here. Exact-source verification validates provenance/applicability metadata, not the semantic correctness of every free-text interpretation; existing typed source and governance checks remain essential. Historical exact verification remains unavailable when the source no longer serves that version.

The nine-document corpus has limited coverage and missing structured configuration/effective-date fields. Manufacturing/quality and some delivery-policy questions therefore yield no evidence. No fabricated policies, quality dispositions or historical diagnoses were added. Source APIs, business data, source-write permissions, approval contracts, graph/orchestration, Agent Workspace visuals and QE-011 background behavior are unchanged. Stop after this integration.
