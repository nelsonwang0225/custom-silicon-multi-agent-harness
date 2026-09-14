import copy
import json
import os
import subprocess
import sys

import pytest

from mock_enterprise.config import PROJECT
from mock_enterprise.db import Store, connect
from conftest import AUTOMATION, ENGINEER, approve, book, draft, draft_body, get, link_body, post


def test_openapi_describes_actual_routes_and_typed_writes(env):
    client, _ = env
    schema = client.get('/openapi.json').json()
    operations = [(path, method, value) for path, item in schema['paths'].items() for method, value in item.items() if method in ('get', 'post')]
    business = [(path, method, value) for path, method, value in operations if path.startswith('/api/v1/')]
    assert len(business) == 58
    assert set(schema['paths']['/api/v1/manufacturing/quality-events/{event_id}']) == {'get'}
    assert sum(method == 'post' for _, method, _ in business) == 15
    assert len({o['operationId'] for _, _, o in operations}) == len(operations)
    for path, method, operation in business:
        assert operation['security']
        assert 'application/json' in operation['responses']['201' if method == 'post' else '200']['content']
        if method == 'post':
            assert any(p['name'] == 'Idempotency-Key' and p['required'] for p in operation['parameters'])
            assert 'requestBody' in operation
            assert '409' in operation['responses'] and '403' in operation['responses']
    assert schema['components']['schemas']['PlanInput']['additionalProperties'] is False
    assert client.get('/docs').status_code == 200
    assert client.get('/health').json() == {'status': 'ready', 'synthetic': True}


@pytest.mark.parametrize('document_id', ['README.md', 'seed.json', 'ACCEPTANCE_TESTS.md', '01_PLAN.md', '..%2F..%2Fdocs%2FACCEPTANCE_TESTS.md', '%2e%2e%2fseed.json'])
def test_documents_cannot_retrieve_developer_files(env, document_id):
    client, _ = env
    result = client.get('/api/v1/engineering/documents/' + document_id, headers=AUTOMATION)
    assert result.status_code == 404
    assert 'Developer acceptance' not in result.text
    assert str(PROJECT) not in result.text


def test_missing_key_and_nested_fields_are_rejected(env):
    client, _ = env
    body = draft_body(client)
    response = client.post('/api/v1/engineering/changes/CR-017/plans', json=body, headers=AUTOMATION)
    assert response.status_code == 422
    body['assessment']['approved'] = True
    response = post(client, '/engineering/changes/CR-017/plans', body, 'nested')
    assert response.status_code == 422


def test_actual_foreign_program_records_remain_inaccessible(env):
    client, settings = env
    con = connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE')
        store = Store(con)
        program = store.get('planner.program', 'PRG-A17')
        foreign_customer = store.get('engineering.customer', 'CUST-FML01')
        foreign_customer['id'] = 'CUST-OTHER'
        store.insert('engineering.customer', foreign_customer)
        # A consistent second customer/program/order/config graph, test setup only.
        config = store.get('engineering.configuration', 'CFG-B-01')
        config.update(id='CFG-OTHER', program_id='PRG-OTHER')
        order = store.get('erp.order', 'ORD-1204')
        order.update(id='ORD-OTHER', program_id='PRG-OTHER', customer_id='CUST-OTHER')
        program.update(id='PRG-OTHER', program_id='PRG-OTHER', customer_id='CUST-OTHER',
                       configuration_id='CFG-OTHER', order_id='ORD-OTHER', milestone_ids=[])
        store.insert('engineering.configuration', config)
        store.insert('erp.order', order)
        store.insert('planner.program', program)
        con.commit()
    finally:
        con.close()
    for path in ['/erp/orders/ORD-OTHER', '/programs/PRG-OTHER', '/engineering/configurations/CFG-OTHER']:
        response = client.get('/api/v1' + path, headers=AUTOMATION)
        assert response.status_code == 404
    body = draft_body(client)
    body['configuration_id'] = 'CFG-OTHER'
    response = post(client, '/engineering/changes/CR-017/plans', body, 'foreign')
    assert response.status_code == 404


