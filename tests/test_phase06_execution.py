"""Deterministic Phase 06 tests. Isolated APIs; simulated demo personas; NO AI."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from conftest import get, post, draft, approve
from test_authority_staleness import external_update
from mock_enterprise.core import IDENTITIES, BusinessError
from mock_enterprise.db import Store, read_store
from program_coordinator.models import CaseState, FinalDecisionPackage, ProgramChangeEvent
from program_investigator.models import ValidationOption
from program_coordinator.application.store import ActivityStore
from program_coordinator.application.models import WorkflowInvocation, WorkflowError
from program_coordinator.application.contracts import proposal_digest
from program_coordinator.application.execution import ExecutionService, reference, proposal_key
from program_coordinator.application.execution_policy import exact_request
from program_coordinator.infrastructure.source_gateway import SourceGateway, HumanDecisionGateway, AUTOMATION, ENGINEER, READER, SourceFailure


class RecordingGateway(SourceGateway):
    def __init__(self, client):
        super().__init__(demo_mode=True, http_client=client)
        self.calls = []

    def schedule(self, body, key):
        self.calls.append(('schedule', body.model_dump(), key))
        return super().schedule(body, key)

    def link(self, body, key):
        self.calls.append(('link', body.model_dump(), key))
        return super().link(body, key)


def analysis_fixture(store, source, invocation='analysis_one'):
    event = ProgramChangeEvent.model_validate_json(Path('coordinator/scenarios/human_review.json').read_text())
    run, _ = store.claim(WorkflowInvocation(invocation_id=invocation, event=event,
        customer_id=event.customer_id, program_id=event.program_id), READER, execution_mode='deterministic_test')
    options = []
    for o in source.read.get_validation_options('CR-017')['items']:
        raw = {k: o[k] for k in ValidationOption.model_fields if k in o}
        raw.update(slot_id=o['slot']['id'], sample_id=o['sample']['id'], rate_id=o['rate']['id'], source_refs=['options_read'])
        options.append(ValidationOption.model_validate(raw))
    final = FinalDecisionPackage(case_id=run.case_id, customer_id=run.customer_id, program_id=run.program_id,
        classified_change_type='workload_profile_change', change_summary='Offline fixture of validated SDK output.',
        affected_scope=[], specialist_findings=[], confirmed_facts=[], evidence_gaps=[], available_options=options,
        relevant_constraints=[], program_impact=[], risks=[], unresolved_questions=[],
        recommended_next_step='Review a qualified on-time validation plan; test results remain unknown.',
        policy_path='human_review_required', requires_human_review=True, escalation_reason=None, source_references=[],
        business_actions_executed=False, approval_granted=False, customer_accepted=False, new_validation_pass_claimed=False)
    return store.finish(run.run_id, state=CaseState(case_id=run.case_id, run_id=run.run_id,
        workflow_id=run.workflow_id, workflow_definition_version=run.definition_version, customer_id=run.customer_id,
        program_id=run.program_id, correlation_id=event.correlation_id, event=event, workflow_stage='completed',
        scope_verified=True, final_package_status='validated', final_package=final))


@pytest.fixture
def phase(env, tmp_path):
    client, settings = env
    source = RecordingGateway(client)
    human = HumanDecisionGateway(demo_mode=True, http_client=client)
    store = ActivityStore(tmp_path / 'phase06')
    run = analysis_fixture(store, source)
    service = ExecutionService(store, source)
    proposal = service.prepare(run.run_id, 'prepare_one')
    return dict(service=service, source=source, human=human, store=store, run=run, p=proposal,
                ref=reference(proposal), client=client, settings=settings)


def reviewed(f, decision='approve'):
    return f['service'].review(f['ref'], decision, 'Simulated engineering review of exact envelope.', ENGINEER, f['human'])


def counts(f):
    return (len(get(f['client'], '/validation/jobs?change_id=CR-017')['items']),
            len(get(f['client'], '/programs/PRG-A17/implementation-links?change_id=CR-017')['items']))


def test_a_no_approval_zero_write_calls(phase):
    with pytest.raises(WorkflowError, match='APPROVAL_REQUIRED'):
        phase['service'].resume(phase['ref'])
    assert not phase['source'].calls and counts(phase) == (0, 0)
    assert phase['service'].inspect(phase['ref'])['execution']['status'] == 'waiting_for_approval'


@pytest.mark.parametrize('actor', [AUTOMATION, READER, replace(ENGINEER), replace(AUTOMATION, role='engineer')])
def test_b_wrong_or_forged_reviewer(phase, actor):
    with pytest.raises(WorkflowError):
        phase['service'].review(phase['ref'], 'approve', 'Fake reviewer', actor, phase['human'])
    with pytest.raises(WorkflowError):
        phase['service'].resume(phase['ref'])
    assert not phase['source'].calls and counts(phase) == (0, 0)


@pytest.mark.parametrize('field,value', [('case_id', 'case_other'), ('program_id', 'PRG-OTHER'), ('customer_id', 'CUST-OTHER'),
    ('workflow_id', 'delivery_readiness'), ('definition_version', 2), ('run_id', 'run_other')])
def test_c_scope_binding(phase, field, value):
    reviewed(phase)
    wrong = phase['ref'].model_copy(update={field: value})
    with pytest.raises(WorkflowError): phase['service'].resume(wrong)
    assert not phase['source'].calls


@pytest.mark.parametrize('kind', ['digest', 'nested_action', 'manifest_arguments', 'manifest_target', 'before_image'])
def test_d_persisted_proposal_tampering(phase, kind):
    reviewed(phase)
    with phase['store'].transaction(write=True) as data:
        key = proposal_key(phase['ref']); p = data.proposals[key]
        if kind == 'digest': p = p.model_copy(update={'proposal_digest': '0' * 64})
        if kind == 'nested_action': p.actions[0].arguments['cost_cents'] = 1
        if kind == 'manifest_arguments': p.manifest[0].arguments['plan_id'] = 'other'
        if kind == 'manifest_target': p.manifest[0].target = '/manufacturing/holds'
        if kind == 'before_image': p.milestone_before.baseline_at = '2026-12-01T00:00:00Z'
        data.proposals[key] = p
    with pytest.raises(WorkflowError): phase['service'].resume(phase['ref'])
    assert not phase['source'].calls


def test_e_h_revised_proposal_supersedes_old_approval(phase):
    reviewed(phase)
    p2 = phase['service'].prepare(phase['run'].run_id, 'prepare_two', supersedes=phase['ref'])
    assert p2.proposal_version == 2 and p2.source_plan.id != phase['p'].source_plan.id
    with pytest.raises(WorkflowError): phase['service'].resume(phase['ref'])
    with pytest.raises(WorkflowError, match='APPROVAL_REQUIRED'): phase['service'].resume(reference(p2))
    assert counts(phase) == (0, 0) and not phase['source'].calls
    with phase['store'].transaction() as data:
        assert data.executions[proposal_key(phase['ref'])].status == 'superseded'
    phase['service'].review(reference(p2), 'approve', 'Simulated revised review', ENGINEER, phase['human'])
    assert phase['service'].resume(reference(p2)).status == 'completed_execution'


@pytest.mark.parametrize('kind', ['engineering.document', 'engineering.procedure', 'engineering.policy', 'validation.result', 'erp.rate'])
def test_f_material_source_changes_stale_zero_writes(phase, kind):
    reviewed(phase)
    snapshot = next(s for s in phase['p'].source_plan.source_snapshot if s.resource_type == kind)
    if kind in {'engineering.document', 'validation.result'}:
        # These source records are immutable. New imports change the source/evidence
        # set; tests must not disable their immutability protections.
        with read_store(phase['settings'].db_path) as db:
            record = db.get(kind, snapshot.resource_id)
            record['id'] += '-NEW'
            db.insert(kind, record)
            db.con.commit()
    else:
        external_update(phase['settings'], kind, snapshot.resource_id, {'content_version': snapshot.content_version + 1})
    with pytest.raises(WorkflowError): phase['service'].resume(phase['ref'])
    assert not phase['source'].calls and counts(phase) == (0, 0)
    assert phase['service'].inspect(phase['ref'])['execution']['status'] == 'stale'


def test_g_rejected_never_executes(phase):
    decision = reviewed(phase, 'reject')
    assert decision.status == 'rejected'
    with pytest.raises(WorkflowError): phase['service'].resume(phase['ref'])
    assert not phase['source'].calls and counts(phase) == (0, 0)


@pytest.mark.parametrize('kind', ['unapproved_action', 'argument', 'nonpermitted_operation', 'target', 'extra_argument'])
def test_i_j_k_invocation_enforcement(phase, kind):
    review = reviewed(phase)
    action = phase['p'].manifest[0]
    call = dict(operation=action.operation, target=action.target,
                arguments=exact_request(action, review.source_decision_id).model_dump())
    if kind == 'unapproved_action': call['operation'] = 'link_approved_validation_plan'
    if kind == 'argument': call['arguments']['plan_id'] = 'different_plan'
    if kind == 'nonpermitted_operation': call['operation'] = 'release_manufacturing_hold'
    if kind == 'target': call['target'] = '/programs/PRG-OTHER/implementation-links'
    if kind == 'extra_argument': call['arguments']['status'] = 'passed'
    with pytest.raises(WorkflowError, match='INVOCATION_NOT_APPROVED'):
        phase['service'].resume(phase['ref'], invocation=call)
    assert not phase['source'].calls


def test_l_m_normal_path_replay_no_duplicates_and_separate_verification(phase):
    reviewed(phase)
    first = phase['service'].resume(phase['ref'])
    assert first.status == 'completed_execution'
    assert first.case_status == 'in_validation' and first.validation_plan == 'approved_and_scheduled'
    assert first.validation_coverage == 'pending_test_results' and first.customer_acceptance == 'pending'
    assert first.hardware_adequacy == 'unvalidated'
    assert [c[0] for c in phase['source'].calls] == ['schedule', 'link']
    assert counts(phase) == (1, 1)
    assert phase['service'].resume(phase['ref']).status == 'completed_execution'
    assert len(phase['source'].calls) == 2 and counts(phase) == (1, 1)
    report = phase['service'].inspect(phase['ref'])
    assert len(report['attempts']) == 2 and len(report['verification']) == 4
    assert all(v['outcome'] == 'matched' and not v['test_passed'] and not v['customer_accepted'] for v in report['verification'])
    assert not phase['run'].recommendation.approval_granted
    assert get(phase['client'], '/engineering/changes/CR-017')['execution_state'] == 'scheduled_awaiting_execution'
    assert get(phase['client'], '/engineering/requirements/REQ-042-V1')['status'] == 'approved'
    assert get(phase['client'], '/engineering/requirements/REQ-042-V2')['status'] == 'requested'


def test_n_partial_failure_retries_only_incomplete_step(phase, monkeypatch):
    reviewed(phase)
    original = phase['source'].link
    def fail(body, key):
        phase['source'].calls.append(('link_failed', body.model_dump(), key))
        raise SourceFailure('RESOURCE_CONFLICT')
    with monkeypatch.context() as m:
        m.setattr(phase['source'], 'link', fail)
        partial = phase['service'].resume(phase['ref'])
    assert partial.status == 'partially_executed' and counts(phase) == (1, 0)
    job_id = partial.steps[0].resource_id
    complete = phase['service'].resume(phase['ref'])
    assert complete.status == 'completed_execution' and complete.steps[0].resource_id == job_id
    assert [c[0] for c in phase['source'].calls] == ['schedule', 'link_failed', 'link']
    assert counts(phase) == (1, 1)


@pytest.mark.parametrize('target', ['job', 'link', 'milestone', 'task'])
def test_o_verification_mismatch_is_not_success(phase, monkeypatch, target):
    reviewed(phase)
    read = phase['source'].read
    if target == 'job':
        original = read.get_validation_job
        def wrong(*a):
            value = original(*a); value['configuration_id'] = 'CFG-WRONG'; return value
        monkeypatch.setattr(read, 'get_validation_job', wrong)
    elif target in {'link', 'task'}:
        original = read.get_implementation_links
        def wrong(*a):
            value = original(*a)
            if value['items']:
                if target == 'link': value['items'][0]['forecast_at'] = '2027-01-01T00:00:00Z'
                else: value['items'][0]['task']['name'] = 'Unapproved task'
            return value
        monkeypatch.setattr(read, 'get_implementation_links', wrong)
    else:
        original = read.get_program_milestone
        def wrong(*a):
            value = original(*a)
            if value['record_version'] > phase['p'].milestone_before.record_version:
                value['owner'] = 'Unapproved owner'
            return value
        monkeypatch.setattr(read, 'get_program_milestone', wrong)
    result = phase['service'].resume(phase['ref'])
    assert result.status == 'attention_required' and result.error_code == 'VERIFICATION_MISMATCH'
    assert result.steps[0].resource_id
    report = phase['service'].inspect(phase['ref'])
    assert report['attempts'][0]['outcome'] == 'succeeded'
    assert any(v['outcome'] == 'mismatch' for v in report['verification'])
    assert counts(phase) == ((1, 0) if target == 'job' else (1, 1))


def test_p_restart_reload_review_and_execution(phase):
    reviewed(phase)
    restored = ExecutionService(ActivityStore(phase['store'].directory), phase['source'])
    assert restored.resume(phase['ref']).status == 'completed_execution'
    restored_again = ExecutionService(ActivityStore(phase['store'].directory), phase['source'])
    assert restored_again.resume(phase['ref']).status == 'completed_execution'
    assert counts(phase) == (1, 1) and len(phase['source'].calls) == 2


@pytest.mark.parametrize('workflow', ['yield_exception_recovery', 'delivery_readiness'])
def test_q_illustrative_workflow_cannot_prepare_or_execute(phase, workflow):
    with phase['store'].transaction(write=True) as data:
        data.runs[phase['run'].run_id].workflow_id = workflow
    with pytest.raises(WorkflowError): phase['service'].prepare(phase['run'].run_id, 'future')
    with pytest.raises(WorkflowError): phase['service'].resume(phase['ref'])
    assert not phase['source'].calls


@pytest.mark.parametrize('target', ['schedule', 'link'])
def test_lost_response_after_commit_reconciles_without_post_retry(phase, monkeypatch, target):
    reviewed(phase)
    original = getattr(phase['source'], target)
    def lost(*args):
        original(*args)
        raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True)
    with monkeypatch.context() as m:
        m.setattr(phase['source'], target, lost)
        result = phase['service'].resume(phase['ref'])
    assert result.status == 'completed_execution' and counts(phase) == (1, 1)
    assert len(phase['source'].calls) == 2
    assert any(s.status == 'already_completed' for s in result.steps)
    assert any(a['outcome'] == 'unknown' for a in phase['service'].inspect(phase['ref'])['attempts'])


def test_unknown_absent_outcome_is_never_blindly_retried(phase, monkeypatch):
    reviewed(phase)
    calls = []
    def unknown(*args):
        calls.append(True)
        raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True)
    with monkeypatch.context() as m:
        m.setattr(phase['source'], 'schedule', unknown)
        result = phase['service'].resume(phase['ref'])
    assert result.status == 'attention_required'
    assert phase['service'].resume(phase['ref']).status == 'attention_required'
    assert counts(phase) == (0, 0) and not phase['source'].calls and len(calls) == 1


def test_crash_after_source_commit_started_marker_recovers(phase, monkeypatch):
    reviewed(phase)
    original = phase['source'].schedule
    def crash(*args):
        original(*args)
        raise KeyboardInterrupt('Offline simulated process crash')
    with monkeypatch.context() as m:
        m.setattr(phase['source'], 'schedule', crash)
        with pytest.raises(KeyboardInterrupt): phase['service'].resume(phase['ref'])
    restored = ExecutionService(ActivityStore(phase['store'].directory), phase['source'])
    assert restored.resume(phase['ref']).status == 'completed_execution'
    assert len(phase['source'].calls) == 2 and counts(phase) == (1, 1)


def test_review_commit_crash_reuses_exact_intent(phase, monkeypatch):
    original = phase['human'].decide
    def crash(*args):
        original(*args)
        raise KeyboardInterrupt('Offline simulated review crash')
    with monkeypatch.context() as m:
        m.setattr(phase['human'], 'decide', crash)
        with pytest.raises(KeyboardInterrupt): reviewed(phase)
    assert reviewed(phase).status == 'approved'
    assert phase['service'].resume(phase['ref']).status == 'completed_execution'


def test_forecast_cas_drift_preserves_booking_and_requires_reconciliation(phase, monkeypatch):
    reviewed(phase)
    original = phase['source'].schedule
    def concurrent_update(*args):
        receipt = original(*args)
        external_update(phase['settings'], 'planner.milestone', 'MS-ACCEPT-01',
                        {'record_version': phase['p'].milestone_before.record_version + 1})
        return receipt
    monkeypatch.setattr(phase['source'], 'schedule', concurrent_update)
    with pytest.raises(WorkflowError, match='STALE_MILESTONE'): phase['service'].resume(phase['ref'])
    assert counts(phase) == (1, 0)
    assert len(phase['source'].calls) == 1
    assert phase['service'].inspect(phase['ref'])['execution']['status'] == 'stale'


def test_demo_actor_map_agrees_with_existing_server_and_no_mode_bypass():
    for actor in [AUTOMATION, ENGINEER, READER]:
        source = IDENTITIES[f'demo-{actor.role}-local-only']
        assert actor.actor_id == source.id
        assert actor.scopes == frozenset((c, p) for p, c in source.scopes)
    with pytest.raises(WorkflowError, match='DEMO_MODE_REQUIRED'): SourceGateway()
    with pytest.raises(ValidationError): SourceGateway('https://example.com', demo_mode=True)


def test_human_source_approval_alone_does_not_authorize_envelope(phase):
    approve(phase['client'], phase['p'].source_plan.model_dump())
    with pytest.raises(WorkflowError, match='APPROVAL_REQUIRED'):
        phase['service'].resume(phase['ref'])
    with pytest.raises(WorkflowError, match='EXTERNAL_DECISION_NOT_ENVELOPE_REVIEW'):
        reviewed(phase)
    assert not phase['source'].calls


def test_old_decision_rebound_to_revised_proposal_is_rejected(phase):
    first = reviewed(phase)
    p2 = phase['service'].prepare(phase['run'].run_id, 'prepare_two', supersedes=phase['ref'])
    with phase['store'].transaction(write=True) as data:
        data.executions[proposal_key(reference(p2))].review_id = first.review_id
        data.executions[proposal_key(reference(p2))].status = 'approved'
    with pytest.raises(WorkflowError, match='APPROVAL_REQUIRED'): phase['service'].resume(reference(p2))
    assert not phase['source'].calls


def test_review_replay_is_idempotent_but_conflicting_decision_is_not(phase):
    first = reviewed(phase)
    assert reviewed(phase) == first
    with pytest.raises(WorkflowError, match='IMMUTABLE_REVIEW_CONFLICT'): reviewed(phase, 'reject')
    with pytest.raises(WorkflowError, match='IMMUTABLE_REVIEW_CONFLICT'):
        phase['service'].review(phase['ref'], 'approve', 'Changed comment', ENGINEER, phase['human'])
    assert not phase['source'].calls


def test_preparation_replay_survives_lost_plan_response(env, tmp_path, monkeypatch):
    client, _ = env
    source = RecordingGateway(client)
    store = ActivityStore(tmp_path / 'activity')
    service = ExecutionService(store, source)
    run = analysis_fixture(store, source)
    original = source.create_plan
    def lost(*args):
        original(*args)
        raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True)
    with monkeypatch.context() as m:
        m.setattr(source, 'create_plan', lost)
        with pytest.raises(SourceFailure): service.prepare(run.run_id, 'preparation')
    proposal = service.prepare(run.run_id, 'preparation')
    assert service.prepare(run.run_id, 'preparation') == proposal
    assert len(get(client, '/engineering/changes/CR-017')['plans']) == 1
    assert not source.calls


@pytest.mark.parametrize('case', ['reader', 'engineer'])
def test_execution_caller_requires_automation(phase, case):
    reviewed(phase)
    with pytest.raises(WorkflowError, match='EXECUTION_ROLE_FORBIDDEN'):
        phase['service'].resume(phase['ref'], READER if case == 'reader' else ENGINEER)
    assert not phase['source'].calls


def test_verification_inconclusive_retries_get_without_repeating_write(phase, monkeypatch):
    from program_coordinator.application.execution_models import SourceReadFailure
    reviewed(phase)
    with monkeypatch.context() as m:
        m.setattr(phase['source'].read, 'get_validation_job', lambda *a: (_ for _ in ()).throw(SourceReadFailure('SOURCE_READ_FAILED')))
        result = phase['service'].resume(phase['ref'])
    assert result.status == 'attention_required' and result.steps[0].status == 'succeeded'
    assert result.steps[0].verification == 'inconclusive'
    assert phase['service'].resume(phase['ref']).status == 'completed_execution'
    assert [c[0] for c in phase['source'].calls] == ['schedule', 'link']


def test_unknown_link_keeps_successful_lab_step_and_refuses_repost(phase, monkeypatch):
    reviewed(phase)
    def unknown(*a): raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True)
    with monkeypatch.context() as m:
        m.setattr(phase['source'], 'link', unknown)
        partial = phase['service'].resume(phase['ref'])
    assert partial.status == 'attention_required' and partial.steps[0].status == 'succeeded'
    assert phase['service'].resume(phase['ref']).status == 'attention_required'
    assert len(phase['source'].calls) == 1 and counts(phase) == (1, 0)


def test_scheduling_failure_records_attempt_but_no_verification(phase, monkeypatch):
    reviewed(phase)
    with monkeypatch.context() as m:
        m.setattr(phase['source'], 'schedule', lambda *a: (_ for _ in ()).throw(SourceFailure('RESOURCE_CONFLICT')))
        result = phase['service'].resume(phase['ref'])
    assert result.status == 'execution_failed'
    report = phase['service'].inspect(phase['ref'])
    assert len(report['attempts']) == 1 and report['attempts'][0]['outcome'] == 'failed'
    assert not report['verification'] and counts(phase) == (0, 0)
    assert phase['service'].resume(phase['ref']).status == 'completed_execution'


def test_stale_before_review_records_no_source_decision(phase):
    external_update(phase['settings'], 'engineering.procedure', 'PROC-LC-02', {'content_version': 2})
    with pytest.raises(WorkflowError, match='STALE_SOURCE'): reviewed(phase)
    assert get(phase['client'], '/engineering/plans/' + phase['p'].proposal_id)['decision_id'] is None
    assert not phase['source'].calls


def test_milestone_changes_before_approval_are_blocked(phase):
    external_update(phase['settings'], 'planner.milestone', 'MS-ACCEPT-01', {'record_version': 2})
    with pytest.raises(WorkflowError, match='STALE_MILESTONE'): reviewed(phase)
    assert counts(phase) == (0, 0)


def test_cannot_supersede_a_partially_executed_plan(phase, monkeypatch):
    reviewed(phase)
    with monkeypatch.context() as m:
        m.setattr(phase['source'], 'link', lambda *a: (_ for _ in ()).throw(SourceFailure('RESOURCE_CONFLICT')))
        phase['service'].resume(phase['ref'])
    with pytest.raises(WorkflowError, match='PARTIAL_EXECUTION_REQUIRES_RECONCILIATION'):
        phase['service'].prepare(phase['run'].run_id, 'revision', supersedes=phase['ref'])
    assert counts(phase) == (1, 0)


def test_touchless_analysis_cannot_prepare(phase):
    with phase['store'].transaction(write=True) as data:
        run = data.runs[phase['run'].run_id]
        run.recommendation.policy_path = 'touchless_eligible'
        run.recommendation.requires_human_review = False
    with pytest.raises(WorkflowError, match='ANALYSIS_NOT_EXECUTABLE'):
        phase['service'].prepare(phase['run'].run_id, 'touchless')
    assert not phase['source'].calls


def test_no_generic_or_new_agent_tool_or_source_authority():
    import ast
    root = Path('src/program_coordinator')
    for file in ['agents.py', 'harness.py', 'mcp.py', 'controls.py', 'sources.py', 'policy.py']:
        text = (root / file).read_text()
        assert 'ExecutionService' not in text and 'HumanDecisionGateway' not in text
        assert 'demo-engineer-local-only' not in text
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom):
                assert node.module not in {'infrastructure.source_gateway', 'application.execution'}
    gateway = ast.parse((root / 'infrastructure/source_gateway.py').read_text())
    assert not any(isinstance(n, ast.ImportFrom) and n.module and
                   (n.module.startswith('mock_enterprise.db') or n.module == 'agents') for n in ast.walk(gateway))


def test_serialized_role_fields_are_never_approval_inputs(phase):
    from program_coordinator.application.execution_models import ProposalRef
    with pytest.raises(ValidationError): ProposalRef.model_validate(phase['ref'].model_dump() | {'role': 'engineer'})


def test_concurrent_execution_is_excluded_before_any_write(phase):
    reviewed(phase)
    with phase['store'].execution_lock():
        with pytest.raises(WorkflowError, match='EXECUTION_BUSY'):
            phase['service'].resume(phase['ref'])
    assert not phase['source'].calls


@pytest.mark.parametrize('failure', ['timeout', 'server_error', 'invalid_json', 'redirect'])
def test_http_gateway_never_automatically_retries_writes(failure):
    from mock_enterprise.schemas import JobInput
    calls = []
    def respond(request):
        calls.append(request)
        if failure == 'timeout': raise httpx.ReadTimeout('Private provider text must not be stored', request=request)
        if failure == 'server_error': return httpx.Response(503, text='Private upstream text')
        if failure == 'invalid_json': return httpx.Response(201, text='Not JSON')
        return httpx.Response(302, headers={'location': 'https://example.com'})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        source = SourceGateway(demo_mode=True, http_client=client)
        with pytest.raises(SourceFailure) as caught:
            source.schedule(JobInput(plan_id='plan_test', approval_id='decision_test'), 'exact_key')
    assert len(calls) == 1 and 'Private' not in str(caught.value)
    if failure != 'redirect': assert caught.value.unknown


def test_actual_source_planner_transaction_failure_preserves_lab_and_recovers(phase, monkeypatch):
    reviewed(phase)
    original = Store.update
    def fail_planner(self, kind, *args, **kwargs):
        if kind == 'planner.milestone':
            raise BusinessError(409, 'RESOURCE_CONFLICT', 'Isolated test-only transaction failure.')
        return original(self, kind, *args, **kwargs)
    with monkeypatch.context() as m:
        m.setattr(Store, 'update', fail_planner)
        result = phase['service'].resume(phase['ref'])
    assert result.status == 'partially_executed' and counts(phase) == (1, 0)
    assert result.steps[0].verification == 'matched' and result.steps[1].status == 'failed'
    assert phase['service'].resume(phase['ref']).status == 'completed_execution'
    assert [c[0] for c in phase['source'].calls] == ['schedule', 'link', 'link']
    assert counts(phase) == (1, 1)


def test_source_staleness_race_at_write_is_denied_transactionally(phase, monkeypatch):
    reviewed(phase)
    original = phase['source'].schedule
    def racing(*args):
        # Change after host preflight, immediately before the source transaction.
        external_update(phase['settings'], 'manufacturing.unit', 'UNIT-B-017',
                        {'restrictions': ['engineering_hold'], 'content_version': 2})
        return original(*args)
    monkeypatch.setattr(phase['source'], 'schedule', racing)
    result = phase['service'].resume(phase['ref'])
    assert result.status == 'stale' and result.steps[0].status == 'failed'
    assert counts(phase) == (0, 0)


def test_protected_source_fields_remain_unchanged_after_execution(phase):
    paths = ['/engineering/requirements/REQ-042-V1', '/engineering/requirements/REQ-042-V2',
             '/engineering/acceptance-criteria/CRIT-BASE-V1', '/manufacturing/lots/LOT-4491',
             '/manufacturing/lots/LOT-4492', '/erp/orders/ORD-1204', '/validation/results/RES-SHORT-B']
    before = {p: get(phase['client'], p) for p in paths}
    reviewed(phase)
    assert phase['service'].resume(phase['ref']).status == 'completed_execution'
    assert {p: get(phase['client'], p) for p in paths} == before


def test_compatibility_proposal_status_remains_an_execution_gate(phase):
    reviewed(phase)
    with phase['store'].transaction(write=True) as data:
        data.proposal_status[proposal_key(phase['ref'])] = 'superseded'
    with pytest.raises(WorkflowError, match='PROPOSAL_NOT_CURRENT'): phase['service'].resume(phase['ref'])
    assert not phase['source'].calls


def test_source_read_failure_between_steps_surfaces_partial_attention(phase, monkeypatch):
    from program_coordinator.application.execution_models import SourceReadFailure
    reviewed(phase)
    original = phase['source'].schedule
    original_read = phase['source'].read.get_plan
    def lose_read_after_booking(*args):
        receipt = original(*args)
        monkeypatch.setattr(phase['source'].read, 'get_plan',
                            lambda *a: (_ for _ in ()).throw(SourceReadFailure('SOURCE_READ_FAILED')))
        return receipt
    monkeypatch.setattr(phase['source'], 'schedule', lose_read_after_booking)
    result = phase['service'].resume(phase['ref'])
    assert result.status == 'attention_required' and result.error_code == 'SOURCE_READ_FAILED'
    assert result.steps[0].status == 'succeeded' and result.steps[0].verification == 'matched'
    assert counts(phase) == (1, 0)
    monkeypatch.setattr(phase['source'].read, 'get_plan', original_read)
    assert phase['service'].resume(phase['ref']).status == 'completed_execution'
    assert len(phase['source'].calls) == 2
