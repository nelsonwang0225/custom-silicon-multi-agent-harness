"""Durable configuration previews. No runner, timer, listener or source gateway."""
from contextlib import contextmanager
from datetime import date
import fcntl
import os
from typing import Annotated, Literal
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
from ..models import ID, Model
from .contracts import digest
from .models import WorkflowError, now_utc
from .demo_identity import AUTOMATION, ENGINEER
from .store import ActivityStore
from .workflow_catalog import Authority, get_workflow

EVENTS = {
    'engineering': ['requirement_changed', 'engineering_decision_updated'],
    'validation': ['result_received', 'job_status_changed'],
    'manufacturing': ['quality_exception_created', 'lot_status_changed'],
    'erp': ['order_commitment_changed'],
    'planner': ['milestone_changed'],
}

class ManualTrigger(Model):
    type: Literal['manual'] = 'manual'

class ChatTrigger(Model):
    type: Literal['chat'] = 'chat'

class ScheduleTrigger(Model):
    type: Literal['schedule'] = 'schedule'
    cadence: Literal['daily', 'weekdays', 'weekly']
    time: str = Field(pattern=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')
    timezone: str = Field(min_length=1, max_length=100)
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')

    @model_validator(mode='after')
    def valid_schedule(self):
        try:
            ZoneInfo(self.timezone)
        except (ValueError, ZoneInfoNotFoundError):
            raise ValueError('Unknown timezone') from None
        if (self.cadence == 'weekly') != (self.weekday is not None):
            raise ValueError('Weekday is required only for a weekly schedule')
        if self.start_date:
            date.fromisoformat(self.start_date)
        return self

class EventTrigger(Model):
    type: Literal['source_event'] = 'source_event'
    system: Literal['engineering', 'validation', 'manufacturing', 'erp', 'planner']
    event: Literal['requirement_changed', 'engineering_decision_updated', 'result_received', 'job_status_changed',
                   'quality_exception_created', 'lot_status_changed', 'order_commitment_changed', 'milestone_changed']

    @model_validator(mode='after')
    def owned_event(self):
        if self.event not in EVENTS[self.system]:
            raise ValueError('Event does not belong to this source system')
        return self

class RiskCondition(Model):
    field: Literal['milestone_risk'] = 'milestone_risk'
    operator: Literal['equals'] = 'equals'
    value: Literal['high'] = 'high'

class AgeCondition(Model):
    field: Literal['evidence_age_hours', 'approval_pending_hours', 'validation_missing_hours']
    operator: Literal['greater_than'] = 'greater_than'
    value: int = Field(ge=1, le=8760)

class QuantityCondition(Model):
    field: Literal['eligible_quantity'] = 'eligible_quantity'
    operator: Literal['less_than'] = 'less_than'
    value: Literal['requested_quantity'] = 'requested_quantity'

class ConditionTrigger(Model):
    type: Literal['condition'] = 'condition'
    condition: Annotated[RiskCondition | AgeCondition | QuantityCondition, Field(discriminator='field')]

TriggerConfig = Annotated[ManualTrigger | ScheduleTrigger | EventTrigger | ConditionTrigger | ChatTrigger, Field(discriminator='type')]

class Safeguards(Model):
    deduplicate_by: Literal['case', 'event'] = 'case'
    reopen_resolved_case: Literal[False] = False
    suppress_duplicate_notifications: bool = True
    minimum_recheck_minutes: int = Field(default=60, ge=5, le=10080)

class AutomationInput(Model):
    name: str = Field(min_length=1, max_length=100)
    workflow_id: ID
    customer_id: ID = 'CUST-FML01'
    program_id: ID = 'PRG-A17'
    case_scope: ID | None = None
    trigger: TriggerConfig
    authority: Authority = 'read_only'
    notification_preference: Literal['important_changes', 'all_outcomes', 'none'] = 'important_changes'
    configuration_state: Literal['configured', 'paused'] = 'configured'
    safeguards: Safeguards = Field(default_factory=Safeguards)

    @field_validator('name')
    @classmethod
    def nonblank_name(cls, value):
        if not value.strip():
            raise ValueError('Name required')
        return value.strip()

class CreateAutomation(Model):
    request_id: ID
    configuration: AutomationInput

class UpdateAutomation(CreateAutomation):
    expected_version: int = Field(ge=1)

class ChangeConfigurationState(Model):
    request_id: ID
    expected_version: int = Field(ge=1)
    configuration_state: Literal['configured', 'paused']

class DeleteAutomation(Model):
    request_id: ID
    expected_version: int = Field(ge=1)

class DeletedAutomation(Model):
    deleted: Literal[True] = True
    automation_id: ID

class AutomationDefinition(AutomationInput):
    automation_id: ID
    version: int = 1
    owner_actor_id: ID
    updated_by: ID
    created_at: str
    updated_at: str
    execution_mode: Literal['configuration_preview'] = 'configuration_preview'
    background_execution_enabled: Literal[False] = False
    seeded_example: bool = False

class AutomationView(AutomationDefinition):
    workflow_name: str
    workflow_mode: Literal['Connected', 'Simulated', 'Preview']
    trigger_summary: str

class AutomationAudit(Model):
    automation_id: ID
    actor_id: ID
    timestamp: str
    action: Literal['create', 'update', 'pause', 'resume', 'delete', 'denied']
    version: int
    error_code: str | None = None

class AutomationReceipt(Model):
    request_digest: str
    automation_id: ID
    # Receipt retains the exact response so an old retry cannot revert a later edit.
    result: AutomationDefinition | None

class AutomationIndex(Model):
    schema_version: Literal[1] = 1
    examples_seeded: bool = False
    definitions: dict[str, AutomationDefinition] = Field(default_factory=dict)
    receipts: dict[str, AutomationReceipt] = Field(default_factory=dict)
    activity: list[AutomationAudit] = Field(default_factory=list)


def trigger_summary(trigger):
    words = lambda s: s.replace('_', ' ').capitalize()
    if isinstance(trigger, ScheduleTrigger):
        hour, minute = map(int, trigger.time.split(':'))
        time = f'{hour % 12 or 12}:{minute:02d} {"AM" if hour < 12 else "PM"}'
        cadence = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][trigger.weekday] if trigger.cadence == 'weekly' else words(trigger.cadence)
        return f'{cadence} at {time} · {trigger.timezone}' + (f' · from {trigger.start_date}' if trigger.start_date else '')
    if isinstance(trigger, EventTrigger):
        return f'{words(trigger.system)} · {words(trigger.event)}'
    if isinstance(trigger, ConditionTrigger):
        c = trigger.condition
        return f'{words(c.field)} {c.operator.replace("_", " ")} {str(c.value).replace("_", " ")}'
    return 'Explicit manual request' if isinstance(trigger, ManualTrigger) else 'Explicit Concierge request'


