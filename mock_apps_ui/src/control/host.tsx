import { useLocation } from "react-router-dom";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { Persona } from "../api";
import { demoEpoch, observeDemoEpoch } from "../demo-epoch";
import type { components } from "./host-schema";
import { useControl } from "./data";
declare const __STRATOS_SOURCE_URL__: string;
export type HostSchema = components["schemas"];
export type HostCase = HostSchema["CaseView"];
export type HostProposal = HostSchema["ProposalView"];
export type ProposalRef = HostSchema["ProposalRef"];
export const connectedCasePath = "/control/programs/PRG-A17/cases/CR-017";
export const decisionPath = (p: HostProposal) =>
  `/control/decisions/${encodeURIComponent(p.proposal.proposal_id)}/${p.proposal.proposal_version}?digest=${p.proposal.proposal_digest}`;
export const reviewable = (p: HostProposal) =>
  p.current_check === "current" &&
  ["proposal_ready", "waiting_for_approval"].includes(p.effective_status) &&
  !p.review;
export const executionLabel = (p: HostProposal) =>
  p.execution.error_code === "VERIFICATION_MISMATCH"
    ? "Verification failed"
    : {
        completed_execution: "Execution verified",
        waiting_for_approval: "Waiting for human review",
        attention_required: "Reconciliation required",
        partially_executed: "Partially executed",
      }[p.effective_status] ||
      p.effective_status
        .replaceAll("_", " ")
        .replace(/^./, (s) => s.toUpperCase());
export const hostError = (code: string) =>
  ({
    WRONG_APPROVER:
      "Approval rejected: the authorized approver profile for this exact plan is required.",
    APPROVAL_REQUIRED:
      "Execution rejected: an exact approved proposal is required.",
    EXECUTION_ROLE_FORBIDDEN:
      "Select a permitted demo profile for this action. The decision card shows the required approver.",
    DEMO_IDENTITY_REQUIRED: "Select a demo identity using Log in.",
    WORKFLOW_CAPACITY_REACHED: "All investigation slots are in use. Your request was not started; retry when a run finishes.",
    RUN_ALREADY_RUNNING:
      "An investigation is already active. Refresh its recorded state.",
    CURRENT_PROPOSAL_EXISTS:
      "A current proposal already exists. Review it before preparing a replacement.",
    PROPOSAL_NOT_CURRENT:
      "This proposal is no longer current. Refresh and inspect its exact replacement.",
    SOURCE_READ_FAILED:
      "Source unavailable. Current authority could not be checked.",
    CONNECTION_INTERRUPTED:
      "Connection interrupted. The outcome is unknown; refresh records before retrying the same request.",
    HOST_UNAVAILABLE:
      "Control host unavailable. No current outcome is confirmed.",
    DEMO_STATE_CHANGED:
      "Demo state changed. This proposal or action is no longer current. Check Demo controls before continuing.",
    DEMO_RESET_RECONCILIATION_REQUIRED:
      "Demo reset is incomplete. Open Operations / Demo controls and retry the reset.",
  })[code] || code.replaceAll("_", " ");
