import json
import pytest
from coordinator.evals.phase08_4b.probe import environment,investigate,post
from coordinator.evals.phase08_4b.fixtures import VARIANTS

def exact(state):
    p=state['progress'][0]
    return {k:p[k] for k in ('run_id','plan_id','plan_version','plan_digest')}

def submit(client,ref,role='automation'):
    return post(client,'quality-recovery/submit',{**ref,
        'submission_id':'ui_quality_operator_handoff',
        'subject':'QE-004 recovery proposal for LOT-B-204',
        'recommendation':'Proceed with released-supply recovery planning and keep the held lot governed.',
        'business_context':'The held lot contributes no eligible supply; the current 200-unit gap remains open.',
        'operator_notes':'Reviewed by the Program Operator.'},role)

@pytest.mark.parametrize('variant',VARIANTS)
def test_connected_quality_lifecycle(tmp_path,variant):
    with environment(tmp_path,variant) as env:
        client,host,double,settings=env;before=host.quality.context().model_dump(mode='json')
        state=investigate(env)
        assert state['runs'][0]['status']=='completed',json.dumps(state)
        assert state['status']=='draft_ready',json.dumps(state)
        assert double.harnesses[0].runner.peak_active==3
        recommendation=state['runs'][0]['recommendation']
        assert recommendation['quality']['root_cause'] is None
        actions=recommendation['recommended_next_step']
        assert all(label in actions for label in (
            '1. Contain LOT-B-204','2. Investigate SITE-2',
            '3. Execute a controlled recovery','4. Protect MS-HEL-800'))
        analysis=state['context']['analysis']
        assert all(value in actions for value in ('80/125','120/125','250'))
        assert all(str(analysis[field]) in actions for field in (
            'eligible_quantity','requested_quantity','gap_quantity'))
        if variant=='comparable':
            assert all(value in actions for value in ('600','800','200','LOT-B-203'))
        assert 'Quality-authorized' in actions and 'ERP commitment' in actions
        assert state['context']['analysis']['affected_eligible_quantity']==0
        ref=exact(state)
        assert not client.get('/control-api/decisions',headers={'X-Stratos-Demo-Profile':'program_owner'}).json()
        assert post(client,'quality-recovery/review',{**ref,'decision':'approve'},'program_owner').status_code==409
        for role in ('engineer','program_owner','reader'):
            assert submit(client,ref,role).status_code==403
        submitted=submit(client,ref)
        assert submitted.status_code==200 and submitted.json()['status']=='awaiting_review'
        queue=client.get('/control-api/decisions',headers={'X-Stratos-Demo-Profile':'program_owner'}).json()
        assert len(queue)==1 and queue[0]['change_id']=='QE-004'
        for role in ('automation','engineer','reader'):
            r=post(client,'quality-recovery/review',{**ref,'decision':'approve','comment':'Recovery planning only'},role)
            assert r.status_code==403,r.text
        decision=post(client,'quality-recovery/review',{**ref,'decision':'approve','comment':'Recovery planning only'},'program_owner')
        assert decision.status_code==200,decision.text
        result=post(client,'quality-recovery/execute',ref)
        assert result.status_code==200,result.text
        assert result.json()['status']=='verified'
        assert post(client,'quality-recovery/execute',ref).json()['status']=='verified'
        assert host.quality.context().model_dump(mode='json')==before
        records=host.quality.records();assert len(records.tasks)==len(records.investigations)==len(records.plans)==len(records.decisions)==1
        assert records.tasks[0].commitment_changed is False
        assert client.get('/control-api/workflows/yield_exception_recovery',headers={'X-Stratos-Demo-Profile':'automation'}).json()['mode']=='Connected'
        assert client.get('/control-api/runs/'+ref['run_id'],headers={'X-Stratos-Demo-Profile':'automation'}).status_code==200
        replay=post(client,'workflows/yield_exception_recovery/runs',{'invocation_id':'ui_quality_first','change_id':'QE-004','workflow_id':'yield_exception_recovery'})
        assert replay.json()['replayed'] and double.calls==1

