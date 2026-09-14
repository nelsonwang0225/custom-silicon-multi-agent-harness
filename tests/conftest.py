import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mock_enterprise.app import create_app
from mock_enterprise.config import PROJECT, Settings
from mock_enterprise.seed import initialize

AUTOMATION = {'Authorization': 'Bearer demo-automation-local-only'}
ENGINEER = {'Authorization': 'Bearer demo-engineer-local-only'}
READER = {'Authorization': 'Bearer demo-reader-local-only'}


@pytest.fixture
def seed():
    return json.loads((PROJECT / 'fixtures/seed.json').read_text())


@pytest.fixture
def factory(tmp_path):
    clients = []
    def make(seed=None):
        directory = tmp_path / str(len(clients))
        directory.mkdir()
        settings = Settings(directory / 'demo.sqlite3', directory, True)
        initialize(settings, source=copy.deepcopy(seed) if seed is not None else json.loads((PROJECT / 'fixtures/seed.json').read_text()))
        client = TestClient(create_app(settings))
        client.__enter__()
        clients.append(client)
        return client, settings
    yield make
    for client in reversed(clients):
        client.__exit__(None, None, None)


@pytest.fixture
def env(factory):
    return factory()


def get(client, path, role=AUTOMATION):
    response = client.get('/api/v1' + path, headers=role)
    assert response.status_code == 200, response.text
    return response.json()


def post(client, path, body, key, role=AUTOMATION):
    return client.post('/api/v1' + path, json=body, headers={**role, 'Idempotency-Key': key})


def draft_body(client, *, late=False):
    options = get(client, '/validation/options?change_id=CR-017')['items']
    option = next(o for o in options if o['resource_eligible'] and o['meets_deadline'] != late)
    return dict(expected_change_content_version=1, target_requirement_revision_id='REQ-042-V2',
                configuration_id=option['configuration_id'], procedure_id=option['procedure_id'],
                sample_id=option['sample']['id'], slot_id=option['slot']['id'], milestone_id=option['milestone_id'],
                assessment=dict(facts=[dict(text='Customer requested additional workload evidence.',
                                source_refs=[dict(resource_type='engineering.change', resource_id='CR-017')])],
                                evidence_gaps=['No complete applicable result.'], unresolved_questions=['Future test result is unknown.']),
                expected_source_versions=option['expected_source_versions'])


def draft(client, key='plan', **kwargs):
    response = post(client, '/engineering/changes/CR-017/plans', draft_body(client, **kwargs), key)
    assert response.status_code == 201, response.text
    return response.json()


def approve(client, plan, decision='approve', key='approve'):
    body = dict(decision=decision, expected_plan_version=plan['plan_version'], expected_plan_digest=plan['plan_digest'], reason='Simulated engineering decision under demo policy.')
    response = post(client, f'/engineering/plans/{plan["id"]}/decisions', body, key, ENGINEER)
    assert response.status_code == 201, response.text
    return response.json()


def book(client, plan, approval, key='book'):
    response = post(client, '/validation/jobs', {'plan_id': plan['id'], 'approval_id': approval['id']}, key)
    assert response.status_code == 201, response.text
    return response.json()


def link_body(plan, approval, job, version=1):
    return dict(plan_id=plan['id'], approval_id=approval['id'], job_id=job['id'], expected_milestone_record_version=version)
