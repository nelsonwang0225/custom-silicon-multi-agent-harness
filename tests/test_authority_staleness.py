import copy
import sqlite3
import pytest

from mock_enterprise.db import Store, connect, read_store, table
from conftest import AUTOMATION, ENGINEER, READER, approve, book, draft, draft_body, get, link_body, post


def external_update(settings, kind, record_id, fields):
    """Simulate external source changes ONLY inside the isolated test database."""
    con = connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE')
        Store(con).update(kind, record_id, fields)
        con.commit()
    finally:
        con.close()


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Bearer unknown-synthetic-selector'}])
def test_unknown_identity_has_no_business_access(env, headers):
    client, _ = env
    response = client.get('/api/v1/engineering/changes/CR-017', headers=headers)
    assert response.status_code == 401
    assert response.json()['error']['code'] == 'UNAUTHENTICATED'


@pytest.mark.parametrize('path', [
    '/engineering/changes/OTHER', '/programs/OTHER',
    '/engineering/documents?program_id=OTHER', '/erp/cost-rates?program_id=OTHER',
    '/validation/samples?program_id=OTHER', '/audit/events?change_id=OTHER',
    '/programs/OTHER/milestones/MS-ACCEPT-01',
])
def test_scope_query_cannot_widen_access(env, path):
    client, _ = env
    assert client.get('/api/v1' + path, headers=AUTOMATION).status_code == 404


@pytest.mark.parametrize('who', [READER, ENGINEER])
def test_only_automation_can_draft(env, who):
    client, _ = env
    assert post(client, '/engineering/changes/CR-017/plans', draft_body(client), 'denied', who).status_code == 403


@pytest.mark.parametrize('operation', ['POST', 'PUT', 'PATCH', 'DELETE'])
@pytest.mark.parametrize('path', [
    '/manufacturing/units/UNIT-B-017', '/manufacturing/lots/LOT-4491',
    '/erp/orders/ORD-1204', '/erp/cost-rates', '/validation/results/RES-SHORT-B',
    '/engineering/acceptance-criteria/CRIT-BASE-V1', '/reset', '/admin',
    '/programs/PRG-A17/milestones/MS-ACCEPT-01',
])
def test_protected_mutation_routes_absent(env, operation, path):
    client, _ = env
    response = client.request(operation, '/api/v1' + path, json={'approved': True}, headers=AUTOMATION)
    assert response.status_code in (404, 405)


@pytest.mark.parametrize('extra', ['actor', 'role', 'is_admin', 'approved', 'cost_cents', 'forecast_at', 'test_passed'])
def test_unexpected_plan_fields_rejected_without_echo(env, extra):
    client, _ = env
    payload = draft_body(client)
    payload[extra] = 'SYNTHETIC-INPUT-NOT-TO-ECHO'
    response = post(client, '/engineering/changes/CR-017/plans', payload, 'extra')
    assert response.status_code == 422
    assert 'SYNTHETIC-INPUT-NOT-TO-ECHO' not in response.text
    assert get(client, '/engineering/changes/CR-017')['plans'] == []


@pytest.mark.parametrize('mutation,code', [('missing', 'INVALID_SOURCE_SET'), ('duplicate', 'INVALID_SOURCE_SET'),
                                         ('extra', 'INVALID_SOURCE_SET'), ('stale', 'STALE_SOURCE'), ('evidence', 'STALE_SOURCE')])
def test_source_set_is_complete_and_current(env, mutation, code):
    client, _ = env
    body = draft_body(client)
    versions = body['expected_source_versions']
    if mutation == 'missing':
        versions['records'].pop()
    if mutation == 'duplicate':
        versions['records'].append(copy.deepcopy(versions['records'][0]))
    if mutation == 'extra':
        versions['records'].append(dict(resource_type='validation.sample', resource_id='SAMPLE-A-010', content_version=1, availability_version=1))
    if mutation == 'stale':
        versions['records'][0]['content_version'] += 1
    if mutation == 'evidence':
        versions['evidence_set_digest'] = 'a' * 64
    response = post(client, '/engineering/changes/CR-017/plans', body, 'bad-source')
    assert response.json()['error']['code'] == code
    assert response.status_code in (409, 422)


