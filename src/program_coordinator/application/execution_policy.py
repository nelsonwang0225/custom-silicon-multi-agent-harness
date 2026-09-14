"""Fixed CR-017 policy, exact manifest derivation and deterministic verification."""
from copy import deepcopy
from mock_enterprise.schemas import JobInput, LinkInput, Milestone
from .contracts import ManifestAction, digest, validate_proposal
from .models import WorkflowError


def manifest_for(plan, milestone):
    p = plan.model_dump(mode='json')
    common = {k: p[k] for k in ('program_id', 'customer_id', 'change_id')}
    common.update(plan_id=plan.id, approval_id='$approval.id')
    job_expected = common | {k: p[k] for k in ('plan_digest', 'configuration_id', 'procedure_id', 'sample_id',
                                              'slot_id', 'cost_cents', 'timing', 'review_minutes')}
    slot = next(s.content for s in plan.source_snapshot if s.resource_type == 'validation.slot' and s.resource_id == plan.slot_id)
    target = next(s.content for s in plan.source_snapshot if s.resource_type == 'engineering.requirement' and s.resource_id == plan.target_requirement_revision_id)
    job_expected.update(status='scheduled', lab_id=slot['lab_id'], workload_profile_id=target['workload_profile_id'])
    schedule_id, link_id = 'schedule_' + plan.id, 'link_' + plan.id
    return [ManifestAction(action_id=schedule_id, sequence=1, operation='schedule_validation_job', target_system='validation',
        target='/validation/jobs', arguments={'plan_id': plan.id, 'approval_id': '$approval.id'}, depends_on=None,
        idempotency_key=schedule_id, expected=job_expected),
        ManifestAction(action_id=link_id, sequence=2, operation='link_approved_validation_plan', target_system='planner',
        target=f'/programs/{plan.program_id}/implementation-links',
        arguments={'plan_id': plan.id, 'approval_id': '$approval.id', 'job_id': '$schedule.resource_id',
                   'expected_milestone_record_version': milestone.record_version}, depends_on=schedule_id,
        idempotency_key=link_id, expected=common | {'job_id': '$schedule.resource_id', 'milestone_id': plan.milestone_id,
            'forecast_at': plan.timing.review_ready_at, 'status': 'linked',
            'milestone_version_before': milestone.record_version, 'milestone_version_after': milestone.record_version + 1})]


def executable_proposal(proposal):
    p = validate_proposal(proposal)
    if ((p.origin.customer_id, p.origin.program_id, p.source_plan.change_id, p.origin.workflow_id, p.origin.definition_version)
            != ('CUST-FML01', 'PRG-A17', 'CR-017', 'requirement_change_analysis', 1)):
        raise WorkflowError('EXECUTION_SCOPE_FORBIDDEN')
    if (not p.created_at or not p.milestone_before or p.milestone_before.id != p.source_plan.milestone_id
            or p.milestone_before.program_id != p.origin.program_id
            or p.manifest != manifest_for(p.source_plan, p.milestone_before)
            or {a.action for a in p.actions} != {'schedule_validation', 'link_program_plan'}):
        raise WorkflowError('INVALID_EXECUTION_MANIFEST')
    return p


def resolve(value, decision_id, job_id=None):
    if isinstance(value, dict):
        return {k: resolve(v, decision_id, job_id) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, decision_id, job_id) for v in value]
    if value == '$approval.id':
        return decision_id
    if value == '$schedule.resource_id':
        if not job_id:
            raise WorkflowError('DEPENDENCY_NOT_VERIFIED')
        return job_id
    return value


def exact_request(manifest, decision_id, job_id=None):
    schema = JobInput if manifest.sequence == 1 else LinkInput
    return schema.model_validate(resolve(manifest.arguments, decision_id, job_id))


def expected_milestone(proposal, job_id):
    expected = proposal.milestone_before.model_dump(mode='json')
    deps = expected['dependencies']
    targets = [d for d in deps if d['kind'] == 'requirement_evidence' and d['requirement_revision_id'] == proposal.source_plan.target_requirement_revision_id]
    if len(targets) != 1:
        raise WorkflowError('INVALID_MILESTONE_DEPENDENCY')
    targets[0]['state'] = 'validation_scheduled'
    deps.append(dict(kind='validation_job', job_id=job_id, requirement_revision_id=None, state='scheduled'))
    expected.update(current_forecast_at=proposal.source_plan.timing.review_ready_at,
                    forecast_status='conditional_on_test_and_review', record_version=expected['record_version'] + 1)
    # Source uses its fixed scenario clock for the update timestamp.
    expected['updated_at'] = proposal.source_plan.updated_at
    return Milestone.model_validate(expected).model_dump(mode='json')


def verify_job(proposal, observed, decision_id):
    expected = resolve(proposal.manifest[0].expected, decision_id)
    errors = [k for k, v in expected.items() if observed.get(k) != v]
    reservation = observed.get('reservation', {})
    p = proposal.source_plan
    expected_reservation = dict(id=observed.get('reservation_id'), program_id=p.program_id, change_id=p.change_id,
        plan_id=p.id, job_id=observed.get('id'), slot_id=p.slot_id, sample_id=p.sample_id,
        lab_id=expected['lab_id'], starts_at=p.timing.lab_start_at, ends_at=p.timing.lab_end_at)
    for kind in ('slot', 'sample'):
        version = next(s.availability_version for s in p.source_snapshot if s.resource_type == 'validation.' + kind and s.resource_id == getattr(p, kind + '_id'))
        expected_reservation[kind + '_version_before'] = version
        expected_reservation[kind + '_version_after'] = version + 1
    errors += ['reservation.' + k for k, v in expected_reservation.items() if reservation.get(k) != v]
    return errors


def verify_link(proposal, observed, milestone, decision_id, job_id):
    expected = resolve(proposal.manifest[1].expected, decision_id, job_id)
    errors = [k for k, v in expected.items() if observed.get(k) != v]
    p = proposal.source_plan
    task_expected = dict(id=observed.get('task_id'), program_id=p.program_id, change_id=p.change_id,
        plan_id=p.id, job_id=job_id, milestone_id=p.milestone_id, link_id=observed.get('id'),
        status='scheduled', forecast_at=p.timing.review_ready_at, name='Supplemental validation and engineering review')
    errors += ['task.' + k for k, v in task_expected.items() if observed.get('task', {}).get(k) != v]
    before = expected_milestone(proposal, job_id)
    # Compare all source milestone fields, including owners, baseline, dependencies
    # and optional descriptions. Unapproved changes cannot hide behind a subset.
    if milestone != before:
        errors.append('milestone')
    return errors
