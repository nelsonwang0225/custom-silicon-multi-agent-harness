"""Explicit business allowlist, organized by domain; no reflective auto-exposure."""

from dataclasses import dataclass
from typing import Callable

from mcp.types import Tool, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, JsonValue, create_model

from enterprise_api import EnterpriseClient
from enterprise_api.config import RecordID
from enterprise_api.errors import ErrorInfo


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


def _inputs(name: str, **fields: str) -> type[Arguments]:
    return create_model(name, __base__=Arguments,
                        **{key: (RecordID, Field(description=description)) for key, description in fields.items()})


DeliveryRequest = _inputs("DeliveryRequest", delivery_id="Existing ERP delivery release request in this program.")
QualityException = _inputs("QualityException", exception_id="Existing Manufacturing quality exception in this program.")
Change = _inputs("Change", change_id="Existing change request ID within the configured program.")
Requirement = _inputs("Requirement", requirement_revision_id="Exact baseline or proposed revision ID from a change.")
Configuration = _inputs("Configuration", configuration_id="Configuration ID referenced by an engineering record.")
Workload = _inputs("Workload", workload_profile_id="Exact workload profile ID from a requirement revision.")
Procedure = _inputs("Procedure", procedure_id="Procedure ID from validation options or engineering context.")
Policy = _inputs("Policy", policy_id="Policy ID from validation options or an existing plan.")
Criteria = _inputs("Criteria", criteria_id="Acceptance criteria ID from acceptance_limits_ref.")
Document = _inputs("Document", document_id="Allowlisted business-document ID from a source record; never a file path.")
Plan = _inputs("Plan", plan_id="Existing plan ID from a change; this tool does not create a plan.")
Decision = _inputs("Decision", decision_id="Existing decision ID from a plan; this tool does not approve it.")
Result = _inputs("Result", result_id="Recorded validation result ID from coverage evidence.")
Program = _inputs("Program", program_id="Program ID; must equal this server's configured program scope.")
Job = _inputs("Job", job_id="Existing scheduled validation job ID from the jobs list.")
Unit = _inputs("Unit", unit_id="Physical unit ID from a validation sample or option.")
Lot = _inputs("Lot", lot_id="Manufacturing source_lot_id from a physical unit.")
Order = _inputs("Order", order_id="Customer order ID referenced by the change or program.")
Milestone = _inputs("Milestone", program_id="The configured program ID.", milestone_id="Milestone ID from the change or program.")
Links = _inputs("Links", program_id="The configured program ID.", change_id="Existing change request ID in that program.")


class ToolPayload(BaseModel):
    """Data is unchanged enterprise-client JSON; errors never include server prose."""
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    ok: bool
    data: dict[str, JsonValue] | None
    error: ErrorInfo | None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    domain: str
    method: Callable
    inputs: type[Arguments]
    description: str

    def definition(self) -> Tool:
        return Tool(name=self.name, description=f"{self.domain}: {self.description}",
                    input_schema=self.inputs.model_json_schema(), output_schema=ToolPayload.model_json_schema(),
                    annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False,
                                                idempotent_hint=True, open_world_hint=False))


