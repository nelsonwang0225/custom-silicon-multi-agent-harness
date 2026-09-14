We are starting the mock-enterprise foundation for our semiconductor-program demo.

Read AGENTS.md, README.md, docs/SCENARIO.md, docs/API_CONTRACT.md,
docs/ACCEPTANCE_TESTS.md, fixtures/seed.json, and fixtures/documents/.
Inspect the current repository and local Python/uv/Git availability without
printing secrets, modifying unrelated files, installing packages, or making paid
calls. This phase has NO OpenAI runtime integration or key requirement.

Before writing application code:
1. Check that the proposed synthetic scenario and records are internally consistent.
2. Confirm five logical systems in one API service, with read/write access only for
   Engineering, Validation, and Program Planner; ERP and Manufacturing are read-only.
3. Propose a minimal file layout, endpoint/schema implementation plan, permission
   checks, approval/version model, idempotency behavior, and test sequence.
4. Explicitly explain how approval will authorize an exact plan without becoming
   stale due to its own status update or reservation.
5. Identify genuinely blocking ambiguities or scope that is excessive for a demo.
   Keep the supplied defaults unless a contradiction needs a decision. Do not
   introduce new business use cases, UI work, or production infrastructure.

Write docs/IMPLEMENTATION_PLAN.md and give me a short summary of the plan and any
blocking questions. Do not create application code yet. Stop for my approval.
