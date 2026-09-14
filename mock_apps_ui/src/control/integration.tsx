import { caseFact, caseNames, nextBusinessStep } from "./experience-model";
import { useControl } from "./data";
import { Link } from "./access";
import { ArrowRight } from "lucide-react";
import { useHost, type HostSchema } from "./host";
import { StatusText, Empty, Section, SourceLink } from "./ui";

export type CaseSummary = HostSchema["CaseSummary"];
export const caseTone = (
  value: CaseSummary,
): "danger" | "warning" | "good" | "neutral" =>
  value.attention === "failure"
    ? "danger"
    : value.attention !== "none"
      ? "warning"
      : ["completed_technical", "completed_recovery", "handoff_verified"].includes(value.state)
        ? "good"
        : "neutral";
export function ConnectedCases({ programId }: { programId: string }) {
  const host = useHost(),
    { data } = useControl();
  const cases =
    host?.data?.case_summaries?.filter((c) => c.program_id === programId) || [];
  if (!cases.length)
    return (
      <Empty>
        {programId !== "PRG-A17"
          ? "No connected workflow is configured for this program."
          : host?.error || "Reading connected case records…"}
      </Empty>
    );
  return (
    <div className="cp-connected-cards" aria-label="Connected workflow cases">
      {cases.map((c) => (
        <Link
          key={c.change_id}
          to={c.href}
          data-case-id={c.change_id}
          data-case-state={c.state}
        >
          <div className="cp-case-card-top">
            <small>{c.change_id}</small>
            <StatusText tone={host?.error ? "warning" : caseTone(c)}>
              {host?.error ? "Current state unavailable" : c.state_label}
            </StatusText>
          </div>
          <strong>{caseNames[c.change_id] || c.title}</strong>
          <p>
            {host?.error
              ? "Stale read · Refresh required"
              : caseFact(
                  host?.data,
                  c,
                  data?.cases.find((v) => v.change.id === c.change_id),
                )}
          </p>
          <div className="cp-case-card-next">
            <span>{nextBusinessStep(host?.data, c)}</span>
            <ArrowRight size={17} />
          </div>
        </Link>
      ))}
    </div>
  );
}
export function CaseStatePanel({ caseId }: { caseId: string }) {
  const host = useHost(),
    value = host?.data?.case_summaries?.find((c) => c.change_id === caseId);
  if (!value)
    return <Empty>{host?.error || "Reading current workflow state…"}</Empty>;
  return (
    <section
      className="cp-integrated-state"
      aria-label={`${caseId} current case state`}
      data-case-state={value.state}
    >
      <StatusText tone={host?.error ? "warning" : caseTone(value)}>
        {host?.error ? "Stale read · Refresh required" : value.state_label}
      </StatusText>
      <p>
        {host?.error
          ? "Last-read facts retained. Refresh current sources before acting."
          : value.detail}
      </p>
      <p>
        <strong>Next step:</strong> {value.next_action}
      </p>
      <small>{value.boundary}</small>
    </section>
  );
}
export function ProgramDependencies({ programId }: { programId: string }) {
  const host = useHost();
  if (programId !== "PRG-A17" || !host?.data?.dependencies?.length) return null;
  return (
    <Section
      title="Shared source dependencies"
      note="Relationships recorded in the current source scope."
    >
      {host.data.dependencies.map((d, i) => (
        <article className="cp-dependency" key={i}>
          <strong>
            {d.from_case ? (
              <>
                <Link
                  to={`/control/programs/${programId}/cases/${d.from_case}`}
                >
                  {d.from_case}
                </Link>{" "}
                →{" "}
              </>
            ) : (
              "Approved baseline → "
            )}
            <Link to={`/control/programs/${programId}/cases/${d.to_case}`}>
              {d.to_case}
            </Link>{" "}
            · {d.kind}
          </strong>
          <p>
            {d.source_available && !host.error
              ? d.detail
              : "Current dependency source unavailable; refresh required."}
          </p>
          <details>
            <summary>Source records</summary>
            <small>{d.source_ids.join(" · ")}</small>
          </details>
        </article>
      ))}
    </Section>
  );
}
