"""Connected delivery tests use real source HTTP/MCP and the existing CaseHarness."""
import json
import pytest
from coordinator.evals.phase08_4c.probe import environment,investigate,post
from coordinator.evals.phase08_4c.fixtures import VARIANTS,mutate


def exact(state):return {k:state['progress'][0][k] for k in ('run_id','plan_id','plan_version','plan_digest')}


def approved(env):
    state=investigate(env);ref=exact(state)
    r=post(env[0],'delivery-commitment/review',{**ref,'decision':'approve','comment':'Exact source-backed partial commitment.'},'program_owner')
    assert r.status_code==200,r.text
    return state,ref


@pytest.mark.parametrize('variant',[v for v in VARIANTS if v not in ('partial_failure','stale_proposal')])
def test_connected_delivery_variants(tmp_path,variant):
    with environment(tmp_path,variant) as env:
        client,host,double,settings=env;before=host.delivery.context().model_dump(mode='json');state=investigate(env)
        assert state['runs'][0]['status']=='completed',json.dumps(state)
        assert double.harnesses[0].runner.peak_active==3
        assert state['runs'][0]['recommendation']['delivery']['eligible_quantity']==before['analysis']['eligible_quantity']
        if not before['analysis']['proposal_allowed']:
            assert state['status']=='readiness_blocked' and not state['records']['plans']
            assert state['runs'][0]['recommendation']['policy_path']=='escalation_required'
            return
        assert state['status']=='awaiting_review',state
        ref=exact(state)
        for role in ('automation','reader','engineer'):
            assert post(client,'delivery-commitment/review',{**ref,'decision':'approve'},role).status_code==403
        assert post(client,'delivery-commitment/execute',ref).status_code==409
        assert post(client,'delivery-commitment/review',{**ref,'decision':'approve'},'program_owner').status_code==200
        result=post(client,'delivery-commitment/execute',ref)
        assert result.status_code==200,result.text
        assert result.json()['status']=='verified'
        assert post(client,'delivery-commitment/execute',ref).json()['status']=='verified'
        after=host.delivery.context().model_dump(mode='json')
        assert after['input_digest']==before['input_digest']
        assert after['commitment']['quantity']==min(before['analysis']['eligible_quantity'],before['request']['quantity'])
        assert after['commitment']['committed_at']==before['analysis']['proposed_at']
        assert after['commitment']['customer_agreement']=='pending' and after['commitment']['allocation_changed'] is False
        records=host.delivery.records();assert len(records.plans)==len(records.decisions)==len(records.commitments)==len(records.links)==1
        assert client.get('/control-api/runs/'+ref['run_id'],headers={'X-Stratos-Demo-Profile':'automation'}).status_code==200
        assert client.get('/control-api/workflows/delivery_readiness',headers={'X-Stratos-Demo-Profile':'automation'}).json()['mode']=='Connected'
        repeat=investigate(env,'ui_delivery_repeat')
        assert repeat['status']=='commitment_current' and len(host.delivery.records().commitments)==1


@pytest.mark.parametrize('operation,fault',[('erp','unknown_committed'),('erp','unknown_uncommitted'),('erp','readback_unavailable'),('erp','readback_mismatch'),('planner','known_failure'),('planner','unknown_committed')])
def test_partial_and_unknown_outcome_recovery(tmp_path,monkeypatch,operation,fault):
    from program_coordinator.application.execution_models import SourceFailure,SourceReadFailure
    with environment(tmp_path) as env:
        client,host,double,settings=env;state,ref=approved(env)
        name='delivery_commit' if operation=='erp' else 'delivery_link';write=getattr(host.source,name);read=host.source.read.get_delivery_records
        called=[];written=False
        def altered_write(body,key):
            nonlocal written
            called.append(key)
            if fault=='unknown_uncommitted':raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
            if fault=='known_failure':raise SourceFailure('SOURCE_WRITE_REJECTED')
            value=write(body,key);written=True
            if fault=='unknown_committed':raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
            return value
        def altered_read(*args):
            if written and fault=='readback_unavailable':raise SourceReadFailure('SOURCE_READ_FAILED')
            data=read(*args)
            if written and fault=='readback_mismatch':data['commitments'][0]['quantity']=599
            return data
        monkeypatch.setattr(host.source,name,altered_write);monkeypatch.setattr(host.source.read,'get_delivery_records',altered_read)
        result=post(client,'delivery-commitment/execute',ref)
        assert result.status_code in (409,502,503),result.text
        progress=host.delivery.load(ref['run_id']);assert progress.status!='verified'
        assert len(called)==1
        if operation=='planner':
            assert progress.status=='partial_completion' and progress.steps['erp'].status=='verified'
            assert len(read('DR-009')['commitments'])==1
        monkeypatch.setattr(host.source,name,write);monkeypatch.setattr(host.source.read,'get_delivery_records',read)
        # Reconstruct the executor from durable storage, as after a host restart.
        from program_coordinator.application.delivery_commitment import DeliveryCommitmentService
        from program_coordinator.application.store import ActivityStore
        host.delivery=DeliveryCommitmentService(ActivityStore(host.store.directory),host.source,host.human)
        result=post(client,'delivery-commitment/execute',ref)
        assert result.status_code==200,result.text
        assert result.json()['status']=='verified'
        assert result.json()['steps'][operation]['key']==called[0]
        assert len(host.delivery.records().commitments)==len(host.delivery.records().links)==1


