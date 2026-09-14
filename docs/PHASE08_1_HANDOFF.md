# Phase 08.1 — product shell and visual review

**Historical initial-shell handoff. The [approved visual refinement handoff](PHASE08_1_REFINEMENT_HANDOFF.md) supersedes the palette, Portfolio composition and docked assistant described here. The floating Ask Stratos preview is now authoritative; chat integration remains 08.5.**

Implemented the shared requirements, scoped visual system and read-only program control-plane shell. **Stop here for visual review. Phase 08.2 has not started.**

The isolated local preview is [Program portfolio](http://127.0.0.1:5188/control). It uses current repository source APIs on port 18008 and a freshly initialized synthetic test database, not the pre-existing working service on port 8000. The five source apps are available at [the original launcher](http://127.0.0.1:5188/).

## Implemented scope

- Persisted the exact approved request and shared Phase 08 product/governance requirements before implementation, plus the six-slice plan.
- Added `/control/*` within the existing React/TypeScript/Vite application. Original root and five source routes retain their provider, behavior and styles. The control branch is lazy-loaded and CSS is scoped beneath `.cp-root`.
- Added a compact Stratos header, horizontal navigation, off-white/white/charcoal tokens, native system typography, reusable status/freshness components, process steps, source links, section layouts and an evidence dialog. No fonts, image assets or dependencies were downloaded.
- Portfolio derives four metrics from filtered displayed source programs. Helios is first in the reason/owner/next-step queue; default focus also includes existing Northstar Boreal and Vela Stream at distinct source lifecycle stages. All eleven programs remain explorable. Next-gate baseline and forecast dates retain their source meaning; activity is explicitly recorded source activity.
- Program pages expose configuration, customer, lifecycle, owner, next gate, risks, cases and technical/validation/supply/commitment drill-downs. Helios additionally has separately namespaced illustrative 1A, QE-004 and DR-009 entries; none creates a host/backend case.
- Source case pages expose actual source workflow, plan and scheduling state, before/after requirement comparison, dependency drill-downs, applicability matrix, read-only calculated lab options, recorded plans/decision references and source audit activity. A passing result is not automatically applicable to the new requirement. The evidence drawer includes source ID, versions, applicability, timestamps, captured configuration/workload/model/criteria, runtime and per-bin exposure.
- Useful workflow detail, decision register, scenario story, controlled-document library and Operations preview routes are functional. DR-009 calculates the 200-unit gap from its isolated 1,000-unit breakdown; it never replaces the real 100-unit CR-017 order.
- Assistant opens globally within the control-plane product, follows route context and restores focus. It reserves space beside the page on larger screens and moves into document flow on narrower screens. Shortcuts navigate existing views; chat input is explicitly disabled as a UI preview.
- Filters, case tabs and evidence/document links use URL state. Reload/back, unknown-scope stops, stale/unavailable reads and rapid filter changes are covered. Refresh reads only; no navigation or timer invokes a model. The five-minute freshness timer does not poll APIs.

## Actual mode and data matrix

All business and illustrative data is synthetic. Execution mode is separate from current/recorded/stale/unavailable freshness.

| Surface | Actual 08.1 behavior | Mode / freshness |
|---|---|---|
| Portfolio / programs / source cases | Existing HTTP GETs via fixed portfolio reader | Connected demo, read only; current read, stale or unavailable |
| Evidence / documents / source plan register | Current HTTP retrieval of persisted observations and records | Connected demo; recorded result distinguished from read freshness |
| Validation option comparison | Existing per-case GET, with source cost/timing/eligibility calculations | Connected demo, read only; no choice, recommendation or approval submitted |
| CR-017 host investigation/proposal/review/resume/execution | Not connected in this slice | Preview only; no host run or verification inferred |
| 1A, QE-004, DR-009 | Clickable explanatory stories with separate `preview-` URL IDs | Preview only; no executed simulation or trace |
| Workflow catalog / triggers | Descriptive view of inspected registry capabilities and planned triggers | Preview only; no invocation, saved configuration or worker |
| Contextual assistant | Context and navigation shortcuts, disabled text input | UI preview only; no chat/model connection or conversation store |
| Operations / evals | Connection observation plus labeled historical handoff context | Preview only for runtime/evals; no fresh model scorecard |

No executed simulations were added in 08.1. This is intentionally narrower than the end-of-Phase-08 capability target.

## Architecture and source authority

`control/data.tsx` calls the existing typed `api('reader').get` adapter with the public mock portfolio selector. It reads `/api/v1/portfolio`, `/programs`, `/manufacturing/units`, `/manufacturing/lots` and `/erp/orders`. Controlled documents and options use their existing scoped GETs on demand. The browser retains a display snapshot only; no business state or competing database is persisted. Failed refresh retains a visibly stale snapshot or reports unavailable, with no simulated fallback.

Source changes use source change IDs in program-scoped deep links. They do not pretend to be host `CaseRecord` IDs. The actual `WorkflowService`, `ActivityStore`, source adapters and `ExecutionService` remain untouched. There is no host HTTP adapter yet; later slices must wrap these existing services rather than build another runtime, approval engine or source store. The workflow catalog in this slice is descriptive presentation metadata, not a dispatcher or authority source.

The SDK investigation completes before the host pauses for exact review. Source plan state is separate from a reviewed host proposal. Scheduling is separate from physical testing, passing, engineering disposition, customer acceptance and case closure.

## Files changed

| Files | Purpose |
|---|---|
| `prompts/08_1_CONTROL_PLANE_SHELL.md` | Exact approved Phase 08.1 request |
| `docs/PHASE08_CONTROL_PLANE_REQUIREMENTS.md` | Full shared normative product requirements plus inspected interface findings |
| `docs/PHASE08_IMPLEMENTATION_PLAN.md` | Six slices, current scope and verification plan |
| `AGENTS.md`, `README.md` | Additive authorization, entry point and handoff |
| `mock_apps_ui/src/main.tsx` | Isolated lazy route branch; existing source app tree retained |
| `mock_apps_ui/src/control/data.tsx` | Typed source snapshot, freshness, presentation selectors and isolated story configuration |
| `mock_apps_ui/src/control/ui.tsx` | Shared components, accessible evidence dialog and provenance labels |
| `mock_apps_ui/src/control/app.tsx` | Product shell, navigation and contextual assistant preview |
| `mock_apps_ui/src/control/portfolio.tsx` | Portfolio, program directory, ranked queue, timeline and activity |
| `mock_apps_ui/src/control/program.tsx` | Program context, case list and source drill-downs |
| `mock_apps_ui/src/control/case.tsx` | Case, evidence, source options and recorded plans |
| `mock_apps_ui/src/control/previews.tsx` | Workflow, decisions, scenarios, knowledge and Operations destinations |
| `mock_apps_ui/src/control/style.css` | Scoped responsive visual system |
| `mock_apps_ui/e2e/control-plane.spec.ts` | Browser/HTTP acceptance, read-only receipt, reflow, focus and style isolation |
| `docs/phase08/screenshots/*.png` | New review images; existing screenshot artifacts restored unchanged |
| This handoff and `docs/phase08/verification.json` | Actual results and preservation inventory |

No backend/API, source fixture, agent, MCP, approval/execution, eval/grader, schema, dependency/lockfile or Vite/Playwright configuration was edited.

## Verification

All browser work is **scripted integration testing over local HTTP, with synthetic data and simulated identities; no AI run or actual human approval**. Existing source-app regressions intentionally perform their authorized synthetic mutations only in a unique isolated test DB. The new control-plane journey records GET-only access and equality of source portfolio payloads before/after navigation.

| Command / check | Actual result |
|---|---|
| `npm run build` in `mock_apps_ui/` | PASS: TypeScript and production Vite build; final build has separate lazy control JS/CSS and no chunk-size warning |
| `.venv/bin/python -m pytest tests/test_phase07_sources.py tests/test_phase06_execution.py -q --junitxml=.cache/phase08-1/source-regression.xml` | 84 passed, 22.43 s |
| `PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 --output .cache/phase07/phase08-1-offline` | 40/40 passed, hard gates PASS, zero critical failures; default runtime probes included |
| `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:e2e` in `mock_apps_ui/` | 25 passed, 2.8 min, including all 20 original browser regressions and the first five new control-plane tests |
| Final focused control-plane browser run after small visual/freshness fixes and added style-isolation check | 6 passed, 48.1 s. Combined with the original 20 regressions, 26 distinct browser tests passed (reruns are not added) |
| Read-only HTTP preview check through `http://127.0.0.1:5188/api/v1/programs` | 11 programs retrieved, including PRG-A17; port 18008 health ready |
| Token contrast calculation | Ink/white 17.93:1; secondary/off-white 7.22:1; warning text 6.10:1; positive status text 6.36:1 |
| Source reads during control journey | No business POSTs; source portfolio payload unchanged; receipt in `.cache/phase08-1/browser-read-receipt.json` |

The full browser report is archived at `.cache/phase08-1/full-browser-report/`. The final focused run uses the existing Playwright reporter. Source regression JUnit, contrast checks and preservation inventory are under `.cache/phase08-1/`. Offline eval artifacts are under `.cache/phase07/phase08-1-offline/`, as required by the existing eval CLI output guard.

Initial development attempts included a build issued from the repository root instead of the frontend, a test-file path issued from the wrong working directory, and an eval output directory rejected by its `.cache/phase07/` guard. These were corrected. Early new browser runs caught evidence focus restoration and rapid-filter transition bugs; both were fixed. A new test initially expected dollars in a controlled document that actually states integer USD cents; its assertion was corrected to the actual document. No existing test/grader expectations or scenario fixture was changed to pass.

Skipped: paid agents, paid semantic grading and any fresh six-case live smoke; full Coordinator/MCP/ProgramInvestigator suites and the unrelated full backend suite were not rerun because those implementations are unchanged. The selected 84 source/Phase 06 tests, unchanged 40-case hard gates, and full original browser workflow cover this slice's integration boundary. No separate component-test dependency was added; the new components are exercised in the real browser acceptance tests.

## Visual review

New images are under `docs/phase08/screenshots/`. Primary desktop Portfolio/Program/Case and evidence views were visually inspected at 1440×900 and 1280×800. Additional captures cover 1920×1080, 1024px, 640px and 375px widths, plus 200% CSS zoom at 1280×800. Narrow-width reflow is checked independently; CSS zoom is not a claim of testing every browser's native zoom behavior. All captured page widths pass the document-overflow check. The evidence table intentionally permits its own horizontal scrolling on narrow viewports.

Visual refinements from inspection: focus programs moved beside the ranked queue; reduced top spacing; removed a leaked legacy navigation inset; preserved visible owners; evidence dialog focus restored; assistant reserves layout space and its close control remains in view. Contrast calculations support the selected text/status tokens. This is not a comprehensive screen-reader certification.

- [Portfolio · 1440](phase08/screenshots/portfolio-1440.png)
- [Portfolio · 1280](phase08/screenshots/portfolio-1280.png)
- [Helios program · 1440](phase08/screenshots/program-1440.png)
- [CR-017 · 1280](phase08/screenshots/case-1280.png)
- [Evidence drawer · 1280](phase08/screenshots/evidence-1280.png)
- [Assistant · 1440](phase08/screenshots/assistant-1440.png)
- [Delivery preview · 1440](phase08/screenshots/delivery-1440.png)
- [Full portfolio · 1024](phase08/screenshots/portfolio-1024.png)
- [Narrow assistant · 375](phase08/screenshots/assistant-375.png)
- [200% CSS zoom](phase08/screenshots/case-200-percent-zoom.png)

## Preservation and limitations

A pre-edit hash inventory covered source code, five-app files, fixtures, Coordinator/eval implementations, existing Phase 07 artifacts and pre-existing demo DBs; existing screenshot artifacts were also backed up before running their capture-producing regressions. Those old screenshots were restored byte-for-byte. No Git commands, reset, cleanup of unrelated files, credential reads or external communication occurred.

**Working-DB audit exception:** the pre-existing port 8000 service returned HTTP 401 for one read-only portfolio-reader discovery request. Its existing denial handler automatically recorded one `GET / denied` audit at `2026-09-12T00:36:02.554975Z`; `.demo/enterprise.sqlite3` therefore is not byte-for-byte unchanged. The audit is retained. No business mutation request was sent to that service. The existing denial path restricts writes to audit infrastructure. No source business record, permission or fixture was deliberately edited, and no attempt was made to erase the audit or restart/reseed the working service. All subsequent verification and the offered preview use isolated storage.

The source API read model is transaction-consistent within `/portfolio`; the separate program/inventory/order reads do not form a distributed transaction. Five-minute display freshness is a UI age indicator, not renewed evidence eligibility. Option/document reads are on-demand and the global source status still exposes outages. Source timestamps stay intact. Preview namespaces and fixed scenario date are distinct from source authority.

No host run artifacts, local-file contents, private reasoning or fabricated agent traces are served. Operations' historical 4/6 failed smoke remains labeled failed; the two later targeted passes are explicitly attributed to the approved Phase 08 request, not a fresh scorecard. Connected host controls, interactive simulations, saved automation previews, chat and runtime/evals integration remain later-slice work.

## Local launch / resume

From the repository root, start an isolated source preview (this is the command actually used; it creates a unique `.demo/ui-e2e-*.sqlite3` and does not reset any existing DB):

```sh
.venv/bin/python scripts/serve_ui_test.py 18008
```

In a second terminal:

```sh
cd mock_apps_ui
MOCK_API_URL=http://127.0.0.1:18008 npm run dev -- --port 5188
```

- Control plane: <http://127.0.0.1:5188/control>
- Helios: <http://127.0.0.1:5188/control/programs/PRG-A17>
- CR-017: <http://127.0.0.1:5188/control/programs/PRG-A17/cases/CR-017>
- Existing source apps: <http://127.0.0.1:5188/>
- Isolated source docs/health: <http://127.0.0.1:18008/docs>, <http://127.0.0.1:18008/health>

The current preview DB is `.demo/ui-e2e-07805828281946a69df329beaa1226e1.sqlite3`. To resume that same persisted preview after stopping its supervisor, instead of initializing another test DB:

```sh
DEMO_MODE=true DEMO_DB="$PWD/.demo/ui-e2e-07805828281946a69df329beaa1226e1.sqlite3" \
  .venv/bin/mock-enterprise serve --port 18008
```

All services bind locally. The source API on 8000 was already running and remains untouched apart from its automatic denial audit. The preview is optional; no production hosting or new host API server was added.

## Next slice

08.2: connect the CR-017 workbench to the existing shared host services for proposal, exact trusted demo review, resume, execution and independent HTTP readback. Preserve the completed-SDK/paused-host distinction, exact manifests, role boundaries, idempotency, source versions, 40-case offline hard gates and failed historical live artifacts. Begin only after review of 08.1; do not implement later slices automatically.