class HostError extends Error {
  constructor(public code: string) {
    super(hostError(code));
  }
}
export async function call<T>(
  path: string,
  profile: Persona | null,
  body?: unknown,
): Promise<T> {
  const controller = new AbortController(),
    timer = setTimeout(() => controller.abort(), body ? 60000 : 15000);
  try {
    const response = await fetch("/control-api" + path, {
      method: body === undefined ? "GET" : "POST",
      signal: controller.signal,
      cache: "no-store",
      headers: {
        ...(demoEpoch() ? { "X-Stratos-Demo-Epoch": demoEpoch()! } : {}),
        ...(profile ? { "X-Stratos-Demo-Profile": profile } : {}),
        ...(body === undefined
          ? {}
          : { "Content-Type": "application/json", "X-Stratos-Action": "1" }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    observeDemoEpoch(response.headers.get("X-Stratos-Demo-Epoch"));
    const data = await response.json().catch(() => null);
    if (!response.ok || !data)
      throw new HostError(data?.error?.code || "HOST_UNAVAILABLE");
    return data as T;
  } catch (error) {
    if (error instanceof HostError) throw error;
    throw new HostError("CONNECTION_INTERRUPTED");
  } finally {
    clearTimeout(timer);
  }
}
type State = {
  data: HostCase | null;
  capabilities: HostSchema["Capabilities"] | null;
  error: string;
  busy: string;
  refreshing: boolean;
  profile: Persona | null;
  refresh: () => Promise<void>;
  read: <T>(path: string) => Promise<T>;
  act: <T>(path: string, body: unknown) => Promise<T>;
};
const Context = createContext<State | null>(null);
export function HostData({
  profile,
  children,
}: {
  profile: Persona | null;
  children: ReactNode;
}) {
  const location = useLocation();
  const [capabilities, setCapabilities] = useState<
    HostSchema["Capabilities"] | null
  >(null);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<HostCase | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState("");
  const active = useRef(true),
    locked = useRef(false),
    reading = useRef<Promise<void> | null>(null),
    fingerprint = useRef("");
  const { refresh: sourceRefresh } = useControl();
  const refresh = useCallback(async () => {
    if (reading.current) return reading.current;
    setRefreshing(true);
    const request = (async () => {
      try {
        const cap = await call<HostSchema["Capabilities"]>(
          "/capabilities",
          profile,
        );
        if (!active.current) return;
        setCapabilities(cap);
        const result = await call<HostCase>("/cases/CR-017", profile);
        if (!active.current) return;
        if (result.source_url !== __STRATOS_SOURCE_URL__) {
          setData(null);
          setError(
            "Host and source connections point to different local demos. Align their source URL before continuing.",
          );
          return;
        }
        setData(result);
        setError("");
        const next = JSON.stringify([
          result.runs.map((r) => [r.run_id, r.status]),
          result.standard,
          result.quality,
          result.autonomous_quality,
          result.delivery,
          result.downstream,
          result.proposals.map((p) => [
            p.proposal.proposal_digest,
            p.effective_status,
            p.execution.steps,
          ]),
        ]);
        if (fingerprint.current && next !== fingerprint.current)
          void sourceRefresh();
        fingerprint.current = next;
      } catch (e) {
        if (active.current) setError((e as Error).message);
      } finally {
        reading.current = null;
        if (active.current) setRefreshing(false);
      }
    })();
    reading.current = request;
    return request;
  }, [profile, sourceRefresh]);
  const read = useCallback(
    async <T,>(path: string) => {
      if (!active.current) throw new HostError("DEMO_IDENTITY_CHANGED");
      const result = await call<T>(path, profile);
      if (!active.current) throw new HostError("DEMO_IDENTITY_CHANGED");
      return result;
    },
    [profile],
  );
  const act = useCallback(
    async <T,>(path: string, body: unknown) => {
      if (!active.current) throw new HostError("DEMO_IDENTITY_CHANGED");
      if (locked.current) throw new HostError("RUN_ALREADY_RUNNING");
      locked.current = true;
      setBusy(path);
      try {
        const result = await call<T>(path, profile, body);
        if (!active.current) throw new HostError("DEMO_IDENTITY_CHANGED");
        return result;
      } finally {
        try {
          if (active.current) {
            // Finish any read started before the mutation, then fetch again.
            // Keep actions locked until this post-mutation read completes.
            if (reading.current) await reading.current;
            await refresh();
            if (!path.startsWith("/automations")) void sourceRefresh();
          }
        } finally {
          locked.current = false;
          if (active.current) setBusy("");
        }
      }
    },
    [profile, refresh, sourceRefresh],
  );
  const running =
    !![
      ...(data?.runs || []),
      ...(data?.standard?.runs || []),
      ...(data?.quality?.runs || []),
      ...(data?.autonomous_quality?.runs || []),
      ...(data?.delivery?.runs || []),
    ].some((r) => r.status === "running") || !!busy || !!data?.pending_source_event;
  useEffect(() => {
    active.current = true;
    return () => { active.current = false; };
  }, [profile]);
  useEffect(() => {
    void refresh();
    const timer = setInterval(
      () => {
        if (document.visibilityState === "visible") void refresh();
      },
      running ? 1500 : 15000,
    );
    const focus = () => void refresh();
    window.addEventListener("focus", focus);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", focus);
    };
  }, [refresh, running]);
  useEffect(() => {
    void refresh();
  }, [location.pathname, refresh]);
  return (
    <Context.Provider
      value={{
        data,
        capabilities,
        error,
        busy,
        refreshing,
        profile,
        refresh,
        read,
        act,
      }}
    >
      {children}
    </Context.Provider>
  );
}
export const useHost = () => useContext(Context);
