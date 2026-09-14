"""Application-owned evidence receipts and fail-closed output verification."""

import hashlib
import json
import re

from pydantic import ValidationError
from program_investigator.validation import records
from .controls import HarnessError
from .models import (ChangeImpactAssessment, ValidationEvidenceAssessment, ProgramCommercialAssessment,
                     ManufacturingAssessment, FinalDecisionPackage, SourceReference, ValidationClarificationResult, StandardValidationAssessment)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def pointer(value, path):
    if path == "":
        return value
    if not path.startswith("/"):
        raise HarnessError("invalid_source_pointer")
    try:
        for key in path[1:].split("/"):
            key = key.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
        return value
    except (KeyError, IndexError, TypeError, ValueError):
        raise HarnessError("invalid_source_pointer") from None


def assert_scope(data, customer_id, program_id):
    for record in records(data):
        for key, expected in (("customer_id", customer_id), ("program_id", program_id)):
            if key in record and record[key] is not None and record[key] != expected:
                raise HarnessError("source_scope_mismatch")
        if "owning_system" in record:
            if (record.get("synthetic") is not True or not isinstance(record.get("id"), str)
                    or type(record.get("content_version")) is not int or record["content_version"] < 1):
                raise HarnessError("malformed_source_record")


def record_contexts(value, path="", historical=False):
    """Keep explicit API snapshot provenance separate from current record state.

    Immutable Plans/Decisions contain source_snapshot; a Plan's coverage is its
    frozen evidence set. Results and lab completions embed historical snapshots. Scope
    checks and exact JSON-pointer citations still traverse the entire payload.
    Missing version fields alone never mark a record as historical.
    """
    if isinstance(value, dict):
        yield path, value, historical
        plan = value.get("owning_system") == "engineering" and "plan_digest" in value and "plan_version" in value
        result = value.get("owning_system") == "validation" and "criteria_passed" in value
        completion = (value.get("owning_system") == "validation" and "result_digest" in value
                      and "job_id" in value and "completed_at" in value)
        for key, child in value.items():
            snapshot = (plan and key in {"source_snapshot", "coverage"}) or (
                result and key in {"configuration_snapshot", "workload_snapshot", "criteria_snapshot"}) or (
                completion and key == "source_snapshot")
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from record_contexts(child, path + "/" + escaped, historical or snapshot)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from record_contexts(child, path + "/" + str(index), historical)


