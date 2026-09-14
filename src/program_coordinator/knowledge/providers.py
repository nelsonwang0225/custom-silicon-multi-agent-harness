"""One ranking boundary; neither provider decides applicability or authority."""
import math
import re
from collections import Counter
from typing import Protocol
from .models import Chunk
from ..application.models import WorkflowError

class KnowledgeIndexProvider(Protocol):
    name: str
    def index(self, chunks: list[Chunk], receipts: dict, save): ...
    def search(self, query: str, chunks: list[Chunk], receipts: dict, limit: int) -> list[tuple[str, float]]: ...

# Small transparent synonym normalization, not a claim of neural semantic parity.
WORDS = {'retest':'validation','testing':'validation','test':'validation','tests':'validation',
    'hold':'restriction','held':'restriction','holds':'restriction','restrictions':'restriction',
    'permission':'approval','authorize':'approval','authorized':'approval','approved':'approval',
    'requirements':'requirement','policies':'policy','procedures':'procedure','scheduling':'schedule'}
STOP = {'the','a','an','and','or','to','for','of','in','on','is','are','with','this','that','be','by','as','it','from'}
def terms(text):
    return Counter(WORDS.get(word,word) for word in re.findall(r'[a-z0-9]+',text.lower()) if word not in STOP)

class OfflineIndexProvider:
    name = 'deterministic_offline'
    def index(self, chunks, receipts, save):
        return {c.chunk_id: {'indexed':True} for c in chunks}
    def search(self, query, chunks, receipts, limit):
        q = terms(query); qnorm = math.sqrt(sum(v*v for v in q.values())) or 1
        ranked = []
        for c in chunks:
            if c.chunk_id not in receipts: continue
            t = terms(c.metadata.title+' '+(c.section or '')+' '+c.passage)
            score = sum(v*t[k] for k,v in q.items()) / (qnorm*(math.sqrt(sum(v*v for v in t.values())) or 1))
            if score > 0: ranked.append((c.chunk_id,round(score,6)))
        return sorted(ranked,key=lambda r:(-r[1],r[0]))[:limit]

class OpenAIIndexProvider:
    """Official vector-store API. Constructed only by explicit live configuration.

    One vector store, one immutable file per canonical section chunk. Its results
    identify canonical chunks; remote snippets/metadata never become authority.
    """
    name = 'openai_vector_store'
    def __init__(self, client=None): self._client = client
    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            from program_investigator.config import load_key, PROJECT
            self._client=OpenAI(api_key=load_key(PROJECT/'.env.local'),max_retries=0,timeout=60)
        return self._client
    def index(self, chunks, receipts, save):
        result = dict(receipts)
        try:
            if '_store' not in result:
                store = self.client.vector_stores.create(name='Stratos shared knowledge')
                result['_store'] = {'id':store.id}; save(result)
            for c in chunks:
                if c.chunk_id in result and result[c.chunk_id].get('indexed'): continue
                entry = result.get(c.chunk_id, {})
                if 'file_id' not in entry:
                    upload = self.client.files.create(file=(c.chunk_id+'.txt', c.passage.encode()),purpose='assistants')
                    entry = {'file_id':upload.id}; result[c.chunk_id]=entry; save(result)
                linked = None
                if entry.get('attached'):
                    linked = self.client.vector_stores.files.poll(entry['file_id'], vector_store_id=result['_store']['id'])
                else:
                    # Recover an attachment that completed before local receipt commit.
                    from openai import NotFoundError
                    try:
                        linked = self.client.vector_stores.files.retrieve(entry['file_id'], vector_store_id=result['_store']['id'])
                    except NotFoundError:
                        linked = self.client.vector_stores.files.create_and_poll(entry['file_id'], vector_store_id=result['_store']['id'],
                            attributes={'chunk_id':c.chunk_id,'document_id':c.metadata.document_id,
                                'document_version':c.metadata.document_version,'customer_id':c.metadata.customer_id,'program_id':c.metadata.program_id},
                            chunking_strategy={'type':'static','static':{'max_chunk_size_tokens':4096,'chunk_overlap_tokens':0}})
                    entry['attached']=True; save(result)
                    if linked.status=='in_progress':
                        linked = self.client.vector_stores.files.poll(entry['file_id'], vector_store_id=result['_store']['id'])
                if linked.status != 'completed': raise WorkflowError('KNOWLEDGE_PROVIDER_INDEX_FAILED')
                entry['indexed']=True; save(result)
            return result
        except Exception:
            raise WorkflowError('KNOWLEDGE_PROVIDER_INDEX_FAILED') from None
    def search(self, query, chunks, receipts, limit):
        ids = {c.chunk_id for c in chunks if receipts.get(c.chunk_id,{}).get('indexed')}
        if not ids or '_store' not in receipts: return []
        ranked = {}
        try:
            ordered=sorted(ids)
            # Filter before provider search, then enforce the identical allowlist again.
            for start in range(0,len(ordered),100):
                rows=self.client.vector_stores.search(receipts['_store']['id'],query=query,max_num_results=limit,
                    rewrite_query=False,filters={'type':'in','key':'chunk_id','value':ordered[start:start+100]})
                for row in rows.data:
                    cid=(row.attributes or {}).get('chunk_id')
                    if cid in ids and receipts[cid]['file_id']==row.file_id:
                        ranked[cid]=max(ranked.get(cid,0),row.score)
        except Exception:
            raise WorkflowError('KNOWLEDGE_PROVIDER_SEARCH_FAILED') from None
        return sorted(ranked.items(),key=lambda r:(-r[1],r[0]))[:limit]
