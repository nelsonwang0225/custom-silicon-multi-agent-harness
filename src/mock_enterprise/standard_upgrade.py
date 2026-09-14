"""Explicit, additive developer fixture installation. Never imported by agent/runtime APIs."""
import hashlib
import json
from .config import PROJECT
from .db import Store, connect, schema_statements, table
from .seed import check_marker, lifecycle_lock

DOCUMENTS = {
    'DOC-STD-REQUEST-019':('standard_change_request.json','standard_validation_request','requested'),
    'DOC-STD-PROC-01':('standard_validation_procedure.md','procedure','approved'),
    'DOC-STD-POLICY-01':('standard_touchless_policy.md','standard_routing_policy','approved'),
}
KINDS=('engineering.standard_request','engineering.standard_rule','validation.intake_queue','validation.intake')
PROVENANCE_MARKER='phase08_4a_request_provenance'


def extension():
    path=PROJECT/'fixtures/standard_change.json'
    if path.is_symlink():
        raise ValueError('Fixture symlinks refused')
    rows=json.loads(path.read_text())
    docs=[]
    for rid,(filename,kind,status) in DOCUMENTS.items():
        path=PROJECT/'fixtures/documents'/filename
        if path.is_symlink():
            raise ValueError('Document symlinks refused')
        content=path.read_text()
        docs.append(dict(id=rid,program_id='PRG-A17',customer_id='CUST-FML01',owning_system='engineering',
            synthetic=True,content_version=1,updated_at='2026-11-16T09:00:00Z',document_type=kind,
            document_version='1',status=status,content=content,content_hash=hashlib.sha256(content.encode()).hexdigest()))
    rows['engineering.document']=docs
    return rows


def install(settings, *, additions=None):
    settings.validate(existing=True)
    rows=extension() if additions is None else additions
    with lifecycle_lock(settings):
        con=connect(settings.db_path)
        try:
            meta=check_marker(con)
            if meta.get('phase08_4a_standard') == 1 and meta.get(PROVENANCE_MARKER) == 1:
                return
            con.execute('BEGIN EXCLUSIVE')
            if meta.get('phase08_4a_standard') == 1:
                # Add required source provenance to an already-installed CR-019
                # case. This explicit stopped-demo installer is the sole migration
                # path; normal business APIs retain document immutability.
                request=rows['engineering.standard_request'][0]
                name=table('engineering.standard_request')
                columns={row['name'] for row in con.execute(f'PRAGMA table_info({name})')}
                for field in ('request_source','requested_by'):
                    if field not in columns:
                        con.execute(f'ALTER TABLE {name} ADD COLUMN "{field}" TEXT')
                changed=con.execute(f'UPDATE {name} SET request_source=?,requested_by=? WHERE id=?',
                    (request['request_source'],request['requested_by'],request['id']))
                if changed.rowcount != 1:
                    raise ValueError('Installed standard request is missing')
                document=next(row for row in rows['engineering.document'] if row['id']==request['request_document_id'])
                trigger='immutable_engineering_document_update'
                con.execute(f'DROP TRIGGER IF EXISTS {trigger}')
                changed=con.execute('UPDATE engineering_document SET content=?,content_hash=? WHERE id=?',
                    (document['content'],document['content_hash'],document['id']))
                if changed.rowcount != 1:
                    raise ValueError('Installed standard request document is missing')
                con.execute(f"CREATE TRIGGER {trigger} BEFORE UPDATE ON engineering_document BEGIN SELECT RAISE(ABORT,'immutable record'); END")
                meta[PROVENANCE_MARKER]=1
                con.execute('UPDATE demo_metadata SET data=? WHERE id=1',(json.dumps(meta,sort_keys=True),))
                con.commit()
                return
            for kind in KINDS:
                name=table(kind)
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone():
                    continue
                for sql in schema_statements():
                    if sql.startswith(('CREATE TABLE '+name+' ', 'CREATE UNIQUE INDEX uq_'+name+'_', 'CREATE TRIGGER immutable_'+name+'_')):
                        con.execute(sql)
            store=Store(con)
            for kind in ('engineering.document','engineering.procedure','engineering.policy','engineering.change',*KINDS[:-1]):
                for record in rows.get(kind,[]):
                    # Collisions stop the installation. Existing records are never overwritten.
                    store.insert(kind,record)
            if con.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Standard fixture reference integrity failed')
            meta['phase08_4a_standard']=1
            meta[PROVENANCE_MARKER]=1
            con.execute('UPDATE demo_metadata SET data=? WHERE id=1',(json.dumps(meta,sort_keys=True),))
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
