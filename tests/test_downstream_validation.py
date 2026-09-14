"""Deterministic source ownership/authority; no physical tests or paid agents."""
import copy
import pytest
from conftest import get, post, draft, approve, book, ENGINEER, AUTOMATION, READER, link_body
from mock_enterprise.core import digest
from mock_enterprise.db import Store, connect
LAB = {'Authorization': 'Bearer demo-lab-local-only'}
PHYSICAL = '/validation/changes/CR-017/physical-validation'
REVIEW = '/engineering/changes/CR-017/evidence-reviews'


def scheduled(env):
    client, settings = env
    plan = draft(client); approval = approve(client, plan); job = book(client, plan, approval)
    assert post(client, '/programs/PRG-A17/implementation-links', link_body(plan, approval, job), 'link').status_code == 201
    return client, settings, plan, job


def publish(client, job, key='publish', role=LAB):
    return post(client, f'/validation/jobs/{job["id"]}/synthetic-result', {'expected_plan_digest': job['plan_digest']}, key, role)


def changed_result(settings, result_id, variant):
    """Developer-only alternate observations. Never a public failure-injection route."""
    con = connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE'); store = Store(con)
        for name in ('validation_result', 'validation_completion'):
            con.execute(f'DROP TRIGGER immutable_{name}_update')
        r = store.get('validation.result', result_id)
        if variant == 'failed':
            r.update(status='completed', criteria_passed=False)
        elif variant == 'software':
            r['configuration_snapshot']['runtime'] = 'RT-wrong'
        elif variant == 'configuration':
            r['configuration_id'] = 'CFG-A-01'
        elif variant == 'incomplete':
            r['actual_suite_minutes'] = 60
            r['observed_minutes_by_context_bin'] = {str(b): 20 for b in r['covered_context_bins']}
        elif variant == 'stale':
            store.update('engineering.workload', 'WF-LC-V2', {'content_version': 2})
        elif variant == 'conflict':
            other = copy.deepcopy(r); other.update(id='conflicting-observation', criteria_passed=False)
            store.insert('validation.result', other)
        if variant not in ('stale', 'conflict'):
            store.update('validation.result', result_id, r)
            event = store.list('validation.completion', result_id=result_id)[0]
            store.update('validation.completion', event['id'], {'result_digest': digest(r)})
        con.commit()
    finally:
        con.close()


def test_publish_requires_job_and_distinct_lab_identity(env):
    client = env[0]
    assert post(client, '/validation/jobs/missing/synthetic-result', {'expected_plan_digest':'0'*64}, 'missing', LAB).status_code == 404
    client, _, _, job = scheduled(env)
    for role in (AUTOMATION, ENGINEER, READER):
        assert publish(client, job, role=role).status_code == 403
    assert get(client, PHYSICAL)['job_status'] == 'scheduled'
    assert get(client, PHYSICAL)['result'] is None
    assert post(client, f'/validation/jobs/{job["id"]}/synthetic-result', {'expected_plan_digest':job['plan_digest'],'criteria_passed':True}, 'forged', LAB).status_code == 422


def test_publish_exact_scope_retry_and_engineering_review(env):
    client, settings, plan, job = scheduled(env)
    first = publish(client, job); assert first.status_code == 201, first.text
    assert publish(client, job).json() == first.json()
    assert publish(client, job, 'different-key').status_code == 409
    event = first.json(); assert event['generated_by'] == 'demo_lab_action' and event['recorded_by'] == 'demo-lab'
    assert event['plan_id'] == plan['id'] and event['plan_digest'] == plan['plan_digest']
    read_job = get(client, f'/validation/jobs/{job["id"]}')
    assert read_job['completion'] == event
    assert {**read_job, 'completion': None} == job
    result = get(client, '/validation/results/' + event['result_id'])
    assert result['actual_suite_minutes'] == 480 and set(result['observed_minutes_by_context_bin'].values()) == {160}
    state = get(client, PHYSICAL)
    assert state['applicability'] == 'confirmed' and state['engineering_status'] == 'ready', state
    assert state['current_review'] is None and state['customer_acceptance'] == 'pending'
    body = {'expected_evidence_digest':state['evidence_digest'], 'decision':'approve','reason':'Exact applicable evidence reviewed.'}
    assert post(client, REVIEW, body, 'wrong-role').status_code == 403
    assert get(client, PHYSICAL)['reviews'] == []
    assert post(client, REVIEW, {**body, 'expected_evidence_digest':'0'*64}, 'wrong-version', ENGINEER).status_code == 409
    reviewed = post(client, REVIEW, body, 'evidence-review', ENGINEER)
    assert reviewed.status_code == 201, reviewed.text
    assert post(client, REVIEW, body, 'evidence-review', ENGINEER).json() == reviewed.json()
    assert post(client, REVIEW, body, 'duplicate', ENGINEER).status_code == 409
    final = get(client, PHYSICAL)
    assert final['technical_state'] == 'validation_complete' and final['customer_acceptance'] == 'pending'
    assert final['customer_commitment'] == 'unchanged' and len(final['reviews']) == 1
    assert get(client, '/engineering/plans/' + plan['id'])['state'] == 'approved'
    assert len(get(client, '/validation/jobs?change_id=CR-017')['items']) == 1
    changed_result(settings, event['result_id'], 'stale')
    stale = get(client, PHYSICAL)
    assert stale['engineering_status'] == 'stale' and stale['current_review'] is None
    assert stale['technical_state'] == 'validation_gap' and len(stale['reviews']) == 1