def automation_view(record):
    workflow = get_workflow(record.workflow_id)
    return AutomationView(**record.model_dump(), workflow_name=workflow.name,
        workflow_mode=workflow.mode, trigger_summary=trigger_summary(record.trigger))

def example_definitions():
    stamp = "2026-11-16T09:00:00Z"
    definitions = {}
    examples = [
        ('example_cr017', 'CR-017 Evidence Reassessment', 'requirement_change_analysis', 'CR-017',
         EventTrigger(system='validation', event='result_received'), 'read_only'),
        ('example_delivery', 'Morning Delivery Readiness', 'delivery_readiness', None,
         ScheduleTrigger(cadence='weekdays', time='07:00', timezone='America/Chicago'), 'read_only'),
        ('example_yield', 'Yield Exception Watch', 'yield_exception_recovery', None,
         EventTrigger(system='manufacturing', event='quality_exception_created'), 'proposal_only'),
    ]
    for key, name, workflow, case, trigger, authority in examples:
        definitions[key] = AutomationDefinition(automation_id=key, name=name, workflow_id=workflow,
            case_scope=case, trigger=trigger, authority=authority, owner_actor_id='demo-seed', updated_by='demo-seed',
            created_at=stamp, updated_at=stamp, seeded_example=True)
    return definitions


