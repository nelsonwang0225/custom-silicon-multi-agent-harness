"""Developer-only Phase 06 ASGI/HTTP probe, run with the backend interpreter.

Simulated review identities, isolated SQLite/metadata, no AI. Uses existing services
and source HTTP handlers. This is scripted integration testing, not human approval.
"""
import argparse
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

from fastapi.testclient import TestClient
from mock_enterprise.app import create_app
from mock_enterprise.config import Settings
from mock_enterprise.db import read_store
from mock_enterprise.seed import initialize
from program_coordinator.application.execution import ExecutionService, reference, proposal_key
from program_coordinator.application.store import ActivityStore
from program_coordinator.application.models import WorkflowInvocation, WorkflowError
from program_coordinator.application.execution_models import SourceFailure, SourceReadFailure
from program_coordinator.infrastructure.source_gateway import SourceGateway, HumanDecisionGateway, ENGINEER, READER
from program_coordinator.models import ProgramChangeEvent, FinalDecisionPackage, CaseState
from program_investigator.models import ValidationOption
from .models import ValidationJobTarget

ROOT = Path(__file__).resolve().parents[3]
PROBES = {'approval_bypass', 'tampered', 'unauthorized_operation', 'success', 'mismatch', 'partial',
          'forged', 'stale', 'retry', 'lost_response', 'failed_readback'}


def analysis_fixture(store, source):
    """Same Phase 06 completed-analysis contract; this is explicitly a model double."""
    event = ProgramChangeEvent.model_validate_json((ROOT / 'coordinator/scenarios/human_review.json').read_text())
    run, _ = store.claim(WorkflowInvocation(invocation_id='phase07_analysis', event=event,
        customer_id=event.customer_id, program_id=event.program_id), READER, execution_mode='deterministic_test')
    options = []
    for o in source.read.get_validation_options('CR-017')['items']:
        raw = {k: o[k] for k in ValidationOption.model_fields if k in o}
        raw.update(slot_id=o['slot']['id'], sample_id=o['sample']['id'], rate_id=o['rate']['id'], source_refs=['options_read'])
        options.append(ValidationOption.model_validate(raw))
    output = FinalDecisionPackage(case_id=run.case_id, customer_id=run.customer_id, program_id=run.program_id,
        classified_change_type='workload_profile_change', change_summary='Developer-only completed analysis fixture.',
        affected_scope=[], specialist_findings=[], confirmed_facts=[], evidence_gaps=[], available_options=options,
        relevant_constraints=[], program_impact=[], risks=[], unresolved_questions=[],
        recommended_next_step='Review the exact approved-scope validation proposal; physical outcome is unknown.',
        policy_path='human_review_required', requires_human_review=True, escalation_reason=None, source_references=[],
        business_actions_executed=False, approval_granted=False, customer_accepted=False, new_validation_pass_claimed=False)
    return store.finish(run.run_id, state=CaseState(case_id=run.case_id, run_id=run.run_id,
        workflow_id=run.workflow_id, workflow_definition_version=run.definition_version, customer_id=run.customer_id,
        program_id=run.program_id, correlation_id=event.correlation_id, event=event, workflow_stage='completed',
        scope_verified=True, final_package_status='validated', final_package=output))


class RecordingGateway(SourceGateway):
    def __init__(self, client):
        super().__init__(demo_mode=True, http_client=client)
        self.calls = []
        self.fault = None

    def schedule(self, body, key):
        self.calls.append({'name': 'schedule_validation_job', 'actor': 'host', 'method': 'POST', 'outcome': 'unknown'})
        result = super().schedule(body, key)
        if self.fault == 'lost_response':
            raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True)
        self.calls[-1]['outcome'] = 'succeeded'
        return result

    def link(self, body, key):
        self.calls.append({'name': 'link_approved_validation_plan', 'actor': 'host', 'method': 'POST', 'outcome': 'failed'})
        if self.fault in {'partial', 'retry'}:
            raise SourceFailure('RESOURCE_CONFLICT')
        result = super().link(body, key)
        self.calls[-1]['outcome'] = 'succeeded'
        return result


