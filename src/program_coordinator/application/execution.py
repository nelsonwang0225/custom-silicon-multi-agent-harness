"""Governed continuation of a completed SDK investigation, with durable host pause.

The service owns all mutations. There is no agent write tool or second agent loop.
Source systems remain the final authority inside their individual transactions.
"""
from copy import deepcopy
from uuid import uuid4

from mock_enterprise.schemas import PlanInput, PlanView, Plan, Decision, DecisionInput, Milestone
from .contracts import Origin, DecisionBinding, VerificationRecord, proposal_from_plan, digest
from .execution_models import Preparation, ProposalRef, HumanReview, ExecutionRecord, ExecutionStep, ExecutionAttempt
from .execution_policy import executable_proposal, manifest_for, exact_request, verify_job, verify_link
from .models import WorkflowError, now_utc
from .demo_identity import AUTOMATION, ENGINEER, READER
from .execution_models import SourceFailure, SourceReadFailure
from ..models import SourceReference


def reference(proposal):
    return ProposalRef(**proposal.origin.model_dump(), proposal_id=proposal.proposal_id,
                       proposal_version=proposal.proposal_version, proposal_digest=proposal.proposal_digest)


def proposal_key(ref):
    return f'{ref.proposal_id}:{ref.proposal_version}'


class ExecutionService:
    def __init__(self, store, source):
        self.store, self.source = store, source

    @staticmethod
    def actor(actor, required=None):
        if not any(actor is trusted for trusted in (AUTOMATION, ENGINEER, READER)):
            raise WorkflowError('UNTRUSTED_ACTOR_CONTEXT')
        if required is not None and actor is not required:
            raise WorkflowError('WRONG_APPROVER' if required is ENGINEER else 'EXECUTION_ROLE_FORBIDDEN')

    def _load(self, ref, actor):
        self.actor(actor)
        ref = ProposalRef.model_validate_json(ref.model_dump_json())
        actor.require_scope(ref.customer_id, ref.program_id)
        with self.store.transaction() as data:
            p = data.proposals.get(proposal_key(ref))
            if not p or reference(p) != ref:
                raise WorkflowError('PROPOSAL_REFERENCE_MISMATCH')
            executable_proposal(p)
            run = data.runs.get(p.origin.run_id)
            case = data.cases.get(p.origin.case_id)
            if (not run or Origin.from_run(run) != p.origin or not case or case.change_id != 'CR-017'
                    or (case.customer_id, case.program_id) != (p.origin.customer_id, p.origin.program_id)):
                raise WorkflowError('PROPOSAL_SCOPE_MISMATCH')
            record = data.executions.get(proposal_key(ref))
            if not record or record.reference != ref:
                raise WorkflowError('EXECUTION_NOT_FOUND')
            return p, record

    def inspect(self, ref, actor=READER):
        p, record = self._load(ref, actor)
        with self.store.transaction() as data:
            return {'proposal': p.model_dump(mode='json'), 'execution': record.model_dump(mode='json'),
                'review': data.reviews[record.review_id].model_dump(mode='json') if record.review_id else None,
                'attempts': [a.model_dump(mode='json') for a in data.execution_attempts if a.reference == ref],
                'verification': [v.model_dump(mode='json') for v in data.verifications.values() if v.action_id in {s.action_id for s in record.steps}],
                'activity': [e.model_dump(mode='json') for e in data.activity if e.proposal_id == p.proposal_id]}

    def _save(self, p, record, event=None, *, actor=AUTOMATION, action_id=None, details=None):
        with self.store.transaction(write=True) as data:
            data.executions[proposal_key(record.reference)] = record
            if event:
                self.store._activity(data, data.runs[p.origin.run_id], event, actor=actor,
                    proposal_id=p.proposal_id, action_id=action_id, details=details or {})

    def _deny(self, ref, actor, code):
        # Persist scoped denials without trusting a supplied role or exception prose.
        if not any(actor is trusted for trusted in (AUTOMATION, ENGINEER, READER)):
            return
        with self.store.transaction(write=True) as data:
            p = data.proposals.get(proposal_key(ref))
            if p and (p.origin.customer_id, p.origin.program_id) in actor.scopes:
                self.store._activity(data, data.runs[p.origin.run_id], 'execution_denied', actor=actor,
                    proposal_id=p.proposal_id, details={'error_code': code})

    def prepare(self, run_id, preparation_id, actor=AUTOMATION, *, slot_id=None, sample_id=None, supersedes=None):
        """Create an exact source draft from a validated, persisted recommendation.

        No ranked option exists in FinalDecisionPackage. The host selects the least
        cost on-time eligible option (then earliest review, then IDs), or an explicit
        slot/sample pair present in that package. It never parses prose as authority.
        """
        self.actor(actor, AUTOMATION)
        with self.store.execution_lock():
            with self.store.transaction() as data:
                run = data.runs.get(run_id)
                if (not run or run.status != 'completed' or not run.recommendation
                        or run.workflow_id != 'requirement_change_analysis' or run.definition_version != 1
                        or (run.customer_id, run.program_id) != ('CUST-FML01', 'PRG-A17')
                        or data.cases[run.case_id].change_id != 'CR-017' or not data.cases[run.case_id].scope_verified
                        or run.recommendation.policy_path != 'human_review_required'):
                    raise WorkflowError('ANALYSIS_NOT_EXECUTABLE')
                prior = data.preparations.get(preparation_id)
                if prior and (prior.origin != Origin.from_run(run)
                        or (slot_id and slot_id != prior.request.slot_id) or (sample_id and sample_id != prior.request.sample_id)
                        or prior.supersedes_key != (proposal_key(supersedes) if supersedes else None)):
                    raise WorkflowError('PREPARATION_ID_CONFLICT')
                if prior and prior.proposal_key:
                    return data.proposals[prior.proposal_key]
                active = [p for key, p in data.proposals.items() if p.origin.case_id == run.case_id
                          and key in data.executions and data.executions[key].status != 'superseded']
            previous = None
            if supersedes:
                previous, old_record = self._load(supersedes, actor)
                if previous.origin.case_id != run.case_id:
                    raise WorkflowError('PROPOSAL_SCOPE_MISMATCH')
                if old_record.status == 'superseded':
                    raise WorkflowError('PROPOSAL_NOT_CURRENT')
                if any(s.status != 'not_attempted' for s in old_record.steps):
                    raise WorkflowError('PARTIAL_EXECUTION_REQUIRES_RECONCILIATION')
            elif active and not prior:
                raise WorkflowError('CURRENT_PROPOSAL_EXISTS')
            if prior is None:
                change = self.source.read.get_change_request('CR-017')
                options = self.source.read.get_validation_options('CR-017')['items']
                if self.source.read.get_validation_coverage('CR-017')['coverage_satisfied']:
                    raise WorkflowError('ANALYSIS_STALE')
                candidates = [o for o in run.recommendation.available_options if o.eligible
                              and (slot_id is None or o.slot_id == slot_id) and (sample_id is None or o.sample_id == sample_id)]
                if not candidates:
                    raise WorkflowError('NO_APPROVABLE_RECOMMENDED_OPTION')
                selected = min(candidates, key=lambda o: (o.cost_cents, o.timing.review_ready_at, o.slot_id, o.sample_id))
                option = next((o for o in options if o['slot']['id'] == selected.slot_id and o['sample']['id'] == selected.sample_id), None)
                if not option or not all(option[x] for x in ('resource_eligible', 'approval_eligible', 'meets_deadline')):
                    raise WorkflowError('OPTION_NO_LONGER_ELIGIBLE')
                for field in ('configuration_id', 'procedure_id', 'policy_id', 'milestone_id', 'cost_cents', 'currency', 'unit_id', 'lot_id'):
                    if option[field] != getattr(selected, field):
                        raise WorkflowError('ANALYSIS_STALE')
                if option['timing'] != selected.timing.model_dump(mode='json') or option['rate']['id'] != selected.rate_id:
                    raise WorkflowError('ANALYSIS_STALE')
                current_versions = {v['resource_id']: v['content_version'] for v in option['expected_source_versions']['records']}
                if any(r.record_id in current_versions and r.content_version is not None
                       and current_versions[r.record_id] != r.content_version for r in run.recommendation.source_references):
                    raise WorkflowError('ANALYSIS_STALE')
                milestone = Milestone.model_validate(self.source.read.get_program_milestone(run.program_id, option['milestone_id']))
                request = PlanInput(expected_change_content_version=change['content_version'],
                    target_requirement_revision_id=change['proposed_requirement_revision_id'],
                    **{k: option[k] for k in ('configuration_id', 'procedure_id', 'milestone_id')},
                    slot_id=selected.slot_id, sample_id=selected.sample_id,
                    expected_source_versions=option['expected_source_versions'],
                    assessment={'facts': [{'text': 'CR-017 requests supplemental workload evidence under the existing criteria.',
                        'source_refs': [{'resource_type': 'engineering.change', 'resource_id': 'CR-017'}]}],
                        'evidence_gaps': [f.statement for f in run.recommendation.evidence_gaps][:30],
                        'unresolved_questions': (run.recommendation.unresolved_questions + ['Future test outcome and customer acceptance remain unknown.'])[:30]},
                    supersedes_plan_id=previous.source_plan.id if previous else None)
                prior = Preparation(preparation_id=preparation_id, origin=Origin.from_run(run), request=request,
                    milestone_before=milestone, rationale=run.recommendation.recommended_next_step,
                    created_at=now_utc(), proposal_version=previous.proposal_version + 1 if previous else 1,
                    supersedes_key=proposal_key(supersedes) if supersedes else None)
                with self.store.transaction(write=True) as data:
                    data.preparations[preparation_id] = prior
            receipt = self.source.create_plan(prior.request, 'prepare_' + digest(preparation_id)[:40])
            # Independent source read also recovers a lost draft response via the
            # identical persisted preparation request and source idempotency key.
            plan = PlanView.model_validate(self.source.read.get_plan(receipt.body['id']))
            if plan.state != 'draft' or plan.job_id:
                raise WorkflowError('SOURCE_PLAN_ALREADY_DECIDED')
            p = proposal_from_plan(plan, prior.origin, rationale=prior.rationale,
                assumptions=['Scheduling is conditional on physical testing and engineering review; customer acceptance is pending.'],
                preconditions=['Exact engineer decision; current source versions and resource eligibility; exact Planner compare-and-swap.'],
                evidence_references=run.recommendation.source_references, proposal_version=prior.proposal_version,
                created_at=prior.created_at, milestone_before=prior.milestone_before, manifest=manifest_for(plan, prior.milestone_before))
            executable_proposal(p)
            record = ExecutionRecord(reference=reference(p), steps=[ExecutionStep(action_id=a.action_id) for a in p.manifest])
            with self.store.transaction(write=True) as data:
                if prior.supersedes_key:
                    old = data.executions[prior.supersedes_key]
                    old.status = 'superseded'
                    data.proposal_status[prior.supersedes_key] = 'superseded'
                    self.store._activity(data, data.runs[old.reference.run_id], 'proposal_superseded', actor=actor,
                        proposal_id=old.reference.proposal_id, details={'replacement_proposal_id': p.proposal_id})
                data.proposals[proposal_key(reference(p))] = p
                data.proposal_status[proposal_key(reference(p))] = 'current'
                data.executions[proposal_key(reference(p))] = record
                data.preparations[preparation_id].proposal_key = proposal_key(reference(p))
                self.store._activity(data, run, 'proposal_created', actor=actor, proposal_id=p.proposal_id,
                    details={'proposal_digest': p.proposal_digest, 'proposal_version': p.proposal_version,
                             'source_plan_id': plan.id, 'cost_cents': plan.cost_cents})
                record.status = 'waiting_for_approval'
                self.store._activity(data, run, 'approval_requested', actor=actor, proposal_id=p.proposal_id,
                    details={'policy_id': p.required_policy_id, 'required_role': p.required_role})
            return p

    def _current(self, p, record):
        if record.status in {'stale', 'superseded', 'rejected'}:
            raise WorkflowError('PROPOSAL_NOT_CURRENT')
        with self.store.transaction() as data:
            if data.proposal_status.get(proposal_key(reference(p))) != 'current':
                raise WorkflowError('PROPOSAL_NOT_CURRENT')
        change = self.source.read.get_change_request('CR-017')
        if change['current_plan_id'] != p.source_plan.id or change['workflow_state'] in {'closed', 'superseded'}:
            raise WorkflowError('PROPOSAL_NOT_CURRENT')
        current = PlanView.model_validate(self.source.read.get_plan(p.source_plan.id))
        if any(getattr(current, k) != getattr(p.source_plan, k) for k in Plan.model_fields):
            raise WorkflowError('STALE_PLAN')
        if not current.implementation_link_id:
            milestone = self.source.read.get_program_milestone(p.origin.program_id, p.source_plan.milestone_id)
            if milestone != p.milestone_before.model_dump(mode='json'):
                raise WorkflowError('STALE_MILESTONE')
        option = next((o for o in self.source.read.get_validation_options('CR-017')['items']
                       if o['slot']['id'] == p.source_plan.slot_id and o['sample']['id'] == p.source_plan.sample_id), None)
        if option is None:
            raise WorkflowError('STALE_SOURCE')
        expected = option['expected_source_versions']
        before = {(s.resource_type, s.resource_id): s.content_version for s in p.source_plan.source_snapshot}
        after = {(s['resource_type'], s['resource_id']): s['content_version'] for s in expected['records']}
        if before != after or len(after) != len(expected['records']):
            raise WorkflowError('STALE_SOURCE')
        if p.source_plan.evidence_set_digest != expected['evidence_set_digest']:
            raise WorkflowError('STALE_EVIDENCE')
        policy = self.source.read.get_policy(p.required_policy_id)
        if (policy['status'] != 'approved' or policy['content_version'] != p.required_policy_version
                or policy['approver_role'] != 'engineer' or p.source_plan.cost_cents > policy['max_incremental_cost_cents']
                or p.source_plan.procedure_id not in policy['permitted_procedure_ids']
                or not {'schedule_validation', 'link_program_plan'} <= set(policy['permitted_actions'])):
            raise WorkflowError('APPROVAL_POLICY_MISMATCH')
        if not current.job_id:
            if (not option['resource_eligible'] or not option['approval_eligible']
                    or option['cost_cents'] != p.source_plan.cost_cents or option['timing'] != p.source_plan.timing.model_dump(mode='json')):
                raise WorkflowError('STALE_SOURCE')
            for s in p.source_plan.source_snapshot:
                if s.availability_version is not None:
                    actual = next(v for v in expected['records'] if (v['resource_type'], v['resource_id']) == (s.resource_type, s.resource_id))
                    if actual['availability_version'] != s.availability_version:
                        raise WorkflowError('STALE_SOURCE')
        return current

    def _approval(self, p, record):
        if not record.review_id:
            raise WorkflowError('APPROVAL_REQUIRED')
        with self.store.transaction() as data:
            review = data.reviews[record.review_id]
            binding = data.decisions.get(review.source_decision_id)
        if (review.status != 'approved' or review.reference != reference(p) or review.actor_id != ENGINEER.actor_id
                or review.actor_role != 'engineer' or review.decision != 'approve' or not binding
                or binding.origin != p.origin or binding.proposal_digest != p.proposal_digest
                or binding.proposal_version != p.proposal_version or binding.proposal_id != p.proposal_id):
            raise WorkflowError('APPROVAL_REQUIRED')
        current = self._current(p, record)
        decision = Decision.model_validate(self.source.read.get_plan_decision(review.source_decision_id))
        if (decision != binding.source_decision or current.state != 'approved' or current.decision_id != decision.id
                or decision.decision != 'approve' or decision.signer_identity != review.actor_id
                or decision.reason != review.source_reason or decision.plan_digest != p.source_plan.plan_digest
                or decision.plan_version != p.source_plan.plan_version or decision.policy_content_version != p.required_policy_version
                or any(getattr(decision, k) != getattr(p.source_plan, k) for k in ('customer_id', 'program_id', 'change_id',
                    'policy_id', 'cost_cents', 'permitted_actions', 'source_snapshot', 'configuration_id', 'sample_id', 'slot_id', 'milestone_id'))):
            raise WorkflowError('APPROVAL_BINDING_MISMATCH')
        return review.source_decision_id

    def _authorize(self, p, record):
        try:
            return self._approval(p, record)
        except SourceReadFailure:
            record.status, record.error_code = 'attention_required', 'SOURCE_READ_FAILED'
            partial = record.steps[0].resource_id is not None
            self._save(p, record, 'execution_partially_completed' if partial else 'execution_denied',
                details={'error_code': record.error_code, 'job_id': record.steps[0].resource_id})
            return None

    def review(self, ref, decision, comment, actor, human_source):
        try:
            self.actor(actor, ENGINEER)
            comment = comment or 'No additional comment.'
            with self.store.execution_lock():
                p, record = self._load(ref, actor)
                if decision not in {'approve', 'reject'}:
                    raise WorkflowError('INVALID_HUMAN_DECISION')
                if record.review_id:
                    with self.store.transaction() as data:
                        intent = data.reviews[record.review_id]
                    if intent.decision != decision or intent.comment != comment or intent.reference != ref or intent.actor_id != actor.actor_id:
                        raise WorkflowError('IMMUTABLE_REVIEW_CONFLICT')
                    if intent.status != 'recording':
                        return intent
                else:
                    self._current(p, record)
                    current = self.source.read.get_plan(p.source_plan.id)
                    if current['state'] != 'draft' or current['decision_id']:
                        raise WorkflowError('EXTERNAL_DECISION_NOT_ENVELOPE_REVIEW')
                    intent = HumanReview(review_id='review_' + uuid4().hex, reference=ref, actor_id=actor.actor_id,
                        authority_source=actor.identity_source, decision=decision, comment=comment or 'No additional comment.',
                        requested_at=now_utc(), policy_id=p.required_policy_id, policy_version=p.required_policy_version,
                        source_reason=f'Phase06 proposal {p.proposal_id} v{p.proposal_version} digest {p.proposal_digest}; {comment}'[:2000])
                    record.review_id = intent.review_id
                    with self.store.transaction(write=True) as data:
                        data.reviews[intent.review_id] = intent
                        data.executions[proposal_key(ref)] = record
                self._current(p, record)
                receipt = human_source.decide(p.source_plan.id, DecisionInput(decision=decision,
                    expected_plan_version=p.source_plan.plan_version, expected_plan_digest=p.source_plan.plan_digest,
                    reason=intent.source_reason), intent.review_id, actor)
                source = Decision.model_validate(self.source.read.get_plan_decision(receipt.body['id']))
                if (source.plan_id != p.proposal_id or source.signer_identity != actor.actor_id
                        or source.reason != intent.source_reason or source.decision != decision
                        or source.plan_digest != p.source_plan.plan_digest):
                    raise WorkflowError('APPROVAL_BINDING_MISMATCH')
                intent.source_decision_id, intent.decided_at = source.id, now_utc()
                intent.status = 'approved' if decision == 'approve' else 'rejected'
                record.status = intent.status
                if decision == 'approve': record.validation_plan = 'approved'
                binding = DecisionBinding(origin=p.origin, proposal_id=p.proposal_id, proposal_version=p.proposal_version,
                    proposal_digest=p.proposal_digest, source_decision=source)
                with self.store.transaction(write=True) as data:
                    data.reviews[intent.review_id] = intent
                    data.decisions[source.id] = binding
                    data.executions[proposal_key(ref)] = record
                    self.store._activity(data, data.runs[p.origin.run_id], 'proposal_approved' if decision == 'approve' else 'proposal_rejected',
                        actor=actor, proposal_id=p.proposal_id, details={'decision_id': source.id, 'review_id': intent.review_id,
                        'policy_id': p.required_policy_id, 'proposal_digest': p.proposal_digest})
                return intent
        except WorkflowError as exc:
            self._deny(ref, actor, str(exc))
            self._stale(ref, str(exc))
            raise

    def _stale(self, ref, code):
        if code not in {'STALE_SOURCE', 'STALE_EVIDENCE', 'STALE_PLAN', 'STALE_MILESTONE', 'PROPOSAL_NOT_CURRENT', 'APPROVAL_POLICY_MISMATCH'}:
            return
        with self.store.transaction(write=True) as data:
            record = data.executions.get(proposal_key(ref))
            if record and record.reference == ref and data.proposal_status.get(proposal_key(ref)) == 'superseded':
                record.status = 'superseded'
                return
            if record and record.reference == ref and record.status not in {'superseded', 'rejected'}:
                record.status, record.error_code = 'stale', code
                data.proposal_status[proposal_key(ref)] = 'stale'
                self.store._activity(data, data.runs[ref.run_id], 'proposal_stale', proposal_id=ref.proposal_id, details={'error_code': code})

    def _verify(self, p, record, index, decision_id):
        step, action = record.steps[index], p.manifest[index]
        record.status = 'verifying'
        self._save(p, record, 'verification_started', action_id=step.action_id)
        errors = []
        refs = []
        try:
            if index == 0:
                observed = self.source.read.get_validation_job(step.resource_id)
                errors = verify_job(p, observed, decision_id)
                tool = 'get_validation_job'
            else:
                links = self.source.read.get_implementation_links(p.origin.program_id, 'CR-017')['items']
                observed = next((v for v in links if v['id'] == step.resource_id), None)
                milestone = self.source.read.get_program_milestone(p.origin.program_id, p.source_plan.milestone_id)
                errors = verify_link(p, observed or {}, milestone, decision_id, record.steps[0].resource_id)
                tool = 'get_implementation_links'
                refs.append(SourceReference(source_id='read_' + uuid4().hex, tool_name='get_program_milestone',
                    record_id=milestone['id'], content_version=milestone['content_version'], record_version=milestone['record_version']))
            outcome = 'mismatch' if errors else 'matched'
            if observed:
                refs.append(SourceReference(source_id='read_' + uuid4().hex, tool_name=tool,
                    record_id=observed['id'], content_version=observed['content_version'], record_version=None))
        except (SourceReadFailure, SourceFailure):
            outcome = 'inconclusive'
        if not refs:
            refs = [SourceReference(source_id='read_' + uuid4().hex, tool_name='source_readback', record_id=step.resource_id,
                                    content_version=None, record_version=None)]
        verification = VerificationRecord(verification_id='verification_' + uuid4().hex, action_id=step.action_id,
            origin=p.origin, verified_at=now_utc(), claim='job_scheduled' if index == 0 else 'planner_link_recorded',
            outcome=outcome, source_references=refs,
            explanation=('Independent HTTP readback matches approved scheduling state.' if outcome == 'matched' else
                         'Readback discrepancy: ' + ', '.join(errors) if errors else 'Readback could not establish source state.'))
        step.verification = outcome
        if outcome == 'matched' and index == 0:
            record.validation_plan, record.case_status = 'approved_and_scheduled', 'in_validation'
        with self.store.transaction(write=True) as data:
            data.verifications[verification.verification_id] = verification
        self._save(p, record, 'source_state_verified' if outcome == 'matched' else 'verification_failed',
                   action_id=step.action_id, details={'outcome': outcome, 'resource_id': step.resource_id})
        if outcome != 'matched':
            record.status, record.error_code = 'attention_required', 'VERIFICATION_' + outcome.upper()
            self._save(p, record)
            return False
        return True

    def _reconcile(self, p, record, index, decision_id):
        step = record.steps[index]
        with self.store.transaction(write=True) as data:
            for attempt in data.execution_attempts:
                if attempt.action_id == step.action_id and attempt.outcome == 'started':
                    attempt.outcome, attempt.finished_at = 'unknown', now_utc()
                    attempt.error_code = 'PROCESS_INTERRUPTED'
        try:
            plan = self.source.read.get_plan(p.proposal_id)
            found = plan['job_id' if index == 0 else 'implementation_link_id']
        except SourceReadFailure:
            found = None
        if found:
            step.resource_id, step.status = found, 'already_completed'
            self._save(p, record, 'action_reconciled', action_id=step.action_id, details={'resource_id': found})
            return self._verify(p, record, index, decision_id)
        step.status, step.error_code = 'unknown', 'OUTCOME_REQUIRES_RECONCILIATION'
        record.status, record.error_code = 'attention_required', step.error_code
        self._save(p, record, 'action_outcome_unknown', action_id=step.action_id)
        if index:
            self._save(p, record, 'execution_partially_completed', details={'job_id': record.steps[0].resource_id,
                       'planner_outcome': 'unknown'})
        return False

    def _step(self, p, record, index, decision_id, invocation=None):
        step, action = record.steps[index], p.manifest[index]
        request = exact_request(action, decision_id, record.steps[0].resource_id)
        if invocation is not None:
            if invocation != {'operation': action.operation, 'target': action.target, 'arguments': request.model_dump(mode='json')}:
                raise WorkflowError('INVOCATION_NOT_APPROVED')
        if step.request is not None and step.request != request:
            raise WorkflowError('PERSISTED_REQUEST_CHANGED')
        if step.status in {'succeeded', 'already_completed'}:
            return self._verify(p, record, index, decision_id)
        if step.status in {'started', 'unknown'}:
            return self._reconcile(p, record, index, decision_id)
        # Detect the concurrent source CAS before issuing the exact approved body.
        if index == 1:
            current = self.source.read.get_program_milestone(p.origin.program_id, p.source_plan.milestone_id)
            if current != p.milestone_before.model_dump(mode='json'):
                raise WorkflowError('STALE_MILESTONE')
        step.request, step.status, step.error_code = request, 'started', None
        record.status = 'executing'
        attempt = ExecutionAttempt(attempt_id='attempt_' + uuid4().hex, action_id=action.action_id,
            reference=reference(p), decision_id=decision_id, idempotency_key=action.idempotency_key,
            request=request, started_at=now_utc())
        with self.store.transaction(write=True) as data:
            data.execution_attempts.append(attempt)
            data.executions[proposal_key(record.reference)] = record
            self.store._activity(data, data.runs[p.origin.run_id], 'action_started', proposal_id=p.proposal_id,
                action_id=action.action_id, actor=AUTOMATION, details={'operation': action.operation, 'attempt_id': attempt.attempt_id})
        try:
            # The invocation is resolved only from the validated manifest. There
            # is no arbitrary operation/URL/arguments capability at this boundary.
            receipt = self.source.schedule(request, action.idempotency_key) if index == 0 else self.source.link(request, action.idempotency_key)
            step.status = 'already_completed' if receipt.replayed else 'succeeded'
            step.resource_id = receipt.body['id']
            attempt.source_request_id = receipt.request_id
            attempt.resource_id, attempt.outcome = step.resource_id, step.status
        except SourceFailure as exc:
            step.status = 'unknown' if exc.unknown or str(exc) == 'ACTION_ALREADY_RECORDED' else 'failed'
            step.error_code = str(exc)
            attempt.outcome, attempt.error_code = step.status, str(exc)
        attempt.finished_at = now_utc()
        with self.store.transaction(write=True) as data:
            data.execution_attempts = [attempt if a.attempt_id == attempt.attempt_id else a for a in data.execution_attempts]
            data.executions[proposal_key(record.reference)] = record
        if step.status == 'unknown':
            return self._reconcile(p, record, index, decision_id)
        if step.status == 'failed':
            record.status = 'partially_executed' if index else 'execution_failed'
            record.error_code = step.error_code
            self._save(p, record, 'action_failed', action_id=step.action_id, details={'error_code': step.error_code})
            if index:
                self._save(p, record, 'execution_partially_completed', details={'job_id': record.steps[0].resource_id})
            self._stale(record.reference, step.error_code)
            return False
        self._save(p, record, 'validation_job_created' if index == 0 else 'program_plan_updated',
            action_id=step.action_id, details={'resource_id': step.resource_id, 'idempotent_replay': receipt.replayed})
        return self._verify(p, record, index, decision_id)

    def resume(self, ref, actor=AUTOMATION, *, invocation=None):
        """Resume the persisted host workflow, not an in-memory conversation.

        Optional invocation is an adversarial/testable exact-call boundary for a
        future narrow tool adapter. It can request only the next manifest action.
        """
        try:
            self.actor(actor, AUTOMATION)
            with self.store.execution_lock():
                p, record = self._load(ref, actor)
                if record.status in {'superseded', 'stale', 'rejected'}:
                    raise WorkflowError('PROPOSAL_NOT_CURRENT')
                decision_id = self._authorize(p, record)
                if decision_id is None:
                    return record
                # Check caller-supplied invocation before any write, including
                # when it attempts to target the later action ahead of dependency.
                if invocation is not None:
                    index = next((i for i, s in enumerate(record.steps) if s.status not in {'succeeded', 'already_completed'}), 1)
                    request = exact_request(p.manifest[index], decision_id, record.steps[0].resource_id)
                    if invocation != {'operation': p.manifest[index].operation, 'target': p.manifest[index].target,
                                      'arguments': request.model_dump(mode='json')}:
                        raise WorkflowError('INVOCATION_NOT_APPROVED')
                record.status, record.error_code = 'resuming', None
                self._save(p, record, 'workflow_resumed')
                for index in range(2):
                    decision_id = self._authorize(p, record)
                    if decision_id is None:
                        return record
                    if not self._step(p, record, index, decision_id):
                        return self._load(ref, actor)[1]
                record.status, record.error_code = 'completed_execution', None
                record.case_status, record.validation_plan = 'in_validation', 'approved_and_scheduled'
                self._save(p, record, 'execution_completed', details={'job_id': record.steps[0].resource_id,
                    'link_id': record.steps[1].resource_id, 'case_closed': False, 'validation_results': 'pending'})
                return record
        except WorkflowError as exc:
            self._deny(ref, actor, str(exc))
            self._stale(ref, str(exc))
            raise
