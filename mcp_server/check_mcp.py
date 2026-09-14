"""Scripted real Streamable HTTP integration; no agent, model or business writes."""

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

import httpx

from enterprise_api import ClientConfig, EnterpriseClient, Scope
from stratos_mcp.catalog import CATALOG
from mcp_server.client import connect
from mcp_server.testing import PROJECT, backend, fingerprint, mcp_server


class VerifiedCalls:
    def __init__(self, mcp, direct):
        self.mcp = mcp
        self.direct = direct
        self.calls = []

    async def call(self, name, **arguments):
        result = await self.mcp.call_tool(name, arguments)
        payload = result.structured_content
        assert not result.is_error and payload["ok"], f"MCP tool failed: {name}"
        expected = CATALOG[name].method(self.direct, **arguments)
        assert payload["data"] == expected, f"MCP/client mismatch: {name}"
        trace = result.meta["stratos/trace"]
        assert trace["http_reads"]
        assert all(r["method"] == "GET" and r["status"] == 200 and r["request_id"]
                   and r["correlation_id"] == r["server_correlation_id"] == trace["correlation_id"]
                   for r in trace["http_reads"])
        self.calls.append({"tool": name, "arguments": arguments, "matches_enterprise_client": True,
                           "data_sha256": hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest(),
                           "trace": trace})
        return payload["data"]


async def collect_context(calls, change_id):
    """Follow returned record IDs. All calculations/rankings remain source API data."""
    call = calls.call
    change = await call("get_change_request", change_id=change_id)
    program_id = change["program_id"]
    program = await call("get_program", program_id=program_id)
    requirements = {rid: await call("get_requirement_revision", requirement_revision_id=rid) for rid in sorted({
        change["baseline_requirement_revision_id"], change["proposed_requirement_revision_id"]})}
    configurations = {rid: await call("get_configuration", configuration_id=rid) for rid in sorted(
        {change["configuration_id"], program["configuration_id"]} | {r["configuration_id"] for r in requirements.values()})}
    workloads = {rid: await call("get_workload_profile", workload_profile_id=rid)
                 for rid in sorted({r["workload_profile_id"] for r in requirements.values()})}
    criteria = {rid: await call("get_acceptance_criteria", criteria_id=rid)
                for rid in sorted({r["acceptance_limits_ref"] for r in requirements.values()})}
    coverage = await call("get_validation_coverage", change_id=change_id)
    options = await call("get_validation_options", change_id=change_id)
    results = {i["result"]["id"]: await call("get_validation_result", result_id=i["result"]["id"]) for i in coverage["items"]}
    procedures = {rid: await call("get_procedure", procedure_id=rid) for rid in sorted({o["procedure_id"] for o in options["items"]})}
    policies = {rid: await call("get_policy", policy_id=rid) for rid in sorted({o["policy_id"] for o in options["items"]})}
    document_metadata = await call("get_documents", program_id=program_id)
    documents = {d["id"]: await call("get_document", document_id=d["id"]) for d in document_metadata["items"]}
    samples = await call("get_validation_samples", program_id=program_id)
    unit_ids = {s["unit_id"] for s in samples["items"]} | {o["unit_id"] for o in options["items"]}
    units = {rid: await call("get_manufacturing_unit", unit_id=rid) for rid in sorted(unit_ids)}
    lots = {rid: await call("get_manufacturing_lot", lot_id=rid) for rid in sorted({u["source_lot_id"] for u in units.values()})}
    orders = {rid: await call("get_customer_order", order_id=rid) for rid in sorted({change["order_id"], program["order_id"]})}
    rates = await call("get_cost_rates", program_id=program_id)
    plans = {p["id"]: await call("get_plan", plan_id=p["id"]) for p in change["plans"]}
    decisions = {p["decision_id"]: await call("get_decision", decision_id=p["decision_id"])
                 for p in plans.values() if p["decision_id"]}
    jobs = await call("get_validation_jobs", change_id=change_id)
    job_details = {j["id"]: await call("get_validation_job", job_id=j["id"]) for j in jobs["items"]}
    milestone = await call("get_program_milestone", program_id=program_id, milestone_id=change["milestone_id"])
    dependencies = await call("get_dependencies", program_id=program_id, milestone_id=milestone["id"])
    links = await call("get_implementation_links", program_id=program_id, change_id=change_id)
    return {"engineering": {"change": change, "requirements": requirements, "configurations": configurations,
                             "workloads": workloads, "criteria": criteria, "procedures": procedures,
                             "policies": policies, "document_metadata": document_metadata,
                             "documents": documents, "plans": plans, "decisions": decisions},
            "validation": {"coverage": coverage, "options": options, "results": results, "samples": samples,
                           "jobs": jobs, "job_details": job_details},
            "manufacturing": {"units": units, "lots": lots}, "erp": {"orders": orders, "cost_rates": rates},
            "planner": {"program": program, "milestone": milestone, "dependencies": dependencies,
                        "implementation_links": links}}


