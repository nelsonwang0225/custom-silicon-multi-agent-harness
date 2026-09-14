"""Closed demo-management contracts; never registered as model tools."""
from typing import Literal
from pydantic import Field, model_validator
from ..models import Model

DemoScope = Literal['full','CR-017','CR-019','QE-004','DR-009','QE-011']

class DemoResetRequest(Model):
    scope: DemoScope
    confirmation: Literal['RESET']
    expected_epoch: str = Field(min_length=1, max_length=80)
    restart_opening: bool = False

    @model_validator(mode='after')
    def full_restart_only(self):
        if self.restart_opening and self.scope != 'full':
            raise ValueError('Restart requires a full demo reset')
        return self

class BaselineCheck(Model):
    scope: DemoScope
    demo_baseline_version: Literal['phase09-v1'] = 'phase09-v1'
    baseline_valid: bool
    checked_at: str
    discrepancies: list[str] = Field(default_factory=list)
    quantities: dict[str, int | None] = Field(default_factory=dict)
    source_digest: str | None = None
    control_digest: str | None = None
    source_readback: dict[str, str] = Field(default_factory=dict)
    scenario_checks: dict[str, bool] = Field(default_factory=dict)

class DemoAudit(Model):
    reset_id: str
    scope: DemoScope
    timestamp: str
    actor: Literal['demo-maintainer'] = 'demo-maintainer'
    result: Literal['started','restored','partial','failed']
    stage: str
    affected_systems: list[str] = Field(default_factory=list)
    baseline_valid: bool = False
    error_code: str | None = None

class DemoState(Model):
    schema_version: Literal[1] = 1
    demo_baseline_version: Literal['phase09-v1'] = 'phase09-v1'
    epoch: str = 'initial'
    recovery_required: bool = False
    pending_scope: DemoScope | None = None
    audit: list[DemoAudit] = Field(default_factory=list)

class DemoControls(Model):
    enabled: bool
    demo_baseline_version: Literal['phase09-v1'] = 'phase09-v1'
    epoch: str = 'initial'
    recovery_required: bool = False
    pending_scope: DemoScope | None = None
    scopes: list[DemoScope] = Field(default_factory=list)
    latest: DemoAudit | None = None
    archived_reset_count: int = 0

class DemoPreview(Model):
    scope: DemoScope
    epoch: str
    affected_systems: list[str]
    resets: list[str]
    preserves: list[str]
    shared_dependencies: list[str]
    allowed: bool
    discrepancies: list[str] = Field(default_factory=list)

class DemoResetResult(Model):
    result: Literal['restored','partial','failed']
    epoch: str
    audit: DemoAudit
    validation: BaselineCheck
    opening_status: Literal['not_requested', 'armed', 'failed'] = 'not_requested'
    opening_error: str | None = None
