# Phase 08.2.1 — CR-017 downstream physical validation

CR-017 now continues from its approved, scheduled and independently verified job
through an explicit synthetic lab result, existing-agent reassessment, and a
separate engineering evidence decision. A successful decision records validation
complete for the exact requirement evidence. Customer acceptance stays pending,
customer commitment stays unchanged, and program health is not automatically upgraded.

**Synthetic lab completion is a demo event in the mock Validation Lab.
The agents do not physically perform the test.**

## Components reused

The implementation reuses the five source applications, source HTTP transactions,
SQLite ownership restrictions, immutable records, idempotency receipts and audits.
It retains the existing Result snapshots, coverage rules, approved procedure,
criteria, plan/decision contracts, job/reservation, Planner link, source readers,
MCP tool set, WorkflowService, ActivityStore, CaseHarness, Coordinator, Validation &
Evidence specialist, and configured live callback. No agent prompt, tool permission,
Phase 06 execution service/policy/manifest or Phase 07 grader was changed.

## Lab event and source ownership

Two additive immutable source tables hold Validation-owned completion provenance
and Engineering-owned evidence decisions. The existing Result table retains its
format. The scheduled Job and reservation remain immutable, including their
scheduled interval. Job GETs additionally expose a nullable completion; this lets
the existing scoped MCP job reads observe the event without adding a tool.

The Validation Lab job detail offers **Publish synthetic result**, after explicit
selection of **Demo identity · Lab operator for this synthetic event**. This is a
separate, source-only public demo selector (`demo-lab-local-only`), not the Program
operator or the Engineering approver. The latter identities cannot publish results.
The lab selector cannot approve, schedule, or alter engineering criteria. It is not
production authentication. The control host has no lab publishing endpoint or lab
identity, and no agent receives this capability.

Publishing requires the existing scheduled CR-017 job, its exact digest, matching
server-recorded approval, owned reservation, current plan and unchanged approved
critical source scope. It creates one Result and one completion in a single
Validation transaction, plus audit and receipt. It cannot accept result content,
thresholds, software, configuration, operation or arbitrary write arguments.
Identical-key retries recover the original receipt; a new-key duplicate returns
`ACTION_ALREADY_RECORDED` and the existing scoped ID. Original booking, Planner,
engineering scheduling decision, manufacturing and ERP records remain intact.

The result uses CFG-B-01 / REQ-042-V2 / WF-LC-V2 and the actual approved procedure:
480 minutes across 32,768, 65,536 and 131,072 token bins, 160 minutes each. Firmware,
runtime, model and criteria snapshots come from approved source data. Criteria use
the existing recorded boolean convention. Numerical acceptance thresholds are not
modeled, and none were invented.

The fixed scenario clock precedes the scheduled test. The explicit event therefore
records **simulated scenario completion** at the booked lab end, plus a separate
wall-clock `recorded_at`. It does not rewrite the global clock, backdate the test,
change the deadline, or imply elapsed real-world execution. Only an immutable lab
event matching the result digest permits this later simulated observation to be
considered arrived. Ordinary future-dated fixture evidence remains inapplicable.

## Exact source and host surfaces

Source operations under `/api/v1` (40 business operations: 34 GET, 6 POST):

| Method / path | Authority and behavior |
|---|---|
| GET `/validation/changes/CR-017/physical-validation` | Scoped aggregate of job, result, applicability, exact binding and engineering history |
| GET `/validation/jobs/{job_id}/completion` | Scoped completion provenance; 404 when not recorded |
| POST `/validation/jobs/{job_id}/synthetic-result` | Lab demo identity only; exact plan digest; demo-generated result only |
| POST `/engineering/changes/CR-017/evidence-reviews` | Engineer only; exact current evidence digest, approve/reject and comment |

Existing `/validation/results/{id}`, `/validation/jobs/{id}`, coverage, portfolio
and audit GETs remain the source retrieval architecture. No generic proxy, public
reset, arbitrary result authoring, failure-injection endpoint or new lab service.

Host additions under `/control-api`:

| Method / path | Behavior |
|---|---|
| GET `/cases/CR-017` | Adds typed downstream source state and recorded reassessment |
| POST `/cases/CR-017/assess-validation-result` | Exact current evidence digest; operator/engineer; existing verified execution required |
| POST `/cases/CR-017/evidence-review` | Exact evidence digest and comment; installed ENGINEER object only; source review and independent readback |

The host retains its existing Origin, Host, custom action header, closed demo-profile
map, strict request schemas, scoped reads, and exclusive admission. It never builds
an actor from a supplied role object. Wrong-role review is denied without any
engineering-state write and is recorded as a host denial.

## Reassessment and decision governance

Refresh/focus/polling only read source records. The explicit reassessment action
provides a bounded lab-result event to the existing requirement-change workflow,
with the job/plan/result references resolved by the host. The existing Coordinator
and Validation & Evidence specialist perform their usual grounded assessment;
there is no new analysis agent or prompt modification. Runs/checkpoints/activity
use ActivityStore. Tests run the actual CaseHarness with deterministic model doubles.

