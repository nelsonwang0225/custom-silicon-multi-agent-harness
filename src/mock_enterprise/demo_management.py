"""Explicit local demo restoration. Never a business router or agent tool.

The existing five systems share one SQLite file. Restoration is a local atomic
maintenance transaction, followed separately by host reconciliation and HTTP
readback. Normal business transactions and their authority are unchanged.
"""
from contextlib import contextmanager
from functools import lru_cache
import fcntl
import hashlib
import json
import os

from .config import PROJECT
from .core import canonical, digest
from .db import MODELS, Store, connect, table
from .seed import check_marker, load_seed

VERSION = 'phase09-v1'
SCENARIO_NOW = '2026-11-16T09:00:00Z'
SCENARIOS = ('CR-017', 'CR-019', 'QE-004', 'DR-009')
SYSTEMS = ('engineering', 'validation', 'manufacturing', 'erp', 'planner')


def storage_id(settings):
    return hashlib.sha256(str(settings.validate(existing=True)).encode()).hexdigest()


@contextmanager
def maintenance_lock(settings, *, exclusive=False):
    path = settings.validate(existing=True).with_suffix('.maintenance.lock')
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_nlink != 1:
            raise ValueError('UNSAFE_DEMO_LOCK')
        try:
            fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('DEMO_MAINTENANCE_BUSY') from None
        yield
    finally:
        os.close(fd)


def scope_cases(scope):
    if scope == 'full':
        return {*SCENARIOS, 'QE-011'}
    if scope not in (*SCENARIOS, 'QE-011'):
        raise ValueError('INVALID_DEMO_SCOPE')
    return {scope}


@lru_cache(maxsize=1)
def baseline():
    """Compose the authored seed and SAME extension loaders used by installers.

    The four scenario namespaces are restored. Full reset also restores the
    explicitly selected Northstar summary and gates used on the Overview; other
    generated programs and cases remain outside reset scope.
    """
    from .standard_upgrade import extension as standard
    from .quality_upgrade import extension as quality
    from .delivery_upgrade import extension as delivery
    base, _ = load_seed(json.loads((PROJECT / 'fixtures/seed.json').read_text()))
    groups = {'CR-017': base, 'CR-019': standard(), 'QE-004': quality(), 'DR-009': delivery()}
    rows, owners = {}, {}
    for case, kinds in groups.items():
        for kind, records in kinds.items():
            for record in records:
                record = MODELS[kind].model_validate(record).model_dump(mode='json')
                key = (kind, record['id'])
                if key in rows and rows[key] != record:
                    raise ValueError('CONTRADICTORY_DEMO_FIXTURES')
                rows[key] = record
                owners.setdefault(key, set()).add(case)
    # Northstar is the stable healthy comparison program in the opening view.
    # Keep its source-owned summary and gates coherent after older demo data is
    # reused; this is selected only by a full reset below.
    portfolio, _ = load_seed()
    for kind in ('planner.program', 'planner.milestone'):
        for record in portfolio[kind]:
            if record.get('program_id') != 'PRG-P01':
                continue
            record = MODELS[kind].model_validate(record).model_dump(mode='json')
            key = (kind, record['id'])
            rows[key] = record
            owners.setdefault(key, set()).add('overview_baseline')
    # Explicit shared business inputs, not recursively following program records
    # into unrelated portfolio cases. Mutable lab availability is owned by CR-017.
    shared = {
        'CR-019': [('engineering.configuration','CFG-B-01'), ('engineering.requirement','REQ-042-V1'),
            ('engineering.workload','WF-LC-V1'), ('engineering.criteria','CRIT-BASE-V1'),
            ('validation.result','RES-BASELINE-B')],
        'QE-004': [('engineering.configuration','CFG-B-01'), ('validation.result','RES-BASELINE-B')],
        'DR-009': [('engineering.configuration','CFG-B-01'), ('engineering.requirement','REQ-042-V1'),
            ('validation.result','RES-BASELINE-B'), ('manufacturing.lot','LOT-B-203'),
            ('manufacturing.lot','LOT-B-204'), ('manufacturing.quality_material','MAT-B-203'),
            ('manufacturing.quality_material','MAT-B-204'), ('erp.order','ORD-HEL-800'),
            ('planner.milestone','MS-HEL-800')],
    }
    for case, keys in shared.items():
        for key in keys:
            if key not in rows:
                raise ValueError('MISSING_DEMO_BASELINE_REFERENCE')
            owners[key].add(case)
    return rows, owners


