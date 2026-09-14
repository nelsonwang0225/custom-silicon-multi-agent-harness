"""Explicit additive upgrade; no reseed, clock change or existing record mutation."""
from .db import connect, schema_statements
from .seed import check_marker, lifecycle_lock


def upgrade(settings):
    path = settings.validate(existing=True)
    names = ('validation_completion', 'engineering_evidence_review')
    with lifecycle_lock(settings):
        con = connect(path)
        try:
            check_marker(con)
            con.execute('BEGIN EXCLUSIVE')
            for name in names:
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone():
                    continue
                for statement in schema_statements():
                    if (statement.startswith('CREATE TABLE ' + name + ' ') or
                        statement.startswith('CREATE UNIQUE INDEX uq_' + name + '_') or
                        statement.startswith('CREATE TRIGGER immutable_' + name + '_')):
                        con.execute(statement)
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
