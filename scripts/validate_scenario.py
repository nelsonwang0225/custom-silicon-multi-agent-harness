#!/usr/bin/env python3
"""Read-only developer fixture checks; NOT an API or runtime business-rules module.

Uses only the standard library (Python 3.9+ for this planning utility). Expected
answers and deliberate corruption probes stay outside business retrieval. The
eventual service must implement and test its own typed rules, not import this file.
"""

import copy
import json
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("engineering", "validation", "manufacturing", "erp", "planner")
DOCUMENTS = {
    "DOC-REQUEST-01": "customer_change_request.md",
    "DOC-BASELINE-01": "approved_baseline.md",
    "DOC-CONFIG-01": "configuration_scope.md",
    "DOC-PROC-01": "supplemental_validation_procedure.md",
    "DOC-POLICY-01": "approval_policy.md",
    "DOC-PLAYBOOK-01": "change_control_playbook.md",
}
REFERENCES = {
    "program_id": "programs", "customer_id": "customers", "supplier_id": "suppliers",
    "configuration_id": "configurations", "supported_configuration_ids": "configurations",
    "workload_profile_id": "workload_profiles", "acceptance_limits_ref": "acceptance_criteria",
    "baseline_requirement_revision_id": "requirement_revisions",
    "proposed_requirement_revision_id": "requirement_revisions",
    "requirement_revision_id": "requirement_revisions",
    "milestone_id": "milestones", "milestone_ids": "milestones", "order_id": "orders",
    "request_document_id": "document_manifest", "document_id": "document_manifest",
    "permitted_procedure_ids": "procedures", "supported_procedure_ids": "procedures",
    "sample_id": "samples", "lab_id": "labs", "rate_id": "cost_rates",
    "unit_id": "units", "source_lot_id": "lots",
}
# Symbolic labels intentionally have no additional entity/catalog table this phase.
LABEL_FIELDS = {"scenario_id", "product_id", "model_bundle_id", "requirement_id"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc(value):
    require(isinstance(value, str) and value.endswith("Z"), "Expected explicit UTC timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def positive_int(value):
    return type(value) is int and value > 0


def validate(data):
    tables = {name: {r["id"]: r for r in rows}
              for domain in DOMAINS for name, rows in data[domain].items()}
    records = [(domain, table, r) for domain in DOMAINS
               for table, rows in data[domain].items() for r in rows]
    ids = [r["id"] for _, _, r in records]
    require(len(ids) == len(set(ids)), "Duplicate entity ID")
    now = utc(data["meta"]["scenario_now"])
    require(data["meta"]["schema_version"] == "1.1", "Unexpected seed schema")
    require(data["meta"]["synthetic"] is True, "Missing synthetic provenance")
    require(data["meta"]["currency"] == "USD" and data["meta"]["timezone"] == "UTC", "Units")
    reference_count = 0

    def walk(value, owner):
        nonlocal reference_count
        if isinstance(value, list):
            for item in value:
                walk(item, owner)
        elif isinstance(value, dict):
            for key, item in value.items():
                if key in REFERENCES:
                    refs = item if isinstance(item, list) else [item]
                    require(len(refs) == len(set(refs)), "Duplicate reference")
                    for ref in refs:
                        target = tables[REFERENCES[key]].get(ref)
                        require(target is not None, "Unresolved {}: {}".format(key, ref))
                        for scope in ("program_id", "customer_id"):
                            if scope in owner and scope in target:
                                require(owner[scope] == target[scope], "Cross-scope reference")
                        reference_count += 1
                elif key.endswith(("_id", "_ids", "_ref")) and key not in LABEL_FIELDS:
                    raise ValueError("Unclassified reference field: " + key)
                if key.endswith("_cents"):
                    require(type(item) is int and item >= 0, "Money must be nonnegative integer cents")
                if key.endswith("_version") and key != "document_version":
                    require(positive_int(item), "Invalid content/record/version binding")
                if key.endswith("_at") or key in ("effective_from", "effective_to"):
                    utc(item)
                walk(item, owner)

    for domain, table, record in records:
        require(record["owning_system"] == domain and record["synthetic"] is True, "Ownership/provenance")
        require(utc(record["updated_at"]) <= now, "Source update after scenario clock")
        require(positive_int(record["content_version"]), "Invalid content version")
        walk(record, record)

    for domain, table in (("engineering", "plans"), ("engineering", "decisions"),
                          ("validation", "jobs"), ("validation", "reservations"),
                          ("planner", "tasks"), ("planner", "implementation_links")):
        require(data[domain][table] == [], "Generated baseline records")
    require(data["audit_events"] == [], "Baseline audits must be empty")

    change = tables["changes"]["CR-017"]
    program = tables["programs"][change["program_id"]]
    baseline = tables["requirement_revisions"][change["baseline_requirement_revision_id"]]
    target = tables["requirement_revisions"][change["proposed_requirement_revision_id"]]
    config = tables["configurations"][change["configuration_id"]]
    workload = tables["workload_profiles"][target["workload_profile_id"]]
    milestone = tables["milestones"][change["milestone_id"]]
    order = tables["orders"][change["order_id"]]
    require(baseline["status"] == "approved" and target["status"] == "requested", "Requirement baseline")
    require(baseline["requirement_id"] == target["requirement_id"] and
            baseline["revision"] < target["revision"], "Revision relationship")
    require(baseline["acceptance_limits_ref"] == target["acceptance_limits_ref"], "Criteria changed")
    require(baseline["configuration_id"] == target["configuration_id"] == config["id"], "Target configuration")
    require(program["configuration_id"] == config["id"] and program["order_id"] == order["id"], "Program references")
    require(program["milestone_ids"] == [milestone["id"]] and milestone["order_id"] == order["id"], "Milestone relationship")
    for field in ("product_id", "product_revision"):
        require(config[field] == program[field] == order[field], "Product/order scope")
    require(config["model_bundle_id"] == workload["model_bundle_id"], "Model scope")
    require(positive_int(order["quantity"]) and order["quantity_unit"] == "accelerator_units", "Order units")
    require(change["workflow_state"] == "pending_impact_assessment", "Initial change state")
    require(utc(change["request_received_at"]) == now, "Request clock")
    require(utc(target["updated_at"]) == utc(change["updated_at"]) == now, "Request revision timestamps")
    require(utc(milestone["updated_at"]) >= utc(change["request_received_at"]), "Dependency precedes request")
    require(milestone["dependencies"] == [{"kind": "requirement_evidence",
            "requirement_revision_id": target["id"], "state": "pending_assessment"}], "Pending dependency")
    require(milestone["baseline_at"] == milestone["current_forecast_at"], "Baseline forecast")
    require(milestone["forecast_status"] == "not_reassessed_for_new_request", "Forecast status")
    require(now < utc(milestone["baseline_at"]) < utc(order["committed_delivery_at"]), "Deadline order")

    procedures = [p for p in tables["procedures"].values() if p["status"] == "approved"
                  and p["workload_profile_id"] == workload["id"] and config["id"] in p["supported_configuration_ids"]]
    require(len(procedures) == 1, "Ambiguous target procedure")
    procedure = procedures[0]
    require(procedure["acceptance_limits_ref"] == target["acceptance_limits_ref"], "Procedure criteria")
    for field in ("setup_minutes", "suite_minutes", "per_bin_minutes", "review_minutes"):
        require(positive_int(procedure[field]), "Invalid procedure duration")
    require(procedure["suite_minutes"] == workload["total_suite_minutes"] ==
            procedure["per_bin_minutes"] * len(workload["context_bins"]), "Target suite/per-bin arithmetic")
    for profile in tables["workload_profiles"].values():
        require(len(set(profile["context_bins"])) == len(profile["context_bins"]), "Duplicate workload bins")
        require(all(positive_int(x) for x in profile["context_bins"]), "Invalid context bin")
        for field in ("total_suite_minutes", "concurrency", "output_tokens"):
            require(positive_int(profile[field]), "Invalid workload quantity")
    policies = [p for p in tables["approval_policies"].values() if
                p["status"] == "approved" and procedure["id"] in p["permitted_procedure_ids"]]
    require(len(policies) == 1, "Ambiguous approval policy")
    policy = policies[0]
    require(policy["approver_role"] == "engineer" and policy["currency"] == "USD", "Policy authority")
    require(set(policy["permitted_actions"]) == {"schedule_validation", "link_program_plan"}, "Policy actions")

    coverage = []
    for result in tables["results"].values():
        result_config = tables["configurations"][result["configuration_id"]]
        result_profile = tables["workload_profiles"][result["workload_profile_id"]]
        result_criteria = tables["acceptance_criteria"][result["acceptance_limits_ref"]]
        for version, source in (("configuration_content_version", result_config),
                                ("workload_profile_content_version", result_profile),
                                ("acceptance_criteria_content_version", result_criteria)):
            require(result[version] == source["content_version"], "Historical version binding")
        require(result["model_bundle_id"] == result_config["model_bundle_id"] ==
                result_profile["model_bundle_id"], "Result model provenance")
        require(result["product_revision"] == result_config["product_revision"], "Result revision provenance")
        require(tables["samples"][result["sample_id"]]["configuration_id"] == result_config["id"], "Result sample provenance")
        require(utc(result["completed_at"]) <= utc(result["updated_at"]) <= now, "Result chronology")
        observed = result["observed_minutes_by_context_bin"]
        require(all(positive_int(v) for v in observed.values()), "Invalid observed minutes")
        require(set(map(int, observed)) == set(result["covered_context_bins"]), "Result bin keys")
        require(sum(observed.values()) == result["actual_suite_minutes"], "Observed total mismatch")
        reasons = []
        if result["product_revision"] != config["product_revision"]:
            reasons.append("WRONG_PRODUCT_REVISION")
        if result["configuration_id"] != config["id"]:
            reasons.append("WRONG_CONFIGURATION")
        if result["workload_profile_id"] != workload["id"]:
            reasons.append("WRONG_PROFILE")
        if result["status"] != "completed" or result["criteria_passed"] is not True:
            reasons.append("NOT_COMPLETED_PASS")
        if not set(workload["context_bins"]).issubset(result["covered_context_bins"]):
            reasons.append("MISSING_CONTEXT_BINS")
        if result["actual_suite_minutes"] < procedure["suite_minutes"] or any(
                observed.get(str(b), 0) < procedure["per_bin_minutes"] for b in workload["context_bins"]):
            reasons.append("INSUFFICIENT_DURATION")
        coverage.append({"result_id": result["id"], "reasons": reasons})
    require(all(row["reasons"] for row in coverage), "Unexpected sufficient seeded result")

    for unit in tables["units"].values():
        lot = tables["lots"][unit["source_lot_id"]]
        require(all(unit[f] == lot[f] for f in ("program_id", "product_id", "product_revision")), "Unit/lot lineage")
    for sample in tables["samples"].values():
        unit = tables["units"][sample["unit_id"]]
        sample_config = tables["configurations"][sample["configuration_id"]]
        require(all(unit[f] == sample_config[f] for f in ("program_id", "product_id", "product_revision")), "Sample/unit lineage")
    options = []
    for slot in tables["slots"].values():
        lab = tables["labs"][slot["lab_id"]]
        rate = tables["cost_rates"][slot["rate_id"]]
        start = utc(slot["starts_at"])
        end = start + timedelta(minutes=procedure["setup_minutes"] + procedure["suite_minutes"])
        ready = end + timedelta(minutes=procedure["review_minutes"])
        require(now <= start < utc(slot["ends_at"]), "Slot chronology")
        require(rate["currency"] == "USD" and rate["status"] == "approved", "Rate approval")
        require(utc(rate["effective_from"]) <= start < end <= utc(rate["effective_to"]), "Rate effective interval")
        for sample in tables["samples"].values():
            unit = tables["units"][sample["unit_id"]]
            lot = tables["lots"][unit["source_lot_id"]]
            reasons = []
            if config["id"] not in lab["supported_configuration_ids"]:
                reasons.append("LAB_CONFIGURATION_UNSUPPORTED")
            if procedure["id"] not in lab["supported_procedure_ids"]:
                reasons.append("LAB_PROCEDURE_UNSUPPORTED")
            if sample["configuration_id"] != config["id"] or unit["product_revision"] != config["product_revision"]:
                reasons.append("SAMPLE_CONFIGURATION_MISMATCH")
            if sample["campus"] != lab["campus"]:
                reasons.append("CAMPUS_MISMATCH")
            if unit["restrictions"] or lot["restrictions"]:
                reasons.append("MANUFACTURING_RESTRICTION")
            if any(not timedelta(0) <= now - utc(r["updated_at"]) <= timedelta(
                    minutes=data["meta"]["partner_freshness_limit_minutes"]) for r in (unit, lot)):
                reasons.append("PARTNER_DATA_STALE")
            if slot["availability"] != "available" or sample["availability"] != "available":
                reasons.append("RESOURCE_UNAVAILABLE")
            if end > utc(slot["ends_at"]):
                reasons.append("SLOT_TOO_SHORT")
            eligible = not reasons
            options.append({"slot_id": slot["id"], "sample_id": sample["id"], "reasons": reasons,
                            "resource_eligible": eligible,
                            "approval_eligible": eligible and rate["incremental_cost_cents"] <= policy["max_incremental_cost_cents"],
                            "cost_cents": rate["incremental_cost_cents"],
                            "review_ready_at": ready.isoformat().replace("+00:00", "Z") if eligible else None,
                            "deadline_slack_minutes": int((utc(milestone["baseline_at"]) - ready).total_seconds() // 60) if eligible else None})

    require(set(tables["document_manifest"]) == set(DOCUMENTS), "Document manifest allowlist")
    for document_id, filename in DOCUMENTS.items():
        document = tables["document_manifest"][document_id]
        require(document["relative_path"] == "fixtures/documents/" + filename, "Unsafe document path")
        path = ROOT / document["relative_path"]
        require(not any(p.is_symlink() for p in (path, path.parent, path.parent.parent)), "Document symlink")
        require(path.is_file() and path.resolve().is_relative_to(ROOT), "Document outside project")
        content = path.read_text()
        require("SYNTHETIC" in content, "Document synthetic label")
        require(not any(slot_id in content for slot_id in tables["slots"]), "Option answer in business document")
    return {"records": len(records), "references": reference_count, "documents": len(DOCUMENTS),
            "coverage": coverage, "options": options}


def main():
    seed = json.loads((ROOT / "fixtures/seed.json").read_text())
    report = validate(seed)
    # Developer-only expected scenario answers, never imported into the service.
    eligible = {x["slot_id"]: x for x in report["options"] if x["resource_eligible"]}
    require(len(report["options"]) == 9 and len(eligible) == 2, "Expected option matrix")
    for slot, ready, slack, cents in (
        ("SLOT-STANDARD", "2026-11-20T22:00:00Z", -1680, 0),
        ("SLOT-PRIORITY", "2026-11-18T20:00:00Z", 1320, 180000),
    ):
        row = eligible[slot]
        require((row["review_ready_at"], row["deadline_slack_minutes"], row["cost_cents"]) ==
                (ready, slack, cents), "Scenario calculation disagreement")
        require(row["sample_id"] == "SAMPLE-B-017" and row["approval_eligible"], "Eligible sample/policy")

    probes = [
        ("broken foreign key", lambda d: d["validation"]["samples"][0].update(unit_id="MISSING")),
        ("fractional cents", lambda d: d["erp"]["cost_rates"][0].update(incremental_cost_cents=0.5)),
        ("lost historical binding", lambda d: d["validation"]["results"][0].update(configuration_content_version=2)),
        ("dependency before request", lambda d: d["planner"]["milestones"][0].update(updated_at="2026-11-16T08:30:00Z")),
        ("per-bin arithmetic", lambda d: d["engineering"]["procedures"][0].update(per_bin_minutes=480)),
        ("document path escape", lambda d: d["engineering"]["document_manifest"][0].update(relative_path="docs/ACCEPTANCE_TESTS.md")),
    ]
    for name, mutate in probes:
        broken = copy.deepcopy(seed)
        mutate(broken)
        try:
            validate(broken)
        except ValueError:
            continue
        raise ValueError("Corruption probe was not rejected: " + name)
    report["corruption_probes_rejected"] = len(probes)
    report["status"] = "PASS — static scenario validation only; no API executed"
    from validate_portfolio import validate_portfolio
    report["expanded_portfolio"] = validate_portfolio()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
