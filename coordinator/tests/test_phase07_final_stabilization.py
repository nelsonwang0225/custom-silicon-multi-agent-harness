"""Saved-failure regressions. Scripted model responses, never paid inference.

Integration cases use the actual harness and scoped MCP/HTTP sources. The
scripted runner tests contracts/routing, not a model's future semantic choices.
"""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from agents import AgentOutputSchema
from pydantic import ValidationError

from coordinator.evals.phase07.dataset import ROOT, load_dataset
from coordinator.evals.phase07.graders import grade
from coordinator.evals.phase07.live import adapt_artifacts, event_for, local_sources
from program_coordinator.agents import build_agent, OUTPUTS
from program_coordinator.controls import HarnessConfig, HarnessError
from program_coordinator.models import (CaseState, CoordinatorReview, FinalDecisionPackage, Finding,
    ProgramChangeEvent, QuestionResolution, SourceFact, SpecialistResult, StatusInspectionScope, TriageDecision,
    ValidationClarificationResult, ValidationEvidenceAssessment, WorkRequest, scoped_work_output)
from program_coordinator.policy import determine_policy
from program_coordinator.sources import canonical, validate_assessment
from program_coordinator.status_inspection import read_only_status_request, status_scope_error, validate_status_reads
from helpers import assessment, fact, final, harness, request, seed_sources, triage
from test_orchestration import MemorySession, wired

SAVED = json.loads((Path(__file__).parent / 'data/phase07_final_failures.json').read_text())
CASES, _, SOURCES = load_dataset()
BY_ID = {c.case_id: c for c in CASES}


def clarification_request(h):
    prior = next(r for r in h.state.completed_assessments if isinstance(r.assessment, ValidationEvidenceAssessment))
    return WorkRequest(specialist='validation_evidence', question=SAVED['covered']['question'],
        rationale=SAVED['covered']['rationale'], focus_record_ids=['CRIT-BASE-V1'], depends_on=[],
        result_kind='validation_clarification', prior_assessment_invocation_id=prior.invocation_id)


def clarification(h, work, *, conflict=False):
    finding = fact(h, 'get_acceptance_criteria', '/scope',
        'The criteria record explicitly leaves numerical thresholds outside this scheduling phase.')
    return ValidationClarificationResult(case_id=h.state.case_id,
        summary=SAVED['covered']['rejected_output']['summary'], confidence=1.0,
        unresolved_questions=[], source_references=[next(r for r in h.state.source_references
            if r.source_id == finding.source_refs[0])], clarification_type='criteria_detail',
        question=work.question, prior_assessment_invocation_id=work.prior_assessment_invocation_id,
        findings=[finding], invalidates_prior_coverage=conflict, introduces_blocker=conflict)


def memory_clarification():
    h = seed_sources(harness(server_factory=MemorySession))
    h.state.triage = triage()
    prior = assessment(h, 'validation_evidence')
    h.state.completed_assessments = [SpecialistResult(invocation_id='work_prior', specialist='validation_evidence', assessment=prior)]
    h.state.workflow_stage = 'specialists'
    h.sources.add('get_acceptance_criteria', {'criteria_id': 'CRIT-BASE-V1'},
        {'id': 'CRIT-BASE-V1', 'content_version': 1, 'synthetic': True, 'owning_system': 'engineering',
         'program_id': 'PRG-A17', 'status': 'approved',
         'scope': 'Existing functional, power, thermal and performance limits; numerical thresholds not modeled in this scheduling phase.'},
        'validation_evidence', 'work_criteria', {}, 0)
    work = clarification_request(h)
    return h, work, clarification(h, work)


