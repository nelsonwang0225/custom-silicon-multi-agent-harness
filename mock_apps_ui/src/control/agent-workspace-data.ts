import { useCallback, useEffect, useRef, useState } from "react";
import { useHost, type HostSchema } from "./host";
import { DEMO_CHANGED } from "../demo-epoch";
type Task = HostSchema["AgentTask"];
type Agent = HostSchema["WorkspaceAgent"];
type Run = HostSchema["WorkspaceRun"];
export type WorkTask = Omit<Task, "evidence" | "dependencies"> & {
  evidence: NonNullable<Task["evidence"]>;
  dependencies: string[];
};
export type WorkAgent = Omit<Agent, "tasks" | "callers"> & {
  tasks: WorkTask[];
  callers: NonNullable<Agent["callers"]>;
};
export type WorkRun = Omit<Run, "agents" | "links"> & {
  agents: WorkAgent[];
  links: NonNullable<Run["links"]>;
};
export type Workspace = Omit<HostSchema["WorkspaceSnapshot"], "runs"> & {
  runs: WorkRun[];
};
const normalize = (v: HostSchema["WorkspaceSnapshot"]): Workspace => ({
  ...v,
  runs: v.runs.map((r) => ({
    ...r,
    links: r.links || [],
    agents: (r.agents || []).map((a) => ({
      ...a,
      callers: a.callers || [],
      tasks: (a.tasks || []).map((t) => ({
        ...t,
        evidence: t.evidence || [],
        dependencies: t.dependencies || [],
      })),
    })),
  })),
});
export function useAgentWorkspace(enabled: boolean) {
  const host = useHost(),
    read = host?.read;
  const [selection, setSelection] = useState<string | undefined>();
  const [data, setData] = useState<Workspace | null>(null);
  const [error, setError] = useState("");
  const [visible, setVisible] = useState(
    document.visibilityState === "visible",
  );
  const [clock, setClock] = useState(Date.now());
  const [resetVersion, setResetVersion] = useState(0);
  const serial = useRef(0),
    alive = useRef(false);
  const refresh = useCallback(async () => {
    if (
      !enabled ||
      !read ||
      !alive.current ||
      document.visibilityState !== "visible"
    )
      return;
    const request = ++serial.current;
    try {
      const raw = await read<HostSchema["WorkspaceSnapshot"]>(
        "/agent-workspace" +
          (selection ? "?run_id=" + encodeURIComponent(selection) : ""),
      );
      if (!alive.current || request !== serial.current) return;
      const value = normalize(raw);
      setData(value);
      setError("");
      setClock(Date.now());
      // Follow the newest observed run until the user explicitly chooses a scope.
      // Keep undefined as the automatic selection; the server prioritizes active work.
    } catch (e) {
      if (alive.current && request === serial.current) {
        setData(null);
        setError((e as Error).message);
        if (selection && /RUN_NOT_FOUND|Run not found/i.test((e as Error).message)) setSelection(undefined);
      }
    }
  }, [enabled, read, selection]);
  useEffect(() => {
    alive.current = true;
    void refresh();
    return () => {
      alive.current = false;
      ++serial.current;
    };
  }, [refresh, resetVersion]);
  const active = data?.runs.some(
    (r) =>
      r.status === "running",
  );
  useEffect(() => {
    if (!active || !visible) return;
    const timer = setInterval(() => void refresh(), 3000);
    return () => clearInterval(timer);
  }, [active, visible, refresh]);
  // Shared host reads discover new records without polling a completed selection.
  const stamp = [
    ...(host?.data?.runs || []),
    ...(host?.data?.standard?.runs || []),
    ...(host?.data?.quality?.runs || []),
    ...(host?.data?.autonomous_quality?.runs || []),
    ...(host?.data?.delivery?.runs || []),
  ]
    .map((r) => r.run_id + r.status + r.business_outcome)
    .join("|");
  useEffect(() => {
    void refresh();
  }, [stamp, refresh]);
  useEffect(() => {
    const visibility = () => {
      setVisible(document.visibilityState === "visible");
      setClock(Date.now());
      if (document.visibilityState === "visible") void refresh();
    };
    const reset = () => {
      ++serial.current;
      setData(null);
      setSelection(undefined);
      setResetVersion((n) => n + 1);
    };
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener(DEMO_CHANGED, reset);
    return () => {
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener(DEMO_CHANGED, reset);
    };
  }, [refresh]);
  // One expiry event, no perpetual completed-run timer or network polling.
  useEffect(() => {
    if (!data) return;
    const timer = setTimeout(
      () => setClock(Date.now()),
      Math.max(
        1,
        Date.parse(data.read_at) +
          data.read_ttl_seconds * 1000 -
          Date.now() +
          10,
      ),
    );
    return () => clearTimeout(timer);
  }, [data]);
  const stale =
    !visible ||
    (!!data && clock - Date.parse(data.read_at) > data.read_ttl_seconds * 1000);
  const select = (id: string | undefined) => {
    ++serial.current;
    setData(null);
    setError("");
    setSelection(id);
  };
  return { data, error, selection, select, refresh, stale, resetVersion };
}
