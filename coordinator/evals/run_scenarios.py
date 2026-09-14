"""Lightweight live behavioral verification, unavailable to agent runtime.

This driver invokes the SAME Coordinator CLI for each input. Expected outcomes
below are test expectations only, never part of a model prompt or tool response.
It fingerprints persisted state using an independent developer-only subprocess,
and replays actual business reads through real local HTTP.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from enterprise_api import ClientConfig, Scope, EnterpriseClient
from stratos_mcp.catalog import CATALOG
from program_coordinator.models import CaseState, FinalDecisionPackage
from program_coordinator.controls import TOOL_MATRIX, GRAPH
from program_coordinator.sources import SourceRegistry, validate_assessment, validate_final
from program_coordinator.policy import determine_policy

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = {"touchless": "touchless_eligible", "human_review": "human_review_required", "escalation": "escalation_required"}


def fingerprint(storage):
    result = subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "coordinator/evals/prepare_demo.py"),
        "--storage", str(storage), "--fingerprint"], capture_output=True, text=True, cwd=ROOT, check=True)
    value = result.stdout.strip()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("Invalid independent fingerprint")
    return value


def verify(run_dir, scenario, before, after, backend_url):
    report = json.loads((run_dir / "report.json").read_text())
    calls = json.loads((run_dir / "tool-calls.json").read_text())
    checks = {"persisted_state_unchanged": before == after, "completed": report["status"] == "completed",
        "only_allowed_read_tools": all(c["tool"] in TOOL_MATRIX[c["role"]] for c in calls),
        "only_http_gets": all(r["method"] == "GET" and r["status"] == 200 for c in calls for r in c["trace"]["http_reads"]),
        "correlation_chain": all(r["correlation_id"] == r["server_correlation_id"] == c["trace"]["correlation_id"]
                                 and r["request_id"] for c in calls for r in c["trace"]["http_reads"]),
        "tracing_enabled_and_flushed": report["tracing_enabled"] and report["trace_export_flush_completed"],
        "live_astra": report["authentication_succeeded"] and bool(report["api_requests"])
            and all(r.get("model") == "gpt-6-astra" and r.get("status") == "completed" for r in report["api_requests"] if 200 <= r["http_status"] < 300)}
    if (run_dir / "result.json").exists():
        state = CaseState.model_validate_json((run_dir / "case-state.json").read_text())
        output = FinalDecisionPackage.model_validate_json((run_dir / "result.json").read_text())
        checks["structured_output_valid"] = True
        checks["expected_policy_path"] = output.policy_path == SCENARIOS[scenario]
        checks["no_claimed_actions"] = not (output.business_actions_executed or output.approval_granted or output.customer_accepted or output.new_validation_pass_claimed)
        checks["case_completed_and_no_pending_work"] = state.workflow_stage == "completed" and not state.pending_specialist_work
        checks["bounded_allowed_graph"] = all(w.specialist in GRAPH[w.caller] and w.depth <= 2 for w in state.requested_specialists) and len(state.requested_specialists) <= 8
        registry = SourceRegistry(state)
        registry.calls = calls
        recomputed = determine_policy(state, registry)
        checks["current_policy_revalidation"] = recomputed.policy_path == output.policy_path and not recomputed.execution_allowed
        all_sources = {c["source_id"] for c in calls}
        for item in state.completed_assessments:
            validate_assessment(item.assessment, registry, all_sources)
        validate_final(output, registry, state, all_sources)
        checks["source_and_domain_checks"] = True
        roles = {w.specialist for w in state.requested_specialists}
        if scenario == "touchless":
            checks["only_needed_specialist"] = roles == {"validation_evidence"}
            checks["sufficient_existing_coverage"] = any(c["tool"] == "get_validation_coverage" and c["data"]["coverage_satisfied"] for c in calls)
            checks["no_unnecessary_scheduling_options"] = not any(c["tool"] == "get_validation_options" for c in calls)
        elif scenario == "human_review":
            checks["core_specialists"] = {"change_impact", "validation_evidence", "program_commercial"} <= roles
            checks["parallel_work"] = any(b["parallel"] for b in report["parallel_branches"])
            checks["dynamic_manufacturing"] = any(d["caller"] == "validation_evidence" and d["target"] == "manufacturing" and d["status"] == "completed" for d in report["delegations"])
            checks["evidence_gap"] = bool(output.evidence_gaps)
            option = next((o for o in output.available_options if o.slot_id == "SLOT-PRIORITY" and o.sample_id == "SAMPLE-B-017"), None)
            checks["golden_cost_and_schedule"] = bool(option and option.cost_cents == 180000 and option.timing.review_ready_at == "2026-11-18T20:00:00Z" and option.timing.deadline_slack_minutes == 1320)
            impact = next((r.assessment for r in state.completed_assessments if r.specialist == "change_impact"), None)
            assertion_values = {json.dumps(json.loads(f.value_json), sort_keys=True) for finding in impact.requirement_delta for f in finding.facts} if impact else set()
            checks["golden_requirement_delta"] = all(json.dumps(v, sort_keys=True) in assertion_values for v in (
                "approved", "requested", "WF-LC-V1", "WF-LC-V2", [8192, 32768], [32768, 65536, 131072], 120, 480))
            checks["configuration_scope_established"] = bool(impact and any("CFG-B-01" in f.statement or any("CFG-B-01" in fact.value_json for fact in f.facts)
                                                                          for f in impact.affected_scope))
        else:
            checks["zero_specialists"] = not state.requested_specialists
            checks["zero_source_reads_for_unscoped_event"] = not calls
            checks["explicit_missing_information"] = bool(output.unresolved_questions and output.escalation_reason)
        with EnterpriseClient(ClientConfig(base_url=backend_url, scope=Scope(customer_id="CUST-FML01", program_id="PRG-A17"))) as client:
            checks["all_mcp_results_match_fresh_http"] = all(CATALOG[c["tool"]].method(client, **c["arguments"]) == c["data"] for c in calls)
    else:
        checks["structured_output_valid"] = False
    return {"passed": all(checks.values()), "checks": checks, "scenario": scenario,
        "source_sha256_before": before, "source_sha256_after": after,
        "trace_id": report["trace_id"], "run_dir": str(run_dir),
        "note": "Actual live model execution plus independent scripted checks; no human approval or business write."}


def main():
    parser = argparse.ArgumentParser(description="Explicit paid live checks for Phase 05; each case runs once.")
    parser.add_argument("--scenario", choices=list(SCENARIOS) + ["all"], required=True)
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--mcp-url", default="http://127.0.0.1:9010/mcp")
    parser.add_argument("--backend-url", default="http://127.0.0.1:9011")
    parser.add_argument("--verify-run", type=Path)
    parser.add_argument("--before-hash")
    args = parser.parse_args()
    outcomes = []
    for scenario in SCENARIOS if args.scenario == "all" else [args.scenario]:
        before = args.before_hash or fingerprint(args.storage)
        if args.verify_run:
            run_dir = args.verify_run
        else:
            result = subprocess.run([sys.executable, "-m", "program_coordinator", "--event",
                str(ROOT / "coordinator/scenarios" / (scenario + ".json")), "--mcp-url", args.mcp_url],
                cwd=ROOT, capture_output=True, text=True, timeout=1250)
            try:
                summary = json.loads(result.stdout)
                run_dir = Path(summary["artifact_directory"])
            except (ValueError, KeyError):
                raise RuntimeError("Coordinator CLI failed without a safe artifact receipt") from None
        after = fingerprint(args.storage)
        try:
            outcome = verify(run_dir, scenario, before, after, args.backend_url)
        except Exception as exc:
            outcome = {"passed": False, "scenario": scenario, "run_dir": str(run_dir),
                "source_sha256_before": before, "source_sha256_after": after,
                "verification_error_type": type(exc).__name__}
        path = run_dir / ("verification.json" if not args.verify_run else "verification-recheck.json")
        with path.open("x") as handle:
            json.dump(outcome, handle, indent=2)
        outcomes.append(outcome)
        print(json.dumps(outcome), flush=True)
    return 0 if all(o["passed"] for o in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
