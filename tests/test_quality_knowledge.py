"""Controlled publication tests; no operational mutation or retrieval-only fixtures."""
import hashlib
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from mock_enterprise.app import create_app
from mock_enterprise.config import Settings, PROJECT
from mock_enterprise.db import Store, connect, MODELS
from mock_enterprise.seed import initialize
from mock_enterprise.quality_upgrade import install as install_case
from mock_enterprise.quality_knowledge import DOCUMENTS, documents, install
from conftest import AUTOMATION


@pytest.fixture
def publication_db(tmp_path):
    settings = Settings(tmp_path/'source.sqlite3', tmp_path, True)
    initialize(settings, source=json.loads((PROJECT/'fixtures/seed.json').read_text()))
    install_case(settings)
    return settings


def records(settings):
    con = connect(settings.db_path)
    try:
        store = Store(con)
        return {kind:store.list(kind) for kind in MODELS if kind != 'engineering.document'}
    finally:
        con.close()


def test_quality_publications_persist_with_real_metadata_and_http_ownership(publication_db):
    before = records(publication_db)
    assert set(install(publication_db)) == set(DOCUMENTS)
    assert records(publication_db) == before
    for _ in range(2):
        with TestClient(create_app(publication_db)) as client:
            rows = client.get('/api/v1/engineering/documents?program_id=PRG-A17', headers=AUTOMATION).json()['items']
            assert set(DOCUMENTS) <= {r['id'] for r in rows}
            for expected in documents():
                r = client.get('/api/v1/engineering/documents/'+expected['id'], headers=AUTOMATION)
                assert r.status_code == 200 and r.json() == expected
                assert expected['content_hash'] == hashlib.sha256(expected['content'].encode()).hexdigest()
                assert expected['owning_system'] == 'engineering' # Existing controlled publication custodian.
                assert 'Quality' in expected['owner_team']
                assert expected['configuration_id'] == 'CFG-B-01'
                assert expected['applicable_workflows'] == ['yield_exception_recovery']
    assert records(publication_db) == before


def test_quality_publication_install_is_idempotent_and_immutable(publication_db):
    install(publication_db)
    before = publication_db.db_path.read_bytes()
    assert install(publication_db) == []
    assert publication_db.db_path.read_bytes() == before
    con = connect(publication_db.db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match='immutable'):
            Store(con).update('engineering.document', 'DOC-QA-HOLD-01', {'status':'draft'})
    finally:
        con.close()


def test_conflicting_publication_rolls_back_additions(publication_db):
    con = connect(publication_db.db_path)
    conflicting = documents()[-1]
    conflicting['title'] = 'An existing distinct publication'
    Store(con).insert('engineering.document', conflicting)
    con.close()
    with pytest.raises(ValueError, match='conflict'):
        install(publication_db)
    con = connect(publication_db.db_path)
    try:
        rows = Store(con).list('engineering.document')
        assert {r['id'] for r in rows} & DOCUMENTS.keys() == {'DOC-QA-HIST-01'}
        assert next(r for r in rows if r['id']=='DOC-QA-HIST-01')['title'] == conflicting['title']
    finally:
        con.close()


def test_default_initialization_contains_quality_publications(tmp_path):
    settings = Settings(tmp_path/'default.sqlite3',tmp_path,True)
    initialize(settings)
    assert install(settings) == []
    with TestClient(create_app(settings)) as client:
        history = client.get('/api/v1/engineering/documents/DOC-QA-HIST-01',headers=AUTOMATION).json()
        assert history['status']=='historical' and history['historical'] is True
        assert history['effective_date'] is None and history['superseded_by'] is None


def test_quality_publications_have_no_business_write_route(publication_db):
    install(publication_db)
    with TestClient(create_app(publication_db)) as client:
        for method in ('post','put','patch','delete'):
            result = getattr(client,method)('/api/v1/engineering/documents/DOC-QA-HOLD-01',headers=AUTOMATION)
            assert result.status_code == 405


def test_absent_document_metadata_preserves_legacy_critical_digest(publication_db):
    from mock_enterprise.schemas import Document
    from mock_enterprise.snapshots import critical_content
    con=connect(publication_db.db_path)
    try:
        current=Store(con).get('engineering.document','DOC-PROC-01')
    finally:
        con.close()
    optional={'title','product','configuration_id','owner_team','effective_date','superseded_by','applicable_workflows','historical'}
    legacy={k:v for k,v in current.items() if k not in optional}
    assert critical_content('engineering.document',Document.model_validate(legacy).model_dump()) == critical_content('engineering.document',legacy)
    for field,value in [('title','Changed procedural title'),('historical',True),('owner_team','Different authority')]:
        changed={**current,field:value}
        assert critical_content('engineering.document',changed)!=critical_content('engineering.document',legacy)


def test_quality_publication_does_not_stale_existing_cr017_approval(publication_db):
    from conftest import draft,approve,book,get
    with TestClient(create_app(publication_db)) as client:
        plan=draft(client)
        approval=approve(client,plan)
        before=get(client,'/validation/options?change_id=CR-017')
    install(publication_db)
    with TestClient(create_app(publication_db)) as client:
        after=get(client,'/validation/options?change_id=CR-017')
        assert before==after
        job=book(client,plan,approval)
        assert job['plan_id']==plan['id']
