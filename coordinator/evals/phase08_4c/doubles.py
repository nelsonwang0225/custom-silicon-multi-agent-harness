"""Developer-only deterministic SDK runner: real CaseHarness and MCP/HTTP reads."""
import asyncio,json,os
from types import SimpleNamespace
from agents import set_tracing_disabled
from program_coordinator.harness import CaseHarness
from program_coordinator.models import TriageDecision,CoordinatorReview,FinalDecisionPackage,WorkRequest,SpecialistSynopsis,DeliveryAssessment
from program_coordinator.delivery import claim
from program_investigator.telemetry import Recorder
from enterprise_api.delivery_models import DeliveryContext
from coordinator.evals.phase08_4a.doubles import fact

class DeliveryModelDouble:
    def __init__(self,h,delay=.02):self.h,self.delay=h,delay;self.active=0;self.peak_active=0
    async def __call__(self,agent,prompt,**kwargs):
        h=self.h
        if issubclass(agent.output_type,TriageDecision):
            out=TriageDecision(classified_change_type='delivery_readiness',confidence=.95,rationale='Reconcile exact demand, technical readiness, inventory and logistics.',
                specialists_required=[WorkRequest(specialist=r,question=q,rationale='Establish source facts and bounded authority.',focus_record_ids=['DR-009'],depends_on=[]) for r,q in [
                    ('manufacturing','Verify shared Manufacturing lots, released quantities, holds and allocations.'),('validation_evidence','Verify exact technical evidence and Engineering clearance.'),('program_commercial','Verify order, requested date semantics, logistics and delivery options.')]],
                missing_information=[],risk_level='high',proposed_workflow='Connected delivery recovery.',likely_policy_path='human_review_required')
        elif issubclass(agent.output_type,CoordinatorReview):
            out=CoordinatorReview(additional_work=[],disagreements=[],unresolved_questions=[],ready_to_synthesize=True)
        elif agent.output_type is FinalDecisionPackage:
            c=h.sources.latest('get_delivery_context');context=DeliveryContext.model_validate(c['data']);p=h.state.policy_decision
            out=FinalDecisionPackage(case_id=h.state.case_id,customer_id=h.state.customer_id,program_id=h.state.program_id,
                classified_change_type='delivery_readiness',delivery=claim(context),change_summary='Delivery options are source-grounded; partial commitment requires exact human review.',
                affected_scope=[],specialist_findings=[SpecialistSynopsis(invocation_id=r.invocation_id,specialist=r.specialist,summary=r.assessment.summary) for r in h.state.completed_assessments],
                confirmed_facts=[fact(h,c,'/analysis/eligible_quantity','The calculator excludes held material from eligible supply.')],evidence_gaps=[],available_options=[],
                relevant_constraints=[],program_impact=[],risks=[],unresolved_questions=list(h.state.unresolved_questions),recommended_next_step='Review the exact supported commitment when readiness gates permit; otherwise resolve source blockers.',
                policy_path=p.policy_path,requires_human_review=True,escalation_reason=' '.join(p.reasons) if p.policy_path=='escalation_required' else None,
                source_references=list(h.state.source_references),business_actions_executed=False,approval_granted=False,customer_accepted=False,new_validation_pass_claimed=False)
        else:
            self.active+=1;self.peak_active=max(self.peak_active,self.active)
            try:
                await asyncio.sleep(self.delay);server=agent.mcp_servers[0]
                c=h.intake['delivery'];context=DeliveryContext.model_validate(c['data'])
                if server.role=='manufacturing':
                    for material in context.material:
                        await server.call_tool('get_manufacturing_lot',{'lot_id':material.lot_id})
                elif server.role=='validation_evidence':
                    await server.call_tool('get_configuration',{'configuration_id':context.request.configuration_id})
                    for evidence in context.evidence:
                        await server.call_tool('get_validation_result',{'result_id':evidence['id']})
                else:
                    await server.call_tool('get_program_milestone',{'program_id':context.program_id,'milestone_id':context.request.milestone_id})
                    await server.call_tool('get_customer_order',{'order_id':context.request.order_id})
                out=DeliveryAssessment(case_id=h.state.case_id,summary='Source-grounded delivery readiness, quantity and timing assessment.',confidence=.95,
                    unresolved_questions=['Customer agreement and actual shipment remain separate.'],source_references=[r for r in h.state.source_references if r.source_id in h.intake_source_ids|server.seen_sources],
                    context_source_id=c['source_id'],delivery=claim(context),findings=[fact(h,c,'/analysis/technical_readiness','Technical readiness is assessed separately from supply.'),
                    fact(h,c,'/analysis/gap_quantity','The calculator records current supply exposure.')])
            finally:self.active-=1
        return SimpleNamespace(final_output=out)

class DeliveryInvestigationDouble:
    def __init__(self,config,delay=.02):self.config,self.delay=config,delay;self.harnesses=[];self.calls=0
    async def __call__(self,incoming,run,checkpoint):
        self.calls+=1;set_tracing_disabled(True);checkpoint.parent.mkdir(parents=True,exist_ok=True)
        def save(state):
            temp=checkpoint.with_suffix('.next');temp.write_text(json.dumps(state));os.replace(temp,checkpoint)
        h=CaseHarness(self.config,incoming.event,None,Recorder('trace_'+'2'*32),checkpoint=save,case_id=run.case_id,run_id=run.run_id,workflow_id=run.workflow_id,workflow_definition_version=run.definition_version)
        h.runner=DeliveryModelDouble(h,self.delay);self.harnesses.append(h)
        try:return await h.run()
        finally:
            h.checkpoint()
            (checkpoint.parent/'tool-calls.json').write_text(json.dumps(h.sources.calls))
