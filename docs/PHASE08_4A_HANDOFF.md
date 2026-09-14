# Phase 08.4A — Connected standard change / touchless handoff

Implemented Use Case 1A as **CR-019**, a real connected route within
`requirement_change_analysis`. The successful outcome is **“Standard change
package prepared and handed to Validation Operations.”** Independent source
readback confirms receipt. No new engineering approval, lab authorization,
scheduling, test pass or customer acceptance is implied.

The existing local demo is [CR-019](http://127.0.0.1:5189/control/programs/PRG-A17/cases/CR-019).
It is installed and ready for explicit initiation. No live model was automatically
run. Recorded successful browser runs use isolated deterministic model doubles.

## 1. Exact scenario

Helios requests WF-LC-V1 in its next PRG-A17 acceptance validation package.
Request HELIOS-PACKAGE-2026-11-019 retains REQ-042-V1 and its acceptance criteria.
PROC-STD-01 v1 and STD-HANDOFF-V1 approve exactly CFG-B-01 v1, REV-B, MODEL-LAB-07,
one device, FW-2.3, RT-4.1, QFMT-1, MEM-1; 8,192/32,768 token bins, concurrency 4,
1,024 output tokens and a 120-minute suite (60 minutes per bin).
RES-BASELINE-B can be reused as historical profile evidence. SAMPLE-B-017 still
needs standard confirmation work after separate lab authorization. Requested
package timing is November 18, 2026 at 18:00 UTC. Existing milestone, forecast,
customer commitment and sample reservations are preserved.

## 2. Shared runtime

Existing WorkflowService, workflow registry, ActivityStore, CaseHarness,
Coordinator, Change Impact, Validation & Evidence and Program/Commercial
specialists, Agents SDK runner, trace/checkpoint plumbing and scoped MCP sessions
are reused. The standard route adds conditional instructions and a bounded
StandardValidationAssessment. Original CR-017 instruction strings are retained.
Manufacturing and ERP are not called merely to populate domains.

The agent runtime remains read-only. A source-identified standard investigation
exposes one extra read tool to its three specialists:
`get_standard_change_context(change_id)`. The trusted host acts only after a
validated shared-harness result and a fresh source policy check.

## 3. Deterministic eligibility

Eighteen explicit checks cover request/source agreement, recognized change type,
approved scoped routing policy, unchanged approved baseline, exact approved
procedure/version, hardware and software, explicit operating conditions,
unchanged acceptance criteria, conflicting evidence, available reusable evidence,
exceptions/waivers, owner/queue, permitted action, consequential decisions,
samples/inputs, timing and required remaining work.

The result records each check, pass/fail reason, exact source digest, rule/version,
reusable evidence and remaining work. Any failed condition blocks autonomous
handoff and requires review or clarification. A model's “eligible” claim cannot
authorize the action. Host and source independently enforce the same pure policy.
No “smaller context must be covered” inference exists.

## 4. Package contract

`HandoffPackage` contains package ID/version; customer/program/change/request;
request reference and baseline version; procedure/version; exact configuration,
profile and conditions; versioned/digested evidence; reusable IDs; required
remaining work and inputs; sample IDs; requested timing; queue/owner; completion
criteria; rule/version; full source digest bindings; and original workflow,
case and run references. Lab authorization, physical testing and customer
acceptance are explicitly pending. Package and provenance are inspectable in
both the control case and source intake.

## 5. Exact write boundary

Only `POST /api/v1/validation/changes/{change_id}/intakes` is added to autonomous
business authority. It accepts a strict package and expected context digest,
requires the source automation role plus idempotency key, reconstructs the exact
package in one source transaction and records an immutable intake/audit event.
Uniqueness binds program, change and request content version.

There is no generic Validation write, arbitrary tool proxy, approval bypass,
lab scheduling reuse, Planner mutation, or public fixture/reset endpoint.
CR-019 cannot enter the CR-017 draft-plan route. The compatibility approval-policy
record for PROC-STD-01 permits no scheduling actions.

## 6. Downstream owner and verification

VALOPS-A17 belongs to **Atlas Validation Operations**. Successful readback verifies
intake identity/scope, full package equality and digest, procedure/configuration,
owner/queue, evidence and expected source state:

| Field | State at handoff |
|---|---|
| Validation Operations intake | Received |
| Package | Complete; independently verified by host |
| Lab authorization | Pending / separate |
| Physical testing | Not started |
| Engineering result review | Downstream, after a result |
| Customer acceptance | Pending |

Durable metadata records package preparation, action started, action succeeded
and handoff verified as distinct events. Write receipt alone is insufficient.
Known failures can retry with the original key after exact policy revalidation.
Lost responses/interruption remain unknown until read-only reconciliation.
Readback mismatch never becomes success. A repeated run reuses a matching intake;
a new invocation cannot bypass an unresolved previous action.

## 7. UI changes

CR-019 has a source request, applicability/evidence/policy view, lifecycle,
recorded specialist findings, inspectable package, action/readback state,
reconciliation controls and downstream responsibilities. It is integrated into
Helios, Overview, Scenarios, workflow launch and history, run details, search and
contextual Concierge suggestions. A successful handoff is history rather than a
persistent attention alert. Failures produce a single relevant alert.

The Validation Lab now has a read-only Operations intake queue/detail surface.
No successful standard case creates a Decisions record. Concierge replies retain
the Preview label; saved background triggers remain configuration only. Existing
blue gradients and visual system are preserved.

## 8. Registry and modes

| Surface | Mode / authority |
|---|---|
| Requirement Change Analysis | Connected shared family; CR-017 and CR-019 |
| Standard Change / Touchless Handoff | Connected catalog route into the same family; bounded intake only |
| CR-017 material change | Connected; exact human engineering approval before governed execution |
| Yield / Quality Exception Recovery | Preview; no executor |
| Delivery Readiness | Preview; no executor |
| Other catalog concepts | Preview |
| Saved schedules/events/conditions/chat triggers | Configuration previews; inactive |
| Concierge replies / Operations | Preview |

Catalog totals: 13 entries, 2 connected presentations, 0 interactive simulations,
11 previews. There is one connected change-management runtime, not two platforms.

## 9. Evals

`--include-standard` adds 23 runtime cases to the unchanged original 40-case
Phase 07 dataset and its original non-averageable hard gates. Eleven success
checks cover exact applicability, evidence reuse, remaining work, absence of a
new approval, bounded write, independent verification, replay, pending customer
acceptance and lab work, criteria protection, and CR-017 preservation. Twelve
variants block wrong firmware/hardware, uncovered conditions, conflicting
evidence, missing procedure, nonstandard parameters, engineering exception/waiver,
acceptance change, missing owner, unknown configuration, closed queue and missing
evidence. New observations cross real source HTTP/MCP with a deterministic model
double through CaseHarness. They do not measure live model reasoning quality.

## 10. Verification and preservation

See [verification record](PHASE08_4A_VERIFICATION.json) for exact commands,
results, corrected failures, artifacts and skipped checks. All verification is
isolated scripted integration testing, with simulated demo identities and no
paid inference. Screenshot examples: [verified handoff](screenshots/phase08-4a/standard-handoff.png),
[workflow history](screenshots/phase08-4a/workflow-history.png),
[source intake](screenshots/phase08-4a/validation-intake.png),
[blocked firmware](screenshots/phase08-4a/standard-wrong_firmware-blocked.png).

Explicit additive installation preserved every old source row and the byte-level
host index. The original run, exact approved/executed plan, scheduled job,
activity and downstream physical-result-pending state remain unchanged.
The installation initially exposed an overly broad document snapshot: unrelated
CR-019 documents made CR-017 look stale. Source snapshot selection now excludes
those distinct-case documents while retaining every original critical record,
explicit assessment reference and exact version check. A regression checks both
unchanged installation and detection of an original procedure-version change.
No original approval or source version was rewritten.

## 11. Optional manual live-model run — not run automatically

The existing demo processes use source 18028, MCP 19084, control host 18084 and
UI 5189. Opening pages does not load credentials or invoke a model. In the UI,
open CR-019, select **Program operator**, then **Start connected investigation**.
That explicit click uses the existing authorized GPT-6 Astra setup.

Equivalent command, from the repository root, for **one manual paid run**:

```sh
curl --fail-with-body -sS \
  -X POST http://127.0.0.1:18084/control-api/cases/CR-019/investigations \
  -H 'Origin: http://127.0.0.1:5189' \
  -H 'Content-Type: application/json' \
  -H 'X-Stratos-Action: 1' \
  -H 'X-Stratos-Demo-Profile: automation' \
  --data '{"invocation_id":"ui_phase08_4a_manual_001","change_id":"CR-019"}'
```

Repeat that exact invocation ID only to recover its response; it replays the same
run. Read its state with:

```sh
curl --fail-with-body -sS http://127.0.0.1:18084/control-api/cases/CR-019
```

Inspect the returned run and case in the app. The expected business outcome is
**Handed to Validation Operations**, with lab/testing/customer acceptance still
pending. If the model or source check fails, inspect the recorded failure; do not
invent a successful outcome or switch to CR-017. No key change is needed.

For a stopped owned local demo that does not yet contain CR-019, installation is
explicit (never run against an active source process):

```sh
DEMO_MODE=true DEMO_DB="$PWD/.demo/phase08-2-connected.sqlite3" PYTHONPATH=src \
  .venv/bin/python -m mock_enterprise.cli install-standard-case
```

## 12. Limitations and stopping point

Live-model interpretation/semantic quality was not measured. This is one named
synthetic approved procedure and one bounded intake; lab authorization and
physical execution are intentionally not implemented on this route. Unknown
writes with no recoverable source receipt remain unresolved for operator review.
Demo identities are local role stand-ins. No background scheduler, freeform chat,
new source permissions beyond the stated contract, or Git work was performed.
The build retains its reported chunk-size advisory.

**Stop after 08.4A.** The exact next requested slice is **Phase 08.4B: Yield /
Quality Exception Recovery**: a distinct source-backed quality exception, its
material/evidence investigation and governed human disposition boundaries,
reusing the shared runtime. No 08.4B implementation has started.