async def verify_catalog(client):
    result = await client.list_tools()
    names = {tool.name for tool in result.tools}
    assert names == set(CATALOG) and len(result.tools) == 28
    assert all(t.annotations.read_only_hint and t.annotations.idempotent_hint
               and not t.annotations.destructive_hint for t in result.tools)
    return sorted(names)


async def verify_cr(url, backend_url):
    config = ClientConfig(base_url=backend_url, scope=Scope(program_id="PRG-A17", customer_id="CUST-FML01"))
    with EnterpriseClient(config) as direct:
        async with connect(url + "/mcp") as client:
            names = await verify_catalog(client)
            calls = VerifiedCalls(client, direct)
            context = await collect_context(calls, "CR-017")
            await calls.call("get_standard_change_context", change_id="CR-019")
            await calls.call("get_quality_context", exception_id="QE-004")
            await calls.call("get_delivery_context", delivery_id="DR-009")
            repeated = await calls.call("get_change_request", change_id="CR-017")
            assert repeated == context["engineering"]["change"]
            return names, context, calls.calls


async def verify_populated(url, backend_url, case):
    scope = Scope(program_id=case["change"]["program_id"], customer_id=case["change"]["customer_id"])
    config = ClientConfig(base_url=backend_url, scope=scope, reader_identity="demo-portfolio-reader-local-only")
    with EnterpriseClient(config) as direct:
        async with connect(url + "/mcp") as client:
            await verify_catalog(client)
            calls = VerifiedCalls(client, direct)
            job = case["jobs"][0]
            plan = next(p for p in case["change"]["plans"] if p["id"] == job["plan_id"])
            await calls.call("get_plan", plan_id=plan["id"])
            await calls.call("get_decision", decision_id=plan["decision_id"])
            await calls.call("get_validation_job", job_id=job["id"])
            await calls.call("get_implementation_links", program_id=scope.program_id, change_id=case["change"]["id"])
            return calls.calls


def run_integration(storage):
    with backend(storage, standard=True, quality=True, delivery=True) as (backend_url, backend_process):
        with httpx.Client(base_url=backend_url, trust_env=False, timeout=10,
                          headers={"Authorization": "Bearer demo-portfolio-reader-local-only"}) as http:
            assert http.get("/openapi.json").json() == json.loads((PROJECT / "docs/openapi.json").read_text())
            before_portfolio = http.get("/api/v1/portfolio").json()
            before = fingerprint(storage)
            with mcp_server(storage, backend_url) as (url, mcp_process):
                assert http.get(url + "/ready").status_code == 200
                names, context, calls = asyncio.run(verify_cr(url, backend_url))
            assert mcp_process.returncode == 0
            # Existing seeded records exercise tools whose CR-017 collections are
            # empty. Choose by available records, never by business recommendation.
            case = next(c for c in before_portfolio["cases"] if c["jobs"] and c["links"]
                        and any(p["decision_id"] for p in c["change"]["plans"]))
            change = case["change"]
            with mcp_server(storage, backend_url, program_id=change["program_id"],
                            customer_id=change["customer_id"], portfolio=True) as (other_url, other_process):
                populated = asyncio.run(verify_populated(other_url, backend_url, case))
            assert other_process.returncode == 0
            assert http.get("/api/v1/portfolio").json() == before_portfolio
            after = fingerprint(storage)
            assert before == after, "Persisted isolated state changed"
            assert {c["tool"] for c in calls + populated} == set(CATALOG)
    assert backend_process.returncode == 0
    return {"label": "SCRIPTED READ-ONLY MCP STREAMABLE HTTP INTEGRATION; NO AGENT OR MODEL CALL",
            "captured_at_utc": datetime.now(timezone.utc).isoformat(), "backend_url": backend_url,
            "mcp_url": url + "/mcp", "tool_count": len(names), "tools": names,
            "context": context, "cr017_calls": calls, "populated_record_calls": populated,
            "checks": {"all_five_domains": len(context) == 5, "all_tools_invoked": True,
                       "matches_enterprise_client": True, "all_downstream_methods_get": True,
                       "correlation_echo_verified": True, "deterministic_repeat": True,
                       "no_write_tools": True, "api_portfolio_unchanged": True,
                       "all_persisted_tables_unchanged": before == after, "clean_shutdown": True},
            "database_fingerprint_before": before, "database_fingerprint_after": after}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT / ".cache/mcp-server/live-integration.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mcp-live-", dir=PROJECT / ".cache") as temp:
        report = run_integration(Path(temp))
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"tool_count": report["tool_count"], "cr017_calls": len(report["cr017_calls"]),
                      "populated_record_calls": len(report["populated_record_calls"]), "checks": report["checks"],
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
