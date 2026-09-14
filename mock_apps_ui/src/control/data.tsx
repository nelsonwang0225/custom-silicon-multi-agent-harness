import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api, type Schema } from "../api";
export type Program = Schema["ProgramSummary"];
export type CaseData = Schema["CaseData"];
export type Snapshot = Schema["Portfolio"] & {
  programs: Program[];
  units: Schema["Unit"][];
  lots: Schema["Lot"][];
  orders: Schema["Order"][];
};
export type Freshness =
  "Current read" | "Recorded result" | "Stale" | "Unavailable";
export type ExecutionMode = "Connected demo" | "Simulated" | "Preview only";
export const read = <T,>(path: string) => api("reader").get<T>(path);
const Context = createContext<{
  data: Snapshot | null;
  loading: boolean;
  error: boolean;
  fetchedAt: string;
  freshness: Freshness;
  refresh: () => Promise<void>;
}>(null!);
export function ControlData({ children }: { children: ReactNode }) {
  const [data, setData] = useState<Snapshot | null>(null);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState(false),
    [fetchedAt, setFetchedAt] = useState("");
  const [clock, setClock] = useState(Date.now());
  const generation = useRef(0);
  const refresh = useCallback(async () => {
    const ticket = ++generation.current;
    setLoading(true);
    try {
      const [portfolio, programs, units, lots, orders] = await Promise.all([
        read<Schema["Portfolio"]>("/portfolio"),
        read<{ items: Program[] }>("/programs"),
        read<{ items: Schema["Unit"][] }>("/manufacturing/units"),
        read<{ items: Schema["Lot"][] }>("/manufacturing/lots"),
        read<{ items: Schema["Order"][] }>("/erp/orders"),
      ]);
      if (ticket !== generation.current) return;
      setData({
        ...portfolio,
        programs: programs.items,
        units: units.items,
        lots: lots.items,
        orders: orders.items,
      });
      setFetchedAt(new Date().toISOString());
      setClock(Date.now());
      setError(false);
    } catch {
      if (ticket === generation.current) setError(true);
    } finally {
      if (ticket === generation.current) setLoading(false);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const timer = setInterval(() => setClock(Date.now()), 30000);
    return () => {
      ++generation.current;
      clearInterval(timer);
    };
  }, [refresh]);
  const freshness: Freshness = !data
    ? "Unavailable"
    : error || clock - Date.parse(fetchedAt) > 300000
      ? "Stale"
      : "Current read";
  return (
    <Context.Provider
      value={{ data, loading, error, fetchedAt, freshness, refresh }}
    >
      {children}
    </Context.Provider>
  );
}
export const useControl = () => useContext(Context);
export const programPath = (id: string) =>
  `/control/programs/${encodeURIComponent(id)}`;
export const casePath = (c: CaseData) =>
  `${programPath(c.change.program_id)}/cases/${encodeURIComponent(c.change.id)}`;
export const words = (value?: string | null) =>
  value
    ? value.replaceAll("_", " ").replace(/^./, (s) => s.toUpperCase())
    : "Unknown";
export const date = (value?: string | null, time = false) =>
  value
    ? new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        ...(time ? { hour: "2-digit", minute: "2-digit" } : {}),
        timeZone: "UTC",
      }).format(new Date(value)) + (time ? " UTC" : "")
    : "Unavailable";
export const money = (cents: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(cents / 100);
export const currentPlan = (c: CaseData) =>
  c.change.plans.find((p) => p.id === c.change.current_plan_id);
export function nextStep(c: CaseData) {
  if (["closed", "superseded"].includes(c.change.workflow_state))
    return "No new work authorized for this source change";
  if (c.change.execution_state === "lab_scheduled_pending_planner")
    return "Reconcile the scheduled job with Program Planner";
  if (c.change.execution_state === "scheduled_awaiting_execution")
    return "Await physical results and engineering review";
  if (currentPlan(c)?.state === "draft")
    return "Review the exact supplemental validation plan";
  if (currentPlan(c)?.state === "approved")
    return "Inspect the approved scope before scheduling";
  return (
    c.change.next_action || "Assess the requested evidence and validation scope"
  );
}
export function reason(c: CaseData) {
  if (c.change.execution_state === "lab_scheduled_pending_planner")
    return "Lab work is scheduled; Planner follow-through is missing.";
  if (c.change.execution_state === "scheduled_awaiting_execution")
    return "Scheduling is recorded; physical results remain pending.";
  if (currentPlan(c)?.state === "draft")
    return "An exact plan is waiting for engineering review.";
  if (currentPlan(c)?.state === "rejected")
    return "The recorded plan was rejected; scope needs reassessment.";
  return c.coverage.coverage_satisfied
    ? "Applicable evidence exists; engineering disposition is still separate."
    : "Existing evidence does not cover the requested requirement.";
}
export function ranked(cases: CaseData[]) {
  const priority = { critical: 0, high: 1, medium: 2, low: 3 };
  return cases
    .filter((c) => !["closed", "superseded"].includes(c.change.workflow_state))
    .sort(
      (a, b) =>
        Number(b.change.id === "CR-017") - Number(a.change.id === "CR-017") ||
        priority[a.change.priority || "medium"] -
          priority[b.change.priority || "medium"] ||
        a.change.request_received_at.localeCompare(
          b.change.request_received_at,
        ),
    );
}
// All four demo cases now resolve through connected source/host projections.
export const stories: {id:string;code:string;title:string;question:string;owner:string;summary:string;next:string;outcome:string}[] = [];
