# Developer acceptance tests — NOT business retrieval material

These requirements are for Codex and tests, not for the future agents to retrieve.
Use fixtures/documents/ as the only business-document allowlist. Never expose this
file, build prompts, tests, or expected answers through a business endpoint.

## Required test groups
1. **Seed validity and reads:** all cross-system references resolve, temporal data
   is coherent, money is integer cents, each domain has working GETs, no generated
   records exist at baseline, and reads do not mutate business state.
2. **Coverage:** baseline-profile REV-B pass, target-profile REV-A pass, and short
   REV-B target run are insufficient. The correct full target config/profile run,
   supplied only as a test fixture, is sufficient. A complete total runtime with
   insufficient time in one required bin is still insufficient. A changed profile, model version,
   or configuration invalidates that coverage. Avoid matching on record IDs.
3. **Option math:** derive STANDARD review-ready Nov 20 22:00Z and -28h deadline
   slack; PRIORITY Nov 18 20:00Z and +22h slack; preserve $0/$1,800 costs; reject the
   unsupported $600 lab option. Reordering/renaming input IDs must not alter logic.
4. **Draft and decision authority:** automation may draft a valid plan, cannot
   approve it, and cannot execute without a valid recorded engineer decision.
   Unknown identities, forged IDs, mismatched approvals, altered bodies, and
   cross-program references cannot bypass permissions. An over-limit plan cannot
   get approved by the seeded engineer.
5. **Successful HTTP workflow:** distinct scripted automation/engineer identities
   create a plan, approve it, create one real job/reservation, create one planner
   link/task, and verify them through GETs. Preserve requirement baseline,
   manufacturing restrictions, order commitment, and baseline milestone date.
6. **Denial and stale state:** rejection creates no job. Changed critical source
   content, held sample, stale partner data, changed approved procedure, or a slot
   taken after planning prevent an unexecuted plan from scheduling. Test changes
   use isolated fixture/repository setup, never production business mutation APIs.
7. **Self-induced state:** approval status updates and the authorized reservation
   do not invalidate the exact plan's normal next action. An immutable approved
   plan cannot have its scope edited and reuse the old decision.
8. **Idempotency and uniqueness:** identical retry returns original resource with
   no duplicate job/reservation/link; changed body under same key returns 409;
   retry with a new key still cannot duplicate the same approved action. Simulate
   a lost HTTP response after commit and recover the original job on retry.
9. **Partial execution:** create lab job, force planner update failure, confirm the
   job persists and planner state is incomplete, then retry only planner update.
   No fake global rollback and no duplicated lab booking. Keep this injection in
   tests; do not build a general public chaos/admin API.
10. **Protected domains and results:** no public mutations for MES/ERP, no change
    to baseline dates through planner writes, no acceptance-criteria edits, no
    automation-authored pass result, no public reset endpoint or file-path reads.
    Unexpected mutation keys are rejected rather than silently ignored.
11. **Persistence and reset:** API writes survive recreating the app using the same
    DB; a local reset restores all seed entities and removes demo jobs/approvals;
    invalid database targets are refused. Test reset twice for repeatability.
12. **Audit and interface:** successful writes and key denials are attributable to
    the case and actor; approvals link to exact plans; no credentials in logs;
    idempotent replay is distinguishable from a second write; `/openapi.json` and
    interactive API docs describe actual implemented behavior.

## Clarification regressions from planning
- Historical evidence retains configuration/workload/criteria content versions.
  Changing content under the same ID with a new version invalidates coverage. New
  evidence after drafting changes the evidence-set digest and blocks old approval
  or an unexecuted action. A model/configuration change is never applied retroactively.
- Retrieve every input needed for a plan through HTTP, including lab/slot metadata,
  procedure/policy IDs and the complete expected-source object from options. Missing,
  extra and duplicate source entries fail with `INVALID_SOURCE_SET`. Public documents
  are exactly the six persisted allowlisted documents; reject encoded traversal,
  symlinks at import, and developer-file requests without leaking local paths.