class SourceRegistry:
    def __init__(self, state):
        self.state = state
        self.calls: list[dict] = []
        self.known_ids = {i for i in (state.event.change_id, state.program_id, state.customer_id) if i}
        self.ids_by_parameter = {"change_id": {state.event.change_id} - {None},
                                 "program_id": {state.program_id} - {None},
                                 "customer_id": {state.customer_id} - {None}}
        if state.workflow_id == "yield_exception_recovery":
            self.ids_by_parameter["exception_id"] = {state.event.change_id} - {None}
        if state.workflow_id == "delivery_readiness":
            self.ids_by_parameter["delivery_id"] = {state.event.change_id} - {None}
        self.observed_versions: dict[tuple, str] = {}

    def learn_ids(self, data):
        aliases = {"baseline_requirement_revision_id": "requirement_revision_id",
                   "proposed_requirement_revision_id": "requirement_revision_id",
                   "target_requirement_revision_id": "requirement_revision_id",
                   "acceptance_limits_ref": "criteria_id", "source_lot_id": "lot_id",
                   "request_document_id": "document_id", "policy_document_id": "document_id",
                   "current_plan_id": "plan_id", "approval_id": "decision_id"}
        for record in records(data):
            for key, value in record.items():
                values = value if key.endswith("_ids") and isinstance(value, list) else [value]
                if key == "id" or key.endswith("_id") or key.endswith("_ids") or key == "acceptance_limits_ref":
                    safe = {v for v in values if isinstance(v, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,100}", v)}
                    self.known_ids.update(safe)
                    parameter = aliases.get(key, key[:-1] if key.endswith("_ids") else key)
                    self.ids_by_parameter.setdefault(parameter, set()).update(safe)
            if "resource_type" in record and isinstance(record.get("resource_id"), str):
                names = {"configuration": "configuration_id", "workload": "workload_profile_id", "requirement": "requirement_revision_id",
                         "procedure": "procedure_id", "criteria": "criteria_id", "policy": "policy_id", "document": "document_id",
                         "sample": "sample_id", "unit": "unit_id", "lot": "lot_id", "order": "order_id", "milestone": "milestone_id"}
                parameter = names.get(record["resource_type"].split(".")[-1])
                if parameter:
                    self.ids_by_parameter.setdefault(parameter, set()).add(record["resource_id"])
        for item in data.get("evidence", []):
            if isinstance(item, dict) and item.get("owning_system") == "validation" and "criteria_passed" in item:
                self.ids_by_parameter.setdefault("result_id", set()).add(item["id"])
        for item in data.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("result"), dict):
                self.ids_by_parameter.setdefault("result_id", set()).add(item["result"]["id"])

    def add(self, tool, args, data, role, invocation_id, receipt, latency_ms):
        assert_scope(data, self.state.customer_id, self.state.program_id)
        # Conflicting responses under the same version or changes mid-case remain explicit.
        versions = dict(self.observed_versions)
        provenance = []
        for path, record, historical in record_contexts(data):
            if "owning_system" not in record:
                continue
            provenance.append({"pointer": path, "record_id": record["id"],
                "owning_system": record["owning_system"],
                "kind": "historical_snapshot" if historical else "current"})
            if historical:
                continue
            key = (record["owning_system"], record["id"])
            version = canonical({k: record[k] for k in ("content_version", "record_version", "availability_version") if k in record})
            if key in versions and versions[key] != version:
                raise HarnessError("source_version_changed_during_case")
            versions[key] = version
        source_id = f"src_{len(self.calls) + 1:04d}"
        entry = {"source_id": source_id, "tool": tool, "arguments": dict(args), "data": data,
                 "role": role, "invocation_id": invocation_id, "trace": receipt, "latency_ms": latency_ms,
                 "sha256": hashlib.sha256(canonical(data).encode()).hexdigest(), "record_provenance": provenance}
        self.calls.append(entry)
        self.observed_versions = versions
        self.learn_ids(data)
        collection_parameters = {"get_documents": "document_id", "get_validation_samples": "sample_id",
                                 "get_validation_jobs": "job_id"}
        if tool in collection_parameters:
            self.ids_by_parameter.setdefault(collection_parameters[tool], set()).update(
                r["id"] for r in data.get("items", []) if isinstance(r, dict) and isinstance(r.get("id"), str))
        if tool == "get_standard_change_context":
            self.ids_by_parameter.setdefault("result_id", set()).update(r["id"] for r in data.get("evidence", []))
        if tool == "get_document" and data.get("document_type") in {"coordination_request", "coordination_policy"}:
            try:
                content = json.loads(data["content"])
                if not isinstance(content, dict):
                    raise ValueError()
                self.learn_ids(content)
            except (ValueError, TypeError):
                raise HarnessError("malformed_coordination_document") from None
        ref = SourceReference(source_id=source_id, tool_name=tool,
                              record_id=data.get("id", data.get("milestone_id", data.get("change_id"))),
                              content_version=data.get("content_version"), record_version=data.get("record_version"))
        self.state.source_references.append(ref)
        return source_id

    def get(self, source_id):
        for call in self.calls:
            if call["source_id"] == source_id:
                return call
        raise HarnessError("unknown_source_reference")

    def latest(self, tool, **args):
        return next((c for c in reversed(self.calls) if c["tool"] == tool
                     and all(c["arguments"].get(k) == v for k, v in args.items())), None)

    def validate_reference(self, ref):
        call = self.get(ref.source_id)
        if ref.tool_name.removeprefix("functions.") != call["tool"]:
            raise HarnessError("source_tool_mismatch")
        if ref.record_id is None:
            # A projection can have a version even without a top-level `id`.
            # Validate it against that exact aggregate, not a fabricated record.
            if any(getattr(ref, key) is not None and getattr(ref, key) != call["data"].get(key)
                   for key in ("content_version", "record_version")):
                raise HarnessError("source_version_mismatch")
            return
        matching = [r for r in records(call["data"]) if r.get("id", r.get("milestone_id", r.get("change_id"))) == ref.record_id]
        if not any(all(getattr(ref, k) == r.get(k) for k in ("content_version", "record_version")) for r in matching):
            raise HarnessError("source_version_mismatch")


