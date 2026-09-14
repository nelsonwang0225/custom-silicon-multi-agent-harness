import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mock_enterprise.app import create_app
from mock_enterprise.config import PROJECT, Settings
from mock_enterprise.db import Store, connect, read_store, restrict_writes, schema_statements, table
from mock_enterprise.seed import initialize, lifecycle_lock, load_seed
from conftest import AUTOMATION, ENGINEER, READER, approve, book, draft, draft_body, get, link_body, post
from test_authority_staleness import external_update


def test_concurrent_same_and_distinct_keys_do_not_duplicate(env):
    client, settings = env
    plan = draft(client)
    approval = approve(client, plan)
    body = dict(plan_id=plan['id'], approval_id=approval['id'])
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: post(client, '/validation/jobs', body, 'same'), range(4)))
    assert [r.status_code for r in responses] == [201] * 4
    assert len({r.json()['id'] for r in responses}) == 1
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda i: post(client, '/validation/jobs', body, f'new-{i}'), range(4)))
    assert [r.status_code for r in responses] == [409] * 4
    with read_store(settings.db_path) as store:
        assert len(store.list('validation.job')) == len(store.list('validation.reservation')) == 1


def test_competing_plans_cannot_share_sample_or_slot(env):
    client, _ = env
    p1, p2 = draft(client, key='one'), draft(client, key='two')
    a1, a2 = approve(client, p1, key='one'), approve(client, p2, key='two')
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda pair: post(client, '/validation/jobs', dict(plan_id=pair[0]['id'], approval_id=pair[1]['id']), pair[0]['id']), [(p1, a1), (p2, a2)]))
    assert sorted(r.status_code for r in responses) == [201, 409]
    assert len(get(client, '/validation/jobs?change_id=CR-017')['items']) == 1


def test_concurrent_planner_links_have_one_task(env):
    client, settings = env
    plan = draft(client)
    approval = approve(client, plan)
    job = book(client, plan, approval)
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'same-link'), range(4)))
    assert all(r.status_code == 201 for r in responses)
    assert len({r.json()['task_id'] for r in responses}) == 1
    with read_store(settings.db_path) as store:
        assert len(store.list('planner.task')) == 1


def test_partial_planner_failure_rolls_back_only_planner(env, monkeypatch):
    client, settings = env
    plan = draft(client)
    approval = approve(client, plan)
    job = book(client, plan, approval)
    before = get(client, '/programs/PRG-A17/milestones/MS-ACCEPT-01')
    original = Store.update
    def fail_planner(self, kind, *args, **kwargs):
        if kind == 'planner.milestone':
            raise RuntimeError('test-only failure after task/link insert')
        return original(self, kind, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Store, 'update', fail_planner)
        response = post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'recover')
    assert response.status_code == 500
    assert get(client, '/programs/PRG-A17/milestones/MS-ACCEPT-01') == before
    assert get(client, '/programs/PRG-A17/implementation-links?change_id=CR-017')['items'] == []
    with read_store(settings.db_path) as store:
        assert len(store.list('validation.job')) == 1
        assert len(store.list('validation.reservation')) == 1
        assert not store.list('planner.task')
        assert store.con.execute("SELECT count(*) FROM idempotency_receipts WHERE route LIKE '%implementation-links'").fetchone()[0] == 0
    assert get(client, f'/engineering/plans/{plan["id"]}')['execution_state'] == 'lab_scheduled_pending_planner'
    response = post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'recover')
    assert response.status_code == 201
    assert len(get(client, '/validation/jobs?change_id=CR-017')['items']) == 1


def test_lost_response_after_commit_recovers_same_booking(env, monkeypatch):
    client, _ = env
    plan = draft(client)
    approval = approve(client, plan)
    original = client.post
    captured = []
    def lost(*args, **kwargs):
        response = original(*args, **kwargs)
        captured.append(response.json()['id'])
        raise TimeoutError('Test transport discarded the committed HTTP response')
    body = dict(plan_id=plan['id'], approval_id=approval['id'])
    with monkeypatch.context() as patch:
        patch.setattr(client, 'post', lost)
        with pytest.raises(TimeoutError):
            post(client, '/validation/jobs', body, 'lost')
    retried = post(client, '/validation/jobs', body, 'lost')
    assert retried.status_code == 201 and retried.json()['id'] == captured[0]
    assert retried.headers['Idempotency-Replayed'] == 'true'


def test_optimistic_milestone_reread_does_not_require_rebooking(env):
    client, settings = env
    plan = draft(client)
    approval = approve(client, plan)
    job = book(client, plan, approval)
    external_update(settings, 'planner.milestone', 'MS-ACCEPT-01', {'record_version': 2})
    result = post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'link')
    assert result.status_code == 409 and result.json()['error']['code'] == 'STALE_MILESTONE'
    result = post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job, version=2), 'link')
    assert result.status_code == 201
    assert result.json()['milestone_version_after'] == 3


@pytest.mark.parametrize('domain,kind', [('validation', 'engineering.change'), ('engineering', 'erp.rate'), ('planner', 'validation.sample')])
def test_sql_authorizer_enforces_domain_write_ownership(env, domain, kind):
    _, settings = env
    con = connect(settings.db_path)
    try:
        restrict_writes(con, domain)
        with pytest.raises(sqlite3.DatabaseError):
            con.execute(f'UPDATE {table(kind)} SET content_version=content_version+1')
    finally:
        con.close()


