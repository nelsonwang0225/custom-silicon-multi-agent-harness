"""Safe local metadata and redacted SDK trace spans. Never record model reasoning."""

from dataclasses import dataclass, field
import re
import time

from agents import RunHooks
from agents.tracing import TracingProcessor


def safe_id(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,160}", value) else None


def usage_metadata(usage):
    return {
        "requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "cached_input_tokens": getattr(usage.input_tokens_details, "cached_tokens", 0),
        "reasoning_tokens": getattr(usage.output_tokens_details, "reasoning_tokens", 0),
    }


@dataclass
class Recorder:
    trace_id: str
    catalog: list[dict] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
    generations: list[dict] = field(default_factory=list)
    spans: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    candidate_output: dict | None = None
    usage: dict | None = None


class MetadataHooks(RunHooks):
    def __init__(self, recorder):
        self.recorder = recorder
        self.started = 0.0

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        self.started = time.perf_counter()

    async def on_llm_end(self, context, agent, response):
        self.recorder.generations.append({
            "response_id": safe_id(response.response_id), "request_id": safe_id(response.request_id),
            "latency_ms": round((time.perf_counter() - self.started) * 1000, 2),
            "usage": usage_metadata(response.usage),
        })


class SafeMetadataProcessor(TracingProcessor):
    """Runs before the SDK exporter, sanitizing errors and discarding payloads."""
    def __init__(self, recorder):
        self.recorder = recorder

    def on_trace_start(self, trace):
        pass

    def on_trace_end(self, trace):
        pass

    def on_span_start(self, span):
        pass

    def on_span_end(self, span):
        data = span.span_data
        # Defense in depth even when a caller accidentally changes RunConfig.
        for field_name in ("input", "output"):
            if hasattr(data, field_name):
                setattr(data, field_name, None)
        if span.error:
            span.set_error({"message": "investigator_operation_failed", "data": {}})
        self.recorder.spans.append({"trace_id": span.trace_id, "span_id": span.span_id,
                                   "parent_id": span.parent_id, "type": data.type,
                                   "started_at": span.started_at, "ended_at": span.ended_at,
                                   "error": bool(span.error),
                                   **{k: safe_id(v) for k,v in (getattr(data, "data", None) or {}).items()
                                      if k in {"tool", "role", "invocation_id"} and safe_id(v)}})

    def force_flush(self):
        pass

    def shutdown(self):
        pass
