"""Explicit developer-only additive installation; never imported by agent runtime."""
import json
from .config import PROJECT
from .db import Store,connect,schema_statements,table
from .seed import check_marker,lifecycle_lock

KINDS=('manufacturing.quality_exception','manufacturing.quality_material','manufacturing.quality_observation','manufacturing.quality_baseline',
       'engineering.quality_procedure','manufacturing.quality_investigation','manufacturing.recovery_plan','manufacturing.recovery_decision','planner.recovery_task')

def extension():
    return json.loads((PROJECT/'fixtures/quality_exception.json').read_text())

def install(settings,*,additions=None):
    settings.validate(existing=True)
    with lifecycle_lock(settings):
        con=connect(settings.db_path)
        try:
            meta=check_marker(con)
            con.execute('BEGIN EXCLUSIVE')
            for kind in KINDS:
                name=table(kind)
                if con.execute("SELECT 1 FROM sqlite_master WHERE name=?",(name,)).fetchone():continue
                for sql in schema_statements():
                    if sql.startswith(('CREATE TABLE '+name+' ','CREATE UNIQUE INDEX uq_'+name+'_','CREATE TRIGGER immutable_'+name+'_')):con.execute(sql)
            # Existing demos predate the optional QE-011 policy fields. Add only
            # these known columns through the stopped-demo installer; never seed
            # facts, reset data, or infer touchless eligibility for older records.
            additions_by_table = {
                'erp_order': {
                    'planning_unit_value_cents': 'INTEGER',
                    'planning_value_basis': 'TEXT',
                },
                'manufacturing_quality_exception': {
                    'exception_type': 'TEXT',
                    'requested_actions': "TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(requested_actions))",
                },
                'engineering_quality_procedure': {
                    'standard_policy': 'TEXT CHECK(standard_policy IS NULL OR json_valid(standard_policy))',
                },
                'manufacturing_recovery_plan': {
                    'workstreams': "TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(workstreams))",
                },
                'manufacturing_recovery_decision': {
                    'submission_digest': 'TEXT',
                    'recommendation': 'TEXT',
                    'business_context': 'TEXT',
                },
                'planner_recovery_task': {
                    'submission_digest': 'TEXT',
                    'approved_recommendation': 'TEXT',
                    'business_context': 'TEXT',
                    'workstreams': "TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(workstreams))",
                },
            }
            for name, fields in additions_by_table.items():
                columns={row['name'] for row in con.execute(f'PRAGMA table_info({name})')}
                for field, sqltype in fields.items():
                    if field not in columns:
                        con.execute(f'ALTER TABLE {name} ADD COLUMN "{field}" {sqltype}')
            if meta.get('phase08_4b_quality'):
                con.commit()
                return
            for kind,records in (extension() if additions is None else additions).items():
                for record in records:Store(con).insert(kind,record)
            if con.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Quality reference integrity failed')
            meta['phase08_4b_quality']=1
            con.execute('UPDATE demo_metadata SET data=? WHERE id=1',(json.dumps(meta,sort_keys=True),));con.commit()
        except Exception:con.rollback();raise
        finally:con.close()