- Slot start includes setup. Priority execution begins Nov 18 08:00Z, reservation
  ends 16:00Z, review ends 20:00Z. Test exact-fit and too-short windows, rate boundary
  coverage, unit AND lot freshness at 24 hours and just beyond, and future refreshes.
  Test spend at exactly 200,000 cents and one cent above; zero must remain valid.
- All nine seeded slot/sample combinations are explained: two resource-eligible
  combinations with SAMPLE-B-017; SAMPLE-B-018 blocked by its lot hold despite lab
  availability, SAMPLE-A-010 by configuration/revision, and LAB-C by configuration.
  Ineligible forecasts/slack are null. Late versus over-budget flags remain distinct.
- Engineering workflow writes, Validation booking and Planner linking each touch
  only owned business tables plus shared audit/idempotency infrastructure. Computed
  execution states expose a committed booking when planner follow-through is missing.
  An owned reservation is valid for linking; an unrelated owner/version is not.
- Concurrent requests, using separate DB connections, cannot double-book a slot,
  sample, overlapping lab interval or plan. Exact-key success returns the original
  status/body; a new-key duplicate returns `ACTION_ALREADY_RECORDED` and a scoped
  reference. Denied requests do not consume keys. Changed-body reuse of a successful
  key is rejected even after state changes. Concurrent milestone writes use compare
  and swap; changing only forecast record_version requires reread/retry of that version,
  while changed baseline/scope content requires reassessment and a new plan.
- After planner failure, lab business state and its audit/receipt survive; planner
  task/link/dependency/forecast all roll back together. Retry creates only the missing
  planner action. Unexpected DB failures never report a successful mutation.
- Approval/decision, plan content, reservation provenance and audit events cannot be
  edited or deleted by normal domain handlers. Reset is the explicit local exception:
  it restores empty generated state including receipts/audits, and refuses a running
  service, absent ownership markers, out-of-project targets, symlinks and hard links.
  Stop/restart/reset lifecycle tests must not operate on the developer's active DB.

## API proof before the agent phase
Use a real running localhost server for at least one end-to-end smoke run. An
in-process TestClient suite is useful but not sufficient for this final integration
proof. Business operations in the smoke script use HTTP only.

The smoke script must label itself: 'SCRIPTED MOCK-SYSTEM INTEGRATION TEST — NO AI
INFERENCE; ENGINEER IDENTITY IS SIMULATED.' It must fail with a nonzero exit code
on a mismatch and print enough record IDs to inspect the outcome manually.

## Phase exit report
Create docs/BUILD_HANDOFF.md with actual commands/results, test counts and skips,
local serve/docs addresses, implemented endpoint inventory, sample read/write
requests, reset procedure, security/modeling limitations, unresolved failures, and
notes for the future agent adapters. Do not claim implementation just because this
spec lists a behavior. A generated but unrun check must be marked unverified.

## Phase 08.4A standard route acceptance

- CR-019 uses the existing CaseHarness and three concurrent specialists over
  scoped MCP and real source HTTP. Exact approved scope yields an immutable
  package and one independently verified Validation Operations intake.
- No plan/decision, job/reservation, result, Planner task/link, criterion change,
  lab authorization or customer acceptance is created by the standard route.
- Wrong firmware/hardware, uncovered condition, conflicting evidence, missing
  procedure, nonstandard parameter, waiver/exception, changed acceptance,
  unknown configuration/evidence and missing/closed downstream queue block all
  autonomous handoff writes and retain exact review reasons.
- Replay/new invocation reuses a matching intake. Known failure retries safely;
  unknown outcome, interruption and readback failure require reconciliation.
  Starting another run cannot evade an unresolved previous action.
- Original CR-017 exact human review and governance regressions remain enforced.
- Phase 07 `--include-standard` adds runtime probes to the unchanged 40-case
  dataset and original hard gates; failures remain in every denominator.