A stable invocation derived from the exact evidence digest prevents accidental
repeat runs after reload/retry. Completed/failed attempts remain recorded. This
narrow action does **not** auto-prepare an execution proposal, schedule another job,
or link Planner. The preparation endpoint also rejects downstream reassessment
runs. Normal run navigation and polling never load credentials or call a model.

Review readiness requires a completed, validated recommendation, a sufficient
Validation & Evidence assessment containing this exact result as applicable,
no outstanding evidence gaps/blockers, and a fresh source binding matching the
one assessed. Missing, failed, incomplete, wrong-version, wrong-configuration,
conflicting or stale observations cannot close the gap. An applicable source
record alone is not an agent assessment or engineering approval.

The new decision is deliberately separate from the earlier **authorize validation
execution** decision. The Phase 06 action contract authorizes only scheduling and
Planner linking; expanding it would weaken that boundary. Instead, a narrow source
handler reuses the established transaction/idempotency/audit/identity conventions.
Its versioned policy `CR017-ENGINEERING-EVIDENCE-V1` allows only the engineer to
review the exact applicable CR-017 requirement evidence. It grants no scheduling,
shipment, qualification or customer-acceptance action.

The decision binds the requirement/configuration/software/workload/criteria and
procedure versions, immutable job and approved plan/digest, completion, exact
result content/version, current engineering source snapshots, complete evidence-set
digest, review policy, reviewer, decision, timestamp and comment. One immutable
decision exists per exact evidence digest. Lost replies are recovered through
independent source reads without another decision. Changed evidence/source versions
make old review history stale; old approval is never silently transferred.

Source engineering authority remains independent of agent text. An authorized
engineer can use the documented source review API directly; the control-plane
review additionally requires the recorded connected reassessment. A model cannot
make the source decision. Rejection keeps the technical case open. Passing evidence
and an engineering decision do not promote the requested requirement baseline,
change hardware qualification, grant customer acceptance, release reservations,
or edit commercial commitments.

## UI and business-state semantics

The existing layout, blue gradients, typography and navigation are retained. The
lifecycle adds Engineering review after Physical validation. The downstream panel
shows the actual job, approved option, configuration, result, applicability,
engineering decision and pending customer acceptance. Source links open the exact
Validation Lab job without copied IDs. The existing structured-evidence modal adds
job/plan, synthetic provenance, timestamp/version and engineering-review context;
no PDF is fabricated.

Decisions shows engineering evidence review separately from execution-plan
approval, with exact-digest URLs and retained history. Overview and alerts reflect
recorded downstream state. CR-017 remains in Needs attention while customer
acceptance is pending; program health uses the existing source rules. Read markers
on alerts do not approve anything. Concierge gets contextual questions and evidence
review context; replies/actions remain Preview and voice stays draft dictation.

| Source/host state | Display |
|---|---|
| Scheduled job; no result | Physical validation pending |
| Result received; no reassessment | Result received / reassessment needed |
| Failed/incomplete/inapplicable/conflicting result | Evidence gap remains; engineering review not ready |
| Applicable result + completed exact reassessment | Evidence gap closed / engineering review ready |
| Engineering rejects exact evidence | Engineering review rejected; case remains open |
| Engineering approves exact evidence | Validation evidence complete / engineering-approved; customer acceptance pending |
| New result/source version | Prior decision retained as historical/stale; no approval transfer |

The original Phase 06 verification remains a record of scheduling and Planner
readback. Later lab evidence does not rewrite that historical proof. The host
labels a completed scheduling record `completed_before_lab_result` and disables
re-execution from that historical proposal; Phase 06 execution authority is unchanged.

## Current demo and migration

