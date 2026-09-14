# Touchless QE-011 and concurrent workflow runs

Current contract: [focused request](../prompts/10_TOUCHLESS_CONCURRENT_WORKFLOWS.md).
This supersedes automatic app entry and the earlier canonical QE-011 human handoff.

Subsequent direct follow-up: [automatic entry and full roster](PHASE10_AUTOMATIC_TOUCHLESS_ENTRY.md)
now supersedes this document's explicit-Prepare and participating-only display
choices. Its touchless authority and concurrency implementation remain current.

1. **Why no human review.** QE-011 completes routine evidence gathering and the
   already permitted Manufacturing investigation route. It does not prepare or
   execute a consequential recovery plan. QE-004 retains Program Owner review;
   CR-017 retains exact Engineering approval. The model cannot grant itself authority.

2. **Deterministic policy.** The shared source/host rule checks exact QE-011,
   LOT-B-219, customer/program/configuration/material scope; final-test anomaly;
   authoritative whole-lot hold; approved procedure; comparable baseline and
   source evidence; only standard investigation routing requested; approved exact
   tasks; active queue and owner matching the existing approved PROC-QE-B-01
   destination; and no other open exception on that lot. Missing/ineligible facts
   escalate. RAG may support investigation guidance but does not authorize action.

3. **Exact write boundary.** The host calls the existing Manufacturing
   quality-investigations HTTP API, with exact context digest, run/case IDs and
   durable idempotency key. The source rechecks the policy in its transaction.
   Independent GET readback must match the work item, tasks, owner, queue, scope
   and provenance. A second context read verifies unchanged protected facts.
   No Planner task is added: its existing recovery-task API requires approval.
   No queue service, inventory release, disposition, test or commitment write exists.

4. **End state.** `handoff_verified` / “Quality investigation handoff verified.”
   The entire 100-unit lot remains held and ineligible; root cause is unresolved;
   customer commitment is unchanged. No recovery plan, Program Owner proposal,
   decision or Planner recovery task is created. Human approval is “Not required
   for executed actions.” Ineligible variants record `review_required` with reasons
   and no handoff. Write/readback failures remain explicit and reconcilable.

5. **Concurrency implementation.** Removed the host's global one-run admission
   check. The existing asynchronous task model, WorkflowService, CaseHarness and
   SDK configurations remain. Each run has an independent invocation of the same
   specialist definitions. No exclusive “busy specialist” ownership is imposed.
   Narrow existing execution locks still protect source-handoff transactions;
   independent reasoning stays concurrent.

6. **Capacity.** Default three concurrent admitted workflows, configurable with
   `STRATOS_MAX_CONCURRENT_WORKFLOW_RUNS` from 1–8 before host startup. Readiness
   reports the configured value. At capacity the host returns
   `WORKFLOW_CAPACITY_REACHED` without claiming the invocation. The caller can retry
   the same key after capacity frees. There is no in-memory waiting queue or
   hidden automatic retry. Same-case exclusion includes admitted postprocessing;
   exact replay returns the original run.

7. **Isolation.** Case/run/workflow IDs, trigger, checkpoints, specialist invocation
   IDs, source registry, ContextVar knowledge scope, activity, RAG, receipts,
   proposals and decisions remain per run. QE-011 Manufacturing readback also checks
   run/case provenance. QE-004 retains its existing sequential source-work deduplication.
   Completing QE-011 does not complete CR-017. Existing source
   versions, stale checks and immutable approval manifests still reject conflicts.

8. **Agent Workspace.** Defaults to the newest active permitted run, then current
   outcome/handoff, then recent history. Manual selection remains sticky during
   refresh. A compact active count and event/user origin labels distinguish runs.
   The graph always shows one run; there is no aggregate graph. QE-011 shows actual
   participants only. Active specialists show Processing with moving colored dots;
   idle/completed/stale work does not animate, and reduced motion is respected.
   A historical selection offers Back to live activity when another run is active.
   Invalid selection is cleared on reset/access change.

9. **Overview.** Running and successful QE-011 are absent from Needs attention.
   The selected recorded outcome remains accessible in the workspace/history.
   Policy failures and unresolved execution/readback failures legitimately need
   attention. No new large history table is added.

10. **Operations and Concierge.** Each run shows its own invocation source,
    specialists, trace/provenance, tools, RAG, actions and outcome. QE-011 displays
    Touchless / standard quality investigation and the explicit approval result.
    Concierge run questions prioritize active runs and list both cases; case
    questions use the same source-grounded summaries. Concierge starts use the
    shared admission service and do not replace another run.

11. **Reset/replay.** Prepare explicitly resets QE-011, checks the golden baseline
    and arms one eight-second event. Startup, navigation and new tabs remain idle.
    QE-011 reset drains event publication and its admitted work before pruning only
    its owned records. CR-017 continues and its history is retained. Full reset
    preserves the existing policy: it disarms/cancels QE-011 but refuses restoration
    while another workflow/Concierge turn is busy; retry once that work settles.
    Source/host reset commits remain separate and partial recovery is explicit.

12. **Verification.** Automated verification uses isolated source/metadata stores,
    deterministic SDK/workflow doubles and mocked speech, with no paid model calls.
    Final commands and results are recorded in the verification section below.
    Browser coverage includes two concurrent graphs, real dot motion, independent
    completion, source-event provenance, three Quality knowledge receipts, no fake
    decision, scoped reset, idle startup, explicit replay and responsive layouts.