def check_prose(text, registry):
    """Defense in depth, not a semantic proof. Typed claims are checked separately."""
    forbidden = r"(?:approval (?:is |was |has been )?granted|(?:we|i|the agent|coordinator|automation) (?:have |has )?(?:approved|scheduled|booked|executed|released|updated)|customer (?:has )?accepted|customer commitment (?:was |has been )?changed|hold (?:is |was |has been )?released|root cause (?:is|was)|(?:silicon|hardware) defect caused|validation (?:has )?passed)"
    negation = r"\b(?:not|no|never|without|cannot|neither|pending|requires?|before|unless|must|should|would|could|hypothetical)\b"
    for sentence in re.split(r"[.!?\n]", text):
        if re.search(forbidden, sentence, re.I) and not re.search(negation, sentence, re.I):
            # A specific historical result may be described, never a new run/pass.
            historical = any(r.get("id", "\x00") in sentence and r.get("status") == "completed"
                             and r.get("criteria_passed") is True
                             for c in registry.calls for r in records(c["data"]))
            if not historical or not re.search(r"validation (?:has )?passed", sentence, re.I):
                raise HarnessError("unsupported_consequential_claim")


def validate_common(output, registry, allowed_sources=None):
    if output.case_id != registry.state.case_id:
        raise HarnessError("output_case_mismatch")
    refs = [r.source_id for r in output.source_references]
    if len(refs) != len(set(refs)):
        raise HarnessError("duplicate_output_reference")
    if allowed_sources is not None and not set(refs) <= allowed_sources:
        raise HarnessError("source_not_in_agent_context")
    for ref in output.source_references:
        registry.validate_reference(ref)
    def walk(value):
        if isinstance(value, dict):
            for name in ("source_refs",):
                if name in value and not set(value[name]) <= set(refs):
                    raise HarnessError("uncited_source")
            if "source_id" in value and value["source_id"] not in refs:
                raise HarnessError("uncited_source")
            if {"source_id", "pointer", "value_json"} <= value.keys():
                source = registry.get(value["source_id"])["data"]
                try:
                    expected = json.loads(value["value_json"])
                except (ValueError, TypeError):
                    raise HarnessError("invalid_source_assertion") from None
                if canonical(pointer(source, value["pointer"])) != canonical(expected):
                    raise HarnessError("source_assertion_mismatch")
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            check_prose(value, registry)
    walk(output.model_dump())


def validate_options(options, source):
    if source is None:
        if options:
            raise HarnessError("options_without_authoritative_tool")
        return
    raw_options = source["data"]["items"]
    actual = {(o.slot_id, o.sample_id): o for o in options}
    if len(actual) != len(options) or set(actual) != {(r["slot"]["id"], r["sample"]["id"]) for r in raw_options}:
        raise HarnessError("incomplete_option_set")
    for raw in raw_options:
        option = actual[(raw["slot"]["id"], raw["sample"]["id"])].model_dump(exclude={"source_refs"})
        expected = {k: raw[k] for k in option if k not in {"slot_id", "sample_id", "rate_id"}}
        expected.update(slot_id=raw["slot"]["id"], sample_id=raw["sample"]["id"], rate_id=raw["rate"]["id"])
        if canonical(option) != canonical(expected):
            raise HarnessError("option_fact_mismatch")


