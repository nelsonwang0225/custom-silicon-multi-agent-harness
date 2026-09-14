# Phase 10 — Autonomous QE-011 app entry

## Request

Make the bounded QE-011 scenario start without a human launch action when a user
enters the Stratos control plane. After an eight-second source-event delay, the
existing Coordinator and specialists process the case and stop at the existing
Program Owner decision boundary.

## Required behavior

- Control-plane entry arms QE-011 automatically; service startup alone stays idle.
- The host owns cross-tab idempotency. Refreshes, route changes and additional tabs
  cannot reset active/completed work or create duplicate events/runs.
- One browser tab attempts automatic entry once. Resetting in that tab leaves the
  opening idle until a new app session or an explicit replay.
- Keep real source publication, existing workflow invocation, agent telemetry,
  Operations provenance and human handoff. Do not fake processing activity.
- Keep reset, failure visibility, exact approval authority and reduced-motion UI.
- Saved generic automations remain inactive; add no scheduler or general listener.
- Offline/deterministic verification must not make paid model calls.

