"""Allowlisted business publications; explicit additive installation into an owned demo.

Only controlled document rows are inserted. No operational case record is changed.
The shared retrieval service ingests these through the existing document HTTP API.
"""
import hashlib
from .config import PROJECT
from .db import Store, connect
from .seed import check_marker, lifecycle_lock
from .schemas import Document

DOCUMENTS = {
    'DOC-QA-HOLD-01': ('quality_hold_disposition_sop.md', 'Quality Hold & Disposition SOP', 'quality_sop', 'approved', 'Product Quality / Manufacturing'),
    'DOC-QA-EXCURSION-01': ('quality_excursion_investigation.md', 'Final-Test Excursion Investigation Procedure', 'manufacturing_procedure', 'approved', 'Product / Test Engineering with Product Quality / Manufacturing'),
    'DOC-QA-HIST-01': ('quality_historical_site_investigation.md', 'Historical Investigation — Test-Site Concentration', 'historical_investigation', 'historical', 'Product Quality / Manufacturing'),
}


def documents():
    result = []
    for rid, (filename, title, kind, status, owner) in DOCUMENTS.items():
        path = PROJECT / 'fixtures/documents' / filename
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(PROJECT):
            raise ValueError('Document symlinks and traversal are refused')
        content = path.read_text()
        result.append(Document(id=rid, title=title, document_type=kind, status=status,
            document_version='1', content_version=1, updated_at='2026-08-01T00:00:00Z',
            program_id='PRG-A17', customer_id='CUST-FML01', owning_system='engineering',
            product='ACCELERATOR-X', configuration_id='CFG-B-01', owner_team=owner,
            effective_date=None if status == 'historical' else '2026-08-01T00:00:00Z',
            superseded_by=None, historical=status == 'historical',
            applicable_workflows=['yield_exception_recovery'], content=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest()).model_dump(mode='json'))
    return result


def install(settings):
    settings.validate(existing=True)
    expected = documents()
    with lifecycle_lock(settings):
        con = connect(settings.db_path)
        try:
            check_marker(con)
            con.execute('BEGIN EXCLUSIVE')
            columns = {r['name'] for r in con.execute('PRAGMA table_info(engineering_document)')}
            # New optional publication metadata only; immutable existing bodies stay untouched.
            for name in ('title', 'product', 'configuration_id', 'owner_team', 'effective_date', 'superseded_by', 'applicable_workflows', 'historical'):
                if name not in columns:
                    sqltype = 'INTEGER NOT NULL DEFAULT 0' if name == 'historical' else 'TEXT'
                    con.execute(f'ALTER TABLE engineering_document ADD COLUMN "{name}" {sqltype}')
            store = Store(con)
            installed = {r['id']: r for r in store.list('engineering.document')}
            added = []
            for row in expected:
                if row['id'] in installed:
                    if installed[row['id']] != row:
                        raise ValueError('Quality document identity/version conflict; existing publication preserved')
                else:
                    store.insert('engineering.document', row)
                    added.append(row['id'])
            if con.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Quality publication reference integrity failed')
            con.commit()
            return added
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
