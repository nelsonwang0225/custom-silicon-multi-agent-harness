"""HTTP transaction, receipt and sanitized audit infrastructure."""
import json
import logging
import sqlite3
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from .core import BusinessError, canonical, digest, fail, iso, new_id, role
from .db import Store, connect, read_store, restrict_writes

LOG = logging.getLogger('mock_enterprise')


def audit(store, request, domain, outcome, *, record=None, changes=None):
    record = record or {}
    actor = getattr(request.state, 'actor', None)
    key = request.headers.get('idempotency-key')
    action = getattr(request.state, 'action', request.method)
    plan_id = record.get('id') if action == 'create_plan' and 'created_by' in record else record.get('plan_id')
    approval_id = record.get('id') if action == 'record_decision' and record.get('decision') == 'approve' else record.get('approval_id')
    job_id = record.get('id') if action == 'schedule_job' and 'reservation_id' in record else record.get('job_id')
    data = dict(id=new_id('evt'), synthetic=True, scenario_at=store.now,
                wall_clock_at=iso(datetime.now(timezone.utc)), domain=domain,
                actor_id=actor.id if actor else None, actor_role=actor.role if actor else None,
                program_id=record.get('program_id'), customer_id=record.get('customer_id'),
                change_id=record.get('change_id') or record.get('exception_id'), action=action,
                outcome=outcome, resource_id=record.get('id'), plan_id=plan_id,
                approval_id=approval_id, job_id=job_id,
                request_id=request.state.request_id, correlation_id=request.state.correlation_id,
                idempotency_hash=digest(key) if key else None, changes=changes or {})
    store.con.execute('INSERT INTO audit_events(id,program_id,change_id,data) VALUES(?,?,?,?)',
                      (data['id'], data['program_id'], data['change_id'], canonical(data)))


def audit_scope(store, request):
    actor = getattr(request.state, 'actor', None)
    if not actor:
        return {}
    # Only identifiers from validated/authorized lookups are used as attribution.
    record = getattr(request.state, 'audit_record', None)
    if record:
        return record
    plan_id = request.path_params.get('plan_id') or getattr(request.state, 'claimed_plan_id', None)
    if plan_id:
        try:
            kind = {'quality_decision': 'manufacturing.recovery_plan', 'delivery_decision': 'erp.commitment_plan'}.get(getattr(request.state, 'domain', ''), 'engineering.plan')
            plan = store.get(kind, plan_id, actor)
            return {**plan, 'plan_id': plan_id}
        except BusinessError:
            pass
    change_id = request.path_params.get('change_id') or request.query_params.get('change_id')
    if change_id:
        try:
            change = store.get('engineering.change', change_id, actor)
            return {**change, 'change_id': change['id']}
        except BusinessError:
            pass
    return dict(program_id=actor.program_id, customer_id=actor.customer_id)


def record_denial(request, code, failed=False):
    con = None
    try:
        con = connect(request.app.state.settings.db_path)
        con.execute('BEGIN IMMEDIATE')
        restrict_writes(con, 'audit')
        store = Store(con)
        audit(store, request, getattr(request.state, 'domain', 'platform'),
              'failed' if failed else 'denied', record=audit_scope(store, request), changes={'code': code})
        con.commit()
    except Exception:
        if con:
            con.rollback()
        LOG.error('Audit unavailable; request failed; request_id=%s code=%s', request.state.request_id, code)
    finally:
        if con:
            con.close()


def mutate(request: Request, model, domain, required_role, action, result_kind, handler):
    request.state.domain, request.state.action = domain, action
    request.state.claimed_plan_id = getattr(model, 'plan_id', None)
    actor = role(request, required_role)
    if domain.startswith(('quality_', 'delivery_')):
        fail(not actor.portfolio, 403, 'FORBIDDEN_ROLE', 'Scoped quality identity required.')
    key = request.headers.get('idempotency-key')
    fail(key is not None and 1 <= len(key) <= 100 and all(32 < ord(c) < 127 for c in key),
         422, 'INVALID_REQUEST', 'A bounded printable Idempotency-Key is required.')
    payload = model.model_dump(mode='json')
    fingerprint = digest(payload)
    scope = (actor.id, request.method, request.url.path, digest(key))
    con = connect(request.app.state.settings.db_path)
    try:
        con.execute('BEGIN IMMEDIATE')
        restrict_writes(con, domain)
        store = Store(con)
        if actor.portfolio:
            change_id = request.path_params.get('change_id')
            plan_id = request.path_params.get('plan_id') or payload.get('plan_id')
            target = store.get('engineering.change', change_id, actor) if change_id else store.get('engineering.plan', plan_id, actor)
            actor = actor.scoped(target['program_id'], target['customer_id'])
            request.state.actor = actor
        store.get('planner.program', actor.program_id, actor)
        receipt = con.execute('SELECT * FROM idempotency_receipts WHERE actor_id=? AND method=? AND route=? AND key_hash=?', scope).fetchone()
        if receipt:
            original = json.loads(receipt['body'])
            store.get(result_kind, original['id'], actor)
            fail(receipt['fingerprint'] == fingerprint, 409, 'IDEMPOTENCY_KEY_REUSED', 'Idempotency key was used with different content.')
            audit(store, request, domain, 'replay', record=original)
            con.commit()
            return JSONResponse(original, status_code=receipt['status'], headers={'Idempotency-Replayed': 'true'})
        record, changes = handler(store, actor, payload)
        # Validate the actual response before commit; failed serialization cannot claim success.
        response_type = request.scope['route'].response_model
        record = response_type.model_validate(record).model_dump(mode='json')
        audit(store, request, domain, 'succeeded', record=record, changes=changes)
        body = canonical(record)
        con.execute('INSERT INTO idempotency_receipts VALUES(?,?,?,?,?,?,?)', (*scope, fingerprint, 201, body))
        con.commit()
        return JSONResponse(record, status_code=201)
    except sqlite3.IntegrityError as exc:
        con.rollback()
        raise BusinessError(409, 'RESOURCE_CONFLICT', 'Write conflicts with persisted constraints.') from exc
    except sqlite3.OperationalError as exc:
        con.rollback()
        if 'locked' in str(exc).lower():
            raise BusinessError(503, 'DATABASE_BUSY', 'Database busy; retry the same request.') from exc
        raise
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def attributed(request, record):
    request.state.audit_record = record


def duplicate(records, *, decision=None):
    if records:
        code = 'DECISION_CONFLICT' if decision and records[0]['decision'] != decision else 'ACTION_ALREADY_RECORDED'
        raise BusinessError(409, code, 'Action already recorded; retrieve the existing resource.', existing_resource_id=records[0]['id'])
