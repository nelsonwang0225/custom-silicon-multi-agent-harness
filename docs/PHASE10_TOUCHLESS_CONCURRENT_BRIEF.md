# QE-011 touchless and concurrent workflows — implementation brief

Before this refinement: the host globally rejected concurrent workflow runs, although each invocation already owned a case, run, checkpoint, activity and source registry. Manufacturing already permitted standard investigation routing. Planner recovery metadata required an exact Program Owner decision. QE-011 followed that consequential recovery path and automatic browser entry armed it. See the completed implementation in the current handoff.

Latest direction: restore explicit Prepare and delayed source publication; route canonical QE-011 only to the pre-authorized Manufacturing investigation, independently verify it, and omit a recovery proposal/decision. Keep QE-004 recovery governance intact. Allow three configurable concurrent independent cases, retain same-case exclusion and idempotency, and show only one run per workspace graph. Failed policy checks escalate without routing.

No new Planner authority is inferred. No credentials or model configuration change is needed; all verification uses deterministic doubles. The existing authorized Agents SDK remains the runtime.
