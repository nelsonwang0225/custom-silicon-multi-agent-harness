Review the implemented mock-enterprise layer against AGENTS.md,
docs/API_CONTRACT.md, and docs/ACCEPTANCE_TESTS.md. Do not assume the existing tests
prove their own assertions. Inspect handlers, state transitions, permissions,
fixtures, and the smoke path, then fix any in-scope defects and add regression tests.

Focus on approval spoofing or self-approval; stale plan/source state; booking the
same plan twice; altering content under an idempotency key; read-only ERP/MES access;
unintended commitment changes; fabricated test results; and leaked test-oracle files.
Confirm that normal approval and booking do not invalidate their own next step.

Using an isolated demo database, run the tests and start the service on localhost.
Exercise real HTTP reads across all five systems. Prove that an unapproved write
is blocked, then use the explicitly simulated engineer identity to approve the exact
plan, create one lab job, update the planner, and read back persisted changes.
Demonstrate retry safety and partial-failure recovery using test-only hooks or
transport simulation. Restart against the same DB to verify persistence, then run
the guarded local reset and verify the original state.

Record the actual commands/results, endpoint examples, local API-docs address,
limitations, and any unverified checks in docs/BUILD_HANDOFF.md. The smoke test is
scripted—not evidence of agent performance or an actual human review. Do not create
an AI harness or UI. Finish with a pass/fail readiness summary for agent integration.
