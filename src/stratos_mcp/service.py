"""Safe tool execution boundary over the existing GET-only enterprise client."""

import json
import logging
import time
from uuid import uuid4

import anyio
from mcp.types import CallToolResult, TextContent
from pydantic import ValidationError

from enterprise_api import EnterpriseAPIError, EnterpriseClient
from enterprise_api.errors import ErrorInfo
from enterprise_api.transport import HttpxReadTransport

from .catalog import CATALOG, ToolPayload
from .config import ServerConfig

LOGGER = logging.getLogger("stratos_mcp")


class TracedReads:
    """Keep bounded request receipts, never bodies, headers or exception strings."""

    def __init__(self, transport):
        self.transport = transport
        self.receipts = []

    def get(self, path, params):
        start = time.perf_counter()
        receipt = {"method": "GET", "path": path, "params": params}
        try:
            response = self.transport.get(path, params)
            receipt.update(status=response.status, attempts=response.attempts,
                           request_id=response.request_id, correlation_id=response.correlation_id,
                           server_correlation_id=response.server_correlation_id)
            return response
        except EnterpriseAPIError as exc:
            receipt.update(status=exc.info.http_status, attempts=exc.info.attempts,
                           request_id=exc.info.request_id, correlation_id=exc.info.correlation_id,
                           server_correlation_id=None)
            raise
        finally:
            receipt["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            self.receipts.append(receipt)

    def close(self):
        self.transport.close()


class ToolService:
    def __init__(self, config: ServerConfig, *, transport_factory=HttpxReadTransport):
        self.config = config
        self._transport_factory = transport_factory
        self._limiter = anyio.CapacityLimiter(8)

    async def call(self, name: str, arguments: dict | None) -> CallToolResult:
        # Per-call resources avoid sharing mutable scope verification or trace state.
        # Blocking HTTP runs in a bounded worker pool and is joined on cancellation.
        return await anyio.to_thread.run_sync(self._call, name, arguments, limiter=self._limiter)

    def _call(self, name, arguments):
        suffix = uuid4().hex
        trace = {"call_id": "mcp-" + suffix, "correlation_id": "corr-" + suffix, "http_reads": []}
        start = time.perf_counter()
        data = error = None
        spec = CATALOG.get(name)
        transport = None
        try:
            if spec is None:
                raise EnterpriseAPIError(ErrorInfo("input", "UNKNOWN_TOOL"))
            try:
                inputs = spec.inputs.model_validate({} if arguments is None else arguments)
            except ValidationError:
                raise EnterpriseAPIError(ErrorInfo("input", "INVALID_TOOL_INPUT")) from None
            transport = TracedReads(self._transport_factory(self.config.enterprise,
                                                           correlation_id=trace["correlation_id"]))
            with EnterpriseClient(self.config.enterprise, transport=transport) as client:
                data = spec.method(client, **inputs.model_dump())
        except EnterpriseAPIError as exc:
            error = exc.info
        except Exception:
            # Unexpected failures never serialize/log exception prose or tracebacks.
            error = ErrorInfo("server", "INTERNAL_ERROR")
        finally:
            if transport is not None:
                trace["http_reads"] = transport.receipts
                try:
                    transport.close()
                except Exception:
                    data = None
                    error = ErrorInfo("server", "INTERNAL_ERROR")
        if error:
            data = None
        trace["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        payload = ToolPayload(ok=error is None, data=data, error=error).model_dump(mode="json")
        LOGGER.info(json.dumps({"event": "tool_call", "tool": spec.name if spec else "unknown",
                                "call_id": trace["call_id"], "correlation_id": trace["correlation_id"],
                                "ok": error is None, "code": error.code if error else None,
                                "http_reads": len(trace["http_reads"]), "latency_ms": trace["latency_ms"]}))
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(payload, allow_nan=False))],
                              structured_content=payload, is_error=error is not None,
                              meta={"stratos/trace": trace})

    async def ready(self) -> bool:
        # A fresh scope-authorized GET tests actual readiness, with a short bound.
        config = self.config.enterprise.model_copy(update={"connect_timeout": 0.5, "read_timeout": 1.0,
                                                           "max_retries": 0})
        def check():
            try:
                with EnterpriseClient(config) as client:
                    client.get_program(config.scope.program_id)
                return True
            except Exception:
                return False
        return await anyio.to_thread.run_sync(check, limiter=self._limiter)