- Browser tests use isolated source/MCP/host and a deterministic model double;
  successful and ineligible flows, run history, source intake and downstream
  pending states are verified. No paid model or microphone is used.

## Phase 08.4B quality recovery

Run `tests/test_quality_recovery.py`, `coordinator/tests/test_phase08_4b_quality.py`,
the MCP regression suite and `coordinator.evals.phase07 --mode offline
--include-standard --include-quality`. The new browser suite uses
`mock_apps_ui/playwright.quality.config.ts`; variants are `comparable`,
`incomparable`, and `no_alternative_supply`. Verify exact source/context binding,
wrong-role denial, held-lot exclusion, independent readback and uncertain-write
reconciliation. A routed investigation is not disposition, shipment or customer
acceptance. Full commands/results are in `PHASE08_4B_VERIFICATION.json`.

## Phase 08.4C delivery readiness

Run the complete source/coordinator/MCP regressions, including
`tests/test_delivery_readiness.py` and `coordinator/tests/test_phase08_4c_delivery.py`.
Run `PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07
--mode offline --include-standard --include-quality --include-delivery` for all 95
offline cases, including 18 critical delivery invariants. No paid model or semantic
grader is run by default. The original hard gates are preserved.

Use `mock_apps_ui/playwright.delivery.config.ts` with DELIVERY_VARIANT set to base,
technical_blocked, future_conditional, wrong_configuration, partial_failure or
stale_proposal. Verify 600 / 800 / 200, distinct technical/customer-agreement states,
wrong-role denial, exact approval, ERP/readback before Planner/readback, incomplete
step retry without duplicate commitment and unchanged QE/CR-017 sources. Frontend
and legacy connected CR-017/CR-019/QE-004 tests remain required. Browser tests are
scripted integration tests with deterministic SDK responses, not real human approvals.
Commands, results, preserved fixture hashes and corrected initial failures are in
[the verification record](PHASE08_4C_VERIFICATION.json).

### Phase 08.5 — connected Concierge

The additive A–Q suite exercises current-case and program grounding, all four
workflow routes, unsupported requests, casual approval versus explicit confirmation,
wrong roles, stale plans, voice-text authority, source injection, missing evidence,
unknown root cause, missing dates, quantity arithmetic, eligible/ineligible standard
handoffs, runtime/business outcome separation, inactive automation configurations,
acceptance/commitment separation and absence of private model reasoning.

Run `coordinator/tests/test_phase08_5_concierge.py` and Phase 07 with
`--include-concierge --include-standard --include-quality --include-delivery`.
The new `playwright.concierge.config.ts` crosses actual local HTTP/MCP boundaries
with developer-only model doubles. Existing source, coordinator, MCP and browser
regressions remain required. No paid models run automatically; see
[08.5 verification and live smoke instructions](PHASE08_5_HANDOFF.md).

### Phase 08.6 — Operations and integrated verification

Run `coordinator/tests/test_phase08_6_operations.py` with the existing source,
coordinator, MCP, Phase 07 and 08.4/08.5 suites. Regressions distinguish runtime
completion from escalation/review/partial execution/readback mismatch, preserve
historical 4/6 live failures and separate targeted passes, validate actual eval
counts/critical failures and semantic skips, deny arbitrary artifact paths, retain
actual agent/tool metadata, keep missing telemetry unavailable, separate human wait,
and derive current staleness from the workbench source view. Concierge history
links runs/proposals/confirmations/configurations without reasoning/audio/action
capabilities. Source health must begin unknown and report real reads.

`mock_apps_ui/playwright.operations.config.ts` runs the integrated journey with
`OPERATIONS_VARIANT=base`, `partial` or `mismatch`, using isolated real HTTP/MCP and
deterministic model doubles. Cross-page quantities, holds, acceptance, handoff,
decisions, search, alerts, sessions and configuration are checked. No paid models.
See [the final Phase 08 verification](PHASE08_6_VERIFICATION.json).

## Phase 09.1 — Demo reset and reproducibility

