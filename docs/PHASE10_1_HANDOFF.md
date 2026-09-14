# Phase 10.1 — Persona-aware navigation, views and actions

Implemented the [approved request](../prompts/10_1_PERSONA_ACCESS.md) in the existing repository. The four personas now have distinct navigation, queues, scenarios and permitted action controls. The host supplies the capability projection and enforces protected data routes; changing persona clears scoped UI/chat state. Source ownership and exact approvals/execution remain in their existing services.

Read the [normative authority and presentation matrix](PHASE10_1_PERSONA_ACCESS.md), [updated runbook](DEMO_RUNBOOK.md), [six-screen visual review](screenshots/phase10-1/README.md), and [verification record](PHASE10_1_VERIFICATION.json).

## Implemented behavior

- Unknown profile/capability scope fails closed; no automatic elevated login. Capability loading does not expose restricted tabs/actions.
- Missing permission removes navigation, buttons, forms and alternate action cards. Existing readiness checks keep permitted but premature actions disabled. Case facts, evidence and the responsible role remain visible.
- Engineering's queue contains CR-017 plan/evidence decisions; Program Owner's contains QE/DR decisions. Operator tracks all; viewer has no dedicated queue. Explicit scenario IDs provide technical/business filtering.
- Source health and program facts are the same across personas. Current reviewable counts and attention ordering reflect the selected actor.
- Scoped case reads preserve outcomes and supporting evidence while removing trace IDs and non-operator catalog/configuration data. Protected Workflows, run/Operations and queue endpoints cannot be bypassed with guessed URLs.
- Concierge uses permitted context and same-owner history before model dispatch. Unauthorized actions receive explanation/scoped navigation without tokens or workflow admission. Reads, cancellation and exact confirmations require the original actor. Both preview and successful confirmation cards filter links. Even operator cannot use another actor's Operations transcript as a Concierge context.
- Explicit persona switching remounts scoped providers, closes dialogs, stops timers/voice, discards drafts/action previews/retry IDs and rejects late old responses. It does not revoke approvals or cancel admitted runs.
- Demo reset remains behind the operator presentation and separate existing maintenance gate/CLI. Source apps retain their independent demo selectors and API permissions.

## Authority found in code

The scope is presentation plus access enforcement, not a new role architecture. In particular, the pre-existing CR-017 case endpoint admits Program Owner investigation; Engineering can already investigate QE/DR; Engineering can already save automation metadata. These paths are preserved and explicitly documented even though their corresponding general workspace or scenario category is hidden. Generic workflow invocation retains its existing operator/engineering restriction.

CR-019 still uses the bounded standard intake without a new human approval. Engineering alone reviews CR-017 plans and, separately, exact downstream evidence. Program Owner alone reviews QE recovery metadata and DR commitment. Existing allowed execution profiles retain exact source/current-plan checks and independent readback. No role gains lot release, technical/customer acceptance, allocation, background execution or agent permission.

## Verification

| Check | Final result |
|---|---|
| Source pytest | 483 passed |
| Coordinator pytest, including host/workflows/Concierge/Operations/reset/personas | 764 passed |
| MCP pytest | 56 passed |
| Current offline eval dataset | 112/112 passed; hard gates PASS |
| Persona browser at 1440×900 / 1280×800, mocked speech | 8 passed |
| Existing five-source-app browser regressions | 14 passed |
| Typecheck / production build / generated host schema comparison | PASS |
| Final targeted Concierge/Operations/persona rerun after transcript-context guard | 42 passed, overlaps coordinator total |

Final results and commands are recorded in `PHASE10_1_VERIFICATION.json`. Suites use isolated storage and deterministic model doubles; browser speech is mocked. They are **scripted integration testing**, not an AI run or proof of actual human approval. Overlapping targeted reruns and embedded evaluation probes are not added to suite totals.

The original 40-case Phase 07 suite and all current expanded hard gates remain. The Concierge evaluation adapter now uses the proper owning human persona for positive approval previews and sends the same profile on polling; case definitions, expected outcomes and graders are unchanged. Wrong-role confirmation remains denied.

Initial failures were resolved: legacy tests made anonymous protected-workspace reads or reused an operator preview for a human approval; these now select the correct explicit identity without weakening business assertions. The first combined pytest invocation had a module/fixture collection collision, so source, MCP and coordinator suites ran separately. Browser launch used the existing installed Chromium path. Two added browser checks needed test-harness corrections: the delivery screenshot targeted a zero-size anchor, and the speech mock initially omitted the audio-start event. Final checks use a visible viewport and explicit mocked speech events. A targeted Operations test also exposed a pre-existing race between runtime completion and automatic proposal preparation; it now waits for the exact proposal before attempting its unchanged review/execution assertions.

## Changed files and preservation

The [verification record](PHASE10_1_VERIFICATION.json) lists changed files. Core additions are `control_host/access.py`, the generated host schema, `control/access.tsx`, new persona API/browser regressions, this contract and screenshots. Existing host/Concierge/Operations projections and control UI call sites consume them. Exact source APIs, fixtures, model prompts, runtime orchestration, graders and business execution services were not changed.

No working walkthrough database was reset or migrated. Existing live/evaluation artifacts are retained. The source browser suite's 33 regenerated legacy screenshots were saved in `.cache/phase10-1/source-captures/` and the originals restored from the verified existing prior-capture tree. The historical capture restoration manifest and test logs are in `.cache/phase10-1/`.

## Limits and stop

Public demo identity selection is not authentication. Anyone with access to the local demo can explicitly select a role; actor-bound sessions distinguish demo personas, not different people using the same persona. Historical sessions without trustworthy owner attribution are retained on disk but are not served over HTTP. Operations remains scoped read access to installed A17 data and allowlisted artifacts, with own-persona chat history.

Independent source apps are not brought into a shared IAM system. Program Owner can inspect QE/DR source evidence through scoped case links despite hidden top-level Knowledge. Portfolio reads retain their original source scope; host actions remain within the installed A17 workflow scope.

Paid model calls, live semantic grading, real microphone/provider use, background triggers and Git work were not run. No Agent Workspace redesign was implemented. Phase 10.1 ends here; further work requires a new request.
