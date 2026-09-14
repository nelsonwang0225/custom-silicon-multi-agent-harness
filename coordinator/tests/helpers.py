"""Developer-only synthetic assessments, never runtime retrieval."""
import json
from pathlib import Path

from program_coordinator.harness import CaseHarness
from program_coordinator.controls import HarnessConfig
from program_coordinator.models import *
from program_investigator.telemetry import Recorder
from program_investigator.models import ValidationOption

ROOT = Path(__file__).resolve().parents[2]


def event(name="human_review"):
    return ProgramChangeEvent.model_validate_json((ROOT / "coordinator/scenarios" / (name + ".json")).read_text())


def harness(**kwargs):
    return CaseHarness(kwargs.pop("config", HarnessConfig()), kwargs.pop("event", event()),
                       None, Recorder("trace_" + "0" * 32), **kwargs)


def seed_sources(h):
    for call in json.loads((Path(__file__).parent / "data/cr017_reads.json").read_text()):
        h.sources.add(call["tool"], call["arguments"], call["data"], "validation_evidence", "work_test", {}, 0.0)
    h.state.scope_verified = True
    return h


def reference(h, source_id):
    return next(r for r in h.state.source_references if r.source_id == source_id)


def fact(h, tool="get_change_request", path="/title", statement="The source describes the change."):
    from program_coordinator.sources import pointer
    call = h.sources.latest(tool)
    return Finding(statement=statement, basis="fact", source_refs=[call["source_id"]],
        facts=[SourceFact(source_id=call["source_id"], pointer=path, value_json=json.dumps(pointer(call["data"], path)))])


def assessment(h, role):
    base = dict(case_id=h.state.case_id, summary="Source-backed domain assessment.", confidence=0.95,
                unresolved_questions=[], source_references=list(h.state.source_references))
    if role == "change_impact":
        return ChangeImpactAssessment(**base, change_type="workload_profile_change", requirement_delta=[fact(h)],
            affected_scope=[fact(h)], confirmed_impacts=[fact(h)], possible_impacts=[], unaffected_scope=[], missing_information=[])
    if role == "validation_evidence":
        cov, opts = h.sources.latest("get_validation_coverage"), h.sources.latest("get_validation_options")
        evidence = [EvidenceItem(result_id=r["result"]["id"], status=r["result"]["status"],
            criteria_passed=r["result"]["criteria_passed"], satisfies=r["satisfies"], mismatch_reasons=r["mismatch_reasons"],
            source_id=cov["source_id"]) for r in cov["data"]["items"]]
        options = []
        for raw in opts["data"]["items"] if opts else []:
            value = {k: raw[k] for k in ValidationOption.model_fields if k not in {"source_refs", "slot_id", "sample_id", "rate_id"}}
            value.update(slot_id=raw["slot"]["id"], sample_id=raw["sample"]["id"], rate_id=raw["rate"]["id"], source_refs=[opts["source_id"]])
            options.append(ValidationOption.model_validate(value))
        return ValidationEvidenceAssessment(**base, coverage_status="sufficient" if cov["data"]["coverage_satisfied"] else "insufficient",
            coverage_source_id=cov["source_id"], evidence_gaps=[] if cov["data"]["coverage_satisfied"] else [fact(h, "get_validation_coverage", "/coverage_satisfied")],
            applicable_evidence=[e for e in evidence if e.satisfies], inapplicable_evidence=[e for e in evidence if not e.satisfies],
            eligible_options=[o for o in options if o.eligible], ineligible_options=[o for o in options if not o.eligible], technical_constraints=[])
    if role == "program_commercial":
        ms, order = h.sources.latest("get_program_milestone"), h.sources.latest("get_customer_order")
        return ProgramCommercialAssessment(**base, affected_milestones=[MilestoneImpact(milestone_id=ms["data"]["id"],
            source_id=ms["source_id"], **{k: ms["data"][k] for k in ("baseline_at", "current_forecast_at", "forecast_status")})],
            customer_commitments=[CustomerCommitment(order_id=order["data"]["id"], source_id=order["source_id"],
                **{k: order["data"][k] for k in ("committed_delivery_at", "quantity", "quantity_unit")})],
            dependencies=[fact(h, "get_program_milestone", "/dependencies")], schedule_exposure=[], cost_context=[], owners=[], risks=[])
    unit, lot = h.sources.latest("get_manufacturing_unit"), h.sources.latest("get_manufacturing_lot")
    return ManufacturingAssessment(**base, units=[UnitFinding(unit_id=unit["data"]["id"], source_lot_id=unit["data"]["source_lot_id"],
        restrictions=unit["data"]["restrictions"], source_id=unit["source_id"])], lots=[LotFinding(lot_id=lot["data"]["id"],
        restrictions=lot["data"]["restrictions"], source_id=lot["source_id"])],
        active_restrictions=[fact(h, "get_manufacturing_lot", "/restrictions")], provenance_findings=[], freshness_findings=[],
        release_conditions=[fact(h, "get_manufacturing_lot", "/hold_details/0/release_conditions")])


def triage(requests=(), **kwargs):
    return TriageDecision(classified_change_type="workload_profile_change", confidence=0.95, rationale="The workload changes.",
        specialists_required=list(requests), missing_information=[], risk_level="medium", proposed_workflow="Inspect necessary domains.",
        likely_policy_path="human_review_required", **kwargs)


def request(role, question="Inspect the domain.", depends_on=()):
    return WorkRequest(specialist=role, question=question, rationale="Establish source-backed domain facts.", focus_record_ids=[], depends_on=list(depends_on))


def final(h, path="human_review_required"):
    validations = [r.assessment for r in h.state.completed_assessments if isinstance(r.assessment, ValidationEvidenceAssessment)]
    return FinalDecisionPackage(case_id=h.state.case_id, customer_id=h.state.customer_id, program_id=h.state.program_id,
        classified_change_type=h.state.triage.classified_change_type, change_summary="Read-only assessment.", affected_scope=[],
        specialist_findings=[SpecialistSynopsis(invocation_id=r.invocation_id, specialist=r.specialist, summary=r.assessment.summary)
                            for r in h.state.completed_assessments],
        confirmed_facts=[fact(h)] if h.sources.latest("get_change_request") else [],
        evidence_gaps=[f for a in validations for f in a.evidence_gaps],
        available_options=[o for a in validations for o in a.eligible_options], relevant_constraints=[], program_impact=[], risks=[],
        unresolved_questions=list(h.state.unresolved_questions), recommended_next_step="Obtain the missing context or engineering review.",
        policy_path=path, requires_human_review=path != "touchless_eligible", escalation_reason="Missing information." if path == "escalation_required" else None,
        source_references=list(h.state.source_references), business_actions_executed=False, approval_granted=False,
        customer_accepted=False, new_validation_pass_claimed=False)