def validate_assessment(output, registry, allowed_sources):
    validate_common(output, registry, allowed_sources)
    from .delivery import validate_delivery_assessment
    validate_delivery_assessment(output, registry)
    from .quality import validate_quality_assessment
    validate_quality_assessment(output, registry)
    if isinstance(output, StandardValidationAssessment):
        from enterprise_api.standard_models import StandardContext
        from enterprise_api.standard_policy import evaluate
        call = registry.get(output.context_source_id)
        if call["tool"] != "get_standard_change_context" or call["arguments"].get("change_id") != registry.state.event.change_id:
            raise HarnessError("standard_context_mismatch")
        context = StandardContext.model_validate(call["data"])
        eligibility = evaluate(context)
        expected_procedure = context.procedure.get("id") if context.procedure else None
        expected_version = context.procedure.get("content_version") if context.procedure else None
        if (output.applicability_matches != eligibility.touchless_eligible or output.procedure_id != expected_procedure
                or output.procedure_content_version != expected_version
                or output.reusable_evidence_ids != eligibility.reusable_evidence_ids
                or output.remaining_work_ids != [w.work_id for w in eligibility.remaining_work]):
            raise HarnessError("standard_assessment_mismatch")
    if isinstance(output, ValidationClarificationResult):
        prior = next((r for r in registry.state.completed_assessments
                      if r.invocation_id == output.prior_assessment_invocation_id
                      and isinstance(r.assessment, ValidationEvidenceAssessment)), None)
        if not prior:
            raise HarnessError("clarification_prior_assessment_missing")
        tool = {"criteria_detail": "get_acceptance_criteria",
                "requirement_detail": "get_requirement_revision",
                "option_provenance": "get_validation_options"}[output.clarification_type]
        facts = [f for finding in output.findings for f in finding.facts]
        if not facts or not any(registry.get(f.source_id)["tool"] == tool for f in facts):
            raise HarnessError("clarification_facts_missing")
    if isinstance(output, ChangeImpactAssessment):
        change = registry.latest("get_change_request", change_id=registry.state.event.change_id)
        for key in ("baseline_requirement_revision_id", "proposed_requirement_revision_id"):
            if not change or not registry.latest("get_requirement_revision", requirement_revision_id=change["data"][key]):
                raise HarnessError("requirement_comparison_missing")
        if not output.requirement_delta or not output.affected_scope:
            raise HarnessError("change_scope_missing")
        for finding in output.confirmed_impacts:
            if re.search(r"coverage (?:is )?(?:sufficient|insufficient)|validation (?:passed|failed)", finding.statement, re.I):
                raise HarnessError("change_specialist_exceeds_role")
    if isinstance(output, ValidationEvidenceAssessment):
        call = registry.get(output.coverage_source_id)
        if call["tool"] != "get_validation_coverage" or call["arguments"].get("change_id") != registry.state.event.change_id:
            raise HarnessError("coverage_source_mismatch")
        coverage = call["data"]
        if output.coverage_status != ("sufficient" if coverage["coverage_satisfied"] else "insufficient"):
            raise HarnessError("coverage_conclusion_mismatch")
        evidence = output.applicable_evidence + output.inapplicable_evidence
        expected = {i["result"]["id"]: i for i in coverage["items"]}
        if len(evidence) != len(expected) or {e.result_id for e in evidence} != set(expected):
            raise HarnessError("incomplete_evidence_set")
        for item in evidence:
            raw = expected[item.result_id]
            if (item.status != raw["result"]["status"] or item.criteria_passed != raw["result"]["criteria_passed"]
                    or item.satisfies != raw["satisfies"] or item.mismatch_reasons != raw["mismatch_reasons"]
                    or item.source_id != output.coverage_source_id):
                raise HarnessError("evidence_fact_mismatch")
        if any(not e.satisfies for e in output.applicable_evidence) or any(e.satisfies for e in output.inapplicable_evidence):
            raise HarnessError("evidence_classification_mismatch")
        source = registry.latest("get_validation_options", change_id=registry.state.event.change_id)
        if not coverage["coverage_satisfied"] and source is None:
            raise HarnessError("gap_options_missing")
        validate_options(output.eligible_options + output.ineligible_options, source)
        if any(not o.eligible for o in output.eligible_options) or any(o.eligible for o in output.ineligible_options):
            raise HarnessError("option_classification_mismatch")
        if not coverage["coverage_satisfied"] and not output.evidence_gaps:
            raise HarnessError("evidence_gap_omitted")
    if isinstance(output, ProgramCommercialAssessment):
        standard = any(c["tool"] == "get_standard_change_context" and c["source_id"] in allowed_sources for c in registry.calls)
        if not output.affected_milestones or (not standard and not output.customer_commitments):
            raise HarnessError("program_context_incomplete")
        for item in output.affected_milestones + output.customer_commitments:
            source = registry.get(item.source_id)
            expected_tool = "get_program_milestone" if hasattr(item, "milestone_id") else "get_customer_order"
            rid = item.milestone_id if hasattr(item, "milestone_id") else item.order_id
            data = source["data"]
            if source["tool"] != expected_tool or data.get("id") != rid:
                raise HarnessError("program_source_mismatch")
            for key, value in item.model_dump(exclude={"source_id", "milestone_id", "order_id"}).items():
                if value != data.get(key):
                    raise HarnessError("program_fact_mismatch")
    if isinstance(output, ManufacturingAssessment):
        if not output.units or not output.lots:
            raise HarnessError("manufacturing_provenance_missing")
        for unit in output.units:
            source = registry.get(unit.source_id)
            if (source["tool"] != "get_manufacturing_unit" or source["data"]["id"] != unit.unit_id
                    or source["data"]["source_lot_id"] != unit.source_lot_id
                    or source["data"]["restrictions"] != unit.restrictions
                    or unit.source_lot_id not in {l.lot_id for l in output.lots}):
                raise HarnessError("manufacturing_fact_mismatch")
        for lot in output.lots:
            source = registry.get(lot.source_id)
            if (source["tool"] != "get_manufacturing_lot" or source["data"]["id"] != lot.lot_id
                    or source["data"]["restrictions"] != lot.restrictions):
                raise HarnessError("manufacturing_fact_mismatch")
        if any(x.restrictions for x in output.units + output.lots) and not output.active_restrictions:
            raise HarnessError("manufacturing_restriction_omitted")


