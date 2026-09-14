"""Supported Agents SDK MCP transport, with a fixed capability boundary and receipts."""

import json
import re
import time

import httpx2
from agents.mcp import MCPServerStreamableHttp, create_static_tool_filter
from agents.tracing import custom_span

from .config import InvestigatorConfig, InvestigatorError

# Deliberate independent allowlist: importing the server catalog would import its
# enterprise client. No agent module imports either business implementation.
READ_TOOLS = frozenset({
    "get_change_request", "get_requirement_revision", "get_configuration",
    "get_workload_profile", "get_procedure", "get_policy", "get_acceptance_criteria",
    "get_document", "get_documents", "get_plan", "get_decision",
    "get_validation_coverage", "get_validation_options", "get_validation_result",
    "get_validation_samples", "get_validation_jobs", "get_validation_job",
    "get_manufacturing_unit", "get_manufacturing_lot", "get_customer_order",
    "get_cost_rates", "get_program", "get_program_milestone", "get_dependencies",
    "get_implementation_links",
})


def http_client_factory(headers=None, timeout=None, auth=None):
    # SDK v2 transport uses HTTPX2. Never inherit proxies or attach the OpenAI key.
    return httpx2.AsyncClient(headers=headers, auth=auth, trust_env=False,
                             follow_redirects=False,
                             timeout=httpx2.Timeout(60, connect=2, write=5, pool=5))


def validate_payload(result) -> dict:
    """Fail closed on inconsistent envelopes before any data reaches the model."""
    data = result.structured_content
    if (not isinstance(data, dict) or set(data) != {"ok", "data", "error"}
            or type(data["ok"]) is not bool or bool(result.is_error) == data["ok"]):
        raise InvestigatorError("malformed_mcp_result")
    if data["ok"]:
        if not isinstance(data["data"], dict) or data["error"] is not None:
            raise InvestigatorError("malformed_mcp_result")
    else:
        # Source errors contain only its fixed metadata schema. The run stops;
        # unavailable authoritative context cannot silently become an assessment.
        raise InvestigatorError("mcp_source_error")
    try:
        encoded = json.dumps(data, allow_nan=False)
    except (ValueError, TypeError):
        raise InvestigatorError("malformed_mcp_result") from None
    if len(encoded) > 2_000_000:
        raise InvestigatorError("mcp_result_too_large")
    return data


def trace_receipt(result) -> dict:
    """Require the existing server's correlation receipts; omit arbitrary metadata."""
    raw = (result.meta or {}).get("stratos/trace", {})
    if not isinstance(raw, dict):
        raise InvestigatorError("invalid_mcp_receipt")
    for field, prefix in (("call_id", "mcp"), ("correlation_id", "corr")):
        if not isinstance(raw.get(field), str) or not re.fullmatch(prefix + r"-[a-f0-9]{32}", raw[field]):
            raise InvestigatorError("invalid_mcp_receipt")
    reads = raw.get("http_reads")
    if not isinstance(reads, list) or not reads:
        raise InvestigatorError("invalid_mcp_receipt")
    safe_reads = []
    for read in reads:
        if (read.get("method") != "GET" or read.get("status") != 200
                or read.get("correlation_id") != raw["correlation_id"]
                or read.get("server_correlation_id") != raw["correlation_id"]
                or not re.fullmatch(r"request-[a-f0-9]{32}", read.get("request_id", ""))):
            raise InvestigatorError("invalid_mcp_receipt")
        safe_reads.append({key: read[key] for key in (
            "method", "path", "status", "attempts", "request_id", "correlation_id",
            "server_correlation_id", "latency_ms")})
    return {"call_id": raw["call_id"], "correlation_id": raw["correlation_id"], "http_reads": safe_reads}


class StratosMCP(MCPServerStreamableHttp):
    """Instrumentation only; SDK connect/list/call performs the MCP protocol."""

    def __init__(self, config: InvestigatorConfig, recorder, case_id: str):
        self.recorder = recorder
        self.case_id = case_id
        super().__init__(
            name="StratosReadOnly",
            params={"url": config.mcp_url, "timeout": 5, "sse_read_timeout": 60,
                    "httpx_client_factory": http_client_factory},
            cache_tools_list=True, use_structured_content=True,
            client_session_timeout_seconds=60, max_retry_attempts=0,
            tool_filter=create_static_tool_filter(allowed_tool_names=sorted(READ_TOOLS)),
            failure_error_function=None,
        )

    async def connect(self):
        try:
            await super().connect()
        except Exception:
            raise InvestigatorError("mcp_unavailable") from None

    async def list_tools(self, run_context=None, agent=None):
        try:
            tools = await super().list_tools(run_context, agent)
        except Exception:
            raise InvestigatorError("mcp_discovery_failed") from None
        if {t.name for t in tools} != READ_TOOLS or len(tools) != len(READ_TOOLS):
            raise InvestigatorError("mcp_catalog_changed")
        for tool in tools:
            hints = tool.annotations
            if (hints is None or hints.read_only_hint is not True
                    or hints.destructive_hint is not False or hints.idempotent_hint is not True
                    or hints.open_world_hint is not False):
                raise InvestigatorError("unsafe_mcp_capability")
        if not self.recorder.catalog:
            self.recorder.catalog = [t.model_dump(mode="json", by_alias=True) for t in tools]
            with custom_span("stratos.discovery", {"case_id": self.case_id, "tool_count": len(tools)}):
                pass
        return tools

    async def call_tool(self, tool_name, arguments, meta=None):
        if tool_name not in READ_TOOLS:
            raise InvestigatorError("tool_not_allowed")
        if (not isinstance(arguments, dict) or not arguments
                or any(not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", v)
                       for v in arguments.values())):
            raise InvestigatorError("invalid_tool_arguments")
        started = time.perf_counter()
        with custom_span("stratos.read", {"case_id": self.case_id, "tool": tool_name}) as span:
            try:
                result = await super().call_tool(tool_name, arguments,
                    meta={"stratos/investigation": {"case_id": self.case_id,
                                                  "trace_id": self.recorder.trace_id}})
                payload = validate_payload(result)
                receipt = trace_receipt(result)
            except InvestigatorError:
                self.recorder.errors.append("mcp_read_rejected")
                raise
            except Exception:
                self.recorder.errors.append("mcp_call_failed")
                raise InvestigatorError("mcp_call_failed") from None
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            self.recorder.calls.append({"tool": tool_name, "arguments": dict(arguments),
                                       "data": payload["data"], "latency_ms": elapsed,
                                       "trace": receipt})
            span.span_data.data.update({"latency_ms": elapsed, "ok": True,
                                       "call_id": receipt["call_id"],
                                       "correlation_id": receipt["correlation_id"],
                                       "http_read_count": len(receipt["http_reads"])})
            return result
