# Phase 08.3 browser evidence

The first eight captures come from scripted integration tests with isolated source
and host storage, deterministic model stubs, and demo profiles. They are not paid
AI runs or actual human approvals. Saved triggers do not execute.

| Capture | Evidence |
|---|---|
| [Workflow catalog](01-catalog.png) | One Connected capability and twelve non-executable Previews |
| [Connected workflow detail](02-connected-detail.png) | CR-017 scope, manual launch, authority and required review |
| [Run detail](03-run-detail.png) | Actual test run, findings, evidence, timeline and waiting-for-review outcome |
| [Run history](04-run-history.png) | Persisted run linked from the catalog |
| [Schedule editor](05-schedule-editor.png) | Weekly time, timezone, date and explicit no-scheduler boundary |
| [Configuration review](06-review-configuration.png) | Scope, authority, limitations, notifications and save action |
| [Automation list](07-automation-list.png) | Saved daily configuration alongside the three seeded examples |
| [Condition editor](08-condition-editor.png) | Typed evidence-age condition and no-background-evaluator boundary |

The following captures inspect the preserved working demo at
[localhost:5189](http://127.0.0.1:5189/control/workflows). This inspection issued
no POST requests and no new model calls. Its original recorded investigation,
approved plan and scheduled lab job predate this phase; the physical result is
still pending.

| Capture | Evidence |
|---|---|
| [Existing demo catalog](09-existing-demo-catalog.png) | Original run and three configuration previews |
| [Narrow catalog](10-narrow-catalog.png) | 760 px viewport, no horizontal document overflow |
| [Existing run](11-existing-demo-run.png) | Completed runtime with physical result pending |
| [Run at 200% zoom](12-existing-run-200-percent.png) | No horizontal document overflow |

Full-page screenshots are tall by design. Open the PNG to inspect it at native
resolution. Editor captures use the viewport to show the fixed dialog footer.
Prior-phase regression captures are preserved separately under
`../regression-08-2-1/`.
