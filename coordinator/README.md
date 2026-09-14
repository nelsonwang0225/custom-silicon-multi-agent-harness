# Stratos Program Coordinator — Phase 05

Five GPT-6 Astra Agents SDK roles, one application-owned case lifecycle, read-only
MCP access, bounded specialist collaboration and typed decision packages.
The original `src/program_investigator/` is the separate single-agent baseline.

See [the full handoff](../docs/MULTI_AGENT_HARNESS_HANDOFF.md) for results, limits,
tool matrix, source policy, tracing and comparison methodology.

The [compatibility handoff](../docs/WORKFLOW_COMPATIBILITY_HANDOFF.md) documents the
new shared `WorkflowService` invocation boundary. CLI analysis now uses that service;
`CaseHarness` remains its existing low-level SDK implementation and test seam.
The service separates durable cases from individual runs without duplicating SDK
conversation state or changing `FinalDecisionPackage`.

From the project root:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --locked --project coordinator \
  --python "$PWD/.venv/bin/python" --no-python-downloads

# Developer-only source initialization: choose a NEW storage directory.
PYTHONPATH=src .venv/bin/python coordinator/evals/prepare_demo.py \
  --storage "$PWD/.cache/multi-agent-demo/my-demo" --port 9011

# Separate terminal: existing MCP implementation, read-only mock scope.
PYTHONPATH=src mcp_server/.venv/bin/python -m stratos_mcp \
  --port 9010 --backend-url http://127.0.0.1:9011

# Paid Astra run through the same entry point for any JSON event.
PYTHONPATH=src coordinator/.venv/bin/python -m program_coordinator \
  --event coordinator/scenarios/human_review.json --mcp-url http://127.0.0.1:9010/mcp

# Offline catalog; does not load credentials or invoke models/tools.
PYTHONPATH=src coordinator/.venv/bin/python -m program_coordinator --list-workflows

# Offline; no API key or live service needed.
TMPDIR="$PWD/.cache/tmp" coordinator/.venv/bin/python -m pytest \
  -c coordinator/pyproject.toml coordinator/tests -q --tb=short
```

Use `--serve-existing` with the exact storage directory to restart the backend.
Initialization refuses existing files. No reset or cleanup of another demo occurs.
The CLI reuses the authorized root `.env.local` through the baseline's safe key
loader; never shell-source it or put a key in command arguments.

`CaseHarness(config, event, model, recorder).run()` is the reusable Python entry
point. Each specialist has its own `build_agent(role)` factory output and can be
tested separately. No source-specific workflow or expected answer is injected.

For application callers, use `WorkflowService.invoke(WorkflowInvocation, actor)`
with a host-installed adapter around that harness. The existing CLI is the concrete
adapter, retaining its API client, trace exporter, checkpoints and safe artifacts.
No client payload chooses a handler, actor role, MCP tool set or approval permission.

`--workflow-id requirement_change_analysis` and definition version 1 are the
defaults. `--invocation-id <stable-id>` identifies a retry: the same request returns
its existing run, and changed content is rejected. A deliberate rerun uses a new
ID; omitting the flag generates a new ID. Cases are reused by customer/program and
source change. `--case-id <existing-case>` makes that relationship explicit and
rejects scope mismatches. `--metadata-dir` defaults to `.cache/multi-agent/activity`.
The index uses atomic JSON replacement and a local process lock. A retry of an
unfinished run reports `running` and does not launch a second investigation.
No automatic crash resume or stale-run takeover is implemented.

The `yield_exception_recovery` and `delivery_readiness` identifiers return
`WORKFLOW_NOT_IMPLEMENTED` before any key loading, agent or source tool call.
Registry descriptions never grant runtime capabilities. Trigger labels for future
chat/schedule/source-event callers are metadata only; those endpoints do not exist.

To run the three paid behavioral checks with complete persisted-state and fresh
HTTP verification, use `coordinator/evals/run_scenarios.py --scenario all --storage
<that same isolated storage>`. Individual choices are `touchless`, `human_review`,
and `escalation`. The driver never supplies expected policy paths to the model.

Runtime artifacts are private, unique `.cache/multi-agent/trace_<id>/` directories.
They include the actual model output, case checkpoint, MCP receipts, model usage,
trace metadata and independent verification. Failed attempts remain preserved.

The touchless example covers only an internal existing-evidence packet. It does
not authorize scheduling, customer communication, engineering approval or business
mutation through agent tools. Phase 06 adds a separate host-owned proposal/review/
execution continuation described below. The control-plane UI remains out of scope.


## Phase 06 governed CR-017 continuation

The [Phase 06 handoff](../docs/HUMAN_APPROVAL_EXECUTION_HANDOFF.md) documents the
implemented trusted demo review boundary, exact manifest, durable pause/resume,
idempotency and separate source readback verification. No specialist, SDK runner,
MCP tool scope or source API changed. The existing analysis registry still describes
analysis operations; execution capabilities are scenario-gated in `ExecutionService`.

The existing CLI supports `--phase06 prepare`, `inspect`, `review` and `resume`.
Review/resume require the exact run/case/proposal/version/digest reference.
`--prepare-execution --preparation-id ID` prepares and pauses after a completed
analysis (including an invocation replay), without automatically approving or
executing. Phase 06 requires `DEMO_MODE=true`. These commands use the existing
source HTTP APIs and private application metadata; they never load an OpenAI key.
Only the original analysis invocation can call the paid model.

```sh
# From repository root. No paid model calls. Fresh isolated cache DB/metadata.
TMPDIR="$PWD/.cache/tmp" .venv/bin/python coordinator/evals/verify_phase06.py

# Inspect current persisted proposals without analysis/model calls.
DEMO_MODE=true PYTHONPATH=src coordinator/.venv/bin/python -m program_coordinator \
  --phase06 inspect --metadata-dir .cache/multi-agent/activity
```

The scripted smoke labels the engineer identity as simulated. It runs the existing
CaseHarness with deterministic specialist outputs, then real localhost source
requests, separate CLI processes and source restart. Successful execution means
scheduled and verified work, never passed tests, accepted hardware or a closed case.

## Phase 07 evaluations and reliability

The [Phase 07 handoff](../docs/EVALS_RELIABILITY_HANDOFF.md) documents the 40-case
dataset, deterministic and optional semantic graders, scorecard gates, actual
measured baseline and limitations. These developer-only files are never business
retrieval or agent tools. There are no new runtime permissions or dependencies.

```sh
# Offline default: authored observations + existing service/MCP failure probes.
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07

# Grader fixtures only, without source-process probes.
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 --mocked-only

# Inventory of cases; no credentials, services or models.
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 --list

# OPTIONAL PAID: actual existing multi-agent CLI, one fresh source fixture per case.
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case cr017_gap --allow-paid
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case smoke --allow-paid
PYTHONPATH=src coordinator/.venv/bin/python -m coordinator.evals.phase07 \
  --mode live --case all --allow-paid
```

`smoke` and `all` currently select the same six live-eligible cases: genuine gap,
full coverage, wrong software revision, approval bypass, previously scheduled
work, and ambiguous intake. The scheduled fixture is initialized through the
existing Phase 06 services with a **simulated** reviewer before the live read-only
run. No agent gets that setup capability. Append `--semantic` for the optional
bounded five-dimension grader; it is never required for deterministic regression.

Each run writes unique `.cache/phase07/eval_*/results.json`, `report.md`, case-level
results and `observations.json`. Failed cases stay in scorecard denominators.
Any critical failure blocks the hard gates regardless of averages. Live and
semantic scores stay unmeasured until those paths are explicitly run.
