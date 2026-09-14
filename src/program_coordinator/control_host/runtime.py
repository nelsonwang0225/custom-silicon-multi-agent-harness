"""Explicit live demo composition. No credentials or API calls at startup."""
from agents import set_trace_processors, set_tracing_disabled
from agents.tracing import TracingProcessor
from program_investigator.telemetry import SafeMetadataProcessor
from ..demo_opening import ScriptedOpening


class RunMetadataRouter(TracingProcessor):
    """Route sanitized spans to their own run even during concurrent work."""
    def __init__(self):
        self.recorders = {}

    def on_trace_start(self, trace): pass
    def on_trace_end(self, trace): pass
    def on_span_start(self, span): pass
    def force_flush(self): pass
    def shutdown(self): pass

    def on_span_end(self, span):
        recorder = self.recorders.get(span.trace_id)
        if recorder is not None:
            SafeMetadataProcessor(recorder).on_span_end(span)


metadata_router = RunMetadataRouter()


class DemoInvestigation:
    case_modes = {'CR-017':'live_model', 'CR-019':'live_model',
                  'QE-004':'live_model', 'DR-009':'live_model',
                  'QE-011':'deterministic_test'}

    def __init__(self, config, store):
        self.config, self.store = config, store
        self.opening = ScriptedOpening(config)
        # One process-wide sanitizer, with trace-specific destinations. Scripted
        # work uses a disabled trace context and never changes these settings.
        set_trace_processors([metadata_router])
        set_tracing_disabled(False)

    async def __call__(self, incoming, run, checkpoint):
        change_id = incoming.event.change_id
        if change_id == 'QE-011':
            return await self.opening(incoming, run, checkpoint)
        if self.case_modes.get(change_id) != 'live_model':
            raise ValueError('LIVE_DEMO_CASE_REQUIRED')
        from .__main__ import live_investigation
        # Failure is a failed live run. There is deliberately no scripted fallback.
        return await live_investigation(incoming, run, checkpoint, config=self.config, store=self.store)
