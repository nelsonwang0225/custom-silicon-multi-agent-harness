"""Shared read-only product semantics. These contracts confer no action authority."""
from typing import Literal
from pydantic import Field
from ..models import Model

CaseState = Literal['new','investigating','draft_ready','needs_review','approved','executing',
    'verification_required','waiting_external','completed_technical','completed_recovery','escalated',
    'partial_failure','stale','failed','unavailable','handoff_verified']

class CaseSummary(Model):
    change_id: str
    program_id: str = 'PRG-A17'
    customer_id: str = 'CUST-FML01'
    workflow_id: str
    route: str
    title: str
    state: CaseState
    state_label: str
    detail: str
    next_action: str
    boundary: str
    source_available: bool
    attention: Literal['none','human_review','blocker','failure','external','stale'] = 'none'
    priority: int = 100
    issue_key: str
    run_id: str | None = None
    decision_ids: list[str] = Field(default_factory=list)
    href: str
    source_href: str

class DecisionSummary(Model):
    id: str
    change_id: str
    kind: Literal['validation_authorization','engineering_evidence','engineering_escalation','quality_recovery','delivery_commitment']
    title: str
    status: Literal['needs_review','approved','rejected','executed','stale','partial_failure','verification_required','unavailable']
    current: bool
    requires_human: bool
    version: int | None = None
    digest: str
    source_decision_id: str | None = None
    reviewer: str | None = None
    required_role: str
    run_id: str | None = None
    execution: str
    href: str

class CaseDependency(Model):
    from_case: str | None = None
    to_case: str
    kind: Literal['supply','technical']
    source_ids: list[str]
    detail: str
    source_available: bool = True
