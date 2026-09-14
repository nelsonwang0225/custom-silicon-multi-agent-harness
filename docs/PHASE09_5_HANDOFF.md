# Phase 09.5 — final manual/live validation and targeted fixes

Validation date: September 12, 2026. Local app: [Stratos Silicon](http://127.0.0.1:5197/control/overview). [Machine-readable verification](PHASE09_5_VERIFICATION.json), [all live attempts](PHASE09_5_LIVE_RESULTS.json), [11-screen review gallery](screenshots/phase09-5/README.md).

This report distinguishes real GPT-6 Astra analyses, agent-operated browser actions under simulated demo roles, and scripted offline integration testing. No actual human approval or physical hardware test is claimed. The app is not frozen. No Git operations, slides, new workflows, background runners, or external communications were performed.

## 1. Baseline / preflight

Used the existing Phase 09.4 helper with an explicitly owned `.demo/phase09-5-review` source/metadata pair. Existing working demos were left intact. The initial clean baseline passed all 11 checks: services, five source apps, exact baseline, four cases, no stale executable proposal, no running work, reset consistency, Concierge, model configuration, inactive background execution, and owned processes. Preparation made no paid model call and printed no secret.

CR-019 had its approved configuration/procedure and no old intake. CR-017 had its original evidence gap, no executable plan, and customer acceptance pending. QE-004 had 200/250 first-pass observations, a comparable 96% baseline, and all 250 affected units held. DR-009 reconciled 1,000 physical minus 250 held minus 150 allocated to 600 eligible against 800 requested, with no revised commitment. Current Concierge history was empty.

Baseline source digest: `5ff45501536e505e62709da628d9f27244f010d107670db2a0760add19fedaa4`. Control digest: `f75718307bffbb869adacbbb2faba1bbc9407e32de8bf27b82204590dbded64d`. Evidence: `.cache/phase09-5/baseline-initial.json` and `reset-replay-first.log`.

## 2. Manual CR-019 result

**PASS after two diagnosed live failures.** Program Operator launched the actual connected case. Three specialists completed source-backed investigation; the deterministic policy retained 18/18 matching conditions and one reusable historical evidence record. The final live run was `run_af5b8128c96e4c719b1ebf545bbed528`. The host created and independently read back exactly one Validation Operations intake: `intake-bbaf29ff8f8141e9b4922a8d1e9e9d9e` for package `package_e716775d52a7b63f5d232ebcec07d811`.

There was no new human approval. Exact replay of the intake request twice returned the same record and one total intake. The actual Validation source page showed package received with lab authorization still pending; it did not claim scheduling, testing, engineering acceptance, or customer acceptance. Treating the intake/package as laboratory scheduling authorization was denied. Unrelated source business fields, milestones, rates, resources and documents were compared before/after without unintended changes. Audit growth was expected.

The initially failed standard analyses remain retained: one incorrectly coupled the separate V2 milestone to this V1 intake; the other treated delegated source reads as missing intake. Prompt clarification fixed scope interpretation without weakening the policy or changing fixtures. Concierge subsequently explained the actual policy and linked the correct nested source intake.

## 3. Manual CR-017 result

**PASS through final Engineering evidence review.** Initial live investigation `run_0ecc7ac71618473784782608a98aabc6` identified the source-backed gap: the matching short result covered 60 minutes against the requested 480. Existing passing results with wrong configuration/profile or insufficient duration remained insufficient. Three primary specialists and a nested Manufacturing assessment completed.

The exact proposal `plan-056a1d23057e414c847c823c74defd9d` v1 selected the only eligible option offered by the authoritative calculation: SLOT-PRIORITY / SAMPLE-B-017 / PROC-LC-02 / CFG-B-01, $1,800 incremental cost. Review-ready forecast was November 18, 2026 20:00 UTC against the November 19 18:00 UTC deadline; 1,320 minutes of slack. Baseline and customer commitments remained distinct.

Wrong-role approval failed. The Engineering Approver demo role recorded source decision `decision-1ffbeea623b847ae8b71cb01428b0ded`; governed execution independently matched both job `job-058aa493005a41eaab874ac274cc7c8d` and Planner link `link-eb9a8bcda51f4531b45ef94d35e1e14a`. At this stage the job was only scheduled.

In Validation Lab, the explicit synthetic lab action under the distinct lab identity then produced result `result-215d984f326c4c148d845a49f3e8b02e`, with the exact 480-minute workload and unchanged acceptance criteria recorded as passed. The scenario completion was November 18 16:00 UTC; the wall-clock recording was September 12 19:42 UTC. Agents did not physically perform that test.

Five evidence reassessments failed their intended business path and were diagnosed before targeted retries. The sixth, `run_b07c6186065247db864b338d5bcef97d`, passed the scoped source validators and the unchanged exact host review gate. Evidence digest `1d1e8a4b7dd0a8a00de9ae1205bc1524d8e939000d01eafbcf0589639180bdb5` bound the separate review. Program Operator received HTTP 403 and a disabled approval control. The Engineering Approver recorded `evidence-review-41c24998fa544d8694b773aed309a768`.

Final truth: validation evidence complete; Engineering review approved; customer acceptance pending. The source Engineering page, case, source result dialog, Program, Decisions, Operations, and fresh Concierge response were inspected. Historical scheduling and investigation records retain their timestamps; current physical validation is displayed separately.

## 4. Manual QE-004 result

**PASS on its first live analysis.** `run_0dec193a8f8f46848d8a7d2e9a15325e` retained 200/250 first-pass = 80%, versus the comparable 96% baseline. Site 2 failure concentration was correlation, not a fabricated root cause. All 250 units in LOT-B-204 remained held; the 200 first-pass passing units were not converted to releasable supply. Eligible supply stayed 600 against 800 requested, a 200-unit gap shared with delivery.

Authorized standard investigation routing created `investigation-f5bb5e16fc1646c79f2cf9d90e704117`. The consequential plan `recovery-570c00f9b4e94612ad9b00a0fee44d98` v1 required Program Owner review. Program Operator was denied. The simulated Program Owner approved the exact plan via `recovery-decision-72f750a7c2db4650b189ee87f83f31ed`; execution created Planner task `recovery-task-e5ee30954cb046fe87467c73f083b8a7`. Every step had a verified independent readback.

Engineering, Validation, Manufacturing, ERP and Planner quality deep links were opened. The lot remained held, root cause unknown, customer commitments unchanged, and the investigation open. A direct automation attempt to release held material was denied as an unavailable business operation.

## 5. Manual DR-009 result

**PASS after one diagnosed triage failure.** The first analysis correctly calculated supply but classified the known 200-unit shortfall as missing request information, preventing specialist work. The fix distinguishes an uncovered remainder from missing destination/quantity/date inputs; source technical and timing gates remain unchanged.

The passing live run `run_39bb048d7dd94ba5b2d86f5da7301082` completed Manufacturing, Validation & Evidence, and Program & Commercial. It checked technical readiness independently: approved REQ-042-V1 / CFG-B-01, RES-BASELINE-B and exact Engineering clearance. CR-017 V2 evidence remained a separate obligation. Supply reconciled 1,000 − 250 − 150 = 600; no supported supply/date was invented for the remaining 200.

Program Operator approval returned 403 `WRONG_APPROVER`. Program Owner approved exact plan `commitment-plan-0ee111a521654fdfb7185b3daa0c4930` v1, digest `d24dd4a1dd2c8a984cf95bcb41967d9f69479b4b05062002c16cb18adaa9c060`: 600 units arriving November 23, 2026 18:00 UTC at Helios Austin receiving. Source decision `commitment-decision-95c59bdfd9f4497a87dc1e5e9057d8c2`, ERP commitment `delivery-commitment-fd19b5b431b649dcb7f6f983c72bcf2c`, and Planner link `delivery-link-cf737911c87c4037b4dedb7f9d5e24b7` were independently verified.

All five delivery source deep links were inspected. ERP and Planner both reported 600 committed / 200 uncommitted. The 150 allocation remained protected, 250 held units excluded, delivered quantity zero, customer agreement pending, and technical customer acceptance pending. Original order obligations were retained. No full 800-unit delivery promise was invented.

## 6. Live model results per workflow

All runs used the existing authorized **gpt-6-astra** runtime and scoped MCP read tools. No broad paid matrix was run. Additional calls were bounded retries after diagnosed failures, the required downstream reassessment, and the explicit reset replay. Table latency is recorded agent execution elapsed time, not cumulative concurrent model latency. Input/output counts cover completed recorded generations only.

| Case | Run ID | Seconds | Input / output tokens | Deterministic result |
|---|---|---:|---:|---|
| CR-019 | `run_e943bba160ce446791e83b5f354af453` | 154.8 | 109,720 / 15,531 | FAIL |
| CR-019 | `run_c95b6b19609e4b37b1f0d974604fcd9b` | 55.0 | 8,142 / 3,225 | FAIL |
| CR-019 | `run_af5b8128c96e4c719b1ebf545bbed528` | 118.8 | 84,889 / 12,872 | PASS |
| CR-017 | `run_0ecc7ac71618473784782608a98aabc6` | 187.2 | 162,357 / 19,403 | PASS |
| CR-017 | `run_0518d601c8144d8cafec99c2671f1a48` | 38.1 | 27,710 / 2,218 | FAIL |
| CR-017 | `run_2c2199f90a1e4b209cbb591d8bd0ac1c` | 76.8 | 107,640 / 4,788 | FAIL |
| CR-017 | `run_822288479f0e4398a42bfe6c1c4fabd2` | 123.2 | 173,746 / 11,826 | Analysis PASS; evidence-review gate FAIL |
| CR-017 | `run_9a4687a7194d48f28cebc69f637b042a` | 106.5 | 104,236 / 7,397 | FAIL |
| QE-004 | `run_0dec193a8f8f46848d8a7d2e9a15325e` | 109.4 | 62,216 / 12,121 | PASS |
| CR-017 | `run_2355558e0cc64e4fbd843e908b85b441` | 115.9 | 103,320 / 8,050 | FAIL |
| CR-017 | `run_b07c6186065247db864b338d5bcef97d` | 115.9 | 103,708 / 8,227 | PASS |
| DR-009 | `run_6906c22233e24d01b7d45a50f8c89ee2` | 59.3 | 12,701 / 3,879 | FAIL |
| DR-009 | `run_39bb048d7dd94ba5b2d86f5da7301082` | 111.4 | 83,397 / 14,138 | PASS |
| CR-019 | `run_a4e8c5c8b6e14ae997f7195365b076da` | 119.6 | 85,135 / 12,487 | PASS |
| QE-004 | `run_e527a8283cca4f918b6ed99c6da472bf` | 113.2 | 63,840 / 13,175 | PASS |

Full trace IDs, termination codes, token totals, and individual validator checks are in `PHASE09_5_LIVE_RESULTS.json`. The developer-only Phase 09.5 adapter validates the actual current `case-state.json`, source-bound specialist/final schemas and allowed read tools; it does not bypass host approval gates. The third CR-017 reassessment illustrates the distinction: generic analysis validation passed, but the business evidence-review gate remained blocked. It is recorded as a failed manual path, not silently promoted to success.

Raw run artifacts and all failures are preserved under `.cache/phase09-5/live/`. Existing historical Phase 07 live artifacts and graders were not rewritten. No dollar cost or successful platform trace export is inferred.

## 7. Concierge live results

Twelve real paid turns were recorded, including targeted retries and a final post-execution check. Completed classification latency ranged from 2.50 to 4.23 seconds. The runtime chooses a bounded intent; source-backed host projections and structured confirmations retain business authority.

| Prompt | Final observed behavior |
|---|---|
| What needs my attention? | Source-backed cards for all four Helios cases; shared QE/DR supply gap not added twice. |
| Why was human approval required? | Exact Engineering policy, role, proposal cost and authorized scheduling/link scope after the targeted mapping correction. |
| What caused QE-004? | Facts and site concentration separated from hypothesis; root cause unknown; held units not available supply. |
| Can we commit 800 units? | 600 eligible / 800 requested / 200 gap; no full quantity/date promise. |
| Why was this handled touchlessly? | 18/18 policy checks, real intake ID, and pending downstream lab authority. |
| Approve this. | Structured decision confirmation; no silent approval. Wrong-role submission denied. |
| Check delivery readiness every weekday morning. | Asked for the missing exact time, accepted weekdays 7 AM CT, and saved an inert configuration preview. No scheduler started. |
| Final current-state attention check | CR-017 technical complete, CR-019 intake handed off, QE recovery verified/hold governed, DR commitment and Planner link verified/200 gap. |

The real microphone check was not performed because no coordinated live speaker was available. No unattended microphone was activated. Automated dictation tests use mocks and verify editable, unsent transcripts and cleanup; typed or spoken text is never authentication or approval. Real browser/provider microphone behavior remains a human rehearsal check.

## 8. Persona / governance negative tests

Program Operator, Engineering Approver, Program Owner and Read-only Viewer were inspected in the actual UI. Required roles and switch-identity controls remain visible. These are explicit simulated demo identities, not production authentication.

| Boundary | Evidence / result |
|---|---|
| Operator cannot approve CR-017 plan | Structured Concierge submission denied; wrong-role decision control disabled. |
| Operator cannot approve final evidence | HTTP 403 `WRONG_APPROVER`; UI disabled. |
| Operator cannot approve QE recovery or DR commitment | Each returned 403; UI identifies Program Owner. |
| Held material cannot be released by automation | Unavailable business-operation denial; source lot stayed held. |
| Passing held units cannot count as supply | 200/250 observation retained; all 250 excluded from eligible supply. |
| Root cause cannot be invented | Live QE specialist and Concierge explicitly kept cause unknown. |
| Stale proposal cannot execute after reset | HTTP 409 `PROPOSAL_REFERENCE_MISMATCH`; no source mutation. |
| Concierge cannot approve through ordinary text | Exact structured confirmation required; authority still checked by host. |
| Touchless intake cannot authorize lab work | Intake/package scheduling attempt rejected; authorization/testing remain pending. |

Source references, immutable digests, exact manifests, actor checks and per-system readbacks were retained. No model received new business write tools. Public physical result authority stayed with the lab demo identity.

## 9. Reset / replay

PASS. Full reset restored the original source/control digests and all 11 readiness checks. Real paid CR-019 replay passed as run_a4e8c5c8b6e14ae997f7195365b076da with one new intake; QE-004 replay passed as run_e527a8283cca4f918b6ed99c6da472bf, required a fresh simulated Program Owner decision, and created one new verified recovery task. Repeating the exact recovery execution twice retained one task. A second full reset removed those records; replaying its stale reset epoch returned 409 DEMO_STATE_CHANGED. A further explicit full reset produced identical business baseline digests with a new audit epoch. Current runs and Concierge sessions are empty. The app is left running on the clean baseline.

Initial and post-reset baseline checks compare source and control digests, all four canonical states, empty run/decision/session metadata, and absent prior source mutation records. The old CR-017 reference was rejected after reset. Reset is performed through the existing explicit demo-maintainer boundary with preview, epoch check, source restore, separate host reconciliation, archive and independent validation. Repeating reset establishes the same business baseline; reset audit IDs/epochs intentionally change.

See `.cache/phase09-5/reset-replay-verification.json`, baseline JSON files, reset logs and pre/post snapshots. Preserved live artifacts live outside resettable demo state.

## 10. Issues discovered

Every paid failure was inspected before another call. The observed problems were source-scope interpretation, host-event provenance, final structured-output consistency, UI mapping, and verification-environment collisions; none justified weakening policy, treating missing evidence as hardware failure, or changing synthetic scenario facts.

| ID | Observed problem | Targeted correction |
|---|---|---|
| UX-01 | Live CR-019 launch button says Run investigation again while the current run is active; agent progress note describes polling implementation. | Active launch buttons name the current activity; specialist completion counts derive from recorded invocations. |
| ENV-01 | First polish run could not launch missing default Chromium headless-shell-1243; all five tests failed before UI assertions. | Reuse Phase09.4 installed Chromium via PLAYWRIGHT_CHROMIUM_EXECUTABLE; no application defect claimed. |
| LIVE-01 | CR019 invented a gating relationship between separate milestone V2 evidence and exact V1 intake, returning an unresolved blocker despite 18/18 source checks. | Standard Coordinator/Change Impact/Program prompts require checking exact source-policy conditions and preserving unrelated milestone obligations as separate; no fixture, permission or policy-code change. |
| LIVE-02 | Triage requested specialists but also labeled their not-yet-fetched evidence and future binding policy as missing intake. Host correctly suppressed delegation. | Standard triage instructions distinguish missing request scope from known source work assigned to specialists. Host guard remains unchanged. |
| UX-02 | New CR019 investigation displayed previous failed handoff as if it belonged to current run. | Resolve handoff by current run across case, lifecycle, visual and summary; retain explicit previous-result link. |
| CHAT-01 | Recurring weekday-morning request returned generic clarification. | Explicit automation routing for missing exact time; host asks for time and retains inert configuration preview. |
| CHAT-02 | Concierge reported missing intake ID despite verified CR019 handoff. | Read nested typed intake; bind displayed handoff to current run; show source link and separate pending lab state. |
| UX-03 | CR019 button labeled Investigating while CR017 was running. | Distinguish current-case run from another case running while preserving admission guard. |
| CHAT-03 | Why-human-approval response showed evidence gaps but omitted the recorded approval-policy explanation. | Show immutable source-plan policy and authorized reviewer for policy/decision explanation. |
| UX-04 | Live verbose rationale dominated the exact decision header. | Lead with source slot/sample and approval scope; retain full recorded rationale in expandable supporting evidence. |
| LIVE-03 | CR017 downstream event linked the new result ID before scoped Coordinator intake could discover it. Guard correctly suppressed specialists; UI offered no retry for completed-but-unconfirmed reassessment. | Event links only established job and plan; specialist discovers result via existing read tools, host still checks exact evidence digest. Add explicit source-bound retry of a completed unconfirmed/failed evidence run; stable retry key preserves idempotency; UI offers retry without granting review authority. |
| LIVE-04 | Validation job read rejected the lab completion snapshot of CR017 content v1 as a current record conflicting with CR017 record v3. SDK wrapper reduced this to specialist_failed; coordinator duplicate retry was denied. | Recognize only typed lab-completion source_snapshot as historical, keeping scope/current-version validation. Unwrap SDK exception causes only to recover fixed safe guard codes. |
| LIVE-05 | Third downstream run correctly found exact sufficient evidence but incorrectly treated customer acceptance as validation evidence gap and requested Planner ownership outside the narrow adequacy question. Runtime/source validators passed; business review remained blocked. | Clarify the host-authored reassessment request: exact evidence adequacy blockers versus known pending engineering/customer/Planner stages. No host approval conditions or final validators relaxed. |
| LIVE-06 | Fourth CR017 evidence reassessment completed its specialist but failed during SDK synthesis output handling with generic case_failed. API retrieval of the unstored response returned 404; exact malformed field unavailable in the historical artifact. | Capture only the typed assistant final object or bounded schema error types/known field paths in the existing private run directory; never invalid values, full SDK responses or hidden reasoning. Preserve malformed outputs as failures and expose fixed malformed_agent_output code. |
| OPS-01 | Operations relabeled manually launched runs as Concierge merely because a later chat referenced them; decision column claimed execution pending after verified readback. | Origin uses invocation provenance; related sessions remain links. Decision label reports decision only; separate verification reports actual execution. |
| ENV-02 | Concurrent pytest commands reused repository default .cache/coordinator-pytest. One subset cleanup error and one full-suite fixture error resulted. | Use unique explicit --basetemp paths for each run. |
| UX-05 | CR017 showed before-scheduling instructions after verified execution; two separate investigation sections each said Last run. | Use current physical-validation stage after a job exists; label each recorded investigation with its actual timestamp and source-read context. |
| LIVE-07 | Fifth evidence reassessment retained a root-level final-package consistency rejection; source adequacy and specialist completion were valid. | Explicit Coordinator instructions for existing final consistency rules: factual-only confirmed_facts, policy/review flag agreement, escalation reason, and read-only false action/acceptance/pass flags. Retain fixed schema-rule labels in private diagnostics. No validator relaxed. |
| SOURCE-01 | After exact Engineering evidence approval, Engineering Hub and source overview still described only scheduled_awaiting_execution as current execution. | Read the existing scoped physical-validation HTTP projection into source UI case data. Show current result/applicability/Engineering decision/customer acceptance separately; label retained scheduling records explicitly; route next steps from current evidence. No source API, fixture or business-state mutation. |
| LIVE-08 | First DR009 live analysis calculated 600/800/200 but put the unfilled remainder in missing_information at triage. The host suppressed specialists; final escalated and no proposal was created. | Clarify delivery triage: known unfilled remainder is an analysis risk, not missing request scope. Preserve missing destination/quantity/date inputs and source technical/timing gates. Independent domain reads may run concurrently. |
| UX-06 | Delivery visual still said a Program Owner decision was needed after approval; lifecycle exposed raw approve/reject labels. | Use approved/rejected decision wording and a universally valid separation of commercial commitment and customer agreement. |
| UX-07 | Five historical failed outcomes pushed Operations run history below the first viewport. | Keep the count visible and make the recorded outcomes expandable; retain all failed runs and current-case status. |

The fourth rejected final output did not retain its malformed field. An attempt to retrieve the unstored response returned 404; the exact historical validation rule is unknown. The fifth retained only a root validation error. Later private diagnostics provide bounded rule identifiers without exposing rejected values, SDK payloads or hidden reasoning. Both remain failed runs.

## 11. Fixes implemented

Coordinator instructions now distinguish exact standard intake from unrelated requested V2 obligations, delegated source reads from missing intake, and a known delivery remainder from incomplete request scope. Shared final instructions restate existing consistency rules. Strict validators, unknown/out-of-scope stops and authoritative policy conditions remain intact.

Downstream reassessment binds the current evidence digest, carries established job/plan links, and lets Validation discover the new result through existing scoped reads. Only typed lab-completion snapshots are treated as historical provenance. Explicit retry of a failed or unconfirmed exact evidence assessment is idempotent and does not grant review authority. Safe SDK cause handling preserves fixed guard codes; private rejected-final diagnostics contain schema error types/known paths or a typed valid final object, never hidden reasoning or rejected input values.

Concierge projections use the current run's typed intake and immutable plan policy; cadence clarification stays a preview until exact configuration save. Operations distinguishes launch origin from later related chat sessions, separates decision from execution/readback, and keeps historical failures expandable. Source Engineering UI reads the existing physical-validation projection and labels the retained scheduling record explicitly. No source API, fixtures, customer commitments, model configuration, approval authority or lab authority were altered to force success.

## 12. Regression tests added

Eleven coordinator tests were added beyond the 737-test starting count: seven Phase 09.5 scope/diagnostic/guard cases, two downstream actual HTTP/MCP and exact-retry cases, one Concierge clarification case, and one Operations provenance/decision/readback case. Existing Concierge checks were extended. The diagnostics tests ensure invalid values/unknown field names are not retained and malformed final output remains failure. Delivery's genuine missing-destination stop remains enforced even when a source partial proposal exists.

Two new polish browser tests cover current-run handoff matching and another case running. Existing downstream browser cases were extended to exercise explicit unconfirmed retry, final Engineering evidence approval, source-page current result/decision/customer state, and retained scheduling context. Operations assertions were updated for truthful historical outcomes. Browser speech is mocked throughout.

## 13. UX, layout, visualization and pacing

The actual live experience exposed long waits of roughly one to three minutes per successful analysis. Loading controls now say Investigating/Assessing/Preparing the relevant action and show actual completed specialist counts, without invented percentages. A different active case is identified correctly. Failed/unconfirmed reassessment has an explicit retry path.

Decision headers lead with exact slot/sample, $1,800 cost and authorized actions; verbose recorded rationale is expandable. Historical findings carry actual run timestamps. Current technical state is separate from older scheduling text. Delivery shows 1,000 inventory, held/allocation exclusions, 600/800 coverage and 200 remaining; QE retains yield comparison and held supply; CR-019 shows policy/handoff boundaries; CR-017 shows the 480/480 evidence lifecycle. Operations now places run history within the first viewport while preserving prior failures.

All 11 required candidate screenshots were captured and visually inspected at 1440×900. No material clipping, unreadable primary typography, or overflow remained in those candidates. Evidence and Concierge panels retain deliberate internal scrolling for longer content. These are review artifacts, not Phase 10 slides. Program-level source health and original forecast remain source-owned observations, separate from case technical completion.

## 14. Final automated test counts

| Suite | Result |
|---|---:|
| Source/backend pytest | 483 passed |
| Coordinator pytest | 748 passed |
| MCP pytest | 56 passed |
| Complete offline evaluation cases, all installed families | 112/112 passed; zero critical failures |
| Browser regression coverage | 89 passed; 3 intentional mutually exclusive Operations-variant skips |
| TypeScript typecheck and production build | Passed |

Browser total is 56 foundation + 32 matrix tests (CR-017, CR-019, Concierge, three quality variants, six delivery variants, three Operations variants, product, reset, seven polish tests) + one cold-start harness. Relevant later source-downstream tests, delivery caption check and all Operations variants were rerun successfully after their final changes; these reruns are not double-counted. No paid models were invoked by automated suites.

Final full coordinator: 748 passed in 358.93 seconds. Source: 483 passed in 194.13 seconds. MCP: 56 passed in 18.54 seconds. Foundation browser: 56 passed in 5.2 minutes. Exact logs are under `.cache/phase09-5/`; browser matrix manifests record command, environment, exit code and duration.

Earlier failures are retained: missing default Chromium prevented launch until the installed executable was specified; two concurrently run pytest suites collided on their repository default basetemp and were rerun with distinct storage; a Snapshot/dict coding error and incomplete schema-generation setup were corrected before acceptance. Intentional unavailable-host HTTP errors in foundation tests and lazy-asset interruption in the cold-start harness are negative scenarios, not silently ignored failures.

The existing cold-start test regenerates `docs/PHASE09_4_COLD_START.json`; this latest offline result is also preserved as `docs/PHASE09_5_COLD_START.json`. Pre-existing screenshots overwritten by regression capture are restored from the pre-run byte copies. Historical paid-run results are not rewritten.

## 15. Remaining limitations

Live model output is nondeterministic. Eight pre-replay attempts missed their intended business path, including five downstream reassessments, before scoped corrections produced passing live paths. A passing correction and bounded replay are not a measured reliability rate. Keep the real-time loading narrative and the existing recorded-run fallback available for an interview; do not portray recorded output as a new live run.

Real microphone/provider behavior remains untested. Platform trace availability was not independently confirmed. Token totals are not an invoice and omit unrecorded failed generations. Lab results and approvals in this review were explicit synthetic/role simulations. Customer agreement, acceptance, physical shipping, the 200-unit gap and held-lot disposition remain unresolved by design. Saved automation triggers are inactive. No new scheduler, listener or actual recurring monitoring exists.

## 16. Demo-readiness assessment

The four canonical paths have now worked in the actual application with real model analyses and independent source verification. Offline hard gates and browser regressions are green. Targeted failures and corrections are retained rather than relabeled as a flawless first run. Readiness is for a supervised human rehearsal with live-model pacing and the remaining microphone check understood; it is not a code freeze or a guarantee of every future model response.

Stop at Phase 09.5 for human review. No final Git cleanup, commit/push, slide creation or later phase has been performed.

## 17. Exact startup, reset and verification commands

Commands were run from the existing repository root. The owned instance uses UI 5197, host 18250, source 18251 and MCP 19251. The source-app launcher is [here](http://127.0.0.1:5197/); the control-plane app is [here](http://127.0.0.1:5197/control/overview).

```sh
# Initial creation performed once for this explicitly disposable validation instance.
./scripts/demo --state-dir .demo/phase09-5-review --source-port 18251 --mcp-port 19251 --host-port 18250 --ui-port 5197 init --yes

# Resume the current instance; start does not reset working state.
./scripts/demo --state-dir .demo/phase09-5-review start
./scripts/demo --state-dir .demo/phase09-5-review --json check

# Explicit supported full reset / prepare; use only when restoring the walkthrough baseline.
./scripts/demo --state-dir .demo/phase09-5-review prepare --yes
./scripts/demo --state-dir .demo/phase09-5-review --json check

# Apply local code changes to owned services, when no investigation is active.
./scripts/demo --state-dir .demo/phase09-5-review stop
./scripts/demo --state-dir .demo/phase09-5-review start

# Full offline Python suites, with distinct storage.
.venv/bin/python -m pytest tests -q --basetemp=.cache/phase09-5/source-current-all
PYTHONPATH=src:. coordinator/.venv/bin/python -m pytest coordinator/tests -q --basetemp=.cache/phase09-5/coordinator-current-all
mcp_server/.venv/bin/python -m pytest mcp_server/tests -q --basetemp=.cache/phase09-5/mcp-current-all
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase07 --include-standard --include-quality --include-delivery --include-concierge --output .cache/phase07/phase09-5-final-validated

# Typecheck / build; browser commands run in mock_apps_ui.
cd mock_apps_ui
npm run typecheck
npm run build
# Installed browser override used in this environment:
export PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Users/nelsonwang/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
./node_modules/.bin/playwright test
./node_modules/.bin/playwright test --config playwright.phase08.config.ts
./node_modules/.bin/playwright test --config playwright.standard.config.ts
./node_modules/.bin/playwright test --config playwright.concierge.config.ts
./node_modules/.bin/playwright test --config playwright.quality.config.ts
./node_modules/.bin/playwright test --config playwright.delivery.config.ts
./node_modules/.bin/playwright test --config playwright.operations.config.ts
./node_modules/.bin/playwright test --config playwright.product.config.ts
./node_modules/.bin/playwright test --config playwright.reset.config.ts
./node_modules/.bin/playwright test --config playwright.polish.config.ts
./node_modules/.bin/playwright test --config playwright.harness.config.ts
```

The quality matrix set `QUALITY_VARIANT` to `comparable`, `incomparable`, and `no_alternative_supply`; delivery used `base`, `technical_blocked`, `future_conditional`, `wrong_configuration`, `partial_failure`, and `stale_proposal`; Operations used `base`, `partial`, and `mismatch`. The saved manifests preserve exact per-run invocations. Manual paid checks were initiated through explicit case/Concierge UI actions, not by these regression commands.
