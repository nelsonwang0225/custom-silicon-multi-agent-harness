# QE-004 Quality knowledge corpus completion

Scope: [approved request](../prompts/10_QE004_KNOWLEDGE_CORPUS.md). This completes
the missing Quality corpus in the existing shared Knowledge & Evidence service.
It adds no workflow, agent, vector store, business write permission or disposition
authority. The canonical QE-004 operational records are unchanged.

## Controlled publications

| Document | Type | Lifecycle | Owner |
|---|---|---|---|
| DOC-QA-HOLD-01 · v1 — Quality Hold & Disposition SOP | quality_sop | Approved | Product Quality / Manufacturing |
| DOC-QA-EXCURSION-01 · v1 — Final-Test Excursion Investigation Procedure | manufacturing_procedure | Approved | Product / Test Engineering with Product Quality / Manufacturing |
| DOC-QA-HIST-01 · v1 — Historical Investigation — Test-Site Concentration | historical_investigation | Historical, closed, non-normative | Product Quality / Manufacturing |

All have program PRG-A17, customer CUST-FML01, product ACCELERATOR-X, configuration
CFG-B-01 (REV-B), content version 1, applicable workflow yield_exception_recovery,
explicit SHA-256 content hashes, owner metadata and no superseding publication.
The approved documents are effective 2026-08-01T00:00:00Z. The historical report
describes a prior investigation closed July 1; it has no normative effective date.
Its `historical=true` and `status=historical` are persisted source fields.

Quality owns the business content; Engineering Hub remains the existing controlled
publication custodian and HTTP endpoint. This preserves the repository's source
ownership and read permissions. PROC-QE-B-01 remains the source-owned Engineering
investigation contract; the new procedure explains it and grants no new task scope.

Files are explicitly allowlisted in `mock_enterprise.quality_knowledge`, imported
as immutable `engineering.document` records and served through the existing
document HTTP endpoints. They are not eval-only or browser-only fixtures. The
source schema now retains the optional metadata already consumed by the RAG
model and recognizes historical lifecycle. Existing records with absent metadata
still decode with unknown/default values.

Default new-demo initialization includes these publications. Existing demo databases
need the explicit additive installer below; merely changing files cannot publish
documents into an existing source database. Repeated installation verifies the
same immutable identities, inserts nothing, and refuses conflicting publications.
It preserves operational records, existing document bodies and historical artifacts.

## Indexing and retrieval

The existing document-type mapping permits all three under MANUFACTURING_QUALITY.
No per-agent index or new retrieval implementation was introduced. Approved
documents are eligible by default. Historical context requires `include_historical`;
requested/draft and superseded documents stay excluded from current normative
retrieval. Program, configuration and product checks retain precedence over scores.

The shared section chunker produces stable identity/version/hash/section IDs.
Repeated sync/rebuild does not duplicate chunks. Exact verification re-reads the
same controlled source document/version and metadata. A current archived source
version is still historical knowledge, never current approved policy.

The existing review preview now has a current **12-document offline index**. The
new publications contribute 10 chunks: hold SOP 4, excursion procedure 3, historical
report 3. After checking zero active runs, the same deterministic preview was
stopped, the three publications installed additively, and the same source/metadata
directories restarted and synchronized. Every non-document table and every old
document content hash matched its pre-install snapshot. The one existing recorded
run remains one; no investigation or historical retrieval was backfilled.

The local HTTP smoke passed against that preview using deterministic retrieval:
both the SOP and historical report were exactly verified against source, and the
current held material/root-cause claims remained unchanged. Evidence artifacts:
`.cache/phase10-quality-corpus/preview-publication.json`, `preview-index.json`,
and `preview-smoke.json`.

Deterministic top results:

| Query | First result |
|---|---|
| What policy governs held material and shipment eligibility? | DOC-QA-HOLD-01 |
| How should a final-test excursion be investigated? | DOC-QA-EXCURSION-01 |
| What does prior experience say about failures concentrated at one test site? | DOC-QA-HIST-01, with historical context enabled |