@pytest.mark.parametrize('corruption,code', [
    ('unused', 'unknown_source_reference'), ('unknown', 'unknown_source_reference'),
    ('fabricated_fact', 'source_assertion_mismatch'), ('uncited', 'uncited_source'),
    ('wrong_version', 'source_version_mismatch'), ('no_facts', 'clarification_facts_missing'),
    ('no_prior', 'clarification_prior_assessment_missing'),
])
def test_clarification_strict_source_validation(corruption, code):
    h, work, output = memory_clarification()
    if corruption in {'unused', 'unknown'}:
        output.source_references[0].source_id = corruption
    elif corruption == 'fabricated_fact': output.findings[0].facts[0].value_json = '"Invented numerical limits"'
    elif corruption == 'uncited': output.source_references = []
    elif corruption == 'wrong_version': output.source_references[0].content_version = 42
    elif corruption == 'no_facts':
        output.findings[0].basis = 'missing_information'
        output.findings[0].facts = []
    elif corruption == 'no_prior': output.prior_assessment_invocation_id = 'work_missing'
    with pytest.raises(HarnessError, match=code):
        validate_assessment(output, h.sources, None)


def test_option_provenance_clarification_accepts_exact_options_receipt():
    h = seed_sources(harness(server_factory=MemorySession))
    prior = assessment(h, 'validation_evidence')
    h.state.completed_assessments = [SpecialistResult(
        invocation_id='work_prior', specialist='validation_evidence', assessment=prior)]
    source = h.sources.latest('get_validation_options')
    finding = fact(h, 'get_validation_options', '/items/1/timing/review_ready_at',
        'The priority option is ready for review at the source-calculated time.')
    output = ValidationClarificationResult(case_id=h.state.case_id,
        summary='Exact option timing provenance.', confidence=1.0, unresolved_questions=[],
        source_references=[next(r for r in h.state.source_references if r.source_id == source['source_id'])],
        clarification_type='option_provenance', question='Verify the priority option timing.',
        prior_assessment_invocation_id='work_prior', findings=[finding],
        invalidates_prior_coverage=False, introduces_blocker=False)

    validate_assessment(output, h.sources, {source['source_id']})


def test_saved_unused_full_coverage_source_is_still_rejected():
    h, _, _ = memory_clarification()
    bad = deepcopy(SAVED['covered']['rejected_output'])
    assert bad['coverage_source_id'] == 'unused'
    # Rebind the one real criteria receipt, leaving the offending field intact.
    sid = h.sources.latest('get_acceptance_criteria')['source_id']
    old = bad['source_references'][0]['source_id']
    bad = json.loads(json.dumps(bad).replace(old, sid))
    bad['case_id'] = h.state.case_id
    bad['source_references'] = [h.state.source_references[-1].model_dump()]
    # The saved exact facts refer to the real criteria record; use the test's copy.
    h.sources.calls[-1]['data'].update(writable=False)
    with pytest.raises(HarnessError, match='unknown_source_reference'):
        validate_assessment(ValidationEvidenceAssessment.model_validate(bad), h.sources, None)


@pytest.mark.parametrize('field,value', [('coverage_status', 'sufficient'), ('coverage_source_id', 'unused'),
    ('applicable_evidence', []), ('inapplicable_evidence', []), ('eligible_options', [])])
def test_clarification_cannot_overwrite_full_assessment_fields(field, value):
    _, _, output = memory_clarification()
    with pytest.raises(ValidationError):
        ValidationClarificationResult.model_validate(output.model_dump() | {field: value})


def test_actual_sdk_schemas_bound_clarification_to_prior_full_work():
    h, work, output = memory_clarification()
    schema = scoped_work_output(h.sources.known_ids, 'reconcile', (), ['work_prior'])
    valid = dict(additional_work=[work.model_dump()], disagreements=[], unresolved_questions=[], ready_to_synthesize=True)
    schema.model_validate(valid)
    valid['additional_work'][0]['prior_assessment_invocation_id'] = 'unused'
    with pytest.raises(ValidationError): schema.model_validate(valid)
    with pytest.raises(ValidationError): scoped_work_output(h.sources.known_ids, 'triage').model_validate(
        triage([work]).model_dump())
    agent = build_agent('validation_evidence', result_kind='validation_clarification')
    sdk = AgentOutputSchema(agent.output_type)
    assert sdk.validate_json(output.model_dump_json()) == output
    assert 'coverage_source_id' not in sdk.json_schema()['properties']
    full = AgentOutputSchema(build_agent('validation_evidence').output_type).json_schema()
    assert 'coverage_source_id' in full['required']


