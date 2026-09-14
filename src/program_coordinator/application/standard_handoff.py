"""Host-owned bounded handoff through HTTP, reusing invocation/store/locking conventions."""
from enterprise_api.standard_models import StandardContext, StandardIntakeInput, ValidationIntake
from enterprise_api.standard_policy import evaluate, build_package, digest
from .models import WorkflowError, now_utc
from .standard_handoff_models import StandardHandoff
from .execution_models import SourceFailure, SourceReadFailure
from .demo_identity import AUTOMATION, ENGINEER

SCOPE=('CUST-FML01','PRG-A17')

class StandardHandoffService:
    def __init__(self,store,source):
        self.store,self.source=store,source

    def context(self, change_id='CR-019'):
        value=StandardContext.model_validate(self.source.read.get_standard_change_context(change_id))
        if (value.customer_id,value.program_id,value.change_id) != (*SCOPE,'CR-019'):
            raise WorkflowError('STANDARD_SCOPE_MISMATCH')
        return value

    def record(self,run_id):
        with self.store.transaction() as data:
            return data.standard_handoffs.get(run_id)

    def save(self,value,event):
        value.updated_at=now_utc()
        with self.store.transaction(write=True) as data:
            old=data.standard_handoffs.get(value.run_id)
            value.version=old.version+1 if old else 1
            data.standard_handoffs[value.run_id]=value
            self.store._activity(data,data.runs[value.run_id],event,actor=AUTOMATION,
                details={'change_id':value.change_id,'status':value.status,'error_code':value.error_code,
                         'package_id':value.package.package_id if value.package else None,
                         'intake_id':value.intake.id if value.intake else None})
        return value

    def process(self,run,state):
        """Called by the existing host after completed, validated shared-harness analysis."""
        now=now_utc()
        value=StandardHandoff(run_id=run.run_id,case_id=run.case_id,change_id='CR-019',customer_id=run.customer_id,
            program_id=run.program_id,status='review_required',created_at=now,updated_at=now)
        with self.store.execution_lock():
            try:
                context=self.context()
                value.eligibility=evaluate(context)
            except (SourceReadFailure,ValueError,WorkflowError):
                value.status='source_unavailable';value.error_code='STANDARD_SOURCE_UNAVAILABLE'
                value.reasons=['Current source context is unavailable; no handoff is authorized.']
                return self.save(value,'standard_review_required')
            policy=state.policy_decision
            if (state.final_package_status != 'validated' or not state.final_package
                    or state.final_package.classified_change_type != 'standard_validation_package'
                    or not policy or policy.rule != 'standard_touchless_handoff_v1'
                    or policy.policy_path != 'touchless_eligible' or not value.eligibility.touchless_eligible):
                value.reasons=[c.reason for c in value.eligibility.checks if not c.passed] or (policy.reasons if policy else ['Analysis incomplete.'])
                value.error_code='STANDARD_POLICY_INELIGIBLE'
                return self.save(value,'standard_review_required')
            if policy.standard_context_digest != context.context_digest:
                value.error_code='STANDARD_SOURCE_CHANGED'
                value.reasons=['Source context changed after analysis; reassessment is required.']
                return self.save(value,'standard_review_required')
            value.package=build_package(context,run_id=run.run_id,case_id=run.case_id)
            value.action_key='standard_' + digest([value.package.request_id,value.package.request_content_version])[:40]
            value.status='prepared'
            self.save(value,'standard_package_prepared')
            return self._execute(value,context)

    def existing(self,value):
        raw=self.source.read.get_standard_validation_intakes(value.change_id)
        rows=[ValidationIntake.model_validate(i) for i in raw['items']
              if i['request_content_version']==value.package.request_content_version]
        if len(rows)>1:
            raise WorkflowError('MULTIPLE_STANDARD_INTAKES')
        return rows[0] if rows else None

    @staticmethod
    def matches(value,intake):
        package=value.package
        return (intake.package == package and intake.package_digest == digest(package)
            and (intake.customer_id,intake.program_id,intake.change_id)==(value.customer_id,value.program_id,value.change_id)
            and intake.downstream_queue_id==package.downstream_queue_id and intake.downstream_owner==package.downstream_owner
            and intake.status=='received' and intake.package_status=='complete'
            and intake.lab_authorization=='pending' and intake.physical_testing=='not_started' and intake.customer_acceptance=='pending')

    def verify(self,value,intake_id):
        try:
            intake=ValidationIntake.model_validate(self.source.read.get_standard_validation_intake(intake_id))
            value.intake=intake
            if not self.matches(value,intake):
                value.status='verification_failed';value.verification_status='failed';value.error_code='HANDOFF_READBACK_MISMATCH'
                return self.save(value,'standard_verification_failed')
            value.status='handoff_verified';value.verification_status='verified';value.error_code=None
            return self.save(value,'standard_handoff_verified')
        except (SourceReadFailure,ValueError):
            value.status='action_succeeded';value.verification_status='unavailable';value.error_code='HANDOFF_READBACK_UNAVAILABLE'
            return self.save(value,'standard_verification_failed')

    def adopt(self,value,intake,context):
        # A previous run may own the original package provenance. Verify its entire
        # business content against the current source before reusing that record.
        expected=build_package(context,run_id=intake.package.workflow_run_id,case_id=intake.package.workflow_case_id)
        if intake.package != expected or intake.package_digest != digest(expected):
            value.status='verification_failed';value.verification_status='failed';value.error_code='EXISTING_HANDOFF_SCOPE_MISMATCH'
            return self.save(value,'standard_verification_failed')
        value.package=intake.package;value.reused_existing=True;value.action_status='succeeded'
        self.save(value,'standard_handoff_recovered')
        return self.verify(value,intake.id)

    def _execute(self,value,context):
        try:
            prior=self.existing(value)
            if prior:
                return self.adopt(value,prior,context)
        except (SourceReadFailure,ValueError,WorkflowError):
            value.status='source_unavailable';value.error_code='STANDARD_RECONCILIATION_UNAVAILABLE'
            return self.save(value,'standard_verification_failed')
        with self.store.transaction() as data:
            uncertain=next((h for h in data.standard_handoffs.values() if h.run_id!=value.run_id and h.package
                and h.package.request_id==value.package.request_id
                and h.package.request_content_version==value.package.request_content_version
                and h.action_status in {'started','unknown','succeeded'} and h.status!='handoff_verified'),None)
        if uncertain:
            # A new invocation cannot evade an interrupted previous action.
            # Preserve the original intent so later readback can reconcile it.
            value.package=uncertain.package;value.action_key=uncertain.action_key
            value.status='outcome_unknown';value.action_status='unknown';value.error_code='HANDOFF_OUTCOME_UNRESOLVED'
            return self.save(value,'standard_handoff_unknown')
        value.status='action_started';value.action_status='started';value.error_code=None
        self.save(value,'standard_handoff_started')  # Durable before HTTP, including process interruption.
        try:
            receipt=self.source.standard_intake(StandardIntakeInput(package=value.package,expected_context_digest=context.context_digest),value.action_key)
        except SourceFailure as exc:
            value.action_status='unknown' if exc.unknown else 'failed'
            value.status='outcome_unknown' if exc.unknown else 'write_failed'
            value.error_code=str(exc)
            return self.save(value,'standard_handoff_unknown' if exc.unknown else 'standard_handoff_failed')
        value.action_status='succeeded';value.status='action_succeeded'
        self.save(value,'standard_action_succeeded')
        return self.verify(value,receipt.body['id'])

    def recover(self,request,actor,*,retry=False):
        if actor not in (AUTOMATION,ENGINEER):
            raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        actor.require_scope(*SCOPE)
        with self.store.execution_lock():
            value=self.record(request.run_id)
            if not value or (value.customer_id,value.program_id)!=SCOPE:
                raise WorkflowError('STANDARD_HANDOFF_NOT_FOUND')
            if value.version!=request.expected_version:
                raise WorkflowError('STALE_HANDOFF_VERSION')
            if not value.package:
                raise WorkflowError('STANDARD_REASSESSMENT_REQUIRED')
            if value.status=='handoff_verified':
                return value
            # A started/interrupted/unknown action is read-only reconciliation.
            # Never blindly repost merely because a GET did not find a record.
            prior=self.existing(value)
            if prior:
                if prior.package!=value.package:
                    value.status='verification_failed';value.verification_status='failed';value.error_code='HANDOFF_READBACK_MISMATCH'
                    return self.save(value,'standard_verification_failed')
                value.action_status='succeeded';value.reused_existing=True
                self.save(value,'standard_handoff_recovered')
                return self.verify(value,prior.id)
            if value.action_status in {'unknown','started','succeeded'}:
                value.status='outcome_unknown';value.action_status='unknown';value.error_code='HANDOFF_OUTCOME_UNRESOLVED'
                return self.save(value,'standard_handoff_unknown')
            if not retry:
                raise WorkflowError('NO_RECORDED_HANDOFF')
            context=self.context()
            if not evaluate(context).touchless_eligible or context.context_digest!=value.package.context_digest:
                raise WorkflowError('STANDARD_REASSESSMENT_REQUIRED')
            return self._execute(value,context)
