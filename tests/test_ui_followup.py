import copy

import pytest
from pydantic import ValidationError

from conftest import approve, book, draft, get, link_body, post
from mock_enterprise.db import connect
from mock_enterprise.schemas import Lot
from mock_enterprise.seed import initialize


def test_change_execution_projection_preserves_engineering_and_prior_bookings(env):
    client, _ = env
    initial = get(client, '/engineering/changes/CR-017')
    assert initial['execution_state'] == 'not_scheduled'
    plan = draft(client)
    approval = approve(client, plan)
    assert get(client, '/engineering/changes/CR-017')['execution_state'] == 'not_scheduled'
    job = book(client, plan, approval)
    booked = get(client, '/engineering/changes/CR-017')
    assert booked['workflow_state'] == 'approved_awaiting_scheduling'
    assert booked['execution_state'] == 'lab_scheduled_pending_planner'
    assert post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'link').status_code == 201
    linked = get(client, '/engineering/changes/CR-017')
    assert linked['execution_state'] == 'scheduled_awaiting_execution'
    assert linked['record_version'] == booked['record_version']
    assert linked['content_version'] == initial['content_version']


def test_current_draft_does_not_hide_an_earlier_booked_plan(env):
    client, _ = env
    old = draft(client, key='old')
    approved = approve(client, old)
    newer = draft(client, key='new', late=True)
    job = book(client, old, approved)
    change = get(client, '/engineering/changes/CR-017')
    assert change['current_plan_id'] == newer['id']
    assert change['workflow_state'] == 'plan_drafted'
    assert change['execution_state'] == 'not_scheduled'
    prior = next(p for p in change['plans'] if p['id'] == old['id'])
    assert prior['job_id'] == job['id']
    assert prior['execution_state'] == 'lab_scheduled_pending_planner'


def test_legacy_database_has_no_invented_context_and_keeps_old_approval_valid(factory, seed):
    legacy = copy.deepcopy(seed)
    for lot in legacy['manufacturing']['lots']:
        lot.pop('hold_details', None)
    for rate in legacy['erp']['cost_rates']:
        rate.pop('service_name', None)
        rate.pop('service_description', None)
    client, settings = factory(legacy)
    plan = draft(client)
    approval = approve(client, plan)
    # Only an isolated test database is made structurally equivalent to v1.
    con = connect(settings.db_path)
    for table, fields in [('manufacturing_lot', ['hold_details']), ('manufacturing_unit', ['hold_details']), ('erp_rate', ['service_name', 'service_description'])]:
        for field in fields:
            con.execute(f'ALTER TABLE {table} DROP COLUMN {field}')
    con.close()
    assert get(client, '/manufacturing/lots/LOT-4492')['hold_details'] == []
    assert all(r['service_name'] is None for r in get(client, '/erp/cost-rates?program_id=PRG-A17')['items'])
    job = book(client, plan, approval)
    assert post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'link').status_code == 201
    # The lifecycle guard still refuses reset while this older file is served.
    with pytest.raises(ValueError, match='Stop the service'):
        initialize(settings, reset=True, confirmed=True)


def test_hold_context_and_rate_descriptions_are_persisted_and_read_only(env):
    client, _ = env
    lot = get(client, '/manufacturing/lots/LOT-4492')
    assert lot['hold_details'][0]['responsible_team'] == 'Pilot Manufacturing Engineering'
    assert lot['restrictions'] == ['engineering_hold']
    assert post(client, '/manufacturing/lots/LOT-4492', {'hold_details': []}, 'forbidden').status_code == 405
    rates = get(client, '/erp/cost-rates?program_id=PRG-A17')['items']
    assert all(r['service_name'] and r['service_description'] for r in rates)
    assert post(client, '/erp/cost-rates', {'service_name': 'Changed'}, 'forbidden').status_code == 405
    assert get(client, '/manufacturing/lots/LOT-4492') == lot
    invalid = {**lot, 'restrictions': []}
    with pytest.raises(ValidationError, match='recorded restrictions'):
        Lot.model_validate(invalid)