# Only these bound references can execute. Tool names never become getattr or URLs.
TOOLS = (
    ToolSpec("get_delivery_context", "Delivery readiness source context", EnterpriseClient.get_delivery_context, DeliveryRequest,
             "Read exact ERP request/allocation/commitment, shared Manufacturing material, Engineering clearance, Validation evidence and Planner logistics. Includes deterministic readiness, quantity and date calculations. No write authority."),
    ToolSpec("get_quality_context", "Quality recovery source context", EnterpriseClient.get_quality_context, QualityException,
             "Read the scoped Manufacturing exception and material, Engineering procedure, historical Validation evidence, Planner milestone and ERP demand. Includes deterministic comparability and eligible-supply calculations. Correlation is not root cause; no write or release authority."),
    ToolSpec("get_standard_change_context", "Engineering / Validation / Planner", EnterpriseClient.get_standard_change_context, Change,
             "Read the explicit standard request, approved procedure/configuration, historical evidence, remaining work and Validation Operations owner. No writes or lab authority."),
    ToolSpec("get_change_request", "Engineering Hub", EnterpriseClient.get_change_request, Change,
             "Read a change, baseline/proposed requirement references and existing plans. Start here to follow authoritative context."),
    ToolSpec("get_requirement_revision", "Engineering Hub", EnterpriseClient.get_requirement_revision, Requirement,
             "Read the exact requirement revision, workload, configuration and acceptance references."),
    ToolSpec("get_configuration", "Engineering Hub", EnterpriseClient.get_configuration, Configuration,
             "Read hardware, firmware, runtime and model applicability for a configuration."),
    ToolSpec("get_workload_profile", "Engineering Hub", EnterpriseClient.get_workload_profile, Workload,
             "Read a workload manifest, bins, concurrency and required duration."),
    ToolSpec("get_procedure", "Engineering Hub", EnterpriseClient.get_procedure, Procedure,
             "Read procedure eligibility, timing inputs and its business-document reference."),
    ToolSpec("get_policy", "Engineering Hub", EnterpriseClient.get_policy, Policy,
             "Read existing approval limits and permitted actions as context; confers no authority."),
    ToolSpec("get_acceptance_criteria", "Engineering Hub", EnterpriseClient.get_acceptance_criteria, Criteria,
             "Read existing acceptance criteria and applicability without changing thresholds."),
    ToolSpec("get_document", "Engineering Hub", EnterpriseClient.get_document, Document,
             "Read one allowlisted business document and its provenance by record ID."),
    ToolSpec("get_documents", "Engineering Hub", EnterpriseClient.get_documents, Program,
             "List allowlisted business-document IDs and metadata for the configured program, including supplemental context."),
    ToolSpec("get_plan", "Engineering Hub", EnterpriseClient.get_plan, Plan,
             "Read an existing immutable plan, source versions and execution context."),
    ToolSpec("get_decision", "Engineering Hub", EnterpriseClient.get_plan_decision, Decision,
             "Read an existing recorded decision and its exact plan/version binding."),
    ToolSpec("get_validation_coverage", "Validation Lab", EnterpriseClient.get_validation_coverage, Change,
             "Read server-calculated evidence coverage, including every evidence item and mismatch reason."),
    ToolSpec("get_validation_options", "Validation Lab", EnterpriseClient.get_validation_options, Change,
             "Read all server-calculated options with timing, integer-cent costs and constraints. No option is selected or ranked here."),
    ToolSpec("get_validation_result", "Validation Lab", EnterpriseClient.get_validation_result, Result,
             "Read recorded test evidence and its historical applicability snapshot."),
    ToolSpec("get_validation_samples", "Validation Lab", EnterpriseClient.get_validation_samples, Program,
             "Read sample availability and physical-unit references within the configured program."),
    ToolSpec("get_validation_jobs", "Validation Lab", EnterpriseClient.get_validation_jobs, Change,
             "Read existing jobs and reservations for a change. Scheduling does not establish test completion."),
    ToolSpec("get_validation_job", "Validation Lab", EnterpriseClient.get_validation_job, Job,
             "Read one existing scheduled job and its embedded resource reservation."),
    ToolSpec("get_manufacturing_unit", "Manufacturing Portal", EnterpriseClient.get_manufacturing_unit, Unit,
             "Read a physical unit, source lot, restrictions and hold provenance."),
    ToolSpec("get_manufacturing_lot", "Manufacturing Portal", EnterpriseClient.get_manufacturing_lot, Lot,
             "Read source-lot restrictions and hold provenance separately from unit restrictions."),
    ToolSpec("get_customer_order", "Commercial ERP", EnterpriseClient.get_customer_order, Order,
             "Read the authoritative customer quantity and committed delivery date."),
    ToolSpec("get_cost_rates", "Commercial ERP", EnterpriseClient.get_cost_rates, Program,
             "Read approved rates effective at server scenario time; USD amounts remain integer cents."),
    ToolSpec("get_program", "Program Planner", EnterpriseClient.get_program, Program,
             "Read program context and verify its configured customer/program association."),
    ToolSpec("get_program_milestone", "Program Planner", EnterpriseClient.get_program_milestone, Milestone,
             "Read milestone baseline, forecast, record version and dependencies."),
    ToolSpec("get_dependencies", "Program Planner", EnterpriseClient.get_dependencies, Milestone,
             "Read the milestone's unchanged dependency records with its ID and record version."),
    ToolSpec("get_implementation_links", "Program Planner", EnterpriseClient.get_implementation_links, Links,
             "Read existing implementation links and embedded tasks for the scoped change."),
)
CATALOG = {tool.name: tool for tool in TOOLS}
