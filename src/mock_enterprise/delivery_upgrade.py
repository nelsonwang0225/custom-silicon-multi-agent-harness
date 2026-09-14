"""Explicit additive source installation. Never used by runtime agents."""
import json
from .config import PROJECT
from .db import Store, connect, schema_statements, table, DELIVERY_MODELS
from .seed import check_marker, lifecycle_lock


def extension():
    return json.loads((PROJECT/'fixtures/delivery_readiness.json').read_text())


def install(settings, *, additions=None):
    settings.validate(existing=True)
    # Shared Manufacturing inventory is installed once and never cloned or reset.
    from .quality_upgrade import install as install_quality
    install_quality(settings)
    with lifecycle_lock(settings):
        con=connect(settings.db_path)
        try:
            meta=check_marker(con)
            if meta.get('phase08_4c_delivery'):return
            con.execute('BEGIN EXCLUSIVE')
            for kind in DELIVERY_MODELS:
                name=table(kind)
                if con.execute('SELECT 1 FROM sqlite_master WHERE name=?',(name,)).fetchone():continue
                for sql in schema_statements():
                    if sql.startswith(('CREATE TABLE '+name+' ','CREATE UNIQUE INDEX uq_'+name+'_','CREATE TRIGGER immutable_'+name+'_')):con.execute(sql)
            for kind,rows in (extension() if additions is None else additions).items():
                for row in rows:Store(con).insert(kind,row)
            if con.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Delivery reference integrity failed')
            meta['phase08_4c_delivery']=1
            con.execute('UPDATE demo_metadata SET data=? WHERE id=1',(json.dumps(meta,sort_keys=True),));con.commit()
        except Exception:con.rollback();raise
        finally:con.close()