def test_immutable_records_and_commitments_have_sql_guards(env):
    client, settings = env
    plan = draft(client)
    approval = approve(client, plan)
    job = book(client, plan, approval)
    con = connect(settings.db_path)
    try:
        for name in ['engineering_plan', 'engineering_decision', 'validation_job', 'validation_reservation', 'validation_result', 'audit_events']:
            with pytest.raises(sqlite3.IntegrityError):
                con.execute(f'DELETE FROM {name}')
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("UPDATE erp_order SET committed_delivery_at='2099-01-01T00:00:00Z'")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("UPDATE planner_milestone SET baseline_at='2099-01-01T00:00:00Z'")
    finally:
        con.close()


def test_cached_result_still_requires_authorized_role(env):
    client, _ = env
    plan = draft(client)
    approval = approve(client, plan)
    book(client, plan, approval)
    response = post(client, '/validation/jobs', {'plan_id': plan['id'], 'approval_id': approval['id']}, 'book', READER)
    assert response.status_code == 403


def test_restart_and_atomic_repeatable_reset(tmp_path):
    settings = Settings(tmp_path / 'demo.sqlite3', tmp_path, True)
    initialize(settings)
    with TestClient(create_app(settings)) as client:
        baseline = get(client, '/engineering/changes/CR-017')
        plan = draft(client)
        approval = approve(client, plan)
        job = book(client, plan, approval)
        with pytest.raises(ValueError, match='Stop the service'):
            initialize(settings, reset=True, confirmed=True)
    with TestClient(create_app(settings)) as client:
        assert get(client, f'/validation/jobs/{job["id"]}') == job
        assert get(client, f'/engineering/plans/{plan["id"]}')['state'] == 'approved'
    for _ in range(2):
        initialize(settings, reset=True, confirmed=True)
        with TestClient(create_app(settings)) as client:
            assert get(client, '/engineering/changes/CR-017') == baseline
            assert not get(client, '/validation/jobs?change_id=CR-017')['items']
            assert not get(client, '/audit/events?change_id=CR-017')['items']


@pytest.mark.parametrize('failure', ['unconfirmed', 'non_demo', 'symlink', 'hardlink', 'outside_storage', 'unexpected_schema'])
def test_reset_refuses_unsafe_targets(tmp_path, failure):
    settings = Settings(tmp_path / 'demo.sqlite3', tmp_path, True)
    initialize(settings)
    if failure == 'non_demo':
        con = connect(settings.db_path)
        con.execute("UPDATE demo_metadata SET data='{}'")
        con.close()
    if failure == 'symlink':
        symlink = tmp_path / 'link.sqlite3'
        symlink.symlink_to(settings.db_path)
        settings = Settings(symlink, tmp_path, True)
    if failure == 'hardlink':
        (tmp_path / 'hard.sqlite3').hardlink_to(settings.db_path)
    if failure == 'outside_storage':
        settings = Settings(settings.db_path, tmp_path / 'other', True)
    if failure == 'unexpected_schema':
        con = connect(settings.db_path)
        con.execute('CREATE TABLE unrelated (id INTEGER)')
        con.close()
    with pytest.raises(ValueError):
        initialize(settings, reset=True, confirmed=failure != 'unconfirmed')


def test_failed_reset_restores_original_transaction(tmp_path, monkeypatch):
    settings = Settings(tmp_path / 'demo.sqlite3', tmp_path, True)
    initialize(settings)
    with read_store(settings.db_path) as store:
        before = list(store.con.iterdump())
    original = Store.insert
    def fail_reload(self, kind, record):
        if kind == 'planner.program':
            raise ValueError('Test-only seed failure')
        return original(self, kind, record)
    monkeypatch.setattr(Store, 'insert', fail_reload)
    with pytest.raises(ValueError):
        initialize(settings, reset=True, confirmed=True)
    with read_store(settings.db_path) as store:
        assert list(store.con.iterdump()) == before


@pytest.mark.parametrize('mutation', ['money', 'broken_ref', 'bad_document', 'duration'])
def test_seed_rejects_inconsistent_input(seed, mutation):
    if mutation == 'money':
        seed['erp']['cost_rates'][0]['incremental_cost_cents'] = 0.5
    elif mutation == 'broken_ref':
        seed['validation']['samples'][0]['unit_id'] = 'MISSING'
    elif mutation == 'bad_document':
        seed['engineering']['document_manifest'][0]['relative_path'] = 'docs/ACCEPTANCE_TESTS.md'
    else:
        seed['engineering']['procedures'][0]['per_bin_minutes'] = 480
    with pytest.raises(ValueError):
        load_seed(seed)


def test_database_busy_fails_without_reporting_success(env, caplog):
    client, settings = env
    body = draft_body(client)
    con = connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE')
        response = post(client, '/engineering/changes/CR-017/plans', body, 'busy')
        assert response.status_code == 503
        assert response.json()['error']['code'] == 'DATABASE_BUSY'
        assert 'Audit unavailable' in caplog.text
        assert 'local-only' not in caplog.text
    finally:
        con.rollback()
        con.close()
    assert get(client, '/engineering/changes/CR-017')['plans'] == []
    assert post(client, '/engineering/changes/CR-017/plans', body, 'busy').status_code == 201


def test_success_audit_failure_rolls_back_business_change(env, monkeypatch):
    import mock_enterprise.http as transaction_http
    client, _ = env
    original = transaction_http.audit
    def fail_success(store, request, domain, outcome, **kwargs):
        if outcome == 'succeeded':
            raise RuntimeError('Test-only audit insert failure')
        return original(store, request, domain, outcome, **kwargs)
    body = draft_body(client)
    with monkeypatch.context() as patch:
        patch.setattr(transaction_http, 'audit', fail_success)
        response = post(client, '/engineering/changes/CR-017/plans', body, 'audit-fail')
    assert response.status_code == 500
    assert get(client, '/engineering/changes/CR-017')['plans'] == []
    assert post(client, '/engineering/changes/CR-017/plans', body, 'audit-fail').status_code == 201
