import {
  Link as RouterLink,
  useResolvedPath,
  type LinkProps,
} from "react-router-dom";
import type { ReactNode } from "react";
import { useHost, type HostSchema, type HostCase } from "./host";

export type Capabilities = HostSchema["Capabilities"];
export type CaseAction = Capabilities["case_actions"][string][number];
export const canAct = (
  cap: Capabilities | null | undefined,
  caseId: string,
  action: CaseAction,
) => !!cap?.selected && !!cap.case_actions[caseId]?.includes(action);
export function routeAllowed(
  cap: Capabilities | null | undefined,
  path: string,
) {
  if (!cap) return false;
  const pathname = path.split(/[?#]/)[0].replace(/\/$/, "");
  if (!pathname.startsWith("/control")) return true; // Independent mock source-app boundary.
  const parts = pathname.split("/");
  const surface =
    (
      {
        portfolio: "overview",
        automations: "workflows",
        runs: "operations",
      } as Record<string, string>
    )[parts[2]] ||
    parts[2] ||
    "overview";
  if (!cap.surfaces.some((s) => s === surface)) return false;
  if (surface === "decisions" && parts[3])
    return cap.decision_kinds.includes(
      parts[3] === "evidence"
        ? "engineering_evidence"
        : "validation_authorization",
    );
  if (pathname.startsWith("/control/operations/demo")) return cap.demo_controls;
  return true;
}
export function accessibleHref(
  cap: Capabilities | null | undefined,
  data: HostCase | null | undefined,
  path: string,
) {
  if (routeAllowed(cap, path)) return path;
  if (!cap) return null;
  // Preserve scoped business reads when the general workspace is unavailable.
  if (path.startsWith("/control/decisions/"))
    return "/control/programs/PRG-A17/cases/CR-017?tab=options";
  if (path.startsWith("/control/runs/")) {
    const id = path.split("/")[3]?.split(/[?#]/)[0];
    const run = [
      ...(data?.runs || []),
      ...(data?.standard?.runs || []),
      ...(data?.quality?.runs || []),
      ...(data?.autonomous_quality?.runs || []),
      ...(data?.delivery?.runs || []),
    ].find((r) => r.run_id === id);
    return run
      ? `/control/programs/PRG-A17/cases/${run.change_id}?tab=activity&run=${id}`
      : null;
  }
  return null;
}
export function Link({ to, ...props }: LinkProps) {
  const host = useHost();
  const resolved = useResolvedPath(to);
  const path = resolved.pathname + resolved.search + resolved.hash;
  const target = accessibleHref(host?.capabilities, host?.data, path);
  return target ? <RouterLink {...props} to={target} /> : null;
}
export function AllowedAction({
  caseId,
  action,
  children,
}: {
  caseId: string;
  action: CaseAction;
  children: ReactNode;
}) {
  return canAct(useHost()?.capabilities, caseId, action) ? (
    <>{children}</>
  ) : null;
}
export const needsYourReview = (
  cap: Capabilities | null | undefined,
  d: HostSchema["DecisionSummary"],
) =>
  d.current &&
  d.requires_human &&
  canAct(
    cap,
    d.change_id,
    d.kind === "engineering_evidence" ? "review_evidence" : "review",
  );
