"""Scripted QE-011 presentation with real CaseHarness and scoped MCP/HTTP reads.

The reusable quality script also supports offline verification. Only
ScriptedOpening is installed in the live host; it rejects every other case.
"""
import asyncio,json,os
from types import SimpleNamespace
from agents.tracing import trace
from program_coordinator.harness import CaseHarness
from program_coordinator.models import TriageDecision,CoordinatorReview,FinalDecisionPackage,WorkRequest,SpecialistSynopsis,QualityAssessment
from program_coordinator.quality import claim,recovery_recommendation
from program_investigator.telemetry import Recorder
from enterprise_api.quality_models import QualityContext
from program_coordinator.models import Finding, SourceFact
from program_coordinator.sources import pointer

def fact(h, call, path, statement):
    sid = call['source_id']
    return Finding(statement=statement, basis='fact', source_refs=[sid],
        facts=[SourceFact(source_id=sid, pointer=path, value_json=json.dumps(pointer(call['data'],path)))])

# Explicit presentation timing for the offline opening, not model latency.
# Parallel specialists share the 84-second stage: 12 + 84 + 12 + 12 = 120 seconds.
OPENING_PHASE_SECONDS = {'triage':12, 'specialist':84, 'reconcile':12, 'synthesis':12}

class QualityModelDouble:
    def __init__(self,h,delay=.02,*,pace_opening=False,pacing_sleep=asyncio.sleep):
        self.h,self.delay=h,delay;self.active=0;self.peak_active=0
        self.pace_opening=pace_opening and h.state.event.change_id=='QE-011'
        self.pacing_sleep=pacing_sleep
        self.phases=[]
    async def __call__(self,agent,prompt,**kwargs):
        h=self.h
        phase=kwargs['hooks'].phase
        self.phases.append((kwargs['hooks'].role,phase))
        if self.pace_opening:
            await self.pacing_sleep(OPENING_PHASE_SECONDS[phase])
        if issubclass(agent.output_type,TriageDecision):
            work=[('manufacturing','Verify signal, lot, baseline comparison and material hold.'),
                  ('validation_evidence','Verify historical evidence and approved investigation procedure; preserve unresolved cause.'),
                  ('program_commercial','Verify milestone demand, eligible supply and recovery options.')]
            if h.state.event.change_id=='QE-011':
                work.insert(0,('change_impact','Verify the affected Engineering configuration and approved procedure scope; identify whether any technical change is requested.'))
            out=TriageDecision(classified_change_type='quality_exception',confidence=.95,rationale='Validate source quality signal and eligible supply.',
                specialists_required=[WorkRequest(specialist=r,question=q,rationale='Establish source facts and bounded authority.',focus_record_ids=[h.state.event.change_id],depends_on=[]) for r,q in work],
                missing_information=[],risk_level='high',proposed_workflow='Connected quality recovery.',likely_policy_path='human_review_required')
        elif issubclass(agent.output_type,CoordinatorReview):
            out=CoordinatorReview(additional_work=[],disagreements=[],unresolved_questions=[],ready_to_synthesize=True)
        elif agent.output_type is FinalDecisionPackage:
            c=h.sources.latest('get_quality_context');context=QualityContext.model_validate(c['data']);p=h.state.policy_decision
            out=FinalDecisionPackage(case_id=h.state.case_id,customer_id=h.state.customer_id,program_id=h.state.program_id,
                classified_change_type='quality_exception',quality=claim(context),change_summary='Quality exception scoped; site concentration is correlation; cause remains unresolved.',
                affected_scope=[],specialist_findings=[SpecialistSynopsis(invocation_id=r.invocation_id,specialist=r.specialist,summary=r.assessment.summary) for r in h.state.completed_assessments],
                confirmed_facts=[fact(h,c,'/analysis/eligible_quantity','The calculator excludes held material from eligible supply.')],evidence_gaps=[],available_options=[],
                relevant_constraints=[],program_impact=[],risks=[],unresolved_questions=list(h.state.unresolved_questions),recommended_next_step='Route and verify the approved standard investigation.' if p.policy_path=='touchless_eligible' else recovery_recommendation(context),
                policy_path=p.policy_path,requires_human_review=p.policy_path!='touchless_eligible',escalation_reason=' '.join(p.reasons) if p.policy_path=='escalation_required' else None,
                source_references=list(h.state.source_references),business_actions_executed=False,approval_granted=False,customer_accepted=False,new_validation_pass_claimed=False)
        else:
            self.active+=1;self.peak_active=max(self.peak_active,self.active)
            try:
                if not self.pace_opening:await asyncio.sleep(self.delay)
                server=agent.mcp_servers[0]
                c=h.intake['quality'];context=QualityContext.model_validate(c['data'])
                if server.role=='manufacturing':
                    for material in context.material:
                        await server.call_tool('get_manufacturing_lot',{'lot_id':material.lot_id})
                elif server.role=='change_impact':
                    await server.call_tool('get_configuration',{'configuration_id':context.exception.configuration_id})
                elif server.role=='validation_evidence':
                    await server.call_tool('get_configuration',{'configuration_id':context.exception.configuration_id})
                    for evidence in context.evidence:
                        await server.call_tool('get_validation_result',{'result_id':evidence['id']})
                else:
                    await server.call_tool('get_program_milestone',{'program_id':context.program_id,'milestone_id':context.exception.milestone_id})
                    await server.call_tool('get_customer_order',{'order_id':context.exception.order_id})
                findings=[fact(h,c,'/observation/root_cause','The source has no established root cause.'),
                          fact(h,c,'/analysis/gap_quantity','The calculator records current supply exposure.')]
                summary='Source-grounded comparison, procedure and supply assessment; cause remains unresolved.'
                if server.role=='change_impact':
                    configuration=h.sources.latest('get_configuration',configuration_id=context.exception.configuration_id)
                    findings=[fact(h,configuration,'/id','Engineering identifies the affected configuration.'),
                              fact(h,c,'/exception/investigation_procedure_id','The exception names the approved investigation procedure.'),
                              fact(h,c,'/exception/requested_actions','Requested work is limited to standard investigation routing.')]
                    summary='Affected Engineering configuration and procedure scope checked; no technical change or new acceptance criteria authorized.'
                out=QualityAssessment(case_id=h.state.case_id,summary=summary,confidence=.95,
                    unresolved_questions=['Quality disposition and physical cause remain unresolved.'],source_references=[r for r in h.state.source_references if r.source_id in h.intake_source_ids|server.seen_sources],
                    context_source_id=c['source_id'],quality=claim(context),findings=findings)
            finally:self.active-=1
        return SimpleNamespace(final_output=out)

