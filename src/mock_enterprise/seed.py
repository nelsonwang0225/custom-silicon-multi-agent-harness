"""Explicit local seed/reset only. No runtime imports of developer expectations."""
import copy
import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

from .config import PROJECT
from .core import at, canonical, digest
from .db import MODELS, REFS, Store, connect, schema_statements, table

MARKER = 'mock-enterprise-local-demo-v1'
SEED_MAP = {
    'suppliers': 'engineering.supplier', 'customers': 'engineering.customer',
    'configurations': 'engineering.configuration', 'workload_profiles': 'engineering.workload',
    'requirement_revisions': 'engineering.requirement', 'changes': 'engineering.change',
    'procedures': 'engineering.procedure', 'acceptance_criteria': 'engineering.criteria',
    'approval_policies': 'engineering.policy', 'document_manifest': 'engineering.document',
    'plans': 'engineering.plan', 'decisions': 'engineering.decision',
    'results': 'validation.result', 'labs': 'validation.lab', 'slots': 'validation.slot',
    'samples': 'validation.sample', 'jobs': 'validation.job', 'reservations': 'validation.reservation',
    'lots': 'manufacturing.lot', 'units': 'manufacturing.unit', 'orders': 'erp.order',
    'cost_rates': 'erp.rate', 'programs': 'planner.program', 'milestones': 'planner.milestone',
    'implementation_links': 'planner.link', 'tasks': 'planner.task',
}
DOCUMENT_PATHS = {
    'DOC-REQUEST-01': 'fixtures/documents/customer_change_request.md',
    'DOC-BASELINE-01': 'fixtures/documents/approved_baseline.md',
    'DOC-CONFIG-01': 'fixtures/documents/configuration_scope.md',
    'DOC-PROC-01': 'fixtures/documents/supplemental_validation_procedure.md',
    'DOC-POLICY-01': 'fixtures/documents/approval_policy.md',
    'DOC-PLAYBOOK-01': 'fixtures/documents/change_control_playbook.md',
}
LIST_REFS = {'supported_configuration_ids': 'engineering.configuration',
             'supported_procedure_ids': 'engineering.procedure',
             'permitted_procedure_ids': 'engineering.procedure', 'milestone_ids': 'planner.milestone'}


