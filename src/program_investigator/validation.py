"""Generic post-run source checks, with no golden-case facts or extra data access."""

from .config import InvestigatorError
from .models import InvestigationResult


def records(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from records(child)
    elif isinstance(value, list):
        for child in value:
            yield from records(child)


def validate_sources(output: InvestigationResult, calls: list[dict], case_id: str) -> None:
    """Reject invented citations or altered numeric/eligibility/evidence fields."""
    if output.case_id != case_id:
        raise InvestigatorError("output_case_mismatch")
    for ref in output.source_references:
        args = {p.name: p.value for p in ref.inputs}
        if len(args) != len(ref.inputs):
            raise InvestigatorError("output_source_mismatch")
        matches = [c for c in calls if c["tool"] == ref.tool_name and c["arguments"] == args]
        if not matches:
            raise InvestigatorError("output_source_mismatch")
        if ref.record_id is not None:
            candidates = [r for c in matches for r in records(c["data"])
                          if r.get("id", r.get("change_id", r.get("milestone_id"))) == ref.record_id]
            if not any(all(getattr(ref, key) is None or r.get(key) == getattr(ref, key)
                           for key in ("content_version", "record_version")) for r in candidates):
                raise InvestigatorError("output_source_version_mismatch")
        elif ref.content_version is not None or ref.record_version is not None:
            raise InvestigatorError("output_source_version_mismatch")

    def latest(tool):
        return next((c["data"] for c in reversed(calls) if c["tool"] == tool
                     and c["arguments"].get("change_id") == case_id), None)

    coverage = latest("get_validation_coverage")
    if coverage is None or output.validation_coverage_status.coverage_satisfied != coverage["coverage_satisfied"]:
        raise InvestigatorError("output_coverage_mismatch")
    evidence = {e.result_id: e for e in output.relevant_evidence}
    if len(evidence) != len(output.relevant_evidence) or set(evidence) != {i["result"]["id"] for i in coverage["items"]}:
        raise InvestigatorError("output_evidence_mismatch")
    for item in coverage["items"]:
        e = evidence[item["result"]["id"]]
        if e.satisfies != item["satisfies"] or e.mismatch_reasons != item["mismatch_reasons"]:
            raise InvestigatorError("output_evidence_mismatch")
        if any(getattr(e, f) != item["result"][f] for f in (
            "configuration_id", "workload_profile_id", "status", "criteria_passed", "covered_context_bins")):
            raise InvestigatorError("output_evidence_mismatch")

    source_options = latest("get_validation_options")
    if source_options is None:
        raise InvestigatorError("output_options_missing")
    options = {(o.slot_id, o.sample_id): o for o in output.eligible_options + output.ineligible_options}
    if set(options) != {(o["slot"]["id"], o["sample"]["id"]) for o in source_options["items"]}:
        raise InvestigatorError("output_options_mismatch")
    for raw in source_options["items"]:
        actual = options[(raw["slot"]["id"], raw["sample"]["id"])].model_dump(exclude={"source_refs"})
        expected = {k: raw[k] for k in actual if k not in {"slot_id", "sample_id", "rate_id"}}
        expected.update(slot_id=raw["slot"]["id"], sample_id=raw["sample"]["id"], rate_id=raw["rate"]["id"])
        if actual != expected:
            raise InvestigatorError("output_options_mismatch")
