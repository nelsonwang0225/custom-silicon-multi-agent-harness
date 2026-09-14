"""Bounded quality adapter sharing Phase 06 locks, receipts and source boundaries.

The existing WorkflowService/CaseHarness performs all agent orchestration. This
service routes a source-defined investigation and exact human-approved Planner
metadata only. No agent receives a mutation capability.
"""
from enterprise_api.quality_models import QualityContext, QualityRecords, QualityIntent, RecoveryReviewInput, RecoveryExecuteInput
from enterprise_api.quality_policy import analyze, plan_digest, standard_investigation_policy, recovery_workstreams, STANDARD_QUALITY_ROUTE
from .contracts import digest
from .models import WorkflowError, now_utc
from .demo_identity import AUTOMATION, PROGRAM_OWNER
from .execution_models import SourceFailure, SourceReadFailure
from .quality_recovery_models import QualityProgress, QualityStep


class QualityRecoveryService:
    def __init__(self,store,source,human):self.store,self.source,self.human=store,source,human

    def context(self, exception_id='QE-004'):
        if exception_id not in {'QE-004','QE-011'}:raise WorkflowError('CASE_SCOPE_MISMATCH')
        return QualityContext.model_validate(self.source.read.get_quality_context(exception_id))
    def records(self, exception_id='QE-004'):
        if exception_id not in {'QE-004','QE-011'}:raise WorkflowError('CASE_SCOPE_MISMATCH')
        return QualityRecords.model_validate(self.source.read.get_quality_records(exception_id))

    def save(self,p,event,actor=AUTOMATION):
        with self.store.transaction(write=True) as data:
            data.quality_recoveries[p.run_id]=p
            self.store._activity(data,data.runs[p.run_id],event,actor=actor,
                details={'exception_id':p.exception_id,'status':p.status,'error_code':p.error_code,
                         'plan_id':p.plan_id,'plan_version':p.plan_version,'plan_digest':p.plan_digest})

    def load(self,run_id):
        with self.store.transaction() as data:
            p=data.quality_recoveries.get(run_id)
            if not p:raise WorkflowError('QUALITY_ANALYSIS_REQUIRED')
            run=data.runs.get(run_id)
            if not run or (run.customer_id,run.program_id,run.workflow_id)!=('CUST-FML01','PRG-A17','yield_exception_recovery'):
                raise WorkflowError('CASE_SCOPE_MISMATCH')
            if data.cases[run.case_id].change_id != p.exception_id:
                raise WorkflowError('CASE_SCOPE_MISMATCH')
            return p

    def current(self,p):
        c=self.context(p.exception_id)
        if c.context_digest!=p.context_digest or not analyze(c).investigation_allowed:
            p.status='stale';p.error_code='STALE_SOURCE';self.save(p,'proposal_stale')
            raise WorkflowError('STALE_SOURCE')
        if p.policy_route == STANDARD_QUALITY_ROUTE and standard_investigation_policy(c):
            p.status='review_required';p.error_code='QUALITY_POLICY_INELIGIBLE'
            p.policy_reasons=standard_investigation_policy(c);self.save(p,'policy_escalated')
            raise WorkflowError('QUALITY_POLICY_INELIGIBLE')
        return c

    def step(self,p,operation,body,method,collection,expected,actor=AUTOMATION):
        """Persist before HTTP; always read back before uncertain retry. No new key."""
        fingerprint=digest(body.model_dump(mode='json'))
        previous=p.steps.get(operation)
        if previous and previous.request_digest!=fingerprint:raise WorkflowError('QUALITY_ACTION_CHANGED')
        values=[v.model_dump(mode='json') for v in getattr(self.records(p.exception_id),collection)]
        matches=[v for v in values if all(v.get(k)==value for k,value in expected.items())]
        if len(matches)>1:raise WorkflowError('VERIFICATION_MISMATCH')
        if matches:
            if previous and previous.source_id and matches[0]['id']!=previous.source_id:
                raise WorkflowError('VERIFICATION_MISMATCH')
            p.steps[operation]=QualityStep(operation=operation,key=previous.key if previous else 'qe_'+digest([operation,fingerprint])[:40],
                request_digest=fingerprint,status='verified',source_id=matches[0]['id'],request_id=previous.request_id if previous else None)
            p.error_code=None;self.save(p,'source_state_verified',actor)
            return matches[0]
        if previous and previous.status in {'verified','action_succeeded','verification_failed'}:
            p.status='verification_failed';p.error_code='VERIFICATION_MISMATCH';previous.status='verification_failed'
            self.save(p,'verification_failed',actor);raise WorkflowError('VERIFICATION_MISMATCH')
        self.current(p)
        step=QualityStep(operation=operation,key=previous.key if previous else 'qe_'+digest([operation,fingerprint])[:40],request_digest=fingerprint,status='started')
        p.steps[operation]=step;p.status=operation+'_started';self.save(p,'action_started',actor)
        try:
            receipt=method(body,step.key)
            step.source_id=receipt.body['id'];step.request_id=receipt.request_id;step.status='action_succeeded'
            p.status=operation+'_action_succeeded';self.save(p,'action_record_retained',actor)
        except SourceFailure as exc:
            step.status='outcome_unknown' if exc.unknown else 'failed';step.error_code=str(exc)
            p.status=step.status;p.error_code=str(exc)
            self.save(p,'action_outcome_unknown' if exc.unknown else 'action_failed',actor)
            raise
        try:
            values=[v.model_dump(mode='json') for v in getattr(self.records(p.exception_id),collection)]
        except SourceReadFailure:
            p.status='verification_failed';p.error_code='SOURCE_READ_FAILED';self.save(p,'verification_failed',actor);raise
        actual=next((v for v in values if v['id']==step.source_id),None)
        if actual is None or any(actual.get(k)!=v for k,v in expected.items()):
            step.status='verification_failed';p.status='verification_failed';p.error_code='VERIFICATION_MISMATCH'
            self.save(p,'verification_failed',actor);raise WorkflowError('VERIFICATION_MISMATCH')
        step.status='verified';p.error_code=None;self.save(p,'source_state_verified',actor)
        return actual

    def process(self,run,state):
        if (state.workflow_stage!='completed' or state.final_package_status!='validated' or state.event.change_id not in {'QE-004','QE-011'}
            or state.run_id!=run.run_id or state.case_id!=run.case_id or state.workflow_id!='yield_exception_recovery'
            or not state.policy_decision or state.policy_decision.rule not in {'quality_recovery_v1', STANDARD_QUALITY_ROUTE}):
            return
        with self.store.execution_lock():
            c=self.context(state.event.change_id)
            if c.context_digest!=state.policy_decision.quality_context_digest:raise WorkflowError('STALE_SOURCE')
            from ..quality import claim
            if state.final_package.quality!=claim(c):raise WorkflowError('QUALITY_CLAIM_MISMATCH')
            with self.store.transaction() as data:p=data.quality_recoveries.get(run.run_id)
            p=p or QualityProgress(run_id=run.run_id,case_id=run.case_id,exception_id=c.exception_id,context_digest=c.context_digest)
            if c.exception_id == 'QE-011':
                p.policy_route=STANDARD_QUALITY_ROUTE
                p.policy_reasons=standard_investigation_policy(c)
                if p.policy_reasons or state.policy_decision.policy_path != 'touchless_eligible':
                    p.status='review_required';p.error_code='QUALITY_POLICY_INELIGIBLE'
                    self.save(p,'policy_escalated');return
            elif state.policy_decision.policy_path != 'human_review_required':
                return
            self.save(p,'quality_policy_confirmed' if p.policy_route==STANDARD_QUALITY_ROUTE else 'proposal_retained')
            try:self.prepare(p)
            except (SourceFailure,SourceReadFailure,WorkflowError):
                # The validated analysis remains available; handoff failure stays explicit.
                if p.status not in {'outcome_unknown','failed','verification_failed','stale'}:
                    p.status='failed';p.error_code='QUALITY_HANDOFF_FAILED';self.save(p,'action_failed')

    def prepare(self,p):
        c=self.current(p);body=QualityIntent(exception_id=c.exception_id,expected_context_digest=c.context_digest,workflow_run_id=p.run_id,workflow_case_id=p.case_id)
        i=self.step(p,'investigate',body,self.source.quality_investigate,'investigations',dict(exception_id=c.exception_id,lot_id=c.exception.lot_id,
            observation_id=c.observation.id,test_program_version=c.observation.test_program_version,context_digest=c.context_digest,
            queue_id=c.procedure.queue_id,owner=c.procedure.owner,tasks=c.procedure.tasks,evidence_ids=[e['id'] for e in c.evidence],status='routed',
            **(dict(workflow_run_id=p.run_id,workflow_case_id=p.case_id) if p.policy_route==STANDARD_QUALITY_ROUTE else {})))
        if p.policy_route == STANDARD_QUALITY_ROUTE:
            self.current(p) # Independent context read verifies protected source facts.
            p.status='handoff_verified';p.error_code=None;self.save(p,'execution_completed')
            return p
        plan=self.step(p,'prepare',body,self.source.quality_prepare,'plans',dict(exception_id=c.exception_id,lot_id=c.exception.lot_id,
            milestone_id=c.exception.milestone_id,order_id=c.exception.order_id,investigation_id=i['id'],context_digest=c.context_digest,
            analysis=analyze(c).model_dump(mode='json'),required_role='program_owner',permitted_action='record_recovery_task',recovery_owner=c.procedure.recovery_owner,
            workstreams=[item.model_dump(mode='json') for item in recovery_workstreams(c)]))
        if plan_digest(plan)!=plan['plan_digest']:raise WorkflowError('VERIFICATION_MISMATCH')
        p.plan_id,p.plan_version,p.plan_digest=plan['id'],plan['plan_version'],plan['plan_digest']
        p.status='draft_ready';self.save(p,'proposal_created')
        return p

    def exact(self,request):
        p=self.load(request.run_id)
        if (request.plan_id,request.plan_version,request.plan_digest)!=(p.plan_id,p.plan_version,p.plan_digest):raise WorkflowError('STALE_PLAN')
        self.current(p)
        plan=next((v for v in self.records(p.exception_id).plans if v.id==p.plan_id),None)
        if not plan or plan.plan_digest!=p.plan_digest or plan.plan_version!=p.plan_version or plan_digest(plan.model_dump(mode='json'))!=p.plan_digest:
            raise WorkflowError('VERIFICATION_MISMATCH')
        return p,plan

    def submit(self,request,actor):
        if actor is not AUTOMATION:raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        with self.store.execution_lock():
            p,_=self.exact(request)
            values={
                'submission_id':request.submission_id,
                'submission_subject':request.subject.strip(),
                'submitted_recommendation':request.recommendation.strip(),
                'submitted_business_context':request.business_context.strip(),
                'operator_notes':request.operator_notes.strip(),
            }
            submission_digest=digest(values)
            if p.submission_id:
                existing={k:getattr(p,k) for k in values}
                if existing!=values or p.submission_digest!=submission_digest:
                    raise WorkflowError('ESCALATION_ID_CONFLICT')
                return p
            if p.decision is not None:raise WorkflowError('REPEAT_EXACT_REVIEW_OR_EXECUTE')
            for key,value in values.items():setattr(p,key,value)
            p.submission_digest=submission_digest;p.submitted_by=actor.actor_id;p.submitted_at=now_utc()
            p.status='awaiting_review';self.save(p,'approval_requested',actor)
            return p

    def review(self,request,actor):
        if actor is not PROGRAM_OWNER:raise WorkflowError('WRONG_APPROVER')
        with self.store.execution_lock():
            p,plan=self.exact(request)
            if not p.submission_id or not p.submitted_at:raise WorkflowError('OPERATOR_ESCALATION_REQUIRED')
            if p.decision and (request.decision,request.comment)!=(p.decision,p.decision_comment):raise WorkflowError('DECISION_CONFLICT')
            p.decision,p.decision_comment=request.decision,request.comment
            body=RecoveryReviewInput(plan_id=p.plan_id,expected_plan_version=p.plan_version,expected_plan_digest=p.plan_digest,
                decision=request.decision,comment=request.comment,submission_digest=p.submission_digest,
                recommendation=p.submitted_recommendation,business_context=p.submitted_business_context)
            self.step(p,'review',body,lambda b,k:self.human.quality_decide(b,k,actor),'decisions',dict(exception_id=p.exception_id,plan_id=p.plan_id,
                plan_version=p.plan_version,plan_digest=p.plan_digest,context_digest=p.context_digest,decision=request.decision,
                signer_identity=actor.actor_id,signer_role=actor.role,comment=request.comment,submission_digest=p.submission_digest,
                recommendation=p.submitted_recommendation,business_context=p.submitted_business_context),actor)
            p.status='approved' if request.decision=='approve' else 'rejected';self.save(p,'proposal_approved' if request.decision=='approve' else 'proposal_rejected',actor)
            return p

    def execute(self,request,actor):
        if actor is not AUTOMATION:raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        with self.store.execution_lock():
            p,plan=self.exact(request)
            decision=next((d for d in self.records(p.exception_id).decisions if d.plan_id==plan.id),None)
            if not decision or decision.decision!='approve' or decision.signer_role!='program_owner':raise WorkflowError('APPROVAL_REQUIRED')
            body=RecoveryExecuteInput(plan_id=plan.id,decision_id=decision.id,expected_plan_digest=plan.plan_digest,
                expected_submission_digest=decision.submission_digest)
            self.step(p,'execute',body,self.source.quality_execute,'tasks',dict(exception_id=p.exception_id,lot_id=plan.lot_id,milestone_id=plan.milestone_id,
                plan_id=plan.id,decision_id=decision.id,plan_digest=plan.plan_digest,owner=plan.recovery_owner,status='recovery_plan_recorded',
                eligible_quantity=plan.analysis.eligible_quantity,gap_quantity=plan.analysis.gap_quantity,
                submission_digest=decision.submission_digest,approved_recommendation=decision.recommendation,
                business_context=decision.business_context,workstreams=[item.model_dump(mode='json') for item in plan.workstreams],
                allocation_changed=False,commitment_changed=False,lot_released=False))
            self.current(p) # Independent source read also verifies protected inputs stayed unchanged.
            p.status='verified';p.error_code=None;self.save(p,'execution_completed')
            return p

    def reconcile(self,run_id,actor):
        if actor is not AUTOMATION:raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        with self.store.execution_lock():
            p=self.load(run_id)
            if p.decision is not None:raise WorkflowError('REPEAT_EXACT_REVIEW_OR_EXECUTE')
            return self.prepare(p)
