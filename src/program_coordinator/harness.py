"""Coordinator-owned lifecycle with bounded dynamic specialist collaboration.

Scheduling, budgets and state are ordinary application code; domain reasoning is
performed by SDK Agent/Runner invocations. No handoff transfers case ownership.
"""

import asyncio
import json
import time
from uuid import uuid4

from agents import RunConfig, Runner, function_tool
from agents.exceptions import ModelBehaviorError
from agents.tracing import custom_span
from openai.types.responses import ResponseOutputMessage
from pydantic import ValidationError

from program_investigator.telemetry import MetadataHooks, usage_metadata
from .agents import build_agent, OUTPUTS
from .controls import HarnessConfig, HarnessError, GRAPH, transition, validate_workflow, failure_code
from .mcp import ScopedMCP
from .models import (CaseState, ProgramChangeEvent, WorkRequest, Invocation, SpecialistResult,
                     TriageDecision, CoordinatorReview, FinalDecisionPackage, Model, AssessmentUnion, scoped_work_output,
                     ValidationEvidenceAssessment, ValidationClarificationResult)
from .policy import determine_policy, AdministrativeRequest
from .sources import SourceRegistry, canonical, validate_assessment, validate_final, apply_review
from .status_inspection import status_scope_error, validate_status_reads


class ConsultationReceipt(Model):
    status: str
    invocation_id: str | None
    reason: str
    result: SpecialistResult | None


def final_output_diagnostic(text):
    """Private schema diagnostics: no invalid input values or SDK response items."""
    try:
        output = FinalDecisionPackage.model_validate_json(text, strict=True).model_dump(mode="json")
        return {"output": output, "schema_errors": []}
    except ValidationError as exc:
        schema = FinalDecisionPackage.model_json_schema()
        fields = set(schema.get("properties", {}))
        for definition in schema.get("$defs", {}).values():
            fields.update(definition.get("properties", {}))
        return {"output": None, "schema_errors": [
            {"type": e["type"], "constraint": {
                "Value error, Review flag must match policy path": "review_flag_matches_policy",
                "Value error, Escalation reason required": "escalation_reason_required",
                "Value error, Confirmed facts must be factual": "confirmed_facts_are_factual",
                "Value error, Facts require exact source assertions": "facts_have_source_assertions",
                "Value error, Assertion must cite its receipt": "assertion_cites_receipt",
             }.get(e["msg"], "schema_constraint"),
             "path": [p if isinstance(p, int) or p in fields else "unknown_field"
                                      for p in e["loc"]]}
            for e in exc.errors(include_input=False, include_url=False)[:20]]}


class CaseHooks(MetadataHooks):
    def __init__(self, harness, role, invocation_id, phase):
        super().__init__(harness.recorder)
        self.harness, self.role, self.invocation_id, self.phase = harness, role, invocation_id, phase

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        if self.role == "coordinator":
            if self.harness.coordinator_turns >= self.harness.config.max_coordinator_turns:
                raise HarnessError("max_coordinator_turns")
            self.harness.coordinator_turns += 1
        await super().on_llm_start(context, agent, system_prompt, input_items)

    async def on_llm_end(self, context, agent, response):
        await super().on_llm_end(context, agent, response)
        self.recorder.generations[-1].update(role=self.role, invocation_id=self.invocation_id, phase=self.phase)
        if self.role == "coordinator" and self.phase in {"reconcile", "synthesis"}:
            # The SDK may reject a bounded enum before Runner returns a typed
            # result. Capture only the public assistant message's typed review,
            # not reasoning items, tool payloads, or the complete model response.
            text = "".join(part.text for item in response.output if isinstance(item, ResponseOutputMessage)
                for part in item.content if part.type == "output_text")
            if self.phase == "synthesis":
                self.harness.final_output_diagnostic = final_output_diagnostic(text)
                return
            try:
                self.harness.pending_review_output = CoordinatorReview.model_validate_json(text).model_dump(mode="json")
            except ValidationError:
                self.harness.pending_review_output = None


