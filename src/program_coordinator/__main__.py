"""Explicit paid CLI. No service, secret loading or model calls on package import."""

import argparse
import asyncio
import contextlib
from datetime import datetime, timezone
import io
import json
import logging
import os
from pathlib import Path
import time
from uuid import uuid4

import httpx2
import openai
from agents import set_trace_processors, set_tracing_disabled
from agents.models.openai_responses import OpenAIResponsesModel
from agents.tracing import flush_traces, gen_trace_id, trace
from agents.tracing.processors import BackendSpanExporter, BatchTraceProcessor
from pydantic import ValidationError

from program_investigator.config import PROJECT, MODEL, load_key
from program_investigator.__main__ import error_code, write_artifact
from program_investigator.telemetry import Recorder, SafeMetadataProcessor, safe_id
from .controls import HarnessConfig, HarnessError
from .harness import CaseHarness
from .models import ProgramChangeEvent
from .application.models import TrustedActor, WorkflowInvocation, WorkflowError
from .application.registry import list_workflows, dispatch_error
from .application.service import WorkflowService
from .application.store import ActivityStore


async def execute(config, event, recorder, key, report, run_dir, *, run_record=None):
    async def response_metadata(response):
        entry = {"http_status": response.status_code, "request_id": safe_id(response.headers.get("x-request-id"))}
        if 200 <= response.status_code < 300:
            await response.aread()
            body = response.json()
            entry["model"] = body.get("model") if body.get("model") == MODEL else "unexpected_model"
            entry["status"] = body.get("status") if body.get("status") in {"completed", "failed", "incomplete"} else "unknown"
        report["api_requests"].append(entry)

    def checkpoint(state):
        # Only the newly created private run directory is writable. Replace an
        # application-owned checkpoint atomically; no fixture/business state writes.
        temp = run_dir / "case-state.next.json"
        write_artifact(temp, state, key)
        os.replace(temp, run_dir / "case-state.json")

    def reconciliation_diagnostic(value):
        # Same private, exclusive, credential-redacted artifact boundary as the
        # other typed outputs. This callback has no business-state capability.
        write_artifact(run_dir / "rejected-reconciliation.json", value, key)

    async with openai.AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1", max_retries=1,
        http_client=httpx2.AsyncClient(trust_env=False, follow_redirects=False,
            timeout=httpx2.Timeout(config.model_timeout_seconds, connect=10),
            event_hooks={"response": [response_metadata]})) as client:
        harness = CaseHarness(config, event, OpenAIResponsesModel(model=MODEL, openai_client=client),
            recorder, checkpoint=checkpoint, reconciliation_diagnostic=reconciliation_diagnostic,
            **({"case_id": run_record.case_id, "run_id": run_record.run_id,
                "workflow_id": run_record.workflow_id, "workflow_definition_version": run_record.definition_version}
                if run_record else {}))
        report["case_id"] = harness.state.case_id
        try:
            state = await harness.run()
            report["output"] = state.final_package.model_dump(mode="json")
            report["policy_path"] = state.final_package.policy_path
            return state
        finally:
            report.update(coordinator_turns=harness.coordinator_turns,
                specialist_invocations=len(harness.state.requested_specialists),
                specialist_calls=[w.model_dump() for w in harness.state.requested_specialists],
                parallel_branches=harness.parallel_branches, delegations=harness.delegations,
                termination_reason=harness.state.termination_reason,
                guardrail_events=harness.state.guardrail_events, tool_calls_started=harness.tool_calls_started,
                triage=harness.state.triage.model_dump() if harness.state.triage else None)
            write_artifact(run_dir / "catalog.json", harness.catalog, key)
            if harness.final_output_diagnostic and harness.state.final_package is None:
                write_artifact(run_dir / "rejected-final.json", {
                    "phase": "synthesis", "error_code": harness.state.termination_reason,
                    **harness.final_output_diagnostic}, key)
            if harness.rejected_outputs:
                write_artifact(run_dir / "rejected-specialists.json", harness.rejected_outputs, key)
            checkpoint(harness.state.model_dump(mode="json"))


