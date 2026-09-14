"""One invocation boundary for present CLI and future trusted application callers."""

import asyncio

from ..models import CaseState
from .models import InvocationResult, WorkflowError, WorkflowInvocation
from .registry import dispatch_error


class WorkflowService:
    def __init__(self, store, *, config, investigate, actors, execution_mode="live_model"):
        """`investigate(request, run)` is the existing CaseHarness adapter.

        The host installs it once; request/trigger/catalog metadata cannot choose
        another handler or supply tools, model configuration, credentials or roles.
        `actors` contains identity objects resolved by trusted host configuration.
        """
        if execution_mode not in {"live_model", "deterministic_test"}:
            raise ValueError("Explicit live or deterministic-test mode required")
        self.store, self.config, self.investigate = store, config, investigate
        self.actors = {actor.actor_id: actor for actor in actors}
        self.execution_mode = execution_mode

    def validate_actor(self, actor):
        if self.actors.get(getattr(actor, "actor_id", None)) is not actor:
            raise WorkflowError("UNTRUSTED_ACTOR_CONTEXT")

    async def invoke(self, request, actor, *, trace_id=None, artifact_directory=None):
        try:
            self.validate_actor(actor)
            request = WorkflowInvocation.model_validate_json(request.model_dump_json())
            error = dispatch_error(request.workflow_id, request.definition_version, request.operation)
            if error:
                return InvocationResult(status="unsupported", error_code=error)
            actor.require_scope(request.customer_id, request.program_id)
            if (request.customer_id, request.program_id) != (self.config.customer_id, self.config.program_id):
                raise WorkflowError("MCP_SCOPE_MISMATCH")
            for field in ("customer_id", "program_id"):
                if getattr(request.event, field) is not None and getattr(request.event, field) != getattr(request, field):
                    raise WorkflowError("EVENT_SCOPE_MISMATCH")
            run, replayed = self.store.claim(request, actor, execution_mode=self.execution_mode,
                trace_id=trace_id, artifact_directory=artifact_directory)
        except WorkflowError as exc:
            return InvocationResult(status="rejected", error_code=str(exc))
        if replayed:
            return InvocationResult(status=run.status, replayed=True, error_code=run.error_code, run=run)
        try:
            state = await self.investigate(request, run)
            state = CaseState.model_validate_json(state.model_dump_json())
            completed = self.store.finish(run.run_id, state=state)
            return InvocationResult(status="completed", run=completed)
        except asyncio.CancelledError:
            self.store.finish(run.run_id, error_code="ANALYSIS_CANCELLED", cancelled=True)
            raise
        except Exception:
            # Detailed, sanitized technical errors already belong in the existing
            # run artifacts. Never copy arbitrary exception text into activity.
            failed = self.store.finish(run.run_id, error_code="ANALYSIS_FAILED")
            return InvocationResult(status="failed", error_code=failed.error_code, run=failed)

    def timeline(self, actor, **scope):
        self.validate_actor(actor)
        return self.store.timeline(actor, **scope)

    def runs(self, actor, **scope):
        self.validate_actor(actor)
        return self.store.runs(actor, **scope)

    def cases(self, actor, **scope):
        self.validate_actor(actor)
        return self.store.cases(actor, **scope)
