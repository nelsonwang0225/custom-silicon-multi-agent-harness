"""Explicit GET allowlist verified against docs/openapi.json and running HTTP schema.

This is a client implementation detail, not an arbitrary-query public interface.
"""

from dataclasses import dataclass

from . import models as m
from .delivery_models import DeliveryContext, DeliveryRecords
from .quality_models import QualityContext, QualityRecords
from .standard_models import StandardContext, IntakeList, ValidationIntake, StandardRequest


@dataclass(frozen=True)
class Endpoint:
    path: str
    response: type[m.ReadModel]
    resource_parameter: str | None = None


ENDPOINTS = {
    "get_delivery_context": Endpoint("/erp/delivery-requests/{delivery_id}/context", DeliveryContext),
    "get_delivery_records": Endpoint("/erp/delivery-requests/{delivery_id}/records", DeliveryRecords),
    "get_quality_context": Endpoint("/manufacturing/quality-exceptions/{exception_id}/context", QualityContext),
    "get_quality_records": Endpoint("/manufacturing/quality-exceptions/{exception_id}/records", QualityRecords),
    "get_standard_change_requests": Endpoint("/engineering/standard-changes", m.Items[StandardRequest]),
    "get_standard_change_context": Endpoint("/engineering/changes/{change_id}/standard-context", StandardContext),
    "get_standard_validation_intakes": Endpoint("/validation/changes/{change_id}/intakes", IntakeList),
    "get_standard_validation_intake": Endpoint("/validation/intakes/{intake_id}", ValidationIntake, "intake_id"),
    "get_change_requests": Endpoint("/engineering/changes", m.Items[m.ChangeRequest]),
    "get_change_request": Endpoint("/engineering/changes/{change_id}", m.ChangeRequestView, "change_id"),
    "get_requirement_revision": Endpoint("/engineering/requirements/{requirement_revision_id}", m.RequirementRevision, "requirement_revision_id"),
    "get_configuration": Endpoint("/engineering/configurations/{configuration_id}", m.Configuration, "configuration_id"),
    "get_workload_profile": Endpoint("/engineering/workloads/{workload_profile_id}", m.WorkloadProfile, "workload_profile_id"),
    "get_procedure": Endpoint("/engineering/procedures/{procedure_id}", m.Procedure, "procedure_id"),
    "get_policy": Endpoint("/engineering/policies/{policy_id}", m.Policy, "policy_id"),
    "get_acceptance_criteria": Endpoint("/engineering/acceptance-criteria/{criteria_id}", m.AcceptanceCriteria, "criteria_id"),
    "get_documents": Endpoint("/engineering/documents", m.Items[m.DocumentMetadata]),
    "get_document": Endpoint("/engineering/documents/{document_id}", m.Document, "document_id"),
    "get_plan": Endpoint("/engineering/plans/{plan_id}", m.Plan, "plan_id"),
    "get_plan_decision": Endpoint("/engineering/decisions/{decision_id}", m.Decision, "decision_id"),
    "get_validation_coverage": Endpoint("/validation/coverage", m.Coverage),
    "get_validation_options": Endpoint("/validation/options", m.ValidationOptions),
    "get_validation_result": Endpoint("/validation/results/{result_id}", m.ValidationResult, "result_id"),
    "get_validation_samples": Endpoint("/validation/samples", m.Items[m.Sample]),
    "get_validation_jobs": Endpoint("/validation/jobs", m.Items[m.ValidationJob]),
    "get_validation_job": Endpoint("/validation/jobs/{job_id}", m.ValidationJob, "job_id"),
    "get_historical_validation_job": Endpoint("/validation/history/{job_id}", m.HistoricalValidationJob, "job_id"),
    "get_manufacturing_units": Endpoint("/manufacturing/units", m.Items[m.ManufacturingUnit]),
    "get_manufacturing_lots": Endpoint("/manufacturing/lots", m.Items[m.ManufacturingLot]),
    "get_manufacturing_unit": Endpoint("/manufacturing/units/{unit_id}", m.ManufacturingUnit, "unit_id"),
    "get_manufacturing_lot": Endpoint("/manufacturing/lots/{lot_id}", m.ManufacturingLot, "lot_id"),
    "get_customer_orders": Endpoint("/erp/orders", m.Items[m.CustomerOrder]),
    "get_customer_order": Endpoint("/erp/orders/{order_id}", m.CustomerOrder, "order_id"),
    "get_cost_rates": Endpoint("/erp/cost-rates", m.Items[m.CostRate]),
    "get_programs": Endpoint("/programs", m.Items[m.Program]),
    "get_program": Endpoint("/programs/{program_id}", m.Program, "program_id"),
    "get_program_milestone": Endpoint("/programs/{program_id}/milestones/{milestone_id}", m.Milestone, "milestone_id"),
    "get_implementation_links": Endpoint("/programs/{program_id}/implementation-links", m.Items[m.ImplementationLink]),
}