def main():
    parser = argparse.ArgumentParser(description="Paid, bounded, read-only Stratos multi-agent case through real MCP.")
    parser.add_argument("--event", type=Path)
    parser.add_argument("--workflow-id", default="requirement_change_analysis")
    parser.add_argument("--definition-version", type=int, default=1)
    parser.add_argument("--invocation-id", help="Reuse for retries; use a new ID for a deliberate rerun.")
    parser.add_argument("--case-id", help="Optional existing case ID; otherwise reuse the case for the source change.")
    parser.add_argument("--metadata-dir", type=Path, default=PROJECT / ".cache/multi-agent/activity")
    parser.add_argument("--list-workflows", action="store_true", help="Offline catalog; no key, model, or source calls.")
    parser.add_argument("--allow-paid-knowledge-search", action="store_true")
    parser.add_argument("--mcp-url", default="http://127.0.0.1:9010/mcp")
    parser.add_argument("--program-id", default="PRG-A17")
    parser.add_argument("--customer-id", default="CUST-FML01")
    from .application import execution_cli
    execution_cli.add_arguments(parser)
    args = parser.parse_args()
    if args.list_workflows:
        print(json.dumps([d.model_dump(mode="json") for d in list_workflows()], indent=2))
        return 0
    if error := dispatch_error(args.workflow_id, args.definition_version):
        print(json.dumps({"status": "unsupported", "error_code": error}))
        return 2
    if (args.phase06 or args.prepare_execution) and args.workflow_id != 'requirement_change_analysis':
        print(json.dumps({'status':'unsupported','error_code':'WORKFLOW_NOT_IMPLEMENTED'}))
        return 2
    if args.phase06:
        return execution_cli.main(args)
    if args.prepare_execution and not args.preparation_id:
        parser.error("--prepare-execution requires --preparation-id for safe retries")
    if args.prepare_execution and os.environ.get('DEMO_MODE', '').lower() != 'true':
        parser.error("--prepare-execution requires DEMO_MODE=true")
    if not args.event:
        parser.error("--event is required for an analysis invocation")
    recorder = Recorder(gen_trace_id())
    run_dir = PROJECT / ".cache" / "multi-agent" / recorder.trace_id
    run_dir.mkdir(parents=True, mode=0o700)
    report = {"trace_id": recorder.trace_id, "model": MODEL, "status": "failed", "api_requests": [],
        "started_at": datetime.now(timezone.utc).isoformat(), "tracing_enabled": False,
        "trace_payloads_enabled": False, "trace_export_flush_completed": False,
        "platform_trace_visibility_verified": False, "business_writes_available": False,
        "artifact_directory": str(run_dir)}
    key = None
    started = time.perf_counter()
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            event = ProgramChangeEvent.model_validate_json(args.event.read_text())
            config = HarnessConfig(mcp_url=args.mcp_url, program_id=args.program_id, customer_id=args.customer_id)
            invocation = WorkflowInvocation(workflow_id=args.workflow_id, definition_version=args.definition_version,
                invocation_id=args.invocation_id or "invoke_" + uuid4().hex, case_id=args.case_id,
                program_id=config.program_id, customer_id=config.customer_id, event=event)
            # Fixed host-side demo identity, aligned with the read-only MCP server.
            # No request field or CLI role flag can supply approval authority.
            actor = TrustedActor("demo-reader", "reader", frozenset({(config.customer_id, config.program_id)}))

            async def investigate(request, run):
                nonlocal key
                # Duplicate/unsupported invocations never reach key loading or API setup.
                key = load_key(PROJECT / ".env.local")
                set_trace_processors([SafeMetadataProcessor(recorder), BatchTraceProcessor(BackendSpanExporter(api_key=key, max_retries=1))])
                set_tracing_disabled(False)
                report["tracing_enabled"] = True
                try:
                    with trace("Stratos Program Coordinator", trace_id=recorder.trace_id, group_id=event.correlation_id,
                        metadata={"event_id": event.event_id, "case_id": run.case_id, "run_id": run.run_id,
                            "workflow_id": run.workflow_id, "correlation_id": event.correlation_id, "model": MODEL, "read_only": True}):
                        from .knowledge.integration import KnowledgeContext, current_knowledge_context
                        from .knowledge.service import KnowledgeService
                        from .knowledge.corpus import SourceCorpus
                        from .knowledge.providers import OpenAIIndexProvider
                        from .infrastructure.source_gateway import SourceGateway
                        from .application.demo_identity import READER
                        source = SourceGateway(args.source_url,demo_mode=True)
                        knowledge = KnowledgeService(args.metadata_dir,SourceCorpus(source.read),
                            OpenAIIndexProvider() if args.allow_paid_knowledge_search else None)
                        token = current_knowledge_context.set(KnowledgeContext(knowledge,READER))
                        try:
                            return await execute(config, event, recorder, key, report, run_dir, run_record=run)
                        finally:
                            current_knowledge_context.reset(token)
                            source.close()
                finally:
                    flush_traces()
                    report["trace_export_flush_completed"] = True

            service = WorkflowService(ActivityStore(args.metadata_dir), config=config, investigate=investigate, actors=[actor])
            result = asyncio.run(service.invoke(invocation, actor, trace_id=recorder.trace_id, artifact_directory=str(run_dir)))
            report["status"] = "replayed" if result.replayed else result.status
            report["invocation_status"] = result.status
            report["invocation_id"] = invocation.invocation_id
            if result.error_code:
                report["error_category"] = result.error_code
            if result.run:
                report.update(run_id=result.run.run_id, case_id=result.run.case_id, workflow_id=result.run.workflow_id,
                    workflow_definition_version=result.run.definition_version)
                if result.replayed:
                    report["original_artifact_directory"] = result.run.artifact_directory
                    report["original_trace_id"] = result.run.trace_id
                    if result.run.recommendation:
                        report["output"] = result.run.recommendation.model_dump(mode="json")
                        report["policy_path"] = result.run.recommendation.policy_path
            if args.prepare_execution and result.status == "completed":
                execution_service = execution_cli.create_service(args)
                try:
                    prepared = execution_cli.prepare(args, execution_service, result.run.run_id)
                    report["phase06"] = {"status": prepared["status"], "reference": prepared["reference"]}
                    write_artifact(run_dir / "proposal.json", prepared["proposal"], key)
                finally:
                    execution_service.source.close()
    except Exception as exc:
        report["status"] = "failed"
        report["error_category"] = str(exc) if isinstance(exc, (HarnessError, WorkflowError)) else error_code(exc)
    finally:
        logging.disable(previous)
    report["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    report["generations"] = recorder.generations
    report["model_calls"] = len(recorder.generations)
    report["api_request_count"] = len(report["api_requests"])
    report["authentication_succeeded"] = any(200 <= r["http_status"] < 300 for r in report["api_requests"])
    report["usage"] = {name: sum(g["usage"][name] for g in recorder.generations) for name in (
        "requests", "input_tokens", "output_tokens", "total_tokens", "cached_input_tokens", "reasoning_tokens")}
    report["usage_scope"] = "completed_generations_only"
    report["mcp_calls"] = len(recorder.calls)
    report["http_gets"] = sum(len(c["trace"]["http_reads"]) for c in recorder.calls)
    report["unique_tools"] = sorted({c["tool"] for c in recorder.calls})
    if "output" in report:
        write_artifact(run_dir / "result.json", report.pop("output"), key)
    elif recorder.candidate_output:
        write_artifact(run_dir / "rejected-result.json", recorder.candidate_output, key)
    write_artifact(run_dir / "tool-calls.json", recorder.calls, key)
    write_artifact(run_dir / "trace-metadata.json", recorder.spans, key)
    write_artifact(run_dir / "report.json", report, key)
    print(json.dumps({k: report[k] for k in ("status", "trace_id", "artifact_directory", "model_calls", "mcp_calls", "usage", "latency_ms")}
                     | {k: report[k] for k in ("policy_path", "error_category", "termination_reason", "phase06") if k in report}, indent=2))
    return 0 if report["status"] != "failed" and (report.get("invocation_status") == "completed" or report["status"] == "completed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
