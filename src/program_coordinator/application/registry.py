"""Discoverable capability descriptions. Never an authorization source."""

from typing import Literal
from pydantic import ConfigDict
from ..models import ID, Model, Role


class WorkflowDefinition(Model):
    model_config = ConfigDict(frozen=True)
    workflow_id: ID
    definition_version: int = 1
    display_name: str
    description: str
    implementation_status: Literal["analysis_implemented", "illustrative"]
    supported_operations: tuple[str, ...]
    participating_specialists: tuple[Role, ...]
    tool_policy_reference: str | None
    approval_policy_reference: str | None
    execution_mode: Literal["live_read_only_analysis", "not_executable"]
    planned_capabilities: tuple[str, ...]
    connected_host_routes: tuple[str, ...] = ()
    business_execution_available: Literal[False] = False


_DEFINITIONS = (
    WorkflowDefinition(workflow_id="requirement_change_analysis", display_name="Requirement-change analysis",
        description="Existing Coordinator investigation of requirement changes, evidence, options and program impact.",
        implementation_status="analysis_implemented", supported_operations=("analyze",),
        participating_specialists=("change_impact", "validation_evidence", "program_commercial", "manufacturing"),
        tool_policy_reference="program_coordinator.controls.TOOL_MATRIX",
        approval_policy_reference="Source-selected engineering policy; program_coordinator.policy determines analysis path only",
        execution_mode="live_read_only_analysis", connected_host_routes=("material_change_human_review", "standard_touchless_handoff"), planned_capabilities=("human_review_of_exact_plan", "approved_scheduling_and_planner_link")),
    WorkflowDefinition(workflow_id="yield_exception_recovery", display_name="Yield/quality exception recovery",
        description="Validate a Manufacturing quality exception, quantify eligible supply and prepare governed recovery.",
        implementation_status="analysis_implemented", supported_operations=("analyze",),
        participating_specialists=("manufacturing", "validation_evidence", "program_commercial"),
        tool_policy_reference="program_coordinator.mcp.ScopedMCP quality route", approval_policy_reference="Engineering quality procedure; exact Program Owner recovery decision",
        execution_mode="live_read_only_analysis", connected_host_routes=("quality_recovery",),
        planned_capabilities=("exception_impact_analysis", "recovery_proposals")),
    WorkflowDefinition(workflow_id="delivery_readiness", display_name="Delivery readiness",
        description="Assess exact customer demand, technical readiness and supply; prepare a governed commitment.",
        implementation_status="analysis_implemented", supported_operations=("analyze",), participating_specialists=("manufacturing", "validation_evidence", "program_commercial"),
        tool_policy_reference="program_coordinator.mcp.ScopedMCP delivery route", approval_policy_reference="Exact Program Owner commercial commitment", execution_mode="live_read_only_analysis", connected_host_routes=("delivery_commitment",),
        planned_capabilities=("readiness_analysis", "commitment_planning")),
)


def list_workflows():
    return _DEFINITIONS


def dispatch_error(workflow_id, definition_version=1, operation="analyze"):
    definition = next((d for d in _DEFINITIONS if d.workflow_id == workflow_id), None)
    if definition is None:
        return "UNKNOWN_WORKFLOW"
    if definition.definition_version != definition_version:
        return "UNSUPPORTED_WORKFLOW_VERSION"
    if definition.implementation_status == "illustrative":
        return "WORKFLOW_NOT_IMPLEMENTED"
    if operation not in definition.supported_operations:
        return "OPERATION_NOT_IMPLEMENTED"
    # Catalog metadata never installs executors or grants tool permissions.
    if workflow_id not in {"requirement_change_analysis", "yield_exception_recovery", "delivery_readiness"} or operation != "analyze":
        return "WORKFLOW_NOT_IMPLEMENTED"
    return None
