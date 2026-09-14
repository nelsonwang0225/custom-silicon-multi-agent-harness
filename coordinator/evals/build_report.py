"""Summarize already recorded runs; no model, MCP, or business calls."""
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def estimate(usage):
    # Official GPT-6 Astra published short-context standard text token prices,
    # checked during this build. An estimate, not an invoice or business savings.
    cost = (Decimal(usage["input_tokens"] - usage["cached_input_tokens"]) * 10
            + Decimal(usage["cached_input_tokens"])
            + Decimal(usage["output_tokens"]) * 50) / 1_000_000
    return float(cost.quantize(Decimal("0.000001")))


def walk_records(value):
    if isinstance(value, dict):
        if value.get("owning_system") and value.get("id"):
            yield value
        for child in value.values(): yield from walk_records(child)
    elif isinstance(value, list):
        for child in value: yield from walk_records(child)


def is_case_attempt(path, report):
    # A service replay/rejection can have a CLI receipt without a new harness
    # checkpoint. It is not another model investigation or a paid demonstration.
    return report.get("status") != "replayed" and (path.parent / "case-state.json").exists()


def main():
    attempts = []
    accepted = {}
    invocation_receipts = []
    for path in sorted((ROOT / ".cache/multi-agent").glob("trace_*/report.json")):
        report = json.loads(path.read_text())
        if not is_case_attempt(path, report):
            invocation_receipts.append({k: report.get(k) for k in (
                "trace_id", "run_id", "status", "invocation_status", "error_category", "original_artifact_directory", "usage")})
            continue
        state = json.loads((path.parent / "case-state.json").read_text())
        verification = json.loads((path.parent / "verification.json").read_text()) if (path.parent / "verification.json").exists() else {}
        calls = json.loads((path.parent / "tool-calls.json").read_text())
        records = list(walk_records([c["data"] for c in calls]))
        summary = {k: report.get(k) for k in ("trace_id", "started_at", "status", "policy_path", "model_calls",
            "api_request_count", "coordinator_turns", "specialist_invocations", "mcp_calls", "http_gets", "latency_ms", "usage",
            "termination_reason", "guardrail_events", "parallel_branches", "delegations")}
        summary.update(event_id=state["event"]["event_id"], classified_change_type=state["triage"]["classified_change_type"] if state["triage"] else None,
            verified=verification.get("passed", False), scenario=verification.get("scenario"),
            estimated_token_cost_usd=estimate(report["usage"]),
            source_systems=sorted({r["owning_system"] for r in records}), unique_source_records=len({(r["owning_system"], r["id"]) for r in records}),
            unique_tools=report["unique_tools"], artifact_directory=str(path.parent),
            specialists=[{"role": w["specialist"], "caller": w["caller"], "depth": w["depth"], "status": w["status"],
                "latency_ms": round(w["ended_ms"]-w["started_ms"],2) if w["ended_ms"] is not None else None}
                for w in state["requested_specialists"]],
            policy_decision=state["policy_decision"], verification=verification)
        if (path.parent / "verification-recheck.json").exists():
            summary["current_code_recheck"] = json.loads((path.parent / "verification-recheck.json").read_text())
        attempts.append(summary)
        if verification.get("passed"):
            old = accepted.get(verification["scenario"])
            if old is None or old["started_at"] < summary["started_at"]:
                accepted[verification["scenario"]] = summary
    attempts.sort(key=lambda r:r["started_at"])
    for scenario, summary in accepted.items():
        source = Path(summary["artifact_directory"]) / "result.json"
        destination = ROOT / "docs/multi_agent" / (scenario + "-decision.json")
        destination.write_text(source.read_text())
        summary["decision_artifact"] = str(destination.relative_to(ROOT))
    baseline_dir = ROOT / ".cache/program-investigator/trace_ef4ecc86847c44bb9db87174587f28a7"
    original = json.loads((baseline_dir / "run-summary.json").read_text())
    baseline_calls = json.loads((baseline_dir / "tool-calls.json").read_text())
    baseline_records = list(walk_records([c["data"] for c in baseline_calls]))
    baseline = {"trace_id": original["trace_id"], "status": original["status"],
        "model_calls": original["successful_assessment_generations"], "mcp_calls": len(baseline_calls),
        "http_gets": original["business_checks"]["http_read_count"], "latency_ms": original["successful_assessment_latency_ms"],
        "usage": original["successful_assessment_usage"], "estimated_token_cost_usd": estimate(original["successful_assessment_usage"]),
        "unique_tools": sorted({c["tool"] for c in baseline_calls}),
        "source_systems": sorted({r["owning_system"] for r in baseline_records}),
        "unique_source_records": len({(r["owning_system"],r["id"]) for r in baseline_records}),
        "verified": original["business_checks"]["passed"], "comparison_note": "Preserved historical baseline; no new paid baseline run."}
    usage = {key:sum(r["usage"][key] for r in attempts)
             + sum(r.get("usage", {}).get(key, 0) for r in invocation_receipts) for key in attempts[0]["usage"]}
    output = {"status": "PASS" if set(accepted) == {"touchless", "human_review", "escalation"} else "PARTIAL",
        "accepted_scenarios": accepted, "attempts": attempts, "baseline": baseline,
        "non_case_invocation_receipts": invocation_receipts,
        "all_phase05_attempt_usage": usage, "all_phase05_estimated_token_cost_usd": estimate(usage),
        "model": "gpt-6-astra", "model_routing": False,
        "pricing_source": "https://developers.openai.com/api/docs/models/gpt-6-astra",
        "cost_limitations": "Token estimate at published $10/M uncached input, $1/M cached input, $50/M output; completed generations only, not an invoice. Per-request input did not exceed 272K tokens.",
        "source_denial_audit_proof": json.loads((ROOT / ".cache/multi-agent/first-attempt-state-proof.json").read_text())}
    path = ROOT / "docs/multi_agent/run-results.json"
    path.write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps({"status": output["status"], "accepted_scenarios": list(accepted), "attempts": len(attempts),
        "model_calls": usage["requests"], "estimated_token_cost_usd": output["all_phase05_estimated_token_cost_usd"], "report": str(path)},indent=2))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
