# Shared Knowledge retrieval — handoff and verification

The later [QE-004 Quality corpus completion](PHASE10_QUALITY_CORPUS_HANDOFF.md)
adds approved quality procedures and labeled historical context through the same
shared index. This foundation handoff's verification counts remain historical.

The [foundation contract](PHASE10_KNOWLEDGE_FOUNDATION.md) documents the inspected nine-document corpus, two retrieval responsibilities, official OpenAI/offline providers, shared index, metadata, exact verification, profiles, security, lifecycle, live commands and next integration boundary.

Implemented: section-aware discovery, stable versioned chunks, explicit incremental sync/rebuild, source-validated eligibility, server-side scope/persona/document filtering, exact current-source verification, retrieval audit and a connected Knowledge & Evidence UI. No agent or MCP tools, prompts, workflow outputs, business authority, source writes or events were added or changed.

## Actual verification

| Check | Actual result |
|---|---|
| Source/backend suite (`.venv/bin/python -m pytest tests -q --basetemp=.cache/phase10-rag/source`) | 483 passed, 170.37s |
| Coordinator suite (`coordinator/.venv/bin/python -m pytest coordinator/tests -q --basetemp=.cache/phase10-rag/coordinator`) | 789 passed, 354.69s; includes original workflows, authority, reset, persona and initial 10 retrieval tests |
| Final focused retrieval suite | 13 passed, 3.20s; overlaps the coordinator suite and adds later failure/race/reset cases |
| MCP suite (`mcp_server/.venv/bin/python -m pytest mcp_server/tests -q --basetemp=.cache/phase10-rag/mcp`) | 56 passed, 14.35s |
| Current offline evaluations, all optional connected offline extensions | 112/112 passed; hard gates PASS, no critical failures |
| Persona/navigation browser suite | 9 passed, 46.6s |
| New Knowledge browser suite | 2 passed; indexing, empty/relevant search, exact preview, 1440/1280/390 layouts, source failure and persona changes |
| Typecheck + production build | Passed |
| Real local HTTP smoke on existing review session | Nine documents, current offline index, three relevant results, exact current source verified |

All Python commands used `PYTHONPATH=src:.` and isolated temporary source/metadata storage. Browser tests used the existing explicit local deterministic HTTP/MCP fixture and mocked speech. Paid agents, embeddings, hosted file indexing/search, semantic model graders and real microphone use were not run. Existing workflow tests use deterministic doubles, not actual human approvals.

Offline eval command:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode offline --include-standard --include-quality --include-delivery --include-concierge
```

Artifacts: `.cache/phase07/eval_e90db08300de4e76adc90069d1f394ae/`. The original Phase 07 and historical live artifacts were preserved.

Browser commands, from `mock_apps_ui/`, with `PLAYWRIGHT_CHROMIUM_EXECUTABLE` set to the installed Google Chrome for Testing executable:

```sh
npx playwright test --config playwright.knowledge.config.ts --reporter line \
  --output ../.cache/phase10-rag/browser-layout
STRATOS_SCREENSHOT_DIR='../docs/screenshots/phase10-knowledge/persona' \
  npx playwright test --config playwright.persona.config.ts --reporter line \
  --output ../.cache/phase10-rag/persona
```

Screenshots visually inspected:
- [Knowledge search/library](screenshots/phase10-knowledge/search-1440.png)
- [Exact document and passage, desktop](screenshots/phase10-knowledge/passage-1440.png)
- [1280 layout](screenshots/phase10-knowledge/passage-1280.png)
- [Mobile modal](screenshots/phase10-knowledge/passage-390.png)

The initial browser attempt used a full reload after selecting a persona; that correctly reset the demo identity and removed admin access. The test now uses in-app navigation. A follow-up selector had the wrong capitalization for Program Owner and was corrected. No access behavior was weakened. Visual inspection found shared button styles overriding passage alignment; selectors were scoped more specifically and browser checks rerun. An initial schema generation omitted demo routes and introduced colliding short model names; the final schema includes demo routes and distinct Knowledge model names. An initial invocation of the eval runner module performed no work; the documented package entry point above executed all 112 cases.

## Files changed

Runtime: `src/program_coordinator/knowledge/{models,corpus,providers,service,__init__,__main__}.py`; `control_host/knowledge.py`, route installation in `control_host/server.py`, explicit hosted-search opt-in in `control_host/__main__.py`; `mock_apps_ui/src/control/knowledge.tsx`, `knowledge.css`, extracted/re-exported Knowledge view in `previews.tsx`, generated `host-schema.d.ts`.

Verification: `coordinator/tests/test_knowledge_foundation.py`, `coordinator/evals/phase10_knowledge/schema.py`, `mock_apps_ui/playwright.knowledge.config.ts`, `mock_apps_ui/e2e-knowledge/knowledge.spec.ts`, `docs/phase10-knowledge-host-openapi.json` and isolated screenshots.

Documentation: approved prompt copy, AGENTS authorization, demo runbook, foundation contract and this handoff. No dependency changes or Git operations.

## Limits and next step

The normal preview uses deterministic offline ranking, not neural embeddings. The OpenAI implementation is ready for explicitly requested hosted setup/search but has not been live-verified. Its SDK calls are mocked in tests and checked against current official documentation and installed SDK signatures.

The corpus is deliberately small and Engineering-owned. Manufacturing/quality and historical report profiles may return no eligible evidence. Missing structured applicability stays unknown. Historical text is retained, but exact authoritative historical verification is unavailable when the source API only serves a newer current version. No invented confidence, page numbers, approval state or model availability.

The exact next step is an explicitly authorized specialist integration: narrowly expose discovery with each specialist's profile, require exact source verification before material reliance, and propagate versioned evidence references into typed findings. Coordinator should consume those findings. Stop here; no broad agent behavior or QE-011 trigger implementation.
