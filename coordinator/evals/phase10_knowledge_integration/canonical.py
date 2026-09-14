"""Before/after canonical conclusions through real local HTTP/MCP, scripted SDK doubles."""
import asyncio
from contextlib import nullcontext
import json
from pathlib import Path
from types import SimpleNamespace
from mock_enterprise.config import Settings
from mock_enterprise.seed import initialize
from mock_enterprise.standard_upgrade import install as standard
from mock_enterprise.delivery_upgrade import install as delivery
from coordinator.evals.phase08_4a.network import network
from coordinator.evals.phase08_2.doubles import InvestigationDouble
from coordinator.evals.phase08_4a.doubles import StandardInvestigationDouble
from coordinator.evals.phase08_4b.doubles import QualityInvestigationDouble
from coordinator.evals.phase08_4c.doubles import DeliveryInvestigationDouble
from program_coordinator.infrastructure.source_gateway import SourceGateway
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import ProgramChangeEvent
from program_coordinator.control_host import standard_change,quality,delivery as delivery_host
from enterprise_api.standard_models import StandardContext
from enterprise_api.quality_models import QualityContext
from enterprise_api.delivery_models import DeliveryContext
from program_coordinator.knowledge.corpus import SourceCorpus
from program_coordinator.knowledge.service import KnowledgeService
from program_coordinator.knowledge.integration import KnowledgeContext,current_knowledge_context
from program_coordinator.application.demo_identity import AUTOMATION,READER
from .doubles import scripted_retrieval

def conclusion(state):
    package=state.final_package
    assert state.workflow_stage=='completed',state.guardrail_events
    assert package is not None
    keys=['classified_change_type','policy_path','requires_human_review','business_actions_executed',
          'approval_granted','customer_accepted','new_validation_pass_claimed','quality','delivery']
    value=package.model_dump(mode='json')
    result={k:value.get(k) for k in keys}
    result['eligible_options']=[{k:o.model_dump(mode='json').get(k) for k in ('slot_id','sample_id','cost_cents','test_complete_at','engineering_review_complete_at')} for o in package.available_options]
    result['coverage']=[r.assessment.coverage_status for r in state.completed_assessments if hasattr(r.assessment,'coverage_status')]
    return result

def run(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    settings=Settings(root/'source.sqlite3',root,True);initialize(settings);standard(settings);delivery(settings)
    results=[]
    with network(settings) as (url,mcp):
        source=SourceGateway(url,demo_mode=True)
        try:
            cfg=HarnessConfig(mcp_url=mcp)
            k=KnowledgeService(root/'metadata',SourceCorpus(source.read));k.sync(AUTOMATION)
            events={
                'CR-017':ProgramChangeEvent.model_validate_json(Path('coordinator/scenarios/human_review.json').read_text()),
                'CR-019':standard_change.event(StandardContext.model_validate(source.read.get_standard_change_context('CR-019'))),
                'QE-004':quality.event(QualityContext.model_validate(source.read.get_quality_context('QE-004'))),
                'DR-009':delivery_host.event(DeliveryContext.model_validate(source.read.get_delivery_context('DR-009')))}
            doubles={'CR-017':InvestigationDouble(source),'CR-019':StandardInvestigationDouble(cfg),
                     'QE-004':QualityInvestigationDouble(cfg),'DR-009':DeliveryInvestigationDouble(cfg)}
            for case,event in events.items():
                values={}
                for mode in ['before','after']:
                    record=SimpleNamespace(case_id='case_'+case.replace('-',''),run_id='run_'+case.replace('-','')+'_'+mode,
                        workflow_id={'QE-004':'yield_exception_recovery','DR-009':'delivery_readiness'}.get(case,'requirement_change_analysis'),definition_version=1)
                    token=current_knowledge_context.set(KnowledgeContext(k,READER) if mode=='after' else None)
                    try:
                        with scripted_retrieval() if mode=='after' else nullcontext():
                            state=asyncio.run(doubles[case](SimpleNamespace(event=event),record,root/(case+'-'+mode)/'case-state.json'))
                        values[mode]=conclusion(state)
                    finally:current_knowledge_context.reset(token)
                entries=k.recent_events(READER,case_id=case)
                assert values['before']==values['after'],f'UNEXPECTED business conclusion change: {case}'
                assert entries or case=='DR-009'
                if case in {'CR-017','CR-019'}:assert any(p.used_in_finding for e in entries for p in e.passages)
                if case=='DR-009':assert not entries
                results.append({'case_id':case,'classification':'UNCHANGED','before':values['before'],'after':values['after'],
                    'retrievals':[e.model_dump(mode='json') for e in entries]})
        finally:source.close()
    report={'mode':'scripted_offline_HTTP_MCP_SDK_tools','paid_calls':False,'cases':results}
    (root/'business-conclusions.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
