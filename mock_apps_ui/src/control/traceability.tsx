import { Link } from "./access";
import type { HostSchema } from "./host";
import {
  sourceLabel,
  versionLabel,
  operationLabel,
  findingText,
  savedStandardFinding,
} from "./trace-language";

export function FindingSummary({
  summary,
  runId,
  role,
  status,
  handoff,
}: {
  summary?: string | null;
  runId: string;
  role: string;
  status: string;
  handoff?: HostSchema["StandardHandoff"];
}) {
  const generic =
    !summary || summary === "Exact source-backed standard package assessment.";
  const saved = generic
    ? savedStandardFinding(runId, role, status, handoff)
    : undefined;
  return (
    <>
      <RecordedText text={saved || findingText(summary)} />
      {saved && (
        <small>From policy checks saved with this investigation.</small>
      )}
      {generic && summary && (
        <details className="tr-details">
          <summary>Original recorded summary</summary>
          <p>{summary}</p>
        </details>
      )}
    </>
  );
}

export function RecordedText({
  text,
  label = "Full recorded finding",
}: {
  text: string;
  label?: string;
}) {
  // Excerpt, not generated paraphrase: preserve the complete original text.
  if (text.length <= 300) return <p className="tr-prose">{text}</p>;
  const boundary = text.slice(0, 300).lastIndexOf(". ");
  const space = text.lastIndexOf(" ", 280);
  const end = boundary > 90 ? boundary + 1 : space > 0 ? space : 280;
  return (
    <>
      <p className="tr-prose">
        {text.slice(0, end)}
        {boundary > 90 ? "" : "…"}
      </p>
      <details className="tr-details">
        <summary>{label}</summary>
        <p className="tr-prose">{text}</p>
      </details>
    </>
  );
}

export function SourceReferenceList({
  refs,
  href,
}: {
  refs: HostSchema["SourceReference"][];
  href?: (ref: HostSchema["SourceReference"]) => string | undefined;
}) {
  return (
    <ul className="tr-sources">
      {refs.map((r, i) => {
        const to = href?.(r);
        const name = sourceLabel(r.tool_name, r.record_id);
        return (
          <li key={`${r.source_id}-${i}`}>
            <div className="tr-source-heading">
              <strong>{to ? <Link to={to}>{name}</Link> : name}</strong>
              {r.record_id && <span>{r.record_id}</span>}
            </div>
            <details className="tr-details">
              <summary>Source record & versions</summary>
              <p>{operationLabel(r.tool_name)}</p>
              <p>{versionLabel(r.content_version, r.record_version)}</p>
              <dl className="tr-technical">
                <dt>Read operation</dt>
                <dd>{r.tool_name || "Not recorded"}</dd>
                <dt>Reference ID</dt>
                <dd>{r.source_id}</dd>
              </dl>
            </details>
          </li>
        );
      })}
    </ul>
  );
}