class CaseHarness:
    def __init__(self, config, event, model, recorder, *, runner=Runner.run, server_factory=ScopedMCP, checkpoint=None,
                 case_id=None, run_id=None, workflow_id=None, workflow_definition_version=None,
                 reconciliation_diagnostic=None):
        self.config: HarnessConfig = config
        self.state = CaseState(case_id=case_id or "case_" + uuid4().hex, correlation_id=event.correlation_id,
            customer_id=event.customer_id, program_id=event.program_id, event=event,
            run_id=run_id, workflow_id=workflow_id, workflow_definition_version=workflow_definition_version)
        self.model, self.recorder, self.runner, self.server_factory = model, recorder, runner, server_factory
        self.sources = SourceRegistry(self.state)
        self.catalog = {}
        self.standard_route = False
        self.delivery_route = workflow_id == "delivery_readiness"
        self.quality_route = workflow_id == "yield_exception_recovery"
        self.intake = {}
        self.intake_source_ids = set()
        self.coordinator_turns = 0
        self.tool_calls_started = 0
        self.started = time.perf_counter()
        self.seen_requests = set()
        self.parallel_branches = []
        self.delegations = []
        self.rejected_outputs = {}
        self.rejected_reviews = []
        self.pending_review_output = None
        self.final_output_diagnostic = None
        self.reconciliation_diagnostic = reconciliation_diagnostic
        self.checkpoint_callback = checkpoint
        from .knowledge.integration import current_knowledge_context
        self.knowledge_context = current_knowledge_context.get()

    def elapsed(self):
        return round((time.perf_counter() - self.started) * 1000, 2)

    def checkpoint(self):
        if self.checkpoint_callback:
            self.checkpoint_callback(self.state.model_dump(mode="json"))

    def move(self, stage):
        transition(self.state, stage)
        self.checkpoint()

    def flag(self, code):
        self.state.guardrail_events.append(code)
        with custom_span("case.guardrail", {"case_id": self.state.case_id, "code": code}):
            pass
        self.checkpoint()

    async def intake_case(self):
        event = self.state.event
        missing = [name for name in ("change_id", "customer_id", "program_id") if not getattr(event, name)]
        if missing:
            self.state.unresolved_questions.append("Missing intake fields: " + ", ".join(missing))
            self.flag("incomplete_intake")
            return
        if event.customer_id != self.config.customer_id or event.program_id != self.config.program_id:
            self.state.unresolved_questions.append("The event customer/program does not match the configured MCP scope.")
            self.flag("intake_scope_mismatch")
            return
        if self.delivery_route:
            from .delivery import intake
            return await intake(self)
        if self.quality_route:
            from .quality import intake
            return await intake(self)
        # Only high-level identity/request reads. No deterministic domain answer is
        # prefetched; specialist tools remain model-selected.
        async with self.server_factory(self, "coordinator", "intake") as server:
            await server.list_tools()
            for name, tool, args in (("program", "get_program", {"program_id": event.program_id}),
                                    ("change", "get_change_request", {"change_id": event.change_id})):
                await server.call_tool(tool, args)
                self.intake[name] = self.sources.calls[-1]
            change = self.intake["change"]["data"]
            await server.call_tool("get_document", {"document_id": change["request_document_id"]})
            self.intake["request"] = self.sources.calls[-1]
            doc = self.intake["request"]["data"]
            self.standard_route = doc.get("document_type") == "standard_validation_request"
            if doc.get("document_type") == "coordination_request":
                try:
                    request = AdministrativeRequest.model_validate_json(doc["content"])
                except ValidationError:
                    raise HarnessError("invalid_administrative_request") from None
                await server.call_tool("get_document", {"document_id": request.policy_document_id})
                self.intake["policy"] = self.sources.calls[-1]
            if not set(event.linked_record_ids) <= self.sources.known_ids:
                self.state.unresolved_questions.append("Some linked records have not been established by the authoritative intake scope.")
                self.flag("unverified_linked_record")
            self.intake_source_ids = set(server.seen_sources)
            self.state.scope_verified = True

    def intake_context(self):
        return {name: {"data": c["data"], "receipt": next(r.model_dump() for r in self.state.source_references if r.source_id == c["source_id"])}
                for name, c in self.intake.items()}

    async def run_agent(self, role, phase, prompt, server=None, tools=(), invocation_id="coordinator"):
        agent = build_agent(role, model=self.model, server=server, tools=tools, phase=phase,
                            result_kind=prompt.get("task", {}).get("result_kind", "domain_assessment"), standard_route=self.standard_route, quality_route=self.quality_route, delivery_route=self.delivery_route)
        if role == "coordinator" and phase in {"triage", "reconcile"}:
            agent.output_type = scoped_work_output(self.sources.known_ids, phase, self.state.unresolved_questions,
                [r.invocation_id for r in self.state.completed_assessments if isinstance(r.assessment, ValidationEvidenceAssessment)])
        max_turns = (max(1, self.config.max_coordinator_turns - self.coordinator_turns)
                     if role == "coordinator" else self.config.max_turns)
        with custom_span("case." + phase, {"case_id": self.state.case_id, "correlation_id": self.state.correlation_id,
                "role": role, "invocation_id": invocation_id}):
            if role == "coordinator" and phase == "reconcile":
                self.pending_review_output = None
            try:
                result = await self.runner(agent, canonical(prompt), max_turns=max_turns,
                    hooks=CaseHooks(self, role, invocation_id, phase),
                    run_config=RunConfig(tracing_disabled=False, trace_include_sensitive_data=False,
                        workflow_name="Stratos Program Coordinator", trace_id=self.recorder.trace_id,
                        group_id=self.state.correlation_id))
            except ModelBehaviorError:
                if role == "coordinator" and phase == "reconcile":
                    self.retain_rejected_review(self.pending_review_output, "malformed_agent_output")
                raise HarnessError("malformed_agent_output") from None
            finally:
                self.pending_review_output = None
            try:
                value = result.final_output.model_dump() if hasattr(result.final_output, "model_dump") else result.final_output
                output = agent.output_type.model_validate(value)
            except (ValidationError, TypeError):
                if role == "coordinator" and phase == "reconcile":
                    self.retain_rejected_review(value, "malformed_agent_output")
                raise HarnessError("malformed_agent_output") from None
            return output

    def retain_rejected_review(self, value, reason):
        # Retain only the public typed decision object, never SDK response items,
        # prompts, hidden reasoning, exception text or validation error inputs.
        try:
            output = CoordinatorReview.model_validate(value).model_dump(mode="json")
        except (ValidationError, TypeError):
            output = None
        diagnostic = {"case_id": self.state.case_id, "run_id": self.state.run_id,
            "trace_id": self.recorder.trace_id, "phase": "reconcile",
            "error_code": reason, "output": output}
        self.rejected_reviews.append(diagnostic)
        if self.reconciliation_diagnostic:
            self.reconciliation_diagnostic(diagnostic)

    def reserve(self, request, caller, ancestry, parent_id):
        if request.specialist not in GRAPH[caller]:
            raise HarnessError("delegation_edge_denied")
        if request.specialist in ancestry:
            raise HarnessError("delegation_cycle_denied")
        depth = len(ancestry) + 1
        if depth > self.config.max_delegation_depth:
            raise HarnessError("max_delegation_depth")
        if not set(request.focus_record_ids) <= self.sources.known_ids:
            raise HarnessError("delegation_scope_mismatch")
        if request.result_kind == "validation_clarification":
            if (caller != "coordinator" or self.state.workflow_stage != "specialists"
                    or not any(r.invocation_id == request.prior_assessment_invocation_id
                        and isinstance(r.assessment, ValidationEvidenceAssessment)
                        for r in self.state.completed_assessments)):
                raise HarnessError("clarification_prior_assessment_missing")
        if len(self.state.requested_specialists) >= self.config.max_specialist_calls:
            raise HarnessError("max_specialist_calls")
        normalized = (request.specialist, " ".join(request.question.casefold().split()), tuple(sorted(set(request.focus_record_ids))))
        if normalized in self.seen_requests:
            raise HarnessError("identical_delegation_denied")
        self.seen_requests.add(normalized)
        invocation = Invocation(invocation_id="work_" + uuid4().hex, parent_invocation_id=parent_id,
            caller=caller, specialist=request.specialist, question=request.question, rationale=request.rationale,
            focus_record_ids=request.focus_record_ids, result_kind=request.result_kind,
            prior_assessment_invocation_id=request.prior_assessment_invocation_id,
            depth=depth, status="pending", started_ms=self.elapsed())
        self.state.requested_specialists.append(invocation)
        self.state.pending_specialist_work.append(invocation.invocation_id)
        self.checkpoint()
        return invocation

    def consultation_tool(self, invocation, ancestry, visible_sources):
        @function_tool(name_override="consult_specialist", failure_error_function=None,
                       description_override="Request permitted specialist expertise for a concrete unresolved dependency. Returns a typed result or bounded status receipt; never transfers case ownership.")
        async def consult(request: WorkRequest) -> str:
            if request.depends_on:
                raise HarnessError("nested_dependencies_not_supported")
            # Record every attempt, including denials and suppressed duplicate work.
            entry = {"caller": invocation.specialist, "parent_invocation_id": invocation.invocation_id,
                     "target": request.specialist, "rationale": request.rationale, "status": "requested"}
            self.delegations.append(entry)
            if request.specialist not in GRAPH[invocation.specialist] or request.specialist in ancestry:
                entry["status"] = "denied"
                self.flag("delegation_graph_or_cycle_denied")
                raise HarnessError("delegation_graph_or_cycle_denied")
            running = next((w for w in self.state.requested_specialists
                            if w.specialist == request.specialist and w.status in {"pending", "running"}), None)
            if running:
                entry.update(status="already_running", invocation_id=running.invocation_id)
                return ConsultationReceipt(status="already_running", invocation_id=running.invocation_id,
                    reason="Coordinator already owns this specialist branch and will reconcile it; do not repeat the request.", result=None).model_dump_json()
            child = self.reserve(request, invocation.specialist, ancestry, invocation.invocation_id)
            entry["invocation_id"] = child.invocation_id
            result = await self.execute_specialist(child, request, ancestry)
            entry["status"] = "completed" if result else "failed"
            if result:
                visible_sources.update(r.source_id for r in result.assessment.source_references)
            return ConsultationReceipt(status=entry["status"], invocation_id=child.invocation_id,
                reason="Structured specialist findings returned; Coordinator retains case ownership.", result=result).model_dump_json()
        return consult

    async def execute_specialist(self, invocation, request, ancestry=()):
        invocation.status = "running"
        self.checkpoint()
        visible_sources = set(self.intake_source_ids)
        dependencies = [r for r in self.state.completed_assessments if r.specialist in request.depends_on
                        or r.invocation_id == request.prior_assessment_invocation_id]
        visible_sources.update(ref.source_id for r in dependencies for ref in r.assessment.source_references)
        try:
            async with asyncio.timeout(self.config.specialist_timeout_seconds):
                async with self.server_factory(self, invocation.specialist, invocation.invocation_id) as server:
                    await server.list_tools()
                    chain = (*ancestry, invocation.specialist)
                    tools = [self.consultation_tool(invocation, chain, visible_sources)] if GRAPH[invocation.specialist] else []
                    from .knowledge.integration import SpecialistKnowledge
                    knowledge = SpecialistKnowledge.for_harness(self, invocation)
                    if knowledge:
                        tools.extend(knowledge.tools())
                    prompt = {"case_id": self.state.case_id, "event": self.state.event.model_dump(),
                        "task": request.model_dump(), "intake": self.intake_context(),
                        "status_inspection": self.state.triage.status_inspection.model_dump()
                            if self.state.triage and self.state.triage.status_inspection else None,
                        "completed_dependencies": [r.model_dump() for r in dependencies],
                        "other_assigned_work": [{"specialist": w.specialist, "status": w.status, "question": w.question}
                                                for w in self.state.requested_specialists if w.invocation_id != invocation.invocation_id],
                        "scenario_now": "2026-11-16T09:00:00Z", "allowed_downstream": sorted(GRAPH[invocation.specialist])}
                    output = await self.run_agent(invocation.specialist, "specialist", prompt,
                        server, tools, invocation.invocation_id)
                    if knowledge:
                        await knowledge.validate(output.knowledge_evidence)
                    elif output.knowledge_evidence:
                        raise HarnessError("knowledge_verification_missing")
                    self.rejected_outputs[invocation.invocation_id] = output.model_dump(mode="json")
                    visible_sources.update(server.seen_sources)
                    if knowledge:
                        visible_sources.update(e.source_reference for e in output.knowledge_evidence)
                    with custom_span("case.validate_specialist", {"invocation_id": invocation.invocation_id,
                            "schema": type(output).__name__}) as span:
                        validate_assessment(output, self.sources, visible_sources)
                        if isinstance(output, ValidationClarificationResult):
                            if (output.question != request.question
                                    or output.prior_assessment_invocation_id != request.prior_assessment_invocation_id):
                                raise HarnessError("clarification_request_mismatch")
                        else:
                            validate_status_reads(output, self.sources, invocation.invocation_id, invocation.specialist)
                        if knowledge:
                            await knowledge.record_usage(output.knowledge_evidence)
                        span.span_data.data["validated"] = True
                    result = SpecialistResult(invocation_id=invocation.invocation_id,
                                              specialist=invocation.specialist, assessment=output)
                    self.state.completed_assessments.append(result)
                    if isinstance(output, ValidationClarificationResult) and (output.invalidates_prior_coverage or output.introduces_blocker):
                        blocker = f"Validation clarification {invocation.invocation_id} requires review: {output.summary}"
                        self.state.blocking_issues.append(blocker)
                        self.state.unresolved_questions.append(blocker)
                    self.rejected_outputs.pop(invocation.invocation_id, None)
                    invocation.status = "completed"
                    return result
        except asyncio.CancelledError:
            invocation.status = "cancelled"
            invocation.error = "case_cancelled"
            raise
        except Exception as exc:
            invocation.status = "failed"
            invocation.error = failure_code(exc, "specialist_failed")
            self.flag(invocation.error)
            self.state.unresolved_questions.append(f"Required {invocation.specialist} work failed: {invocation.error}.")
            self.state.blocking_issues.append(f"Required {invocation.specialist} work failed: {invocation.error}.")
            return None
        finally:
            invocation.ended_ms = self.elapsed()
            if invocation.invocation_id in self.state.pending_specialist_work:
                self.state.pending_specialist_work.remove(invocation.invocation_id)
            self.checkpoint()

    async def execute_batch(self, requests):
        validate_workflow(requests)
        pending = list(requests)
        done = set()
        while pending:
            ready = [r for r in pending if set(r.depends_on) <= done]
            if not ready:
                raise HarnessError("missing_specialist_dependency")
            # Reserve the whole wave before launching, so nested calls see siblings.
            old_count = len(self.state.requested_specialists)
            old_seen = set(self.seen_requests)
            try:
                reserved = [(self.reserve(r, "coordinator", (), None), r) for r in ready]
            except Exception:
                # Wave admission is atomic within application state, before any
                # agent starts. Failed validation must not strand pending work.
                discarded = {w.invocation_id for w in self.state.requested_specialists[old_count:]}
                del self.state.requested_specialists[old_count:]
                self.state.pending_specialist_work[:] = [w for w in self.state.pending_specialist_work if w not in discarded]
                self.seen_requests = old_seen
                self.checkpoint()
                raise
            self.parallel_branches.append({"invocations": [w.invocation_id for w, _ in reserved],
                "specialists": [w.specialist for w, _ in reserved], "parallel": len(reserved) > 1})
            tasks = [asyncio.create_task(self.execute_specialist(w, r)) for w, r in reserved]
            try:
                results = await asyncio.gather(*tasks)
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            for (work, request), result in zip(reserved, results):
                if result is not None:
                    done.add(request.specialist)
                pending.remove(request)
            if any(not set(r.depends_on) <= done | {p.specialist for p in pending} for r in pending):
                raise HarnessError("missing_specialist_dependency")

    def collect_open_questions(self):
        resolved = {item.question for review in self.state.coordinator_reviews for item in review.resolved_questions}
        for completed in self.state.completed_assessments:
            questions = completed.assessment.unresolved_questions + getattr(completed.assessment, "missing_information", [])
            self.state.unresolved_questions.extend(q for q in questions
                if q not in self.state.unresolved_questions and q not in resolved)

    def synthesis_context(self):
        return {"case_id": self.state.case_id, "event": self.state.event.model_dump(),
            "intake": self.intake_context(), "triage": self.state.triage.model_dump(),
            "assessments": [r.model_dump() for r in self.state.completed_assessments],
            "failed_work": [w.model_dump() for w in self.state.requested_specialists if w.status != "completed"],
            "unresolved_questions": self.state.unresolved_questions,
            "blocking_issues": self.state.blocking_issues,
            "remaining_specialist_calls": self.config.max_specialist_calls - len(self.state.requested_specialists)}

    def normalize_reconciliation_work(self, review):
        """Bind an explicitly narrow option-provenance read to its prior assessment.

        The Coordinator chooses the work itself. This host normalization only fixes
        the output contract when its task says that coverage must not be repeated;
        it does not add work, change the question, or broaden source access.
        """
        prior = next((result for result in reversed(self.state.completed_assessments)
                      if isinstance(result.assessment, ValidationEvidenceAssessment)), None)
        if not prior:
            return review
        normalized = []
        for request in review.additional_work:
            intent = f"{request.question} {request.rationale}".casefold()
            provenance_only = (request.specialist == "validation_evidence"
                and request.result_kind == "domain_assessment"
                and ("provenance-only" in intent or "provenance only" in intent)
                and ("do not repeat coverage" in intent or "sourcefact" in intent))
            if provenance_only:
                request = request.model_copy(update={
                    "result_kind": "validation_clarification",
                    "prior_assessment_invocation_id": prior.invocation_id,
                })
            normalized.append(request)
        return review.model_copy(update={"additional_work": normalized})

    async def run(self):
        try:
            async with asyncio.timeout(self.config.run_timeout_seconds):
                await self.intake_case()
                self.move("triage")
                triage = await self.run_agent("coordinator", "triage", {"case_id": self.state.case_id,
                    "event": self.state.event.model_dump(), "intake": self.intake_context(),
                    "input_guardrails": self.state.unresolved_questions, "scope_verified": self.state.scope_verified})
                self.state.triage = triage
                scope_error = status_scope_error(self.state, self.sources)
                if scope_error:
                    self.flag(scope_error)
                    self.state.unresolved_questions.append(scope_error)
                self.state.unresolved_questions.extend(q for q in triage.missing_information if q not in self.state.unresolved_questions)
                self.state.blocking_issues = list(self.state.unresolved_questions)
                stop = (not self.state.scope_verified or triage.confidence < 0.75 or self.state.unresolved_questions
                        or triage.classified_change_type == "other_or_unknown")
                if stop and triage.specialists_required:
                    self.flag("triage_specialists_suppressed")
                if not stop and triage.specialists_required:
                    self.move("specialists")
                    await self.execute_batch(triage.specialists_required)
                    self.move("reconcile")
                    for round_number in range(self.config.max_reconcile_rounds):
                        self.collect_open_questions()
                        review = await self.run_agent("coordinator", "reconcile", self.synthesis_context())
                        review = self.normalize_reconciliation_work(review)
                        allowed = self.intake_source_ids | {ref.source_id for r in self.state.completed_assessments for ref in r.assessment.source_references}
                        try:
                            apply_review(review, self.sources, self.state, allowed)
                        except HarnessError as exc:
                            self.retain_rejected_review(review.model_dump(), str(exc))
                            raise
                        if not review.additional_work:
                            break
                        self.move("specialists")
                        await self.execute_batch(review.additional_work)
                        self.move("reconcile")
                # Also collect after the last additional-work wave, or when
                # reconciliation is disabled, before deciding policy eligibility.
                self.collect_open_questions()
                self.state.policy_decision = determine_policy(self.state, self.sources)
                self.move("synthesis")
                prompt = self.synthesis_context()
                prompt["binding_policy_decision"] = self.state.policy_decision.model_dump()
                output = await self.run_agent("coordinator", "synthesis", prompt)
                self.recorder.candidate_output = output.model_dump(mode="json")
                allowed = self.intake_source_ids | {ref.source_id for r in self.state.completed_assessments for ref in r.assessment.source_references}
                with custom_span("case.validate_final", {"case_id": self.state.case_id, "schema": "FinalDecisionPackage"}) as span:
                    validate_final(output, self.sources, self.state, allowed)
                    span.span_data.data["validated"] = True
                self.state.final_package = output
                if output.classified_change_type != self.state.triage.classified_change_type:
                    self.flag("coordinator_refined_classification")
                self.state.final_package_status = "validated"
                self.move("completed")
                return self.state
        except BaseException as exc:
            code = (str(exc) if isinstance(exc, HarnessError) else "case_timeout" if isinstance(exc, TimeoutError)
                    else "case_cancelled" if isinstance(exc, asyncio.CancelledError) else "case_failed")
            self.state.termination_reason = code
            self.state.final_package_status = "rejected" if self.recorder.candidate_output else "unavailable"
            self.flag(code)
            if self.state.workflow_stage not in {"completed", "terminated"}:
                self.move("terminated")
            raise
