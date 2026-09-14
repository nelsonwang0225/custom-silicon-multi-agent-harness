# Five source-system redesign

September 13, 2026. Implemented the five source applications as distinct enterprise tools. The main Stratos agentic control plane was not redesigned.

[Before / after gallery](screenshots/source-redesign/index.html) · [Approved request](../prompts/10_SOURCE_SYSTEM_REDESIGN.md)

## Research and design

Category conventions informed these designs; no vendor interface, logo or asset was copied. Shared typography, icons and neutral surfaces establish the Stratos family. Each application has its own operational structure.

| References | Convention studied | Design interpretation |
|---|---|---|
| [Teamcenter Active Workspace](https://blogs.sw.siemens.com/teamcenter/navigate-active-workspace/), [Windchill structure view](https://support.ptc.com/help/windchill/plus/r13.1.2.0/en/Windchill_Help_Center/prodfamily/PFSBTabAbout.html) | Product structure, controlled objects and related records | PLM hierarchy, change worklist and applicability chain |
| [NI SystemLink lab operations](https://www.ni.com/content/dam/web/pdfs/niconnect/2025/connectivity/Streamline_Your_Lab_Operations_with_NI_SystemLink_Software.pdf), [result reporting](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q0000019fmmCAA&l=en-US) | Resources, work scheduling and result detail | TestOps operational summary, job lifecycle and separate coverage/results |
| [Opcenter Semiconductor](https://blogs.sw.siemens.com/opcenter/whats-new-in-siemens-opcenter-execution-semiconductor-2410/), [Applied SmartFactory](https://appliedsmartfactory.com/semiconductor-blog/manufacturing-execution/cim-solution/) | Lot tracking, restrictions and quality operations | MES lot registers, unmistakable holds, yield and investigation records |
| [SAP Fiori floorplans](https://www.sap.com/design-system/fiori-design-web/v1-38/page-types/floorplan-overview), [table features](https://www.sap.com/design-system/fiori-design-web/v1-120/discover/frameworks/sap-fiori-elements/tables-and-lists/table-features-sap-fiori-elements) | Filtered lists, object headers, line items and contextual actions | ERP order book, object page and supply accounting |
| [Planisware work management](https://planisware.com/capabilities/work-management) | Planning, ownership, milestones and connected work | ProgramOps timeline, dependencies and recovery work |

These are interpretations of public product material, not claims of equivalent capabilities. The frontend exposes only existing supported source data.

## Implemented applications

**Stratos PLM — Product Lifecycle & Engineering Change.** Added a product/configuration hierarchy alongside the filtered change worklist. CR-017 and CR-019 have object headers, applicability relationships and sections for requirements, configuration, scope, plans, documents and history. Controlled documents are searchable. Existing draft, revision and engineering-decision contracts remain intact.

**Stratos TestOps — Validation & Qualification.** The landing page prioritizes real scheduled jobs, execution/result observations, upcoming work, samples and resources. Job detail shows sample/configuration, procedure, environment, schedule and lifecycle. Booking, physical execution, available results, engineering review and customer acceptance remain distinct. Coverage/evidence, execution history and CR-019 intake records remain independently inspectable.

**Stratos MES — Manufacturing & Quality.** Manufacturing navigation and a restrained dark sidebar frame unit/lot registers. QE-004 foregrounds LOT-B-204: 250 held, zero eligible, 80% first-pass yield versus comparable 96% baseline, −16 percentage points. Site observations remain separate from the unestablished root cause. Material, investigation, recovery decisions, downstream work and traceability have dedicated sections. Missing QE-011 data never substitutes QE-004.

**Stratos ERP — Commercial, Orders & Supply.** Added an order-book presentation, business-object headers, customer/program relationships, line items and commitment sections. DR-009 preserves 1,000 physical − 250 held − 150 allocated = 600 eligible, with demand 800 and gap 200. Original obligation and governed release commitments stay separate. **DR-009 belongs to ORD-HEL-800; ORD-1204 remains the separate 100-unit CR-017 order.** The prompt's example did not override these existing facts.

**Stratos ProgramOps — Program Planning & Readiness.** Portfolio filters expose status, accountable owners and next milestones. PRG-A17's timeline uses actual UTC milestone dates, with separate baseline diamonds and forecast circles. The register, dependencies, implementation links and recovery work remain planning records. No unsupported project phase dates or decorative completion percentages were added.

## Shared UX and names

Names changed only in source UI labels. Existing `/engineering`, `/validation`, `/manufacturing`, `/erp` and `/programs` routes remain. Internal names, IDs and persistence keys were not renamed.

Tables use prioritized columns, tabular numerals, thin separators and readable density. Status uses an icon plus text; HOLD receives stronger amber treatment. Source-only CSS preserves control-plane styling. Keyboard focus and reduced-motion support remain. Existing inline evidence disclosures and document pages are retained rather than introducing an unsupported modal workflow.

## Files changed

Application files under `mock_apps_ui/src/`:

- Shared: `source-app.tsx`, `ui.tsx`, new `source-suite.css`.
- PLM: `engineering.tsx`, new `source-plm.css`.
- TestOps: `validation.tsx`, `lab-portfolio.tsx`, `validation-intakes.tsx`, new `source-testops.css`.
- MES/ERP: `operations.tsx`, `quality-source.tsx`, `delivery-source.tsx`, new `source-operations.css`.
- ProgramOps: `programs.tsx`, new `source-programops.css`.
- Display labels: `assessment-form.tsx`, `lab-completion.tsx`.

Verification uses updated source/standard/quality/delivery browser selectors plus new `e2e-sources/source-redesign.spec.ts` and `playwright.sources.config.ts`. The approved prompt, AGENTS authorization, report and screenshot gallery document this scope.

## Preservation

Pre/post SHA-256 checks covered 215 protected files across backend source, fixtures, API client/data/schema, OpenAPI and the main control-plane implementation. **Zero protected files changed.** No runtime dependencies or model calls were added. Source ownership, approval rules, agents, MCP, RAG, calculations, reset and automation behavior remain unchanged.

All verification writes use isolated synthetic databases. The working demo was not reset.

## Verification results

All checks used isolated synthetic state and deterministic model/speech doubles. No paid model calls or real microphone sessions were used. Browser workflow tests are **scripted integration testing**, not live AI runs or actual human approvals.

| Check | Exact result | Evidence |
|---|---|---|
| Source/API Python regressions | **507 passed**, 0 failed/errors/skipped; 194.12 s | [Log](../.cache/source-redesign/source-tests.log), [JUnit](../.cache/source-redesign/source-tests.xml) |
| Scoped MCP regressions | **56 passed**, 0 failed/errors/skipped; 13.29 s | [Log](../.cache/source-redesign/mcp-tests.log), [JUnit](../.cache/source-redesign/mcp-tests.xml) |
| Full coordinator regressions | **848 passed, 18 failed**, 0 errors/skipped; 552.28 s | [Log](../.cache/source-redesign/coordinator-tests.log), [JUnit](../.cache/source-redesign/coordinator-tests.xml) |
| Source browser suite and pure view-model checks | **24 passed**; 3.3 min | [Log](../.cache/source-redesign/source-browser.log) |
| Source redesign desktop suite | **18 passed**; 2.3 min | [Log](../.cache/source-redesign/redesign-browser.log) |
| CR-019 connected browser regression | **2 passed**; 22.9 s | [Log](../.cache/source-redesign/standard-browser.log) |
| QE-004 connected browser regression | **1 passed**; 29.7 s | [Log](../.cache/source-redesign/quality-browser-r7.log) |
| DR-009 connected browser regression | **1 passed**; 38.2 s | [Log](../.cache/source-redesign/delivery-browser.log) |
| TypeScript and frontend production build | **Passed** | [Build log](../.cache/source-redesign/build.log) |
| Protected-file comparison | **215 checked; 0 changed** | [Manifest result](../.cache/source-redesign/protected-after.json) |

**46 browser/view-model checks passed in total.** The project has no separate component-test runner; the existing pure view-model checks and browser interaction suites were used. The broader coordinator suite is not green, so this report does not claim a completely passing end-to-end product regression.

### Remaining coordinator failures

These tests execute unchanged backend code independently of source UI rendering. The observed failures were classified using the final tracebacks and retained test artifacts:

- **16 tests:** helpers still assume investigation automatically creates a review proposal or bypasses the current explicit Program Operator submission. They fail on missing proposal/action identifiers or the existing `OPERATOR_ESCALATION_REQUIRED` / review-conflict response. The current QE-004 browser flow passes when it follows operator submission, exact owner approval and execution/readback.
- **1 test:** an exact-copy assertion expects “evidence available”; the existing response says “Applicable workload evidence is available.”
- **1 A–Q evaluation test:** the fresh Overview question returns `CHAT_INVALID_OUTPUT`. The unchanged Concierge read projection dereferences CR-019 eligibility before that investigation has populated it. Its early abort accounts for the downstream A–Q violations; those were not separate successful observations.

The [detailed failure manifest](SOURCE_SYSTEM_REDESIGN_VERIFICATION.json) lists all 18 test IDs, tracebacks and source references. These 16 setup failures do not verify the later behavior their tests intended to exercise.

No backend corrections or weakened business assertions were introduced to make these tests pass. A focused follow-up should fix the unassessed-eligibility handling and reconcile old test helpers with the current submission workflow.

### Browser coverage and screenshots

The new desktop suite checks all five source applications at **1440×900, 1920×1080 and 1280×800**, including PLM CR-017/CR-019, TestOps jobs/results/intakes, MES LOT-B-204/QE-004, ERP ORD-1204/supply, and ProgramOps PRG-A17/milestones/dependencies. It checks page overflow, source facts, navigation, filters, disclosures, document preview, keyboard focus and loading/error recovery. Inspected screenshots showed no blocking clipping or page overflow. Wide tables retain local scrolling.

Existing scripted browser flows exercise CR-017 source review/scheduling/readback, CR-019 intake creation/reuse, QE-004 operator submission/owner approval/recovery readback, and DR-009 exact commitment/Planner linking. Protected holds, allocations, source ownership and role denials remain asserted. Test selectors were updated for changed labels and layout without relaxing those business checks.

The [gallery](screenshots/source-redesign/index.html) contains **10 before/after pairs**: landing and representative detail views for every app, captured against the same isolated baseline. Additional [responsive screenshots](screenshots/source-redesign/responsive/) and connected-flow screenshots are retained alongside it.

### QE-011 source event: partial verification

The isolated automatic-entry attempt returned `AUTONOMOUS_EVENT_FAILED`; its preparation retry returned `DEMO_BASELINE_INVALID`. No autonomous run was created. That host path therefore remains **unverified end to end** in this task, and its failure was not hidden or fixed by changing backend behavior.

To inspect the requested source UI, the existing developer-only publisher was invoked on a separate copied database. Exact HTTP reads confirmed the published `quality_exception_created` event for **QE-011 / LOT-B-219**, with a matching context digest. Both the quality record and lot page were captured and inspected at all three sizes: 100 held, 0 eligible, 88% observed versus 96% comparable baseline, no QE-004 leakage, no browser errors or writes, and unchanged business readbacks. All processes owned by that supplemental check were stopped.

This is **scripted source publication; not a successful autonomous-dispatch test**. See the [QE-011 provenance and screenshot checks](screenshots/source-redesign/qe011/validation.json).

### Commands run

From the repository root, the completed Python suites used:

```sh
.venv/bin/python -m pytest tests --basetemp=.cache/source-redesign/pytest-source -o tmp_path_retention_policy=failed --junitxml=.cache/source-redesign/source-tests.xml
PYTHONPATH=src:. coordinator/.venv/bin/python -m pytest coordinator/tests -c coordinator/pyproject.toml --basetemp=.cache/source-redesign/pytest-coordinator -o tmp_path_retention_policy=failed --junitxml=.cache/source-redesign/coordinator-tests.xml --tb=short -rA
PYTHONPATH=src:. mcp_server/.venv/bin/python -m pytest mcp_server/tests -c mcp_server/pyproject.toml --basetemp=.cache/source-redesign/pytest-mcp -o tmp_path_retention_policy=failed --junitxml=.cache/source-redesign/mcp-tests.xml --tb=short -rA
```

From `mock_apps_ui/`, the checks included:

```sh
npm run build  # Includes tsc --noEmit before Vite
PLAYWRIGHT_JSON_OUTPUT_NAME=../.cache/source-redesign/source-browser.json npx playwright test e2e/workflow.spec.ts e2e/portfolio.spec.ts e2e/enhancements.spec.ts e2e/review.spec.ts e2e/control-view-model.spec.ts --reporter=list,json --trace=off
SOURCE_UI_URL=http://127.0.0.1:5241 PLAYWRIGHT_JSON_OUTPUT_NAME=../.cache/source-redesign/redesign-browser.json npx playwright test --config playwright.sources.config.ts --reporter=list,json --trace=off
```

The standard, quality and delivery suites used their existing `playwright.standard.config.ts`, `playwright.quality.config.ts` and `playwright.delivery.config.ts` configurations. Exact final quality/delivery commands and earlier attempts are recorded in the [verification manifest](../.cache/source-redesign/quality-delivery-verification.json).

### Storage interruption and cleanup

Earlier regression attempts hit a full disk and could not reliably write databases/reports. Those attempts are preserved as storage failures and are not counted as completed checks. After explicit user authorization, 172 disposable browser-test database/sidecar files (about 598 MiB) were removed only from `.demo/ui-e2e-*` and `.cache/phase08-4a/browser/`, excluding open files. Working demo databases, code, screenshots and historical evaluation reports were preserved. See the [cleanup record](../.cache/source-redesign/authorized-cleanup.json). The final results above come from completed reruns after storage was available.

## Limitations and follow-up

Desktop enterprise use remains the target. Wide registers use local table scrolling where necessary. Missing source procedure versions, execution results or quality events remain unavailable rather than inferred. Timelines represent source milestones, not a new scheduling engine. Long source-authored evidence and audit details are preserved behind secondary sections.

Potential follow-up: richer saved views or contextual object side panels backed by documented data contracts. Neither was added for cosmetic effect.
