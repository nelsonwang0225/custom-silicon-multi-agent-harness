import { useHost, type HostCase } from "./host";

export function caseRuntime(data: HostCase | null | undefined, caseId: string) {
  return data?.case_runtime_modes?.[caseId] || data?.mode;
}

export function RuntimeLabel({ caseId, run }: {
  caseId: string; run?: { execution_mode: string };
}) {
  const data = useHost()?.data;
  const mode = caseRuntime(data, caseId);
  if (!mode) return null;
  return <p className="cp-caption">
    {mode === "live_model"
      ? "Next investigation: Live AI · Uses the configured model and connected source APIs."
      : "Next investigation: Scripted demo · Connected source APIs, no model calls."}
    {run && <> This investigation: {run.execution_mode === "live_model" ? "Live AI" : "Scripted demo"}.</>}
  </p>;
}
