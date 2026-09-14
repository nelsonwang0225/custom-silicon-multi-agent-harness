"""Source-owned event publication and reset. No agent imports or model calls."""
import json
import pytest
from fastapi.testclient import TestClient
from mock_enterprise.app import create_app
from mock_enterprise.config import Settings
from mock_enterprise.seed import initialize
from mock_enterprise.standard_upgrade import install as standard
from mock_enterprise.delivery_upgrade import install as delivery
from mock_enterprise.autonomous_quality import publish, records
from mock_enterprise.demo_management import current_rows, maintenance_lock, restore_source, finish_source_reset
from mock_enterprise.db import connect, Store

STAMP='2026-09-12T23:00:00Z'
HEADERS={'Authorization':'Bearer demo-reader-local-only'}

@pytest.fixture
def source(tmp_path):
    settings=Settings(tmp_path/'source.sqlite3',tmp_path,True)
    initialize(settings); standard(settings); delivery(settings)
    with TestClient(create_app(settings)) as client: yield client,settings

def rows(settings):
    con=connect(settings.db_path)
    try:return current_rows(con)
    finally:con.close()


def test_existing_demo_upgrade_preserves_records_and_supports_touchless_publication(tmp_path):
    from mock_enterprise.quality_upgrade import install
    from enterprise_api.quality_models import QualityContext
    from enterprise_api.quality_policy import standard_investigation_policy
    settings=Settings(tmp_path/'legacy.sqlite3',tmp_path,True)
    initialize(settings);standard(settings);delivery(settings)
    before=rows(settings)
    con=connect(settings.db_path)
    try:
        con.execute('ALTER TABLE manufacturing_quality_exception DROP COLUMN exception_type')
        con.execute('ALTER TABLE manufacturing_quality_exception DROP COLUMN requested_actions')
        con.execute('ALTER TABLE engineering_quality_procedure DROP COLUMN standard_policy')
    finally:con.close()
    assert rows(settings)==before # Optional defaults support legacy reads.
    install(settings);install(settings)
    assert rows(settings)==before # No fixture replacement or changed business facts.
    with TestClient(create_app(settings)) as client:
        event=publish(settings,'quality_event_upgraded',STAMP,'initial')
        response=client.get('/api/v1/manufacturing/quality-exceptions/QE-011/context',headers=HEADERS)
        assert response.status_code==200,response.text
        context=QualityContext.model_validate(response.json())
        assert context.context_digest==event.context_digest
        assert standard_investigation_policy(context)==[]
        routed=client.post('/api/v1/manufacturing/quality-investigations',
            headers={'Authorization':'Bearer demo-automation-local-only','Idempotency-Key':'upgraded-touchless'},
            json={'exception_id':'QE-011','expected_context_digest':context.context_digest,
                  'workflow_run_id':'run_upgraded','workflow_case_id':'case_upgraded'})
        assert routed.status_code in (200,201),routed.text
    after=rows(settings)
    assert all(after[k]==v for k,v in before.items())

def test_atomic_source_event_and_real_context_are_idempotent(source):
    c,s=source; before=rows(s)
    assert c.get('/api/v1/manufacturing/quality-exceptions/QE-011/context',headers=HEADERS).status_code==404
    event=publish(s,'quality_event_test',STAMP,'initial')
    assert publish(s,event.event_id,'2026-09-12T23:01:00Z','initial')==event
    result=c.get('/api/v1/manufacturing/quality-events/'+event.event_id,headers=HEADERS)
    assert result.status_code==200 and result.json()==event.model_dump(mode='json')
    value=c.get('/api/v1/manufacturing/quality-exceptions/QE-011/context',headers=HEADERS).json()
    assert value['context_digest']==event.context_digest
    assert value['exception']['lot_id']=='LOT-B-219'
    assert value['observation']['test_program_version']=='FT-B-7.2'
    assert value['analysis']['observed_rate_bps']==8800 and value['analysis']['baseline_rate_bps']==9600
    assert (value['analysis']['held_quantity'],value['analysis']['first_pass_pass_quantity'],value['analysis']['eligible_quantity'])==(100,88,0)
    assert value['analysis']['root_cause'] is None
    after=rows(s)
    assert all(after[k]==v for k,v in before.items())
    assert len(after)-len(before)==7 # includes the dedicated approved standard procedure

