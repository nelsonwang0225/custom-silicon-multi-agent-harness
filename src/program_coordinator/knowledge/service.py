"""Shared versioned index with source-first eligibility and fail-closed reads."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import sqlite3
import time
from uuid import uuid4
from urllib.parse import urlencode, quote
from .models import (KnowledgeDocument, Chunk, KnowledgeResult, SearchRequest, SearchResponse, KnowledgeSourceReference,
    IndexStatus, IndexDocument, Verification, PROFILES)
from .corpus import chunk, digest
from .providers import OfflineIndexProvider
from ..application.models import WorkflowError, now_utc
from ..application.observability import visible
from ..control_host.access import require_surface, project, SCOPE

class KnowledgeService:
    def __init__(self, directory, corpus, provider=None):
        self.directory=Path(directory)/'knowledge'
        self.corpus=corpus; self.provider=provider or OfflineIndexProvider()

    @contextmanager
    def db(self):
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        with sqlite3.connect(self.directory/'index.sqlite3',timeout=30) as db:
            db.execute('CREATE TABLE IF NOT EXISTS documents (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, document_key TEXT NOT NULL, value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS searches (id TEXT PRIMARY KEY, value TEXT NOT NULL)')
            yield db

    def get(self,db,key,default=None):
        row=db.execute('SELECT value FROM metadata WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default
    def put(self,db,key,value):
        db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',(key,json.dumps(value)))
    def key(self,d):
        m=d.metadata
        return digest([m.document_id,m.document_version,m.content_version,m.content_hash])
    def corpus_digest(self,docs): return digest([d.model_dump(mode='json') for d in docs])
    def allowed(self,actor,m):
        return (m.customer_id,m.program_id)==SCOPE and (m.access_roles is None or actor.role in m.access_roles)
    def source(self,actor,customer=SCOPE[0],program=SCOPE[1]):
        require_surface(actor,'knowledge')
        actor.require_scope(customer,program)
        if (customer,program)!=SCOPE: raise WorkflowError('SCOPE_FORBIDDEN')
        return self.corpus.documents(customer,program)
    def reference(self,c):
        m=c.metadata
        return KnowledgeSourceReference(document_id=m.document_id,document_version=m.document_version,content_version=m.content_version,
            content_hash=m.content_hash,path='/api/v1/engineering/documents/'+quote(m.document_id,safe=''),
            verification_path='/control-api/knowledge/verify/'+c.chunk_id)

    def status(self,actor):
        docs=self.source(actor)
        with self.db() as db:
            indexed=self.get(db,'digest:'+self.provider.name)
            receipts=self.get(db,'receipts:'+self.provider.name,{})
            rows=[]
            for d in docs:
                if not self.allowed(actor,d.metadata): continue
                chunks=chunk(d); count=sum(bool(receipts.get(c.chunk_id,{}).get('indexed')) for c in chunks)
                rows.append(IndexDocument(metadata=d.metadata,indexed=count==len(chunks) and count>0,
                    current=not bool(d.metadata.superseded_by),superseded=bool(d.metadata.superseded_by),chunk_count=count))
            # Scope digest is never used as a permission; no restricted document counts are exposed.
            current=self.corpus_digest(docs)
            return IndexStatus(provider=self.provider.name,state='not_indexed' if indexed is None else 'current' if current==indexed else 'out_of_date',
                corpus_digest=current,indexed_digest=indexed,documents=rows,
                updated_at=self.get(db,'updated:'+self.provider.name),can_reindex=project(actor).demo_controls)

    def sync(self,actor,*,rebuild=False):
        require_surface(actor,'knowledge')
        if not project(actor).demo_controls: raise WorkflowError('SURFACE_FORBIDDEN')
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        with (self.directory/'sync.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            docs=self.source(actor)
            with self.db() as db:
                receipts=self.get(db,'receipts:'+self.provider.name,{})
                old=[KnowledgeDocument.model_validate_json(r[0]) for r in db.execute('SELECT value FROM documents')]
                # A changed body cannot reuse a version/content-version identity.
                for d in docs:
                    for prior in old:
                        a,b=d.metadata,prior.metadata
                        if (a.document_id,a.document_version,a.content_version)==(b.document_id,b.document_version,b.content_version) and a.content_hash!=b.content_hash:
                            raise WorkflowError('KNOWLEDGE_VERSION_CONFLICT')
                historical={self.key(d):d for d in old}
                historical.update({self.key(d):d for d in docs})
                chunks=[c for d in historical.values() for c in chunk(d)]
            def save(receipts):
                with self.db() as db: self.put(db,'receipts:'+self.provider.name,receipts)
            receipts=self.provider.index(chunks,receipts,save)
            # Re-read authoritative corpus before publishing a completed generation.
            if self.corpus_digest(docs)!=self.corpus_digest(self.source(actor)):
                raise WorkflowError('KNOWLEDGE_SOURCE_CHANGED')
            with self.db() as db:
                if rebuild: db.execute('DELETE FROM chunks')
                for d in historical.values():
                    key=self.key(d)
                    db.execute('INSERT OR REPLACE INTO documents VALUES (?,?)',(key,d.model_dump_json()))
                    for c in chunk(d): db.execute('INSERT OR REPLACE INTO chunks VALUES (?,?,?)',(c.chunk_id,key,c.model_dump_json()))
                self.put(db,'receipts:'+self.provider.name,receipts)
                self.put(db,'digest:'+self.provider.name,self.corpus_digest(docs))
                self.put(db,'updated:'+self.provider.name,now_utc())
        return self.status(actor)

    def eligible(self,actor,c,current,request):
        m=c.metadata; f=request.metadata_filters
        source=current.get(m.document_id)
        if source is None or not self.allowed(actor,source.metadata) or not self.allowed(actor,m): return False
        latest=source.metadata
        if m.document_type not in PROFILES[request.retrieval_profile]: return False
        if m.approval_status in {'draft','rejected','requested'}: return False
        if latest.approval_status != 'approved' and not (latest.historical and f.include_historical): return False
        if self.key(KnowledgeDocument(metadata=m,content=''))==self.key(source) and m!=latest: return False
        prior=self.key(KnowledgeDocument(metadata=m,content=''))!=self.key(source)
        if (prior or latest.superseded_by or m.superseded_by) and not f.include_prior_versions: return False
        if m.historical and not f.include_historical: return False
        if m.approval_status!='approved' and not (m.historical and f.include_historical): return False
        if m.effective_date:
            try:
                # Never treat a future effective date as applicable at retrieval time.
                effective=datetime.fromisoformat(m.effective_date.replace('Z','+00:00'))
                if effective.tzinfo is None: effective=effective.replace(tzinfo=timezone.utc)
                source_time=datetime.now(timezone.utc)
                if effective > source_time: return False
            except ValueError: return False
        if f.document_ids and m.document_id not in f.document_ids: return False
        if f.document_types and m.document_type not in f.document_types: return False
        if f.document_version and m.document_version!=f.document_version: return False
        if f.configuration_id and m.configuration_id!=f.configuration_id: return False
        if f.product and m.product!=f.product: return False
        return True

    def search_knowledge(self,actor,request: SearchRequest):
        started=time.perf_counter(); query_id='knowledge_'+uuid4().hex
        docs=self.source(actor,request.customer_id,request.program_id)
        if request.retrieval_profile=='COORDINATOR': raise WorkflowError('KNOWLEDGE_SPECIALIST_PROFILE_REQUIRED')
        current={d.metadata.document_id:d for d in docs}
        with self.db() as db:
            receipts=self.get(db,'receipts:'+self.provider.name,{})
            generation=self.get(db,'digest:'+self.provider.name)
            candidates=[Chunk.model_validate_json(row[0]) for row in db.execute('SELECT value FROM chunks')]
        eligible=[c for c in candidates if self.eligible(actor,c,current,request)]
        ranked=self.provider.search(request.query,eligible,receipts,request.max_results)
        if self.corpus_digest(docs)!=self.corpus_digest(self.source(actor,request.customer_id,request.program_id)):
            raise WorkflowError('KNOWLEDGE_SOURCE_CHANGED')
        # A provider cannot insert passages, broaden scope or change metadata.
        permitted={c.chunk_id:c for c in eligible}
        results=[]; seen=set()
        for cid,score in ranked:
            if cid not in permitted or cid in seen: continue
            seen.add(cid); c=permitted[cid]; m=c.metadata
            is_current=self.key(KnowledgeDocument(metadata=m,content=''))==self.key(current[m.document_id]) and not current[m.document_id].metadata.superseded_by
            flags=[]
            if not is_current: flags.append('prior_or_superseded_version')
            if m.historical: flags.append('historical_report')
            if m.configuration_id is None: flags.append('configuration_not_recorded')
            results.append(KnowledgeResult(document_id=m.document_id,document_version=m.document_version,chunk_id=cid,title=m.title,
                section=c.section,passage=c.passage,metadata=m,source_reference=self.reference(c),score=score,rank=len(results)+1,current=is_current,flags=flags))
            if len(results)>=request.max_results: break
        latency=round((time.perf_counter()-started)*1000,2)
        state='not_indexed' if generation is None else 'current' if generation==self.corpus_digest(docs) else 'out_of_date'
        response=SearchResponse(query_id=query_id,provider=self.provider.name,results=results,result_count=len(results),latency_ms=latency,index_state=state)
        with self.db() as db:
            db.execute('INSERT INTO searches VALUES (?,?)',(query_id,json.dumps({
                'at':now_utc(),'actor_id':actor.actor_id,'query':visible(request.query),'retrieval_profile':request.retrieval_profile,
                'permitted_scope':[request.customer_id,request.program_id],'filters':request.metadata_filters.model_dump(),
                'provider':self.provider.name,'latency_ms':latency,'result_count':len(results),
                'results':[{'document_id':r.document_id,'chunk_id':r.chunk_id,'document_version':r.document_version,'content_version':r.metadata.content_version,'record_version':r.metadata.record_version} for r in results]})))
        return response

    def verify(self,actor,cid):
        docs=self.source(actor)
        current={d.metadata.document_id:d for d in docs}
        with self.db() as db:
            row=db.execute('SELECT value FROM chunks WHERE id=?',(cid,)).fetchone()
        if row is None: raise WorkflowError('KNOWLEDGE_NOT_FOUND')
        c=Chunk.model_validate_json(row[0]); source=current.get(c.metadata.document_id)
        if source is None or not self.allowed(actor,source.metadata) or not self.allowed(actor,c.metadata):
            raise WorkflowError('KNOWLEDGE_NOT_FOUND')
        same=self.key(source)==self.key(KnowledgeDocument(metadata=c.metadata,content='')) and source.metadata==c.metadata
        return Verification(verified=same,status='exact_current_source_verified' if same else 'source_version_changed',
            document=source if same else None,reference=self.reference(c))

    def record_event(self,event):
        event=event.model_copy(deep=True)
        event.query=visible(event.query);event.why_relevant=visible(event.why_relevant)
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS retrieval_events (id TEXT PRIMARY KEY,value TEXT NOT NULL)')
            db.execute('INSERT OR REPLACE INTO retrieval_events VALUES (?,?)',(event.event_id,event.model_dump_json()))

    def recent_events(self,actor,*,run_id=None,case_id=None,document_id=None,limit=100):
        from .models import KnowledgeEvent
        docs={d.metadata.document_id:d.metadata for d in self.source(actor)}
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS retrieval_events (id TEXT PRIMARY KEY,value TEXT NOT NULL)')
            rows=db.execute('SELECT value FROM retrieval_events ORDER BY rowid DESC LIMIT 1000').fetchall()
        results=[]
        for row in rows:
            e=KnowledgeEvent.model_validate_json(row[0])
            if run_id and e.run_id!=run_id: continue
            if case_id and e.case_id!=case_id: continue
            if document_id and not any(p.document_id==document_id for p in e.passages): continue
            # A session's explanatory queries remain private to its owning persona.
            if e.session_id and e.actor_id!=actor.actor_id: continue
            # Suppress the entire query when any returned document is no longer accessible.
            if any(p.document_id not in docs or not self.allowed(actor,docs[p.document_id])
                   or not self.allowed(actor,p.metadata) for p in e.passages): continue
            if not e.passages and e.actor_id!=actor.actor_id: continue
            for p in e.passages:
                current=docs[p.document_id]
                if p.metadata!=current:
                    p.current=False
                    p.verification_state='source_changed_since_run'
            results.append(e)
            if len(results)>=min(limit,100): break
        return results

    def passage(self,actor,cid):
        verified=self.verify(actor,cid)  # Rechecks source scope/access, even for retained history.
        with self.db() as db:
            row=db.execute('SELECT value FROM chunks WHERE id=?',(cid,)).fetchone()
        c=Chunk.model_validate_json(row[0])
        return KnowledgeResult(document_id=c.metadata.document_id,document_version=c.metadata.document_version,
            chunk_id=c.chunk_id,title=c.metadata.title,section=c.section,passage=c.passage,metadata=c.metadata,
            source_reference=self.reference(c),score=None,rank=1,current=verified.verified and not bool(c.metadata.superseded_by),
            flags=['historical_report'] if c.metadata.historical else [])
