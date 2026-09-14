"""Typed relational storage. Registry drives persistence, never generic HTTP CRUD."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import schemas as m
from .downstream_models import LabCompletion, EvidenceReview
from enterprise_api.standard_models import StandardRequest, StandardRule, ValidationIntake, ValidationIntakeQueue
from enterprise_api.quality_models import QualityException, QualityMaterial, QualityObservation, QualityBaseline, QualityProcedure, QualityInvestigation, RecoveryPlan, RecoveryDecision, RecoveryTask
from .core import BusinessError, canonical, fail

SOURCE_MODELS = {
    'engineering.supplier': m.Supplier, 'engineering.customer': m.Customer,
    'engineering.configuration': m.Configuration, 'engineering.workload': m.Workload,
    'engineering.requirement': m.Requirement, 'engineering.change': m.Change,
    'engineering.procedure': m.Procedure, 'engineering.criteria': m.Criteria,
    'engineering.policy': m.Policy, 'engineering.document': m.Document,
    'validation.result': m.Result, 'validation.lab': m.Lab,
    'validation.slot': m.Slot, 'validation.sample': m.Sample,
    'manufacturing.lot': m.Lot, 'manufacturing.unit': m.Unit,
    'erp.order': m.Order, 'erp.rate': m.Rate,
    'planner.program': m.Program, 'planner.milestone': m.Milestone,
}
MODELS = {**SOURCE_MODELS, 'engineering.plan': m.Plan, 'engineering.plan_state': m.PlanState,
          'engineering.decision': m.Decision, 'validation.job': m.Job,
          'validation.reservation': m.Reservation, 'planner.link': m.Link, 'planner.task': m.Task,
          'validation.history': m.HistoricalJob, 'validation.completion': LabCompletion,
          'engineering.evidence_review': EvidenceReview, 'engineering.standard_request': StandardRequest,
          'engineering.standard_rule': StandardRule, 'validation.intake': ValidationIntake, 'validation.intake_queue': ValidationIntakeQueue}
MODELS.update({
    'manufacturing.quality_exception': QualityException, 'manufacturing.quality_material': QualityMaterial,
    'manufacturing.quality_observation': QualityObservation, 'manufacturing.quality_baseline': QualityBaseline,
    'engineering.quality_procedure': QualityProcedure, 'manufacturing.quality_investigation': QualityInvestigation,
    'manufacturing.recovery_plan': RecoveryPlan, 'manufacturing.recovery_decision': RecoveryDecision,
    'planner.recovery_task': RecoveryTask,
})
from enterprise_api.delivery_models import (DeliveryRequest, DeliveryState, DeliveryAllocation, DeliveryClearance,
    DeliveryLogistics, FutureSupply, CommitmentPlan, CommitmentDecision, DeliveryCommitment, DeliveryLink)
DELIVERY_MODELS = {
    'erp.delivery_request': DeliveryRequest, 'erp.delivery_state': DeliveryState, 'erp.delivery_allocation': DeliveryAllocation,
    'engineering.delivery_clearance': DeliveryClearance, 'planner.delivery_logistics': DeliveryLogistics,
    'manufacturing.future_supply': FutureSupply, 'erp.commitment_plan': CommitmentPlan,
    'erp.commitment_decision': CommitmentDecision, 'erp.delivery_commitment': DeliveryCommitment, 'planner.delivery_link': DeliveryLink,
}
MODELS.update(DELIVERY_MODELS)
WRITES = {
    'delivery_plan': {'erp.commitment_plan'},
    'delivery_decision': {'erp.commitment_decision'},
    'delivery_commitment': {'erp.delivery_commitment', 'erp.delivery_state'},
    'delivery_link': {'planner.delivery_link'},
    'quality_investigation': {'manufacturing.quality_investigation'},
    'quality_plan': {'manufacturing.recovery_plan'},
    'quality_decision': {'manufacturing.recovery_decision'},
    'quality_task': {'planner.recovery_task'},
    'engineering': {'engineering.plan', 'engineering.plan_state', 'engineering.decision', 'engineering.change'},
    'validation': {'validation.job', 'validation.reservation', 'validation.slot', 'validation.sample'},
    'planner': {'planner.link', 'planner.task', 'planner.milestone'},
    'audit': set(),
    'lab_completion': {'validation.result', 'validation.completion'},
    'evidence_review': {'engineering.evidence_review'},
    'standard_intake': {'validation.intake'},
}
REFS = {
    'delivery_id': 'erp.delivery_request', 'clearance_id': 'engineering.delivery_clearance',
    'logistics_id': 'planner.delivery_logistics', 'material_id': 'manufacturing.quality_material',
    'commitment_id': 'erp.delivery_commitment', 'current_commitment_id': 'erp.delivery_commitment',
    'prior_commitment_id': 'erp.delivery_commitment', 'supersedes_commitment_id': 'erp.delivery_commitment',
    'technical_change_id': 'engineering.change',
    'exception_id': 'manufacturing.quality_exception', 'lot_id': 'manufacturing.lot',
    'observation_id': 'manufacturing.quality_observation', 'baseline_id': 'manufacturing.quality_baseline',
    'investigation_procedure_id': 'engineering.quality_procedure', 'investigation_id': 'manufacturing.quality_investigation',
    'expected_milestone_id': 'planner.milestone', 'allocation_order_id': 'erp.order',
    'program_id': 'planner.program', 'customer_id': 'engineering.customer',
    'supplier_id': 'engineering.supplier', 'configuration_id': 'engineering.configuration',
    'workload_profile_id': 'engineering.workload', 'acceptance_limits_ref': 'engineering.criteria',
    'baseline_requirement_revision_id': 'engineering.requirement',
    'proposed_requirement_revision_id': 'engineering.requirement',
    'target_requirement_revision_id': 'engineering.requirement',
    'milestone_id': 'planner.milestone', 'order_id': 'erp.order',
    'request_document_id': 'engineering.document', 'document_id': 'engineering.document',
    'procedure_id': 'engineering.procedure', 'policy_id': 'engineering.policy',
    'sample_id': 'validation.sample', 'slot_id': 'validation.slot', 'lab_id': 'validation.lab',
    'rate_id': 'erp.rate', 'unit_id': 'manufacturing.unit', 'source_lot_id': 'manufacturing.lot',
    'change_id': 'engineering.change', 'current_plan_id': 'engineering.plan',
    'plan_id': 'engineering.plan', 'supersedes_plan_id': 'engineering.plan',
    'decision_id': 'engineering.decision', 'approval_id': 'engineering.decision',
    'job_id': 'validation.job', 'reserved_by_job_id': 'validation.job',
    'result_id': 'validation.result', 'requirement_revision_id': 'engineering.requirement',
    'reservation_id': 'validation.reservation', 'link_id': 'planner.link', 'task_id': 'planner.task',
}
JSON_FIELDS = {}


def table(kind):
    if kind not in MODELS:
        raise ValueError('Unknown storage type')
    return kind.replace('.', '_')


def property_type(prop):
    if 'anyOf' in prop:
        prop = next(p for p in prop['anyOf'] if p.get('type') != 'null')
    return prop.get('type', 'object' if '$ref' in prop else 'string')


for kind, model in MODELS.items():
    JSON_FIELDS[kind] = {key for key, prop in model.model_json_schema()['properties'].items()
                         if property_type(prop) in ('object', 'array')}


def schema_statements():
    statements = []
    for kind, model in MODELS.items():
        properties = model.model_json_schema()['properties']
        fields = []
        for key, prop in properties.items():
            typ = property_type(prop)
            sqltype = 'INTEGER' if typ in ('integer', 'boolean') else 'TEXT'
            nullable = any(p.get('type') == 'null' for p in prop.get('anyOf', []))
            suffix = '' if nullable else ' NOT NULL'
            if key == 'id':
                suffix += ' PRIMARY KEY'
            if typ in ('integer', 'boolean'):
                suffix += f' CHECK ("{key}" IS NULL OR typeof("{key}") = \'integer\')'
            if key.endswith('_cents'):
                suffix += f' CHECK ("{key}" >= 0)'
            if key.endswith('_version') or key in ('plan_version', 'revision'):
                if typ == 'integer':
                    suffix += f' CHECK ("{key}" > 0)'
            if key in JSON_FIELDS[kind]:
                suffix += f' CHECK ("{key}" IS NULL OR json_valid("{key}"))'
            if key == 'owning_system':
                suffix += f" CHECK (owning_system = '{kind.split('.')[0]}')"
            fields.append(f'"{key}" {sqltype}{suffix}')
        if 'program_id' in properties:
            fields.append('UNIQUE(program_id, id)')
        for key in properties:
            target = REFS.get(key)
            if kind in ('manufacturing.recovery_decision', 'planner.recovery_task') and key == 'plan_id':
                target = 'manufacturing.recovery_plan'
            if kind == 'planner.recovery_task' and key == 'decision_id':
                target = 'manufacturing.recovery_decision'
            if kind in ('erp.commitment_decision', 'erp.delivery_commitment', 'planner.delivery_link') and key == 'plan_id':
                target = 'erp.commitment_plan'
            if kind in ('erp.delivery_commitment', 'planner.delivery_link') and key == 'decision_id':
                target = 'erp.commitment_decision'
            if kind == 'engineering.plan_state' and key == 'id':
                target = 'engineering.plan'
            if target:
                if key != 'program_id' and 'program_id' in properties and 'program_id' in MODELS[target].model_fields:
                    fields.append(f'FOREIGN KEY(program_id,"{key}") REFERENCES {table(target)}(program_id,id) DEFERRABLE INITIALLY DEFERRED')
                else:
                    fields.append(f'FOREIGN KEY("{key}") REFERENCES {table(target)}(id) DEFERRABLE INITIALLY DEFERRED')
        statements.append(f'CREATE TABLE {table(kind)} ({",".join(fields)})')
    unique = {
        'erp.delivery_request': [('program_id', 'order_id', 'line_id')],
        'erp.delivery_state': [('program_id', 'delivery_id')],
        'erp.commitment_plan': [('program_id', 'delivery_id', 'context_digest', 'selected_option'), ('program_id', 'delivery_id', 'plan_version')],
        'erp.commitment_decision': [('program_id', 'plan_id')],
        'erp.delivery_commitment': [('program_id', 'plan_id')],
        'planner.delivery_link': [('program_id', 'plan_id'), ('program_id', 'commitment_id')],
        'manufacturing.quality_investigation': [('program_id', 'exception_id', 'context_digest')],
        'manufacturing.recovery_plan': [('program_id', 'exception_id', 'context_digest'), ('program_id', 'exception_id', 'plan_version')],
        'manufacturing.recovery_decision': [('program_id', 'plan_id')],
        'planner.recovery_task': [('program_id', 'plan_id')],
        'engineering.requirement': [('program_id', 'requirement_id', 'revision')],
        'engineering.decision': [('program_id', 'plan_id')],
        'validation.job': [('program_id', 'plan_id')],
        'validation.reservation': [('job_id',), ('slot_id',), ('sample_id',)],
        'planner.link': [('program_id', 'plan_id'), ('program_id', 'job_id')],
        'planner.task': [('link_id',)],
        'validation.completion': [('program_id', 'job_id'), ('result_id',)],
        'engineering.evidence_review': [('program_id', 'evidence_digest')],
        'engineering.standard_request': [('program_id', 'change_id')],
        'validation.intake': [('program_id', 'change_id', 'request_content_version')],
    }
    for kind, indexes in unique.items():
        for index, columns in enumerate(indexes):
            statements.append(f'CREATE UNIQUE INDEX uq_{table(kind)}_{index} ON {table(kind)} ({",".join(columns)})')
    statements += [
        'CREATE TABLE demo_metadata (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL CHECK(json_valid(data)))',
        'CREATE TABLE idempotency_receipts (actor_id TEXT, method TEXT, route TEXT, key_hash TEXT, fingerprint TEXT NOT NULL, status INTEGER NOT NULL, body TEXT NOT NULL CHECK(json_valid(body)), PRIMARY KEY(actor_id,method,route,key_hash))',
        'CREATE TABLE audit_events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE, program_id TEXT, change_id TEXT, data TEXT NOT NULL CHECK(json_valid(data)))',
    ]
    immutable = ['erp.commitment_plan', 'erp.commitment_decision', 'erp.delivery_commitment', 'planner.delivery_link', 'manufacturing.quality_investigation', 'manufacturing.recovery_plan', 'manufacturing.recovery_decision', 'planner.recovery_task', 'engineering.plan', 'engineering.decision', 'validation.result', 'validation.job',
                 'validation.reservation', 'validation.history', 'validation.completion', 'engineering.evidence_review', 'planner.link', 'planner.task', 'engineering.document', 'validation.intake']
    for name in [table(k) for k in immutable] + ['audit_events', 'idempotency_receipts']:
        for operation in ('UPDATE', 'DELETE'):
            statements.append(f"CREATE TRIGGER immutable_{name}_{operation.lower()} BEFORE {operation} ON {name} BEGIN SELECT RAISE(ABORT,'immutable record'); END")
    for kind, protected in {
        'planner.milestone': ['baseline_at', 'program_id', 'order_id', 'content_version'],
        'erp.order': ['committed_delivery_at', 'quantity', 'product_id', 'planning_unit_value_cents', 'planning_value_basis'],
    }.items():
        statements.append(f"CREATE TRIGGER protect_{table(kind)} BEFORE UPDATE OF {','.join(protected)} ON {table(kind)} BEGIN SELECT RAISE(ABORT,'protected content'); END")
    return statements


def connect(path: Path):
    con = sqlite3.connect(path, isolation_level=None, timeout=2.0)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


class Store:
    def __init__(self, con):
        self.con = con
        row = con.execute('SELECT data FROM demo_metadata WHERE id=1').fetchone()
        self.meta = json.loads(row['data'])
        self.now = self.meta['scenario_now']

    def decode(self, kind, row):
        data = dict(row)
        for key in JSON_FIELDS[kind]:
            # Older demo files can omit newly optional read-only context fields.
            # Pydantic still rejects missing required fields; defaults add no facts.
            if data.get(key) is not None:
                data[key] = json.loads(data[key])
        return MODELS[kind].model_validate(data).model_dump(mode='json')

    def get(self, kind, record_id, actor=None):
        row = self.con.execute(f'SELECT * FROM {table(kind)} WHERE id=?', (record_id,)).fetchone()
        fail(row is not None, 404, 'NOT_FOUND', 'Resource not found.')
        data = self.decode(kind, row)
        if actor:
            self.authorize(data, actor)
        return data

    def authorize(self, data, actor):
        program_id = data.get('program_id')
        if program_id is not None:
            p = self.con.execute('SELECT customer_id FROM planner_program WHERE id=?', (program_id,)).fetchone()
            fail(p is not None and (program_id, p['customer_id']) in actor.scopes, 404, 'NOT_FOUND', 'Resource not found.')
        elif data['owning_system'] == 'engineering':
            allowed = [p for p in self.con.execute('SELECT id,customer_id,supplier_id FROM planner_program') if (p['id'],p['customer_id']) in actor.scopes]
            fail(any(data['id'] in (p['customer_id'],p['supplier_id']) for p in allowed), 404, 'NOT_FOUND', 'Resource not found.')
        if 'customer_id' in data:
            fail((data.get('program_id'),data['customer_id']) in actor.scopes, 404, 'NOT_FOUND', 'Resource not found.')

    def list(self, kind, actor=None, **filters):
        for key in filters:
            if key not in MODELS[kind].model_fields:
                raise ValueError('Unknown filter')
        if actor and 'program_id' in MODELS[kind].model_fields:
            if 'program_id' in filters:
                self.get('planner.program', filters['program_id'], actor)
            elif not actor.portfolio:
                self.get('planner.program', actor.program_id, actor)
                filters['program_id'] = actor.program_id
        where = ' AND '.join(f'"{key}"=?' for key in filters) or '1=1'
        rows = self.con.execute(f'SELECT * FROM {table(kind)} WHERE {where} ORDER BY id', tuple(filters.values())).fetchall()
        result = [self.decode(kind, row) for row in rows]
        if actor and actor.portfolio:
            result = [r for r in result if r.get('program_id') in {p for p,c in actor.scopes}]
        if actor:
            for data in result:
                self.authorize(data, actor)
        return result

    def insert(self, kind, data):
        data = MODELS[kind].model_validate(data).model_dump(mode='json')
        values = [canonical(v) if k in JSON_FIELDS[kind] and v is not None else v for k, v in data.items()]
        names = ','.join(f'"{k}"' for k in data)
        self.con.execute(f'INSERT INTO {table(kind)} ({names}) VALUES ({",".join("?" for _ in values)})', values)
        return data

    def update(self, kind, record_id, fields, expected=None):
        data = self.get(kind, record_id)
        data.update(fields)
        data = MODELS[kind].model_validate(data).model_dump(mode='json')
        values = [canonical(data[k]) if k in JSON_FIELDS[kind] and data[k] is not None else data[k] for k in fields]
        where = 'id=?'
        values.append(record_id)
        if expected:
            where += ' AND ' + ' AND '.join(f'"{k}"=?' for k in expected)
            values.extend(expected.values())
        result = self.con.execute(f'UPDATE {table(kind)} SET {",".join(chr(34)+k+chr(34)+"=?" for k in fields)} WHERE {where}', values)
        fail(result.rowcount == 1, 409, 'RESOURCE_CONFLICT', 'Record changed concurrently.')
        return data


@contextmanager
def read_store(path):
    con = connect(path)
    try:
        con.execute('BEGIN')
        yield Store(con)
    finally:
        con.rollback()
        con.close()


def restrict_writes(con, domain):
    allowed = {table(k) for k in WRITES[domain]} | {'audit_events', 'idempotency_receipts', 'sqlite_sequence'}

    def authorize(action, name, column, db_name, trigger):
        if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE):
            if name not in allowed:
                return sqlite3.SQLITE_DENY
        if action in (sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_ALTER_TABLE):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    con.set_authorizer(authorize)