The specialist now obtains product applicability from the already verified intake
configuration, avoiding dependence on another specialist's read timing. Concierge
likewise uses the existing QE-004 snapshot configuration. Its bounded explanatory
path allows history for site-causality questions, cites exact versions, and displays
current structured facts separately. No tool permission changes were required.

Approval compatibility is preserved explicitly: absent/default publication fields
do not alter legacy document critical digests, populated metadata remains bound,
and quality-only publications do not enter an unrelated CR-017 plan's automatic
critical source set. Explicit assessment document references still bind normally.
Tests create an exact CR-017 approval before installing the corpus and successfully
use it afterward, with the full validation-options response unchanged.
The existing preview's six original document snapshot digests also match after
the update (`.cache/phase10-quality-corpus/preview-approval-compatibility.json`).

## Before and after QE-004

Before: no useful quality knowledge evidence. After: approved hold guidance,
approved investigation guidance and historical context are discoverable and
exactly verifiable. Canonical business conclusions remain **UNCHANGED**:

- Manufacturing records LOT-B-204 held: 250 physical/held units and 200 first-pass
  passes. Its eligible supply contribution stays zero.
- The other released supply remains 600 against demand of 800, a 200-unit gap.
- Site concentration warrants investigation. Historical setup findings do not
  establish QE-004 root cause; the current observation still records it as unresolved.
- Quality retains disposition authority. Standard investigation and Program Owner
  recovery planning do not release, retest, rework or allocate the held lot.

Knowledge, case and Operations views use existing provenance: document/version,
section, lifecycle, specialist/profile, exact verification and cited-use state.
The library retains Document / Type / Version / Approval; Program and Source state
columns were not restored. Historical rows explicitly say non-normative. Index and
source-version state remain in the existing search/verification surfaces. Existing
runs are not retroactively assigned retrievals they never performed.

## Verification

All automated checks use isolated storage, deterministic retrieval
and SDK/manager doubles. They test enforced contracts and scripted outcomes, not
live model reasoning. No paid search, hosted indexing, model generation or real
speech was run.

| Final check | Result |
|---|---|
| Source/backend, including 7 publication/compatibility tests | 490 passed, 178.56s |
| Full coordinator, including RAG, QE-004, Concierge and Operations | 819 passed, 375.63s |
| MCP | 56 passed, 14.79s |
| Canonical offline workflow/Concierge evals | 112/112 passed; hard gates PASS, no critical failures |
| Existing RAG integration gates | 15/15 passed; all four canonical conclusions unchanged |
| Focused Quality corpus evals | 12/12 passed, with 14 test observations including two Concierge questions |
| Knowledge browser, including Operations provenance | 4 passed, 38.9s |
| Typecheck + production build | Passed |
| Existing preview read-only smoke | Passed, using deterministic retrieval and live local source HTTP |

Final canonical eval artifacts:
`.cache/phase07/eval_766ba2e725f74b93b4114d9c0b06a5a5/`.
Existing RAG gate artifacts:
`.cache/phase10-rag-integration/eval_abf1376a26524c08b40a1bd343d7daf4/`.
Quality gate artifacts:
`.cache/phase10-quality-corpus/eval_70324708219b488dbd85a1d245f630c7/`.
These are overlapping suites, not additive independent case counts. No automated
tests were skipped. Paid live agents, hosted indexing/search, the optional
model-based semantic grader and real speech were intentionally not run.

Inspected screenshots: quality library at 1440/1920/1280/390 widths, historical
source preview, and Operations provenance in `docs/screenshots/phase10-knowledge/`.
The existing preview's [three-document library capture](screenshots/phase10-knowledge/quality-library-detail.png)
shows the final published roles and statuses without test-run labels.

Commands run from the repository root unless noted:

```sh
PYTHONPATH=src:. .venv/bin/python -m pytest tests -q --basetemp=.cache/phase10-quality-corpus/source-verified
PYTHONPATH=src:. coordinator/.venv/bin/python -m pytest coordinator/tests -q --basetemp=.cache/phase10-quality-corpus/coordinator-verified
PYTHONPATH=src:. mcp_server/.venv/bin/python -m pytest mcp_server/tests -q --basetemp=.cache/phase10-quality-corpus/mcp-verified
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07 --mode offline --include-standard --include-quality --include-delivery --include-concierge
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_knowledge_integration
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_quality_knowledge
```

From `mock_apps_ui/`: `npx playwright test -c playwright.knowledge.config.ts --reporter line`,
`npm run schema`, and `npm run build` (includes TypeScript checking). The exported
source OpenAPI was separately compared with the current app schema and matched.
Logs and scorecards are under `.cache/phase10-quality-corpus/`.

The first source lifecycle run caught the required uppercase SYNTHETIC marker;
the publications were corrected without weakening the check. Screenshot review
caught captures taken while the library was loading; the browser test now waits
for all three rows and a current index before capturing. Approval-compatibility
review led to the two explicit regression tests described above and a final full
source/coordinator pass. Original failure logs remain alongside final logs.

Focused coverage: all 12 requested corpus gates in
`coordinator/evals/phase10_quality_knowledge/cases.json`, plus two Concierge
questions. Source tests cover immutable persistent HTTP publications, ownership,
idempotence, conflict rollback, legacy approval compatibility and absence of a document write route. Browser
checks cover library roles, historical verification, mobile layout and three
recorded QE-004 retrievals in Operations.

## Manual installation and optional live retrieval

For an existing default `.demo` database, stop its source service, then run from
the repository root (set DEMO_DB explicitly if using another database under `.demo`):

```sh
DEMO_MODE=true PYTHONPATH=src:. .venv/bin/python -m mock_enterprise.cli install-quality-knowledge
```

Restart the same source service. Use its actual URL and the existing host metadata
directory below; this is the same shared index, not a new index location:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.knowledge sync \
  --source-url http://127.0.0.1:18322 \
  --metadata-dir .cache/phase09-3/phase10-2-preview/metadata --provider offline
```

Optional read-only smoke against that synchronized source/index:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_quality_knowledge.smoke \
  --source-url http://127.0.0.1:18322 \
  --metadata-dir .cache/phase09-3/phase10-2-preview/metadata --provider offline
```

For the existing hosted shared store, manually sync using the same source URL and
**its existing metadata directory** via the existing index CLI with
`--provider openai --allow-paid`. Do not use a new metadata directory: that CLI
would provision a new store if it has no receipt. Then run the smoke above with
`--provider openai --allow-paid`. The smoke itself requires an existing hosted-store
receipt and never indexes or creates a store. These hosted commands are provided
for manual opt-in and were **not run**.

Exact hosted commands, only after setting `STRATOS_EXISTING_METADATA_DIR` to the
directory that already owns the hosted shared-store receipt:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m program_coordinator.knowledge sync \
  --source-url http://127.0.0.1:18322 \
  --metadata-dir "${STRATOS_EXISTING_METADATA_DIR:?Set the existing hosted index directory}" \
  --provider openai --allow-paid
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_quality_knowledge.smoke \
  --source-url http://127.0.0.1:18322 \
  --metadata-dir "${STRATOS_EXISTING_METADATA_DIR:?Set the existing hosted index directory}" \
  --provider openai --allow-paid
```

The smoke retrieves the approved hold SOP and historical report, verifies exact
source bytes/lifecycle, reads Manufacturing before and after, and checks the
existing source-derived HOLD/root-cause/release claims. It performs no model
generation or business writes and does not measure live model reasoning. If
current source facts differ from canonical QE-004, it stops instead of inventing
the expected result.

## Limitations and stopping point

Three deliberately small synthetic publications support one quality scenario.
Offline ranking is transparent term/synonym matching; hosted retrieval and live
reasoning quality remain unmeasured. Existing access and source-freshness rules
remain in force. Historical content is contextual even after exact verification.
No arbitrary document ingestion, new workflow logic, disposition mutation,
QE-011 event trigger, new agent/store or Git packaging was implemented.
