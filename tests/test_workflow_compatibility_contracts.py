"""Offline contract tests reuse isolated source APIs and simulated demo identities.

No agent executor is introduced. No working demo database or paid model is used.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from conftest import approve, draft, get, post
from mock_enterprise.core import IDENTITIES
from mock_enterprise.schemas import PlanView, Policy, Decision, JobInput
from program_coordinator.models import CaseState, FinalDecisionPackage, ProgramChangeEvent, SourceReference
from program_coordinator.application.models import TrustedActor, WorkflowInvocation, WorkflowError
from program_coordinator.application.contracts import (Origin, Proposal, DecisionBinding, ActionAttempt, VerificationRecord,
    proposal_from_plan, proposal_digest, validate_proposal, validate_decision_contract)
from program_coordinator.application.store import ActivityStore, MetadataIndex


def trusted(role):
    identity = IDENTITIES[f"demo-{role}-local-only"]
    return TrustedActor(identity.id, identity.role, frozenset((customer, program) for program, customer in identity.scopes))


@pytest.fixture
def contract(env, tmp_path):
    client, _ = env
    plan = draft(client)
    decision = approve(client, plan)
    plan = PlanView.model_validate(get(client, f'/engineering/plans/{plan["id"]}'))
    policy = Policy.model_validate(get(client, f'/engineering/policies/{plan.policy_id}'))
    event = ProgramChangeEvent.model_validate_json((Path(__file__).resolve().parents[1] / 'coordinator/scenarios/human_review.json').read_text())
    store = ActivityStore(tmp_path / "activity")
    run, _ = store.claim(WorkflowInvocation(invocation_id="contract_fixture", event=event,
        customer_id=event.customer_id, program_id=event.program_id), trusted("reader"), execution_mode="deterministic_test")
    # Explicit metadata fixture, not a simulated live-model success.
    recommendation = FinalDecisionPackage(case_id=run.case_id, customer_id=run.customer_id, program_id=run.program_id,
        classified_change_type="workload_profile_change", change_summary="Deterministic contract-test fixture.",
        affected_scope=[], specialist_findings=[], confirmed_facts=[], evidence_gaps=[], available_options=[],
        relevant_constraints=[], program_impact=[], risks=[], unresolved_questions=[], recommended_next_step="Engineering review.",
        policy_path="human_review_required", requires_human_review=True, escalation_reason=None, source_references=[],
        business_actions_executed=False, approval_granted=False, customer_accepted=False, new_validation_pass_claimed=False)
    state = CaseState(case_id=run.case_id, run_id=run.run_id, workflow_id=run.workflow_id,
        workflow_definition_version=run.definition_version, customer_id=run.customer_id, program_id=run.program_id,
        correlation_id=event.correlation_id, event=event, workflow_stage="completed", scope_verified=True,
        final_package_status="validated", final_package=recommendation)
    run = store.finish(run.run_id, state=state)
    proposal = proposal_from_plan(plan, Origin.from_run(run), rationale="Existing source plan retained for contract tests.",
        assumptions=["Future test outcome is unknown."], preconditions=["Source authorization and resources must be revalidated."])
    binding = DecisionBinding(origin=proposal.origin, proposal_id=proposal.proposal_id, proposal_version=proposal.proposal_version,
        proposal_digest=proposal.proposal_digest, source_decision=Decision.model_validate(decision))
    return dict(client=client, store=store, run=run, proposal=proposal, decision=binding,
        kwargs=dict(trusted_reviewer=trusted("engineer"), current_plan=plan, current_policy=policy,
            current_sources=deepcopy(plan.source_snapshot), evidence_set_digest=plan.evidence_set_digest))


def test_existing_source_plan_and_decision_are_reused_without_new_authority(contract):
    p, d = contract['proposal'], contract['decision']
    assert p.proposal_id == p.source_plan.id and d.source_decision.plan_digest == p.source_plan.plan_digest
    assert p.proposal_digest != p.source_plan.plan_digest
    assert [a.action for a in p.actions] == ['schedule_validation', 'link_program_plan']
    check = validate_decision_contract(p, d, **contract['kwargs'])
    assert check.binding_valid and not check.execution_allowed


@pytest.mark.parametrize('mutation', ['action_argument', 'target', 'evidence', 'assumption', 'version', 'case', 'run', 'definition'])
def test_material_proposal_changes_cannot_reuse_binding(contract, mutation):
    p = contract['proposal'].model_copy(deep=True)
    if mutation == 'action_argument': p.actions[0].arguments['cost_cents'] = 1
    if mutation == 'target': p.actions[0].arguments['sample_id'] = 'SAMPLE-OTHER'
    if mutation == 'evidence': p.evidence_references.append(SourceReference(source_id='source_extra', tool_name='get_document',
        record_id='DOC-OTHER', content_version=2, record_version=None))
    if mutation == 'assumption': p.assumptions.append('Material new assumption.')
    if mutation == 'version': p = p.model_copy(update={'proposal_version': 2})
    if mutation == 'case': p.origin.case_id = 'case_other'
    if mutation == 'run': p.origin.run_id = 'run_other'
    if mutation == 'definition': p.origin.definition_version = 2
    # Even correctly re-digesting changed content cannot reuse the old approval.
    p = p.model_copy(update={'proposal_digest': proposal_digest(p)})
    with pytest.raises(WorkflowError): validate_decision_contract(p, contract['decision'], **contract['kwargs'])


def test_nested_content_tampering_is_detected_without_new_digest(contract):
    p = contract['proposal']
    p.source_plan.source_snapshot[0].content['tampered'] = True
    with pytest.raises(WorkflowError, match='PROPOSAL_CONTENT_CHANGED'):
        validate_proposal(p)


@pytest.mark.parametrize('mutation', ['missing', 'rejected', 'unapproved', 'stale_status', 'wrong_role', 'wrong_identity', 'wrong_scope',
    'source_decision_scope', 'source_decision_version', 'policy_limit', 'policy_version', 'source_version', 'source_content',
    'evidence_set', 'missing_source', 'duplicate_source', 'source_plan_changed'])
def test_approval_contract_denials(contract, mutation):
    p, d, kwargs = contract['proposal'], contract['decision'], contract['kwargs']
    if mutation == 'missing': d = None
    if mutation == 'rejected': d.source_decision.decision = 'reject'
    if mutation == 'unapproved': kwargs['current_plan'].state = 'draft'
    if mutation == 'stale_status': kwargs['proposal_status'] = 'stale'
    if mutation == 'wrong_role': kwargs['trusted_reviewer'] = trusted('automation')
    if mutation == 'wrong_identity':
        kwargs['trusted_reviewer'] = TrustedActor('unknown_engineer', 'engineer', trusted('engineer').scopes)
    if mutation == 'wrong_scope':
        kwargs['trusted_reviewer'] = TrustedActor('demo-engineer', 'engineer', frozenset({('CUST-OTHER', 'PRG-OTHER')}))
    if mutation == 'source_decision_scope': d.source_decision.customer_id = 'CUST-OTHER'
    if mutation == 'source_decision_version': d.source_decision.plan_version = 2
    if mutation == 'policy_limit': kwargs['current_policy'].max_incremental_cost_cents = 1
    if mutation == 'policy_version': kwargs['current_policy'].content_version += 1
    if mutation == 'source_version': kwargs['current_sources'][0].content_version += 1
    if mutation == 'source_content': kwargs['current_sources'][0].content['tampered'] = True
    if mutation == 'evidence_set': kwargs['evidence_set_digest'] = 'f' * 64
    if mutation == 'missing_source': kwargs['current_sources'].pop()
    if mutation == 'duplicate_source': kwargs['current_sources'].append(kwargs['current_sources'][0])
    if mutation == 'source_plan_changed': kwargs['current_plan'].sample_id = 'SAMPLE-OTHER'
    with pytest.raises(WorkflowError): validate_decision_contract(p, d, **kwargs)


def test_proposal_contract_cannot_introduce_other_source_actions(contract):
    data = contract['proposal'].model_dump()
    data['actions'][0]['action'] = 'release_manufacturing_hold'
    with pytest.raises(ValidationError): Proposal.model_validate(data)


def test_retained_records_reload_with_distinct_meanings(contract):
    store, p, binding = contract['store'], contract['proposal'], contract['decision']
    store.retain(p, trusted('reader'))
    store.retain(binding, trusted('engineer'))
    # Existing source POST in an isolated TestClient fixture, never an agent tool.
    response = post(contract['client'], '/validation/jobs', {'plan_id': p.proposal_id, 'approval_id': binding.source_decision.id}, 'contract-job')
    assert response.status_code == 201
    job = response.json()
    attempt = ActionAttempt(action_id='attempt_test', origin=p.origin, proposal_id=p.proposal_id,
        proposal_version=p.proposal_version, proposal_digest=p.proposal_digest, decision_id=binding.source_decision.id,
        action='schedule_validation', request=JobInput(plan_id=p.proposal_id, approval_id=binding.source_decision.id),
        idempotency_key='contract-job', attempted_at='2026-09-11T12:00:00Z', outcome='succeeded',
        source_request_id=response.headers['x-request-id'], resource_id=job['id'], error_code=None)
    store.retain(attempt, trusted('automation'))
    observed = get(contract['client'], '/validation/jobs/' + job['id'])
    assert observed['status'] == 'scheduled'
    verification = VerificationRecord(verification_id='verify_test', action_id=attempt.action_id, origin=p.origin,
        verified_at='2026-09-11T12:01:00Z', claim='job_scheduled', outcome='matched',
        source_references=[SourceReference(source_id='job_read', tool_name='get_validation_job', record_id=job['id'],
            content_version=job['content_version'], record_version=None)], explanation='Fresh isolated source GET confirms scheduled status only.')
    store.retain(verification, trusted('reader'))
    reloaded = ActivityStore(store.directory)
    with reloaded.transaction() as data:
        assert data.proposals[f'{p.proposal_id}:1'] == p
        assert data.decisions[binding.source_decision.id] == binding
        assert data.actions[attempt.action_id] == attempt and data.verifications[verification.verification_id] == verification
        assert not data.runs[p.origin.run_id].recommendation.approval_granted
        assert not data.verifications[verification.verification_id].test_passed
        assert not data.verifications[verification.verification_id].customer_accepted
        assert [e.actor_id for e in data.activity[-4:]] == ['demo-reader', 'demo-engineer', 'demo-automation', 'demo-reader']
        assert all('retained' in e.event_type for e in data.activity[-4:])


def test_old_source_decision_cannot_be_rebound_to_new_envelope(contract):
    store, p, binding = contract['store'], contract['proposal'], contract['decision']
    store.retain(p, trusted('reader'));store.retain(binding, trusted('engineer'))
    revised = proposal_from_plan(contract['kwargs']['current_plan'], p.origin, rationale='Materially revised review rationale.', proposal_version=2)
    store.retain(revised, trusted('reader'))
    rebound = DecisionBinding(origin=p.origin, proposal_id=p.proposal_id, proposal_version=2,
        proposal_digest=revised.proposal_digest, source_decision=binding.source_decision)
    with pytest.raises(WorkflowError, match='IMMUTABLE_RECORD_CONFLICT'): store.retain(rebound, trusted('engineer'))


def test_proposal_storage_is_immutable_and_checks_run_scope(contract):
    store, p = contract['store'], contract['proposal']
    store.retain(p, trusted('reader'));store.retain(p, trusted('reader'))
    revised = proposal_from_plan(contract['kwargs']['current_plan'], p.origin, rationale='Changed content under the same version.')
    with pytest.raises(WorkflowError, match='IMMUTABLE_RECORD_CONFLICT'): store.retain(revised, trusted('reader'))
    wrong = p.model_copy(deep=True);wrong.origin.run_id = 'run_missing'
    with pytest.raises(WorkflowError, match='RECORD_RUN_MISMATCH'): store.retain(wrong, trusted('reader'))


def test_atomic_metadata_write_rolls_back_on_error(contract):
    store = contract['store'];before = store.path.read_bytes()
    with pytest.raises(RuntimeError):
        with store.transaction(write=True) as data:
            data.runs.clear()
            raise RuntimeError('injected offline failure')
    assert store.path.read_bytes() == before


def test_binding_does_not_replace_owned_reservation_checks(contract):
    # Availability changes need the existing per-action source provenance checks;
    # pure content-binding validation must never turn into permission to execute.
    for source in contract['kwargs']['current_sources']:
        if source.availability_version is not None: source.availability_version += 1
    result = validate_decision_contract(contract['proposal'], contract['decision'], **contract['kwargs'])
    assert result.binding_valid and result.execution_allowed is False


@pytest.mark.parametrize('patch', [{'claim': 'customer_accepted'}, {'customer_accepted': True}, {'test_passed': True},
                                  {'verified_at': '2026-09-11T12:00:00-05:00'}])
def test_verification_cannot_claim_customer_acceptance_or_test_pass(patch):
    data = dict(verification_id='v', action_id='a', origin=dict(customer_id='CUST-TEST', program_id='PRG-TEST',
        case_id='case_test', run_id='run_test', workflow_id='requirement_change_analysis', definition_version=1),
        verified_at='2026-09-11T12:00:00Z', claim='job_scheduled', outcome='matched',
        source_references=[dict(source_id='source_test', tool_name='get_validation_job', record_id='job_test',
                               content_version=1, record_version=None)], explanation='Scheduled status only.')
    VerificationRecord.model_validate(data)
    with pytest.raises(ValidationError):
        VerificationRecord.model_validate(data | patch)
