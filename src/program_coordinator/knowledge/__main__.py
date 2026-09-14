"""Explicit local index management. No arbitrary path/file ingestion."""
import argparse
import json
from pathlib import Path
from .corpus import SourceCorpus
from .service import KnowledgeService
from .providers import OfflineIndexProvider, OpenAIIndexProvider
from ..infrastructure.source_gateway import SourceGateway
from ..application.demo_identity import AUTOMATION
from ..application.models import WorkflowError


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['sync','rebuild','status','search'])
    p.add_argument('--source-url',required=True)
    p.add_argument('--metadata-dir',required=True,type=Path)
    p.add_argument('--provider',choices=['offline','openai'],default='offline')
    p.add_argument('--allow-paid',action='store_true')
    p.add_argument('--query')
    p.add_argument('--profile',default='VALIDATION_EVIDENCE')
    args=p.parse_args()
    if args.provider=='openai' and not args.allow_paid:
        p.error('OpenAI mode requires explicit --allow-paid, including search')
    provider=OfflineIndexProvider()
    if args.provider=='openai':
        from openai import OpenAI
        from program_investigator.config import load_key, PROJECT
        # Existing authorized key file; never printed or included in index metadata.
        provider=OpenAIIndexProvider(OpenAI(api_key=load_key(PROJECT/'.env.local'),max_retries=0,timeout=60))
    source=SourceGateway(args.source_url,demo_mode=True)
    try:
        service=KnowledgeService(args.metadata_dir,SourceCorpus(source.read),provider)
        if args.command in {'sync','rebuild'}: result=service.sync(AUTOMATION,rebuild=args.command=='rebuild')
        elif args.command=='status': result=service.status(AUTOMATION)
        else:
            from .models import SearchRequest
            if not args.query: p.error('--query required')
            result=service.search_knowledge(AUTOMATION,SearchRequest(query=args.query,retrieval_profile=args.profile))
        print(result.model_dump_json(indent=2))
    except WorkflowError as exc:
        p.exit(1,str(exc)+'\n')
    finally: source.close()

if __name__=='__main__': main()
