Proceed with the mock-enterprise implementation from the reviewed plan, including
any clarifications we agreed. Read AGENTS.md and the scenario, API, test, and fixture
files again. Implement only this phase, not the future OpenAI agents or frontend.

Build a local Python FastAPI service with five logical domain modules and persistent
SQLite state. Use the supplied seed records and business documents, typed schemas,
scoped HTTP reads/writes, generated OpenAPI docs, a guarded local reset command,
and automated tests. Keep dependencies small and local to the project.

Implement in these increments and run relevant checks after each:
A. Startup, database/seed loading, all read APIs, coverage checks, and option math.
B. Draft plans and role-authorized immutable approvals, then lab-job/resource
   creation and planner linking with real persistence.
C. Idempotency, stale-state rejection, protected domains, auditability, and negative
   tests. Security boundaries must be in code, not documentation or prompts only.
D. A scripted HTTP smoke test, a concise README with working commands, and an
   exported OpenAPI schema. Label simulated identities and scripted execution.

Do not bypass the HTTP boundary in the integration smoke script, hard-code the
preferred option, auto-approve, auto-pass tests, or change immutable commitments.
Do not add OpenAI/Agents SDK dependencies, API keys, model calls, React, Docker,
MCP servers, real enterprise connectors, or public reset/admin endpoints.

Run the checks you can actually run. Fix failures without weakening the contract.
Report changed files, commands and actual results, skipped checks, and remaining
limitations. Update docs/BUILD_HANDOFF.md. Stop when the mock API layer is ready
for review; do not continue into the agent phase.
