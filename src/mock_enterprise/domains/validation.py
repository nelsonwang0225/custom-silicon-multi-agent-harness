"""Validation owns scheduling and atomic resource reservations, never fabricated results."""
from fastapi import APIRouter, Request
from .. import schemas as m
from ..approvals import approved_plan
from ..core import fail, identity, metadata, new_id
from ..db import read_store
from ..http import attributed, duplicate, mutate
from ..snapshots import check_live, expected_sources, source_snapshot
from ..views import job_view
from .validation_rules import calculate_option, context, coverage

router = APIRouter(prefix='/validation', tags=['Validation Lab'])


@router.get('/coverage', response_model=m.Coverage, operation_id='compute_evidence_coverage')
def get_coverage(change_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        return coverage(store, actor, context(store, actor, change_id))


@router.get('/options', response_model=m.Options, operation_id='compute_validation_options')
def options(change_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        ctx = context(store, actor, change_id)
        evidence = coverage(store, actor, ctx)
        items = []
        for slot in store.list('validation.slot', actor, program_id=ctx['change']['program_id']):
            for sample in store.list('validation.sample', actor, program_id=ctx['change']['program_id']):
                option = calculate_option(store, actor, ctx, slot, sample)
                sources = source_snapshot(store, actor, ctx, option)
                option['expected_source_versions'] = expected_sources(sources, evidence['evidence_set_digest'])
                items.append(option)
        return dict(synthetic=True, change_id=change_id, items=items)


@router.get('/results/{result_id}', response_model=m.Result, operation_id='get_validation_result')
def result(result_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return store.get('validation.result', result_id, identity(request))


@router.get('/samples', response_model=m.Items[m.Sample], operation_id='list_validation_samples')
def samples(program_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return {'items': store.list('validation.sample', identity(request), program_id=program_id)}


@router.get('/jobs', response_model=m.Items[m.JobView], operation_id='list_validation_jobs')
def jobs(change_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        store.get('engineering.change', change_id, actor)
        return {'items': [job_view(store, actor, j) for j in store.list('validation.job', actor, change_id=change_id)]}


@router.get('/jobs/{job_id}', response_model=m.JobView, operation_id='get_validation_job')
def job(job_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        return job_view(store, actor, store.get('validation.job', job_id, actor))


@router.post('/jobs', response_model=m.JobView, status_code=201, operation_id='schedule_validation_job',
             description='Automation atomically schedules one job and reserves its exact slot/sample using a persisted engineer approval. Does not execute tests or create results.')
def schedule(body: m.JobInput, request: Request):
    def execute(store, actor, payload):
        plan = store.get('engineering.plan', payload['plan_id'], actor)
        attributed(request, {**plan, 'plan_id': plan['id']})
        # An existing job is visible only after the supplied approval matches it.
        plan, approval = approved_plan(store, actor, plan['id'], payload['approval_id'])
        duplicate(store.list('validation.job', actor, plan_id=plan['id']))
        fail('schedule_validation' in approval['permitted_actions'], 403, 'APPROVAL_REQUIRED', 'Scheduling is outside approval scope.')
        ctx = check_live(store, actor, plan)
        slot = store.get('validation.slot', plan['slot_id'], actor)
        sample = store.get('validation.sample', plan['sample_id'], actor)
        option = calculate_option(store, actor, ctx, slot, sample)
        fail(option['resource_eligible'], 409, 'RESOURCE_CONFLICT', 'Resources are no longer eligible.', reasons=option['eligibility_reasons'])
        fail(option['approval_eligible'] and option['cost_cents'] == plan['cost_cents'] and option['timing'] == plan['timing'],
             403, 'APPROVAL_POLICY_EXCEEDED', 'Calculated work no longer matches the approval.')
        job_id, reservation_id = new_id('job'), new_id('reservation')
        job = {**metadata(store, 'validation', job_id, actor), 'customer_id': actor.customer_id,
               'change_id': plan['change_id'], 'plan_id': plan['id'], 'approval_id': approval['id'],
               'plan_digest': plan['plan_digest'], 'configuration_id': plan['configuration_id'],
               'procedure_id': plan['procedure_id'], 'workload_profile_id': ctx['workload']['id'],
               'sample_id': sample['id'], 'slot_id': slot['id'], 'lab_id': slot['lab_id'],
               'cost_cents': plan['cost_cents'], 'timing': plan['timing'], 'review_minutes': plan['review_minutes'],
               'status': 'scheduled', 'reservation_id': reservation_id}
        reservation = {**metadata(store, 'validation', reservation_id, actor), 'change_id': plan['change_id'],
                       'plan_id': plan['id'], 'job_id': job_id, 'slot_id': slot['id'], 'sample_id': sample['id'],
                       'lab_id': slot['lab_id'], 'starts_at': plan['timing']['lab_start_at'], 'ends_at': plan['timing']['lab_end_at'],
                       'slot_version_before': slot['availability_version'], 'slot_version_after': slot['availability_version'] + 1,
                       'sample_version_before': sample['availability_version'], 'sample_version_after': sample['availability_version'] + 1}
        job = store.insert('validation.job', job)
        store.insert('validation.reservation', reservation)
        for kind, record in [('validation.slot', slot), ('validation.sample', sample)]:
            store.update(kind, record['id'], dict(availability='reserved', availability_version=record['availability_version'] + 1,
                                                 reserved_by_job_id=job_id, updated_at=store.now),
                         dict(availability='available', availability_version=record['availability_version']))
        return job_view(store, actor, job), {'status': 'scheduled', 'slot_availability_version': [slot['availability_version'], slot['availability_version'] + 1],
                                           'sample_availability_version': [sample['availability_version'], sample['availability_version'] + 1]}
    return mutate(request, body, 'validation', 'automation', 'schedule_job', 'validation.job', execute)
