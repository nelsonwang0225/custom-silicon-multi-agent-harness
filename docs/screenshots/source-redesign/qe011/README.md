# QE-011 source-view verification

**Scripted source publication; not a successful autonomous-dispatch test.**

These screenshots verify an already-published synthetic Manufacturing event in a separate copied database. The prior automatic-entry `AUTONOMOUS_EVENT_FAILED` and prepare `DEMO_BASELINE_INVALID` remain failures and were not repaired or hidden by this check.

The exact source event `diagnostic-source-redesign` was read through HTTP and matched the QE-011 / LOT-B-219 context digest. Browser checks covered the exception and lot pages at 1440×900, 1920×1080 and 1280×800. All six viewport images were inspected; corresponding full-page captures are included.

Results: no browser or console errors, no horizontal page overflow, no QE-004 record leakage, no business/host writes, and unchanged source HTTP readbacks. No models were run. The separate fixture/UI processes on ports 18661, 18662, 19662 and 5252 were stopped and the ports checked closed. The existing working demo and port 5241 were left alone.

See [validation.json](validation.json) for exact provenance, source facts and checks.