@pytest.mark.parametrize('conflict', [False, True])
def test_clarification_persists_and_real_conflict_escalates(conflict):
    h, work, output = memory_clarification()
    prior = h.state.completed_assessments[0].model_dump_json()
    if conflict:
        # Test a genuine source-backed withdrawal, not invented numerical limits.
        h.sources.calls[-1]['data']['status'] = 'withdrawn'
        output.summary = 'The criteria source is withdrawn; the prior coverage requires engineering review.'
        output.findings = [fact(h, 'get_acceptance_criteria', '/status', 'The criteria source is withdrawn.')]
        output.invalidates_prior_coverage = True
        output.introduces_blocker = True
    snapshots = []
    h.checkpoint_callback = snapshots.append
    async def runner(*args, **kwargs): return SimpleNamespace(final_output=output)
    h.runner = runner
    invocation = h.reserve(work, 'coordinator', (), None)
    result = asyncio.run(h.execute_specialist(invocation, work))
    assert isinstance(result.assessment, ValidationClarificationResult)
    assert h.state.completed_assessments[0].model_dump_json() == prior
    assert snapshots[-1]['completed_assessments'][-1]['assessment']['clarification_type'] == 'criteria_detail'
    restored = CaseState.model_validate(snapshots[-1])
    assert isinstance(restored.completed_assessments[-1].assessment, ValidationClarificationResult)
    assert (determine_policy(h.state, h.sources).policy_path == 'escalation_required') is conflict


def test_required_full_assessment_failure_still_escalates():
    h, _ = wired([request('validation_evidence')], malformed='validation_evidence')
    state = asyncio.run(h.run())
    assert state.policy_decision.policy_path == 'escalation_required'
    assert state.requested_specialists[0].status == 'failed'


@pytest.mark.parametrize('corruption', ['question', 'prior', 'invisible_source', 'failed_read'])
def test_clarification_cannot_hide_a_failed_or_unrelated_followup(corruption):
    h, work, output = memory_clarification()
    if corruption == 'question': output.question = 'A different issue.'
    if corruption == 'prior': output.prior_assessment_invocation_id = 'work_unknown'
    if corruption == 'invisible_source':
        class InvisibleSession(MemorySession):
            def __init__(self, *args): super().__init__(*args); self.seen_sources = set()
        h.server_factory = InvisibleSession
    async def runner(*args, **kwargs):
        if corruption == 'failed_read': raise HarnessError('mcp_source_rejected')
        return SimpleNamespace(final_output=output)
    h.runner = runner
    invocation = h.reserve(work, 'coordinator', (), None)
    assert asyncio.run(h.execute_specialist(invocation, work)) is None
    assert invocation.status == 'failed'
    assert len(h.state.completed_assessments) == 1
    assert determine_policy(h.state, h.sources).policy_path == 'escalation_required'


def status_triage(h):
    change = h.intake['change']['data']
    plan = next(p for p in change['plans'] if p['id'] == change['current_plan_id'])
    value = triage([request('validation_evidence', 'Inspect the existing job and its reservation.'),
                    request('program_commercial', 'Inspect the linked Planner task and current milestone.')])
    value.classified_change_type = 'existing_case_status'
    value.status_inspection = StatusInspectionScope(workflow_id='requirement_change_analysis', intent='read_only_status',
        change_id=change['id'], program_id=change['program_id'], customer_id=change['customer_id'],
        plan_id=plan['id'], job_id=plan['job_id'], implementation_link_id=plan['implementation_link_id'],
        questions=['validation_job_status', 'planner_linkage', 'results_availability', 'customer_acceptance'])
    return value


