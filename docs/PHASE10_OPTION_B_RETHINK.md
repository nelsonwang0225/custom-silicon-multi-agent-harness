# Option B — connected presentation

User-approved implementation, 13 September 2026. This supersedes the previous design-review-only stop. The isolated review remains a historical concept artifact.

## Changes

- Shared control-plane shell: dark-to-light blue masthead, consistent spacing, existing Lucide navigation, gradient Concierge and responsive content width. Source-system styles remain outside this scope.
- Overview: capability-based persona headline, focused program ribbon, agents beside attention, verified source outcomes, focus programs and All programs links. Default attention excludes completed cases; All statuses and observed-state filters expose the full scoped case list.
- Agent workspace: Coordinator above all four specialists, actual task labels, separate run/status selection, explicit current/recorded state, qualified handoff and expandable activity details. Polling, inspectors, reduced motion and active-only branch animation remain intact.
- Programs: real health filters with All, gate/baseline/forecast/commitment context, customer request titles, case status/type filters, source dependencies and drilldowns.
- Cases: distinct coverage, scope/reuse, yield/site, supply and source-event visuals; prominent existing actions; concise recommendations with agent-action sections and expanded originals; source checks and exact details available on expansion.
- Decisions, Scenarios, Workflows, Knowledge, Operations and presenter controls: business-first hierarchy, observed-record filters, source provenance and concise summaries. Knowledge separates governing material, request context and precedent. Operations starts with recorded outcome and source confirmation.
- Concierge: contextual evidence and next-action presentation; existing draft and structured confirmation boundaries retained.

## Preserved business meaning

CR-017 keeps operator preparation, Engineering approval, explicit lab handoff and its current shortened downstream completion path. CR-019 scope/reuse counts remain pending until completed investigation, and its endpoint is Operations intake. QE-004 completes recovery coordination while Quality disposition remains external; $1.4M remains the existing synthetic yield-shortfall exposure, not realized savings. QE-011 retains a touchless standard investigation handoff. DR-009 retains direct exact Program Owner commitment review. No extra human gate or source write has been added by the presentation.

All UI state comes from existing source/host records. The prototype’s example-state/presenter exploration controls were not imported. Persona labels change emphasis; server capabilities continue to determine actions and navigation.

## Verification

- `npm run build` in `mock_apps_ui`: passed (includes TypeScript).
- `npx playwright test --config playwright.rethink.config.ts`: five tests passed in 1.3 minutes, including completed-investigation operator forms, real All-status filtering, freshness gating, persona capability navigation and 12 loaded routes at 1920×1080, 1440×900 and 1280×800. The first attempt exposed test-fixture teardown/reload assumptions; both were corrected without changing product identity behavior.
- CR-017 and QE-004: deterministic investigations produced real isolated drafts. Pre-filled recommendations remained editable; explicit submission buttons were enabled; original descriptions, evidence disclosures and Manufacturing source receipts were accessible. No approval or execution was submitted. Recommendation cards use two columns on desktop with readable action text and full scope disclosures.
- Agent workspace: nine deterministic display checks passed for run/status isolation, roster, active branches and inspector selection.
- Utilities: fourteen focused read-only interaction checks passed for actual Knowledge categories/search, disclosure focus, workflow filters, Operations metadata and run detail.
- Read-only observation of the working app: five case routes at 1440, 1280 and 390px; no horizontal overflow or uncaught errors. Utilities were inspected after source loading at 1440 and 600px. No working-demo investigation, approval, execution or reset was issued.
- New browser tests use isolated source/metadata storage and deterministic harness doubles. Speech is disabled and the autonomous opening is suppressed in display checks.

Responsive screenshots and test reports are in `.cache/rethink-implementation/`. The implementation does not claim a paid-model or production end-to-end verification.
