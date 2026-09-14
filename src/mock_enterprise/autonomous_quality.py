"""One synthetic source publication, called only by explicit demo maintenance.

The source owns the records and its immutable event in existing demo metadata.
There is no public business write, startup publisher, agent tool or new store.
"""
import json
from .config import PROJECT
from .db import Store, connect
from .seed import check_marker
from .core import canonical
from .demo_management import maintenance_lock
from enterprise_api.quality_events import QualitySourceEvent

CASE = 'QE-011'
EVENT_KEY = 'autonomous_quality_event'


def records():
    return json.loads((PROJECT / 'fixtures/autonomous_quality_exception.json').read_text())


def owned_keys():
    return {(kind, row['id']) for kind, values in records().items() for row in values}


def publish(settings, event_id, timestamp, expected_epoch):
    """Atomic source records + one versioned event; retries return the same event.

    Caller serializes prepare/reset with the host maintenance lease. Source locks
    also protect against independent local maintenance. Conflicts fail closed.
    """
    from .domains.quality import context
    from .core import IDENTITIES
    with maintenance_lock(settings, exclusive=True):
        con = connect(settings.validate(existing=True))
        try:
            con.execute('BEGIN IMMEDIATE')
            con.execute('PRAGMA defer_foreign_keys=ON')
            meta = check_marker(con)
            if meta.get('demo_reset_pending'):
                raise ValueError('DEMO_RESET_RECONCILIATION_REQUIRED')
            if meta.get('demo_epoch', 'initial') != expected_epoch:
                raise ValueError('DEMO_STATE_CHANGED')
            previous = meta.get(EVENT_KEY)
            if previous:
                event = QualitySourceEvent.model_validate(previous)
                if event.event_id != event_id:
                    raise ValueError('AUTONOMOUS_SOURCE_ALREADY_PUBLISHED')
                return event
            store = Store(con)
            for kind, values in records().items():
                for row in values:
                    if con.execute('SELECT 1 FROM '+kind.replace('.', '_')+' WHERE id=?', (row['id'],)).fetchone():
                        raise ValueError('AUTONOMOUS_SOURCE_COLLISION')
                    store.insert(kind, row)
            # Same domain projection as the public HTTP read, with source scope.
            actor = IDENTITIES['demo-automation-local-only']
            current = context(store, actor, CASE)
            event = QualitySourceEvent(event_id=event_id, event_timestamp=timestamp,
                source_record_updated_at=current.exception.updated_at, context_digest=current.context_digest)
            meta[EVENT_KEY] = event.model_dump(mode='json')
            con.execute('UPDATE demo_metadata SET data=? WHERE id=1', (canonical(meta),))
            if con.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('AUTONOMOUS_REFERENCE_CONFLICT')
            con.commit()
            return event
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