class ScriptedRunner:
    def __init__(self, h, variant, job_tool='get_validation_job'):
        self.h, self.variant, self.job_tool = h, variant, job_tool
        self.prior = None
        self.review_count = 0

    async def __call__(self, agent, prompt, **kwargs):
        data = json.loads(prompt)
        h = self.h
        if issubclass(agent.output_type, TriageDecision):
            result = status_triage(h) if self.variant == 'scheduled' else triage([request('validation_evidence')])
        elif issubclass(agent.output_type, CoordinatorReview):
            self.review_count += 1
            resolved = []
            additional = []
            if self.variant == 'covered' and self.review_count == 1:
                additional = [clarification_request(h)]
            elif self.variant == 'covered' and data['unresolved_questions']:
                criteria = fact(h, 'get_acceptance_criteria', '/scope',
                    'The criteria scope answers the requested clarification.')
                resolved = [QuestionResolution(question=data['unresolved_questions'][0],
                    resolution='The source confirms that numerical thresholds are outside this scheduling phase.',
                    supporting_facts=criteria.facts)]
            result = CoordinatorReview(additional_work=additional,
                disagreements=[], unresolved_questions=[], ready_to_synthesize=True,
                resolved_questions=resolved)
            result = agent.output_type.model_validate(result.model_dump())
        elif agent.output_type is FinalDecisionPackage:
            result = final(h, h.state.policy_decision.policy_path)
            result.recommended_next_step = 'Engineering review remains pending; customer acceptance remains pending.'
            result.confirmed_facts += [fact(h, 'get_validation_coverage', '/coverage_satisfied',
                'The source records current evidence coverage.')]
            if self.variant == 'scheduled':
                scope = h.state.triage.status_inspection
                tool = self.job_tool
                path = '/status' if tool == 'get_validation_job' else '/items/0/status'
                result.confirmed_facts += [fact(h, tool, path, 'The existing validation job is scheduled; test results remain pending.')]
        else:
            server = agent.mcp_servers[0]
            async def read(tool, **args): await server.call_tool(tool, args)
            if agent.output_type is ValidationClarificationResult:
                assert data['completed_dependencies'][0]['assessment']['coverage_status'] == 'sufficient'
                await read('get_acceptance_criteria', criteria_id='CRIT-BASE-V1')
                result = clarification(h, WorkRequest.model_validate(data['task']))
            else:
                role = next(r for r, cls in OUTPUTS.items() if cls is agent.output_type)
                if role == 'validation_evidence':
                    await read('get_validation_coverage', change_id='CR-017')
                    await read('get_requirement_revision', requirement_revision_id='REQ-042-V2')
                    if self.variant == 'scheduled':
                        scope = h.state.triage.status_inspection
                        await read(self.job_tool, **({'job_id': scope.job_id} if self.job_tool == 'get_validation_job' else {'change_id': 'CR-017'}))
                        await read('get_validation_options', change_id='CR-017')
                    else:
                        await read('get_configuration', configuration_id='CFG-B-01')
                        await read('get_acceptance_criteria', criteria_id='CRIT-BASE-V1')
                else:
                    await read('get_program_milestone', program_id='PRG-A17', milestone_id='MS-ACCEPT-01')
                    await read('get_customer_order', order_id='ORD-1204')
                    await read('get_implementation_links', program_id='PRG-A17', change_id='CR-017')
                result = assessment(h, role)
                visible = h.intake_source_ids | server.seen_sources
                result.source_references = [r for r in result.source_references if r.source_id in visible]
                if self.variant == 'covered': self.prior = result.model_dump_json()
        return SimpleNamespace(final_output=result)


@pytest.fixture(scope='module', params=['covered', 'scheduled'])
def source_service(request):
    variant = request.param
    directory = ROOT / '.cache/phase07' / ('stabilization-sources-' + uuid4().hex)
    with local_sources(BY_ID['cr017_' + variant], directory) as service:
        yield variant, service