@pytest.mark.parametrize('fault',['unknown_committed','unknown_no_write','readback_unavailable','readback_mismatch'])
def test_quality_reconciliation(tmp_path,monkeypatch,fault):
    from program_coordinator.application.execution_models import SourceFailure,SourceReadFailure
    with environment(tmp_path) as env:
        client,host,double,settings=env;write=host.source.quality_investigate;read=host.source.read.get_quality_records;calls=[];committed=False
        def altered_write(*args):
            nonlocal committed
            calls.append(args)
            if fault=='unknown_no_write':raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
            value=write(*args);committed=True
            if fault=='unknown_committed':raise SourceFailure('SOURCE_OUTCOME_UNKNOWN',unknown=True)
            return value
        def altered_read(*args):
            if committed and fault=='readback_unavailable':raise SourceReadFailure('SOURCE_READ_FAILED')
            value=read(*args)
            if committed and fault=='readback_mismatch':value['investigations'][0]['owner']='Unrelated queue'
            return value
        monkeypatch.setattr(host.source,'quality_investigate',altered_write)
        monkeypatch.setattr(host.source.read,'get_quality_records',altered_read)
        state=investigate(env)
        assert state['status'] in {'outcome_unknown','verification_failed'},json.dumps(state)
        p=state['progress'][0];assert len(calls)==1
        monkeypatch.setattr(host.source,'quality_investigate',write);monkeypatch.setattr(host.source.read,'get_quality_records',read)
        recovered=post(client,'quality-recovery/reconcile',{'run_id':p['run_id']})
        assert recovered.status_code==200,recovered.text
        assert recovered.json()['status']=='draft_ready'
        assert len(host.quality.records().investigations)==1
        assert len(host.quality.records().plans)==1


def test_changed_source_rejects_approval_and_execution(tmp_path):
    from mock_enterprise.db import connect,Store
    with environment(tmp_path) as env:
        client,host,double,settings=env;state=investigate(env);ref=exact(state)
        con=connect(settings.db_path);Store(con).update('manufacturing.quality_observation','OBS-QE-004',{'content_version':2});con.close()
        assert post(client,'quality-recovery/review',{**ref,'decision':'approve'},'program_owner').status_code==409
        assert post(client,'quality-recovery/execute',ref).status_code==409
        assert not host.quality.records().decisions and not host.quality.records().tasks


def test_claims_scope_and_evidence_fail_closed(tmp_path):
    from program_coordinator.sources import validate_assessment,validate_final
    from program_coordinator.controls import HarnessError
    with environment(tmp_path) as env:
        state=investigate(env);h=env[2].harnesses[0];result=h.state.completed_assessments[0].assessment
        for field,value in [('root_cause','The tester'),('eligible_quantity',800),('affected_eligible_quantity',200),('lot_id','LOT-4491')]:
            bad=result.model_copy(update={'quality':result.quality.model_copy(update={field:value})})
            with pytest.raises(HarnessError):validate_assessment(bad,h.sources,{r.source_id for r in result.source_references})
        for text in ('The tester caused the failures.','The silicon is defective.','The held lot can ship.','Delivery will miss.'):
            bad=h.state.final_package.model_copy(update={'change_summary':text})
            with pytest.raises(HarnessError):validate_final(bad,h.sources,h.state,{r.source_id for r in h.state.source_references})
        finding=result.findings[0];fact=finding.facts[0]
        bad=result.model_copy(update={'findings':[finding.model_copy(update={'facts':[fact.model_copy(update={'value_json':'"invented"'})]})]})
        with pytest.raises(HarnessError):validate_assessment(bad,h.sources,{r.source_id for r in result.source_references})
        # Operational data are source-owned; index contains only workflow references/attempt metadata.
        from program_coordinator.application.quality_recovery_models import QualityProgress
        assert not {'context','material','order','observation','procedure','lot','root_cause'} & QualityProgress.model_fields.keys()
        assert sum(c['tool']=='get_quality_context' for c in h.sources.calls)==1
        assert not any(c['tool']=='get_customer_order' and c['role']!='program_commercial' for c in h.sources.calls)
        for r in ('manufacturing','validation_evidence','program_commercial'):
            from program_coordinator.controls import TOOL_MATRIX
            assert {t['name'] for t in h.catalog[r]}==TOOL_MATRIX[r]|{'get_quality_context'}
        body={'invocation_id':'ui_wrong_quality','change_id':'CR-017','workflow_id':'yield_exception_recovery'}
        assert post(env[0],'cases/QE-004/investigations',body).status_code==422


def test_same_source_rerun_deduplicates_source_work(tmp_path):
    with environment(tmp_path) as env:
        first=investigate(env);second=investigate(env,'ui_quality_again')
        assert first['progress'][0]['plan_id']==second['progress'][0]['plan_id']
        assert len(env[1].quality.records().investigations)==len(env[1].quality.records().plans)==1