def load_seed(source=None):
    seed = copy.deepcopy(source) if source is not None else json.loads((PROJECT / 'fixtures/seed.json').read_text())
    if seed['meta']['schema_version'] != '1.1' or not seed['meta']['synthetic']:
        raise ValueError('Unsupported synthetic seed')
    now = at(seed['meta']['scenario_now'])
    rows = {}
    for domain in ('engineering', 'validation', 'manufacturing', 'erp', 'planner'):
        for group, records in seed[domain].items():
            kind = SEED_MAP[group]
            if not kind.startswith(domain + '.'):
                raise ValueError('Seed owner mismatch')
            rows[kind] = records
    manifest = rows['engineering.document']
    if {d['id'] for d in manifest} != set(DOCUMENT_PATHS):
        raise ValueError('Document manifest must match the explicit allowlist')
    for document in manifest:
        expected = DOCUMENT_PATHS[document['id']]
        if document.pop('relative_path') != expected:
            raise ValueError('Document path is not allowlisted')
        path = PROJECT / expected
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(PROJECT):
            raise ValueError('Document symlinks and traversal are refused')
        document['content'] = path.read_text()
        document['content_hash'] = hashlib.sha256(document['content'].encode()).hexdigest()
    for program in rows['planner.program']:
        program['program_id'] = program['id']
    indexes = {kind: {r['id']: r for r in records} for kind, records in rows.items()}
    for result in rows['validation.result']:
        for name, source_kind, key, version in (
            ('configuration_snapshot', 'engineering.configuration', 'configuration_id', 'configuration_content_version'),
            ('workload_snapshot', 'engineering.workload', 'workload_profile_id', 'workload_profile_content_version'),
            ('criteria_snapshot', 'engineering.criteria', 'acceptance_limits_ref', 'acceptance_criteria_content_version'),
        ):
            source_record = indexes[source_kind][result[key]]
            if source_record['content_version'] != result[version]:
                raise ValueError('Seed historical version has no matching source')
            result[name] = copy.deepcopy(source_record)
    for kind, records in rows.items():
        if len({r['id'] for r in records}) != len(records):
            raise ValueError('Duplicate seed record')
        rows[kind] = [MODELS[kind].model_validate(r).model_dump(mode='json') for r in records]
    indexes = {kind: {r['id']: r for r in records} for kind, records in rows.items()}
    for kind, records in rows.items():
        for record in records:
            if record['owning_system'] != kind.split('.')[0] or at(record['updated_at']) > now:
                raise ValueError('Invalid owner or future source timestamp')
            for key, value in record.items():
                refs = [(REFS[key], value)] if key in REFS and value else []
                if key in LIST_REFS:
                    if len(value) != len(set(value)):
                        raise ValueError('Duplicate applicability reference')
                    refs += [(LIST_REFS[key], item) for item in value]
                for target, ref in refs:
                    other = indexes.get(target, {}).get(ref)
                    if other is None:
                        raise ValueError('Unresolved seed reference')
                    for scope in ('program_id', 'customer_id'):
                        if scope in record and scope in other and record[scope] != other[scope]:
                            raise ValueError('Cross-scope seed reference')
            if kind == 'engineering.workload':
                if len(set(record['context_bins'])) != len(record['context_bins']):
                    raise ValueError('Duplicate context bin')
            if kind == 'engineering.procedure':
                workload = indexes['engineering.workload'][record['workload_profile_id']]
                if record['suite_minutes'] != workload['total_suite_minutes'] or record['suite_minutes'] != len(workload['context_bins']) * record['per_bin_minutes']:
                    raise ValueError('Inconsistent procedure duration')
            if kind == 'validation.result':
                if sum(record['observed_minutes_by_context_bin'].values()) != record['actual_suite_minutes'] or set(map(int, record['observed_minutes_by_context_bin'])) != set(record['covered_context_bins']):
                    raise ValueError('Inconsistent result duration')
                if at(record['completed_at']) > at(record['updated_at']):
                    raise ValueError('Result completion after refresh')
            if kind in ('validation.slot', 'erp.rate'):
                start, end = ('starts_at', 'ends_at') if kind == 'validation.slot' else ('effective_from', 'effective_to')
                if at(record[start]) >= at(record[end]):
                    raise ValueError('Invalid time interval')
            if kind == 'planner.milestone':
                for dep in record['dependencies']:
                    if dep['kind'] != 'requirement_evidence' or dep['requirement_revision_id'] not in indexes['engineering.requirement']:
                        raise ValueError('Invalid seed dependency')
            if kind == 'manufacturing.unit':
                lot = indexes['manufacturing.lot'][record['source_lot_id']]
                if any(record[f] != lot[f] for f in ('product_id', 'product_revision')):
                    raise ValueError('Unit/lot lineage mismatch')
            if kind == 'validation.sample':
                unit = indexes['manufacturing.unit'][record['unit_id']]
                config = indexes['engineering.configuration'][record['configuration_id']]
                if any(unit[f] != config[f] for f in ('product_id', 'product_revision')):
                    raise ValueError('Sample configuration lineage mismatch')
    for kind in ('engineering.plan', 'engineering.decision', 'validation.job', 'validation.reservation', 'planner.link', 'planner.task'):
        if rows[kind]:
            raise ValueError('Generated entities must be empty in the seed')
    if seed['audit_events']:
        raise ValueError('Seed audit must be empty')
    meta = seed['meta']
    if source is None:
        from .portfolio import expand
        rows, meta = expand(rows, meta)
        from .quality_knowledge import documents
        rows['engineering.document'].extend(documents())
    validate_graph(rows)
    return rows, meta


