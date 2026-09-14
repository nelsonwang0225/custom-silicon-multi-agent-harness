# Phase 09.3 — UX, identity and demo polish

Phase 09.3 polishes the existing product. The four workflows, five source apps, source records, agent prompts, tools, exact approvals and execution services retain their existing authority. This is a primary polish pass, not a permanent UI freeze. Stop here; later manual/live validation may identify targeted corrections.

## What changed

1. **Issues found.** The pre-edit browser review covered 24 surfaces at 1440×900. Helios cases appeared well below the fold; case status preceded the title; technical metadata displaced the business story; the large Concierge launcher obscured content; active identity and role requirements were hard to see. See [the recorded review](PHASE09_3_UX_REVIEW.md).
2. **Layout.** Overview pairs a compact health summary with attention and actual recorded agent activity. Helios leads with four case cards. Cases share a title/question, current outcome, next step, lifecycle and source-backed visual. Technical comparisons remain available below.
3. **Copy.** Cards use short business titles, one relevant fact and a next step. Infrastructure information, historical run IDs, source comparisons and tool activity move into links or expandable sections. Current case state remains distinct from historical runtime and source-record status.
4. **Visuals.** CR-017 compares approved/requested workloads and the duration of the latest matching-profile observation. CR-019 shows policy checks, reusable evidence and intake. QE-004 compares pass rates and held/eligible supply. DR-009 reconciles physical inventory with held, allocated and eligible quantity, request coverage and separate technical readiness.
5. **Identity.** The header shows the installed demo actor and role. A four-card picker explains capabilities and limits. Contextual “Switch identity” opens it with the required role highlighted; choosing remains explicit. The exact review URL survives switching; drafts and voice are cleared by the existing identity boundary.
6. **Disabled actions.** Investigation, review, execution, reassessment and configuration controls explain the required role or source/workflow prerequisite. Already-verified work, stale state and required review comments remain visible. Disabled predicates and server authority are preserved.
7. **Concierge.** A compact floating launcher includes explicit dictation access. The opened panel retains its full conversation and governed confirmations. Context summarizes the current case or four-case program scope. Status cards lead with the current source and next step; extra source fields expand on demand. Consequential action cards retain all confirmation facts.
8. **Decisions.** The queue leads with consequences and the required owner. Exact CR-017 review highlights cost, forecast and authorized actions. Recovery/delivery links open the exact selected plan and focus its decision section. Approval remains a separate deliberate action.
9. **Navigation.** Evidence links open the scoped native dialog and restore focus. Case-to-decision links preserve exact references; run-to-case and source-app links remain intact. Search prioritizes business cases and decisions. Alerts show six prioritized items, with remaining alerts available through a disclosure and accurate total/read counts.
10. **Implementation.** Changes are scoped to React presentation, pure view models, browser tests, documentation and a developer-only fixture guard permitting isolated `.cache/phase09-3/` storage. The [verification manifest](PHASE09_3_VERIFICATION.json) lists every changed file and hashes. No new dependency or runtime framework was added.
11. **Screenshots.** [The gallery](screenshots/phase09-3/README.md) contains the requested 1440×900 screens, plus 1920×1080, 1280×800, zoom, source, agent and run detail views. All new screenshots depict isolated scripted fixtures, deterministic model doubles and simulated identities.
12. **Verification.** 86 unique frontend/browser checks passed across the existing source-app suite, connected workflow/governance matrix, integrated product/reset journeys and five new polish checks. Three Operations tests were intentionally skipped in variants where they do not apply. Targeted backend projection tests passed **19/19**; offline evaluation passed **112/112**, with no critical failures. TypeScript checking and production build passed. Actual commands, initial failures, successful affected-file reruns and preservation checks are recorded in [the verification manifest](PHASE09_3_VERIFICATION.json). No paid models or real microphone were used.
13. **Later manual validation.** Review the visual pacing with the actual presentation window, representative long live findings and slow real investigations. Live model prose, provider speech behavior and a human-operated full demo remain untested in this slice. Preserve explicit approval boundaries if later copy or layout changes are needed.

## Terminology and scope

| Display | Meaning |
|---|---|
| Needs review | A current source-bound human decision is pending. |
| Investigation running | An actual recorded run is running; specialist checkpoints may arrive separately. |
| Recorded result / findings recorded | Historical runtime output exists; no running model is implied. |
| Handoff verified | The CR-019 intake has independent readback; lab authorization remains downstream. |
| Validation complete | Exact Engineering evidence approval is recorded; customer acceptance remains pending. |
| Waiting for external source | Current case state requires external work, such as the physical lab result or Quality disposition. The adjacent next step names the dependency. |
| Readback verified | The specific authorized source action was independently observed. |
| Partial execution | Some writes may have succeeded. Reconcile the existing exact work before any retry. |
| Stale / current source unavailable | Historical observations remain available, but do not grant current action authority. |
| Lot held | Held quantity is excluded from eligible supply, including first-pass passes. |
| Schedule configured · runner inactive | Configuration metadata exists; no background scheduler/listener/evaluator is installed. |

Scoped terms are intentional: runtime completion, a recorded review, verified execution, technical validation and customer acceptance are different events. Original baseline dates, internal forecasts, proposed commitment dates and customer obligations keep their source meanings.

## Installed persona model

