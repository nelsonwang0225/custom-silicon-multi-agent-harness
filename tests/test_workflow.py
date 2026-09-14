from conftest import AUTOMATION, ENGINEER, READER, approve, book, draft, draft_body, get, link_body, post


def test_golden_path_and_retries(env):
    client, _ = env
    body = draft_body(client)
    response = post(client, '/engineering/changes/CR-017/plans', body, 'draft')
    assert response.status_code == 201, response.text
    plan = response.json()
    spoof = post(client, '/validation/jobs', {'plan_id': plan['id'], 'approval_id': 'not-an-approval'}, 'book')
    assert spoof.status_code == 404
    decision_body = dict(decision='approve', expected_plan_version=1, expected_plan_digest=plan['plan_digest'], reason='Simulated.')
    assert post(client, f'/engineering/plans/{plan["id"]}/decisions', decision_body, 'self').status_code == 403
    approval = approve(client, plan)
    assert get(client, f'/engineering/plans/{plan["id"]}')['state'] == 'approved'
    job = book(client, plan, approval)
    plan_after_job = get(client, f'/engineering/plans/{plan["id"]}')
    assert plan_after_job['execution_state'] == 'lab_scheduled_pending_planner'
    assert plan_after_job['plan_digest'] == plan['plan_digest']
    linked = post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'link')
    assert linked.status_code == 201, linked.text
    link = linked.json()
    assert link['task']['status'] == 'scheduled'
    assert get(client, f'/engineering/plans/{plan["id"]}')['execution_state'] == 'scheduled_awaiting_execution'
    milestone = get(client, '/programs/PRG-A17/milestones/MS-ACCEPT-01')
    assert milestone['current_forecast_at'] == '2026-11-18T20:00:00Z'
    assert milestone['baseline_at'] == '2026-11-19T18:00:00Z'
    assert milestone['forecast_status'] == 'conditional_on_test_and_review'
    assert milestone['content_version'] == 1 and milestone['record_version'] == 2
    assert get(client, '/erp/orders/ORD-1204')['committed_delivery_at'] == '2026-11-23T18:00:00Z'
    assert get(client, '/engineering/requirements/REQ-042-V1')['status'] == 'approved'
    assert get(client, '/engineering/requirements/REQ-042-V2')['status'] == 'requested'
    assert len(get(client, '/validation/coverage?change_id=CR-017')['items']) == 3
    for path, payload, key, original, role in [
        ('/engineering/changes/CR-017/plans', body, 'draft', plan, AUTOMATION),
        (f'/engineering/plans/{plan["id"]}/decisions', dict(decision='approve', expected_plan_version=1, expected_plan_digest=plan['plan_digest'], reason='Simulated engineering decision under demo policy.'), 'approve', approval, ENGINEER),
        ('/validation/jobs', {'plan_id': plan['id'], 'approval_id': approval['id']}, 'book', job, AUTOMATION),
        ('/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'link', link, AUTOMATION),
    ]:
        retry = post(client, path, payload, key, role)
        assert retry.status_code == 201, retry.text
        assert retry.json() == original
        assert retry.headers['Idempotency-Replayed'] == 'true'
        if '/changes/' not in path:
            new_key = post(client, path, payload, key + '-other', role)
            assert new_key.status_code == 409 and new_key.json()['error']['code'] == 'ACTION_ALREADY_RECORDED'
    assert len(get(client, '/validation/jobs?change_id=CR-017')['items']) == 1
    assert len(get(client, '/programs/PRG-A17/implementation-links?change_id=CR-017')['items']) == 1
    events = get(client, '/audit/events?change_id=CR-017')['items']
    assert len([e for e in events if e['outcome'] == 'succeeded']) == 4
    assert len([e for e in events if e['outcome'] == 'replay']) == 4
    assert len([e for e in events if e['outcome'] == 'denied']) >= 1
    assert 'Bearer' not in str(events) and 'local-only' not in str(events)


def test_rejected_plan_cannot_schedule(env):
    client, _ = env
    plan = draft(client)
    rejected = approve(client, plan, decision='reject')
    response = post(client, '/validation/jobs', {'plan_id': plan['id'], 'approval_id': rejected['id']}, 'job')
    assert response.status_code == 403
    assert get(client, '/validation/jobs?change_id=CR-017')['items'] == []
    response = post(client, f'/engineering/plans/{plan["id"]}/decisions',
                    dict(decision='approve', expected_plan_version=1, expected_plan_digest=plan['plan_digest'], reason='Different decision'), 'again', ENGINEER)
    assert response.status_code == 409 and response.json()['error']['code'] == 'DECISION_CONFLICT'


def test_changed_plan_does_not_inherit_approval(env):
    client, _ = env
    plan = draft(client)
    approval = approve(client, plan)
    revision_body = draft_body(client, late=True)
    revision_body['supersedes_plan_id'] = plan['id']
    revision = post(client, '/engineering/changes/CR-017/plans', revision_body, 'revision').json()
    assert revision['plan_digest'] != plan['plan_digest']
    response = post(client, '/validation/jobs', {'plan_id': revision['id'], 'approval_id': approval['id']}, 'bad')
    assert response.status_code == 403
    response = post(client, f'/engineering/plans/{revision["id"]}/decisions', dict(decision='approve', expected_plan_version=2, expected_plan_digest=revision['plan_digest'], reason='Wrong version'), 'wrong-version', ENGINEER)
    assert response.status_code == 409


def test_changed_body_under_successful_key(env):
    client, _ = env
    body = draft_body(client)
    assert post(client, '/engineering/changes/CR-017/plans', body, 'same').status_code == 201
    body['assessment']['unresolved_questions'] = ['Changed scope discussion.']
    result = post(client, '/engineering/changes/CR-017/plans', body, 'same')
    assert result.status_code == 409
    assert result.json()['error']['code'] == 'IDEMPOTENCY_KEY_REUSED'
