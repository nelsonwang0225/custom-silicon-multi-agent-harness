"""Downstream host passes through the existing CaseHarness without a scheduler."""
import time
import pytest
from test_phase08_control_host import env, host, investigate, post, snapshot
from mock_enterprise.db import Store, connect
from mock_enterprise.core import digest


def execution_and_result(f):
    client, service, double, settings = f
    item = investigate(f); ref = item['execution']['reference']
    assert post(client, 'proposals/review', {'reference':ref,'decision':'approve'}, 'engineer').status_code == 200
    assert post(client, 'proposals/execute', {'reference':ref}).status_code == 200
    job = service.source.read.get_validation_jobs(change_id='CR-017')['items'][0]
    response = service.source._http.post('/api/v1/validation/jobs/' + job['id'] + '/synthetic-result',
        headers={'Authorization':'Bearer demo-lab-local-only','Idempotency-Key':'synthetic'}, json={'expected_plan_digest':job['plan_digest']})
    assert response.status_code == 201, response.text
    return response.json()


def assess(f):
    client = f[0]
    physical = snapshot(client)['downstream']['physical']
    body = {'expected_evidence_digest':physical['evidence_digest']}
    start = post(client, 'cases/CR-017/assess-validation-result', body)
    assert start.status_code == 202, start.text
    for _ in range(150):
        state = snapshot(client)
        run = next(r for r in state['runs'] if r['run_id'] == start.json()['run_id'])
        if run['status'] in ('completed','failed'):
            return state, body
        time.sleep(0.03)
    pytest.fail('Reassessment did not finish')


