"""One pre-authorized intake write. No scheduling, lab approval or acceptance authority."""
from fastapi import APIRouter, Request
from enterprise_api.standard_models import (StandardContext, StandardIntakeInput, ValidationIntake, IntakeList)
from enterprise_api.standard_policy import digest, evaluate, build_package
from ..core import BusinessError, fail, identity, metadata, new_id
from ..db import read_store
from ..http import attributed, mutate, duplicate
from ..schemas import Items
from enterprise_api.standard_models import StandardRequest

router = APIRouter(tags=['Standard change / Validation Operations'])


def installed(store):
    return store.con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='engineering_standard_request'").fetchone() is not None


def standard_request(store, actor, change_id):
    if not installed(store):
        return None
    rows = store.list('engineering.standard_request', actor, change_id=change_id)
    return rows[0] if len(rows) == 1 else None


def context(store, actor, change_id):
    change = store.get('engineering.change', change_id, actor)
    raw = standard_request(store, actor, change_id)
    fail(raw is not None, 404, 'NOT_FOUND', 'Standard request not found.')
    from enterprise_api.standard_models import StandardRequest
    request = StandardRequest.model_validate(raw)
    def optional(kind, record_id):
        if record_id is None:
            return None
        try:
            return store.get(kind, record_id, actor)
        except BusinessError as exc:
            if exc.status == 404:
                return None
            raise
    rule = optional('engineering.standard_rule', request.routing_rule_id)
    baseline = optional('engineering.requirement', request.baseline_requirement_revision_id)
    configuration = optional('engineering.configuration', request.configuration.configuration_id if request.configuration else change['configuration_id'])
    workload = optional('engineering.workload', request.workload_profile_id)
    procedure = optional('engineering.procedure', request.procedure_id)
    criteria = optional('engineering.criteria', baseline['acceptance_limits_ref'] if baseline else None)
    data = dict(change_id=change_id, customer_id=change['customer_id'], program_id=change['program_id'], scenario_at=store.now,
        request=raw, rule=rule, queue=optional('validation.intake_queue', rule['downstream_queue_id'] if rule else None), change=change, program=store.get('planner.program', change['program_id'], actor),
        baseline=baseline, configuration=configuration, workload=workload, criteria=criteria, procedure=procedure,
        procedure_document=optional('engineering.document', procedure['document_id'] if procedure else None),
        policy_document=optional('engineering.document', rule['document_id'] if rule else None),
        request_document=store.get('engineering.document', request.request_document_id, actor),
        milestone=optional('planner.milestone', change['milestone_id']),
        evidence=store.list('validation.result', actor, program_id=change['program_id'], workload_profile_id=request.workload_profile_id),
        samples=[s for s in (optional('validation.sample', rid) for rid in request.sample_ids) if s is not None])
    return StandardContext.model_validate({**data, 'context_digest': digest(data)})


@router.get('/engineering/standard-changes', response_model=Items[StandardRequest], operation_id='get_standard_change_requests')
def get_requests(request: Request, program_id: str | None = None):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        if program_id: store.get('planner.program', program_id, actor)
        return {'items': store.list('engineering.standard_request', actor, **({'program_id':program_id} if program_id else {})) if installed(store) else []}


@router.get('/engineering/changes/{change_id}/standard-context', response_model=StandardContext, operation_id='get_standard_change_context')
def get_context(change_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return context(store, identity(request), change_id)


@router.get('/validation/changes/{change_id}/intakes', response_model=IntakeList, operation_id='get_standard_validation_intakes')
def get_intakes(change_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        change = store.get('engineering.change', change_id, actor)
        return dict(change_id=change_id, program_id=change['program_id'], customer_id=change['customer_id'],
                    items=store.list('validation.intake', actor, change_id=change_id) if installed(store) else [])


@router.get('/validation/intakes/{intake_id}', response_model=ValidationIntake, operation_id='get_standard_validation_intake')
def get_intake(intake_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        fail(installed(store), 404, 'NOT_FOUND', 'Intake not found.')
        return store.get('validation.intake', intake_id, identity(request))


@router.post('/validation/changes/{change_id}/intakes', response_model=ValidationIntake, status_code=201, operation_id='create_standard_validation_intake')
def create_intake(change_id: str, body: StandardIntakeInput, request: Request):
    def execute(store, actor, payload):
        fail(installed(store), 409, 'STANDARD_UPGRADE_REQUIRED', 'Explicit local standard-case installation required.')
        package = body.package
        change = store.get('engineering.change', package.change_id, actor)
        attributed(request, change)
        fail(change_id == package.change_id, 404, 'NOT_FOUND', 'Scope not found.')
        current = context(store, actor, package.change_id)
        fail((package.program_id,package.customer_id) == (current.program_id,current.customer_id), 404, 'NOT_FOUND', 'Scope not found.')
        duplicate(store.list('validation.intake', actor, change_id=package.change_id, request_content_version=package.request_content_version))
        fail(body.expected_context_digest == package.context_digest == current.context_digest, 409, 'STALE_SOURCE', 'Exact current source context required.')
        eligibility = evaluate(current)
        fail(eligibility.touchless_eligible, 409, 'STANDARD_POLICY_INELIGIBLE', 'The standard policy requires review.')
        expected = build_package(current, run_id=package.workflow_run_id, case_id=package.workflow_case_id)
        fail(expected == package, 422, 'INVALID_HANDOFF_PACKAGE', 'The package must match the exact approved standard scope.')
        item = store.insert('validation.intake', {
            **metadata(store, 'validation', new_id('intake'), actor), 'customer_id':current.customer_id,
            'change_id':current.change_id, 'request_content_version':current.request.content_version,
            'package':package.model_dump(mode='json'), 'package_digest':digest(package),
            'downstream_queue_id':package.downstream_queue_id, 'downstream_owner':package.downstream_owner,
            'received_at':store.now, 'received_by':actor.id})
        return item, {'package_id':package.package_id, 'standard_handoff':True, 'lab_authorization':'pending', 'customer_acceptance':'pending'}
    return mutate(request, body, 'standard_intake', 'automation', 'create_standard_validation_intake', 'validation.intake', execute)
