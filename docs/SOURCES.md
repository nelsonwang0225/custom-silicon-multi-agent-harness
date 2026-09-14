# Sources and provenance

Checked September 10, 2026. These sources support development mechanics only.
All customer, semiconductor, workload, capacity, schedule, cost, and policy records
in this starter pack are original synthetic assumptions. The API paths are our
contracts, not vendor API compatibility claims. Nothing represents confidential
Broadcom, Apple, OpenAI, or any other company's internal process or data.

- OpenAI, Custom instructions with AGENTS.md:
  https://developers.openai.com/codex/guides/agents-md
  Repository guidance is read when Codex starts a task/session.
- OpenAI, Build skills:
  https://developers.openai.com/codex/skills
  Reusable skills use a SKILL.md with metadata and may include scripts/references.
- OpenAI, Prompting Codex:
  https://developers.openai.com/codex/prompting
  Useful tasks name desired behavior, preserve constraints, and define verification;
  planning before edits and scoped implementation are supported workflows.
- FastAPI, First Steps:
  https://fastapi.tiangolo.com/tutorial/first-steps/
  Generated interactive documentation and OpenAPI schema.
- FastAPI, Testing:
  https://fastapi.tiangolo.com/tutorial/testing/
  HTTPX-backed TestClient and pytest integration.

The starter pack is not a production security specification. Its known local-only
role tokens, shared database, fixed clock, simplified review calendar, and synthetic
fixtures deliberately trade deployment realism for a small, testable prototype.
