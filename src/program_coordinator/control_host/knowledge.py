"""Thin local host routes. Index writes are operator-only, never agent tools."""
from fastapi import Request
from starlette.concurrency import run_in_threadpool
from ..knowledge.corpus import SourceCorpus
from ..knowledge.service import KnowledgeService
from ..knowledge.models import SearchRequest, SearchResponse, IndexStatus, SyncRequest, Verification, KnowledgeEvent, KnowledgeResult
from ..application.models import WorkflowError
from .access import resolve_actor, project, require_surface


def install(app,host):
    # Construction does not read documents, initialize an index, load keys or call a provider.
    if not hasattr(host,'knowledge'):
        host.knowledge=KnowledgeService(host.store.directory,SourceCorpus(host.source.read))

    @app.get('/control-api/knowledge',response_model=IndexStatus)
    async def status(request:Request):
        return await run_in_threadpool(host.knowledge.status,resolve_actor(request))

    @app.post('/control-api/knowledge/search',response_model=SearchResponse)
    async def search(body:SearchRequest,request:Request):
        return await run_in_threadpool(host.knowledge.search_knowledge,resolve_actor(request),body)

    @app.get('/control-api/knowledge/verify/{chunk_id}',response_model=Verification)
    async def verify(chunk_id:str,request:Request):
        return await run_in_threadpool(host.knowledge.verify,resolve_actor(request),chunk_id)

    @app.get('/control-api/knowledge/passages/{chunk_id}',response_model=KnowledgeResult)
    async def passage(chunk_id:str,request:Request):
        return await run_in_threadpool(host.knowledge.passage,resolve_actor(request),chunk_id)

    @app.get('/control-api/knowledge/events',response_model=list[KnowledgeEvent])
    async def events(request:Request,run_id:str|None=None,case_id:str|None=None,document_id:str|None=None):
        actor=resolve_actor(request)
        # Case/run provenance never surfaces archived/reset runs or another scope.
        with host.store.transaction() as data:
            active_runs={rid for rid,r in data.runs.items() if (r.customer_id,r.program_id)==('CUST-FML01','PRG-A17')}
            active_sessions={sid for sid,s in data.concierge_sessions.items() if s.owner_actor_id==actor.actor_id}
        values=await run_in_threadpool(host.knowledge.recent_events,actor,run_id=run_id,case_id=case_id,document_id=document_id)
        return [e for e in values if (e.session_id in active_sessions if e.session_id else e.run_id in active_runs)]

    @app.post('/control-api/knowledge/reindex',response_model=IndexStatus)
    async def reindex(body:SyncRequest,request:Request):
        actor=resolve_actor(request,write=True)
        require_surface(actor,'knowledge')
        if not project(actor).demo_controls: raise WorkflowError('SURFACE_FORBIDDEN')
        # Hosted indexing can incur charges; available only through the explicit CLI.
        if host.knowledge.provider.name!='deterministic_offline':
            raise WorkflowError('KNOWLEDGE_USE_EXPLICIT_LIVE_SYNC')
        return await run_in_threadpool(host.knowledge.sync,actor,rebuild=body.rebuild)
