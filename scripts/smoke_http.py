#!/usr/bin/env python3
"""Scripted HTTP-only business integration; never imports service/database/fixtures."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

import httpx

LABEL = 'SCRIPTED MOCK-SYSTEM INTEGRATION TEST — NO AI INFERENCE; ENGINEER IDENTITY IS SIMULATED.'
PROJECT = Path(__file__).resolve().parents[1]
ROLES = {role: {'Authorization': f'Bearer demo-{role}-local-only'} for role in ('automation', 'engineer', 'reader')}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


class Smoke:
    def __init__(self, url, change_id):
        parsed = urlparse(url)
        check(parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost') and not parsed.username and not parsed.password,
              'Smoke targets must be loopback HTTP URLs without credentials.')
        self.client = httpx.Client(base_url=url.rstrip('/') + '/api/v1', timeout=10, follow_redirects=False, trust_env=False)
        self.change_id = change_id

    def close(self):
        self.client.close()

    def get(self, path):
        response = self.client.get(path, headers=ROLES['automation'])
        check(response.status_code == 200, f'GET {path}: HTTP {response.status_code}')
        return response.json()

    def post(self, path, body, key, role='automation', expected=201):
        response = self.client.post(path, json=body, headers={**ROLES[role], 'Idempotency-Key': key, 'X-Correlation-ID': 'scripted-http-smoke'})
        check(response.status_code == expected, f'POST {path}: expected {expected}, received {response.status_code}, code={response.json().get("error", {}).get("code")}')
        return response

    def baseline(self):
        change = self.get(f'/engineering/changes/{self.change_id}')
        program = self.get('/programs/' + change['program_id'])
        milestone = self.get(f'/programs/{program["id"]}/milestones/{change["milestone_id"]}')
        order = self.get('/erp/orders/' + change['order_id'])
        config = self.get('/engineering/configurations/' + change['configuration_id'])
        requirements = [self.get('/engineering/requirements/' + change[k]) for k in ('baseline_requirement_revision_id', 'proposed_requirement_revision_id')]
        coverage = self.get('/validation/coverage?change_id=' + self.change_id)
        samples = self.get('/validation/samples?program_id=' + program['id'])
        units = [self.get('/manufacturing/units/' + s['unit_id']) for s in samples['items']]
        lots = [self.get('/manufacturing/lots/' + u['source_lot_id']) for u in units]
        documents = self.get('/engineering/documents?program_id=' + program['id'])
        for document in documents['items']:
            check('SYNTHETIC' in self.get('/engineering/documents/' + document['id'])['content'], 'Missing synthetic document label')
        self.get('/erp/cost-rates?program_id=' + program['id'])
        check(not change['plans'], 'Baseline contains implementation plans; reset the demo first.')
        check(not self.get('/validation/jobs?change_id=' + self.change_id)['items'], 'Baseline contains jobs.')
        check(not self.get(f'/programs/{program["id"]}/implementation-links?change_id={self.change_id}')['items'], 'Baseline contains planner links.')
        check(not coverage['coverage_satisfied'], 'Seed unexpectedly satisfies target coverage.')
        check(milestone['current_forecast_at'] == milestone['baseline_at'], 'Seed forecast differs from baseline.')
        return dict(change=change, program=program, milestone=milestone, order=order, config=config,
                    requirements=requirements, coverage=coverage, samples=samples, units=units, lots=lots, documents=documents)

    def workflow(self):
        baseline = self.baseline()
        change, program = baseline['change'], baseline['program']
        choices = self.get('/validation/options?change_id=' + self.change_id)['items']
        feasible = [o for o in choices if o['resource_eligible'] and o['approval_eligible'] and o['meets_deadline']]
        check(bool(feasible), 'No policy-compliant option meets the deadline.')
        selected = min(feasible, key=lambda o: (o['cost_cents'], o['timing']['review_ready_at'], o['slot']['id'], o['sample']['id']))
        body = dict(expected_change_content_version=change['content_version'], target_requirement_revision_id=change['proposed_requirement_revision_id'],
                    configuration_id=selected['configuration_id'], procedure_id=selected['procedure_id'], sample_id=selected['sample']['id'],
                    slot_id=selected['slot']['id'], milestone_id=selected['milestone_id'],
                    assessment=dict(facts=[dict(text='Customer requested supplemental workload evidence.',
                                               source_refs=[dict(resource_type='engineering.change', resource_id=self.change_id)])],
                                    evidence_gaps=['No complete applicable result is currently recorded.'],
                                    unresolved_questions=['The outcome of future testing and review is unknown.']),
                    expected_source_versions=selected['expected_source_versions'])
        plan = self.post(f'/engineering/changes/{self.change_id}/plans', body, 'smoke-plan').json()
        decision_body = dict(decision='approve', expected_plan_version=plan['plan_version'], expected_plan_digest=plan['plan_digest'],
                             reason='SCRIPTED simulated engineer approval of the exact supplemental procedure and delegated spend.')
        denied = self.post(f'/engineering/plans/{plan["id"]}/decisions', decision_body, 'smoke-self-approval', expected=403)
        check(denied.json()['error']['code'] == 'FORBIDDEN_ROLE', 'Self-approval was not blocked by role.')
        denied = self.post('/validation/jobs', dict(plan_id=plan['id'], approval_id='nonexistent-demo-approval'), 'smoke-booking', expected=404)
        check(denied.json()['error']['code'] == 'NOT_FOUND', 'Unapproved booking was not rejected.')
        approval = self.post(f'/engineering/plans/{plan["id"]}/decisions', decision_body, 'smoke-engineer', 'engineer').json()
        job_body = dict(plan_id=plan['id'], approval_id=approval['id'])
        job = self.post('/validation/jobs', job_body, 'smoke-booking').json()
        check(self.get('/engineering/plans/' + plan['id'])['execution_state'] == 'lab_scheduled_pending_planner', 'Missing partial execution state.')
        link_path = f'/programs/{program["id"]}/implementation-links'
        link_body = dict(**job_body, job_id=job['id'], expected_milestone_record_version=baseline['milestone']['record_version'])
        linked = self.post(link_path, link_body, 'smoke-link').json()
        for path, payload, key, original in [('/validation/jobs', job_body, 'smoke-booking', job), (link_path, link_body, 'smoke-link', linked)]:
            replay = self.post(path, payload, key)
            check(replay.json() == original and replay.headers.get('Idempotency-Replayed') == 'true', 'Idempotent replay differs.')
            duplicate = self.post(path, payload, key + '-new-key', expected=409)
            check(duplicate.json()['error']['code'] == 'ACTION_ALREADY_RECORDED', 'New key duplicated an action.')
        receipt = dict(baseline=baseline, plan=plan, approval=approval, job=job, link=linked)
        self.verify(receipt)
        print(json.dumps({'plan_id': plan['id'], 'approval_id': approval['id'], 'job_id': job['id'],
                          'reservation_id': job['reservation_id'], 'link_id': linked['id'], 'task_id': linked['task_id'],
                          'forecast_at': linked['forecast_at'], 'status': 'scheduled_awaiting_execution',
                          'unapproved_booking': 'blocked', 'automation_self_approval': 'blocked', 'idempotency': 'PASS'}, indent=2))
        return receipt

    def verify(self, receipt):
        baseline, plan, approval, job, linked = (receipt[k] for k in ('baseline', 'plan', 'approval', 'job', 'link'))
        program = baseline['program']['id']
        check(self.get('/engineering/decisions/' + approval['id']) == approval, 'Approval did not persist exactly.')
        check(self.get('/validation/jobs/' + job['id']) == job, 'Job or reservation did not persist exactly.')
        jobs = self.get('/validation/jobs?change_id=' + self.change_id)['items']
        links = self.get(f'/programs/{program}/implementation-links?change_id={self.change_id}')['items']
        check(jobs == [job] and links == [linked], 'Duplicate/missing job, reservation, link or task.')
        current_plan = self.get('/engineering/plans/' + plan['id'])
        check(current_plan['execution_state'] == 'scheduled_awaiting_execution' and current_plan['plan_digest'] == plan['plan_digest'], 'Plan execution state/digest mismatch.')
        milestone = self.get(f'/programs/{program}/milestones/{baseline["milestone"]["id"]}')
        check(milestone['baseline_at'] == baseline['milestone']['baseline_at'], 'Baseline milestone changed.')
        check(milestone['current_forecast_at'] == job['timing']['review_ready_at'] == linked['forecast_at'], 'Conditional forecast mismatch.')
        check(milestone['forecast_status'] == 'conditional_on_test_and_review', 'Forecast is not explicitly conditional.')
        check(len(milestone['dependencies']) == len(baseline['milestone']['dependencies']) + 1, 'Dependency count mismatch.')
        check(self.get('/erp/orders/' + baseline['order']['id']) == baseline['order'], 'Customer commitment/order changed.')
        for requirement in baseline['requirements']:
            check(self.get('/engineering/requirements/' + requirement['id']) == requirement, 'Requirement baseline changed.')
        for unit in baseline['units']:
            check(self.get('/manufacturing/units/' + unit['id']) == unit, 'Manufacturing unit changed.')
        for lot in baseline['lots']:
            check(self.get('/manufacturing/lots/' + lot['id']) == lot, 'Manufacturing lot changed.')
        check(self.get('/validation/coverage?change_id=' + self.change_id) == baseline['coverage'], 'Scheduling changed evidence/results.')
        audit = self.get('/audit/events?change_id=' + self.change_id)['items']
        check(len([e for e in audit if e['outcome'] == 'succeeded']) == 4, 'Expected four audited business mutations.')
        check(any(e['outcome'] == 'denied' for e in audit) and any(e['outcome'] == 'replay' for e in audit), 'Denial/replay audit missing.')
        check('Bearer' not in json.dumps(audit) and 'local-only' not in json.dumps(audit), 'Role selectors leaked into audit.')


def main():
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--change-id', default='CR-017')
    parser.add_argument('--mode', choices=['workflow', 'verify', 'baseline'], default='workflow')
    parser.add_argument('--receipt', type=Path, default=PROJECT / '.cache/smoke-receipt.json')
    args = parser.parse_args()
    check(args.receipt.absolute().resolve().is_relative_to(PROJECT), 'Receipt must stay inside this project.')
    print(LABEL)
    smoke = Smoke(args.base_url, args.change_id)
    try:
        if args.mode == 'workflow':
            receipt = smoke.workflow()
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
        elif args.mode == 'verify':
            smoke.verify(json.loads(args.receipt.read_text()))
        else:
            current = smoke.baseline()
            if args.receipt.exists():
                check(current == json.loads(args.receipt.read_text())['baseline'], 'Reset baseline differs from original HTTP reads.')
        print('PASS: ' + args.mode + ' verified through real HTTP.')
    finally:
        smoke.close()


if __name__ == '__main__':
    main()