def test_event_has_no_public_publisher_or_authority_mutation(source):
    c,s=source;publish(s,'quality_event_test',STAMP,'initial'); before=rows(s)
    for path in ('/manufacturing/quality-events/quality_event_test','/manufacturing/quality-exceptions','/manufacturing/lots/LOT-B-219/release'):
        result=c.post('/api/v1'+path,headers={**HEADERS,'Idempotency-Key':'no-authority'},json={'disposition':'released'})
        assert result.status_code in {404,405}
    assert c.get('/api/v1/manufacturing/quality-events/quality_event_test').status_code==401
    assert rows(s)==before

def test_conflict_rolls_back_partial_publication(source):
    _,s=source
    con=connect(s.db_path)
    try:
        con.execute('BEGIN');Store(con).insert('erp.order',records()['erp.order'][0]);con.commit()
    finally:con.close()
    before=rows(s)
    with pytest.raises(ValueError,match='COLLISION'):publish(s,'quality_event_test',STAMP,'initial')
    assert rows(s)==before

def test_scoped_source_reset_removes_event_and_rejects_old_generation(source):
    c,s=source; before=rows(s);publish(s,'quality_event_test',STAMP,'initial')
    archived=[]
    with maintenance_lock(s,exclusive=True):restore_source(s,'QE-011',archive=archived.append,epoch='reset_test')
    finish_source_reset(s,'reset_test')
    assert rows(s)==before
    assert archived[0]['autonomous_event']['event_id']=='quality_event_test'
    assert c.get('/api/v1/manufacturing/quality-events/quality_event_test',headers=HEADERS).status_code==404
    with pytest.raises(ValueError,match='DEMO_STATE_CHANGED'):publish(s,'quality_event_test',STAMP,'initial')
    assert rows(s)==before


@pytest.mark.parametrize('variant', ['actions','queue','owner','procedure','type','tasks','hold','baseline','conflict','missing_policy','nonexistent_queue','retired_destination'])
def test_standard_policy_fails_closed_at_source_write_boundary(source,variant):
    c,s=source;publish(s,'quality_event_policy',STAMP,'initial')
    con=connect(s.db_path)
    try:
        con.execute('BEGIN IMMEDIATE');store=Store(con)
        q=store.get('manufacturing.quality_exception','QE-011')
        p=store.get('engineering.quality_procedure','PROC-QE-011-STD')
        if variant=='actions':store.update('manufacturing.quality_exception',q['id'],{'requested_actions':['release_material']})
        if variant=='type':store.update('manufacturing.quality_exception',q['id'],{'exception_type':'unknown'})
        if variant=='procedure':store.update('engineering.quality_procedure',p['id'],{'status':'retired'})
        if variant=='tasks':store.update('engineering.quality_procedure',p['id'],{'tasks':['Release material']})
        if variant=='missing_policy':store.update('engineering.quality_procedure',p['id'],{'standard_policy':None})
        if variant=='nonexistent_queue':
            policy=p['standard_policy'];policy['queue_id']='QUEUE-NOT-REGISTERED'
            store.update('engineering.quality_procedure',p['id'],{'queue_id':'QUEUE-NOT-REGISTERED','standard_policy':policy})
        if variant=='retired_destination':store.update('engineering.quality_procedure','PROC-QE-B-01',{'status':'retired'})
        if variant in {'queue','owner'}:
            policy=p['standard_policy'];policy['queue_status' if variant=='queue' else 'owner']='inactive' if variant=='queue' else 'Other owner'
            store.update('engineering.quality_procedure',p['id'],{'standard_policy':policy})
        if variant=='hold':store.update('manufacturing.lot','LOT-B-219',{'restrictions':[],'hold_details':[]})
        if variant=='baseline':store.update('manufacturing.quality_observation','OBS-QE-011',{'test_program_version':'UNAPPROVED'})
        if variant=='conflict':store.insert('manufacturing.quality_exception',{**q,'id':'QE-012'})
        con.commit()
    finally:con.close()
    value=c.get('/api/v1/manufacturing/quality-exceptions/QE-011/context',headers=HEADERS).json()
    from enterprise_api.quality_models import QualityContext
    from enterprise_api.quality_policy import standard_investigation_policy
    assert standard_investigation_policy(QualityContext.model_validate(value))
    before=rows(s)
    response=c.post('/api/v1/manufacturing/quality-investigations',headers={'Authorization':'Bearer demo-automation-local-only','Idempotency-Key':'blocked-standard'},
        json={'exception_id':'QE-011','expected_context_digest':value['context_digest'],'workflow_run_id':'run_policy','workflow_case_id':'case_policy'})
    assert response.status_code==409,response.text
    assert rows(s)==before