def validate_graph(rows):
    """Validate both authored golden fixtures and the complete generated graph."""
    for kind, records in rows.items():
        if len({r['id'] for r in records}) != len(records):
            raise ValueError('Duplicate portfolio record')
        rows[kind] = [MODELS[kind].model_validate(r).model_dump(mode='json') for r in records]
    indexes = {k: {r['id']: r for r in records} for k, records in rows.items()}
    def reference(record, kind, rid):
        target = indexes.get(kind, {}).get(rid)
        if target is None:
            raise ValueError('Unresolved portfolio reference')
        for scope in ('program_id', 'customer_id'):
            if scope in record and scope in target and record[scope] != target[scope]:
                raise ValueError('Cross-scope portfolio reference')
        return target
    for kind, records in rows.items():
        for r in records:
            for field, target in REFS.items():
                if r.get(field): reference(r, target, r[field])
            for field, target in LIST_REFS.items():
                for rid in r.get(field, []): reference(r, target, rid)
            if 'program_id' in r and 'customer_id' in r:
                if indexes['planner.program'][r['program_id']]['customer_id'] != r['customer_id']:
                    raise ValueError('Program/customer mismatch')
            if kind == 'planner.milestone':
                for d in r['dependencies']:
                    reference(r, 'engineering.requirement' if d['kind']=='requirement_evidence' else 'validation.job', d['requirement_revision_id'] if d['kind']=='requirement_evidence' else d['job_id'])
                    if d['kind'] == 'requirement_evidence' and d['state'] == 'completed' and indexes['engineering.requirement'][d['requirement_revision_id']]['status'] != 'approved':
                        raise ValueError('Requested evidence cannot be seeded as accepted/completed')
            if kind == 'manufacturing.unit':
                lot = indexes['manufacturing.lot'][r['source_lot_id']]
                if any(r[f] != lot[f] for f in ('product_id','product_revision')):
                    raise ValueError('Portfolio unit/lot lineage mismatch')
            if kind == 'validation.sample':
                config = indexes['engineering.configuration'][r['configuration_id']]
                unit = indexes['manufacturing.unit'][r['unit_id']]
                if any(config[f] != unit[f] for f in ('product_id','product_revision')):
                    raise ValueError('Portfolio sample lineage mismatch')
            if kind == 'engineering.procedure':
                workload = indexes['engineering.workload'][r['workload_profile_id']]
                if r['suite_minutes'] != workload['total_suite_minutes'] or r['suite_minutes'] != len(workload['context_bins']) * r['per_bin_minutes']:
                    raise ValueError('Portfolio procedure duration mismatch')
            if kind == 'validation.result':
                if sum(r['observed_minutes_by_context_bin'].values()) != r['actual_suite_minutes'] or set(map(int,r['observed_minutes_by_context_bin'])) != set(r['covered_context_bins']):
                    raise ValueError('Portfolio observation mismatch')
                for field, target, key, version in [('configuration_snapshot','engineering.configuration','configuration_id','configuration_content_version'),('workload_snapshot','engineering.workload','workload_profile_id','workload_profile_content_version'),('criteria_snapshot','engineering.criteria','acceptance_limits_ref','acceptance_criteria_content_version')]:
                    source = reference(r,target,r[key])
                    if r[field] != source or r[version] != source['content_version']:
                        raise ValueError('Portfolio historical snapshot mismatch')
            if kind == 'validation.history':
                if at(r['started_at']) >= at(r['completed_at']) or at(r['completed_at']) > at(r['updated_at']):
                    raise ValueError('Invalid historical execution times')
                for rid in r['result_ids']:
                    result = reference(r,'validation.result',rid)
                    if any(result[f] != r[f] for f in ('configuration_id','sample_id','completed_at')):
                        raise ValueError('Historical job observation mismatch')


@contextmanager
def lifecycle_lock(settings):
    path = settings.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + '.lock')
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_nlink != 1:
            raise ValueError('Unsafe lifecycle lock')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Stop the service before initialization or reset') from exc
        yield
    finally:
        os.close(fd)


def check_marker(con):
    try:
        row = con.execute('SELECT data FROM demo_metadata WHERE id=1').fetchone()
        meta = json.loads(row['data'])
    except Exception as exc:
        raise ValueError('Not an owned demo database') from exc
    if meta.get('ownership_marker') != MARKER or meta.get('database_schema_version') != 1 or meta.get('scenario_id') != 'SCN-LC-001':
        raise ValueError('Not a compatible owned demo database')
    return meta


def initialize(settings, *, reset=False, confirmed=False, source=None):
    path = settings.validate(existing=reset)
    if reset and not confirmed:
        raise ValueError('Reset requires explicit confirmation')
    rows, meta = load_seed(source)
    with lifecycle_lock(settings):
        created = False
        if not reset:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            os.close(fd)
            created = True
        con = connect(path)
        try:
            old = check_marker(con) if reset else {}
            con.execute('BEGIN EXCLUSIVE')
            con.execute('PRAGMA defer_foreign_keys=ON')
            if reset:
                known_tables = {table(k) for k in MODELS} | {'demo_metadata', 'idempotency_receipts', 'audit_events'}
                objects = con.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
                expected_names = set()
                for statement in schema_statements():
                    words = statement.split()
                    expected_names.add(words[3] if words[1] == 'UNIQUE' else words[2])
                if {r['name'] for r in objects} != expected_names:
                    raise ValueError('Unexpected database schema; reset refused')
                for row in objects:
                    if row['type'] == 'trigger':
                        con.execute('DROP TRIGGER "' + row['name'] + '"')
                for name in known_tables:
                    con.execute('DROP TABLE "' + name + '"')
            for statement in schema_statements():
                con.execute(statement)
            meta.update(ownership_marker=MARKER, database_schema_version=1,
                        seed_digest=digest(rows), reset_generation=old.get('reset_generation', -1) + 1)
            con.execute('INSERT INTO demo_metadata VALUES (1,?)', (canonical(meta),))
            store = Store(con)
            for kind, records in rows.items():
                for record in records:
                    store.insert(kind, record)
            if meta.get('generator_version'):
                from .portfolio import seed_history
                seed_history(store)
            if con.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Seed foreign key validation failed')
            con.commit()
        except Exception:
            con.rollback()
            if created:
                con.close()
                path.unlink()
            raise
        finally:
            con.close()
