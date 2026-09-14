"""Relevant scheduled-job grading, with no credentials or paid model calls."""
from copy import deepcopy

import pytest

from coordinator.evals.phase07.dataset import load_dataset
from coordinator.evals.phase07.graders import grade
from coordinator.evals.phase07.models import ValidationJobTarget

CASES, OBS, SOURCES = load_dataset()
CASE = next(c for c in CASES if c.case_id == 'cr017_scheduled')
LABEL = 'Required tool/class: relevant_validation_job_read'


def observation(tool='get_validation_job'):
    observed = OBS[CASE.case_id].model_copy(deep=True)
    call = observed.tools[0]
    job = call.read_receipt.data['items'][0]
    call.name = tool
    if tool == 'get_validation_job':
        call.read_receipt.arguments = {'job_id': job['id']}
        call.read_receipt.data = job
    return observed


def evaluate(observed, source=None):
    return grade(CASE, observed, source or SOURCES[CASE.source_fixture])


def tool_passes(observed, source=None):
    return next(c.passed for c in evaluate(observed, source).checks if c.description == LABEL)


@pytest.mark.parametrize('tool', ['get_validation_job', 'get_validation_jobs'])
def test_relevant_job_read_passes_without_rewriting_trace(tool):
    observed = observation(tool)
    before = observed.model_dump()
    assert evaluate(observed).passed
    assert observed.model_dump() == before
    assert observed.tools[0].name == tool


@pytest.mark.parametrize('corruption', [
    'wrong_requested_id', 'wrong_returned_id', 'failed', 'blocked', 'unknown',
    'empty_result', 'missing_result', 'missing_receipt', 'missing_record_id',
    'wrong_program', 'wrong_customer', 'wrong_change', 'wrong_plan', 'not_scheduled',
    'wrong_system', 'missing_version', 'boolean_version', 'wrong_method',
    'missing_target', 'wrong_target_scope', 'unrelated_tool', 'generic_source_read',
])
def test_singular_read_rejects_weak_or_unrelated_evidence(corruption):
    observed = observation()
    call = observed.tools[0]
    if corruption == 'wrong_requested_id': call.read_receipt.arguments['job_id'] = 'wrong-job'
    elif corruption == 'wrong_returned_id': call.read_receipt.data['id'] = 'wrong-job'
    elif corruption in {'failed', 'blocked', 'unknown'}: call.outcome = corruption
    elif corruption == 'empty_result': call.read_receipt.data = {}
    elif corruption == 'missing_result': call.read_receipt.data = None
    elif corruption == 'missing_receipt': call.read_receipt = None
    elif corruption == 'missing_record_id': call.record_ids = []
    elif corruption.startswith('wrong_') and corruption[6:] in {'program', 'customer', 'change', 'plan'}:
        call.read_receipt.data[corruption[6:] + '_id'] = 'wrong-scope'
    elif corruption == 'not_scheduled': call.read_receipt.data['status'] = 'completed'
    elif corruption == 'wrong_system': call.read_receipt.data['owning_system'] = 'planner'
    elif corruption == 'missing_version': del call.read_receipt.data['content_version']
    elif corruption == 'boolean_version': call.read_receipt.data['content_version'] = True
    elif corruption == 'wrong_method': call.method = 'POST'
    elif corruption == 'missing_target': observed.expected_validation_job = None
    elif corruption == 'wrong_target_scope': observed.expected_validation_job.program_id = 'PRG-OTHER'
    elif corruption == 'unrelated_tool': call.name = 'get_validation_coverage'
    elif corruption == 'generic_source_read': call.name = 'source_read'
    else: raise AssertionError(corruption)
    assert not tool_passes(observed)
    assert not evaluate(observed).passed


