# Recorded demo fallback

Announce **Recorded demo** before opening these artifacts. They are historical observations, not current case state or evidence that a live model is running. Opening them does not mutate the source database.

| Record | Provenance and limitation | Access |
|---|---|---|
| Phase 09.3 four-case gallery | Isolated scripted HTTP integration, deterministic model doubles, simulated identities, mocked speech. All four workflows are illustrated; this is not paid live intelligence. | [Gallery](screenshots/phase09-3/README.md) and [verification](PHASE09_3_VERIFICATION.json) |
| Historical targeted covered CR-017 | Recorded live evaluation, one case passed; does not establish success for other scenarios or the original full smoke. | Operations → Evals & Reliability → Later targeted validation · cr017_covered |
| Historical targeted scheduled CR-017 | Recorded live evaluation, one case passed; scheduled is not tested or accepted. | Operations → Evals & Reliability → Later targeted validation · cr017_scheduled |
| Original full live smoke | Preserved **FAIL**, four of six passed. Show this truthfully if discussing reliability history. | Operations → Evals & Reliability → Historical full smoke |

The existing read-only allowlist in `src/program_coordinator/control_host/operations_artifacts.py` indexes those files. This phase generates no new model success and does not copy a historical result into a current workflow. Do not publish private run artifacts or render raw traces as an executive status summary.

To return to live mode, close the recorded material, restore local services and configuration, run `./scripts/demo status`, and explicitly initiate the desired existing workflow. `./scripts/demo prepare` is an optional deliberate baseline reset, not a mode switch. Model availability and live behavior remain unverified until an operator explicitly invokes the runtime during final validation.
