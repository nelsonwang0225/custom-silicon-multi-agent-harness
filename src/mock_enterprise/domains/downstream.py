"""CR-017 downstream source ownership. No model calls and no scheduling authority."""
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from ..core import at, digest, fail, identity, iso, metadata, new_id
from ..db import read_store
from ..http import attributed, duplicate, mutate
from ..approvals import approved_plan
from ..snapshots import check_live, snapshot
from ..views import job_view
from ..downstream_models import LabCompletion, PublishResultInput, EvidenceReview, EvidenceReviewInput, PhysicalValidation
from .validation_rules import context, coverage

router = APIRouter(tags=['Downstream validation'])
KINDS = ('engineering.change', 'engineering.requirement', 'engineering.configuration',
         'engineering.workload', 'engineering.criteria', 'engineering.procedure', 'engineering.policy')


def installed(store):
    return store.con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='validation_completion'").fetchone() is not None


def completions(store, actor, **filters):
    return store.list('validation.completion', actor, **filters) if installed(store) else []


def binding_sources(store, actor, plan):
    return [snapshot(store, actor, s['resource_type'], s['resource_id']) for s in plan['source_snapshot']
            if s['resource_type'] in KINDS]


def physical(store, actor):
    change = store.get('engineering.change', 'CR-017', actor)
    result = PhysicalValidation(available=installed(store)).model_dump(mode='json')
    if not result['available']:
        return result
    result['reviews'] = store.list('engineering.evidence_review', actor, change_id='CR-017')
    jobs = store.list('validation.job', actor, change_id='CR-017', plan_id=change.get('current_plan_id')) if change.get('current_plan_id') else []
    if len(jobs) != 1:
        return result
    job = jobs[0]
    result.update(job=job_view(store, actor, job), job_status='scheduled')
    events = completions(store, actor, job_id=job['id'])
    if not events:
        return result
    event = events[0]
    observation = store.get('validation.result', event['result_id'], actor)
    result.update(completion=event, result=observation, job_status=observation['status'])
    plan, approval = approved_plan(store, actor, job['plan_id'], job['approval_id'])
    ctx = context(store, actor, 'CR-017')
    covered = coverage(store, actor, ctx)
    item = next(x for x in covered['items'] if x['result']['id'] == observation['id'])
    reasons = list(item['mismatch_reasons'])
    sources = binding_sources(store, actor, plan)
    if sources != event['source_snapshot']:
        reasons.append('STALE_APPROVED_SCOPE')
    if (event['plan_digest'] != plan['plan_digest'] or event['plan_version'] != plan['plan_version']
            or job['plan_digest'] != plan['plan_digest'] or event['result_digest'] != digest(observation)
            or event['requirement_revision_id'] != ctx['target']['id']
            or event['requirement_content_version'] != ctx['target']['content_version']
            or event['procedure_id'] != job['procedure_id'] or event['procedure_content_version'] != ctx['procedure']['content_version']
            or observation['configuration_id'] != job['configuration_id'] or observation['workload_profile_id'] != job['workload_profile_id']
            or observation['sample_id'] != job['sample_id'] or event['completed_at'] != observation['completed_at']
            or event['started_at'] != job['timing']['execution_start_at'] or event['completed_at'] != job['timing']['lab_end_at']):
        reasons.append('RESULT_BINDING_MISMATCH')
    # Conflicting observations from this exact campaign cannot be hidden by any-pass coverage.
    for other in covered['items']:
        r = other['result']
        if (r['id'] != observation['id'] and all(r[k] == observation[k] for k in ('configuration_id', 'workload_profile_id', 'sample_id'))
                and at(r['completed_at']) >= at(event['started_at']) and
                (r['criteria_passed'] != observation['criteria_passed'] or r['status'] != observation['status'])):
            reasons.append('CONFLICTING_RESULT')
    evidence_binding = dict(review_policy='CR017-ENGINEERING-EVIDENCE-V1', change_id='CR-017', requirement=ctx['target'], job=job, plan_id=plan['id'],
        plan_version=plan['plan_version'], plan_digest=plan['plan_digest'], approval_id=approval['id'],
        completion=event, result=observation, current_sources=sources, evidence_set_digest=covered['evidence_set_digest'])
    exact_digest = digest(evidence_binding)
    current = next((r for r in result['reviews'] if r['evidence_digest'] == exact_digest), None)
    applicable = not reasons
    engineering = ('approved' if current['decision'] == 'approve' else 'rejected') if current and (applicable or current['decision'] == 'reject') else 'stale' if result['reviews'] else 'ready' if applicable else 'not_ready'
    result.update(mismatch_reasons=sorted(set(reasons)), applicability='confirmed' if applicable else 'gap_remains',
        evidence_binding=evidence_binding, evidence_digest=exact_digest, current_review=current if applicable or (current and current['decision'] == 'reject') else None,
        engineering_status=engineering,
        technical_state='validation_complete' if engineering == 'approved' else 'engineering_rejected' if engineering == 'rejected' else 'engineering_review_ready' if applicable else 'validation_gap')
    return result


