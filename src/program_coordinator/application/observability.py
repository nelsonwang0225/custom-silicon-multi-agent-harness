"""Bounded, sanitized visible Concierge history in the existing metadata index.

These are historical observations, never source truth or executable confirmations.
"""
import re
from pydantic import Field
from ..models import Model


def visible(value):
    text = str(value)
    text = re.sub(r'(?i)\b(?:bearer\s+\S+|sk-[\w-]+|(?:api[_-]?key|authorization|password|secret)\s*[:=]\s*\S+)', '[redacted]', text)
    text = re.sub(r'(?:file://\S+|/(?:Users|home|tmp|private|var|etc)/[^\s,;]+)', '[local path omitted]', text)
    return text[:6000]


def identifier(value):
    return value if isinstance(value, str) and not value.startswith('sk-') and re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}', value) else None


def safe_link(value):
    return value if isinstance(value, str) and re.fullmatch(r'/(?:control|engineering|validation|manufacturing|erp|programs)(?:/[A-Za-z0-9_%.-]+)*(?:\?[A-Za-z0-9_=&%-]+)?', value) and '..' not in value else None


class ObservedCard(Model):
    knowledge_chunk_id: str | None = None
    kind: str
    title: str
    facts: list[tuple[str,str]] = Field(default_factory=list)
    links: list[tuple[str,str]] = Field(default_factory=list)
    run_id: str | None = None


class ObservedTurn(Model):
    message_id: str
    timestamp: str
    context: str
    user_text: str
    text: str
    status: str
    classification: str
    error_code: str | None = None
    cards: list[ObservedCard] = Field(default_factory=list)
    model: str | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_calls: int | None = None
    service_calls: list[str] = Field(default_factory=list)


class ObservedConfirmation(Model):
    timestamp: str
    operation: str
    actor_id: str
    status: str
    run_id: str | None = None
    plan_id: str | None = None
    automation_id: str | None = None


class ObservedSession(Model):
    owner_actor_id: str | None = None
    session_id: str
    customer_id: str
    program_id: str
    created_at: str
    updated_at: str
    turns: list[ObservedTurn] = Field(default_factory=list)
    confirmations: list[ObservedConfirmation] = Field(default_factory=list)
    run_ids: list[str] = Field(default_factory=list)


def retain_turn(host, turn):
    # Best effort observability must never affect action authority or response delivery.
    from .models import now_utc
    try:
        cards=[ObservedCard(kind=c.kind,knowledge_chunk_id=c.knowledge_chunk_id,title=visible(c.title),facts=[(visible(k),visible(v)) for k,v in c.facts if not (c.knowledge_chunk_id and k=='Passage (source text)')],
            links=[(visible(l.label),l.href) for l in c.links if safe_link(l.href)],run_id=identifier(c.run_id)) for c in turn.cards]
        t=ObservedTurn(message_id=turn.message_id,timestamp=turn.created_at,context=safe_link(turn.context) or '/control/overview',
            user_text=visible(turn.user_text),text=visible(turn.text),status=turn.status,classification=turn.classification,error_code=identifier(turn.error_code),cards=cards,
            model=identifier(turn.telemetry.model),latency_ms=turn.telemetry.latency_ms,
            input_tokens=turn.telemetry.input_tokens,output_tokens=turn.telemetry.output_tokens,model_calls=turn.telemetry.model_calls,
            service_calls=[visible(v) for v in turn.telemetry.service_calls])
        with host.store.transaction(write=True) as data:
            s=data.concierge_sessions.setdefault(turn.session_id,ObservedSession(session_id=turn.session_id,customer_id='CUST-FML01',
                program_id='PRG-A17',owner_actor_id=turn.actor_id,created_at=turn.created_at,updated_at=now_utc()))
            s.turns=([v for v in s.turns if v.message_id!=t.message_id]+[t])[-48:]
            s.updated_at=now_utc();s.run_ids=list(dict.fromkeys(s.run_ids+[c.run_id for c in cards if c.run_id]))[-96:]
            while len(data.concierge_sessions)>256:del data.concierge_sessions[next(iter(data.concierge_sessions))]
    except (OSError,ValueError):
        host.observability_error='CONCIERGE_HISTORY_UNAVAILABLE'


def retain_confirmation(host, session, operation, actor_id, status, body=None, result=None):
    from .models import now_utc
    body=body or {};result=result or {}
    try:
        with host.store.transaction(write=True) as data:
            s=data.concierge_sessions.get(session)
            if not s:return
            run_id=identifier(result.get('run_id') or body.get('run_id') or body.get('reference',{}).get('run_id'))
            s.confirmations.append(ObservedConfirmation(timestamp=now_utc(),operation=visible(operation),actor_id=identifier(actor_id) or 'unavailable',
                status=visible(status),run_id=run_id,plan_id=identifier(body.get('plan_id') or body.get('reference',{}).get('proposal_id')),
                automation_id=identifier(result.get('automation_id'))))
            s.confirmations=s.confirmations[-96:];s.updated_at=now_utc()
            if run_id:s.run_ids=list(dict.fromkeys(s.run_ids+[run_id]))[-96:]
    except (OSError,ValueError):host.observability_error='CONCIERGE_HISTORY_UNAVAILABLE'
