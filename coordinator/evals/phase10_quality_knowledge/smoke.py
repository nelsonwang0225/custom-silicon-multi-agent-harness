"""Explicit read-only QE-004 retrieval smoke against an already synchronized shared index.

No model generation, indexing, new vector store, or business mutation. OpenAI search
requires --allow-paid and an existing hosted-store receipt in --metadata-dir.
"""
import argparse
import json
from pathlib import Path
from enterprise_api.quality_models import QualityContext
from program_coordinator.application.demo_identity import READER
from program_coordinator.infrastructure.source_gateway import SourceGateway
from program_coordinator.knowledge.corpus import SourceCorpus
from program_coordinator.knowledge.models import SearchRequest, Filters
from program_coordinator.knowledge.service import KnowledgeService
from program_coordinator.knowledge.providers import OfflineIndexProvider, OpenAIIndexProvider
from program_coordinator.quality import claim

QUERIES=(
    ('DOC-QA-HOLD-01','What policy governs held material and shipment eligibility?',False),
    ('DOC-QA-HIST-01','What does prior experience say about failures concentrated at one test site?',True),
)


def check(service, source):
    before=source.read.get_quality_context('QE-004')
    c=QualityContext.model_validate(before)
    conclusions=claim(c)
    if not ('quality_hold' in c.lot['restrictions'] and conclusions.affected_eligible_quantity==0
            and conclusions.root_cause is None and not conclusions.release_authorized):
        raise ValueError('Current source no longer matches the canonical held/unresolved QE-004 smoke scope')
    results=[]
    for expected,query,historical in QUERIES:
        response=service.search_knowledge(READER,SearchRequest(query=query,retrieval_profile='MANUFACTURING_QUALITY',
            metadata_filters=Filters(include_historical=historical,configuration_id=c.exception.configuration_id,
                product=c.configuration['product_id'])))
        matching=[r for r in response.results if r.document_id==expected]
        if not matching:raise ValueError('Expected controlled publication absent: '+expected)
        passage=matching[0]
        verified=service.verify(READER,passage.chunk_id)
        if not verified.verified or verified.document.metadata!=passage.metadata:
            raise ValueError('Exact source verification failed: '+expected)
        if passage.metadata.historical != historical or passage.metadata.approval_status != ('historical' if historical else 'approved'):
            raise ValueError('Unexpected publication lifecycle: '+expected)
        results.append({'document_id':expected,'version':passage.document_version,'section':passage.section,
            'status':passage.metadata.approval_status,'profile':'MANUFACTURING_QUALITY','exact_source_verified':True})
    if source.read.get_quality_context('QE-004')!=before:
        raise ValueError('Operational source changed during verification; rerun against a stable current read')
    return {'status':'PASS','provider':service.provider.name,'knowledge':results,
        'structured_evidence':{'lot_id':c.exception.lot_id,'restrictions':c.lot['restrictions'],
            'first_pass_pass_quantity':c.observation.passed_quantity,'affected_eligible_quantity':conclusions.affected_eligible_quantity,
            'root_cause':conclusions.root_cause,'release_authorized':conclusions.release_authorized},
        'conclusion':'Current HOLD excludes first-pass passing units; historical site concentration does not establish current root cause. Human Quality disposition remains required.',
        'model_generation':False,'business_writes':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-url',required=True)
    p.add_argument('--metadata-dir',type=Path,required=True)
    p.add_argument('--provider',choices=['offline','openai'],default='offline')
    p.add_argument('--allow-paid',action='store_true')
    args=p.parse_args()
    if args.provider=='openai' and not args.allow_paid:p.error('Hosted search requires explicit --allow-paid')
    if not (args.metadata_dir/'knowledge/index.sqlite3').is_file():p.error('Existing synchronized shared index required')
    source=SourceGateway(args.source_url,demo_mode=True)
    try:
        provider=OpenAIIndexProvider() if args.provider=='openai' else OfflineIndexProvider()
        service=KnowledgeService(args.metadata_dir,SourceCorpus(source.read),provider)
        if args.provider=='openai':
            with service.db() as db:receipts=service.get(db,'receipts:'+provider.name,{})
            if '_store' not in receipts:p.error('Existing shared OpenAI store required; no new store will be created')
        print(json.dumps(check(service,source),indent=2))
    finally:source.close()


if __name__=='__main__':main()
