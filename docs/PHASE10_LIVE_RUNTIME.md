# Live demo runtime

The latest user request switches CR-017, CR-019, QE-004 and DR-009 to the existing
Agents SDK and configured `gpt-6-astra` Responses API. The existing authorized
credential is loaded only after an explicit model invocation is admitted.
Specialists choose and call their scoped MCP tools against the local source
HTTP APIs. Shared knowledge retrieval remains the existing offline index unless
the operator explicitly enables the hosted provider. The source enterprise is
still fictional; live AI does not imply external production systems.

QE-011 is the only scripted case in the live host. Its existing one-shot source
event, source reads, policy validation and independently verified handoff remain
real local operations. Coordinator and four specialists use the disclosed
two-minute presentation sequence. No model request or credential is needed for
this opening. Startup and reset never initiate the four main paid investigations.

`DemoInvestigation` owns the fixed per-case selection. Unsupported cases fail;
model errors never fall back to scripted findings. Each admitted run persists
its execution mode. Case pages show both the mode for the next investigation and
the mode that produced the displayed result. Workspace and search use the saved
run mode, including for old scripted records after the host switches to live.

The existing standard control-host command and `scripts/demo start` install this
configuration. The currently reviewed preview uses the same data and URL as
before, with this explicit launch:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve \
  --root .cache/phase09-3/phase10-autonomous-review-20260912-a \
  --port 18421 --source-port 18422 --mcp-port 19422 \
  --ui-origin http://127.0.0.1:5211 --live-models
```

This flag selects the actual live runtime and live Concierge. Omit it for offline
browser verification. The knowledge-integration scripted launcher rejects this
flag so its test monkeypatches cannot wrap a live run. Restart preserves source
and host state. Use the masthead reset control for a new walkthrough.

Concurrent live runs use one sanitized metadata processor routed by trace ID.
Scripted work suppresses tracing only in its own async context. Completed or
cancelled runs release their recorder. Existing private report, tool-call and
trace metadata artifacts remain authoritative for observed API usage; this does
not claim Platform trace export or dashboard visibility.

CR-019 may complete its policy-authorized intake without another human decision.
CR-017 still requires Engineering approval, and QE-004/DR-009 retain their exact
Program Owner decisions. No new authority, simulated lab results, hold releases,
customer acceptance, or implicit governed execution is introduced.

For an explicitly authorized paid check of all four analyses, with concurrent
scripted QE-011 and newly isolated source storage:

```sh
PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_live.verify --run-paid
```

This probe preserves sanitized per-run API request IDs, token usage and tool
activity plus `verification.json` under `.cache/phase10-live/verify_<id>/`.
It does not approve the governed workflows or modify the working demo database.
Normal automated tests remain offline.
