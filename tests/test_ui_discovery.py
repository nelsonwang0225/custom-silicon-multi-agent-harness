"""UI discovery is scoped, read-only and drawn from persisted business records."""
import pytest

from conftest import AUTOMATION, ENGINEER, READER, get
from mock_enterprise.db import read_store

DIRECTORIES = [('/engineering/changes', 'engineering.change', 1),
               ('/manufacturing/units', 'manufacturing.unit', 3),
               ('/manufacturing/lots', 'manufacturing.lot', 3),
               ('/erp/orders', 'erp.order', 1), ('/programs', 'planner.program', 1)]


@pytest.mark.parametrize('path,kind,count', DIRECTORIES)
@pytest.mark.parametrize('persona', [READER, AUTOMATION, ENGINEER])
def test_discovery_fidelity_and_no_mutation(env, path, kind, count, persona):
    client, settings = env
    with read_store(settings.db_path) as store:
        before = list(store.con.iterdump())
        expected = store.list(kind)
    rows = get(client, path, persona)['items']
    assert len(rows) == count
    for actual, original in zip(rows, expected):
        assert {k: actual[k] for k in original} == original
    with read_store(settings.db_path) as store:
        assert list(store.con.iterdump()) == before
    if path == '/programs':
        assert rows[0]['scenario_at'] == '2026-11-16T09:00:00Z'
        assert rows[0]['customer_name'] == 'HELIOS AI'
        assert rows[0]['partner_freshness_limit_minutes'] == 1440


@pytest.mark.parametrize('path,kind,count', DIRECTORIES)
def test_discovery_requires_identity_and_cannot_widen_scope(env, path, kind, count):
    client, _ = env
    assert client.get('/api/v1' + path).status_code == 401
    assert client.get('/api/v1' + path + '?program_id=PRG-OTHER', headers=READER).status_code == 404
    assert client.post('/api/v1' + path, json={}, headers=AUTOMATION).status_code == 405
