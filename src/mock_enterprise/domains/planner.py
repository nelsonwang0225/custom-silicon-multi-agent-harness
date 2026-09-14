"""Planner owns conditional forecasts and dependencies; baselines remain protected."""
from datetime import timedelta
from fastapi import APIRouter, Request
from .. import schemas as m
from ..approvals import approved_plan
from ..core import at, fail, identity, iso, metadata, new_id
from ..db import read_store
from ..http import attributed, duplicate, mutate
from ..snapshots import check_live
from ..views import link_view
from .validation_rules import calculate_option

router = APIRouter(prefix='/programs', tags=['Program Planner'])


@router.get('', response_model=m.Items[m.ProgramSummary], operation_id='list_programs')
def programs(request: Request, program_id: str | None = None):
    """Scoped directory; exposes only explicit business context, not DB metadata."""
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        records = store.list('planner.program', actor, **({"program_id": program_id} if program_id else {}))
        return {'items': [{**p,
                          'customer_name': store.get('engineering.customer', p['customer_id'], actor)['name'],
                          'supplier_name': store.get('engineering.supplier', p['supplier_id'], actor)['name'],
                          'scenario_at': store.now,
                          'partner_freshness_limit_minutes': store.meta['partner_freshness_limit_minutes']}
                         for p in records]}


@router.get('/{program_id}', response_model=m.Program, operation_id='get_program')
def program(program_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return store.get('planner.program', program_id, identity(request))


@router.get('/{program_id}/milestones/{milestone_id}', response_model=m.Milestone, operation_id='get_program_milestone')
def milestone(program_id: str, milestone_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        store.get('planner.program', program_id, actor)
        result = store.get('planner.milestone', milestone_id, actor)
        fail(result['program_id'] == program_id, 404, 'NOT_FOUND', 'Resource not found.')
        return result


@router.get('/{program_id}/implementation-links', response_model=m.Items[m.LinkView], operation_id='list_implementation_links')
def links(program_id: str, change_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        store.get('planner.program', program_id, actor)
        store.get('engineering.change', change_id, actor)
        return {'items': [link_view(store, actor, r) for r in store.list('planner.link', actor, program_id=program_id, change_id=change_id)]}


@router.post('/{program_id}/implementation-links', response_model=m.LinkView, status_code=201, operation_id='link_approved_validation_plan',
             description='Atomically creates a task/dependency and conditional internal forecast from the exact scheduled job. Preserves baseline and customer commitment.')
def link(program_id: str, body: m.LinkInput, request: Request):
    def execute(store, actor, payload):
        store.get('planner.program', program_id, actor)
        plan = store.get('engineering.plan', payload['plan_id'], actor)
        attributed(request, {**plan, 'plan_id': plan['id']})
        plan, approval = approved_plan(store, actor, plan['id'], payload['approval_id'])
        job = store.get('validation.job', payload['job_id'], actor)
        fail(plan['program_id'] == program_id and job['plan_id'] == plan['id'] and job['approval_id'] == approval['id'] and
             job['plan_digest'] == plan['plan_digest'] and job['status'] == 'scheduled' and
             all(job[k] == plan[k] for k in ('configuration_id', 'procedure_id', 'sample_id', 'slot_id', 'cost_cents', 'timing', 'review_minutes')),
             403, 'APPROVAL_REQUIRED', 'Job must match this exact approved plan.')
        duplicate(store.list('planner.link', actor, plan_id=plan['id']))
        fail('link_program_plan' in approval['permitted_actions'], 403, 'APPROVAL_REQUIRED', 'Planner action is outside approval scope.')
        ctx = check_live(store, actor, plan, job=job)
        option = calculate_option(store, actor, ctx, store.get('validation.slot', plan['slot_id'], actor), store.get('validation.sample', plan['sample_id'], actor), owned_job=job['id'])
        fail(option['resource_eligible'] and option['approval_eligible'], 409, 'STALE_SOURCE', 'Approved work is no longer eligible.')
        milestone = store.get('planner.milestone', plan['milestone_id'], actor)
        fail(milestone['record_version'] == payload['expected_milestone_record_version'], 409, 'STALE_MILESTONE', 'Read the current milestone version and retry the missing action.')
        forecast = iso(at(job['timing']['lab_end_at']) + timedelta(minutes=plan['review_minutes']))
        fail(forecast == plan['timing']['review_ready_at'], 409, 'STALE_SOURCE', 'Forecast provenance changed.')
        link_id, task_id = new_id('link'), new_id('task')
        linked = {**metadata(store, 'planner', link_id, actor), 'customer_id': actor.customer_id,
                  'change_id': plan['change_id'], 'plan_id': plan['id'], 'approval_id': approval['id'], 'job_id': job['id'],
                  'milestone_id': milestone['id'], 'task_id': task_id, 'forecast_at': forecast,
                  'milestone_version_before': milestone['record_version'], 'milestone_version_after': milestone['record_version'] + 1, 'status': 'linked'}
        task = {**metadata(store, 'planner', task_id, actor), 'change_id': plan['change_id'], 'plan_id': plan['id'], 'job_id': job['id'],
                'milestone_id': milestone['id'], 'link_id': link_id, 'name': 'Supplemental validation and engineering review', 'status': 'scheduled', 'forecast_at': forecast}
        linked = store.insert('planner.link', linked)
        store.insert('planner.task', task)
        dependencies = milestone['dependencies']
        target_deps = [d for d in dependencies if d['kind'] == 'requirement_evidence' and d['requirement_revision_id'] == plan['target_requirement_revision_id']]
        fail(len(target_deps) == 1, 409, 'STALE_SOURCE', 'Expected proposed-evidence dependency is missing.')
        target_deps[0]['state'] = 'validation_scheduled'
        dependencies.append(dict(kind='validation_job', job_id=job['id'], requirement_revision_id=None, state='scheduled'))
        store.update('planner.milestone', milestone['id'], dict(dependencies=dependencies, current_forecast_at=forecast,
                    forecast_status='conditional_on_test_and_review', record_version=milestone['record_version'] + 1, updated_at=store.now),
                    {'record_version': payload['expected_milestone_record_version']})
        return link_view(store, actor, linked), {'forecast': [milestone['current_forecast_at'], forecast], 'milestone_record_version': [milestone['record_version'], milestone['record_version'] + 1]}
    return mutate(request, body, 'planner', 'automation', 'link_program_plan', 'planner.link', execute)
