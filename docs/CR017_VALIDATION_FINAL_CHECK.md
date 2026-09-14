# CR-017 final check before result publication

Implemented the approved interactive engineering diagram in Stratos TestOps, on
the CR-017 validation job immediately above the existing lab identity and Publish
synthetic result controls. The working demo was not reset.

## Experience

- One draggable, zoomable conceptual chip; select Context & memory, Compute, or
  I/O & scheduling to inspect their before/after values.
- Original, Updated and Changes views highlight validation scope. Hardware
  geometry stays identical. Camera buttons provide keyboard controls.
- The final-check header summarizes the approved workload, procedure and total
  test duration. Values come from the existing source-loaded case and job records.
- The green outcome is labeled **Passing result preview** and **Simulated result ·
  Not yet published**. The existing demo action creates the recorded test result
  only after the lab operator explicitly publishes it.
- After publication, the panel shows the source completion record and its
  validation-result link. It does not leave an unpublished preview on screen.
- Missing/current-version mismatched scope hides the passing preview and requests
  a source refresh. The source service still owns publication authorization.
- The local lab identity checkbox clears when navigating to a different job.

## Scope and preservation

CR-017 only. No source API, schema, fixture, backend, agent, MCP, RAG, approval,
reset or downstream workflow changes. No new dependency, model call, extra
approval, mandatory review checkbox or automatic publication was added. Exact
publication payload, lab identity, idempotency key and independent HTTP readback
remain unchanged. An illustrative floorplan never establishes a silicon change,
physical test measurement or Engineering/customer acceptance.

The original versus updated comparison reads the existing source profiles:
8,192 / 32,768 versus 32,768 / 65,536 / 131,072 input tokens; 120 versus 480 total
minutes. The procedure supplies 160 minutes per target bin. I/O remains four
concurrent requests and 1,024 output tokens each. These are source values, not
hard-coded outcome data in the visual component.

## Files

- `mock_apps_ui/src/validation-final-check.tsx` — source-bound summary and inspector.
- `mock_apps_ui/src/validation-final-check.css` — TestOps-only presentation.
- `mock_apps_ui/src/validation-chip-canvas.tsx` — local interactive chip drawing.
- `mock_apps_ui/src/lab-completion.tsx` — final-check placement and published state.
- `mock_apps_ui/src/validation.tsx` — job identity key prevents local state leaking.
- `mock_apps_ui/e2e/final-check.spec.ts` — isolated source integration verification.
- `mock_apps_ui/e2e-connected/downstream.spec.ts` — updated heading selector only.

## Verification

- TypeScript check: passed (`npm run typecheck`).
- Final production build: passed (`npm run build`, including TypeScript).
- Focused source browser/HTTP test: **1 passed**, 8.5 seconds test duration,
  11.7 seconds overall. It creates an approved CR-017 job with simulated source
  identities, confirms no result exists before publication, exercises scope
  modes/regions/camera/drag/hotspots, intercepts a changed source version and
  verifies recovery, checks absence on CR-105, clears identity across route
  changes, then publishes through the original action and checks exact readback
  and result snapshots. This is scripted integration testing, not a live AI run
  or real physical lab execution.
- Browser inspection: 1440×900, 1920×1080, 1280×800; no page overflow or browser
  runtime errors. Rotated bounds now fit at default zoom; deliberate zoom-in can
  crop for close inspection.
- Protected file audit: 215 backend/fixture/API/control-plane files checked;
  zero changes. Test-owned source/UI servers stopped after verification.
- Broader coordinator/host suites and paid live models were not rerun for this
  focused source UI change. Source-only test harness messages about the absent
  optional control host are expected; host integration was not claimed.

[Final test log](../.cache/cr017-final-check/verification-final.log) ·
[Build log](../.cache/cr017-final-check/build.log) ·
[Protected-file audit](../.cache/cr017-final-check/protected-files.json)

[Before](screenshots/cr017-final-check/before-1440.png) ·
[After — 1440](screenshots/cr017-final-check/preview-1440.png) ·
[After — 1920](screenshots/cr017-final-check/preview-1920.png) ·
[After — 1280](screenshots/cr017-final-check/preview-1280.png)
