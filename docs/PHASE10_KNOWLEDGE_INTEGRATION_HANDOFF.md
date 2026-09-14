# Specialist knowledge integration — final handoff

**Subsequent corpus completion:** the focused [QE-004 Quality corpus handoff](PHASE10_QUALITY_CORPUS_HANDOFF.md)
supersedes this report's missing-quality-corpus limitation. Historical verification
counts below describe the original integration; the new handoff records its own
current regressions and publication/index status.

The [implementation contract](PHASE10_KNOWLEDGE_INTEGRATION.md) contains the architecture, access rules, UI behavior, source precedence, live commands and limitations. The [approved request](../prompts/10_SPECIALIST_KNOWLEDGE_INTEGRATION.md) is preserved.

## 1. Agents integrated

Change Impact, Validation & Evidence, Manufacturing / Supply and Program / Commercial have optional bounded discovery/verification tools in the existing CaseHarness. Concierge's existing manager can route document explanations to the same service. Coordinator has no corpus search tool. No new agent, store, scheduler or orchestration framework.

## 2. Retrieval profiles

Each specialist is host-bound to CHANGE_IMPACT, VALIDATION_EVIDENCE, MANUFACTURING_QUALITY or PROGRAM_COMMERCIAL. Profile, actor and program are not tool arguments. Shared workflow retrieval excludes role-restricted documents to prevent their text entering broadly visible case/proposal summaries; authorized persona-owned discovery/Concierge can still use them.

## 3. Workflow-specific usage

CR-017 uses supplemental validation/review and change-policy evidence. CR-019 uses standard procedure/routing explanations. QE-004 has the Manufacturing profile and truthful empty retrieval with the existing corpus. DR-009 continues structured quantities/dates; optional knowledge is reserved for genuine policy questions. No source documents or business facts were added.

## 4. Structured-versus-RAG rules

Structured tools determine current state, quantities, dates, jobs, approvals and coverage. RAG discovers procedural/document evidence when necessary. Known exact documents remain accessible through existing tools. Similarity does not establish applicability. Historical reports cannot override a current HOLD, determine root cause or authorize release.

## 5. Exact verification

Material citations require an invocation-bound host verification receipt. The host validates the exact document/version/metadata, registers a source receipt, rejects fabricated/modified references and marks usage only after existing assessment validation passes. Historical versions no longer served by the source cannot be claimed exactly verified.

## 6. UI

Knowledge & Evidence now has a used-in-runs filter, recent-use labels, recorded retrieval activity and versioned links into the existing split passage/source modal. Case views distinguish Knowledge evidence from structured source evidence. Older runs are not backfilled with invented retrievals.

## 7. Operations and Concierge

Operations run detail shows specialist/profile, query, provider, latency, returned document sections/versions/status and verification/citation state. Query/relevance observability uses existing redaction. No embeddings, hidden reasoning or full passage bodies are logged in retrieval events. Concierge history is actor-owned; cached evidence rechecks source access/version on read, and persisted visible history omits passage bodies.

## 8. Evals

All 15 requested A–O retrieval gates are represented in the [executed manifest](../coordinator/evals/phase10_knowledge_integration/cases.json). Coverage includes exact receipts, wrong configuration/product, high-score mismatch, history, empty/failure behavior, fabricated policies, HOLD precedence, injection, persona access and optional tool selection. These deterministic checks validate tool/host contracts, not live model reasoning.

## 9. Business conclusions before and after

| Workflow | Before and after | Change classification |
|---|---|---|
| CR-017 | Evidence gap; conditional validation options; Engineering review and separate customer acceptance | UNCHANGED |
| CR-019 | Exact deterministic standard-routing eligibility; bounded handoff only | UNCHANGED |
| QE-004 | Held material ineligible; root cause unresolved; existing investigation/recovery boundaries | UNCHANGED |
| DR-009 | Structured 600 eligible / 800 requested / 200 gap; exact Program Owner approval boundary | UNCHANGED |

No expected or unexpected material conclusion changes were observed. Canonical before/after runs cross real local HTTP/MCP and use the existing deterministic SDK doubles plus explicit retrieval calls.

Latest hybrid artifact: `.cache/phase10-rag-integration/eval_255509a6bd8f45e3a8897ca21bd3f79b/` (15 gates, four comparisons, zero unexpected changes). Additional final access hardening is covered by the final focused run below.