def run_scripted(source_service, *, job_tool='get_validation_job'):
    variant, (_, url, fingerprint) = source_service
    h = harness(config=HarnessConfig(mcp_url=url), event=ProgramChangeEvent.model_validate(event_for(variant)),
                workflow_id='requirement_change_analysis')
    h.runner = ScriptedRunner(h, variant, job_tool)
    before = fingerprint()
    state = asyncio.run(h.run())
    assert before == fingerprint()
    return h, state


def test_saved_failures_reproduced_through_actual_read_only_harness(source_service, tmp_path, monkeypatch):
    import program_investigator.config as config
    monkeypatch.setattr(config, 'load_key', lambda *a, **k: pytest.fail('No credentials in offline tests'))
    variant, (backend, _, fingerprint) = source_service
    before = fingerprint()
    h, state = run_scripted(source_service)
    assert state.workflow_stage == 'completed' and state.final_package_status == 'validated'
    assert state.termination_reason is None and not state.guardrail_events
    assert state.policy_decision.policy_path == 'human_review_required'
    assert not state.final_package.business_actions_executed
    assert not state.final_package.new_validation_pass_claimed and not state.final_package.customer_accepted
    assert not state.final_package.approval_granted
    assert all(read['method'] == 'GET' and read['status'] == 200
        for c in h.sources.calls for read in c['trace']['http_reads'])
    if variant == 'covered':
        full, narrow = [r.assessment for r in state.completed_assessments]
        assert full.model_dump_json() == h.runner.prior and full.coverage_status == 'sufficient'
        assert isinstance(narrow, ValidationClarificationResult)
        assert not state.final_package.available_options and not state.blocking_issues
        assert sum(c['tool'] == 'get_validation_coverage' for c in h.sources.calls) == 1
        assert not any(c['tool'] == 'get_validation_options' for c in h.sources.calls)
        assert any(e.result_id == 'RES-FULL-B-EVAL' and e.satisfies for e in full.applicable_evidence)
        assert 'not_yet_demonstrated_for_WF-LC-V2' not in json.dumps(h.sources.latest('get_configuration')['data'])
    else:
        assert state.triage.classified_change_type == 'existing_case_status'
        assert {r.specialist for r in state.completed_assessments} == {'validation_evidence', 'program_commercial'}
        assert state.policy_decision.rule == 'existing_case_status_read_only'
        assert any(p['kind'] == 'historical_snapshot' for p in h.intake['change']['record_provenance'])
        assert h.intake['change']['data']['record_version'] == 3
    for name, value in {'case-state.json': state.model_dump(mode='json'),
        'result.json': state.final_package.model_dump(mode='json'), 'tool-calls.json': h.sources.calls,
        'report.json': {'status': 'completed', 'model': 'offline_scripted_runner', 'latency_ms': 0,
                        'usage': None, 'trace_id': 'trace_offline', 'guardrail_events': []}}.items():
        (tmp_path / name).write_text(json.dumps(value))
    case = BY_ID['cr017_' + variant]
    observed, source = adapt_artifacts(case.case_id, tmp_path, SOURCES[case.source_fixture], before=before, after=fingerprint())
    result = grade(case, observed, source)
    assert result.passed, [(c.description, c.actual, c.expected) for c in result.checks if not c.passed]
    if variant == 'scheduled':
        assert observed.output['scheduling_observed'] is True
        assert observed.output['validation_coverage'] == 'pending_test_results'
        assert observed.output['validation_passed'] is False and observed.output['customer_accepted'] is False
    with httpx.Client(trust_env=False, headers={'Authorization': 'Bearer demo-reader-local-only'}) as http:
        jobs = http.get(backend + '/api/v1/validation/jobs', params={'change_id': 'CR-017'}).json()['items']
    assert len(jobs) == int(variant == 'scheduled')
    assert before == fingerprint()


