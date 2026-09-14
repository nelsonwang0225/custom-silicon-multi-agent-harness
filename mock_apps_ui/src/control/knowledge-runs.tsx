import { useEffect, useState } from "react";
import { Link } from "./access";
import { useHost, type HostSchema } from "./host";
import { Section, Empty, StatusText } from "./ui";
import { words, date } from "./data";
import { agentName, traceStatus } from "./trace-language";
import { RecordedText } from "./traceability";
export type KnowledgeEvent = HostSchema["KnowledgeEvent"];
export function KnowledgeRunEvidence({
  runId,
  caseId,
  detailed = false,
  onEvents,
}: {
  runId?: string;
  caseId?: string;
  detailed?: boolean;
  onEvents?: (events: KnowledgeEvent[]) => void;
}) {
  const host = useHost(),
    read = host?.read;
  const permitted = host?.capabilities?.surfaces.includes("knowledge");
  const [events, setEvents] = useState<KnowledgeEvent[] | null>(null),
    [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const query = runId
    ? `run_id=${encodeURIComponent(runId)}`
    : caseId
      ? `case_id=${encodeURIComponent(caseId)}`
      : "";
  useEffect(() => {
    let active = true;
    setEvents(null);
    setError("");
    if (read && permitted)
      read<KnowledgeEvent[]>(`/knowledge/events?${query}`)
        .then((v) => {
          if (active) {
            setEvents(v);
            onEvents?.(v);
          }
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [read, permitted, query, revision, host?.profile, onEvents]);
  if (!permitted) return null;
  return (
    <Section
      title={detailed ? "Documents the agents searched" : "Document evidence"}
      note="See why each document was retrieved, whether its source was checked, and whether the agent cited it."
    >
      <button onClick={() => setRevision((v) => v + 1)}>
        Refresh knowledge activity
      </button>
      {error ? (
        <p role="alert">{error}</p>
      ) : events === null ? (
        <Empty>Reading document search history…</Empty>
      ) : events.length === 0 ? (
        <Empty>
          No document search was recorded. The agents may have used the
          source-system records listed with their findings.
        </Empty>
      ) : (
        events.map((e) => (
          <article className="kn-run-event" key={e.event_id}>
            <div className="cp-inline">
              <strong>
                {agentName(e.specialist)}
                {e.session_id ? " · Concierge" : ""}
              </strong>
              <StatusText>{traceStatus(e.status)}</StatusText>
            </div>
            <span className="tr-label">What the agent looked for</span>
            <p>{e.query}</p>
            <span className="tr-label">Why it mattered</span>
            <RecordedText text={e.why_relevant} />
            <details className="tr-details">
              <summary>Search details</summary>
              <p>
                {agentName(e.profile.toLowerCase())} · {e.provider} ·{" "}
                {e.latency_ms.toFixed(0)} ms · {date(e.at, true)}
              </p>
              <p>Search profile: {e.profile}</p>
              <p>{e.event_id}</p>
            </details>
            {(e.passages || []).length === 0 && (
              <p>
                No eligible document passages were found. This search did not
                establish a policy conclusion.
              </p>
            )}
            {(e.passages || []).map((p) => (
              <div className="kn-run-passage" key={p.chunk_id}>
                <Link
                  to={`/control/knowledge?chunk=${encodeURIComponent(p.chunk_id)}`}
                >
                  {p.title} · v{p.document_version}
                </Link>
                <p>
                  {p.used_in_finding
                    ? "Used in the agent’s finding"
                    : "Found by search; not cited in the finding"}
                </p>
                <p>
                  {["verified", "exact_source_verified"].includes(
                    p.verification_state,
                  )
                    ? "Checked against the source document"
                    : `Source check: ${words(p.verification_state)}`}{" "}
                  ·{" "}
                  {p.metadata.historical
                    ? "Historical context"
                    : p.current
                      ? "Current when checked"
                      : "Older version or source changed"}
                </p>
                <details className="tr-details">
                  <summary>Passage and version details</summary>
                  <p>
                    {p.section || "Section not recorded"} ·{" "}
                    {words(p.metadata.approval_status)}
                  </p>
                  <p>
                    {p.metadata.program_id}
                    {p.metadata.configuration_id
                      ? ` · ${p.metadata.configuration_id}`
                      : " · Configuration not recorded"}
                  </p>
                  <p>
                    {p.chunk_id} · {p.verification_state}
                  </p>
                </details>
              </div>
            ))}
            {!runId && e.run_id && (
              <Link to={`/control/runs/${e.run_id}`}>Open recorded run →</Link>
            )}
          </article>
        ))
      )}
    </Section>
  );
}
