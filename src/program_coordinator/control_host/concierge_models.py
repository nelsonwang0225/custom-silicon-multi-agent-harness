"""Bounded visible conversation contracts. No source tools or write arguments."""
from typing import Literal
from pydantic import Field
from ..models import Model

Case = Literal['CR-017', 'CR-019', 'QE-004', 'DR-009']
Intent = Literal['EXPLAIN', 'INVESTIGATE', 'COMPARE', 'ACT', 'NAVIGATE', 'AUTOMATION_CONFIGURATION', 'CLARIFY', 'UNSUPPORTED']

class Route(Model):
    knowledge_profile: Literal['CHANGE_IMPACT','VALIDATION_EVIDENCE','MANUFACTURING_QUALITY','PROGRAM_COMMERCIAL'] | None = None
    intent: Intent
    case_id: Case | None
    topic: Literal['status', 'evidence', 'cause', 'supply', 'options', 'decision', 'execute', 'run', 'downstream', 'policy', 'attention', 'knowledge']
    target: Literal['case', 'run', 'evidence', 'decision', 'workflow', 'source']
    cadence: Literal['daily', 'weekdays', 'weekly'] | None
    time: str | None = Field(pattern=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$')
    timezone: str | None
    weekday: int | None = Field(ge=0, le=6)
    watch: bool

class ChatRequest(Model):
    session_id: str = Field(pattern=r'^chat_[a-f0-9]{32}$')
    message_id: str = Field(pattern=r'^msg_[a-f0-9]{32}$')
    context: str = Field(min_length=8, max_length=400)
    text: str = Field(min_length=1, max_length=3000)

class Confirmation(Model):
    context: str = Field(min_length=8, max_length=400)
    confirmed: Literal[True]

class Link(Model):
    label: str
    href: str

class Card(Model):
    knowledge_chunk_id: str | None = None
    kind: Literal['status', 'evidence', 'options', 'decision', 'run', 'action', 'automation', 'navigation']
    title: str
    facts: list[tuple[str, str]] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    action_id: str | None = None
    action_label: str | None = None
    required_role: str | None = None
    run_id: str | None = None

class Telemetry(Model):
    model: str | None = None
    latency_ms: int = 0
    model_calls: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    service_calls: list[str] = Field(default_factory=list)

class Turn(Model):
    actor_id: str | None = None
    session_id: str
    message_id: str
    context: str
    user_text: str
    created_at: str
    status: Literal['running', 'completed', 'failed', 'cancelled'] = 'running'
    intent: Intent | None = None
    classification: Literal['READ', 'RUN', 'DECISION', 'EXECUTION', 'AUTOMATION_SAVE'] = 'READ'
    text: str = ''
    cards: list[Card] = Field(default_factory=list)
    error_code: str | None = None
    telemetry: Telemetry = Field(default_factory=Telemetry)