def test_plural_status_job_read_uses_same_host_check(scheduled_intake):
    h = deepcopy(scheduled_intake)
    async def intake(): pass  # Already loaded through real scoped MCP by the fixture.
    h.intake_case = intake
    h.runner = ScriptedRunner(h, 'scheduled', 'get_validation_jobs')
    state = asyncio.run(h.run())
    assert state.policy_decision.policy_path == 'human_review_required'
    assert h.sources.latest('get_validation_jobs')


@pytest.fixture(scope='module')
def completed_status(scheduled_intake):
    h = deepcopy(scheduled_intake)
    async def intake(): pass
    h.intake_case = intake
    h.runner = ScriptedRunner(h, 'scheduled')
    asyncio.run(h.run())
    return h


@pytest.mark.parametrize('corruption,role', [
    ('missing_job', 'validation_evidence'), ('wrong_job', 'validation_evidence'),
    ('wrong_program', 'validation_evidence'), ('wrong_plan', 'validation_evidence'),
    ('wrong_reservation', 'validation_evidence'), ('intake_only', 'validation_evidence'),
    ('uncited_job', 'validation_evidence'), ('missing_link', 'program_commercial'),
    ('wrong_link', 'program_commercial'), ('wrong_task', 'program_commercial'),
    ('wrong_task_program', 'program_commercial'), ('wrong_link_job', 'program_commercial'),
])
def test_status_requires_actual_matching_job_and_planner_reads(completed_status, corruption, role):
    h = deepcopy(completed_status)
    result = next(r for r in h.state.completed_assessments if r.specialist == role)
    job = h.sources.latest('get_validation_job')
    links = h.sources.latest('get_implementation_links')
    if corruption == 'missing_job': h.sources.calls.remove(job)
    elif corruption == 'wrong_job': job['data']['id'] = 'job_wrong'
    elif corruption == 'wrong_program': job['data']['program_id'] = 'PRG-OTHER'
    elif corruption == 'wrong_plan': job['data']['plan_id'] = 'plan_wrong'
    elif corruption == 'wrong_reservation': job['data']['reservation']['job_id'] = 'job_wrong'
    elif corruption == 'intake_only': job['invocation_id'] = 'intake'
    elif corruption == 'uncited_job': result.assessment.source_references = [r for r in result.assessment.source_references if r.source_id != job['source_id']]
    elif corruption == 'missing_link': h.sources.calls.remove(links)
    elif corruption == 'wrong_link': links['data']['items'][0]['id'] = 'link_wrong'
    elif corruption == 'wrong_task': links['data']['items'][0]['task']['link_id'] = 'link_wrong'
    elif corruption == 'wrong_task_program': links['data']['items'][0]['task']['program_id'] = 'PRG-OTHER'
    elif corruption == 'wrong_link_job': links['data']['items'][0]['job_id'] = 'job_wrong'
    with pytest.raises(HarnessError, match='status_inspection_'):
        validate_status_reads(result.assessment, h.sources, result.invocation_id, role)
    assert determine_policy(h.state, h.sources).policy_path == 'escalation_required'


def test_status_scope_alone_is_never_completed_investigation(scheduled_intake):
    h = deepcopy(scheduled_intake)
    h.state.triage = status_triage(h)
    assert status_scope_error(h.state, h.sources) is None
    assert determine_policy(h.state, h.sources).policy_path == 'escalation_required'
    sdk = AgentOutputSchema(scoped_work_output(h.sources.known_ids, 'triage'))
    assert sdk.validate_json(h.state.triage.model_dump_json()).classified_change_type == 'existing_case_status'


