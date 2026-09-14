"""Allowlisted Operations projections: no arbitrary payloads or trace contents."""
from pydantic import Field
from ..models import Model
from ..application.observability import ObservedSession

class OpsLink(Model):
    label: str
    href: str

class OpsAgent(Model):
    name: str
    invocation_id: str | None = None
    caller: str | None = None
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: float | None = None
    summary: str | None = None
    error: str | None = None

class OpsCall(Model):
    name: str
    caller: str
    target: str
    status: str
    duration_ms: float | None = None
    identifiers: list[str] = Field(default_factory=list)
    source_id: str | None = None
    link: str | None = None

class OpsEvidence(Model):
    source_id: str
    tool: str
    record_id: str | None = None
    content_version: int | None = None
    record_version: int | None = None
    applicability: str = 'Referenced in analysis; inspect source for applicability'
    link: str

class OpsAction(Model):
    name: str
    status: str
    verification: str
    source_id: str | None = None
    error: str | None = None
    idempotency_key: str | None = None
    expected: str = 'Not recorded'
    actual: str = 'Not recorded'
    attempts: list[tuple[str,str]] = Field(default_factory=list)

class OpsEvent(Model):
    timestamp: str | None = None
    stage: str
    actor: str | None = None
    status: str | None = None
    error: str | None = None

class OpsRun(Model):
    current_case_state: str | None = None
    current_case_label: str | None = None
    source_checked_at: str | None = None
    run_id: str
    case_id: str
    program_id: str
    workflow_id: str
    invocation_source: str
    policy_route: str = ''
    event_id: str | None = None
    event_name: str | None = None
    event_version: int | None = None
    actor: str
    started_at: str
    completed_at: str | None = None
    duration_ms: float | None = None
    runtime_state: str
    business_outcome: str
    decision_state: str = 'Not recorded'
    verification_state: str = 'Not recorded'
    trace_id: str | None = None
    model: str | None = None
    execution_mode: str
    attention: bool = False
    case_link: str
    session_ids: list[str] = Field(default_factory=list)

class OpsRunDetail(Model):
    run: OpsRun
    question: str | None = None
    agents: list[OpsAgent] = Field(default_factory=list)
    calls: list[OpsCall] = Field(default_factory=list)
    evidence: list[OpsEvidence] = Field(default_factory=list)
    timeline: list[OpsEvent] = Field(default_factory=list)
    actions: list[OpsAction] = Field(default_factory=list)
    decision: list[tuple[str,str]] = Field(default_factory=list)
    links: list[OpsLink] = Field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    model_latency_ms: float | None = None
    human_wait_ms: float | None = None
    external_wait_ms: float | None = None
    artifact_state: str = 'Unavailable'
    failure: list[tuple[str,str]] = Field(default_factory=list)
    facts: list[tuple[str,str]] = Field(default_factory=list)
    source_checked_at: str | None = None

class OpsEvalCase(Model):
    case_id: str
    passed: bool
    critical_failures: list[str]
    semantic: str

class OpsEval(Model):
    eval_id: str
    label: str
    mode: str
    timestamp: str
    total: int
    passed: int
    failed: int
    critical_failures: list[tuple[str,str]]
    hard_gate: str
    semantic: str
    model: str | None = None
    cases: list[OpsEvalCase]

class OpsHealth(Model):
    system: str
    status: str = 'Unknown / not checked'
    checked_at: str | None = None
    detail: str | None = None

class OpsSessionSummary(Model):
    session_id: str
    created_at: str
    updated_at: str
    turn_count: int
    run_ids: list[str]

class OpsIndex(Model):
    runs: list[OpsRun]
    evals: list[OpsEval]
    unavailable_artifacts: list[str]
    sessions: list[OpsSessionSummary]
    health: list[OpsHealth]
    runtime: str
    observability_error: str | None = None
