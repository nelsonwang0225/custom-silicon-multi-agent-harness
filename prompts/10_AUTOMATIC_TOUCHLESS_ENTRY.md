# Direct user follow-up: automatic touchless opening and full roster

How do we reset the entire demo, getting back to the initial state?

Have all agents displayed by default. If an agent isn't used, put it on Idle.
QE-011 should run autonomously in the background after starting the demo, with
processing colors and moving dots for active agents. It must not require human
assessment/approval on its standard path.

This supersedes the explicit-Prepare and participating-only presentation in the
preceding touchless/concurrent request. Reuse the existing eight-second source
event, touchless policy, runtime, bounded concurrency and reset boundaries.
Do not simulate work or change the other workflows' approval requirements.

Implementation interpretation: entering the local control plane automatically
arms one opening for a cleared demo. Reloads/tabs join a running or recorded
opening. Reset leaves the current page at baseline; a reload or explicit Replay
starts a new opening. Process startup alone does not replay unfinished work.
Verification uses isolated deterministic agents and no paid calls. Explain reset
steps; do not reset the user's existing working data merely to answer the question.