The targeted reset suite is `coordinator/tests/test_phase09_demo_reset.py`; the
real browser/restart fixture uses `mock_apps_ui/playwright.reset.config.ts`.
Verify full reset after mutations through all four connected paths, downstream lab
arrival/review, restored arithmetic/versions/ownership, scoped host cleanup,
Concierge token invalidation, inactive curated automation configuration and
byte-preserved historical eval/trace files. Repeated resets must preserve identical
business/source and current control-plane baseline digests. Single-case reset
preserves unrelated state and refuses inconsistent shared dependencies.

Inject failure only in tests: actual restoration rollback, source unavailable,
host reconciliation failure and independent readback failure. Invalid baseline
must remain false and the journal must require explicit recovery. Verify origin,
maintainer/epoch/scope/schema/storage guards, unavailable off-mode controls, no
MCP/Concierge reset tool, and no implicit reset during restart. Browser checks
exercise mutation → service restart → mutation persists → explicit reset → second
restart → baseline persists, plus cases, search, alerts, Decisions and Operations.
Retain all existing source/coordinator/MCP/offline/browser checks and mocked speech.
No paid model or full live smoke is run by this verification.


## Phase 09.2 — Cross-workflow product consistency

Run `coordinator/tests/test_phase09_product_integration.py` alongside all existing
source/coordinator/MCP and 112-case offline evaluations. Verify four canonical case
summaries, exact human-only decision identities, shared held-material equality,
600/800/200 arithmetic, approved V1 separation and actual CR-017 V2 dependency,
source-derived evidence coverage, stale standard intake provenance, full CR-017
physical result/reassessment/exact evidence review, and partial QE/DR execution
with preserved verified first steps. Operations index/detail and Concierge current
facts must agree with case summaries; historical outcomes remain distinguished.

The new `mock_apps_ui/playwright.product.config.ts` exercises all four workflows
through isolated local HTTP/MCP and deterministic model doubles. It checks unique
Program rows, all-workflow review counts, deduplicated attention/alerts, business
search ranking, exact Manufacturing source links, current state across six Concierge
page contexts, exact decision navigation, recorded CR-019 agent activity, explicit
full reset, stale-tab action invalidation and session retry-key cleanup. Existing
browser checks retain exact role, approval, source-write, readback and failure
assertions while using the shared case links and cross-workflow decision filters.
All browser speech is mocked. See [actual results](PHASE09_2_VERIFICATION.json).

## Phase 10.1 persona acceptance

Use isolated source and host storage and deterministic model/speech doubles. Follow the [persona matrix](PHASE10_1_PERSONA_ACCESS.md). Verify all four roles against seven destinations and four scoped case families; denied API/Concierge calls produce no business writes. Preserve exact allowed investigation, separate plan/evidence review, execution/readback and reset regressions. Verify owner-bound chat reads/actions, restricted context rejection before model dispatch, current review counts, hidden controls versus disabled prerequisites, safe deep links, late response isolation, cleared drafts and aborted mocked dictation. Capture each Overview and engineering/delivery decision views. See `coordinator/tests/test_phase10_access.py` and `mock_apps_ui/e2e-persona/access.spec.ts`; results belong in the [10.1 handoff](PHASE10_1_HANDOFF.md).

## Phase 10.2 — Agent workspace

Run `coordinator/tests/test_phase10_workspace.py` for isolated projection/permission/provenance tests and `mock_apps_ui/playwright.workspace.config.ts` for deterministic browser fixtures. Verify idle, observed parallel work, completed human handoff, partial failure, missing/stale observations, distinct concurrent runs, verified CR-019 intake with lab authorization pending, exact-review persona eligibility, unsent Concierge drafts, lifecycle polling and reset/persona invalidation. No model/write calls on render/inspection. Inspect 1440×900, 1280×800, narrow, enlarged-text and reduced-motion captures. Keep the workflow/Concierge/reset/persona regressions and all 112 current offline eval hard gates. [Actual 10.2 results](PHASE10_2_VERIFICATION.json) distinguish scripted deterministic integration from paid AI/human approval evidence.

