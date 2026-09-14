"""Exact ERP then Planner execution using existing locks, receipts and readback patterns."""
from enterprise_api.delivery_models import DeliveryContext, DeliveryRecords, DeliveryPrepareInput, DeliveryExecuteInput
from enterprise_api.quality_models import RecoveryReviewInput
from enterprise_api.delivery_policy import analyze, plan_digest
from .contracts import digest
from .models import WorkflowError
from .demo_identity import AUTOMATION, PROGRAM_OWNER
from .execution_models import SourceFailure, SourceReadFailure
from .delivery_models import DeliveryProgress, DeliveryStep


class DeliveryCommitmentService:
    def __init__(self,store,source,human):self.store,self.source,self.human=store,source,human
    def context(self):return DeliveryContext.model_validate(self.source.read.get_delivery_context('DR-009'))
    def records(self):return DeliveryRecords.model_validate(self.source.read.get_delivery_records('DR-009'))

    def save(self,p,event,actor=AUTOMATION):
        with self.store.transaction(write=True) as data:
            data.delivery_commitments[p.run_id]=p
            self.store._activity(data,data.runs[p.run_id],event,actor=actor,details={'delivery_id':p.delivery_id,'status':p.status,
                'error_code':p.error_code,'plan_id':p.plan_id,'plan_version':p.plan_version,'plan_digest':p.plan_digest})

    def load(self,run_id):
        with self.store.transaction() as data:
            p=data.delivery_commitments.get(run_id);r=data.runs.get(run_id)
            if not p or not r or (r.customer_id,r.program_id,r.workflow_id)!=('CUST-FML01','PRG-A17','delivery_readiness'):
                raise WorkflowError('DELIVERY_ANALYSIS_REQUIRED')
            return p

    def current(self,p,*,owned=False):
        c=self.context();exact=c.context_digest==p.context_digest
        if owned and c.commitment and p.plan_id:
            plan=next((v for v in self.records().plans if v.id==p.plan_id),None)
            exact=exact or bool(plan and c.commitment.plan_id==p.plan_id and c.commitment.plan_digest==p.plan_digest
                and c.state.record_version==plan.expected_state_version+1 and c.commitment.supersedes_commitment_id==plan.prior_commitment_id)
        if not exact or c.input_digest!=p.input_digest or not analyze(c).proposal_allowed:
            p.status='stale';p.error_code='STALE_SOURCE';self.save(p,'proposal_stale');raise WorkflowError('STALE_SOURCE')
        return c

    def step(self,p,operation,body,method,collection,expected,actor=AUTOMATION):
        fingerprint=digest(body.model_dump(mode='json'));previous=p.steps.get(operation)
        if previous and previous.request_digest!=fingerprint:raise WorkflowError('DELIVERY_ACTION_CHANGED')
        values=[v.model_dump(mode='json') for v in getattr(self.records(),collection)]
        matches=[v for v in values if all(v.get(k)==x for k,x in expected.items())]
        if len(matches)>1:raise WorkflowError('VERIFICATION_MISMATCH')
        if matches:
            if previous and previous.source_id and previous.source_id!=matches[0]['id']:raise WorkflowError('VERIFICATION_MISMATCH')
            p.steps[operation]=DeliveryStep(operation=operation,key=previous.key if previous else 'dr_'+digest([operation,fingerprint])[:40],
                request_digest=fingerprint,status='verified',source_id=matches[0]['id'],request_id=previous.request_id if previous else None)
            p.error_code=None;self.save(p,'source_state_verified',actor);return matches[0]
        if previous and previous.status in {'verified','action_succeeded','verification_failed'}:
            previous.status='verification_failed';p.status='verification_failed';p.error_code='VERIFICATION_MISMATCH'
            self.save(p,'verification_failed',actor);raise WorkflowError('VERIFICATION_MISMATCH')
        self.current(p,owned=operation in ('erp','planner'))
        step=DeliveryStep(operation=operation,key=previous.key if previous else 'dr_'+digest([operation,fingerprint])[:40],request_digest=fingerprint,status='started')
        p.steps[operation]=step;p.status=operation+'_started';self.save(p,'action_started',actor)
        try:
            receipt=method(body,step.key);step.source_id=receipt.body['id'];step.request_id=receipt.request_id;step.status='action_succeeded'
            p.status=operation+'_action_succeeded';self.save(p,'action_record_retained',actor)
        except SourceFailure as exc:
            step.status='outcome_unknown' if exc.unknown else 'failed';step.error_code=str(exc);p.error_code=str(exc)
            p.status='partial_completion' if operation=='planner' and p.steps.get('erp') and p.steps['erp'].status=='verified' else step.status
            self.save(p,'action_outcome_unknown' if exc.unknown else 'action_failed',actor);raise
        try:values=[v.model_dump(mode='json') for v in getattr(self.records(),collection)]
        except SourceReadFailure:
            p.status='verification_failed';p.error_code='SOURCE_READ_FAILED';self.save(p,'verification_failed',actor);raise
        actual=next((v for v in values if v['id']==step.source_id),None)
        if actual is None or any(actual.get(k)!=v for k,v in expected.items()):
            step.status='verification_failed';p.status='verification_failed';p.error_code='VERIFICATION_MISMATCH'
            self.save(p,'verification_failed',actor);raise WorkflowError('VERIFICATION_MISMATCH')
        step.status='verified';p.error_code=None;self.save(p,'source_state_verified',actor);return actual

    def process(self,run,state):
        if (state.workflow_stage!='completed' or state.final_package_status!='validated' or state.event.change_id!='DR-009'
            or state.run_id!=run.run_id or state.case_id!=run.case_id or state.workflow_id!='delivery_readiness'
            or not state.policy_decision or state.policy_decision.rule!='delivery_commitment_v1'):return
        with self.store.execution_lock():
            c=self.context()
            if c.context_digest!=state.policy_decision.delivery_context_digest:raise WorkflowError('STALE_SOURCE')
            from ..delivery import claim
            if state.final_package.delivery!=claim(c):raise WorkflowError('DELIVERY_CLAIM_MISMATCH')
            with self.store.transaction() as data:p=data.delivery_commitments.get(run.run_id)
            p=p or DeliveryProgress(run_id=run.run_id,case_id=run.case_id,delivery_id=c.delivery_id,context_digest=c.context_digest,input_digest=c.input_digest)
            self.save(p,'proposal_retained')
            if not analyze(c).proposal_allowed:
                p.status='readiness_blocked';self.save(p,'execution_denied');return
            # Reassessment reports the current promise; it cannot create another identical commitment.
            if c.commitment and (c.commitment.quantity,c.commitment.committed_at)==(min(c.request.quantity,analyze(c).eligible_quantity),analyze(c).proposed_at):
                p.status='commitment_current';self.save(p,'source_state_verified');return
            try:self.prepare(p)
            except (SourceFailure,SourceReadFailure,WorkflowError):
                if p.status not in {'outcome_unknown','failed','verification_failed','stale'}:
                    p.status='failed';p.error_code='DELIVERY_PREPARATION_FAILED';self.save(p,'action_failed')

    def prepare(self,p):
        c=self.current(p);a=analyze(c);o=next(o for o in a.options if o.id=='partial_commitment' and o.executable)
        body=DeliveryPrepareInput(delivery_id=c.delivery_id,expected_context_digest=c.context_digest,workflow_run_id=p.run_id,workflow_case_id=p.case_id)
        plan=self.step(p,'prepare',body,self.source.delivery_prepare,'plans',dict(delivery_id=c.delivery_id,order_id=c.request.order_id,line_id=c.request.line_id,
            milestone_id=c.request.milestone_id,context_digest=c.context_digest,input_digest=c.input_digest,expected_state_version=c.state.record_version,
            prior_commitment_id=c.state.current_commitment_id,analysis=a.model_dump(mode='json'),quantity=o.quantity,committed_at=o.proposed_at,
            selected_option='partial_commitment',date_semantics=c.request.date_semantics,destination=c.request.destination,owner=c.request.commitment_owner,
            required_role='program_owner',permitted_actions=['record_delivery_commitment','link_delivery_plan'],allocation_changed=False))
        if plan_digest(plan)!=plan['plan_digest']:raise WorkflowError('VERIFICATION_MISMATCH')
        p.plan_id,p.plan_version,p.plan_digest=plan['id'],plan['plan_version'],plan['plan_digest'];p.status='awaiting_review';self.save(p,'approval_requested');return p

    def exact(self,request,*,owned=False):
        p=self.load(request.run_id)
        if (request.plan_id,request.plan_version,request.plan_digest)!=(p.plan_id,p.plan_version,p.plan_digest):raise WorkflowError('STALE_PLAN')
        self.current(p,owned=owned)
        plan=next((v for v in self.records().plans if v.id==p.plan_id),None)
        if not plan or (plan.plan_version,plan.plan_digest)!=(p.plan_version,p.plan_digest) or plan_digest(plan.model_dump(mode='json'))!=p.plan_digest:raise WorkflowError('VERIFICATION_MISMATCH')
        return p,plan

    def review(self,request,actor):
        if actor is not PROGRAM_OWNER:raise WorkflowError('WRONG_APPROVER')
        with self.store.execution_lock():
            p,plan=self.exact(request)
            if p.decision and (request.decision,request.comment)!=(p.decision,p.decision_comment):raise WorkflowError('DECISION_CONFLICT')
            p.decision,p.decision_comment=request.decision,request.comment
            body=RecoveryReviewInput(plan_id=p.plan_id,expected_plan_version=p.plan_version,expected_plan_digest=p.plan_digest,decision=request.decision,comment=request.comment)
            self.step(p,'review',body,lambda b,k:self.human.delivery_decide(b,k,actor),'decisions',dict(delivery_id=p.delivery_id,plan_id=p.plan_id,
                plan_version=p.plan_version,plan_digest=p.plan_digest,context_digest=p.context_digest,decision=request.decision,signer_identity=actor.actor_id,signer_role=actor.role,comment=request.comment),actor)
            p.status='approved' if request.decision=='approve' else 'rejected';self.save(p,'proposal_approved' if request.decision=='approve' else 'proposal_rejected',actor);return p

    def execute(self,request,actor):
        if actor is not AUTOMATION:raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        with self.store.execution_lock():
            p,plan=self.exact(request,owned=True);c=self.context()
            decision=next((d for d in self.records().decisions if d.plan_id==plan.id),None)
            if not decision or decision.decision!='approve' or decision.signer_role!='program_owner' or decision.signer_identity!=PROGRAM_OWNER.actor_id:raise WorkflowError('APPROVAL_REQUIRED')
            body=DeliveryExecuteInput(plan_id=plan.id,decision_id=decision.id,expected_plan_digest=plan.plan_digest)
            commitment=self.step(p,'erp',body,self.source.delivery_commit,'commitments',dict(delivery_id=p.delivery_id,order_id=plan.order_id,line_id=plan.line_id,
                plan_id=plan.id,decision_id=decision.id,plan_digest=plan.plan_digest,quantity=plan.quantity,committed_at=plan.committed_at,date_semantics=plan.date_semantics,
                destination=plan.destination,remaining_uncommitted_quantity=plan.analysis.requested_quantity-plan.quantity,status='authorized_commitment',allocation_changed=False,
                delivered_quantity=0,customer_agreement=c.request.customer_agreement,supersedes_commitment_id=plan.prior_commitment_id))
            self.current(p,owned=True)
            self.step(p,'planner',body,self.source.delivery_link,'links',dict(delivery_id=p.delivery_id,order_id=plan.order_id,milestone_id=plan.milestone_id,
                plan_id=plan.id,decision_id=decision.id,commitment_id=commitment['id'],plan_digest=plan.plan_digest,quantity=plan.quantity,committed_at=plan.committed_at,
                date_semantics=plan.date_semantics,remaining_uncommitted_quantity=commitment['remaining_uncommitted_quantity'],owner=plan.owner,
                status='commitment_linked_pending_fulfillment',customer_agreement=c.request.customer_agreement,shipment_completed=False))
            self.current(p,owned=True);p.status='verified';p.error_code=None;self.save(p,'execution_completed');return p

    def reconcile(self,run_id,actor):
        if actor is not AUTOMATION:raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        with self.store.execution_lock():
            p=self.load(run_id)
            if p.decision is not None:raise WorkflowError('REPEAT_EXACT_REVIEW_OR_EXECUTE')
            return self.prepare(p)