class QualityInvestigationDouble:
    def __init__(self,config,delay=.02,*,pace_opening=False,pacing_sleep=asyncio.sleep):
        self.config,self.delay=config,delay;self.harnesses=[];self.calls=0;self.pace_opening=pace_opening
        self.retain_harnesses = True
        self.pacing_sleep=pacing_sleep
    async def __call__(self,incoming,run,checkpoint):
        self.calls+=1;checkpoint.parent.mkdir(parents=True,exist_ok=True)
        def save(state):
            temp=checkpoint.with_suffix('.next');temp.write_text(json.dumps(state));os.replace(temp,checkpoint)
        h=CaseHarness(self.config,incoming.event,None,Recorder('trace_'+run.run_id.removeprefix('run_')),checkpoint=save,case_id=run.case_id,run_id=run.run_id,workflow_id=run.workflow_id,workflow_definition_version=run.definition_version)
        h.runner=QualityModelDouble(h,self.delay,pace_opening=self.pace_opening,pacing_sleep=self.pacing_sleep)
        if h.runner.pace_opening:h.state.demo_pacing_min_seconds=sum(OPENING_PHASE_SECONDS.values())
        if self.retain_harnesses:self.harnesses.append(h)
        try:
            # Context-local suppression: never disable a concurrent live run.
            with trace('Scripted quality demo', disabled=True):
                return await h.run()
        finally:
            h.checkpoint()
            (checkpoint.parent/'tool-calls.json').write_text(json.dumps(h.sources.calls))


class ScriptedOpening(QualityInvestigationDouble):
    def __init__(self, config):
        super().__init__(config, pace_opening=True)
        self.retain_harnesses = False

    async def __call__(self, incoming, run, checkpoint):
        if incoming.event.change_id != 'QE-011':
            raise ValueError('SCRIPTED_OPENING_SCOPE_REQUIRED')
        return await super().__call__(incoming, run, checkpoint)
