"""Deterministic model responses through the real shared CaseHarness and MCP sessions.

No prefilled final state and no API model calls. Every business read is selected
by this developer model double and crosses the installed scoped MCP/HTTP boundary.
"""
import asyncio
import json
import os
from types import SimpleNamespace
from agents import set_tracing_disabled
from program_coordinator.harness import CaseHarness
from program_coordinator.models import (TriageDecision,CoordinatorReview,FinalDecisionPackage,WorkRequest,Finding,SourceFact,
    SpecialistSynopsis,ChangeImpactAssessment,StandardValidationAssessment,ProgramCommercialAssessment,MilestoneImpact)
from program_investigator.telemetry import Recorder
from enterprise_api.standard_models import StandardContext
from enterprise_api.standard_policy import evaluate


def fact(h,call,path,statement):
    from program_coordinator.sources import pointer
    sid=call['source_id']
    return Finding(statement=statement,basis='fact',source_refs=[sid],facts=[SourceFact(source_id=sid,pointer=path,value_json=json.dumps(pointer(call['data'],path)))])

class StandardModelDouble:
    def __init__(self,h,delay=0.02):
        self.h,self.delay=h,delay
        self.active=0;self.peak_active=0

    async def __call__(self,agent,prompt,**kwargs):
        h=self.h;value=json.loads(prompt)
        if issubclass(agent.output_type,TriageDecision):
            output=TriageDecision(classified_change_type='standard_validation_package',confidence=.95,rationale='Inspect the explicit approved-profile package request.',
                specialists_required=[WorkRequest(specialist=r,question=q,rationale='Establish exact source facts.',focus_record_ids=[h.state.event.change_id],depends_on=[])
                    for r,q in [('change_impact','Compare the approved baseline and exact requested package change.'),('validation_evidence','Verify approved procedure/configuration and reusable evidence; list remaining work.'),('program_commercial','Verify requested timing and downstream ownership.')]],
                missing_information=[],risk_level='low',proposed_workflow='Shared requirement-change standard route.',likely_policy_path='touchless_eligible')
        elif issubclass(agent.output_type,CoordinatorReview):
            output=CoordinatorReview(additional_work=[],disagreements=[],unresolved_questions=[],ready_to_synthesize=True)
        elif agent.output_type is FinalDecisionPackage:
            p=h.state.policy_decision
            change=h.sources.latest('get_change_request')
            output=FinalDecisionPackage(case_id=h.state.case_id,customer_id=h.state.customer_id,program_id=h.state.program_id,
                classified_change_type='standard_validation_package',change_summary='Standard approved-profile package update; exact source policy governs handoff.',
                affected_scope=[],specialist_findings=[SpecialistSynopsis(invocation_id=r.invocation_id,specialist=r.specialist,summary=r.assessment.summary) for r in h.state.completed_assessments],
                confirmed_facts=[fact(h,change,'/id','The source identifies this standard package request.')],evidence_gaps=[],available_options=[],
                relevant_constraints=[],program_impact=[],risks=[],unresolved_questions=list(h.state.unresolved_questions),
                recommended_next_step='Prepare the bounded Validation Operations package; separate lab authorization and standard confirmation work remain required.' if p.policy_path=='touchless_eligible' else 'Request review or clarification: '+' '.join(p.reasons),
                policy_path=p.policy_path,requires_human_review=p.policy_path!='touchless_eligible',escalation_reason=' '.join(p.reasons) if p.policy_path=='escalation_required' else None,
                source_references=list(h.state.source_references),business_actions_executed=False,approval_granted=False,customer_accepted=False,new_validation_pass_claimed=False)
        else:
            self.active+=1;self.peak_active=max(self.active,self.peak_active)
            try:
                await asyncio.sleep(self.delay)
                server=agent.mcp_servers[0]
                await server.call_tool('get_standard_change_context',{'change_id':h.state.event.change_id})
                context_call=next(c for c in reversed(h.sources.calls) if c['invocation_id']==server.invocation_id and c['tool']=='get_standard_change_context')
                context=StandardContext.model_validate(context_call['data'])
                if agent.output_type is ChangeImpactAssessment:
                    await server.call_tool('get_requirement_revision',{'requirement_revision_id':context.request.baseline_requirement_revision_id})
                if agent.output_type is ProgramCommercialAssessment:
                    await server.call_tool('get_program_milestone',{'program_id':context.program_id,'milestone_id':context.change['milestone_id']})
                refs=[r for r in h.state.source_references if r.source_id in h.intake_source_ids|server.seen_sources]
                base=dict(case_id=h.state.case_id,summary='Exact source-backed standard package assessment.',confidence=.95,unresolved_questions=[],source_references=refs)
                if agent.output_type is ChangeImpactAssessment:
                    finding=fact(h,context_call,'/request/summary','The request adds the named profile to the package without changing the approved baseline.')
                    output=ChangeImpactAssessment(**base,change_type='standard_validation_package',requirement_delta=[finding],affected_scope=[finding],confirmed_impacts=[],possible_impacts=[],unaffected_scope=[],missing_information=[])
                elif agent.output_type is StandardValidationAssessment:
                    e=evaluate(context)
                    output=StandardValidationAssessment(**base,context_source_id=context_call['source_id'],applicability_matches=e.touchless_eligible,
                        procedure_id=context.procedure['id'] if context.procedure else None,procedure_content_version=context.procedure['content_version'] if context.procedure else None,
                        reusable_evidence_ids=e.reusable_evidence_ids,remaining_work_ids=[w.work_id for w in e.remaining_work],
                        findings=[fact(h,context_call,'/request/sample_ids','The source nominates samples; remaining lab work is separate from historical evidence.')])
                else:
                    call=next(c for c in reversed(h.sources.calls) if c['invocation_id']==server.invocation_id and c['tool']=='get_program_milestone')
                    ms=call['data']
                    output=ProgramCommercialAssessment(**base,affected_milestones=[MilestoneImpact(milestone_id=ms['id'],source_id=call['source_id'],**{k:ms[k] for k in ('baseline_at','current_forecast_at','forecast_status')})],
                        customer_commitments=[],dependencies=[],schedule_exposure=[],cost_context=[],owners=[fact(h,context_call,'/rule/downstream_owner','The source records downstream ownership.')],risks=[])
            finally:self.active-=1
        return SimpleNamespace(final_output=output)

class StandardInvestigationDouble:
    def __init__(self,config,*,delay=.02):
        self.config,self.delay=config,delay
        self.calls=0;self.harnesses=[]
    async def __call__(self,incoming,run,checkpoint):
        self.calls+=1;set_tracing_disabled(True)
        checkpoint.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
        def save(state):
            temporary=checkpoint.with_suffix('.next');temporary.write_text(json.dumps(state));os.replace(temporary,checkpoint)
        h=CaseHarness(self.config,incoming.event,None,Recorder('trace_'+'1'*32),checkpoint=save,
            case_id=run.case_id,run_id=run.run_id,workflow_id=run.workflow_id,workflow_definition_version=run.definition_version)
        h.runner=StandardModelDouble(h,self.delay);self.harnesses.append(h)
        try:return await h.run()
        finally:
            h.checkpoint()
            (checkpoint.parent/'tool-calls.json').write_text(json.dumps(h.sources.calls))
