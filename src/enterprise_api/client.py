"""Narrow business reads with caller-bound scope and unchanged JSON outputs."""

from copy import deepcopy
import json
from string import Formatter

from pydantic import TypeAdapter, ValidationError

from .config import ClientConfig, RecordID
from .endpoints import ENDPOINTS
from .errors import EnterpriseAPIError, ErrorInfo
from .models import JSONRecord
from .transport import HttpxReadTransport, ReadResponse, ReadTransport, RETRY_STATUSES

_ID = TypeAdapter(RecordID)
_ERROR_CODES = frozenset({"UNAUTHENTICATED", "FORBIDDEN_ROLE", "NOT_FOUND", "INVALID_REQUEST",
                          "RESOURCE_CONFLICT", "STALE_SOURCE", "STALE_MILESTONE", "INTERNAL_ERROR",
                          "DATABASE_BUSY", "RESOURCE_INELIGIBLE", "METHOD_NOT_ALLOWED"})


class EnterpriseClient:
    """Read-only client; instantiate one per explicit customer/program scope.

    A future MCP adapter can call the get_* methods with ordinary string inputs
    and return their JSON dictionaries. No API key, backend imports, local state
    reads, mutation methods, agent code, or MCP decorators are involved.
    """

    def __init__(self, config: ClientConfig, *, transport: ReadTransport | None = None):
        self._config = config
        self._transport = transport if transport is not None else HttpxReadTransport(config)
        self._owns_transport = transport is None
        self._scope_verified = False
        self._closed = False

    def __enter__(self):
        self._check_open()
        return self

    def __exit__(self, *args):
        self.close()

    def close(self) -> None:
        """Close owned HTTP resources; injected transports remain caller-owned."""
        if not self._closed and self._owns_transport:
            self._transport.close()
        self._closed = True

    def _check_open(self):
        if self._closed:
            raise EnterpriseAPIError(ErrorInfo("closed", "CLIENT_CLOSED"))

    def _inputs(self, values: dict) -> dict[str, str]:
        self._check_open()
        try:
            result = {name: _ID.validate_python(value) for name, value in values.items()}
        except ValidationError:
            raise EnterpriseAPIError(ErrorInfo("input", "INVALID_IDENTIFIER")) from None
        if "program_id" in result and result["program_id"] != self._config.scope.program_id:
            raise EnterpriseAPIError(ErrorInfo("scope", "SCOPE_MISMATCH"))
        return result

    def _verify_scope(self, value):
        if isinstance(value, dict):
            for name in ("program_id", "customer_id"):
                if name in value and value[name] is not None and value[name] != getattr(self._config.scope, name):
                    raise EnterpriseAPIError(ErrorInfo("scope", "SCOPE_MISMATCH"))
            for child in value.values():
                self._verify_scope(child)
        elif isinstance(value, list):
            for child in value:
                self._verify_scope(child)

    def _http_error(self, response: ReadResponse):
        status = response.status
        kind = {401: "unauthenticated", 403: "forbidden", 404: "not_found",
                409: "conflict", 422: "validation"}.get(status, "server" if 500 <= status < 600 else "http")
        candidate = response.body.get("error", {}) if isinstance(response.body, dict) else {}
        code = candidate.get("code") if isinstance(candidate, dict) else None
        if not isinstance(code, str) or code not in _ERROR_CODES:
            code = "HTTP_ERROR"
        raise EnterpriseAPIError(ErrorInfo(kind, code, status, status in RETRY_STATUSES,
                                           response.attempts, response.request_id, response.correlation_id))

    def _fetch(self, operation: str, inputs: dict[str, str]) -> JSONRecord:
        endpoint = ENDPOINTS[operation]
        path_fields = {name for _, name, _, _ in Formatter().parse(endpoint.path) if name}
        path = "/api/v1" + endpoint.path.format(**inputs)
        response = self._transport.get(path, {k: v for k, v in inputs.items() if k not in path_fields})
        if response.status != 200:
            self._http_error(response)
        body = response.body
        try:
            endpoint.response.model_validate(body)
            json.dumps(body, allow_nan=False)
        except (ValidationError, TypeError, ValueError, RecursionError):
            raise EnterpriseAPIError(ErrorInfo("invalid_response", "INVALID_RESPONSE", response.status,
                                               attempts=response.attempts, request_id=response.request_id,
                                               correlation_id=response.correlation_id)) from None
        self._verify_scope(body)
        if endpoint.resource_parameter and body["id"] != inputs[endpoint.resource_parameter]:
            raise EnterpriseAPIError(ErrorInfo("invalid_response", "UNEXPECTED_RESOURCE"))
        if "change_id" in inputs:
            if "change_id" in body and body["change_id"] != inputs["change_id"]:
                raise EnterpriseAPIError(ErrorInfo("scope", "CHANGE_SCOPE_MISMATCH"))
            for item in body.get("items", []):
                if "change_id" in item and item["change_id"] != inputs["change_id"]:
                    raise EnterpriseAPIError(ErrorInfo("scope", "CHANGE_SCOPE_MISMATCH"))
        if "delivery_id" in inputs and body.get("delivery_id") != inputs["delivery_id"]:
            raise EnterpriseAPIError(ErrorInfo("scope", "DELIVERY_SCOPE_MISMATCH"))
        if "exception_id" in inputs and body.get("exception_id") != inputs["exception_id"]:
            raise EnterpriseAPIError(ErrorInfo("scope", "EXCEPTION_SCOPE_MISMATCH"))
        return deepcopy(body)

    def _read(self, operation: str, **values) -> JSONRecord:
        inputs = self._inputs(values)
        if not self._scope_verified:
            # Validate customer/program pairing even when a later record carries
            # program_id only. The server remains the authority on membership.
            self.get_program(self._config.scope.program_id)
        if operation in {"get_validation_coverage", "get_validation_options", "get_validation_jobs", "get_implementation_links"}:
            # Aggregates may be empty and lack scope fields. Verify the change
            # before asking for them, including under the portfolio reader.
            self.get_change_request(inputs["change_id"])
        return self._fetch(operation, inputs)

    def get_change_requests(self, program_id: str) -> JSONRecord:
        """List existing change requests for the bound program; no client filtering or ranking."""
        return self._read("get_change_requests", program_id=program_id)

    def get_change_request(self, change_id: str) -> JSONRecord:
        """Get a change, exact baseline/proposed revision references, and existing plans."""
        return self._read("get_change_request", change_id=change_id)

    def get_requirement_revision(self, requirement_revision_id: str) -> JSONRecord:
        """Get the exact named requirement revision and its requested/approved status."""
        return self._read("get_requirement_revision", requirement_revision_id=requirement_revision_id)

    def get_configuration(self, configuration_id: str) -> JSONRecord:
        """Get authoritative hardware, firmware, runtime and model applicability."""
        return self._read("get_configuration", configuration_id=configuration_id)

    def get_workload_profile(self, workload_profile_id: str) -> JSONRecord:
        """Get the exact workload manifest, bins, concurrency and required duration."""
        return self._read("get_workload_profile", workload_profile_id=workload_profile_id)

    def get_procedure(self, procedure_id: str) -> JSONRecord:
        """Get procedure eligibility, timing inputs, criteria reference and document ID."""
        return self._read("get_procedure", procedure_id=procedure_id)

    def get_policy(self, policy_id: str) -> JSONRecord:
        """Read delegated approval limits and permitted actions; grants no approval authority."""
        return self._read("get_policy", policy_id=policy_id)

    def get_acceptance_criteria(self, criteria_id: str) -> JSONRecord:
        """Get existing acceptance-criteria context without changing or inventing thresholds."""
        return self._read("get_acceptance_criteria", criteria_id=criteria_id)

    def get_documents(self, program_id: str) -> JSONRecord:
        """List server-allowlisted business-document metadata for the bound program."""
        return self._read("get_documents", program_id=program_id)

    def get_document(self, document_id: str) -> JSONRecord:
        """Get one allowlisted business document by ID, including its content and provenance."""
        return self._read("get_document", document_id=document_id)

    def get_plan(self, plan_id: str) -> JSONRecord:
        """Get an existing immutable plan, digest, source snapshot and execution context."""
        return self._read("get_plan", plan_id=plan_id)

    def get_plan_decision(self, decision_id: str) -> JSONRecord:
        """Read an existing recorded decision and its exact plan binding; never approve."""
        return self._read("get_plan_decision", decision_id=decision_id)

    def get_change_plans(self, change_id: str) -> JSONRecord:
        """Project unchanged existing plans from the authoritative change response."""
        change = self.get_change_request(change_id)
        return {"change_id": change["id"], "program_id": change["program_id"],
                "record_version": change["record_version"], "items": change["plans"]}

    def get_validation_coverage(self, change_id: str) -> JSONRecord:
        """Get server-calculated coverage and all evidence/mismatch records; no local conclusions."""
        return self._read("get_validation_coverage", change_id=change_id)

    def get_validation_options(self, change_id: str) -> JSONRecord:
        """Get every server-calculated option with timing, costs, eligibility and source versions."""
        return self._read("get_validation_options", change_id=change_id)

    def get_validation_result(self, result_id: str) -> JSONRecord:
        """Read recorded validation evidence and historical applicability snapshots."""
        return self._read("get_validation_result", result_id=result_id)

    def get_validation_samples(self, program_id: str) -> JSONRecord:
        """List samples, physical-unit references and current availability for the bound program."""
        return self._read("get_validation_samples", program_id=program_id)

    def get_validation_jobs(self, change_id: str) -> JSONRecord:
        """List existing jobs and their embedded reservations; scheduled is not tested."""
        return self._read("get_validation_jobs", change_id=change_id)

    def get_validation_job(self, job_id: str) -> JSONRecord:
        """Get an existing scheduled job and its exact resource reservation."""
        return self._read("get_validation_job", job_id=job_id)

    def get_validation_reservation(self, job_id: str) -> JSONRecord:
        """Project the unchanged reservation embedded in GET /validation/jobs/{job_id}."""
        job = self.get_validation_job(job_id)
        reservation = job["reservation"]
        if reservation["id"] != job["reservation_id"] or reservation["job_id"] != job["id"]:
            raise EnterpriseAPIError(ErrorInfo("invalid_response", "UNEXPECTED_RESOURCE"))
        return reservation

    def get_historical_validation_job(self, job_id: str) -> JSONRecord:
        """Get imported lab-execution provenance and independent result IDs, separate from booking."""
        return self._read("get_historical_validation_job", job_id=job_id)

    def get_manufacturing_units(self, program_id: str) -> JSONRecord:
        """List physical units and their recorded restrictions within the bound program."""
        return self._read("get_manufacturing_units", program_id=program_id)

    def get_manufacturing_lots(self, program_id: str) -> JSONRecord:
        """List manufacturing source lots and their recorded restrictions within the bound program."""
        return self._read("get_manufacturing_lots", program_id=program_id)

    def get_manufacturing_unit(self, unit_id: str) -> JSONRecord:
        """Get physical-unit provenance, source lot, restrictions and hold details."""
        return self._read("get_manufacturing_unit", unit_id=unit_id)

    def get_manufacturing_lot(self, lot_id: str) -> JSONRecord:
        """Get a source lot with its authoritative restrictions and hold provenance."""
        return self._read("get_manufacturing_lot", lot_id=lot_id)

    def get_manufacturing_provenance(self, unit_id: str) -> JSONRecord:
        """Read the unit and its referenced lot separately; retain both restriction sets unchanged."""
        unit = self.get_manufacturing_unit(unit_id)
        return {"unit": unit, "lot": self.get_manufacturing_lot(unit["source_lot_id"])}

    def get_customer_orders(self, program_id: str) -> JSONRecord:
        """List authoritative customer orders and commitments for the bound program."""
        return self._read("get_customer_orders", program_id=program_id)

    def get_customer_order(self, order_id: str) -> JSONRecord:
        """Read customer quantity and committed delivery without altering commitments."""
        return self._read("get_customer_order", order_id=order_id)

    def get_cost_rates(self, program_id: str) -> JSONRecord:
        """Get rates approved and effective at the server scenario time; preserve integer USD cents."""
        return self._read("get_cost_rates", program_id=program_id)

    def get_programs(self, program_id: str) -> JSONRecord:
        """Read the program directory narrowed to the bound program, including scenario metadata."""
        return self._read("get_programs", program_id=program_id)

    def get_program(self, program_id: str) -> JSONRecord:
        """Get the program and verify its customer association against this client's immutable scope."""
        inputs = self._inputs({"program_id": program_id})
        result = self._fetch("get_program", inputs)
        self._scope_verified = True
        return result

    def get_program_milestone(self, program_id: str, milestone_id: str) -> JSONRecord:
        """Get a milestone with baseline, forecast, record version and dependencies kept distinct."""
        return self._read("get_program_milestone", program_id=program_id, milestone_id=milestone_id)

    def get_dependencies(self, program_id: str, milestone_id: str) -> JSONRecord:
        """Project the milestone's unchanged dependencies with its ID and record version."""
        milestone = self.get_program_milestone(program_id, milestone_id)
        return {"program_id": milestone["program_id"], "milestone_id": milestone["id"],
                "record_version": milestone["record_version"], "dependencies": milestone["dependencies"]}

    def get_implementation_links(self, program_id: str, change_id: str) -> JSONRecord:
        """Read existing Planner implementation links with their embedded tasks for this change."""
        return self._read("get_implementation_links", program_id=program_id, change_id=change_id)

    def get_delivery_context(self, delivery_id: str) -> JSONRecord:
        """Read scoped ERP demand and source-owned technical/material/logistics context."""
        return self._read("get_delivery_context", delivery_id=delivery_id)

    def get_delivery_records(self, delivery_id: str) -> JSONRecord:
        """Read exact ERP proposal, decision, commitment and Planner link receipts."""
        return self._read("get_delivery_records", delivery_id=delivery_id)

    def get_quality_context(self, exception_id: str) -> JSONRecord:
        """Read source-owned signal, material, procedure, evidence and milestone demand plus deterministic calculations."""
        return self._read("get_quality_context", exception_id=exception_id)

    def get_quality_records(self, exception_id: str) -> JSONRecord:
        """Independently read source investigation, recovery proposal, human decision and Planner task."""
        return self._read("get_quality_records", exception_id=exception_id)

    def get_standard_change_context(self, change_id: str) -> JSONRecord:
        """Read exact standard request/procedure/configuration/evidence/owner context."""
        return self._read("get_standard_change_context", change_id=change_id)

    def get_standard_validation_intakes(self, change_id: str) -> JSONRecord:
        """Read immutable Validation Operations intakes for one scoped change."""
        return self._read("get_standard_validation_intakes", change_id=change_id)

    def get_standard_validation_intake(self, intake_id: str) -> JSONRecord:
        """Independently read one received standard package and its downstream status."""
        return self._read("get_standard_validation_intake", intake_id=intake_id)

    def get_standard_change_requests(self, program_id: str) -> JSONRecord:
        """Discover explicitly installed standard requests in the fixed program scope."""
        return self._read("get_standard_change_requests", program_id=program_id)
