# Phase 09.1 — Demo reset and reproducibility

Implemented from [the Phase 09.1 request](../prompts/09_1_DEMO_RESET.md).
The [canonical baseline contract](PHASE09_1_DEMO_BASELINE.md) defines source IDs,
initial user-facing state, ownership, 600/800/200 arithmetic, single-case dependencies,
Concierge behavior, automation configuration and archive policy. Phase 09.2 is not
started. No application redesign or new business workflow was introduced.

## Architecture and ordering

The existing source fixture architecture remains authoritative. The narrow optional
host `DemoManagement` adapter invokes the source-owned administrative restoration
module; no agent or MCP tool can call it. It is independent of business profiles,
workflow approvals and Concierge confirmations. There is no reset route in the five
source business APIs and no generic database/table/record/path parameter.

1. Validate the exact allowed scope, typed `RESET` confirmation, current demo epoch,
   configured source file's demo marker/schema/path and its identity over source
   HTTP. The source health response carries a one-way storage identifier and protocol
   header, not a path or credential. A mismatched file/source URL is refused.
2. Refuse active investigations/conversations or an active governed execution lock.
   Drain in-flight host requests (ordinary reads remain concurrent), persist an audit/journal admission barrier, then take the
   source maintenance lease. Normal source HTTP requests take nonblocking shared
   leases; reset takes an exclusive lease and requests receive a retryable 503 while
   it is held. Concurrent CLI invocation admission observes the same journal barrier.
3. Archive selected source facts and receipts durably. In the existing single SQLite
   source deployment, use one administrative maintenance transaction to restore the
   fixture graph, including immutable records, and reinstate every original protection
   trigger before checking foreign keys and committing. The graph is composed from
   Engineering/Validation base, standard intake provenance, QE Manufacturing material
   and shared ERP/Planner records, then the DR extension. Deferred references permit
   exact snapshot restoration without exposing an intermediate graph.
4. Only after the source commit, archive/reconcile scoped host workflow metadata,
   automation configuration, affected conversation history and current capabilities.
5. Release source maintenance and perform independent five-system HTTP readback plus
   deterministic baseline validation. Complete the persistent audit only on success.

This local maintenance transaction is an explicit exception for restoration, not a
new cross-system business transaction. Source restoration and host reconciliation
are separate commits. There is no distributed rollback claim. A failed source
transaction leaves its prior source state intact. A later failure reports `partial`,
identifies its stage and failed read subsystem, keeps `baseline_valid=false`, and
blocks host business actions until an explicit same-scope/full reset reconciles it.
After a source commit, a persisted source maintenance barrier also blocks source-app
business writes until independent verification completes; GETs remain available.
An interrupted journal survives restart. Retry makes new archive/audit entries;
original immutable snapshots are never overwritten.

## Demo-only security and APIs

Enable controls explicitly with **DEMO_MODE=true** and the host's
`--enable-demo-controls` flag. Its `DEMO_DB` must match the source serving
`--source-url` and remain inside configured project `.demo/` storage. The host metadata directory must be
inside project `.demo/` or `.cache/` storage. Symlinks,
hard-linked/non-regular targets, unknown markers/schemas and arbitrary scopes fail
closed. Existing strict loopback Host/Origin and `X-Stratos-Action` protections apply.
POST reset additionally requires the separate public local demo-maintainer selector
`X-Stratos-Demo-Maintainer: local-demo-reset`. This is a demo stand-in, not production
authentication. Normal automation/engineer/Program Owner selectors alone cannot reset.

| Host path under `/control-api` | Behavior |
|---|---|
| GET `/demo` | Enabled state, baseline version, epoch, latest management audit, recovery status and archive count |
| GET `/demo/preview?scope=full` | Exact scope, affected systems, reset/preservation policy and dependency refusal reasons |
| GET `/demo/verify?scope=full` | Structured read-only baseline check, discrepancies, source/control digests, arithmetic and HTTP-read observations |
| POST `/demo/reset` | Closed `{scope, confirmation:"RESET", expected_epoch}`; no arbitrary identifiers or filesystem input |

Allowed scopes are `full`, `CR-017`, `CR-019`, `QE-004`, `DR-009`. With controls
unconfigured, only GET `/demo` returns `enabled:false`; reset/preview/verify routes
are absent and the UI entry is hidden. The generated enabled-host contract is
[phase09-1-host-openapi.json](phase09-1-host-openapi.json).

UI business requests carry the observed epoch; stale source/host requests are
rejected before their business handler. Exact source/host approval and freshness
checks still apply independently. Existing automation tools receive no reset
capability. Product launch, navigation, refresh and normal restart do not call reset.

## Exact pre-demo sequence

Use the **same existing demo file, source port, MCP port and metadata directory** as
your working demo. The following matches repository default ports; substitute your
already configured paths/ports consistently. These commands do not initialize or
reset on launch. If source/host processes are already running older code, stop and
restart only those owned processes first, preserving their paths.