class AutomationStore:
    """Same POSIX lock, atomic replacement and fsync convention as ActivityStore.

    A separate file prevents configuration edits from touching case/run/source state.
    Receipts and tombstones survive deletions and process restarts.
    """
    def __init__(self, directory):
        self.directory = directory
        self.path = directory / 'automation-configurations.json'

    @contextmanager
    def transaction(self, *, write=False):
        lock_path = self.directory / 'automation-configurations.lock'
        ActivityStore._safe_file(lock_path)
        with os.fdopen(os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), 'r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            ActivityStore._safe_file(self.path)
            data = AutomationIndex.model_validate_json(self.path.read_text()) if self.path.exists() else AutomationIndex()
            yield data
            if write:
                encoded = data.model_dump_json(indent=2)
                AutomationIndex.model_validate_json(encoded)
                temp = self.directory / ('automation-' + uuid4().hex + '.tmp')
                try:
                    with os.fdopen(os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as target:
                        target.write(encoded + '\n'); target.flush(); os.fsync(target.fileno())
                    os.replace(temp, self.path)
                    fd = os.open(self.directory, os.O_RDONLY)
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                finally:
                    temp.unlink(missing_ok=True)

    def seed_examples(self):
        with self.transaction(write=True) as data:
            if data.examples_seeded:
                return
            data.definitions.update(example_definitions())
            data.examples_seeded = True

    def list(self, actor):
        with self.transaction() as data:
            return [automation_view(a) for a in sorted(data.definitions.values(), key=lambda a: a.updated_at, reverse=True)
                    if (a.customer_id, a.program_id) in actor.scopes]

    def read(self, key, actor):
        with self.transaction() as data:
            item = data.definitions.get(key)
            if not item or (item.customer_id, item.program_id) not in actor.scopes:
                raise WorkflowError('AUTOMATION_NOT_FOUND')
            return automation_view(item)

    @staticmethod
    def validate(configuration, actor):
        actor.require_scope(configuration.customer_id, configuration.program_id)
        # Current trusted host has only this installed source scope. Concepts may not widen it.
        if (configuration.customer_id, configuration.program_id) != ('CUST-FML01', 'PRG-A17'):
            raise WorkflowError('SCOPE_FORBIDDEN')
        workflow = get_workflow(configuration.workflow_id)
        if not workflow:
            raise WorkflowError('UNKNOWN_WORKFLOW')
        if configuration.authority not in workflow.configuration_authorities:
            raise WorkflowError('AUTOMATION_AUTHORITY_EXCEEDED')
        if workflow.manual_available:
            event_scope_preview = workflow.workflow_id == 'yield_exception_recovery' and isinstance(configuration.trigger, EventTrigger) and configuration.case_scope is None
            schedule_scope_preview = workflow.workflow_id == 'delivery_readiness' and isinstance(configuration.trigger, ScheduleTrigger) and configuration.case_scope is None
            if configuration.case_scope not in workflow.cases and not event_scope_preview and not schedule_scope_preview:
                raise WorkflowError('CASE_SCOPE_MISMATCH')
        elif configuration.case_scope is not None:
            # Future stories are not persisted business cases.
            raise WorkflowError('CASE_SCOPE_MISMATCH')
        if not isinstance(configuration.trigger, EventTrigger) and configuration.safeguards.deduplicate_by == 'event':
            raise WorkflowError('EVENT_DEDUP_REQUIRES_EVENT_TRIGGER')

    def mutate(self, action, body, actor, key=None):
        try:
            return self._mutate(action, body, actor, key)
        except WorkflowError as exc:
            if str(exc) != 'UNSAFE_METADATA_STORAGE':
                with self.transaction(write=True) as data:
                    data.activity.append(AutomationAudit(automation_id=key if key and key in data.definitions else 'configuration_request',
                        actor_id=actor.actor_id, timestamp=now_utc(), action='denied', version=0, error_code=str(exc)))
            raise

    def _mutate(self, action, body, actor, key=None):
        if actor is not AUTOMATION and actor is not ENGINEER:
            raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        if action in {'create', 'update'}:
            self.validate(body.configuration, actor)
        fingerprint = digest({'action': action, 'target': key, 'body': body.model_dump(mode='json'), 'actor': actor.actor_id})
        with self.transaction(write=True) as data:
            prior = data.receipts.get(body.request_id)
            if prior:
                if prior.request_digest != fingerprint:
                    raise WorkflowError('CONFIGURATION_REQUEST_CONFLICT')
                return automation_view(prior.result) if prior.result else None
            stamp = now_utc()
            if action == 'create':
                key = 'automation_' + uuid4().hex
                result = AutomationDefinition(**body.configuration.model_dump(), automation_id=key,
                    owner_actor_id=actor.actor_id, updated_by=actor.actor_id, created_at=stamp, updated_at=stamp)
                version = 1
            else:
                current = data.definitions.get(key)
                if not current or (current.customer_id, current.program_id) not in actor.scopes:
                    raise WorkflowError('AUTOMATION_NOT_FOUND')
                if current.version != body.expected_version:
                    raise WorkflowError('STALE_AUTOMATION_VERSION')
                version = current.version + 1
                if action == 'delete':
                    result = None
                    del data.definitions[key]
                else:
                    fields = body.configuration.model_dump() if action == 'update' else {'configuration_state': body.configuration_state}
                    result = AutomationDefinition.model_validate({**current.model_dump(), **fields,
                        'version': version, 'updated_at': stamp, 'updated_by': actor.actor_id})
            if result:
                data.definitions[key] = result
            data.receipts[body.request_id] = AutomationReceipt(request_digest=fingerprint, automation_id=key, result=result)
            kind = ('pause' if body.configuration_state == 'paused' else 'resume') if action == 'state' else action
            data.activity.append(AutomationAudit(automation_id=key, actor_id=actor.actor_id, timestamp=stamp, action=kind, version=version))
            return automation_view(result) if result else None