GENERATED = {
    'engineering.plan', 'engineering.plan_state', 'engineering.decision',
    'validation.job', 'validation.reservation', 'validation.completion',
    'engineering.evidence_review', 'planner.link', 'planner.task',
    'validation.intake', 'manufacturing.quality_investigation',
    'manufacturing.recovery_plan', 'manufacturing.recovery_decision', 'planner.recovery_task',
    'erp.commitment_plan', 'erp.commitment_decision', 'erp.delivery_commitment', 'planner.delivery_link',
}


def current_rows(con):
    store = Store(con)
    return {(kind, r['id']): r for kind in MODELS for r in store.list(kind)}


def selected_rows(rows, cases):
    expected, owners = baseline()
    selected = {key for key, scopes in owners.items() if scopes & cases}
    if set(SCENARIOS).issubset(cases):
        selected.update(key for key, scopes in owners.items() if 'overview_baseline' in scopes)
    if 'QE-011' in cases:
        from .autonomous_quality import owned_keys
        selected.update(owned_keys() & rows.keys())
    # Traverse only typed generated records and their known provenance fields.
    # Do not treat arbitrary matching text as ownership.
    changed = True
    while changed:
        before = len(selected)
        ids = {key[1] for key in selected if key[0] in GENERATED}
        for key, r in rows.items():
            if r.get('program_id') != 'PRG-A17' or r.get('customer_id', 'CUST-FML01') != 'CUST-FML01':
                continue
            if key[0] in GENERATED and (any(r.get(f) in cases for f in ('change_id','exception_id','delivery_id'))
                    or any(r.get(f) in ids for f in ('plan_id','job_id','link_id'))
                    or (key[0] == 'engineering.plan_state' and key[1] in ids)):
                selected.add(key)
            if key[0] == 'validation.completion' and key in selected:
                selected.add(('validation.result', r['result_id']))
        changed = before != len(selected)
    if 'DR-009' in cases:
        request = rows.get(('erp.delivery_request','DR-009'), {})
        selected.update(('manufacturing.future_supply', rid) for rid in request.get('future_supply_ids', []))
    return selected


def dependency_conflicts(rows, scope):
    cases = scope_cases(scope)
    if scope == 'full':
        return []
    expected, owners = baseline()
    selected = selected_rows(rows, cases)
    conflicts = []
    for key in selected & expected.keys():
        other = owners[key] - cases
        if other and rows.get(key) != expected[key]:
            conflicts.append(f'{key[0]}:{key[1]} is shared with {", ".join(sorted(other))}; use Full Demo Reset.')
    if scope == 'CR-017':
        dr = rows.get(('erp.delivery_request','DR-009'), {})
        if dr.get('technical_change_id') == 'CR-017':
            conflicts.append('DR-009 currently depends on CR-017 technical readiness; use Full Demo Reset.')
        # Existing intake packages bind the nominated sample's source version.
        resources = [('validation.sample','SAMPLE-B-017'), ('planner.milestone','MS-ACCEPT-01')]
        if any(rows.get(k) != expected[k] for k in resources) and any(k[0]=='validation.intake' and r.get('change_id')=='CR-019' for k,r in rows.items()):
            conflicts.append('CR-019 has a recorded handoff against shared CR-017 resources; use Full Demo Reset.')
    return conflicts


def inspect_source(settings, scope='full'):
    con = connect(settings.validate(existing=True))
    try:
        con.execute('BEGIN')
        meta = check_marker(con)
        rows = current_rows(con)
        selected = selected_rows(rows, scope_cases(scope))
        expected, _ = baseline()
        discrepancies = [f'{kind}:{rid} differs from the canonical baseline' for kind,rid in sorted(selected)
                         if rows.get((kind,rid)) != expected.get((kind,rid))]
        if 'QE-011' in scope_cases(scope) and meta.get('autonomous_quality_event'):
            discrepancies.append('QE-011 source event remains; reset the autonomous opening.')
        if con.execute('PRAGMA foreign_key_check').fetchall():
            discrepancies.append('Source references do not resolve')
        if meta.get('scenario_now') != SCENARIO_NOW:
            discrepancies.append('Shared source scenario clock differs from canonical UTC baseline')
        material = [rows.get(('manufacturing.quality_material', rid), {}) for rid in ('MAT-B-203','MAT-B-204','MAT-B-202')]
        quantities = {field: sum(m.get(field,0) for m in material) for field in
                      ('physical_quantity','held_quantity','allocated_quantity','eligible_unallocated_quantity')}
        quantities['requested_quantity'] = rows.get(('erp.delivery_request','DR-009'), {}).get('quantity')
        requested = quantities['requested_quantity']
        quantities['gap_quantity'] = max(0, requested - quantities['eligible_unallocated_quantity']) if requested is not None else None
        if 'DR-009' in scope_cases(scope) and list(quantities.values()) != [1000,250,150,600,800,200]:
            discrepancies.append('DR-009 quantities must be physical 1000 / held 250 / allocated 150 / eligible 600 / requested 800 / gap 200')
        return {'discrepancies': discrepancies, 'quantities': quantities,
                'reset_pending': bool(meta.get('demo_reset_pending',False)),
                'source_digest': digest([rows.get(k) for k in sorted(selected)]),
                'conflicts': dependency_conflicts(rows, scope)}
    finally:
        con.rollback()
        con.close()


