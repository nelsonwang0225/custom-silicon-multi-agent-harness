"""Per-invocation least-privilege SDK MCP sessions; no direct business transport."""

import asyncio
import json
import re
import time

from agents.mcp import MCPServerStreamableHttp, create_static_tool_filter
from agents.tracing import custom_span
from mcp.types import TextContent, CallToolResult
from program_investigator.mcp import http_client_factory, validate_payload, trace_receipt
from program_investigator.config import InvestigatorError
from .controls import HarnessError, TOOL_MATRIX


class ScopedMCP(MCPServerStreamableHttp):
    def __init__(self, harness, role, invocation_id):
        self.harness, self.role, self.invocation_id = harness, role, invocation_id
        self.allowed = TOOL_MATRIX[role]
        if getattr(harness, "standard_route", False) and role in {"change_impact", "validation_evidence", "program_commercial"}:
            self.allowed = self.allowed | {"get_standard_change_context"}
        if getattr(harness, "delivery_route", False):
            self.allowed = frozenset({"get_delivery_context", "get_program"}) if role == "coordinator" else TOOL_MATRIX[role] | {"get_delivery_context"}
        if getattr(harness, "quality_route", False):
            self.allowed = frozenset({"get_quality_context", "get_program"}) if role == "coordinator" else TOOL_MATRIX[role] | {"get_quality_context"}
        self.seen_sources = set()
        super().__init__(name=f"Stratos_{role}", params={"url": harness.config.mcp_url,
            "timeout": 5, "sse_read_timeout": 60, "httpx_client_factory": http_client_factory},
            cache_tools_list=True, use_structured_content=True,
            client_session_timeout_seconds=harness.config.tool_timeout_seconds,
            max_retry_attempts=0, failure_error_function=None,
            tool_filter=create_static_tool_filter(allowed_tool_names=sorted(self.allowed)))

    async def list_tools(self, run_context=None, agent=None):
        try:
            tools = await super().list_tools(run_context, agent)
        except Exception:
            raise HarnessError("mcp_discovery_failed") from None
        if len(tools) != len(self.allowed) or {t.name for t in tools} != self.allowed:
            raise HarnessError("mcp_catalog_mismatch")
        for tool in tools:
            hints = tool.annotations
            if not hints or (hints.read_only_hint is not True or hints.destructive_hint is not False
                    or hints.idempotent_hint is not True or hints.open_world_hint is not False):
                raise HarnessError("unsafe_mcp_capability")
        self.harness.catalog[self.role] = [t.model_dump(mode="json", by_alias=True) for t in tools]
        return tools

    async def connect(self):
        try:
            await super().connect()
        except Exception:
            raise HarnessError("mcp_unavailable") from None

    async def call_tool(self, tool_name, arguments, meta=None):
        registry, state = self.harness.sources, self.harness.state
        if self.harness.tool_calls_started >= self.harness.config.max_tool_calls:
            raise HarnessError("max_tool_calls")
        self.harness.tool_calls_started += 1
        if tool_name not in self.allowed:
            raise HarnessError("tool_not_allowed")
        if (not isinstance(arguments, dict) or not arguments
                or any(not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", v) for v in arguments.values())):
            raise HarnessError("invalid_tool_arguments")
        if any(v not in registry.known_ids for v in arguments.values()):
            raise HarnessError("undiscovered_record_id")
        invalid = {k: sorted(registry.ids_by_parameter.get(k, set())) for k, v in arguments.items()
                   if v not in registry.ids_by_parameter.get(k, set())}
        if invalid:
            # A mistyped read is rejected locally, without causing an enterprise
            # denial audit. The model may correct it using these already scoped IDs.
            self.harness.flag("typed_record_reference_denied")
            payload = {"ok": False, "data": None, "error": {"code": "TYPED_RECORD_REFERENCE_DENIED",
                "known_ids_for_parameter": invalid, "message": "Use a discovered ID of the required record type. This is a host guardrail receipt, not business evidence."}}
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(payload))],
                                  structured_content=payload, is_error=True)
        if "program_id" in arguments and arguments["program_id"] != state.program_id:
            raise HarnessError("tool_scope_mismatch")
        if "exception_id" in arguments and arguments["exception_id"] != state.event.change_id:
            raise HarnessError("tool_case_mismatch")
        if "change_id" in arguments and arguments["change_id"] != state.event.change_id:
            raise HarnessError("tool_case_mismatch")
        started = time.perf_counter()
        with custom_span("case.mcp_read", {"case_id": state.case_id, "correlation_id": state.correlation_id,
                "role": self.role, "invocation_id": self.invocation_id, "tool": tool_name}) as span:
            try:
                async with asyncio.timeout(self.harness.config.tool_timeout_seconds):
                    result = await super().call_tool(tool_name, arguments, meta={"stratos/case": {
                        "case_id": state.case_id, "correlation_id": state.correlation_id,
                        "trace_id": self.harness.recorder.trace_id, "invocation_id": self.invocation_id}})
                payload, receipt = validate_payload(result), trace_receipt(result)
                data = payload["data"]
                if "exception_id" in data and data["exception_id"] != state.event.change_id:
                    raise HarnessError("response_case_mismatch")
                if "change_id" in data and data["change_id"] != state.event.change_id:
                    raise HarnessError("response_case_mismatch")
                direct_id = next((v for k, v in arguments.items() if k != "program_id"), arguments.get("program_id"))
                if "id" in data and data["id"] != direct_id:
                    raise HarnessError("response_record_mismatch")
                elapsed = round((time.perf_counter() - started) * 1000, 2)
                sid = registry.add(tool_name, arguments, data, self.role, self.invocation_id, receipt, elapsed)
                self.seen_sources.add(sid)
                self.harness.recorder.calls = registry.calls
                span.span_data.data.update(source_id=sid, call_id=receipt["call_id"],
                    mcp_correlation_id=receipt["correlation_id"], latency_ms=elapsed)
                # The source remains byte-equivalent in the registry. The model receives
                # a host citation receipt alongside the unchanged business data.
                enriched = {**payload, "data": {**data, "_receipt": registry.state.source_references[-1].model_dump()}}
                return result.model_copy(update={"structured_content": enriched,
                    "content": [TextContent(type="text", text=json.dumps(enriched, allow_nan=False))]})
            except HarnessError:
                raise
            except InvestigatorError:
                raise HarnessError("mcp_source_rejected") from None
            except TimeoutError:
                raise HarnessError("tool_timeout") from None
            except Exception:
                raise HarnessError("mcp_call_failed") from None
