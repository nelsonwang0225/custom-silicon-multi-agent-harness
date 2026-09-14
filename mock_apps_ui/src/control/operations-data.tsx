import { useCallback, useEffect, useState } from "react";
import { Link } from "./access";
import { date } from "./data";
import { gateLabel } from "./trace-language";
import { useHost, type HostSchema } from "./host";
import type { SearchRecord, SourceAlert } from "./presentation-model";
type Index = HostSchema["OpsIndex"];
const runPath = (id: string) => "/control/runs/" + encodeURIComponent(id);
export function useOperations(enabled = true) {
  const host = useHost(),
    read = host?.read;
  const [data, setData] = useState<Index | null>(null),
    [error, setError] = useState("");
  const refresh = useCallback(async () => {
    if (!read || !host?.capabilities?.surfaces.includes("operations")) return;
    try {
      setData(await read<Index>("/operations"));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [read, host?.capabilities]);
  const runStamp =
    [
      ...(host?.data?.runs || []),
      ...(host?.data?.standard?.runs || []),
      ...(host?.data?.quality?.runs || []),
      ...(host?.data?.autonomous_quality?.runs || []),
      ...(host?.data?.delivery?.runs || []),
    ]
      .map((r) => r.run_id + ":" + r.status + ":" + r.business_outcome)
      .join("|") + JSON.stringify(host?.data?.case_summaries || []);
  useEffect(() => {
    if (enabled) void refresh();
  }, [enabled, refresh, runStamp]);
  return { data, error, refresh, setData };
}
export function operationsSearch(data: Index | null): SearchRecord[] {
  if (!data) return [];
  return [
    ...data.runs.map((r) => ({
      id: "ops/" + r.run_id,
      title: `${r.case_id} · Investigation · ${date(r.started_at, true)}`,
      group: "Workflow runs",
      context: r.business_outcome,
      mode: r.execution_mode,
      terms: `${r.run_id} ${r.trace_id || ""} ${r.case_id} ${r.workflow_id}`,
      to: runPath(r.run_id),
    })),
    ...data.sessions.map((s) => ({
      id: s.session_id,
      title: "Concierge · " + date(s.updated_at, true),
      group: "Concierge sessions",
      context: `${s.turn_count} visible messages`,
      mode: "Recorded history",
      terms: s.session_id + " " + s.run_ids.join(" "),
      to: "/control/operations/sessions/" + s.session_id,
    })),
    ...data.evals.map((e) => ({
      id: "eval/" + e.eval_id,
      title: e.label,
      group: "Evals & Reliability",
      context: `${e.passed} of ${e.total} passed · ${gateLabel(e.hard_gate)}`,
      mode: e.mode,
      terms:
        e.eval_id +
        " " +
        e.label +
        " " +
        e.cases.map((c) => c.case_id).join(" "),
      to: "/control/operations/evals?eval=" + e.eval_id,
    })),
  ];
}
export function operationsAlerts(data: Index | null): SourceAlert[] {
  return (data?.evals || [])
    .filter((e) => e.hard_gate === "FAIL")
    .map((e) => ({
      id: "eval/" + e.eval_id,
      title: e.label + " · Hard gate failed",
      context: `${e.mode} · ${e.passed}/${e.total} · ${e.critical_failures.length} critical failures`,
      to: "/control/operations/evals?eval=" + e.eval_id,
      kind: "host",
      time: e.timestamp,
    }));
}

export function CaseRunLink({ caseId }: { caseId: string }) {
  const data = useHost()?.data;
  const runs = [
    ...(data?.runs || []),
    ...(data?.standard?.runs || []),
    ...(data?.quality?.runs || []),
    ...(data?.autonomous_quality?.runs || []),
    ...(data?.delivery?.runs || []),
  ].filter((r) => r.change_id === caseId);
  return runs.length ? (
    <p className="cp-caption">
      <Link to={runPath(runs[0].run_id)}>View run details</Link> ·{" "}
      <Link to="/control/operations">Operations history</Link>
    </p>
  ) : null;
}