def evidence_escalate(client, state, evidence):
    run = next(r for r in state['runs'] if r['run_id'] == state['downstream']['assessment']['run_id'])
    response = post(client, 'cases/CR-017/evidence-escalations', {
        'submission_id': 'ui_test_evidence_handoff',
        'run_id': run['run_id'],
        'expected_evidence_digest': evidence,
        'subject': 'Final validation evidence review',
        'recommendation': 'Review the exact recorded result and decide whether it satisfies the approved plan.',
        'business_context': 'The agents matched the result to the approved job, workload, configuration, and source versions.',
        'operator_notes': 'Scripted Program Operator handoff for isolated verification.',
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_passing_lab_result_completes_shortened_demo_without_reassessment(host):
    client, service, double, settings = host
    execution_and_result(host)
    state = snapshot(client)
    summary = next(item for item in state['case_summaries'] if item['change_id'] == 'CR-017')
    assert summary['state'] == 'completed_technical'
    assert summary['attention'] == 'none'
    assert state['downstream']['assessment'] is None
    assert state['downstream']['physical']['applicability'] == 'confirmed'
    assert not any(d['kind'] == 'engineering_evidence' for d in state['decision_summaries'])
    assert len(service.source.read.get_validation_jobs(change_id='CR-017')['items']) == 1
    assert len(service.source.read.get_implementation_links(program_id='PRG-A17',change_id='CR-017')['items']) == 1
    assert double.calls == 1


def test_failed_result_is_assessed_without_closing_gap(host):
    client, service, double, settings = host
    event = execution_and_result(host)
    con = connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE'); store = Store(con)
        con.execute('DROP TRIGGER immutable_validation_result_update'); con.execute('DROP TRIGGER immutable_validation_completion_update')
        result = store.update('validation.result', event['result_id'], {'criteria_passed':False})
        store.update('validation.completion', event['id'], {'result_digest':digest(result)})
        con.commit()
    finally: con.close()
    state, body = assess(host)
    assert state['runs'][0]['status'] == 'completed', state['runs'][0]
    assert not state['downstream']['assessment']['confirmed']
    assert not state['downstream']['review_ready']
    assert state['downstream']['physical']['technical_state'] == 'validation_gap'
    assert len(state['proposals']) == 1
    assert post(client,'cases/CR-017/evidence-review',{**body,'decision':'approve','comment':'invalid'},'engineer').status_code == 409


def test_downstream_denials_stale_binding_and_no_prepare(host):
    client, service, double, settings = host
    assert post(client,'cases/CR-017/assess-validation-result',{'expected_evidence_digest':'0'*64}).status_code==409
    assert double.calls==0
    execution_and_result(host)
    physical=snapshot(client)['downstream']['physical']
    body={'expected_evidence_digest':physical['evidence_digest']}
    assert post(client,'cases/CR-017/assess-validation-result',body,'reader').status_code==403
    assert post(client,'cases/CR-017/assess-validation-result',{**body,'prompt':'override'}).status_code==422
    state,body=assess(host)
    assert post(client,'proposals/prepare',{'run_id':state['downstream']['assessment']['run_id']}).status_code==409
    con=connect(settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE'); Store(con).update('engineering.criteria','CRIT-BASE-V1',{'content_version':2});con.commit()
    finally:con.close()
    assert post(client,'cases/CR-017/evidence-review',{**body,'decision':'approve','comment':'Old evidence'},'engineer').status_code==409
    assert snapshot(client)['downstream']['physical']['reviews']==[]
    assert len(snapshot(client)['proposals'])==1


def test_lost_engineering_review_reply_recovers_without_second_write(host):
    from program_coordinator.application.execution_models import SourceFailure
    client,service,_,_=host
    execution_and_result(host); state,body=assess(host)
    original=service.human._post
    calls=[]
    def lost(*args,**kwargs):
        calls.append(1); original(*args,**kwargs)
        raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
    service.human._post=lost
    review={**body,'decision':'approve','comment':'Review survives a lost response.'}
    assert post(client,'cases/CR-017/evidence-review',review,'engineer').status_code==503
    assert post(client,'cases/CR-017/evidence-review',review,'engineer').status_code==200
    assert len(calls)==1
    assert len(snapshot(client)['downstream']['physical']['reviews'])==1


def test_reassessment_event_passes_real_scoped_intake_without_prefetching_result(host,tmp_path):
    import asyncio
    import sqlite3
    from helpers import harness
    from mock_enterprise.config import Settings
    from program_coordinator.controls import HarnessConfig
    from coordinator.evals.phase08_4a.network import network
    execution_and_result(host)
    service=host[1];original=service.investigate;seen=[]
    async def capture(incoming,*args):
        seen.append(incoming.event)
        return await original(incoming,*args)
    service.investigate=capture
    state,_=assess(host)
    event=seen[0];result_id=state['downstream']['physical']['result']['id']
    assert result_id not in event.linked_record_ids
    isolated=tmp_path/'intake-http';isolated.mkdir()
    settings=Settings(isolated/'demo.sqlite3',isolated,True)
    # The source lifecycle correctly forbids two services owning one demo DB.
    with sqlite3.connect(host[3].db_path) as source, sqlite3.connect(settings.db_path) as target:
        source.backup(target)
    with network(settings) as (_,mcp):
        h=harness(config=HarnessConfig(mcp_url=mcp),event=event)
        asyncio.run(h.intake_case())
        assert h.state.scope_verified and not h.state.guardrail_events
        assert set(event.linked_record_ids)<=h.sources.known_ids
        assert result_id not in h.sources.known_ids
        async def read_completed_job():
            async with h.server_factory(h,'validation_evidence','completed_job_probe') as server:
                await server.list_tools()
                await server.call_tool('get_validation_job',{'job_id':state['downstream']['physical']['job']['id']})
                await server.call_tool('get_validation_coverage',{'change_id':'CR-017'})
        asyncio.run(read_completed_job())
        job=h.sources.latest('get_validation_job')
        assert any(p['kind']=='historical_snapshot' and p['record_id']=='CR-017'
                   and p['pointer'].startswith('/completion/source_snapshot/') for p in job['record_provenance'])
        assert result_id in h.sources.known_ids
        bad=harness(config=HarnessConfig(mcp_url=mcp),event=event.model_copy(update={'linked_record_ids':[*event.linked_record_ids,result_id]}))
        asyncio.run(bad.intake_case())
        assert 'unverified_linked_record' in bad.state.guardrail_events


def test_explicit_unsuccessful_reassessment_retry_is_scoped_and_idempotent(host,monkeypatch):
    from program_coordinator.control_host import downstream
    execution_and_result(host)
    original=downstream.record_assessment
    def unsuccessful(service,run,state,expected):
        state.unresolved_questions.append('Unresolved recorded intake scope.')
        return original(service,run,state,expected)
    monkeypatch.setattr(downstream,'record_assessment',unsuccessful)
    failed,body=assess(host)
    prior=failed['downstream']['assessment']['run_id']
    assert not failed['downstream']['review_ready']
    client=host[0]
    assert post(client,'cases/CR-017/assess-validation-result',{**body,'retry_run_id':'run_'+'0'*32}).status_code==409
    monkeypatch.setattr(downstream,'record_assessment',original)
    retry={**body,'retry_run_id':prior}
    first=post(client,'cases/CR-017/assess-validation-result',retry)
    second=post(client,'cases/CR-017/assess-validation-result',retry)
    assert first.status_code==second.status_code==202
    assert first.json()['run_id']==second.json()['run_id']!=prior
    assert second.json()['replayed']
    for _ in range(150):
        value=snapshot(client)
        if value['downstream']['review_ready']:break
        time.sleep(.03)
    assert value['downstream']['review_ready']
    assert post(client,'cases/CR-017/assess-validation-result',{**body,'retry_run_id':first.json()['run_id']}).status_code==409
    assert post(client,'cases/CR-017/evidence-review',{**retry,'decision':'approve','comment':'No retry argument on approvals'},'engineer').status_code==422
    assert len(value['proposals'])==1 and len(value['downstream']['physical']['reviews'])==0