## 10. Actual verification

| Check | Result |
|---|---|
| Source/backend | 483 passed, 179.73s |
| Full coordinator | 804 passed, 370.86s |
| MCP | 56 passed, 15.27s |
| Current canonical offline evals before | 112/112; no critical failures |
| Current canonical offline evals after | 112/112; no critical failures |
| Hybrid RAG evals | 15/15 gates; all four canonical conclusions unchanged |
| Final focused knowledge/access/Operations | 38 passed, 21.72s; overlaps full suite, includes the last shared-output access check |
| Knowledge browser | 3 passed, 30.0s |
| Persona/navigation browser | 9 passed, 51.4s |
| Typecheck + production build | Passed; final Vite build 1.26s |
| Existing local preview HTTP read | Current offline index, nine documents, zero active runs, original one recorded run preserved |

Python commands actually run (from repository root, with `PYTHONPATH=src:.`):

```sh
.venv/bin/python -m pytest tests -q --basetemp=.cache/phase10-rag-integration/source
coordinator/.venv/bin/python -m pytest coordinator/tests -q --basetemp=.cache/phase10-rag-integration/coordinator
mcp_server/.venv/bin/python -m pytest mcp_server/tests -q --basetemp=.cache/phase10-rag-integration/mcp
coordinator/.venv/bin/python -m coordinator.evals.phase07 --mode offline --include-standard --include-quality --include-delivery --include-concierge
coordinator/.venv/bin/python -m coordinator.evals.phase10_knowledge_integration
coordinator/.venv/bin/python -m pytest coordinator/tests/test_knowledge_foundation.py coordinator/tests/test_knowledge_integration.py coordinator/tests/test_phase08_6_operations.py -q --basetemp=.cache/phase10-rag-integration/final-verified
```

Browser commands actually run from `mock_apps_ui/`, using the installed Google Chrome for Testing executable through `PLAYWRIGHT_CHROMIUM_EXECUTABLE`:

```sh
npx playwright test --config playwright.knowledge.config.ts --reporter line --output ../.cache/phase10-rag-integration/browser
STRATOS_SCREENSHOT_DIR='../docs/screenshots/phase10-knowledge-integration/persona' npx playwright test --config playwright.persona.config.ts --reporter line --output ../.cache/phase10-rag-integration/persona
npm run build
```

Logs: `.cache/phase10-rag-integration/`. Original before/after Phase 07 artifacts: `eval_212343776cca4e5bb86287fa74405ca9` and `eval_1c5c54b7d9aa4e45b2464eafa4b92a39` under `.cache/phase07/`.

Visual inspection: [used documents and retrieval activity](screenshots/phase10-knowledge/used-in-runs-1440.png), [Operations provenance](screenshots/phase10-knowledge/run-provenance-1440.png), and the existing desktop/mobile passage screenshots. Browser speech is mocked. The first provenance browser attempt used an invalid invocation-ID prefix; it now uses the documented `ui_` prefix. Browser testing also exposed the library/activity refresh mismatch, which was corrected. The persona geometry test read two panels across a telemetry refresh; both dimensions are now sampled in a single layout snapshot. No Agent Workspace design was changed.

## 11. Optional live steps

See [manual live commands](PHASE10_KNOWLEDGE_INTEGRATION.md#optional-paidlive-smoke--not-run). Existing CLI `--help` was checked for `--allow-paid-knowledge-search`, source URL and shared metadata arguments. Hosted indexing/search, paid model runs and model-based graders were not run. Existing credentials were neither printed nor changed.

## 12. Limitations and stop

Offline term/synonym ranking does not measure neural retrieval or live reasoning quality. The small corpus lacks quality SOPs/history and some delivery guidance. Missing metadata remains explicit, and source-only-current APIs limit historical verification. No new business authority is inferred from documents. Program Owner has no Knowledge surface; shared workflow text is restricted to program-shared documents.

The existing deterministic preview at http://127.0.0.1:5203/control/knowledge was restarted using the explicit knowledge browser fixture against the same source/metadata directories after checking zero active runs. Its existing business state and recorded run were preserved. It produces scripted test investigations, not live intelligence. No historical retrievals were invented.

No paid calls, commits/pushes, working-demo reset, approval changes, source writes, background triggers or QE-011 implementation. Stop after the specialist retrieval integration.
