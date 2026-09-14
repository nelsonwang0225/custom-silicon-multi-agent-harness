# Phase 08 — implementation plan

**Current status:** Phase 08.6 and integrated verification are complete; see the
[final Phase 08 handoff](PHASE08_6_HANDOFF.md). The explicit 08.4A/B/C and 08.5
requests superseded the simulation/CR-017-only scope in the historical plan below.
All four workflows, Concierge, configuration, Decisions and Operations are connected.
Saved background triggers remain inactive. Phase 09 has not started.

Current visual direction: [darker blue and minimalist refinement](PHASE08_1_MINIMAL_DESIGN_HANDOFF.md), superseding the preceding lighter palette and nested Overview containers. This remains within 08.1.

Each slice stops for review. The explicit [08.3 request](../prompts/08_3_WORKFLOWS_AUTOMATIONS.md) authorizes the current Workflows & Automations slice. Earlier sections describe their historical scope; see the [08.3 handoff](PHASE08_3_WORKFLOWS_HANDOFF.md) for current behavior and verification.

| Slice | Deliverables | Boundary / exit |
|---|---|---|
| 08.1 | Shared requirements, scoped tokens/components, shell, Portfolio → Program → Case → evidence, useful secondary previews, Stratos Concierge with browser dictation input | Read-only source HTTP; responsive/keyboard/browser verification; review visual direction |
| 08.2 | Connected CR-017 workbench; thin typed host adapters | Reuse WorkflowService, ActivityStore, source adapters and ExecutionService; preserve exact Phase 06 identities, manifest and independent readback |
| 08.3 | Catalog, manual invocation, saved schedule/event/condition previews | Catalog grants no authority; no active scheduler |
| 08.4 | Interactive scenario stories 1A, 2, 3 and lifecycle previews | Isolated simulation namespace; no touchless execution authority |
| 08.5 | Contextual text chat | Same governed host services for supported CR-017; modes explicit; no second runtime |
| 08.6 | Operations/evals visibility and integrated QA | Recorded vs fresh results explicit; preserve 40-case offline gates and failed 4/6 historical smoke |

## 08.1 design and implementation

1. Persist normative requirements and this plan before implementation.
2. Add `/control/*` alongside all existing routes. Mount a read-only control data provider only on that branch; use existing typed source API adapter with fixed reader persona. Keep legacy provider and CSS untouched.
3. Use shared lighter-blue-to-white gradients for masthead, Overview summary and larger Stratos Concierge. Retain native large typography, plain semantic StatusText, viewport reflow and centered accessible evidence/agent dialogs. Canonical landing is /control/overview with /overview, /portfolio, /control and /control/portfolio compatibility aliases. Preserve all source-app routes.
4. Give Overview a fixed explicit available focus-program scope, one visual summary with real counts/health mix/next baseline gate, short program/agent tiles and three attention entries. Move detailed filters to Programs. Global masthead search groups loaded accessible record metadata and existing definitions; always offer the same concierge with safe query append/no auto-send. Add source-backed alerts with session read markers and clearly simulated demo-profile access; fixed reader HTTP authority remains unchanged. Profile changes reset presentation state. Preserve mocked-verifiable voice input; replies/actions remain Preview and real integration remains 08.5.
5. Build program context, gates, risks, cases and technical/validation/supply/commitment source links. Keep illustrative cases separate. Build CR-017 source outcome, evidence applicability, before/after requirements, recorded plan/decision summaries and activity. Do not manufacture host runtime status.
6. Build useful workflow, decision, scenario, knowledge and operations preview/detail destinations. Use only static descriptive catalog configuration and clearly labeled illustrative data; no business persistence or model calls.
7. Add browser acceptance coverage for navigation, filters/reload/back, source failures/stale state, evidence metadata, modal focus, all source routes and GET-only control access. Run existing browser regressions against isolated test backend and preserve prior screenshots.
8. Capture and inspect 1440×900 and 1280×800 plus 1920×1080, 1024px and reflow. Verify TypeScript/build and source/backend regressions offline. Record preservation hashes and actual checks in the slice handoff.

## Delivery truth

08.1 supports current source reads only. Host investigation/proposal/review/execution, recurring configuration and chat are not wired. Stratos Concierge replies/actions and other capability surfaces say Preview only. Browser speech support is detected at runtime; live recognition is unverified until a user chooses to test it. Audio may be processed by the browser provider. Illustrative scenario descriptions are not executed simulations or traces. Backend failure is unavailable/stale, never substituted with preview success. No source schema, fixture, business permission, SDK orchestration or approval logic changes are planned.

## Phase 08.2 implementation

Connected CR-017, exact Decisions, trusted demo review, governed execution and
readback are implemented; see [handoff](PHASE08_2_CONNECTED_HANDOFF.md). The
standalone host reuses existing application services and checkpoints. All other
workflow cards, schedules, scenarios and freeform Concierge retain their prior
preview boundaries. The next planned slice is 08.3: catalog/manual invocation
and saved schedule/event/condition previews, without an active scheduler. It
requires the next explicit user request; no 08.3 work is included here.

## Phase 08.2.1 downstream implementation

[CR-017 downstream validation](PHASE08_2_1_DOWNSTREAM_HANDOFF.md) extends the
connected workbench with source-owned synthetic lab completion, explicit existing
Coordinator/Validation & Evidence reassessment, and a distinct immutable engineering
evidence review. Existing scheduling/Planner approval authority and visual design
are preserved. Validation complete retains pending customer acceptance. The source
upgrade is explicit and additive; no existing demo data is reset. Stop at 08.2.1.
Next: 08.3 catalog, manual invocation, saved schedule/event/condition previews;
no active scheduler, and no implementation until the next explicit request.

## Phase 08.3 implementation

The registry-derived catalog, shared manual CR-017 invocation, real run detail and
saved automation configurations are implemented. The one Connected and twelve
Preview definitions accurately distinguish existing runtime from product concepts.
There are no interactive Simulated workflows yet. Schedule/event/condition/chat
configurations do not execute. Existing exact approval, governed execution and
downstream evidence review are unchanged. See [handoff](PHASE08_3_WORKFLOWS_HANDOFF.md).
Stop after 08.3. Next: explicit 08.4 interactive scenario simulations in isolated
presentation state, with no additional workflow backend or authority.
