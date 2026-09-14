"""Independent HTTP oracle, never imported or exposed to the investigator.

Capture before a run, then compare its final output and actual MCP records with
fresh HTTP data. Golden assertions here are deliberately outside agent runtime.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re

import httpx

from enterprise_api import ClientConfig, EnterpriseClient, Scope
from mcp_server.check_mcp import collect_context
from stratos_mcp.catalog import CATALOG
from program_investigator.models import InvestigationResult
from program_investigator.validation import validate_sources


class DirectReads:
    def __init__(self, client):
        self.client = client

    async def call(self, name, **arguments):
        return CATALOG[name].method(self.client, **arguments)


def capture(base_url):
    with EnterpriseClient(ClientConfig(base_url=base_url,
            scope=Scope(program_id="PRG-A17", customer_id="CUST-FML01"))) as client:
        context = asyncio.run(collect_context(DirectReads(client), "CR-017"))
    with httpx.Client(base_url=base_url, trust_env=False, follow_redirects=False, timeout=10,
                      headers={"Authorization": "Bearer demo-reader-local-only"}) as http:
        for key, path in (("portfolio", "/api/v1/portfolio"),
                          ("audit", "/api/v1/audit/events?change_id=CR-017")):
            response = http.get(path)
            response.raise_for_status()
            context[key] = response.json()
    return context


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def verify(run_dir, before, base_url):
    after = capture(base_url)
    output = InvestigationResult.model_validate_json((run_dir / "result.json").read_text())
    calls = json.loads((run_dir / "tool-calls.json").read_text())
    report = json.loads((run_dir / "report.json").read_text())
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
    check("source_state_unchanged", digest(before) == digest(after))
    with EnterpriseClient(ClientConfig(base_url=base_url,
            scope=Scope(program_id="PRG-A17", customer_id="CUST-FML01"))) as client:
        check("every_mcp_result_matches_fresh_http", all(
            CATALOG[c["tool"]].method(client, **c["arguments"]) == c["data"] for c in calls))
    validate_sources(output, calls, "CR-017")
    check("generic_source_and_numeric_validation", True)
    check("customer", output.customer.id == "CUST-FML01" and output.customer.name.casefold() == "Helios AI".casefold())
    check("program", output.program.id == "PRG-A17")
    scope_ids = {s.id for s in output.affected_scope}
    configuration = after["engineering"]["configurations"]["CFG-B-01"]
    check("configuration_and_product", "CFG-B-01" in scope_ids and any(
        configuration["product_id"] in s.description and configuration["product_revision"] in s.description
        for s in output.affected_scope))
    summary = output.change_summary.statement.lower()
    check("long_context_change", all(re.search(pattern, summary) for pattern in
          (r"32\s*k|32,?768", r"64\s*k|65,?536", r"128\s*k|131,?072")))
    check("coverage_insufficient", output.validation_coverage_status.coverage_satisfied is False)
    check("all_evidence_and_mismatches", len(output.relevant_evidence) == len(after["validation"]["coverage"]["items"]))
    check("all_options", len(output.eligible_options) + len(output.ineligible_options)
          == len(after["validation"]["options"]["items"]))
    units, lots = after["manufacturing"]["units"], after["manufacturing"]["lots"]
    check("manufacturing_provenance_and_restrictions",
          {c.unit_id for c in output.manufacturing_constraints} == set(units) and all(
              c.source_lot_id == units[c.unit_id]["source_lot_id"]
              and c.unit_restrictions == units[c.unit_id]["restrictions"]
              and c.lot_restrictions == lots[c.source_lot_id]["restrictions"] and bool(c.provenance)
              for c in output.manufacturing_constraints))
    order = after["erp"]["orders"]["ORD-1204"]
    commitment = output.customer_commitment
    check("customer_commitment", commitment is not None and commitment.order_id == order["id"] and all(
        getattr(commitment, key) == order[key] for key in ("quantity", "quantity_unit", "committed_delivery_at")))
    milestone = after["planner"]["milestone"]
    result_milestone = output.program_milestone
    check("milestone_baseline_and_forecast", result_milestone is not None
          and result_milestone.milestone_id == milestone["id"] and all(
              getattr(result_milestone, key) == milestone[key]
              for key in ("baseline_at", "current_forecast_at", "forecast_status")))
    check("human_engineering_review_required", output.requires_human_review
          and "engineer" in output.recommended_next_step.statement.lower())
    reads = [r for c in calls for r in c["trace"]["http_reads"]]
    check("only_read_tools_and_http_gets", bool(reads) and all(CATALOG[c["tool"]] for c in calls)
          and all(r["method"] == "GET" and r["status"] == 200 for r in reads))
    check("correlation_chain", all(r["request_id"] and r["correlation_id"] == c["trace"]["correlation_id"]
          == r["server_correlation_id"] for c in calls for r in c["trace"]["http_reads"]))
    accepted = report["status"] == "completed"
    if (run_dir / "revalidation.json").exists():
        recovery = json.loads((run_dir / "revalidation.json").read_text())
        accepted = (recovery["status"] == "validated" and recovery["business_assessment_unchanged"]
                    and recovery["result_sha256"] == hashlib.sha256((run_dir / "result.json").read_bytes()).hexdigest())
    check("real_astra_and_tracing", accepted and report["authentication_succeeded"]
          and report["tracing_enabled"] and report["trace_export_flush_completed"]
          and bool(report["api_requests"]) and all(r.get("model") == "gpt-6-astra"
          and r.get("status") == "completed" for r in report["api_requests"]))
    return {"passed": all(checks.values()), "checks": checks, "source_sha256_before": digest(before),
            "source_sha256_after": digest(after), "http_read_count": len(reads),
            "tool_call_count": len(calls), "unique_tools_called": len({c["tool"] for c in calls}),
            "note": "Deterministic checks plus separate prose review; this oracle is unavailable to the agent."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-url", default="http://127.0.0.1:9001")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    if args.run_dir is None:
        with args.before.open("x") as out:
            json.dump(capture(args.backend_url), out, indent=2)
        print(json.dumps({"source_snapshot_captured": True}))
        return 0
    result = verify(args.run_dir, json.loads(args.before.read_text()), args.backend_url)
    (args.run_dir / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
