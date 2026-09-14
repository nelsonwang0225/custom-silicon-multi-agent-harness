"""Explicit local demo host. Starting it does not load a key or invoke a model."""
import argparse
import os
from pathlib import Path
import re
import time
import uvicorn
from program_investigator.config import PROJECT
from ..application.store import ActivityStore
from ..infrastructure.source_gateway import SourceGateway, HumanDecisionGateway
from ..controls import HarnessConfig
from ..models import ProgramChangeEvent
from .server import ControlHost, create_app

async def live_investigation(request, run, checkpoint, *, config, store):
    # Reuse the existing bounded CaseHarness and API configuration verbatim.
    # Imports and credential loading are deferred until WorkflowService admits an explicit invocation.
    from agents.tracing import trace, gen_trace_id
    from program_investigator.config import load_key
    from program_investigator.telemetry import Recorder
    from .runtime import metadata_router
    from ..__main__ import execute
    key = load_key(PROJECT / '.env.local')
    recorder = Recorder(gen_trace_id())
    checkpoint.parent.mkdir(parents=True, mode=0o700, exist_ok=False)
    from program_investigator.config import MODEL
    from program_investigator.__main__ import write_artifact
    from ..application.models import now_utc
    # Same existing artifacts and sanitized SDK Recorder as the CLI, no new trace store.
    run.trace_id=recorder.trace_id
    with store.transaction(write=True) as index:
        index.runs[run.run_id].trace_id=recorder.trace_id
        for activity in index.activity:
            if activity.run_id==run.run_id:activity.trace_id=recorder.trace_id
    started=time.perf_counter()
    report = {'api_requests': [],'run_id':run.run_id,'case_id':run.case_id,'trace_id':recorder.trace_id,'model':MODEL,'timestamp':now_utc()}
    metadata_router.recorders[recorder.trace_id] = recorder
    try:
        with trace('Stratos Program Coordinator', trace_id=recorder.trace_id, group_id=run.correlation_id):
            return await execute(config, request.event, recorder, key, report, checkpoint.parent, run_record=run)
    finally:
        metadata_router.recorders.pop(recorder.trace_id, None)
        report.pop('output',None)
        report.update(latency_ms=round((time.perf_counter()-started)*1000,2),generations=recorder.generations,
            usage={name:sum(g['usage'][name] for g in recorder.generations) for name in ('input_tokens','output_tokens','total_tokens')} if recorder.generations else {},
            usage_scope='completed_generations_only',platform_trace_visibility_verified=False)
        # Observation failure must not reinterpret an admitted workflow or business write.
        try:
            write_artifact(checkpoint.parent/'report.json',report,key)
            write_artifact(checkpoint.parent/'tool-calls.json',recorder.calls,key)
            write_artifact(checkpoint.parent/'trace-metadata.json',recorder.spans,key)
        except OSError:
            pass



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18082)
    parser.add_argument('--source-url', required=True)
    parser.add_argument('--mcp-url', default='http://127.0.0.1:19082/mcp')
    parser.add_argument('--metadata-dir', type=Path, required=True)
    parser.add_argument('--ui-origin', default='http://127.0.0.1:5188')
    parser.add_argument('--enable-demo-controls', action='store_true',
        help='Explicitly enable local demo reset for DEMO_DB; verifies it matches --source-url')
    parser.add_argument('--allow-paid-knowledge-search', action='store_true', help='Explicitly use the shared OpenAI vector-store index for knowledge search; never index at startup')
    args = parser.parse_args()
    if os.environ.get('DEMO_MODE') != 'true':
        parser.error('DEMO_MODE=true is required')
    if not re.fullmatch(r'http://127\.0\.0\.1:\d+', args.source_url) or not re.fullmatch(r'http://127\.0\.0\.1:\d+', args.ui_origin):
        parser.error('Source and UI must use loopback HTTP')
    config = HarnessConfig(mcp_url=args.mcp_url)
    event = ProgramChangeEvent.model_validate_json((PROJECT / 'coordinator/scenarios/human_review.json').read_text())
    source = SourceGateway(args.source_url, demo_mode=True)
    human = HumanDecisionGateway(args.source_url, demo_mode=True)
    from mock_enterprise.config import Settings
    from .runtime import DemoInvestigation
    store = ActivityStore(args.metadata_dir)
    host = ControlHost(store, source, human, config, DemoInvestigation(config, store), event,
        demo_settings=Settings.environment() if args.enable_demo_controls else None)
    if args.allow_paid_knowledge_search:
        from ..knowledge.service import KnowledgeService
        from ..knowledge.corpus import SourceCorpus
        from ..knowledge.providers import OpenAIIndexProvider
        host.knowledge=KnowledgeService(host.store.directory,SourceCorpus(source.read),OpenAIIndexProvider())
    try:
        uvicorn.run(create_app(host, allowed_origins=(args.ui_origin,)), host='127.0.0.1', port=args.port, access_log=False)
    finally:
        human.close()
        source.close()

if __name__ == '__main__':
    main()
