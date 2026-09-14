import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";
import { api, enc, errorMessage, type Persona, type Schema } from "./api";
type Items<T> = { items: T[] };
export type Case = {
  physical?: Schema["PhysicalValidation"];
  change: Schema["ChangeView"];
  baseline: Schema["Requirement"];
  target: Schema["Requirement"];
  baselineWorkload: Schema["Workload"];
  targetWorkload: Schema["Workload"];
  config: Schema["Configuration"];
  coverage: Schema["Coverage"];
  options: Schema["Option"][];
  milestone: Schema["Milestone"];
  jobs: Schema["JobView"][];
  links: Schema["LinkView"][];
  audit: Schema["AuditEvent"][];
  procedures: Schema["Procedure"][];
  policies: Schema["Policy"][];
  criteria: Schema["Criteria"];
};
export type Workspace = {
  programs: Schema["ProgramSummary"][];
  cases: Case[];
  units: Schema["Unit"][];
  lots: Schema["Lot"][];
  orders: Schema["Order"][];
  rates: Schema["Rate"][];
  samples: Schema["Sample"][];
  documents: Schema["DocumentMetadata"][];
  milestones: Schema["Milestone"][];
  slots: Schema["Slot"][];
  labs: Schema["Lab"][];
  history: Schema["HistoricalJob"][];
  activity: Schema["AuditEvent"][];
};
async function load(persona: Persona, route: string): Promise<Workspace> {
  const { get } = api(persona);
  const [programs, changes, units, lots, orders] = await Promise.all([
    get<Items<Schema["ProgramSummary"]>>("/programs"),
    get<Items<Schema["Change"]>>("/engineering/changes"),
    get<Items<Schema["Unit"]>>("/manufacturing/units"),
    get<Items<Schema["Lot"]>>("/manufacturing/lots"),
    get<Items<Schema["Order"]>>("/erp/orders"),
  ]);
  const portfolio = await get<Schema["Portfolio"]>("/portfolio");
  const requested = decodeURIComponent(route);
  const selected =
    portfolio.cases.find(
      (c) =>
        requested.includes(c.change.id) ||
        c.change.plans.some((p) => requested.includes(p.id)) ||
        c.jobs.some((j) => requested.includes(j.id)),
    ) || portfolio.cases[0];
  const cases = await Promise.all(
    changes.items
      .filter((change) => change.id === selected?.change.id)
      .map(async (change) => {
        const q = `?change_id=${enc(change.id)}`;
        const [
          full,
          baseline,
          target,
          config,
          coverage,
          options,
          milestone,
          jobs,
          links,
          audit,
          physical,
        ] = await Promise.all([
          get<Schema["ChangeView"]>(`/engineering/changes/${enc(change.id)}`),
          get<Schema["Requirement"]>(
            `/engineering/requirements/${enc(change.baseline_requirement_revision_id)}`,
          ),
          get<Schema["Requirement"]>(
            `/engineering/requirements/${enc(change.proposed_requirement_revision_id)}`,
          ),
          get<Schema["Configuration"]>(
            `/engineering/configurations/${enc(change.configuration_id)}`,
          ),
          get<Schema["Coverage"]>("/validation/coverage" + q),
          get<Schema["Options"]>("/validation/options" + q),
          get<Schema["Milestone"]>(
            `/programs/${enc(change.program_id)}/milestones/${enc(change.milestone_id)}`,
          ),
          get<Items<Schema["JobView"]>>("/validation/jobs" + q),
          get<Items<Schema["LinkView"]>>(
            `/programs/${enc(change.program_id)}/implementation-links` + q,
          ),
          get<Items<Schema["AuditEvent"]>>("/audit/events" + q),
          change.id === "CR-017"
            ? get<Schema["PhysicalValidation"]>("/validation/changes/CR-017/physical-validation")
            : Promise.resolve(undefined),
        ]);
        const [
          baselineWorkload,
          targetWorkload,
          criteria,
          procedures,
          policies,
        ] = await Promise.all([
          get<Schema["Workload"]>(
            `/engineering/workloads/${enc(baseline.workload_profile_id)}`,
          ),
          get<Schema["Workload"]>(
            `/engineering/workloads/${enc(target.workload_profile_id)}`,
          ),
          get<Schema["Criteria"]>(
            `/engineering/acceptance-criteria/${enc(target.acceptance_limits_ref)}`,
          ),
          Promise.all(
            [...new Set(options.items.map((o) => o.procedure_id))].map((id) =>
              get<Schema["Procedure"]>(`/engineering/procedures/${enc(id)}`),
            ),
          ),
          Promise.all(
            [...new Set(options.items.map((o) => o.policy_id))].map((id) =>
              get<Schema["Policy"]>(`/engineering/policies/${enc(id)}`),
            ),
          ),
        ]);
        return {
          change: full,
          physical,
          baseline,
          target,
          config,
          baselineWorkload,
          targetWorkload,
          coverage,
          options: options.items,
          milestone,
          jobs: jobs.items,
          links: links.items,
          audit: audit.items,
          criteria,
          procedures,
          policies,
        };
      }),
  );
  return {
    programs: programs.items,
    cases: portfolio.cases.map(
      (c) => cases.find((detail) => detail.change.id === c.change.id) || c,
    ),
    units: units.items,
    lots: lots.items,
    orders: orders.items,
    rates: portfolio.rates,
    samples: portfolio.samples,
    documents: portfolio.documents,
    milestones: portfolio.milestones,
    slots: portfolio.slots,
    labs: portfolio.labs,
    history: portfolio.history,
    activity: portfolio.activity,
  };
}
const Context = createContext<{
  data: Workspace | null;
  persona: Persona;
  setPersona: (p: Persona) => void;
  refresh: () => Promise<boolean>;
  changed: () => Promise<boolean>;
  loading: boolean;
  error: string;
  fetchedAt: string;
}>(null!);
export function DataProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const route = location.pathname + location.search;
  const [persona, select] = useState<Persona>(() => {
    const p = sessionStorage.getItem("demo-persona");
    return p === "automation" || p === "engineer" ? p : "reader";
  });
  const [data, setData] = useState<Workspace | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [fetchedAt, setFetchedAt] = useState("");
  const generation = useRef(0);
  const latestRefresh = useRef<Promise<boolean> | null>(null);
  const refresh = useCallback(async () => {
    const ticket = ++generation.current;
    setLoading(true);
    const run = async (): Promise<boolean> => {
      try {
        const next = await load(persona, route);
        if (ticket === generation.current) {
          setData(next);
          setError("");
          setFetchedAt(new Date().toISOString());
        }
        // A focus/visibility refresh can supersede a mutation's refresh. Await
        // that newer outcome instead of confirming an obsolete snapshot or
        // incorrectly reporting a healthy refresh as a failed write.
        return ticket === generation.current
          ? true
          : (latestRefresh.current ?? false);
      } catch (e) {
        if (ticket === generation.current) setError(errorMessage(e));
        return ticket === generation.current
          ? false
          : (latestRefresh.current ?? false);
      } finally {
        if (ticket === generation.current) setLoading(false);
      }
    };
    latestRefresh.current = run();
    return latestRefresh.current;
  }, [persona, route]);
  useEffect(() => {
    void refresh();
    const focus = () => void refresh();
    const visibility = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    window.addEventListener("focus", focus);
    document.addEventListener("visibilitychange", visibility);
    const channel = new BroadcastChannel("mock-business-refresh");
    channel.onmessage = focus;
    return () => {
      ++generation.current;
      latestRefresh.current = null;
      window.removeEventListener("focus", focus);
      document.removeEventListener("visibilitychange", visibility);
      channel.close();
    };
  }, [refresh]);
  const changed = async () => {
    const channel = new BroadcastChannel("mock-business-refresh");
    channel.postMessage("refresh");
    channel.close();
    return refresh();
  };
  const setPersona = (p: Persona) => {
    sessionStorage.setItem("demo-persona", p);
    select(p);
  };
  return (
    <Context.Provider
      value={{
        data,
        persona,
        setPersona,
        refresh,
        changed,
        loading,
        error,
        fetchedAt,
      }}
    >
      {children}
    </Context.Provider>
  );
}
export const useData = () => useContext(Context);
export function useFormState<T>(
  key: string,
  initial: T,
): [T, (value: T) => void] {
  const [value, set] = useState<T>(() => {
    try {
      return (
        JSON.parse(sessionStorage.getItem("form:" + key) || "null") ?? initial
      );
    } catch {
      return initial;
    }
  });
  return [
    value,
    (next: T) => {
      set(next);
      sessionStorage.setItem("form:" + key, JSON.stringify(next));
    },
  ];
}
