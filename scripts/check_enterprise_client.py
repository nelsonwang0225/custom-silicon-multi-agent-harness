"""Scripted read-only HTTP integration testing; no agent, model call or business writes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from pydantic import ValidationError

from enterprise_api import ClientConfig, EnterpriseAPIError, EnterpriseClient, Scope
from enterprise_api.transport import HttpxReadTransport, ReadTransport


class RecordingReads:
    """Record safe HTTP receipts; credentials and headers are never retained."""

    def __init__(self, delegate: ReadTransport):
        self.delegate = delegate
        self.receipts = []

    def get(self, path, params):
        start = time.perf_counter()
        response = self.delegate.get(path, params)
        body_digest = hashlib.sha256(json.dumps(response.body, sort_keys=True, allow_nan=False).encode()).hexdigest()
        self.receipts.append({"method": "GET", "path": path, "params": params,
                              "status": response.status, "attempts": response.attempts,
                              "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                              "request_id": response.request_id, "correlation_id": response.correlation_id,
                              "response_sha256": body_digest})
        return response

    def close(self):
        self.delegate.close()


def collect_context(client: EnterpriseClient, change_id: str) -> dict:
    """Follow HTTP-returned references; retain all options/evidence without ranking."""
    change = client.get_change_request(change_id)
    program_id = change["program_id"]
    program = client.get_program(program_id)
    requirements = {rid: client.get_requirement_revision(rid) for rid in sorted({
        change["baseline_requirement_revision_id"], change["proposed_requirement_revision_id"]})}
    configurations = {rid: client.get_configuration(rid) for rid in sorted(
        {change["configuration_id"], program["configuration_id"]} | {r["configuration_id"] for r in requirements.values()})}
    workloads = {rid: client.get_workload_profile(rid) for rid in sorted({r["workload_profile_id"] for r in requirements.values()})}
    criteria = {rid: client.get_acceptance_criteria(rid) for rid in sorted({r["acceptance_limits_ref"] for r in requirements.values()})}
    coverage = client.get_validation_coverage(change_id)
    options = client.get_validation_options(change_id)
    results = {item["result"]["id"]: client.get_validation_result(item["result"]["id"]) for item in coverage["items"]}
    procedures = {rid: client.get_procedure(rid) for rid in sorted({o["procedure_id"] for o in options["items"]})}
    policies = {rid: client.get_policy(rid) for rid in sorted({o["policy_id"] for o in options["items"]})}
    metadata = client.get_documents(program_id)
    documents = {d["id"]: client.get_document(d["id"]) for d in metadata["items"]}
    samples = client.get_validation_samples(program_id)
    unit_ids = {s["unit_id"] for s in samples["items"]} | {o["unit_id"] for o in options["items"]}
    provenance = {rid: client.get_manufacturing_provenance(rid) for rid in sorted(unit_ids)}
    orders = {rid: client.get_customer_order(rid) for rid in sorted({change["order_id"], program["order_id"]})}
    plans = {p["id"]: client.get_plan(p["id"]) for p in change["plans"]}
    decisions = {p["decision_id"]: client.get_plan_decision(p["decision_id"]) for p in plans.values() if p["decision_id"]}
    jobs = client.get_validation_jobs(change_id)
    job_details = {job["id"]: client.get_validation_job(job["id"]) for job in jobs["items"]}
    reservations = {job["id"]: client.get_validation_reservation(job["id"]) for job in jobs["items"]}
    milestone = client.get_program_milestone(program_id, change["milestone_id"])
    dependencies = client.get_dependencies(program_id, milestone["id"])
    links = client.get_implementation_links(program_id, change_id)
    return {
        "engineering": {"change": change, "requirements": requirements, "configurations": configurations,
                        "workloads": workloads, "criteria": criteria, "procedures": procedures,
                        "policies": policies, "document_metadata": metadata, "documents": documents,
                        "plans": plans, "decisions": decisions},
        "validation": {"coverage": coverage, "options": options, "results": results, "samples": samples,
                       "jobs": jobs, "job_details": job_details, "reservations": reservations},
        "manufacturing": {"provenance": provenance},
        "erp": {"orders": orders, "approved_cost_rates": client.get_cost_rates(program_id)},
        "planner": {"program": program, "milestone": milestone, "dependencies": dependencies,
                    "implementation_links": links},
    }


def summarize(context: dict, receipts: list) -> dict:
    """Count retrieved records, not business outcomes or recommended actions."""
    eng = context["engineering"]
    val = context["validation"]
    return {
        "systems_retrieved": list(context),
        "change_id": eng["change"]["id"],
        "program_id": eng["change"]["program_id"],
        "customer_id": eng["change"]["customer_id"],
        "counts": {"requirement_revisions": len(eng["requirements"]), "configurations": len(eng["configurations"]),
                   "workloads": len(eng["workloads"]), "procedures": len(eng["procedures"]),
                   "policies": len(eng["policies"]), "criteria": len(eng["criteria"]),
                   "documents": len(eng["documents"]), "validation_results": len(val["results"]),
                   "validation_options": len(val["options"]["items"]), "samples": len(val["samples"]["items"]),
                   "unit_lot_provenance_pairs": len(context["manufacturing"]["provenance"]),
                   "orders": len(context["erp"]["orders"]), "approved_cost_rates": len(context["erp"]["approved_cost_rates"]["items"]),
                   "plans": len(eng["plans"]), "decisions": len(eng["decisions"]),
                   "jobs": len(val["jobs"]["items"]), "reservations": len(val["reservations"]),
                   "milestones": 1, "dependencies": len(context["planner"]["dependencies"]["dependencies"]),
                   "implementation_links": len(context["planner"]["implementation_links"]["items"])},
        "logical_http_reads": len(receipts),
        "http_attempts": sum(r["attempts"] for r in receipts),
        "all_http_statuses_200": all(r["status"] == 200 for r in receipts),
        "all_http_methods_get": all(r["method"] == "GET" for r in receipts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--change-id", default="CR-017")
    parser.add_argument("--program-id", default="PRG-A17")
    parser.add_argument("--customer-id", default="CUST-FML01")
    parser.add_argument("--reader-identity", choices=["demo-reader-local-only", "demo-portfolio-reader-local-only"], default="demo-reader-local-only")
    parser.add_argument("--output", type=Path, default=Path(".cache/enterprise-client/cr017-http.json"))
    args = parser.parse_args()
    try:
        config = ClientConfig(base_url=args.base_url, reader_identity=args.reader_identity,
                              scope=Scope(program_id=args.program_id, customer_id=args.customer_id))
        transport = RecordingReads(HttpxReadTransport(config))
        try:
            with EnterpriseClient(config, transport=transport) as client:
                context = collect_context(client, args.change_id)
        finally:
            transport.close()
        summary = summarize(context, transport.receipts)
        report = {"label": "SCRIPTED READ-ONLY ENTERPRISE HTTP INTEGRATION TESTING; NO AGENT OR MODEL CALL",
                  "captured_at_utc": datetime.now(timezone.utc).isoformat(), "base_url": config.base_url,
                  "summary": summary, "context": context, "http_receipts": transport.receipts}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"label": report["label"], "summary": summary, "output": str(args.output)}, indent=2))
        return 0
    except EnterpriseAPIError as exc:
        print(json.dumps({"status": "failed", "error": exc.to_dict()}))
    except ValidationError:
        print(json.dumps({"status": "failed", "error": {"kind": "input", "code": "INVALID_CONFIGURATION"}}))
    except OSError:
        print(json.dumps({"status": "failed", "error": {"kind": "output", "code": "OUTPUT_UNAVAILABLE"}}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