def restore_source(settings, scope, *, archive, epoch):
    """Caller holds exclusive maintenance lock and supplies a durable archive sink.

    Restore existing triggers exactly, including on rollback. Unknown schemas are
    refused. No generic table/path/fixture selectors cross a public boundary.
    """
    cases = scope_cases(scope)
    con = connect(settings.validate(existing=True))
    try:
        con.execute('BEGIN EXCLUSIVE')
        con.execute('PRAGMA defer_foreign_keys=ON')
        meta = check_marker(con)
        from .db import schema_statements
        expected_names = set()
        for statement in schema_statements():
            words = statement.split()
            expected_names.add(words[3] if words[1]=='UNIQUE' else words[2])
        objects = con.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
        if {r['name'] for r in objects} != expected_names:
            raise ValueError('UNEXPECTED_DEMO_SOURCE_SCHEMA')
        rows = current_rows(con)
        conflicts = dependency_conflicts(rows, scope)
        if conflicts:
            raise ValueError('SHARED_DEPENDENCY_REQUIRES_FULL_RESET')
        selected = selected_rows(rows, cases)
        expected, _ = baseline()
        receipts = [dict(r) for r in con.execute('SELECT * FROM idempotency_receipts')
                    if _receipt_owned(json.loads(r['body']), selected, cases)]
        selected_ids = {rid for kind,rid in selected}
        audits = [dict(r) for r in con.execute('SELECT * FROM audit_events')
                  if r['program_id']=='PRG-A17' and (r['change_id'] in cases or
                    json.loads(r['data']).get('resource_id') in selected_ids)]
        # Archive is durable BEFORE deleting any current source record.
        archive({'category':'archived_demo_source_state','scope':scope,'baseline_version':VERSION,
                 'records':[{'kind':k[0],'record':rows[k]} for k in sorted(selected) if k in rows],
                 'receipts':receipts,'audit_events':audits,
                 'autonomous_event':meta.get('autonomous_quality_event') if 'QE-011' in cases else None})
        triggers = [r for r in objects if r['type']=='trigger']
        for r in triggers:
            con.execute('DROP TRIGGER "'+r['name']+'"')
        for kind,rid in sorted(selected):
            con.execute(f'DELETE FROM {table(kind)} WHERE id=?', (rid,))
        store = Store(con)
        for key in sorted(selected & expected.keys()):
            store.insert(key[0], expected[key])
        for r in receipts:
            con.execute('DELETE FROM idempotency_receipts WHERE actor_id=? AND method=? AND route=? AND key_hash=?',
                        (r['actor_id'],r['method'],r['route'],r['key_hash']))
        for r in audits:
            con.execute('DELETE FROM audit_events WHERE id=?', (r['id'],))
        for r in triggers:
            con.execute(r['sql'])
        if con.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('RESET_REFERENCE_CONFLICT')
        meta.update(demo_baseline_version=VERSION, demo_epoch=epoch, demo_reset_pending=True)
        if 'QE-011' in cases: meta.pop('autonomous_quality_event', None)
        if scope == 'full': meta['scenario_now'] = SCENARIO_NOW
        if 'CR-019' in cases: meta.update(phase08_4a_standard=1, phase08_4a_request_provenance=1)
        if 'QE-004' in cases: meta['phase08_4b_quality']=1
        if 'DR-009' in cases: meta['phase08_4c_delivery']=1
        con.execute('UPDATE demo_metadata SET data=? WHERE id=1', (canonical(meta),))
        con.commit()
        return sorted({k[0].split('.')[0] for k in selected})
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _receipt_owned(body, selected, cases):
    ids = {rid for kind,rid in selected}
    return body.get('program_id')=='PRG-A17' and (body.get('id') in ids or
        any(body.get(f) in cases for f in ('change_id','exception_id','delivery_id')))


def finish_source_reset(settings, epoch):
    """Clear only the maintenance barrier after independent host verification."""
    con = connect(settings.validate(existing=True))
    try:
        con.execute('BEGIN IMMEDIATE')
        meta = check_marker(con)
        if meta.get('demo_epoch') != epoch:
            raise ValueError('DEMO_STATE_CHANGED')
        meta['demo_reset_pending'] = False
        con.execute('UPDATE demo_metadata SET data=? WHERE id=1',(canonical(meta),))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