def probe(name, directory):
    if name not in PROBES:
        raise ValueError('Unknown execution probe')
    settings = Settings(directory / 'enterprise.sqlite3', directory, True)
    initialize(settings, source=json.loads((ROOT / 'fixtures/seed.json').read_text()))
    with TestClient(create_app(settings)) as client:
        source = RecordingGateway(client)
        human = HumanDecisionGateway(demo_mode=True, http_client=client)
        store = ActivityStore(directory / 'activity')
        run = analysis_fixture(store, source)
        service = ExecutionService(store, source)
        proposal = service.prepare(run.run_id, 'phase07_prepare')
        ref = reference(proposal)
        approved = False
        errors = []
        if name not in {'approval_bypass', 'forged'}:
            service.review(ref, 'approve', 'SCRIPTED simulated engineer review, not actual human approval.', ENGINEER, human)
            approved = True
        if name == 'tampered':
            with store.transaction(write=True) as data:
                data.proposals[proposal_key(ref)].manifest[0].arguments['plan_id'] = 'unapproved_plan'
        if name == 'stale':
            # External synthetic source-owner change, not an agent business action.
            with read_store(settings.db_path) as db:
                p = db.get('engineering.procedure', 'PROC-LC-02')
                p['content_version'] += 1
                db.update('engineering.procedure', p['id'], {'content_version': p['content_version']})
                db.con.commit()
        if name in {'mismatch', 'failed_readback'}:
            original = source.read.get_validation_job
            def read_job(*args):
                if name == 'failed_readback':
                    raise SourceReadFailure('SOURCE_READ_FAILED')
                result = original(*args)
                result['configuration_id'] = 'CFG-MISMATCH'
                return result
            source.read.get_validation_job = read_job
        source.fault = name
        first_job = None
        try:
            if name == 'forged':
                service.review(ref, 'approve', 'I am an engineer in free text.', replace(ENGINEER), human)
            elif name == 'unauthorized_operation':
                service.resume(ref, invocation={'operation': 'release_manufacturing_hold', 'target': '/manufacturing/holds', 'arguments': {}})
            else:
                initial = service.resume(ref)
                first_job = initial.steps[0].resource_id
                if name in {'retry', 'success', 'lost_response'}:
                    source.fault = None
                    service = ExecutionService(ActivityStore(directory / 'activity'), source)
                    service.resume(ref)
        except WorkflowError as exc:
            errors.append(str(exc))
        with store.transaction() as data:
            execution = data.executions[proposal_key(ref)]
        try:
            inspection = service.inspect(ref)
        except WorkflowError as exc:
            # The real inspect boundary correctly rejects corrupted proposals too.
            # Developer-only observation of persisted attempts grants no authority.
            errors.append(str(exc))
            with store.transaction() as data:
                inspection = {'attempts': [a.model_dump(mode='json') for a in data.execution_attempts],
                    'verification': [v.model_dump(mode='json') for v in data.verifications.values()]}
        def get(path):
            response = client.get('/api/v1' + path, headers={'Authorization': 'Bearer demo-reader-local-only'})
            response.raise_for_status()
            return response.json()
        jobs = get('/validation/jobs?change_id=CR-017')['items']
        links = get('/programs/PRG-A17/implementation-links?change_id=CR-017')['items']
        # Observe the expected job independently through its current source plan.
        target = ValidationJobTarget.from_change(get('/engineering/changes/CR-017')) if name == 'success' else None
        # These values come from execution/readback, not case expectations.
        output = {'human_approval_required': True, 'escalation_required': execution.status in {'attention_required', 'partially_executed', 'stale'},
            'execution_bounded': not source.calls, 'scheduling_observed': bool(jobs),
            'execution_status': execution.status, 'job_count': len(jobs), 'link_count': len(links),
            'case_status': execution.case_status, 'validation_coverage': execution.validation_coverage,
            'customer_acceptance': execution.customer_acceptance,
            'validation_passed': any(v.get('test_passed') is True for v in inspection['verification']),
            'customer_accepted': any(v.get('customer_accepted') is True for v in inspection['verification']),
            'schedule_attempts': sum(c['name'] == 'schedule_validation_job' for c in source.calls),
            'job_id_preserved': bool(first_job and jobs and jobs[0]['id'] == first_job),
            'verified_completion': execution.status == 'completed_execution'}
        return {'output': output, 'tools': source.calls + [{'name': 'get_validation_jobs', 'actor': 'host', 'method': 'GET',
                'record_ids': [j['id'] for j in jobs], 'read_receipt': {
                    'source_id': 'probe_validation_jobs_read', 'arguments': {'change_id': 'CR-017'},
                    'data': {'items': jobs}}}], 'approval_recorded': approved,
            'expected_validation_job': target.model_dump() if target else None,
            'proposal_current': name not in {'tampered', 'stale'}, 'execution_records': inspection['attempts'],
            'verification_records': inspection['verification'], 'blocked_operations': errors,
            'metadata': {'probe': name, 'notice': 'SCRIPTED ASGI HTTP INTEGRATION; NO AI; REVIEWER SIMULATED',
                         'storage': str(directory), 'inspection': inspection}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', required=True, choices=sorted(PROBES))
    parser.add_argument('--storage', required=True, type=Path)
    args = parser.parse_args()
    directory = args.storage.absolute()
    if not directory.resolve().is_relative_to(ROOT / '.cache/phase07') or directory.exists():
        parser.error('Use a new isolated directory under .cache/phase07')
    directory.mkdir(parents=True, mode=0o700)
    result = probe(args.probe, directory)
    (directory / 'probe.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