## Phase 10 — touchless/concurrent refinement (current)

The focused request supersedes the historical human-handoff expectations below.
`test_phase10_touchless_concurrency.py` covers simultaneous QE-011/CR-017 with
separate invocations, activity, tool/RAG receipts and independent outcomes; active
Concierge run answers; capacity/retry/same-case exclusion; three admitted cases;
scoped reset and full-reset busy policy; and ineligible zero-write escalation.
`test_autonomous_quality.py` checks source-enforced eligibility, including missing
or mismatched approved queue/owner binding, holds, actions, baseline, procedure
and conflicting exceptions. Canonical QE-011 has no recovery plan or decision.
The latest entry/roster follow-up supersedes explicit Prepare and participating-only
display. Autonomous browser checks verify entry without a launch click, one shared
event across tabs/reload, all four specialists visible, unused Idle, moving active
dots, independent concurrent outcomes and reset followed by reload/replay. Workspace
fixtures disable demo entry to isolate idle/stale/unknown, sticky selection, return
to live work and other display states. Host checks cover anonymous/scoped entry,
no maintenance/approval authority, stale epoch/origin denial and no failure retry.
The latest [minute-long opening](PHASE10_MINUTE_FULL_TEAM_OPENING.md) also verifies
all four completed specialist assessments, Change Impact's own configuration
read, Coordinator triage/reconciliation/synthesis, explicit pacing metadata, and
at least 120 seconds of elapsed investigation in the browser. Reset must cancel
both paced Coordinator and specialist phases. Other test/live runs retain their
actual durations; QE-004 does not require the additional Change Impact work.
See [the entry handoff](PHASE10_AUTOMATIC_TOUCHLESS_ENTRY.md) for earlier results.

## Phase 10 — original autonomous opening A–Q (historical)

The new acceptance tests remain developer-only and excluded from runtime retrieval.
Use isolated stores and deterministic SDK doubles over real local HTTP/MCP; no paid
models or real speech. See [actual verification](PHASE10_AUTONOMOUS_VERIFICATION.json).

| Requested gate | Coverage |
|---|---|
| A–D: preparation, delay, authoritative event, existing workflow | `test_phase10_autonomous.py::test_event_source_shared_workflow_handoff_and_replay`; browser idle → event → investigation |
| E: repeated and concurrent delivery | `test_concurrent_event_redelivery_claims_one_run`; source atomic idempotency |
| F–G: startup/restart/navigation idle | `test_idle_navigation_and_pending_reset`, `test_restart_disarms_without_source_publication`; browser navigation check |
| H–K: pending/active/completed reset, no late work, replay | pending reset, scoped/full active reset, publication-drain race, idempotent reset/replay tests; browser repeat journey |
| L–M: actual participants, fresh motion, late human handoff | `test_actual_participation_then_human_handoff_and_operations`; autonomous/workspace browser checks |
| N: four golden cases unchanged | source record equality before/after, reset restoration; all 112 offline gates and RAG canonical comparison |
| O: unchanged governance | self-approval/early execution rejection; `test_exact_human_review_scoped_to_autonomous_plan_and_no_disposition_change`; existing four-workflow regressions |
| P: scoped RAG | three Manufacturing/Quality retrieval events with program/case/run provenance; existing 15 retrieval and 12 Quality corpus gates |
| Q: generic configurations inactive | `test_scope_role_epoch_guards_and_generic_automations_stay_inactive`; saved background flags unchanged |

`tests/test_autonomous_quality.py` also checks source publication rollback on owned-ID
collision, authenticated reads, no public publisher/release endpoint, scoped reset
and old-generation rejection. Forged/stale events, unsupported names/versions/scope,
wrong maintainers and stale epochs fail closed. Source version 2 is deliberately
unsupported; explicit reset/preparation is the only replay policy in this slice.