13. **Optional live check.** Follow the exact numbered walkthrough in the
    [runbook](DEMO_RUNBOOK.md#autonomous-back-office-opening-and-concurrent-investigations).
    Full reset → Program operator → Prepare → Overview → QE-011 running → CR-017
    Run investigation → Overview → switch both runs → independent outcomes.
    This live check was not run automatically. Each run may issue multiple existing
    Coordinator/specialist API calls and optional configured hosted retrieval calls.
    Per-run budgets apply separately; no new aggregate dollar cap is introduced.

14. **Local limitations.** One local host owns the metadata directory. Capacity is
    bounded admission, not a durable queue; interrupted work does not auto-resume.
    The event is one explicit synthetic demo event, not a general event fabric.
    The destination is verified through the existing approved procedure's queue/
    owner binding, not an external ticket-queue availability probe. Model reasoning
    quality, paid latency, API rate limits and live concurrency were not measured.
    Working demo stores and historical live evidence are preserved.

15. **Production evolution.** Put the existing invocation layer behind durable
    queue/worker infrastructure with horizontal scaling, backpressure, rate and
    cost limits, resource-specific concurrency and durable recovery. Keep exact
    source transactions, approval manifests and independent verification. No such
    distributed scheduling infrastructure is claimed or implemented here.

## Verification record

Verified September 12, 2026 (local time). All HTTP/MCP/browser verification below
is **scripted integration testing with deterministic agents**, not a paid AI run
or an actual human approval. Test stores are isolated under `.cache/`.

Commands run from the repository root unless noted:

| Check | Actual command | Result |
|---|---|---|
| Source regression | `PYTHONPATH=src:. .venv/bin/pytest -q --basetemp=.cache/source-touchless-final` | **506 passed** |
| Coordinator broad regression | `PYTHONPATH=src:. coordinator/.venv/bin/pytest -q coordinator/tests --basetemp=.cache/coordinator-full-touchless` | Initially **844 passed, 3 failed**; all three diagnosed and corrected as described below |
| Corrected coordinator suites | `PYTHONPATH=src:. coordinator/.venv/bin/pytest -q coordinator/tests/test_phase08_4b_quality.py coordinator/tests/test_phase08_workflows.py coordinator/tests/test_phase10_workspace.py --basetemp=.cache/coordinator-corrections` | **82 passed**, including all three previously failing tests |
| MCP regression | `PYTHONPATH=src:. mcp_server/.venv/bin/pytest -q mcp_server/tests --basetemp=.cache/mcp-touchless-final` | **56 passed** |
| Shared knowledge / canonical conclusions | `PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_knowledge_integration --output .cache/phase10-rag-integration/touchless-concurrency` | **15 retrieval gates, 4 canonical cases passed; 0 unexpected changes** |
| Original reliability eval | `PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07 --mode offline --output .cache/phase07/touchless-concurrency` | **40/40 passed; hard gates passed** |
| QE-011 touchless scorecard | `PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_touchless` | **45 passed; A–J and concurrency checks passed** |
| Concurrent opening browser flow | In `mock_apps_ui/`: `npx playwright test --config playwright.autonomous.config.ts` | **2 passed**, no skipped/flaky tests |
| Agent Workspace browser regression | In `mock_apps_ui/`: `npx playwright test --config playwright.workspace.config.ts` | **15 passed**, no skipped/flaky tests |
| Typecheck and production build | In `mock_apps_ui/`: `npm run build` | **Passed**; TypeScript check and Vite build |

The coordinator corrections preserve QE-004's existing same-source deduplication,
regenerate the workflow catalog for the current policy wording, and update the
legacy aggregate-selection expectation to a single active run. The full broad
suite was not repeated after the corrections; its three affected suites were run
in full. New capacity coverage and the final 45-test scorecard also passed.
Concurrent RAG testing corrected a deterministic test double that had incorrectly
copied another specialist's unseen references; runtime provenance guards remain
unchanged. Browser testing also exposed and corrected a late CR-017 callback that
could navigate away after the user returned to Overview.

Artifacts:

- [QE-011 scorecard](../.cache/phase10-touchless/eval_c152ee92a73645e5aae57dae8834d77f/scorecard.json)
- [Original 40-case evaluation](../.cache/phase07/touchless-concurrency/report.md)
- [Concurrent investigations, 1440](screenshots/phase10-touchless/concurrent-1440.png)
- [Verified handoff, 1920](screenshots/phase10-touchless/handoff-1920.png),
  [1280](screenshots/phase10-touchless/handoff-1280.png),
  [390](screenshots/phase10-touchless/handoff-390.png)
- [Operations](screenshots/phase10-touchless/operations-1440.png) and
  [QE-011 case](screenshots/phase10-touchless/case-1440.png)

Screenshots were inspected for desktop and responsive layout. Browser assertions
also check actual dot displacement during active work, paused idle/reduced-motion
states, separate selections, successful handoff, preserved CR-017 review, and
absence of a QE-011 human decision.

Skipped: paid live concurrency, hosted indexing, semantic model grading, real
speech and production scheduling/load tests. No Git operations were performed.
The optional live walkthrough remains a manual validation step, not a claim of
measured live-model quality or performance.

The existing owned preview at `http://127.0.0.1:5211` was restarted against its
preserved source/metadata stores. HTTP checks returned a healthy deterministic
test host, configured capacity 3, no running workflow, and a successful UI
response. No Prepare, reset, source event or paid investigation was triggered in
that preserved preview during this refresh.