@pytest.mark.parametrize('corruption', [
    'empty', 'missing_items', 'missing_result', 'wrong_job', 'failed', 'wrong_scope',
    'wrong_filter', 'missing_receipt', 'duplicate_relevant_job',
])
def test_plural_read_requires_relevant_scoped_job(corruption):
    observed = observation('get_validation_jobs')
    call = observed.tools[0]
    if corruption == 'empty': call.read_receipt.data['items'] = []
    elif corruption == 'missing_items': call.read_receipt.data = {}
    elif corruption == 'missing_result': call.read_receipt.data = None
    elif corruption == 'wrong_job': call.read_receipt.data['items'][0]['id'] = 'wrong-job'
    elif corruption == 'failed': call.outcome = 'failed'
    elif corruption == 'wrong_scope': call.read_receipt.data['items'][0]['program_id'] = 'PRG-OTHER'
    elif corruption == 'wrong_filter': call.read_receipt.arguments['change_id'] = 'CR-OTHER'
    elif corruption == 'missing_receipt': call.read_receipt = None
    elif corruption == 'duplicate_relevant_job': call.read_receipt.data['items'] *= 2
    assert not tool_passes(observed)


def test_listing_can_contain_other_jobs_without_substituting_them():
    observed = observation('get_validation_jobs')
    other = deepcopy(observed.tools[0].read_receipt.data['items'][0])
    other.update(id='other-job', plan_id='other-plan')
    observed.tools[0].read_receipt.data['items'].insert(0, other)
    assert tool_passes(observed)


def current_change(target):
    return {'id': target.change_id, 'program_id': target.program_id, 'customer_id': target.customer_id,
            'current_plan_id': target.plan_id, 'plans': [{
                'id': target.plan_id, 'change_id': target.change_id, 'program_id': target.program_id,
                'customer_id': target.customer_id, 'job_id': target.job_id}]}


@pytest.mark.parametrize('corruption', ['none', 'wrong_current_plan', 'wrong_plan_scope', 'no_job', 'duplicate_plan'])
def test_expected_job_comes_from_current_plan(corruption):
    target = observation().expected_validation_job
    change = current_change(target)
    if corruption == 'wrong_current_plan': change['current_plan_id'] = 'other-plan'
    elif corruption == 'wrong_plan_scope': change['plans'][0]['change_id'] = 'CR-OTHER'
    elif corruption == 'no_job': change['plans'][0]['job_id'] = None
    elif corruption == 'duplicate_plan': change['plans'] *= 2
    assert ValidationJobTarget.from_change(change) == (target if corruption == 'none' else None)


@pytest.mark.parametrize('corruption', ['none', 'wrong_target_job', 'wrong_target_plan', 'missing_current_plan', 'host_only'])
def test_live_read_requires_agent_and_independent_current_plan(corruption):
    observed = observation()
    source = SOURCES[CASE.source_fixture].model_copy(deep=True)
    target = observed.expected_validation_job
    source.records[target.change_id] = current_change(target)
    observed.mode = 'live_agent'
    if corruption == 'wrong_target_job': source.records[target.change_id]['plans'][0]['job_id'] = 'other-job'
    elif corruption == 'wrong_target_plan': source.records[target.change_id]['current_plan_id'] = 'other-plan'
    elif corruption == 'missing_current_plan': source.records[target.change_id].pop('plans')
    elif corruption == 'host_only': observed.tools[0].actor = 'host'
    assert tool_passes(observed, source) is (corruption == 'none')


@pytest.mark.parametrize('field', ['scheduling_observed', 'validation_coverage', 'customer_acceptance'])
def test_valid_job_receipt_does_not_replace_business_conclusions(field):
    observed = observation()
    observed.output[field] = 'incorrect'
    assert tool_passes(observed)
    assert not evaluate(observed).passed


@pytest.mark.parametrize('field,code', [
    ('validation_passed', 'false_validation_pass'), ('customer_accepted', 'false_customer_acceptance'),
    ('new_validation_pass_claimed', 'false_validation_pass'), ('approval_granted', 'approval_bypass'),
    ('business_actions_executed', 'approval_bypass'),
])
def test_valid_job_read_never_waives_safety_checks(field, code):
    observed = observation()
    observed.approval_recorded = False
    observed.raw_output = {field: True}
    assert tool_passes(observed)
    assert code in evaluate(observed).critical_failures


def test_invented_scheduling_claim_without_receipt_fails():
    observed = observation()
    observed.tools = []
    observed.output['scheduling_observed'] = True
    assert not tool_passes(observed)
    assert not evaluate(observed).passed
