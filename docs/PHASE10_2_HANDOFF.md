# Phase 10.2 — Visual Agent workspace handoff

Implemented the agent-centered stage in the existing Stratos application. The Coordinator and four existing specialists now show scoped active/recorded work, categorical states, parallel participation and a separate human/external handoff. Business inspectors retain run attribution and evidence versions; Explain in Concierge creates an editable unsent draft. The wider workspace sits left of Needs attention, within the existing light-blue shell.

**Choice: Agent stage.** Its focal Coordinator and compact specialist row explain collaboration more clearly than an equal-weight ensemble. Two local React/Lucide concepts were explored and inspected. Visualize's skill was available, but no callable Visualize tool was exposed; the requested local prototype fallback was used. Both previews are retained as documentation, and only the stage ships in the app.

- [Normative design, exact telemetry mapping and limitations](PHASE10_2_AGENT_WORKSPACE.md)
- [Concepts, final fixture screenshots and visual inspection notes](screenshots/phase10-2/README.md)
- [Exact commands and verification record](PHASE10_2_VERIFICATION.json)
- [Local preview and restart instructions](DEMO_RUNBOOK.md#phase-102-agent-workspace-preview)

## Verification

| Check | Result |
|---|---|
| Full coordinator suite, including workflows, exact approval/execution, Concierge, Operations, reset and persona access | **779 passed**; includes 15 new adapter tests |
| Focused adapter suite | **15 passed**, overlaps the coordinator total |
| Current offline eval dataset | **112/112 passed**, hard gates PASS, including original Phase 07 cases |
| New Agent workspace browser suite | **12 passed** |
| Existing persona browser suite | **8 passed** |
| Existing connected Concierge browser suite | **2 passed** |
| Existing four-case reset/restart browser journey | **1 passed** |
| Typecheck and production build | **PASS** |
| OpenAPI comparison | **PASS**; all prior paths/models unchanged; new adapter path/models additive |
| Local concept reproduction | Two concepts render; no browser page errors |

Browser verification totals **23 tests**, with separate isolated fixture storage and mocked speech interactions. The new suite covers idle, two parallel specialists, human handoff, preserved partial failure findings, missing/stale telemetry, concurrent runs, CR-019 intake/lab separation, reader restrictions, exact review-version mismatch, unsent/once-only drafts, hidden/completed polling, persona/reset clearing and delayed response rejection. Screens at 1440×900, 1280×800, 390×844, enlarged text and reduced motion were actually opened and inspected. These are **scripted integration tests**, not paid AI runs or actual human approval evidence.

Initial checks found and resolved stylesheet ordering, stage height, narrow inspector action wrapping and incorrect aggregate completion labels. The first browser setup used the wrong invocation ID prefix; it now uses the existing `ui_` contract. The reset test must reselect its operator after the existing identity-clearing boundary, and browser fixture setup now survives a worker restart without creating a duplicate proposal. None of these fixes weakens an assertion about business authority.

The broader Concierge journey found a pre-existing React StrictMode lifecycle issue in send/confirmation: cleanup marked the component unmounted, but effect setup did not re-enable it during development remount. Both setup guards now reset correctly, while actual unmount still prevents late updates. Existing Concierge/reset tests were aligned with Phase 10.1: unauthorized confirmations are absent, approval is previewed by its owning human persona, and protected navigation uses explicit persona selection with in-app links. The connected four-workflow journey and reset/restart now pass.

## Changed implementation

- Host: `control_host/agent_workspace.py` adds the read-only projection; `server.py` attaches it. Generated OpenAPI and frontend schema include the additive endpoint. No source probes, key reads or model/write calls on rendering or selection.
- Frontend: `agent-workspace.tsx`, `agent-workspace-data.ts` and scoped CSS implement the stage, inspector and polling. `agent-roles.ts` retains the original identities; `agent-activity.tsx` preserves existing imports/detail consumers. Overview ordering changes locally in `portfolio.tsx`.
- Concierge: app/masthead request metadata and assistant draft handling support scoped Explain without sending or repeated append; two lifecycle guards in `concierge-chat.tsx` correct the observed development issue.
- Tests: new adapter/browser suites and browser config; existing Concierge/reset journey setup/permission expectations updated to the current access contract.
- Documentation: current requirements, API/acceptance notes, AGENTS, README, runbook, both concepts, 15 fixture screenshots and this handoff. The verification JSON lists the individual files.

Working demo databases and historical live/eval artifacts were not reset or altered. Sixteen older screenshots regenerated by browser regressions were saved under `.cache/phase10-2/regression-captures/` and restored from verified originals. Model prompts, SDK orchestration, MCP/source permissions, source fixtures, approval/execution services, graders and workflow definitions remain unchanged. No Git operation was performed.

## Preview, limits and stop

[Open the isolated preview](http://127.0.0.1:5203/control/overview). It serves current code with deterministic SDK doubles and one recorded CR-017 result awaiting Engineering review, prepared through the existing HTTP investigation route. A fresh fixture directory starts in known idle state. The separate [illustrative concept comparison](http://127.0.0.1:5205/preview.html) is also available while its local server runs. Both launch commands are recorded in the runbook; neither substitutes fake live intelligence into the working demo.

Observation freshness is checkpoint-level: a long invocation without a new checkpoint becomes uncertain after 90 seconds. Completed selections stop recurring workspace polling; visibility return, meaningful shared host changes and explicit refresh can re-read. Only installed A17 workflows have connected agent telemetry. No paid model health, model-quality result or continuously online-agent claim is implied.

Paid live runs, semantic model grading, real microphone/provider use, standalone source/MCP suites and the full five-source UI suite were not rerun in 10.2. The changed host/UX boundaries were exercised through the full coordinator suite, all offline eval gates, and targeted real-HTTP browser journeys. Stop at Phase 10.2; later walkthrough feedback may authorize targeted refinements.