def test_repeated_identical_planner_receipts_do_not_fabricate_a_conflict(completed_status):
    h = deepcopy(completed_status)
    result = next(r for r in h.state.completed_assessments if r.specialist == 'program_commercial')
    call = h.sources.latest('get_implementation_links')
    h.sources.add(call['tool'], call['arguments'], deepcopy(call['data']), call['role'], call['invocation_id'], {}, 0)
    result.assessment.source_references.append(h.state.source_references[-1])
    validate_status_reads(result.assessment, h.sources, result.invocation_id, result.specialist)
    assert determine_policy(h.state, h.sources).policy_path == 'human_review_required'


@pytest.fixture(scope='module')
def scheduled_intake():
    # The full exact current-plan snapshot came from the saved failed intake.
    # Use an isolated source fixture for portable tests, without reading a cache.
    directory = ROOT / '.cache/phase07' / ('stabilization-intake-' + uuid4().hex)
    with local_sources(BY_ID['cr017_scheduled'], directory) as (_, url, fingerprint):
        h = harness(config=HarnessConfig(mcp_url=url), event=ProgramChangeEvent.model_validate(SAVED['scheduled']['event']))
        before = fingerprint()
        asyncio.run(h.intake_case())
        assert before == fingerprint()
        yield h


@pytest.mark.parametrize('problem', ['unknown', 'unrelated', 'missing_program', 'missing_scope', 'low_confidence',
    'wrong_job', 'wrong_plan', 'wrong_link', 'cross_program', 'different_workflow', 'no_program_specialist', 'disguised_write'])
def test_status_routing_fail_closed(scheduled_intake, problem):
    h = deepcopy(scheduled_intake)
    h.server_factory = MemorySession
    value = status_triage(h)
    if problem == 'unknown': value.classified_change_type = 'other_or_unknown'; value.status_inspection = None
    elif problem == 'unrelated': h.state.event.request_summary = 'Inspect my stock portfolio.'
    elif problem == 'missing_program': h.state.event.program_id = None; h.state.scope_verified = False
    elif problem == 'missing_scope': value.status_inspection = None
    elif problem == 'low_confidence': value.confidence = 0.4
    elif problem in {'wrong_job', 'wrong_plan', 'wrong_link'}:
        setattr(value.status_inspection, {'wrong_job': 'job_id', 'wrong_plan': 'plan_id', 'wrong_link': 'implementation_link_id'}[problem], 'wrong-id')
    elif problem == 'cross_program': value.status_inspection.program_id = 'PRG-OTHER'
    elif problem == 'different_workflow': h.state.workflow_id = 'delivery_readiness'
    elif problem == 'no_program_specialist': value.specialists_required = [value.specialists_required[0]]
    elif problem == 'disguised_write': h.state.event.request_summary = 'Inspect the CR-017 validation status and schedule a new job.'
    async def intake(): pass
    async def runner(agent, prompt, **kwargs):
        if issubclass(agent.output_type, TriageDecision): return SimpleNamespace(final_output=value)
        assert agent.output_type is FinalDecisionPackage, 'Unsafe route launched specialist work'
        return SimpleNamespace(final_output=final(h, h.state.policy_decision.policy_path))
    h.intake_case, h.runner = intake, runner
    state = asyncio.run(h.run())
    assert not state.requested_specialists and state.policy_decision.policy_path == 'escalation_required'
    assert 'triage_specialists_suppressed' in state.guardrail_events


@pytest.mark.parametrize('text,allowed', [
    (SAVED['scheduled']['event']['request_summary'], True),
    ('What is the current status of the CR-017 validation job?', True),
    ('Has the approved validation work been scheduled?', True),
    ('Are validation results available yet?', True),
    ('Is customer acceptance still pending?', True),
    ('Check the validation job. Do not schedule or approve anything.', False),  # conservative unsupported phrasing
    ('Inspect the CR-017 job; send the customer an update.', False),
    ('Inspect the CR-017 job and grant approval.', False),
    ('Inspect the CR-017 job; do not wait and execute it.', False),
    ('Inspect the CR-017 job and change the plan.', False),
])
def test_read_only_intent_admission(text, allowed):
    assert read_only_status_request(text) is allowed