@pytest.mark.parametrize('kind,rid,fields', [
    ('engineering.change', 'CR-017', {'title': 'Changed requirement request', 'content_version': 2}),
    ('engineering.procedure', 'PROC-LC-02', {'review_minutes': 300, 'content_version': 2}),
    ('engineering.policy', 'POLICY-APP-01', {'max_incremental_cost_cents': 100000, 'content_version': 2}),
    ('manufacturing.unit', 'UNIT-B-017', {'restrictions': ['engineering_hold'], 'content_version': 2}),
    ('manufacturing.lot', 'LOT-4491', {'restrictions': ['engineering_hold'], 'content_version': 2}),
    ('manufacturing.unit', 'UNIT-B-017', {'updated_at': '2026-11-15T08:00:00Z'}),
    ('validation.slot', 'SLOT-PRIORITY', {'availability': 'unavailable', 'availability_version': 2}),
    ('erp.rate', 'RATE-PRIORITY', {'incremental_cost_cents': 180001}),
])
@pytest.mark.parametrize('stage', ['decision', 'booking', 'linking'])
def test_critical_stale_changes_block_unexecuted_action(env, kind, rid, fields, stage):
    client, settings = env
    plan = draft(client)
    approval = approve(client, plan) if stage != 'decision' else None
    job = book(client, plan, approval) if stage == 'linking' else None
    # Unrelated availability changes during linking retain the original owner but change version.
    external_update(settings, kind, rid, fields)
    if stage == 'decision':
        response = post(client, f'/engineering/plans/{plan["id"]}/decisions', dict(decision='approve', expected_plan_version=1, expected_plan_digest=plan['plan_digest'], reason='Stale attempt.'), 'stale', ENGINEER)
    elif stage == 'booking':
        response = post(client, '/validation/jobs', {'plan_id': plan['id'], 'approval_id': approval['id']}, 'stale')
    else:
        response = post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'stale')
    assert response.status_code == 409, response.text
    assert response.json()['error']['code'] == 'STALE_SOURCE'
    assert len(get(client, '/validation/jobs?change_id=CR-017')['items']) == (1 if stage == 'linking' else 0)
    assert get(client, '/programs/PRG-A17/implementation-links?change_id=CR-017')['items'] == []


@pytest.mark.parametrize('cents,allowed', [(200000, True), (200001, False)])
def test_policy_limit_inclusive(factory, seed, cents, allowed):
    seed['erp']['cost_rates'][1]['incremental_cost_cents'] = cents
    client, _ = factory(seed)
    plan = draft(client)
    response = post(client, f'/engineering/plans/{plan["id"]}/decisions', dict(decision='approve', expected_plan_version=1, expected_plan_digest=plan['plan_digest'], reason='Boundary policy test'), 'decision', ENGINEER)
    assert response.status_code == (201 if allowed else 403)
    if not allowed:
        assert response.json()['error']['code'] == 'APPROVAL_POLICY_EXCEEDED'


@pytest.mark.parametrize('timestamp,eligible', [('2026-11-15T09:00:00Z', True), ('2026-11-15T08:59:59Z', False), ('2026-11-16T09:00:01Z', False)])
@pytest.mark.parametrize('kind,rid', [('manufacturing.unit', 'UNIT-B-017'), ('manufacturing.lot', 'LOT-4491')])
def test_partner_freshness_boundaries(env, timestamp, eligible, kind, rid):
    client, settings = env
    external_update(settings, kind, rid, {'updated_at': timestamp})
    options = get(client, '/validation/options?change_id=CR-017')['items']
    selected = next(o for o in options if o['slot']['id'] == 'SLOT-PRIORITY' and o['sample']['id'] == 'SAMPLE-B-017')
    assert selected['resource_eligible'] is eligible


@pytest.mark.parametrize('field,time,eligible', [('ends_at', '2026-11-18T16:00:00Z', True), ('ends_at', '2026-11-18T15:59:59Z', False),
                                               ('effective_to', '2026-11-18T16:00:00Z', True), ('effective_to', '2026-11-18T15:59:59Z', False)])
def test_slot_and_rate_boundary(env, field, time, eligible):
    client, settings = env
    kind, rid = ('validation.slot', 'SLOT-PRIORITY') if field == 'ends_at' else ('erp.rate', 'RATE-PRIORITY')
    external_update(settings, kind, rid, {field: time})
    options = get(client, '/validation/options?change_id=CR-017')['items']
    selected = next(o for o in options if o['slot']['id'] == 'SLOT-PRIORITY' and o['sample']['id'] == 'SAMPLE-B-017')
    assert selected['resource_eligible'] is eligible


def test_late_option_remains_permissible(env):
    client, _ = env
    plan = draft(client, late=True)
    approval = approve(client, plan)
    job = book(client, plan, approval)
    assert job['cost_cents'] == 0 and job['timing']['deadline_slack_minutes'] == -1680


def test_new_result_invalidates_evidence_snapshot(env):
    client, settings = env
    plan = draft(client)
    approval = approve(client, plan)
    con = connect(settings.db_path)
    try:
        store = Store(con)
        result = store.get('validation.result', 'RES-SHORT-B')
        result['id'] = 'RES-NEW-IN-TEST-ONLY'
        store.insert('validation.result', result)
    finally:
        con.close()
    response = post(client, '/validation/jobs', {'plan_id': plan['id'], 'approval_id': approval['id']}, 'new-evidence')
    assert response.status_code == 409 and response.json()['error']['code'] == 'STALE_SOURCE'
