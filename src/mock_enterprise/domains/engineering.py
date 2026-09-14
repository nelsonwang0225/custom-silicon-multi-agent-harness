"""Engineering owns immutable assessments/plans and policy-restricted decisions."""
from fastapi import APIRouter, Request
from .. import schemas as m
from ..core import fail, identity, metadata, new_id
from ..db import read_store
from ..http import attributed, duplicate, mutate
from ..snapshots import check_expected, check_live, expected_sources, plan_digest, source_snapshot
from ..views import plan_view
from .validation_rules import ACTIONS, calculate_option, context, coverage

router = APIRouter(prefix='/engineering', tags=['Engineering Hub'])


def one(request, kind, record_id):
    with read_store(request.app.state.settings.db_path) as store:
        return store.get(kind, record_id, identity(request))


@router.get('/changes', response_model=m.Items[m.Change], operation_id='list_changes')
def changes(request: Request, program_id: str | None = None):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        return {'items': store.list('engineering.change', actor, **({"program_id": program_id} if program_id else {}))}


@router.get('/changes/{change_id}', response_model=m.ChangeView, operation_id='get_change')
def change(change_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        record = store.get('engineering.change', change_id, actor)
        plans = [plan_view(store, actor, p) for p in store.list('engineering.plan', actor, change_id=change_id)]
        current = next((p for p in plans if p['id'] == record['current_plan_id']), None)
        return {**record, 'plans': plans,
                'execution_state': current['execution_state'] if current else 'not_scheduled'}


@router.get('/requirements/{requirement_revision_id}', response_model=m.Requirement, operation_id='get_requirement_revision')
def requirement(requirement_revision_id: str, request: Request):
    return one(request, 'engineering.requirement', requirement_revision_id)


@router.get('/configurations/{configuration_id}', response_model=m.Configuration, operation_id='get_configuration')
def configuration(configuration_id: str, request: Request):
    return one(request, 'engineering.configuration', configuration_id)


@router.get('/workloads/{workload_profile_id}', response_model=m.Workload, operation_id='get_workload')
def workload(workload_profile_id: str, request: Request):
    return one(request, 'engineering.workload', workload_profile_id)


@router.get('/procedures/{procedure_id}', response_model=m.Procedure, operation_id='get_procedure')
def procedure(procedure_id: str, request: Request):
    return one(request, 'engineering.procedure', procedure_id)


@router.get('/policies/{policy_id}', response_model=m.Policy, operation_id='get_approval_policy')
def policy(policy_id: str, request: Request):
    return one(request, 'engineering.policy', policy_id)


@router.get('/acceptance-criteria/{criteria_id}', response_model=m.Criteria, operation_id='get_acceptance_criteria')
def criteria(criteria_id: str, request: Request):
    return one(request, 'engineering.criteria', criteria_id)


@router.get('/documents', response_model=m.Items[m.DocumentMetadata], operation_id='list_business_documents')
def documents(program_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return {'items': [{k: v for k, v in d.items() if k != 'content'} for d in store.list('engineering.document', identity(request), program_id=program_id)]}


@router.get('/documents/{document_id}', response_model=m.Document, operation_id='get_business_document')
def document(document_id: str, request: Request):
    return one(request, 'engineering.document', document_id)


@router.get('/plans/{plan_id}', response_model=m.PlanView, operation_id='get_implementation_plan')
def plan(plan_id: str, request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        actor = identity(request)
        return plan_view(store, actor, store.get('engineering.plan', plan_id, actor))


@router.get('/decisions/{decision_id}', response_model=m.Decision, operation_id='get_plan_decision')
def decision(decision_id: str, request: Request):
    return one(request, 'engineering.decision', decision_id)


@router.post('/changes/{change_id}/plans', response_model=m.PlanView, status_code=201, operation_id='create_implementation_plan',
             description='Automation drafts an immutable assessment and calculated plan. Requires complete source versions and an Idempotency-Key.')
def draft(change_id: str, body: m.PlanInput, request: Request):
    def execute(store, actor, payload):
        from .standard_change import standard_request
        fail(standard_request(store, actor, change_id) is None, 409, 'STANDARD_INTAKE_ONLY', 'Standard package requests use the bounded intake route, not a scheduling plan.')
        ctx = context(store, actor, change_id)
        change = ctx['change']
        attributed(request, {**change, 'change_id': change_id})
        fail(change['workflow_state'] not in ('closed','superseded'), 409, 'CHANGE_CLOSED',
             'This change is closed or superseded; use its active replacement scope.')
        fail(payload['expected_change_content_version'] == change['content_version'], 409, 'STALE_SOURCE', 'Change content changed.')
        # Resolve all submitted references before checking their relationship.
        for field, kind in [('target_requirement_revision_id', 'engineering.requirement'), ('configuration_id', 'engineering.configuration'),
                            ('procedure_id', 'engineering.procedure'), ('milestone_id', 'planner.milestone')]:
            store.get(kind, payload[field], actor)
        fail(payload['target_requirement_revision_id'] == ctx['target']['id'] and payload['configuration_id'] == ctx['config']['id'] and
             payload['procedure_id'] == ctx['procedure']['id'] and payload['milestone_id'] == ctx['milestone']['id'],
             422, 'RESOURCE_INELIGIBLE', 'Selected scope does not match the change.')
        if payload['supersedes_plan_id']:
            previous = store.get('engineering.plan', payload['supersedes_plan_id'], actor)
            fail(previous['change_id'] == change_id, 422, 'RESOURCE_INELIGIBLE', 'Revision must belong to the same change.')
        slot = store.get('validation.slot', payload['slot_id'], actor)
        sample = store.get('validation.sample', payload['sample_id'], actor)
        option = calculate_option(store, actor, ctx, slot, sample)
        fail(option['resource_eligible'], 422, 'RESOURCE_INELIGIBLE', 'Resources are ineligible.', reasons=option['eligibility_reasons'])
        evidence = coverage(store, actor, ctx)
        snapshots = source_snapshot(store, actor, ctx, option, payload['assessment'])
        check_expected(payload['expected_source_versions'], expected_sources(snapshots, evidence['evidence_set_digest']))
        record = {**metadata(store, 'engineering', new_id('plan'), actor), 'customer_id': actor.customer_id,
                  'change_id': change_id, 'plan_version': 1, 'plan_digest': '0' * 64,
                  **{k: payload[k] for k in ('target_requirement_revision_id', 'configuration_id', 'procedure_id', 'sample_id', 'slot_id', 'milestone_id', 'supersedes_plan_id', 'assessment')},
                  'source_snapshot': snapshots, 'evidence_set_digest': evidence['evidence_set_digest'],
                  'policy_id': ctx['policy']['id'], 'cost_cents': option['cost_cents'], 'currency': 'USD',
                  'timing': option['timing'], 'review_minutes': ctx['procedure']['review_minutes'],
                  'permitted_actions': ACTIONS, 'coverage': evidence, 'created_by': actor.id}
        record = m.Plan.model_validate(record).model_dump(mode='json')
        record['plan_digest'] = plan_digest(record)
        record = store.insert('engineering.plan', record)
        store.insert('engineering.plan_state', dict(id=record['id'], program_id=actor.program_id, state='draft', record_version=1))
        store.update('engineering.change', change_id, dict(current_plan_id=record['id'], workflow_state='plan_drafted', record_version=change['record_version'] + 1, updated_at=store.now), {'record_version': change['record_version']})
        return plan_view(store, actor, record), {'change_record_version': [change['record_version'], change['record_version'] + 1], 'plan_digest': record['plan_digest']}
    return mutate(request, body, 'engineering', 'automation', 'create_plan', 'engineering.plan', execute)


@router.post('/plans/{plan_id}/decisions', response_model=m.Decision, status_code=201, operation_id='record_plan_decision',
             description='Simulated engineer records one approve/reject decision for the exact immutable plan version and digest. Automation cannot approve.')
def decide(plan_id: str, body: m.DecisionInput, request: Request):
    def execute(store, actor, payload):
        plan = store.get('engineering.plan', plan_id, actor)
        attributed(request, {**plan, 'plan_id': plan_id})
        duplicate(store.list('engineering.decision', actor, plan_id=plan_id), decision=payload['decision'])
        fail(payload['expected_plan_version'] == plan['plan_version'] and payload['expected_plan_digest'] == plan['plan_digest'] == plan_digest(plan),
             409, 'STALE_SOURCE', 'Exact plan version and digest required.')
        policy = store.get('engineering.policy', plan['policy_id'], actor)
        if payload['decision'] == 'approve':
            ctx = check_live(store, actor, plan)
            option = calculate_option(store, actor, ctx, store.get('validation.slot', plan['slot_id'], actor), store.get('validation.sample', plan['sample_id'], actor))
            fail(option['resource_eligible'], 409, 'RESOURCE_CONFLICT', 'Resources are no longer eligible.', reasons=option['eligibility_reasons'])
            fail(option['approval_eligible'], 403, 'APPROVAL_POLICY_EXCEEDED', 'Plan exceeds delegated policy.', reasons=option['approval_reasons'])
        decision = {**metadata(store, 'engineering', new_id('decision'), actor), 'customer_id': actor.customer_id,
                    'change_id': plan['change_id'], 'plan_id': plan_id, 'plan_version': plan['plan_version'], 'plan_digest': plan['plan_digest'],
                    'decision': payload['decision'], 'signer_identity': actor.id, 'signer_role': 'engineer', 'reason': payload['reason'],
                    'policy_id': policy['id'], 'policy_content_version': policy['content_version'],
                    **{k: plan[k] for k in ('cost_cents', 'permitted_actions', 'source_snapshot', 'configuration_id', 'sample_id', 'slot_id', 'milestone_id')}}
        decision = store.insert('engineering.decision', decision)
        state = store.get('engineering.plan_state', plan_id, actor)
        store.update('engineering.plan_state', plan_id, dict(state='approved' if payload['decision'] == 'approve' else 'rejected', decision_id=decision['id'], record_version=state['record_version'] + 1))
        change = store.get('engineering.change', plan['change_id'], actor)
        if change['current_plan_id'] == plan_id:
            store.update('engineering.change', change['id'], dict(workflow_state='approved_awaiting_scheduling' if payload['decision'] == 'approve' else 'plan_rejected', record_version=change['record_version'] + 1, updated_at=store.now), {'record_version': change['record_version']})
        return decision, {'plan_state': [state['state'], 'approved' if payload['decision'] == 'approve' else 'rejected'], 'plan_record_version': [state['record_version'], state['record_version'] + 1]}
    return mutate(request, body, 'engineering', 'engineer', 'record_decision', 'engineering.decision', execute)
