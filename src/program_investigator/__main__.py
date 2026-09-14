"""Explicit paid CLI entry point. Writes synthetic assessment artifacts, safe stdout."""

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

import httpx2
from agents import set_trace_processors, set_tracing_disabled
from agents.models.openai_responses import OpenAIResponsesModel
from agents.tracing import custom_span, flush_traces, gen_trace_id, trace
from agents.tracing.processors import BackendSpanExporter, BatchTraceProcessor
import openai
from pydantic import ValidationError

from .agent import run_investigation
from .config import MODEL, PROJECT, InvestigatorConfig, InvestigatorError, load_key
from .telemetry import Recorder, SafeMetadataProcessor, safe_id


async def execute(config, case_id, customer, recorder, key, report):
    async def response_metadata(response):
        entry = {"http_status": response.status_code, "request_id": safe_id(response.headers.get("x-request-id"))}
        if 200 <= response.status_code < 300:
            await response.aread()
            body = response.json()
            entry["model"] = body.get("model") if body.get("model") == MODEL else "unexpected_model"
            entry["status"] = body.get("status") if body.get("status") in {
                "completed", "failed", "incomplete", "cancelled", "queued", "in_progress"} else "unknown"
        report["api_requests"].append(entry)

    async with openai.AsyncOpenAI(
        api_key=key, base_url="https://api.openai.com/v1", max_retries=1,
        timeout=config.model_timeout_seconds,
        http_client=httpx2.AsyncClient(trust_env=False, follow_redirects=False,
            timeout=httpx2.Timeout(config.model_timeout_seconds, connect=10),
            event_hooks={"response": [response_metadata]}),
    ) as client:
        model = OpenAIResponsesModel(model=MODEL, openai_client=client)
        output, usage = await run_investigation(config, case_id, customer, model, recorder)
        report["usage"] = usage
        report["output"] = output.model_dump(mode="json")


def error_code(exc):
    if isinstance(exc, InvestigatorError):
        return str(exc)
    if isinstance(exc, openai.APIStatusError):
        return {400: "model_request_rejected", 401: "authentication_failed", 403: "model_access_denied",
                404: "model_unavailable", 429: "quota_or_rate_limit"}.get(exc.status_code, "openai_http_error")
    if isinstance(exc, (TimeoutError, openai.APITimeoutError)):
        return "timeout"
    if isinstance(exc, openai.APIConnectionError):
        return "openai_connection_failed"
    if isinstance(exc, ValidationError):
        return "output_schema_invalid"
    return "investigation_failed"


def safe_error_chain(exc):
    """Transport diagnosis by exception class only, never messages/requests/headers."""
    allowed = {"APIConnectionError", "APITimeoutError", "ConnectError", "ReadError",
               "WriteError", "RemoteProtocolError", "LocalProtocolError", "ConnectTimeout",
               "ReadTimeout", "PoolTimeout", "WriteTimeout", "SSLError", "gaierror",
               "ConnectionResetError", "BrokenPipeError", "OSError", "ValueError", "TypeError"}
    result = []
    while exc is not None and len(result) < 6:
        name = type(exc).__name__
        result.append(name if name in allowed else "other_error")
        exc = exc.__cause__
    return result


def write_artifact(path: Path, value, key: str | None):
    text = json.dumps(value, indent=2, allow_nan=False)
    if key:
        text = text.replace(key, "[REDACTED]")
    # Per-run exclusive creation prevents overwriting previous runs or symlinks.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(text + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run one read-only Astra investigation through local MCP.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--customer", required=True)
    parser.add_argument("--mcp-url", default="http://127.0.0.1:9000/mcp")
    args = parser.parse_args()
    recorder = Recorder(gen_trace_id())
    run_dir = PROJECT / ".cache" / "program-investigator" / recorder.trace_id
    run_dir.mkdir(parents=True, mode=0o700)
    report = {"trace_id": recorder.trace_id, "model": MODEL, "status": "failed",
              "started_at": datetime.now(timezone.utc).isoformat(), "api_requests": [],
              "tracing_enabled": False, "trace_payloads_enabled": False,
              "trace_export_flush_completed": False, "platform_trace_visibility_verified": False}
    key = None
    previous = logging.root.manager.disable
    started = time.perf_counter()
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            config = InvestigatorConfig(mcp_url=args.mcp_url)
            key = load_key(PROJECT / ".env.local")
            exporter = BackendSpanExporter(api_key=key, max_retries=1)
            batch = BatchTraceProcessor(exporter)
            set_trace_processors([SafeMetadataProcessor(recorder), batch])
            set_tracing_disabled(False)
            report["tracing_enabled"] = True
            try:
                with trace("ProgramInvestigator", trace_id=recorder.trace_id, group_id=args.case_id,
                           metadata={"case_id": args.case_id, "model": MODEL, "read_only": True}):
                    asyncio.run(execute(config, args.case_id, args.customer, recorder, key, report))
                    with custom_span("investigation.output", {"schema": "InvestigationResult", "validated": True}):
                        pass
                report["status"] = "completed"
            finally:
                flush_traces()
                report["trace_export_flush_completed"] = True
    except Exception as exc:
        report["error_category"] = error_code(exc)
        report["error_types"] = safe_error_chain(exc)
    finally:
        logging.disable(previous)
    report["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    report["authentication_succeeded"] = any(200 <= r["http_status"] < 300 for r in report["api_requests"])
    report["generations"] = recorder.generations
    if "usage" not in report and recorder.generations:
        report["usage"] = {name: sum(g["usage"][name] for g in recorder.generations)
                           for name in recorder.generations[0]["usage"]}
        report["usage_scope"] = "completed_generations_only"
    report["tool_call_count"] = len(recorder.calls)
    report["tools_called"] = sorted({c["tool"] for c in recorder.calls})
    report["errors"] = recorder.errors
    report["artifact_directory"] = str(run_dir)
    if "output" in report:
        write_artifact(run_dir / "result.json", report.pop("output"), key)
    elif recorder.candidate_output is not None:
        write_artifact(run_dir / "rejected-result.json", recorder.candidate_output, key)
    write_artifact(run_dir / "tool-calls.json", recorder.calls, key)
    write_artifact(run_dir / "catalog.json", recorder.catalog, key)
    write_artifact(run_dir / "trace-metadata.json", recorder.spans, key)
    write_artifact(run_dir / "report.json", report, key)
    print(json.dumps({k: v for k, v in report.items() if k not in {"generations", "api_requests"}}, indent=2))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
