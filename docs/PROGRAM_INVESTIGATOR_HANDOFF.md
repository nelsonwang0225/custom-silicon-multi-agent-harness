# Phase 04 — Step 6: ProgramInvestigator

`ProgramInvestigator` investigates an engineering/program change and returns a typed,
source-backed assessment for human engineering review. It is one OpenAI Agents SDK
agent using **gpt-6-astra** through the Responses API. Business access follows:

```text
Case trigger → ProgramInvestigator / Agents SDK / GPT-6 Astra
             → SDK MCPServerStreamableHttp → Stratos MCP :9000/mcp
             → EnterpriseClient → Stratos HTTP APIs :9001 → five mock applications
```

The model chooses its business reads. The host performs protocol discovery before
the first model generation; it does not supply a case answer, prefetch the case for
the agent, prescribe a tool sequence, or iterate over the catalog. The agent has no
local function tools, filesystem/database access, direct enterprise client, handoffs,
approval/scheduling capabilities, retrieval, model routing, or control-plane UI.

## Official guidance and isolated dependencies

Checked current official guidance and installed SDK implementation on 2026-09-11 UTC:

- [Agents SDK MCP](https://openai.github.io/openai-agents-python/mcp/): supported
  `MCPServerStreamableHttp`, static tool filters, structured results and MCP v2 compatibility.
- [Agents SDK agents](https://openai.github.io/openai-agents-python/agents/): `Agent`,
  instructions, `Runner.run`, Pydantic output types and model settings.
- [Tracing](https://openai.github.io/openai-agents-python/tracing/): explicit traces,
  sensitive-data exclusion, custom processors, batch exporter and final flushing.
- [Agents guide](https://developers.openai.com/api/docs/guides/agents) and
  [agent evaluations](https://developers.openai.com/api/docs/guides/agent-evals):
  inspect real tool/model behavior and keep evaluation separate from the application.
- [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra): requested model.

`investigator/pyproject.toml` and `investigator/uv.lock` manage `investigator/.venv`.
Python is the existing **3.12.10**. Locked packages include **openai-agents 0.22.2**,
**openai 3.13.0**, **mcp 2.2.0**, **Pydantic 2.13.5**, **python-dotenv 1.2.3**,
**HTTPX2 2.12.0** for the current SDK transports, and **HTTPX 0.28.1** for the
independent verifier. There are 46 installed packages including offline tests.
The root/backend and MCP environments, their lockfiles, existing enterprise client,
backend routes and frontend source remain unchanged. No Git operation is required.

## Modules

| Module | Responsibility |
| --- | --- |
| `src/program_investigator/agent.py` | One `Agent`, supported MCP attachment, user case input, bounded `Runner.run`. |
| `instructions.py` | General investigation policy, source-vs-instruction separation, evidence and review rules. |
| `models.py` | Strict nested `InvestigationResult` and internal consistency validation. |
| `mcp.py` | Explicit read-tool filter, annotation checks, guarded MCP results and correlation receipts. |
| `validation.py` | Generic checks against actual tool calls: citations/versions, coverage, evidence, all option fields. |
| `config.py` | Loopback endpoint validation and secure `.env.local` loader. |
| `telemetry.py` | Generation usage/latency, local safe span metadata and export-payload/error redaction. |
| `__main__.py` | Explicit paid CLI, in-memory key use, safe error categories, trace flushing and artifacts. |
| `revalidate.py` | Offline revalidation of a saved model assessment; no model calls or business edits. |
| `investigator/tests/test_investigator.py` | Offline boundary/schema/error/source-validation checks. |
| `investigator/evals/verify_cr017.py` | Independent HTTP oracle and before/after comparison, never agent-accessible. |

## Run commands

From the project root, install the isolated locked environment:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --locked --project investigator \
  --python "$PWD/.venv/bin/python" --no-python-downloads
```

The existing MCP server must be running and scoped to the target customer/program.
See [MCP_SERVER_HANDOFF.md](MCP_SERVER_HANDOFF.md) for its startup, readiness and
shutdown commands. The actual Step 6 target is `http://127.0.0.1:9000/mcp`, backed
by `http://127.0.0.1:9001` and the existing `.demo/mcp-step5.sqlite3` demo.
The older service on port 8000 is not the integration target. No database was reset.

This command makes paid OpenAI requests:

```sh
PYTHONPATH=src investigator/.venv/bin/python -m program_investigator \
  --case-id CR-017 --customer "Helios AI" \
  --mcp-url http://127.0.0.1:9000/mcp
```

The reusable Python entry point is `run_investigation(config, case_id, customer,
model, recorder)`. The CLI creates the SDK Responses model and tracing context.
Importing the package does not read credentials, connect services or call a model.

## Credentials, identity and failure behavior

The CLI loads only `OPENAI_API_KEY` from the authorized `.env.local`. It requires an
owner-owned, mode-0600, single-link regular file and rejects symlinks, oversized
files and malformed values. Dotenv interpolation and shell sourcing are disabled.
The key is passed in memory to the official OpenAI client and tracing exporter.
It is never passed to MCP, made a tool argument, printed or stored in run artifacts.
SDK diagnostics are suppressed; artifact writing additionally redacts the loaded key.
`.env.local` remains ignored. CLI stdout reports safe run metadata, not raw errors.

MCP uses the existing server-owned **demo-reader-local-only** mock selector scoped
to **CUST-FML01 / PRG-A17**. This is a public synthetic role-test identity, not
production authentication. The agent cannot select identities or widen the scope.
Its local MCP HTTP client disables environment proxies and redirects; its endpoint
accepts only credential-free loopback HTTP `/mcp` URLs. Source access remains the
enterprise client's existing fixed GET routes and server authorization checks.

MCP connect timeout is 2 seconds, read/session timeout 60 seconds, write/pool timeout
5 seconds, with no outer MCP retries. Existing enterprise-client GET retries remain
bounded to two for its documented safe read failures. Model requests use a 10-second
HTTP connect timeout, 180-second request timeout and at most one SDK retry. The run
has a 900-second deadline and 24 model-turn limit; each generation is capped at
16,000 output tokens, with medium reasoning and response storage disabled.

Discovery must return all expected read names with read-only, non-destructive,
idempotent, closed-world annotations. Unknown tool names are filtered out. Calls
outside the allowlist, malformed envelopes, source errors, invalid correlation
receipts and source/output mismatches stop the assessment with fixed error codes.
MCP unavailability is detected before `Runner.run`; no fallback business route exists.
No automatic workflow restart or model-generated business write is available.

## Exposed catalog

All 25 tools are attached through the supported SDK MCP integration. Complete input
and endpoint mapping remains in [the MCP handoff](MCP_SERVER_HANDOFF.md#catalog-and-source-mapping).
The exact discovered descriptions, schemas and annotations are saved as `catalog.json`.

| System | Tools |
| --- | --- |
| Engineering Hub | `get_change_request`, `get_requirement_revision`, `get_configuration`, `get_workload_profile`, `get_procedure`, `get_policy`, `get_acceptance_criteria`, `get_document`, `get_documents`, `get_plan`, `get_decision` |
| Validation Lab | `get_validation_coverage`, `get_validation_options`, `get_validation_result`, `get_validation_samples`, `get_validation_jobs`, `get_validation_job` |
| Manufacturing Portal | `get_manufacturing_unit`, `get_manufacturing_lot` |
| Commercial ERP | `get_customer_order`, `get_cost_rates` |
| Program Planner | `get_program`, `get_program_milestone`, `get_dependencies`, `get_implementation_links` |

## Structured output and validation

`InvestigationResult` contains `case_id`, customer/program entities, `change_summary`,
`affected_scope`, `confirmed_facts`, `validation_coverage_status`, `evidence_gaps`,
`relevant_evidence`, `manufacturing_constraints`, `customer_commitment`,
`program_milestone`, `eligible_options`, `ineligible_options`, `risks`,
`unresolved_questions`, `recommended_next_step`, `requires_human_review` and
`source_references`.

Findings carry a basis (`fact`, `inference`, `missing_information`, `question`,
`recommendation`) and source references. References identify an actual tool call
by name and exact inputs, optionally a returned record ID and content/record version.
Evidence preserves result IDs, applicability, status and every mismatch reason.
Manufacturing context identifies unit-to-lot provenance and both restriction lists.
Commitments keep quantity/units/date separate from milestone baseline/forecast/status.
Options preserve the slot/sample pair, relevant source IDs, integer-cent money,
currency, all eligibility flags/reasons and the API's exact timing object.

An eligible option has all three API flags true: resource eligibility, approval
eligibility and deadline feasibility. Other options remain visible with their reasons.
These flags establish candidates for review, not actual approval. No option ranking
or winner is hard-coded. The generic validator compares every returned option and
evidence record with actual MCP data and rejects missing/altered numeric facts.
It also checks citations, versions, coverage consistency and required human review.
Citation names normalize the optional `functions.` namespace, then must match an
actually executed MCP tool and exact inputs. Dependency projection citations use
their authoritative `milestone_id` and `record_version`.
It does not claim to mechanically prove every prose assertion; independent review
of the live assessment is documented below.

## Traces and artifacts

Tracing is explicitly enabled. `trace_include_sensitive_data=False` excludes model
and tool payloads from SDK spans. A processor also clears input/output fields and
replaces exception messages before the official batch exporter receives them.
Safe custom spans cover discovery, each read receipt and structured-output completion.
Generation hooks record response/request IDs, latency and token metadata, never
private model reasoning. Response IDs remain in SDK traces even with storage disabled.

The trace groups by case ID. Each custom read span carries the MCP `call_id` and
`correlation_id`; local receipts link these to backend `request_id` and matching
server correlation echoes. The agent includes case/trace IDs in MCP `_meta` as
non-authorizing context. The current MCP server deliberately does not trust inbound
metadata as scope or replace its own IDs; the returned receipt is the correlation link.

After the trace context closes, the CLI calls `flush_traces()`. Inspect the
[OpenAI Platform Traces dashboard](https://platform.openai.com/traces) in the project
associated with the configured key, locate workflow **ProgramInvestigator**, and
match the trace ID/case metadata in `report.json`. Expand model/function/custom spans.
Export flushing is recorded locally; visibility in the authenticated Platform UI
is not asserted without inspecting that UI.

Each unique `.cache/program-investigator/trace_<id>/` folder contains:

- `report.json`: safe status, model requests, usage/latency and trace metadata.
- `catalog.json`: discovered tool definitions.
- `tool-calls.json`: actual tool arguments, raw synthetic authoritative data and GET receipts.
- `trace-metadata.json`: safe span identifiers/types/timestamps/errors.
- `result.json`: accepted typed assessment; rejected candidates use `rejected-result.json`.
- `verification.json`: separate verifier results after a successful run.
- `revalidation.json`: immutable offline validation receipt when recovering a saved candidate.
- `run-summary.json`: measured live-run/recovery/verification summary for this handoff.

Directories/files use owner-only creation; previous runs are never overwritten.
The model has no tool that reads these files or the independent oracle.

## Verification commands

```sh
TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q \
  tests runtime_checks/test_openai_connection.py --tb=short
TMPDIR="$PWD/.cache/tmp" mcp_server/.venv/bin/python -m pytest \
  -c mcp_server/pyproject.toml mcp_server/tests -q --tb=short
TMPDIR="$PWD/.cache/tmp" investigator/.venv/bin/python -m pytest \
  -c investigator/pyproject.toml investigator/tests -q --tb=short
uv pip check --python investigator/.venv/bin/python
```

For a separately verified run, capture a unique pre-run HTTP snapshot with:

```sh
PYTHONPATH=src:. investigator/.venv/bin/python investigator/evals/verify_cr017.py \
  --before .cache/program-investigator/source-before.json
```

After running the agent, pass the same snapshot and the exact artifact directory:

```sh
PYTHONPATH=src:. investigator/.venv/bin/python investigator/evals/verify_cr017.py \
  --before .cache/program-investigator/source-before.json \
  --run-dir .cache/program-investigator/trace_REPLACE_WITH_ACTUAL_ID
```

The verifier alone reads through the enterprise client/public HTTP APIs. It checks
the full scoped source context, portfolio and audit data before/after, replays the
actual MCP calls against fresh HTTP records, and validates the golden case separately.
It never reads the live SQLite database or supplies facts to the agent.

## Actual run results

**PASS after a transient request retry and offline correction of citation validation.**
Two actual Astra workflows were attempted. There were eight completed Responses
generations in total; the saved assessment came from five generations in attempt 2.
No model was asked to grade itself. No third paid workflow was necessary.

| Attempt | UTC start | Trace ID | Outcome |
| --- | --- | --- | --- |
| 1 | 2026-09-11 03:03:43 | `trace_4e6e45924c8e4278837bc5a490967555` | Three authenticated completed generations and 20 MCP calls; a later model request raised `APIConnectionError`. No final assessment. |
| 2 | 2026-09-11 03:04:49 | `trace_ef4ecc86847c44bb9db87174587f28a7` | Five authenticated completed generations, 25 MCP calls, typed assessment produced. The host citation checker initially rejected namespace/projection spelling; offline revalidation now passes. |

The first failure was a model transport failure, not a 401, quota response or MCP
failure. Its underlying network cause was not retained and is not claimed. One
bounded SDK retry plus safe exception-class diagnostics were added; the next workflow
completed all model generations. Neither instructions nor source data changed.

The second run used `functions.get_*` in its citation names and correctly cited the
dependency projection's `milestone_id`. The initial checker expected unprefixed names
and recognized only `id`/`change_id`. The minimal fix normalizes that optional namespace
and recognizes the existing projection contract. Tests cover both and still reject
invented tools, inputs, IDs and versions. The original model candidate and failed-run
report remain preserved. Revalidation changed only citation spelling, made **zero
model calls**, and retained every business assertion and option field. Its command was:

```sh
PYTHONPATH=src investigator/.venv/bin/python -m program_investigator.revalidate \
  --run-dir .cache/program-investigator/trace_ef4ecc86847c44bb9db87174587f28a7
```

Thus the final implementation's validation path was checked offline against the actual
live model output; a third full paid CLI run after the validator fix was deliberately
not performed. `report.json` accurately retains the original process failure, while
`revalidation.json`, `verification.json` and `run-summary.json` record final acceptance.

### Actual tools selected

The successful assessment used **17 distinct tools, 25 calls, 53 underlying HTTP GETs**.
The model first read the change; then requirements/configuration/program, coverage,
options, order/milestone/dependencies and current execution state; then workload,
procedure/policy, manufacturing units; finally source lots and procedure/policy documents.
Those are observed choices, not a host-scripted sequence. Independent calls were
batched by the model. Counts below refer to attempt 2, not the independent verifier.

| Tool | Calls |
| --- | ---: |
| `get_change_request` | 1 |
| `get_requirement_revision` | 2 |
| `get_configuration` | 1 |
| `get_program` | 1 |
| `get_validation_coverage` | 1 |
| `get_validation_options` | 1 |
| `get_customer_order` | 1 |
| `get_program_milestone` | 1 |
| `get_dependencies` | 1 |
| `get_document` | 3 |
| `get_validation_jobs` | 1 |
| `get_implementation_links` | 1 |
| `get_workload_profile` | 2 |
| `get_procedure` | 1 |
| `get_policy` | 1 |
| `get_manufacturing_unit` | 3 |
| `get_manufacturing_lot` | 3 |

It did not call `get_acceptance_criteria`, `get_documents`, `get_plan`, `get_decision`,
`get_validation_result`, `get_validation_samples`, `get_validation_job` or `get_cost_rates`.
Coverage already supplied historical results and criteria snapshots; options supplied
sample records and approved rates. Empty plans/jobs gave no detail IDs to follow.
The three documents read were the customer request, procedure and approval policy.

### Business checks and assessment

**All 17 deterministic verification checks passed**, and separate review of the prose
confirmed facts vs inference, no fabricated results/acceptance, the numerical-criteria
limitation, administrative hold provenance and a human engineering review recommendation.

- Customer **HELIOS AI / CUST-FML01**; program **Helios Atlas Inference / PRG-A17**.
- The requested revision changes **REQ-042-V1 → REQ-042-V2** and workload
  **WF-LC-V1 → WF-LC-V2**: bins `[8192, 32768]` → `[32768, 65536, 131072]`,
  suite 120 → 480 minutes. Concurrency 4, output tokens 1024 and the acceptance
  reference remain unchanged. The baseline is approved; the proposal is requested.
- Affected **ACCELERATOR-X REV-B / CFG-B-01** retains MODEL-LAB-07, one device,
  FW-2.3, RT-4.1, QFMT-1 and MEM-1. The model did not claim silicon redesign or root cause.
- The API reports **coverage_satisfied=false**. RES-BASELINE-B has insufficient
  duration, missing bins and wrong profile; RES-LONG-A has wrong configuration/revision;
  RES-SHORT-B has insufficient duration. All are historical completed passes, none
  satisfies the new request. Exact mismatch lists and covered bins match the source.
- UNIT-B-018 traces to **LOT-4492**, content version 2, with an engineering hold for
  pending traceability disposition. The output correctly distinguishes this administrative
  restriction from hardware failure, and records the responsible team/release condition.
  UNIT-B-017 / LOT-4491 has no hold; UNIT-A-010 / LOT-4480 is REV-A and inapplicable.
- **ORD-1204** remains an open commitment for **100 accelerator units**, delivery
  **2026-11-23T18:00:00Z**. **MS-ACCEPT-01** has baseline and current forecast
  **2026-11-19T18:00:00Z**, status `not_reassessed_for_new_request`, and a pending
  REQ-042-V2 dependency. Customer commitment and internal forecast are kept separate.
- All nine API options are represented once, with exact costs/flags/timing/reasons.
  There is one currently on-time eligible candidate, eight others retained for review.
  Candidate eligibility is not approval, scheduling, test execution or acceptance.
- The recommendation is to bring evidence scope, all alternatives, source-lot hold,
  review ownership and milestone impact to the engineering SME. Human review remains
  required. No plan, approval, job or implementation link was created.

The API option matrix reproduced in the structured assessment is:

| Slot / sample | Cost (USD cents) | Resource / approval eligible | Deadline | Source reasons |
| --- | ---: | --- | --- | --- |
| PRIORITY / A-010 | 180000 | false / false | null | SAMPLE_CONFIGURATION_MISMATCH |
| PRIORITY / B-017 | 180000 | true / true | true | none |
| PRIORITY / B-018 | 180000 | false / false | null | MANUFACTURING_RESTRICTION |
| STANDARD / A-010 | 0 | false / false | null | SAMPLE_CONFIGURATION_MISMATCH |
| STANDARD / B-017 | 0 | true / true | false | none; timing misses deadline |
| STANDARD / B-018 | 0 | false / false | null | MANUFACTURING_RESTRICTION |
| UNQUALIFIED / A-010 | 60000 | false / false | null | LAB_CONFIGURATION_UNSUPPORTED; SAMPLE_CONFIGURATION_MISMATCH |
| UNQUALIFIED / B-017 | 60000 | false / false | null | LAB_CONFIGURATION_UNSUPPORTED |
| UNQUALIFIED / B-018 | 60000 | false / false | null | LAB_CONFIGURATION_UNSUPPORTED; MANUFACTURING_RESTRICTION |

Slot IDs have prefix `SLOT-`; sample IDs have prefix `SAMPLE-`. Only the two
resource-eligible combinations have calculated timing. PRIORITY/B-017 starts in lab
2026-11-18 06:00 UTC, execution 08:00, ends 16:00, review-ready 20:00, **1320 minutes
slack**. STANDARD/B-017 starts 2026-11-20 08:00 UTC, execution 10:00, ends 18:00,
review-ready 22:00, **-1680 minutes slack**. These are copied API results, not new calculations.

Every actual MCP result matched a fresh authoritative HTTP read. All 53 request
receipts are GET/200 and carry matching correlation echoes. The complete scoped
source context, portfolio and audit snapshot hashes were identical before/after:
`dde0816523bea1e308e882d24cd3793ad20a9896776c3708aa0e3063dea99a37`.
This HTTP comparison and the read-only capability/request evidence establish no
business write in this run; it is not a claim of an inspected global SQLite snapshot.

### Measured usage, latency and traces

| Metric | Attempt 1 | Attempt 2 assessment | Combined observed |
| --- | ---: | ---: | ---: |
| Completed model generations | 3 | 5 | 8 |
| Input tokens | 33047 | 84348 | 117395 |
| Cached input tokens (subset) | 9215 | 62768 | 71983 |
| Output tokens | 472 | 7378 | 7850 |
| Reasoning tokens (subset) | 0 | 45 | 45 |
| Total tokens | 33519 | 91726 | 125245 |
| End-to-end process latency | 16557.93 ms | 106613.51 ms | — |
| Summed generation latency | 14953.80 ms | 104941.58 ms | — |

All eight returned model responses report **gpt-6-astra**, **completed**, HTTP **200**;
authentication succeeded. The first attempt's later connection failure has no response
usage, so totals are observed completed-response usage, not an invoice or exact charge.
No dollar price is inferred. The five generation latencies in attempt 2 were
3222.43, 6401.61, 3943.05, 4440.70 and 86933.79 milliseconds.

Attempt 2's local SDK trace metadata contains one agent span, one task span,
five turn spans, five response spans, five MCP discovery spans (catalog caching enabled),
25 function spans and 26 custom discovery/read spans. The actual CLI produced its
typed output before the host citation-validation failure. Final acceptance is captured
in the offline revalidation receipt; it is not retroactively presented as a successful
Platform trace. The corrected code also traces subsequent source-validation completion.
Both workflows enabled tracing and completed final exporter flushing. Authenticated
Platform UI visibility was not checked.

Artifacts for the accepted assessment:

- [Typed result](../.cache/program-investigator/trace_ef4ecc86847c44bb9db87174587f28a7/result.json)
- [Consolidated run summary](../.cache/program-investigator/trace_ef4ecc86847c44bb9db87174587f28a7/run-summary.json)
- [Actual MCP records and HTTP receipts](../.cache/program-investigator/trace_ef4ecc86847c44bb9db87174587f28a7/tool-calls.json)
- [Independent verification](../.cache/program-investigator/trace_ef4ecc86847c44bb9db87174587f28a7/verification.json)
- [Offline validation receipt](../.cache/program-investigator/trace_ef4ecc86847c44bb9db87174587f28a7/revalidation.json)

### Actual test results

| Check | Result |
| --- | --- |
| Existing backend/client/offline connectivity tests | **282 passed**, 46.31 s |
| Existing MCP tests, including isolated database/real HTTP integration | **56 passed**, 10.67 s |
| Final agent offline tests | **39 passed**, 1.37 s |
| Isolated dependency compatibility | **46 packages compatible** |
| Live MCP discovery preflight | **25 tools**, correct agent/model, strict output schema |
| Independent CR-017 verification | **17/17 passed**, 25 exact tool-result comparisons, 53 GET receipts |
| Protected application/dependency files | **54 checked, zero changes** by SHA-256 |

Total: **377 automated tests passed**. The initial offline test used an incorrect SDK
attribute name; the test was corrected before the live run. Added regression tests
cover namespace/projection citations, altered money/missing options, safe transport
failure, offline recovery preservation and the final Runner result-processing path.
The existing isolated database suites were actually executed; the live verifier uses
HTTP and does not read SQLite. Frontend browser/build checks were not repeated because
frontend source and dependencies were unchanged. No large paid evaluation sweep ran.

## Limits and next phase

This is a bounded local prototype and one case evaluation, not evidence of reliability
across all programs or all model behaviors. Generative wording/tool selection may vary.
Malformed/unavailable sources fail closed; restarting a failed CLI starts a new paid
investigation. A saved candidate can be revalidated offline after a validation-code fix,
without changing its business assessment. No model-session resume or production
authentication is implemented.

The next phase can consume `InvestigationResult` as a typed handoff to a separately
scoped engineering-review agent and add targeted cross-case evaluations. Any later
write/approval orchestration requires its own explicit implementation and authorization
boundaries. No such agents, orchestration or write actions are implemented here.

**PROGRAM INVESTIGATOR STATUS: PASS**
