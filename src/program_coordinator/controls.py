"""Code-enforced capability, delegation, and operational limits."""

from pydantic import Field
from program_investigator.config import InvestigatorConfig
from .models import Role, Model


class HarnessError(Exception):
    """Fixed safe error codes only; never raw request/credential/error prose."""


def failure_code(exc, fallback, _seen=None):
    """Unwrap SDK task groups without retaining untrusted exception messages."""
    seen=set() if _seen is None else _seen
    if id(exc) in seen or len(seen)>=20:
        return fallback
    seen.add(id(exc))
    if isinstance(exc, HarnessError):
        return str(exc)
    if isinstance(exc, TimeoutError):
        return "specialist_timeout"
    if isinstance(exc, BaseExceptionGroup):
        for inner in exc.exceptions:
            code = failure_code(inner, fallback, seen)
            if code != fallback:
                return code
    # Agents SDK wraps MCP failures. Retain only our fixed safe code, never
    # the SDK wrapper message (which can contain tool arguments or payloads).
    for inner in (exc.__cause__,exc.__context__):
        if inner is not None:
            code=failure_code(inner,fallback,seen)
            if code!=fallback:
                return code
    return fallback


class HarnessConfig(InvestigatorConfig):
    customer_id: str = "CUST-FML01"
    program_id: str = "PRG-A17"
    max_turns: int = Field(default=12, ge=1, le=20)
    max_coordinator_turns: int = Field(default=10, ge=2, le=20)
    max_specialist_calls: int = Field(default=8, ge=1, le=16)
    max_delegation_depth: int = Field(default=2, ge=1, le=3)
    # A first review may request narrowly scoped follow-up work. The Coordinator
    # needs one more pass to reconcile that new evidence and explicitly resolve
    # the original question before final synthesis.
    max_reconcile_rounds: int = Field(default=2, ge=0, le=2)
    max_tool_calls: int = Field(default=80, ge=1, le=150)
    tool_timeout_seconds: float = Field(default=45, gt=0, le=60)
    specialist_timeout_seconds: float = Field(default=300, gt=0, le=600)
    run_timeout_seconds: float = Field(default=900, gt=0, le=1200)


TOOL_MATRIX: dict[Role, frozenset[str]] = {
    "coordinator": frozenset({"get_change_request", "get_program", "get_document", "get_documents"}),
    "change_impact": frozenset({"get_change_request", "get_requirement_revision", "get_configuration",
        "get_workload_profile", "get_document", "get_program", "get_program_milestone"}),
    "validation_evidence": frozenset({"get_validation_coverage", "get_validation_options", "get_validation_result",
        "get_validation_samples", "get_validation_jobs", "get_validation_job", "get_requirement_revision",
        "get_configuration", "get_workload_profile", "get_procedure", "get_acceptance_criteria", "get_policy",
        "get_document"}),
    "program_commercial": frozenset({"get_program", "get_program_milestone", "get_dependencies",
        "get_implementation_links", "get_customer_order", "get_cost_rates", "get_change_request"}),
    "manufacturing": frozenset({"get_manufacturing_unit", "get_manufacturing_lot", "get_validation_samples"}),
}

GRAPH: dict[Role, frozenset[str]] = {
    "coordinator": frozenset({"change_impact", "validation_evidence", "program_commercial", "manufacturing"}),
    "change_impact": frozenset({"validation_evidence", "program_commercial"}),
    "validation_evidence": frozenset({"manufacturing", "program_commercial"}),
    "program_commercial": frozenset({"change_impact"}),
    "manufacturing": frozenset(),
}

TRANSITIONS = {
    "intake": {"triage", "terminated"}, "triage": {"specialists", "synthesis", "terminated"},
    "specialists": {"reconcile", "terminated"}, "reconcile": {"specialists", "synthesis", "terminated"},
    "synthesis": {"completed", "terminated"}, "completed": set(), "terminated": set(),
}


def transition(state, stage):
    if stage not in TRANSITIONS[state.workflow_stage]:
        raise HarnessError("invalid_state_transition")
    state.transitions.append(f"{state.workflow_stage}->{stage}")
    state.workflow_stage = stage


def validate_workflow(work):
    roles = {w.specialist for w in work}
    done = set()
    pending = list(work)
    while pending:
        ready = [w for w in pending if set(w.depends_on) <= done]
        if not ready or any(not set(w.depends_on) <= roles for w in pending):
            raise HarnessError("invalid_workflow_dependencies")
        done.update(w.specialist for w in ready)
        pending = [w for w in pending if w not in ready]