@pytest.mark.parametrize('variant', ['failed', 'software', 'configuration', 'incomplete', 'conflict', 'stale'])
def test_bad_result_never_closes_gap(env, variant):
    client, settings, _, job = scheduled(env)
    event = publish(client, job).json()
    changed_result(settings, event['result_id'], variant)
    state = get(client, PHYSICAL)
    assert state['applicability'] == 'gap_remains' and state['technical_state'] == 'validation_gap', state
    assert state['mismatch_reasons']
    body = {'expected_evidence_digest':state['evidence_digest'], 'decision':'approve', 'reason':'Cannot approve'}
    assert post(client, REVIEW, body, 'deny', ENGINEER).status_code == 409
    assert get(client, PHYSICAL)['reviews'] == []


def test_rejected_review_retains_history_and_customer_pending(env):
    client, _, _, job = scheduled(env); publish(client, job)
    state = get(client, PHYSICAL)
    body = {'expected_evidence_digest':state['evidence_digest'], 'decision':'reject', 'reason':'Engineering rejects adequacy.'}
    assert post(client, REVIEW, body, 'reject', ENGINEER).status_code == 201
    state = get(client, PHYSICAL)
    assert state['technical_state'] == 'engineering_rejected' and state['customer_acceptance'] == 'pending'
    assert post(client, REVIEW, {**body, 'decision':'approve'}, 'alter', ENGINEER).status_code == 409


def test_result_version_change_and_superseded_plan_invalidate_review(env):
    client, settings, plan, job = scheduled(env)
    event=publish(client,job).json(); state=get(client,PHYSICAL)
    body={'expected_evidence_digest':state['evidence_digest'],'decision':'approve','reason':'Original result reviewed.'}
    assert post(client,REVIEW,body,'review',ENGINEER).status_code==201
    con=connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE'); store=Store(con)
        con.execute('DROP TRIGGER immutable_validation_result_update')
        store.update('validation.result',event['result_id'],{'content_version':2})
        con.commit()
    finally: con.close()
    state=get(client,PHYSICAL)
    assert state['current_review'] is None and state['engineering_status']=='stale'
    assert 'RESULT_BINDING_MISMATCH' in state['mismatch_reasons']
    assert post(client,REVIEW,body,'old-version',ENGINEER).status_code==409


def test_explicit_upgrade_preserves_booked_records(env):
    from mock_enterprise.downstream_upgrade import upgrade
    client,settings,plan,job=scheduled(env)
    # Close only this test client to release its lifecycle lock before the explicit CLI-equivalent upgrade.
    client.__exit__(None,None,None)
    con=connect(settings.db_path)
    try:
        for name in ('validation_completion','engineering_evidence_review'):
            con.execute('DROP TABLE '+name)
    finally: con.close()
    upgrade(settings); upgrade(settings)
    con=connect(settings.db_path)
    try:
        store=Store(con)
        assert store.get('validation.job',job['id'])['plan_id']==plan['id']
        assert store.list('validation.completion')==[]
        assert store.list('engineering.evidence_review')==[]
    finally: con.close()
    client.__enter__()