[Open the connected CR-017 case](http://127.0.0.1:5189/control/programs/PRG-A17/cases/CR-017).
The existing user-created run, exact approved plan and verified job were preserved.
No new result or engineering evidence decision was published into this manual demo
during implementation. Source/host were restarted at 18028/18084; the existing MCP
19084 and Vite 5189 remain in use. The earlier 5188 preview is separate.

Existing database: `.demo/phase08-2-connected.sqlite3`.
Existing metadata: `.cache/phase08-2/connected/`.
A local backup and a hash proof under `.cache/phase08-2-1/` show that the additive
upgrade preserved all rows in the 31 pre-existing tables. There was no reset,
reseed, fixture change, new model invocation, commit or push.

For another existing owned demo, stop its source server first, then run:

```sh
DEMO_MODE=true DEMO_DB="$PWD/.demo/your-existing-demo.sqlite3" \
  .venv/bin/python -m mock_enterprise.cli upgrade-downstream
```

This explicit CLI checks demo ownership/path/lifecycle locks, adds only missing
downstream tables, and is retry-safe. Startup does not migrate or reseed. Fresh
initialization already includes the new tables. Retain the original Phase 08.2
[local startup commands](PHASE08_2_CONNECTED_HANDOFF.md#manual-connected-demo).

## Manual click path

1. Open CR-017 with its existing verified job; choose **Open Validation Lab**.
2. Select the explicit **Demo identity · Lab operator** checkbox in the synthetic
   event panel and click **Publish synthetic result**. No model is needed.
3. Return to CR-017 and **Refresh workflow**. Inspect the structured source result.
4. Select **Program operator**, then **Assess validation result**. In the configured
   demo, this is the optional paid/live invocation; it was not run for this slice.
5. Open **Review validation evidence** (also listed separately on Decisions).
   The Program operator cannot approve it.
6. Select **Engineering approver**, inspect the exact result/binding, enter a
   comment and approve or reject. Approval displays validation complete; customer
   acceptance stays pending and the original execution decision remains in history.

An optional programmatic manual invocation uses the same host route: GET the case,
read `downstream.physical.evidence_digest`, then POST that value as
`expected_evidence_digest` to `/control-api/cases/CR-017/assess-validation-result`
with the configured Origin, `X-Stratos-Action: 1`, and the known operator profile.
It uses the existing configured OpenAI runtime. **No paid reassessment was run.**

## Verification

All automated source mutations and reviews are **scripted integration testing**
with simulated identities, not actual human approval or a physical lab test.
Real local HTTP is used by the browser fixtures, including all lab/host/source
writes and independent reads. Models and speech are deterministic doubles.

Actual commands/results are recorded in [verification JSON](PHASE08_2_1_VERIFICATION.json).
The final source suite passed **403 tests**, including the existing **69 Phase 06**
execution regressions and **11 new downstream source tests**. The coordinator suite
passed **561 tests**, including **19 host tests** across the existing and downstream
modules. The final Phase 07 offline run passed **40/40**, with zero critical failures.
TypeScript and production build passed. All **61 browser checks passed**: 56 existing application/preview checks and five connected cases, including two downstream scenarios. A final happy-path screenshot/profile refinement also passed (overlapping coverage).

Coverage includes: missing job/result, distinct lab authority, synthetic provenance,
exact scope and retrieval, duplicate publication, result/software/configuration and
criteria version changes, failed criteria, incomplete duration, conflicting results,
engineering rejection, stale review, wrong role, exact digest, lost review reply,
no extra scheduling/Planner/proposal, safe additive upgrade, source readback,
existing UI routes, preview speech, Overview/Decisions, and 200% zoom.

The initial full source run found only the obsolete 36-operation API assertion;
it was updated to the actual authorized 40 operations (six writes). Browser setup
initially lacked the matching bundled Chromium binary; tests used the existing
Google Chrome executable. An initial browser test incorrectly expected a popup
from the existing same-tab source link; the test was corrected. No product
permission was relaxed to pass these checks. Historical Phase 07 artifacts and
prior phase screenshots are preserved; new screenshots live under
[downstream screenshots](phase08/downstream/screenshots/README.md).

## Limitations and next slice

Only CR-017 has this downstream flow. The primary UI synthetic event produces the
successful fixture; alternate failed/inapplicable/conflicting states are developer
fixtures/tests, never public failure controls. No physical hardware, numerical
acceptance engine, real authentication, production event bus or active monitor was
introduced. No paid model, semantic grader, real microphone, or live-model quality
claim is part of this verification. A recorded failed reassessment is retry-stable
for its evidence digest; this slice does not add a general rerun/reset controller.
Result corrections/supersession are handled conservatively when observed in source
state, but no public arbitrary result-edit API is provided.

Stop at 08.2.1. The exact next 08.3 step is the **Workflows & Automations catalog,
manual invocation forms, and saved schedule/event/condition previews**, reusing
registered workflow/host boundaries and adding **no active scheduler**. It requires
a separate request. Other workflows, connected freeform Concierge, touchless
execution, cosmetic redesign and Git work remain outside this delivery.

## Files changed

The [verification JSON](PHASE08_2_1_VERIFICATION.json) lists every changed author
file. Principal additions are:

- `src/mock_enterprise/downstream_models.py`, `domains/downstream.py`, and
  `downstream_upgrade.py`; additive schema/CLI/view/identity/coverage wiring.
- `src/program_coordinator/control_host/downstream.py`; typed existing-host
  reassessment/review routes in `server.py` and `models.py`.
- `mock_apps_ui/src/lab-completion.tsx` and
  `control/physical-validation.tsx`; existing case, evidence modal, Decisions,
  Overview, alerts, Concierge and generated API types updated.
- `tests/test_downstream_validation.py`,
  `coordinator/tests/test_phase08_downstream.py`, and
  `mock_apps_ui/e2e-connected/downstream.spec.ts`; developer-only failed-result
  source fixture in `coordinator/evals/phase08_2_1/lab_source.py`.
- Existing browser screenshot paths point to this slice's regression directories,
  preserving historical captures. Documentation, OpenAPI and the request archive
  describe the narrow new authorization and manual path.