def test_overlapping_lab_windows_block_distinct_slots_and_samples(factory, seed):
    seed['manufacturing']['lots'][1]['restrictions'] = []
    seed['manufacturing']['lots'][1]['hold_details'] = []
    other_slot = copy.deepcopy(seed['validation']['slots'][1])
    other_slot['id'] = 'SLOT-OVERLAP'
    seed['validation']['slots'].append(other_slot)
    client, _ = factory(seed)
    options = get(client, '/validation/options?change_id=CR-017')['items']
    plans, approvals = [], []
    for slot_id, sample_id in [('SLOT-PRIORITY', 'SAMPLE-B-017'), ('SLOT-OVERLAP', 'SAMPLE-B-018')]:
        selected = next(o for o in options if o['slot']['id'] == slot_id and o['sample']['id'] == sample_id)
        body = draft_body(client)
        body.update(slot_id=slot_id, sample_id=sample_id, expected_source_versions=selected['expected_source_versions'])
        result = post(client, '/engineering/changes/CR-017/plans', body, slot_id)
        assert result.status_code == 201
        plan = result.json()
        plans.append(plan)
        approvals.append(approve(client, plan, key=slot_id))
    book(client, plans[0], approvals[0])
    response = post(client, '/validation/jobs', dict(plan_id=plans[1]['id'], approval_id=approvals[1]['id']), 'overlap')
    assert response.status_code == 409
    assert 'RESERVATION_CONFLICT' in response.json()['error']['details']['reasons']


def test_book_and_link_reject_wrong_approval_and_job(env):
    client, _ = env
    p1, p2 = draft(client, key='p1'), draft(client, key='p2')
    a1, a2 = approve(client, p1, key='a1'), approve(client, p2, key='a2')
    job = book(client, p1, a1)
    response = post(client, '/programs/PRG-A17/implementation-links', link_body(p2, a2, job), 'wrong-job')
    assert response.status_code == 403
    response = post(client, '/programs/PRG-A17/implementation-links', link_body(p1, a2, job), 'wrong-approval')
    assert response.status_code == 403


def test_real_http_process_restart_and_reset():
    result = subprocess.run([sys.executable, 'scripts/verify_http_lifecycle.py'], cwd=PROJECT,
                            env={**os.environ, 'TMPDIR': str(PROJECT / '.cache/tmp')},
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'SCRIPTED MOCK-SYSTEM INTEGRATION TEST' in result.stdout
    assert '"real_process_restart": "PASS"' in result.stdout
    assert '"deterministic_reset_runs": 2' in result.stdout


def test_readonly_rates_are_approved_and_effective(env):
    from test_authority_staleness import external_update
    client, settings = env
    external_update(settings, 'erp.rate', 'RATE-PRIORITY', {'status': 'retired'})
    external_update(settings, 'erp.rate', 'RATE-OTHER', {'effective_from': '2026-11-17T00:00:00Z'})
    rates = get(client, '/erp/cost-rates?program_id=PRG-A17')['items']
    assert [r['id'] for r in rates] == ['RATE-STANDARD']


def test_denials_identify_actor_and_exact_plan(env):
    client, _ = env
    plan = draft(client)
    response = post(client, f'/engineering/plans/{plan["id"]}/decisions', dict(decision='approve', expected_plan_version=1,
                     expected_plan_digest=plan['plan_digest'], reason='Denied self approval'), 'denial')
    assert response.status_code == 403
    events = get(client, '/audit/events?change_id=CR-017')['items']
    denied = next(e for e in events if e['outcome'] == 'denied')
    assert denied['actor_id'] == 'demo-automation' and denied['plan_id'] == plan['id']
    created = next(e for e in events if e['outcome'] == 'succeeded')
    assert created['plan_id'] == plan['id']


def test_denial_audit_does_not_invent_uncreated_resource_refs(env):
    client, _ = env
    body = draft_body(client)
    body['expected_change_content_version'] = 2
    assert post(client, '/engineering/changes/CR-017/plans', body, 'stale-change').status_code == 409
    plan = draft(client)
    assert post(client, '/validation/jobs', dict(plan_id=plan['id'], approval_id='absent-approval'), 'absent').status_code == 404
    events = get(client, '/audit/events?change_id=CR-017')['items']
    denied_draft = next(e for e in events if e['action'] == 'create_plan' and e['outcome'] == 'denied')
    denied_job = next(e for e in events if e['action'] == 'schedule_job' and e['outcome'] == 'denied')
    assert denied_draft['plan_id'] is None
    assert denied_job['plan_id'] == plan['id'] and denied_job['job_id'] is None