def test_stale_commercial_state_and_changed_inventory(tmp_path):
    with environment(tmp_path) as env:
        state,ref=approved(env)
        mutate(env[3],lambda s:s.update('erp.delivery_state','STATE-DR-009',{'record_version':2}))
        assert post(env[0],'delivery-commitment/execute',ref).status_code==409
        assert not env[1].delivery.records().commitments
        state=investigate(env,'ui_reassess');ref=exact(state)
        mutate(env[3],lambda s:s.update('manufacturing.quality_material','MAT-B-203',{'eligible_unallocated_quantity':500,'content_version':2}))
        assert post(env[0],'delivery-commitment/review',{**ref,'decision':'approve'},'program_owner').status_code==409


def test_typed_claims_and_metadata_boundaries(tmp_path):
    from program_coordinator.sources import validate_assessment,validate_final,assert_scope
    from program_coordinator.controls import HarnessError,TOOL_MATRIX
    from program_coordinator.application.delivery_models import DeliveryProgress
    with environment(tmp_path) as env:
        state=investigate(env);h=env[2].harnesses[0];result=h.state.completed_assessments[0].assessment
        for field,value in [('eligible_quantity',1000),('held_quantity',0),('gap_quantity',0),('order_id','ORD-OTHER'),('proposed_at','2026-11-17T09:00:00Z')]:
            with pytest.raises(HarnessError):validate_assessment(result.model_copy(update={'delivery':result.delivery.model_copy(update={field:value})}),h.sources,None)
        for text in ['Customer accepted split delivery.','The held material can ship.','Future supply is guaranteed.']:
            with pytest.raises(HarnessError):validate_final(h.state.final_package.model_copy(update={'change_summary':text}),h.sources,h.state,None)
        finding=result.findings[0];f=finding.facts[0]
        with pytest.raises(HarnessError):validate_assessment(result.model_copy(update={'findings':[finding.model_copy(update={'facts':[f.model_copy(update={'value_json':'"fabricated"'})]})]}),h.sources,None)
        assert not {'context','order','material','allocations','configuration','evidence','quantity','requested_at'} & DeliveryProgress.model_fields.keys()
        assert sum(c['tool']=='get_delivery_context' for c in h.sources.calls)==1
        for role in ('manufacturing','validation_evidence','program_commercial'):assert {t['name'] for t in h.catalog[role]}==TOOL_MATRIX[role]|{'get_delivery_context'}
        assert not any(c['tool']=='get_customer_order' and c['role']!='program_commercial' for c in h.sources.calls)
        with pytest.raises(HarnessError):assert_scope({'program_id':'other'},'CUST-FML01','PRG-A17')
        assert post(env[0],'cases/DR-009/investigations',{'invocation_id':'ui_wrong','change_id':'QE-004','workflow_id':'delivery_readiness'}).status_code==422


def test_duplicate_analysis_retains_exact_source_plan(tmp_path):
    with environment(tmp_path) as env:
        first=investigate(env);second=investigate(env,'ui_delivery_second')
        assert first['progress'][0]['plan_id']==second['progress'][0]['plan_id']
        assert len(env[1].delivery.records().plans)==1
