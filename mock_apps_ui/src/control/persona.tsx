import { ArrowRight, ShieldCheck, UserRound } from "lucide-react";
import { personas, type Persona } from "../api";
import { useHost } from "./host";
import { canAct, type CaseAction } from "./access";

export const CHOOSE_IDENTITY = "stratos:choose-identity";
// Display descriptions of the existing installed demo identities. No role is created here.
export const identityDetails: Record<
  Persona,
  { name: string; purpose: string; boundary: string }
> = {
  automation: {
    name: "demo-automation",
    purpose:
      "Investigate cases, prepare work and carry out exactly authorized actions.",
    boundary: "Cannot approve engineering evidence or commercial commitments.",
  },
  engineer: {
    name: "demo-engineer",
    purpose:
      "Review validation plans and exact engineering evidence; investigate changes.",
    boundary: "Customer acceptance and held-material release remain separate.",
  },
  program_owner: {
    name: "demo-program-owner",
    purpose:
      "Approve recovery plans and delivery commitments; investigate quality and delivery.",
    boundary: "Cannot release held material or approve engineering adequacy.",
  },
  reader: {
    name: "demo-reader",
    purpose: "Explore programs, evidence, decisions and recorded activity.",
    boundary: "Read-only access; cannot investigate, approve or execute.",
  },
};
export const identityOrder: Persona[] = [
  "automation",
  "engineer",
  "program_owner",
  "reader",
];
export function chooseIdentity(roles: Persona[] = []) {
  window.dispatchEvent(new CustomEvent(CHOOSE_IDENTITY, { detail: roles }));
}
export function ActionAccess({
  caseId,
  action,
  reason,
  ready = true,
}: {
  caseId: string;
  action: CaseAction;
  reason?: string;
  ready?: boolean;
}) {
  const host = useHost();
  const permitted = canAct(host?.capabilities, caseId, action);
  const roles = host?.capabilities?.action_roles[caseId]?.[action] || [];
  const state = host?.error
    ? "Source connection unavailable. Refresh before acting."
    : host?.busy
      ? "An action is in progress. Await its recorded result."
      : !ready
        ? reason || "A current source record is required."
        : null;
  if (!host?.capabilities || (permitted && !state)) return null;
  return (
    <div className="cp-action-access" role="status">
      <ShieldCheck size={17} aria-hidden="true" />
      <span>
        {permitted
          ? state
          : `Responsible role: ${roles.map((r) => personas[r as Persona]).join(" or ")}.`}
      </span>
    </div>
  );
}
export function IdentityChoices({
  profile,
  onProfile,
  recommended = [],
}: {
  profile: Persona | null;
  onProfile: (p: Persona) => void;
  recommended?: Persona[];
}) {
  return (
    <div className="cp-identity-choices">
      {identityOrder.map((id) => (
        <button
          key={id}
          aria-pressed={profile === id}
          onClick={() => onProfile(id)}
          className={recommended.includes(id) ? "cp-identity-recommended" : ""}
        >
          <UserRound size={23} />
          <span>
            <strong>{personas[id]}</strong>
            <small>
              {identityDetails[id].name}
              {profile === id ? " · Active identity" : ""}
            </small>
            <p>{identityDetails[id].purpose}</p>
            <small>{identityDetails[id].boundary}</small>
          </span>
          <ArrowRight size={17} />
        </button>
      ))}
    </div>
  );
}