def validate_final(output, registry, state, allowed_sources):
    validate_common(output, registry, allowed_sources)
    from .delivery import validate_delivery_final
    validate_delivery_final(output, registry, state)
    from .quality import validate_quality_final
    validate_quality_final(output, registry, state)
    if output.customer_id != state.customer_id or output.program_id != state.program_id:
        raise HarnessError("final_scope_mismatch")
    # Triage is provisional semantic classification. The Coordinator may refine
    # a supported category after specialist findings; it cannot refine away the
    # binding policy restriction or broaden the sole administrative touchless rule.
    if (output.classified_change_type == "other_or_unknown" and output.policy_path != "escalation_required"):
        raise HarnessError("unknown_final_classification_requires_escalation")
    touchless_type = ("quality_exception" if state.policy_decision.rule == "standard_quality_investigation_handoff"
        and state.workflow_id == "yield_exception_recovery" and state.event.change_id == "QE-011"
        else "standard_validation_package" if state.policy_decision.rule == "standard_touchless_handoff_v1" else "administrative_evidence_reference")
    if output.policy_path == "touchless_eligible" and output.classified_change_type != touchless_type:
        raise HarnessError("touchless_classification_outside_policy")
    if output.policy_path != state.policy_decision.policy_path:
        raise HarnessError("final_policy_mismatch")
    if ((state.triage.classified_change_type == "existing_case_status")
            != (output.classified_change_type == "existing_case_status")):
        raise HarnessError("status_inspection_intent_changed")
    expected = {(r.invocation_id, r.specialist) for r in state.completed_assessments}
    actual = {(r.invocation_id, r.specialist) for r in output.specialist_findings}
    if actual != expected or len(actual) != len(output.specialist_findings):
        raise HarnessError("final_specialists_missing")
    for result in state.completed_assessments:
        assessment = result.assessment
        if isinstance(assessment, ValidationEvidenceAssessment):
            if assessment.coverage_status == "insufficient" and not output.evidence_gaps:
                raise HarnessError("final_evidence_gap_omitted")
            expected_options = {canonical(o.model_dump(exclude={"source_refs"})) for o in assessment.eligible_options}
            actual_options = {canonical(o.model_dump(exclude={"source_refs"})) for o in output.available_options}
            if expected_options != actual_options or len(actual_options) != len(output.available_options):
                raise HarnessError("final_options_mismatch")
    if not any(isinstance(r.assessment, ValidationEvidenceAssessment) for r in state.completed_assessments) and output.available_options:
        raise HarnessError("final_options_without_specialist")
    if state.completed_assessments and not output.confirmed_facts:
        raise HarnessError("final_facts_missing")
    if not set(state.unresolved_questions) <= set(output.unresolved_questions):
        raise HarnessError("final_unresolved_questions_omitted")


def apply_review(review, registry, state, allowed_sources):
    """Resolve exact questions only with checked source facts; separate blockers.

    An engineering question for future human review is not equivalent to missing
    intake or conflicting evidence that prevents a decision package today.
    """
    for item in review.resolved_questions:
        if item.question not in state.unresolved_questions:
            raise HarnessError("resolution_question_not_pending")
        for assertion in item.supporting_facts:
            if assertion.source_id not in allowed_sources:
                raise HarnessError("resolution_source_not_available")
            source = registry.get(assertion.source_id)["data"]
            try:
                expected = json.loads(assertion.value_json)
            except (ValueError, TypeError):
                raise HarnessError("invalid_resolution_assertion") from None
            if canonical(pointer(source, assertion.pointer)) != canonical(expected):
                raise HarnessError("resolution_fact_mismatch")
        check_prose(item.resolution, registry)
    # Validate every resolution before changing state.
    resolved = {r.question for r in review.resolved_questions}
    state.unresolved_questions[:] = [q for q in state.unresolved_questions if q not in resolved]
    # A blocker is an unresolved question with policy effect. Once the exact
    # question is resolved with validated source facts, retaining that same text
    # would incorrectly force an escalation despite successful reconciliation.
    state.blocking_issues[:] = [q for q in state.blocking_issues if q not in resolved]
    for question in review.unresolved_questions + review.disagreements + review.blocking_issues:
        if question not in state.unresolved_questions:
            state.unresolved_questions.append(question)
    for blocker in review.disagreements + review.blocking_issues:
        if blocker not in state.blocking_issues:
            state.blocking_issues.append(blocker)
    if not review.ready_to_synthesize and not review.additional_work:
        state.blocking_issues.append("Coordinator cannot reconcile the available findings.")
    state.coordinator_reviews.append(review)
