"""Duplicate-trigger probe of the existing invocation service, using its test seam."""
import asyncio
from program_coordinator.application.service import WorkflowService
from program_coordinator.application.store import ActivityStore
from program_coordinator.application.models import WorkflowInvocation
from program_coordinator.application.demo_identity import READER
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import CaseState, ProgramChangeEvent, FinalDecisionPackage
from .dataset import ROOT


def source_failure_probe(kind):
    """Exercise existing ScopedMCP validation/timeout with a transport double."""
    from unittest.mock import AsyncMock, patch
    from agents.mcp import MCPServerStreamableHttp
    from mcp.types import CallToolResult
    from program_coordinator.harness import CaseHarness
    from program_coordinator.mcp import ScopedMCP
    from program_coordinator.controls import HarnessError
    from program_investigator.telemetry import Recorder
    event = ProgramChangeEvent.model_validate_json((ROOT / 'coordinator/scenarios/human_review.json').read_text())
    h = CaseHarness(HarnessConfig(tool_timeout_seconds=.001), event, None, Recorder('trace_' + '0' * 32))
    server = ScopedMCP(h, 'validation_evidence', 'phase07_source_failure')
    if kind == 'missing_system':
        transport = AsyncMock(side_effect=ConnectionError('Synthetic unavailable source'))
    elif kind == 'source_timeout':
        async def delayed(*args, **kwargs):
            await asyncio.sleep(.1)
        transport = delayed
    elif kind == 'malformed_tool':
        transport = AsyncMock(return_value=CallToolResult(content=[], structured_content={'data': 'not a valid envelope'}))
    else:
        raise ValueError('Unknown source failure probe')
    error = None
    with patch.object(MCPServerStreamableHttp, 'call_tool', transport):
        try:
            asyncio.run(server.call_tool('get_validation_coverage', {'change_id': 'CR-017'}))
        except HarnessError as exc:
            error = str(exc)
    return {'output': {'evidence_incomplete': error is not None and not h.sources.calls,
        'verified_completion': False, 'escalation_required': error is not None},
        'tools': [{'name': 'get_validation_coverage', 'role': 'validation_evidence', 'outcome': 'failed' if error else 'succeeded'}],
        'blocked_operations': [error] if error else [],
        'metadata': {'probe': kind, 'notice': 'Existing ScopedMCP with an offline transport double; no model/source network calls.'}}


def duplicate_probe(directory):
    count = 0
    async def investigation(request, run):
        nonlocal count
        count += 1
        output = FinalDecisionPackage(case_id=run.case_id, customer_id=run.customer_id, program_id=run.program_id,
            classified_change_type='workload_profile_change', change_summary='Deterministic invocation probe.',
            affected_scope=[], specialist_findings=[], confirmed_facts=[], evidence_gaps=[], available_options=[],
            relevant_constraints=[], program_impact=[], risks=[], unresolved_questions=[], recommended_next_step='Request review.',
            policy_path='human_review_required', requires_human_review=True, escalation_reason=None, source_references=[],
            business_actions_executed=False, approval_granted=False, customer_accepted=False, new_validation_pass_claimed=False)
        return CaseState(case_id=run.case_id, run_id=run.run_id, workflow_id=run.workflow_id,
            workflow_definition_version=run.definition_version, customer_id=run.customer_id, program_id=run.program_id,
            correlation_id=request.event.correlation_id, event=request.event, workflow_stage='completed',
            scope_verified=True, final_package_status='validated', final_package=output)
    store = ActivityStore(directory)
    event = ProgramChangeEvent.model_validate_json((ROOT / 'coordinator/scenarios/human_review.json').read_text())
    request = WorkflowInvocation(invocation_id='phase07_duplicate', event=event,
        customer_id=event.customer_id, program_id=event.program_id)
    def service():
        return WorkflowService(ActivityStore(directory), config=HarnessConfig(), investigate=investigation,
            actors=[READER], execution_mode='deterministic_test')
    first = asyncio.run(service().invoke(request, READER))
    second = asyncio.run(service().invoke(request, READER))
    with store.transaction() as data:
        run_count = len(data.runs)
        action_count = len(data.execution_attempts)
    return {'output': {'investigation_count': count, 'run_count': run_count,
        'replayed': second.replayed and first.run.run_id == second.run.run_id,
        'duplicate_business_actions': action_count}, 'tools': [],
        'metadata': {'probe': 'WorkflowService duplicate invocation across service instances', 'model_calls': 0}}
