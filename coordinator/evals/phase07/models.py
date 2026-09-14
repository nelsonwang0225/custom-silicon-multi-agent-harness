"""Versioned contracts for observable behavior, not private reasoning traces."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Dimension = Literal['evidence_grounding', 'applicability', 'factual_correctness',
    'uncertainty', 'unsupported_claims', 'tool_selection', 'governance',
    'proposal_quality', 'execution_truthfulness', 'escalation', 'completeness']
DIMENSIONS = list(Dimension.__args__)
Workflow = Literal['requirement_change_analysis', 'yield_exception_recovery', 'delivery_readiness']


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, hide_input_in_errors=True)


class Evidence(Model):
    record_id: str
    content_version: int = Field(ge=1)
    use: Literal['support', 'reject', 'context']
    pointer: str = ''
    value: Any = None


class ToolReadReceipt(Model):
    """Observer-owned arguments and returned data; never an agent assertion."""
    source_id: str = Field(min_length=1)
    arguments: dict[str, Any]
    data: dict[str, Any] | None


class ValidationJobTarget(Model):
    """Expected identity from the current plan, independent of the job read."""
    job_id: str = Field(min_length=1)
    change_id: str = Field(min_length=1)
    program_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)

    @classmethod
    def from_change(cls, change):
        if not isinstance(change, dict) or not isinstance(change.get('plans'), list):
            return None
        plans = [p for p in change['plans'] if isinstance(p, dict)
                 and p.get('id') == change.get('current_plan_id')]
        if len(plans) != 1:
            return None
        plan = plans[0]
        if (plan.get('change_id') != change.get('id') or
                any(plan.get(k) != change.get(k) for k in ('program_id', 'customer_id'))):
            return None
        try:
            return cls(job_id=plan.get('job_id'), change_id=change.get('id'),
                       program_id=change.get('program_id'), customer_id=change.get('customer_id'),
                       plan_id=plan.get('id'))
        except ValueError:
            return None


class ToolCall(Model):
    name: str
    actor: Literal['agent', 'host', 'simulated_reviewer'] = 'agent'
    role: str | None = None
    method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'LOCAL'] = 'GET'
    outcome: Literal['succeeded', 'blocked', 'failed', 'unknown'] = 'succeeded'
    record_ids: list[str] = Field(default_factory=list)
    action_id: str | None = None
    read_receipt: ToolReadReceipt | None = None


class Assertion(Model):
    dimension: Dimension
    path: str
    op: Literal['eq', 'contains', 'not_contains', 'nonempty', 'absent'] = 'eq'
    value: Any = None
    description: str
    critical_code: str | None = None


class EvalCase(Model):
    schema_version: Literal[1] = 1
    case_id: str = Field(pattern=r'^[a-z0-9_]+$')
    title: str
    workflow_type: Workflow
    scenario_family: str
    input_facts: dict[str, Any]
    source_fixture: str
    expected_evidence: list[str]
    irrelevant_evidence: list[str]
    expected_applicability: dict[str, bool]
    expected_tools: list[str]
    prohibited_tools: list[str]
    prohibited_actions: list[str]
    expected_conclusions: dict[str, Any]
    forbidden_conclusions: list[str]
    escalation_expected: bool
    approval_required: bool
    downstream_state: dict[str, Any]
    grading_criteria: list[Assertion] = Field(min_length=1)
    severity: Literal['critical', 'high', 'medium']
    deterministic: Literal[True] = True
    live_fixture: Literal['gap', 'covered', 'wrong_software', 'bypass', 'scheduled', 'ambiguous'] | None = None
    smoke: bool = False
    runtime_probe: str | None = None

    @model_validator(mode='after')
    def boundaries(self):
        if (self.live_fixture or self.runtime_probe) and self.workflow_type != 'requirement_change_analysis':
            raise ValueError('Future workflows have only illustrative offline observations')
        if self.smoke and not self.live_fixture:
            raise ValueError('Smoke cases must be live eligible')
        if set(self.expected_evidence) & set(self.irrelevant_evidence):
            raise ValueError('Evidence cannot be both required and irrelevant')
        return self


class Observation(Model):
    case_id: str
    mode: Literal['mocked_observation', 'runtime_probe', 'live_agent']
    output: dict[str, Any]
    evidence: list[Evidence]
    tools: list[ToolCall]
    specialists: list[str]
    proposed_actions: list[str]
    # These are observer-owned records, never filled from model claims of authority.
    approval_recorded: bool = False
    proposal_current: bool = True
    execution_records: list[dict[str, Any]] = Field(default_factory=list)
    verification_records: list[dict[str, Any]] = Field(default_factory=list)
    blocked_operations: list[str] = Field(default_factory=list)
    raw_output: dict[str, Any] | None = None
    expected_validation_job: ValidationJobTarget | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Check(Model):
    dimension: Dimension
    description: str
    passed: bool
    critical_code: str | None = None


class SemanticScore(Model):
    dimension: Literal['uncertainty', 'unsupported_claims', 'escalation', 'proposal_quality', 'completeness']
    score: int = Field(ge=0, le=3)
    rationale: str = Field(min_length=1, max_length=800)
    observable_reference: str = Field(min_length=1, max_length=800)


class SemanticResult(Model):
    scores: list[SemanticScore] = Field(min_length=5, max_length=5)

    @model_validator(mode='after')
    def unique_dimensions(self):
        if len({s.dimension for s in self.scores}) != 5:
            raise ValueError('Each semantic dimension must be graded exactly once')
        return self


class CaseResult(Model):
    case_id: str
    title: str
    workflow_type: Workflow
    scenario_family: str
    mode: str
    severity: str
    checks: list[Check]
    passed: bool
    critical_failures: list[str]
    semantic: SemanticResult | None = None
    semantic_error: str | None = None
    error_code: str | None = None


class SourceFixture(Model):
    description: str
    records: dict[str, dict[str, Any]]
