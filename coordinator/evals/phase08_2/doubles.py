"""Existing CaseHarness/model double, with source reads through the real gateway."""
import asyncio
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'coordinator/tests'))
from agents import set_tracing_disabled
from helpers import request, harness
from test_orchestration import ModelDouble, MemorySession

class InvestigationDouble:
    def __init__(self, source, *, delay=0.03, failure=False):
        self.source, self.delay, self.failure = source, delay, failure
        self.calls = 0

    async def __call__(self, incoming, run, checkpoint):
        self.calls += 1
        set_tracing_disabled(True)
        h = harness(server_factory=MemorySession, event=incoming.event)
        for call in json.loads((ROOT / 'coordinator/tests/data/cr017_reads.json').read_text()):
            data = getattr(self.source.read, call['tool'])(**call['arguments'])
            h.sources.add(call['tool'], call['arguments'], data, 'validation_evidence', 'work_test', {}, 0.0)
        h.state.scope_verified = True
        h.intake_source_ids = {r.source_id for r in h.state.source_references}
        async def intake(): pass
        h.intake_case = intake
        h.state.case_id, h.state.run_id = run.case_id, run.run_id
        h.state.workflow_id, h.state.workflow_definition_version = run.workflow_id, run.definition_version
        checkpoint.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        def save(state):
            temp = checkpoint.with_suffix('.next')
            temp.write_text(json.dumps(state))
            os.replace(temp, checkpoint)
        h.checkpoint_callback = save
        model = ModelDouble(h, [request('change_impact'), request('validation_evidence'), request('program_commercial')],
            nested=True, delay=self.delay, fail='validation_evidence' if self.failure else None)
        async def scoped_model(agent, prompt, **kwargs):
            result = await model(agent, prompt, **kwargs)
            # This old fixture helper copies every reference in the run. With
            # parallel RAG a sibling can add references after a task starts.
            # Match real per-invocation visibility instead of weakening guards.
            if agent.mcp_servers:
                allowed = h.intake_source_ids | agent.mcp_servers[0].seen_sources
                result.final_output.source_references = [r for r in result.final_output.source_references if r.source_id in allowed]
            return result
        h.runner = scoped_model
        try:
            state = await h.run()
            if self.failure:
                raise RuntimeError("Deterministic runtime failure after specialist failure")
            return state
        finally:
            h.checkpoint()
            (checkpoint.parent/"tool-calls.json").write_text(json.dumps(h.sources.calls))
