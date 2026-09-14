"""Real source contract tests against isolated SQLite and FastAPI; no model calls."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from enterprise_api.standard_models import StandardContext, StandardIntakeInput, StandardRequest
from enterprise_api.standard_policy import evaluate,build_package
from mock_enterprise.app import create_app
from mock_enterprise.config import Settings
from mock_enterprise.db import read_store,connect,Store
from mock_enterprise.core import IDENTITIES
from mock_enterprise.standard_upgrade import install
from coordinator.evals.phase08_4a.fixtures import prepare,VARIANTS

H={'Authorization':'Bearer demo-automation-local-only','Idempotency-Key':'standard-test'}
PATH='/api/v1/validation/changes/CR-019/intakes'

@pytest.fixture
def standard(tmp_path):
    settings=Settings(tmp_path/'standard.sqlite3',tmp_path,True)
    prepare(settings)
    with TestClient(create_app(settings)) as client:
        yield settings,client

def read_context(client):
    result=client.get('/api/v1/engineering/changes/CR-019/standard-context',headers=H)
    assert result.status_code==200,result.text
    return StandardContext.model_validate(result.json())

def package_body(client):
    c=read_context(client)
    return StandardIntakeInput(package=build_package(c,run_id='run_test',case_id='case_test'),expected_context_digest=c.context_digest).model_dump(mode='json')

def source_counts(settings):
    with read_store(settings.db_path) as store:
        return {k:len(store.list(k)) for k in ['engineering.plan','engineering.decision','validation.job','validation.reservation','validation.result','planner.link','planner.task','validation.intake']}

def test_success_exact_package_idempotency_and_independent_readback(standard):
    settings,client=standard;before=source_counts(settings)
    context=read_context(client);eligibility=evaluate(context)
    assert eligibility.touchless_eligible
    assert eligibility.reusable_evidence_ids==['RES-BASELINE-B']
    assert eligibility.remaining_work and not eligibility.requires_human_approval_for_handoff
    body=package_body(client)
    result=client.post(PATH,headers=H,json=body)
    assert result.status_code==201,result.text
    intake=result.json()
    assert intake['status']=='received' and intake['lab_authorization']=='pending'
    assert intake['physical_testing']=='not_started' and intake['customer_acceptance']=='pending'
    assert intake['downstream_owner']=='Atlas Validation Operations'
    read=client.get('/api/v1/validation/intakes/'+intake['id'],headers=H)
    assert read.json()==intake
    replay=client.post(PATH,headers=H,json=body)
    assert replay.status_code==201 and replay.headers['Idempotency-Replayed']=='true' and replay.json()==intake
    duplicate=client.post(PATH,headers={**H,'Idempotency-Key':'second-key'},json=body)
    assert duplicate.status_code==409 and duplicate.json()['error']['code']=='ACTION_ALREADY_RECORDED'
    after=source_counts(settings)
    assert after=={**before,'validation.intake':1}
    audit=client.get('/api/v1/audit/events?change_id=CR-019',headers=H).json()
    assert 'create_standard_validation_intake' in json.dumps(audit)


def test_standard_request_provenance_is_engineering_source_data(standard):
    _,client=standard
    context=read_context(client)
    assert context.request.owning_system=='engineering'
    assert context.request.request_source=='customer_intake'
    assert context.request.requested_by=='Helios AI / acceptance package coordination'
    assert json.loads(context.request_document['content'])==context.request.model_dump(mode='json')


def test_standard_request_missing_provenance_is_rejected_explicitly():
    from mock_enterprise.standard_upgrade import extension
    request=extension()['engineering.standard_request'][0]
    for field in ('request_source','requested_by'):
        incomplete=deepcopy(request);incomplete.pop(field)
        with pytest.raises(ValueError):
            StandardRequest.model_validate(incomplete)

@pytest.mark.parametrize('variant',[v for v in VARIANTS if v!='success'])
def test_ineligible_source_variants_stop_with_zero_intake(tmp_path,variant):
    settings=Settings(tmp_path/'source.sqlite3',tmp_path,True);prepare(settings,variant)
    with TestClient(create_app(settings)) as client:
        c=read_context(client); e=evaluate(c)
        assert not e.touchless_eligible and any(not r.passed for r in e.checks)
        with pytest.raises(ValueError,match='STANDARD_POLICY_INELIGIBLE'):
            build_package(c,run_id='run_negative',case_id='case_negative')
        assert source_counts(settings)['validation.intake']==0

@pytest.mark.parametrize('field,value',[('procedure_content_version',99),('downstream_owner','Different owner'),('requested_at','2026-11-17T12:00:00Z'),('sample_ids',['SAMPLE-B-018']),('remaining_work',[]),('reusable_evidence_ids',[]),('configuration',None)])
def test_package_cannot_widen_or_replace_approved_scope(standard,field,value):
    settings,client=standard;body=package_body(client);body['package'][field]=value
    result=client.post(PATH,headers=H,json=body)
    assert result.status_code in (409,422),result.text
    assert source_counts(settings)['validation.intake']==0

@pytest.mark.parametrize('role',['reader','engineer','lab'])
def test_only_automation_can_create_intake(standard,role):
    settings,client=standard
    result=client.post(PATH,headers={**H,'Authorization':f'Bearer demo-{role}-local-only'},json=package_body(client))
    assert result.status_code==403
    assert source_counts(settings)['validation.intake']==0

@pytest.mark.parametrize('field,value',[('customer_id','CUST-NORTH'),('program_id','PRG-P01'),('change_id','CR-017')])
def test_cross_scope_and_wrong_case_denied(standard,field,value):
    settings,client=standard;body=package_body(client);body['package'][field]=value
    result=client.post(PATH,headers=H,json=body)
    assert result.status_code in (404,409,422)
    assert source_counts(settings)['validation.intake']==0

def test_stale_context_rejected_and_criteria_not_writable(standard):
    settings,client=standard;body=package_body(client);body['expected_context_digest']='0'*64
    assert client.post(PATH,headers=H,json=body).status_code==409
    for extra in ['approval_id','schedule_job','criteria_override','owner_override']:
        payload={**package_body(client),extra:True}
        assert client.post(PATH,headers=H,json=payload).status_code==422
    assert source_counts(settings)['validation.intake']==0

def test_install_is_additive_and_idempotent(tmp_path):
    from mock_enterprise.seed import initialize
    settings=Settings(tmp_path/'source.sqlite3',tmp_path,True);initialize(settings)
    with read_store(settings.db_path) as store:
        before={k:store.list(k) for k in ['engineering.change','engineering.requirement','engineering.configuration','validation.job','validation.result','planner.milestone']}
    install(settings);install(settings)
    with read_store(settings.db_path) as store:
        for k,rows in before.items():
            current={r['id']:r for r in store.list(k)}
            assert all(current[r['id']]==r for r in rows)
        assert len(store.list('engineering.standard_request'))==1


def test_install_migrates_existing_standard_request_provenance(tmp_path):
    from mock_enterprise.standard_upgrade import PROVENANCE_MARKER
    settings=Settings(tmp_path/'source.sqlite3',tmp_path,True);prepare(settings)
    con=connect(settings.db_path)
    try:
        request=Store(con).get('engineering.standard_request','STD-REQUEST-019')
        request.pop('request_source');request.pop('requested_by')
        content=json.dumps(request,indent=2)+'\n'
        meta=json.loads(con.execute('SELECT data FROM demo_metadata WHERE id=1').fetchone()['data'])
        meta.pop(PROVENANCE_MARKER)
        con.execute('BEGIN EXCLUSIVE')
        con.execute('DROP TRIGGER immutable_engineering_document_update')
        con.execute('UPDATE engineering_document SET content=?,content_hash=? WHERE id=?',
            (content,hashlib.sha256(content.encode()).hexdigest(),'DOC-STD-REQUEST-019'))
        con.execute('ALTER TABLE engineering_standard_request DROP COLUMN request_source')
        con.execute('ALTER TABLE engineering_standard_request DROP COLUMN requested_by')
        con.execute('UPDATE demo_metadata SET data=? WHERE id=1',(json.dumps(meta,sort_keys=True),))
        con.commit()
    finally:con.close()
    install(settings)
    with read_store(settings.db_path) as store:
        request=store.get('engineering.standard_request','STD-REQUEST-019')
        document=store.get('engineering.document','DOC-STD-REQUEST-019')
        assert request['request_source']=='customer_intake'
        assert request['requested_by']=='Helios AI / acceptance package coordination'
        assert json.loads(document['content'])==request

def test_standard_client_reads(standard):
    from enterprise_api import EnterpriseClient,ClientConfig,Scope
    from enterprise_api.transport import HttpxReadTransport
    settings,server=standard
    conf=ClientConfig(scope=Scope(program_id='PRG-A17',customer_id='CUST-FML01'))
    client=EnterpriseClient(conf,transport=HttpxReadTransport(conf,http_client=server))
    assert client.get_standard_change_context('CR-019')==read_context(server).model_dump(mode='json')
    assert len(client.get_standard_change_requests('PRG-A17')['items'])==1
    assert client.get_standard_validation_intakes('CR-019')['items']==[]
    item=server.post(PATH,headers=H,json=package_body(server)).json()
    assert client.get_standard_validation_intake(item['id'])==item
    assert client.get_standard_validation_intakes('CR-019')['items']==[item]


def test_shared_standard_policy_modules_have_no_business_access():
    import ast
    from enterprise_api import standard_models,standard_policy
    forbidden={'httpx','requests','urllib','sqlite3','mock_enterprise','subprocess','openai','agents','stratos_mcp'}
    for module in (standard_models,standard_policy):
        tree=ast.parse(Path(module.__file__).read_text())
        for node in ast.walk(tree):
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            assert not any(n and n.split('.')[0] in forbidden for n in names)

def test_standard_install_preserves_material_critical_source_set(tmp_path):
    from mock_enterprise.seed import initialize
    from mock_enterprise.core import IDENTITIES
    settings=Settings(tmp_path/'source.sqlite3',tmp_path,True);initialize(settings)
    def snapshots():
        with TestClient(create_app(settings)) as client:
            response=client.get('/api/v1/validation/options?change_id=CR-017',headers=H)
            assert response.status_code==200,response.text
            return response.json()['items'][0]['expected_source_versions']
    before=snapshots();install(settings)
    assert snapshots()==before
    # Existing critical procedure updates are still detected exactly.
    con=connect(settings.db_path)
    with con:
        Store(con).update('engineering.procedure','PROC-LC-02',{'content_version':2})
    con.close()
    assert snapshots()!=before