@router.get('/validation/changes/CR-017/physical-validation', response_model=PhysicalValidation, operation_id='get_cr017_physical_validation')
def get_physical(request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return physical(store, identity(request))


@router.get('/validation/jobs/{job_id}/completion', response_model=LabCompletion, operation_id='get_lab_completion')
def get_completion(job_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        store.get('validation.job', job_id, actor)
        rows = completions(store, actor, job_id=job_id)
        fail(bool(rows), 404, 'NOT_FOUND', 'Result not yet available.')
        return rows[0]


@router.post('/validation/jobs/{job_id}/synthetic-result', response_model=LabCompletion, status_code=201, operation_id='publish_synthetic_lab_result')
def publish(job_id: str, body: PublishResultInput, request: Request):
    def execute(store, actor, payload):
        fail(installed(store), 409, 'DOWNSTREAM_UPGRADE_REQUIRED', 'Explicit local schema upgrade required.')
        job = store.get('validation.job', job_id, actor)
        attributed(request, job)
        fail(job['change_id'] == 'CR-017' and job['status'] == 'scheduled', 409, 'SCHEDULED_CR017_JOB_REQUIRED', 'An existing scheduled CR-017 job is required.')
        fail(job['plan_digest'] == payload['expected_plan_digest'], 409, 'STALE_PLAN', 'Exact scheduled plan required.')
        existing = completions(store, actor, job_id=job_id)
        duplicate(existing)
        plan, _ = approved_plan(store, actor, job['plan_id'], job['approval_id'])
        ctx = check_live(store, actor, plan, job=job)
        fail(ctx['change']['current_plan_id'] == plan['id'], 409, 'STALE_PLAN', 'The scheduled plan has been superseded.')
        config, workload, criteria, procedure = (ctx[k] for k in ('config', 'workload', 'criteria', 'procedure'))
        completed = job['timing']['lab_end_at']
        result_id = new_id('result')
        observed = store.insert('validation.result', {
            **metadata(store, 'validation', result_id, actor), 'updated_at': completed,
            'customer_id': job['customer_id'], 'configuration_id': config['id'], 'configuration_content_version': config['content_version'],
            'workload_profile_id': workload['id'], 'workload_profile_content_version': workload['content_version'],
            'acceptance_limits_ref': criteria['id'], 'acceptance_criteria_content_version': criteria['content_version'],
            'product_revision': config['product_revision'], 'model_bundle_id': config['model_bundle_id'], 'sample_id': job['sample_id'],
            'status': 'completed', 'criteria_passed': True, 'covered_context_bins': workload['context_bins'],
            'actual_suite_minutes': procedure['suite_minutes'],
            'observed_minutes_by_context_bin': {str(b): procedure['per_bin_minutes'] for b in workload['context_bins']},
            'completed_at': completed, 'configuration_snapshot': config, 'workload_snapshot': workload, 'criteria_snapshot': criteria})
        event = store.insert('validation.completion', {
            **metadata(store, 'validation', new_id('completion'), actor), 'updated_at': completed,
            'customer_id': job['customer_id'], 'change_id': job['change_id'], 'job_id': job_id, 'plan_id': plan['id'],
            'plan_version': plan['plan_version'], 'plan_digest': plan['plan_digest'], 'result_id': result_id, 'result_digest': digest(observed),
            'requirement_revision_id': ctx['target']['id'], 'requirement_content_version': ctx['target']['content_version'],
            'procedure_id': procedure['id'], 'procedure_content_version': procedure['content_version'],
            'source_snapshot': binding_sources(store, actor, plan), 'started_at': job['timing']['execution_start_at'],
            'completed_at': completed, 'recorded_at': iso(datetime.now(timezone.utc)), 'recorded_by': actor.id,
            'source_reference': 'Validation Lab / explicit synthetic completion / ' + job_id,
            'note': 'Synthetic lab completion is a demo event in the mock Validation Lab. Agents do not physically perform the test. Simulated scenario completion time; global fixture clock unchanged. Criteria use the existing recorded boolean convention; numerical thresholds are not modeled.'})
        return event, {'result_id': result_id, 'demo_generated': True, 'booking_preserved': True}
    return mutate(request, body, 'lab_completion', 'lab', 'publish_synthetic_result', 'validation.completion', execute)


@router.post('/engineering/changes/CR-017/evidence-reviews', response_model=EvidenceReview, status_code=201, operation_id='review_cr017_validation_evidence')
def review(body: EvidenceReviewInput, request: Request):
    def execute(store, actor, payload):
        current = physical(store, actor)
        fail(current['available'], 409, 'DOWNSTREAM_UPGRADE_REQUIRED', 'Explicit local schema upgrade required.')
        attributed(request, {'change_id': 'CR-017', 'program_id': actor.program_id, 'customer_id': actor.customer_id})
        fail(current['evidence_digest'] == payload['expected_evidence_digest'], 409, 'STALE_EVIDENCE', 'Review must bind the exact current evidence.')
        duplicate([r for r in current['reviews'] if r['evidence_digest'] == payload['expected_evidence_digest']], decision=payload['decision'])
        fail(current['applicability'] == 'confirmed' or payload['decision'] == 'reject', 409, 'EVIDENCE_INAPPLICABLE', 'Engineering approval requires complete applicable evidence.')
        job, result = current['job'], current['result']
        fail(job is not None and result is not None, 409, 'RESULT_REQUIRED', 'A source result is required.')
        record = store.insert('engineering.evidence_review', {
            **metadata(store, 'engineering', new_id('evidence-review'), actor), 'updated_at': current['completion']['completed_at'],
            'customer_id': actor.customer_id, 'change_id': 'CR-017', 'job_id': job['id'], 'plan_id': job['plan_id'],
            'result_id': result['id'], 'result_content_version': result['content_version'], 'evidence_digest': current['evidence_digest'],
            'decision': payload['decision'], 'signer_identity': actor.id, 'reason': payload['reason'],
            'recorded_at': iso(datetime.now(timezone.utc)), 'evidence_binding': current['evidence_binding']})
        return record, {'engineering_review': payload['decision'], 'customer_acceptance': 'pending', 'customer_commitment': 'unchanged'}
    return mutate(request, body, 'evidence_review', 'engineer', 'review_validation_evidence', 'engineering.evidence_review', execute)