```sh
# Repository root — terminal 1: existing source apps, fixed loopback binding
DEMO_MODE=true .venv/bin/mock-enterprise serve --port 8000

# Terminal 2: existing scoped MCP reader (needed for later manual investigations)
DEMO_MODE=true PYTHONPATH=src mcp_server/.venv/bin/python -m stratos_mcp \
  --port 9000 --backend-url http://127.0.0.1:8000

# Terminal 3: existing host, with explicit demo maintenance enabled
# Replace the metadata directory below with your CURRENT host metadata directory.
DEMO_MODE=true PYTHONPATH=src:. coordinator/.venv/bin/python \
  -m program_coordinator.control_host --source-url http://127.0.0.1:8000 \
  --mcp-url http://127.0.0.1:9000/mcp --metadata-dir .demo/control-host \
  --port 18082 --ui-origin http://127.0.0.1:5188 --enable-demo-controls

# Terminal 4: frontend
MOCK_API_URL=http://127.0.0.1:8000 CONTROL_HOST_URL=http://127.0.0.1:18082 \
  npm --prefix mock_apps_ui run dev -- --port 5188

# Explicit reset, then separate validation. Both use the running host boundary.
DEMO_MODE=true PYTHONPATH=src:. coordinator/.venv/bin/python \
  -m program_coordinator.control_host.demo_cli reset --scope full --yes
DEMO_MODE=true PYTHONPATH=src:. coordinator/.venv/bin/python \
  -m program_coordinator.control_host.demo_cli verify --scope full
```

For a nondefault database, supply the same `DEMO_DB` to source and host. For
nondefault ports, pass `--host-url` and `--ui-origin` **before** the CLI subcommand.
The CLI prints the reviewed scope and JSON result; absence of `--yes` requires an
interactive `RESET`. It exits nonzero on invalid baseline or unknown outcome.
The legacy stopped-service `mock-enterprise reset-demo` remains the historical
foundation reset and does not reconcile Phase 08 host metadata: use the new full
reset for an integrated walkthrough.

UI equivalent: **Operations → Demo controls → Full demo → Review reset… → type
RESET → Confirm demo reset → Verify baseline**. A single-scenario selection previews
any refusal before confirmation. After a valid full check, open
[Overview](http://127.0.0.1:5188/control/overview). No paid model is needed for launch,
reset, verification or navigation. Later manual investigations retain their existing
explicit model invocation boundary.

## Verification, files and limitations

Actual commands/results and exact changed files are recorded in
[PHASE09_1_VERIFICATION.json](PHASE09_1_VERIFICATION.json). New tests exercise all
four governed paths, downstream synthetic result/review, single-scenario preservation,
shared dependency refusal, real restoration rollback, source/readback/reconciliation
failure and retry, busy admission, schema/identity/epoch/CSRF guards, variant cleanup,
Concierge invalidation, immutable artifacts and idempotency. Browser testing is
scripted integration testing with deterministic model doubles, real local HTTP/MCP
and mocked speech; approvals are simulated.

| Final executed check | Actual result |
|---|---|
| Source/backend suite, after the final source maintenance barrier | 483 passed |
| Full coordinator suite | 716 passed |
| Final focused reset suite, including two subsequently added regressions | 24 passed; overlaps the full suite |
| MCP suite | 56 passed |
| All offline eval families | 112/112 passed; zero critical failures; semantic grader skipped |
| Existing UI suite + connected workflow/Concierge/Operations matrix + reset journey | 80 passed; 3 intentional Operations variant skips |
| Typecheck and production build | Passed; existing 500 kB bundle advisory remains |
| CLI reset/verify and same-storage service restart/verify | Exit 0; baseline valid and identical source/control digests |

The initial coordinator run exposed a race in the developer-only Concierge probe:
it advanced after the investigation status completed but before the host finished
proposal preparation. The helper now waits for that existing host task as well;
the full rerun passed. Runtime prompts, graders and SDK orchestration were not
changed. Initial browser failures and their corrections are recorded in the
verification JSON; no failure was relabeled as a pass.

The new browser fixture persists storage under `.cache/phase09-1/` and restarts the
source/MCP/host services against the same files. Its journey proves mutations survive
restart, explicit reset restores the baseline, then a second restart retains that
baseline. It also checks cross-tab draft invalidation, cases, Decisions, Operations,
search, alerts, historical eval truth and mobile layout.
Inspected captures: [baseline](screenshots/phase09-1/baseline.png),
[explicit confirmation](screenshots/phase09-1/confirmation.png),
[mobile controls](screenshots/phase09-1/mobile.png), and
[preserved eval history](screenshots/phase09-1/preserved-history.png).
All 662 prior screenshot artifacts were preserved byte-for-byte; newly generated
regression captures were retained separately in the isolated verification cache.

Only one local control host should own a demo source/metadata pair. Concurrent
source maintenance fails promptly and is retried explicitly. This is not production
administration/authentication, cross-host coordination or an active scheduler.
Archives intentionally accumulate; retention/deletion tooling is outside this slice.
Historical source/trace/eval files are not deleted. Archived generations have a
management summary; there is no general archive browser or restore-old-run action.
Older incompatible source schemas require the existing explicit stopped-service
migrations before controls can restore them. The working demo databases were not
reset as part of automated verification. No paid live smoke or microphone/provider
speech call was run. The existing bundle-size advisory remains.

**Exact Phase 09.2 starting point:** only after a new explicit request, use this
pre-demo sequence, require `baseline_valid=true`, then perform the golden-path
walkthrough/fixes using the four existing workflows and connected Concierge. Do not
infer authorization for paid model smoke, visual polish, Git cleanup/push,
slides/storytelling or later phases from completion of Phase 09.1.