| UI role | Installed actor | Existing capability | Boundary |
|---|---|---|---|
| Program operator | `demo-automation` | Investigate, prepare and coordinate work; carry out policy-permitted or exactly approved actions | Cannot approve Engineering evidence, release held material or self-approve commitments |
| Engineering approver | `demo-engineer` | Investigate changes; decide exact validation authorization and Engineering evidence adequacy | Customer acceptance, Quality disposition and commercial approvals remain separate |
| Program Owner | `demo-program-owner` | Investigate quality/delivery; approve exact recovery metadata and delivery commitments | Cannot release lots, approve Engineering adequacy or bypass allocation authority |
| Read-only viewer | `demo-reader` | Inspect current business records and recorded activity | No investigation, approval or execution |

These are installed synthetic role-test identities, not production authentication. Source-app reads keep the existing read-only HTTP identity. The host checks the actor, scope and exact source binding on every consequential action. No client-only Quality release persona was invented.

The workflow catalog's generic manual-launch surface retains its existing Program operator / Engineering approver check. Program Owner quality/delivery investigation is available from the existing case workbenches. The UI does not broaden that adapter's authority.

## Visualization rules

- Use existing HTTP projections and source-calculated values. Do not synthesize readiness scores, success states, thresholds or eligible quantity.
- CR-017's duration bar is an observed-duration comparison, **not** percent readiness. `satisfies` comes from the source coverage assessment. Matching a workload/profile and meeting a duration do not independently establish criteria acceptance.
- CR-019 checklist counts are recorded policy checks. Package creation, verified intake and downstream lab authority are separate stages.
- QE-004 rates are basis points converted to percentages. Comparability is an explicit source finding; unknown/incomparable observations do not establish degradation or root cause.
- DR-009 inventory segments use the source reconciliation. Eligible inventory is shown separately from customer-ready quantity after technical/timing gates. Partial commitment does not erase the remaining demand or original order.
- Agent branches show only actual recorded specialist invocations. They express consultation, not inferred concurrent timing. Idle role definitions do not imply invocation. Failed or incomplete runs stay incomplete.
- A source outage removes current lifecycle claims. Stale stages require refresh; partial execution/readback remains an unresolved execution stage.
- Color supplements labels, quantities, icons and stage text. No animation represents old activity. Reduced-motion behavior remains supported.

## Interaction and accessibility decisions

The compact default launcher supersedes the earlier large resting dock in this slice; the opened Concierge remains substantial and floating. Its existing focus-collision handling remains active. Dictation is explicit, editable and bounded, with browser-provider disclosure and cleanup on modality, navigation and identity changes. All automated speech checks use mocks.

Native dialogs retain Escape, focus trapping, focus return, scroll restoration and the shared heading/close/footer treatment. The larger identity picker keeps both capabilities and role boundaries available. Main desktop headings remain 40 px. At 1280×800 and at 200% zoom, content reflows or uses intentional local scrolling instead of shrinking the desktop type to fit.

Consequential review and confirmation steps were not merged. Role switching selects an existing actor; it does not approve or execute. Exact missing/stale plan URLs do not silently select a replacement.

## Known limits

- Source and host reads are independent observations, not a distributed snapshot. Existing action revalidation remains authoritative.
- The five-minute tour is optimized for desktop. Dense option tables and longer evidence remain deliberate scroll/disclosure content; very narrow screens are supported for access rather than as the primary presentation.
- Operations retains bounded historical visibility and separate eval history. Failed live artifacts have not been relabeled or replaced.
- The pre-existing >500 kB shared entry chunk remains; this slice adds no dependency and does not perform an unrelated bundling refactor.
- The user’s working demo databases were not reset. Explicit reset/restart tests ran only against their own isolated fixture databases.
- No paid live model, real microphone, external speech, production authentication, scheduler, Git work or later Phase 09 work was performed.

## Verification scope and review preview

Browser verification is scripted integration testing over real local HTTP boundaries with deterministic model doubles and simulated role-test approvals. It is not a live AI run or actual human approval. The 86 count excludes overlapping reruns: 56 foundation checks, 23 connected scenario checks, one integrated product journey, one reset/restart journey and five polish checks. The full foundation run ended with 55 passes and one outdated evidence expectation; the entire affected 15-test voice/dialog file then passed. The CR-017 matrix ended with seven passes and one outdated configuration-copy expectation; its three-test workflow file then passed. All authority/readback assertions remain in place.

The unchanged full source, coordinator and MCP suites were not rerun in this UI slice. The 19 targeted backend tests cover the reused Operations and shared product projections; the 112 offline cases retain their existing hard gates. Semantic score remains null because no paid grader ran. Foundation tests intentionally exercise unavailable host projections; reset tests intentionally restart isolated services, so those logs can contain expected connection-refused messages.

The local review preview at `http://127.0.0.1:5193/control/programs/PRG-A17` uses isolated `.cache/phase09-3/review/` state and deterministic doubles. It contains three pending source-bound decisions and a verified CR-019 intake; it is separate from the user's working demo. The [screenshot index](screenshots/phase09-3/capture-index.json) records 41 captures, dimensions, fixture origin and SHA-256. Historical screenshot files were restored byte-for-byte after regression capture; regenerated copies are retained under `.cache/phase09-3/regenerated-captures/`.
