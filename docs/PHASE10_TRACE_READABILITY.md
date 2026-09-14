# Phase 10: readable agent traceability

## User request

Make agent findings, activity, sources, evidence, actions, and evaluations understandable in concise plain English across the existing app.

## Presentation changes

- Case findings and Agent Workspace inspectors explain the assigned task, recorded finding, and sources consulted. Completed work uses the existing green completion treatment.
- Source references lead with business descriptions such as “Change request” and “Program milestone.” Original tool names, receipt IDs, and versions remain in expandable details.
- Operations separates “What each agent did,” “What happened,” “Sources the agents consulted,” and “Actions taken and confirmed.” Saving an action and independently confirming its source record are explicitly different outcomes.
- Knowledge search and run evidence explain the search purpose, discovered versus cited documents, exact-source verification, and historical applicability. Search profiles, hashes, ranking metadata, and exact passages remain available.
- Policy checks describe the business constraint being checked. Workflow history, Concierge context, and evidence mismatch explanations use readable labels; exact approval bindings and action comparisons remain inspectable.
- Evaluation pages explain scenarios, required-check failures, and skipped answer-quality reviews. Historical failures and their original codes remain visible. Unknown results are not relabeled as passes or failures.
- Long recorded findings show a concise excerpt with the full original available. Paragraph spacing, wrapping, and independent card heights improve scanning.

## Evidence and authority safeguards

The shared `trace-language.ts` and `traceability.tsx` helpers change presentation only. They do not create conclusions, grant permissions, change source records, or call models.

The deterministic CR-019 fixture records the same generic summary for each specialist. When complete policy checks were saved with that exact run, the UI can show a role-specific explanation explicitly attributed to those saved checks. Failed tasks, another run's checks, and incomplete check sets do not receive that explanation. The original summary remains available.

Current policy checks stay separate from the checks saved with an investigation. Existing source-state, persona, exact approval, and independent readback boundaries are unchanged. The standard-case completion headline is conditional on a verified handoff; a pending handoff cannot say “Workflow complete.”

## Verification

All browser investigations used the repository's isolated deterministic test servers and mocked speech. The working demo was not reset, and no paid model calls were made.

Commands run from `mock_apps_ui/`:

```text
npm run build
./node_modules/.bin/playwright test -c playwright.polish.config.ts -g 'traceability|current-source visuals|a new standard investigation|another case running'
./node_modules/.bin/playwright test -c playwright.knowledge.config.ts
./node_modules/.bin/playwright test -c playwright.workspace.config.ts -g 'completed human handoff|failed invocation|persona switch|narrow, enlarged'
```

Results: production build and TypeScript check passed; 7 focused polish/traceability tests passed, 4 Knowledge tests passed, and 4 focused Workspace tests passed (15 total). Copy assertions were updated for the intentional wording changes. An existing history-link assertion was corrected to respect the viewer's scoped case-activity route.

Browser coverage includes all four primary cases; same-run evidence binding; incomplete, unknown, failed, and unverified states; historical evaluation failures; source details; profile isolation; document retrieval and exact verification; and Agent Workspace inspectors.

Layouts were checked at 1440×900, 1920×1080, and 1280×800. Existing Knowledge and Workspace checks also cover narrow layouts. Findings, confirmed actions, evaluations, and document previews were visually inspected. Relevant screenshots are in `docs/screenshots/trace-readability/` and `docs/screenshots/phase10-knowledge/`.

The full backend/evaluation regression suites and paid runtime were not rerun for these presentation-only changes. Existing source-system record and audit views were reviewed; their business data and mutation behavior were preserved.
