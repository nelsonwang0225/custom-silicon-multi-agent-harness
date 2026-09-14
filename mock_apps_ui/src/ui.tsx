import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  CheckCircle2,
  Circle,
  Clock3,
  OctagonAlert,
  Search,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api, enc, errorMessage, type Schema } from "./api";
import { FieldValue } from "./sources";
import { useData } from "./data";
export const human = (s: string) =>
  (/^[A-Z_]+$/.test(s) ? s.toLowerCase() : s)
    .replaceAll("_", " ")
    .replace(/^./, (c) => c.toUpperCase());
export const money = (c: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    c / 100,
  );
export const date = (s: string | null | undefined) =>
  s
    ? new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "UTC",
      }).format(new Date(s)) + " UTC"
    : "Not available";
export const number = (n: number) => n.toLocaleString("en-US");
export function Badge({ value, tone }: { value: string; tone?: string }) {
  const kind =
    tone ||
    (/critical|high|at_risk|validation_risk|blocked|constraint|hold|insufficient|ineligible|rejected|denied|missing|late|unavailable|not reassessed|not_reassessed/.test(
      value,
    )
      ? "warning"
      : /^(approved|linked|available|succeeded|on_track|completed|coverage satisfied|within delegated policy)$/.test(
            value,
          )
        ? "good"
        : /scheduled|draft|requested|pending/.test(value)
          ? "info"
          : "neutral");
  const Icon =
    kind === "good"
      ? CheckCircle2
      : kind === "warning" || kind === "danger"
        ? /hold/.test(value)
          ? OctagonAlert
          : AlertCircle
        : kind === "info"
          ? Clock3
          : Circle;
  return (
    <span className={"badge " + kind} data-state={value}>
      <Icon size={13} aria-hidden="true" />
      {human(value)}
    </span>
  );
}
export function Banner({
  children,
  tone = "info",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return (
    <div
      className={"banner " + tone}
      role={tone === "danger" ? "alert" : "status"}
    >
      {tone === "good" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
      <div>{children}</div>
    </div>
  );
}
export function Panel({
  title,
  aside,
  children,
  className = "",
  id,
}: {
  title: string;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={"panel " + className}>
      <div className="panel-heading">
        <h2>{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}
export function Heading({
  eyebrow,
  title,
  children,
  action,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        {children && <p>{children}</p>}
      </div>
      {action}
    </div>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}
export function Table({
  headers,
  children,
}: {
  headers: string[];
  children: ReactNode;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
export function Facts({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="facts">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}
export function SearchField({
  value,
  onChange,
  label = "Search records",
}: {
  value: string;
  onChange: (v: string) => void;
  label?: string;
}) {
  return (
    <label className="search">
      <Search size={17} />
      <input
        aria-label={label}
        placeholder={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
export function Fresh({
  record,
}: {
  record: { updated_at: string; content_version: number };
}) {
  return (
    <span className="metadata">
      Source refreshed {date(record.updated_at)} · Content v
      {record.content_version}
    </span>
  );
}
export function Reasons({ values }: { values: string[] }) {
  return values.length ? (
    <ul className="reasons">
      {values.map((v) => (
        <li key={v}>{human(v)}</li>
      ))}
    </ul>
  ) : (
    <span className="muted">No restrictions recorded</span>
  );
}
export function Timing({ timing }: { timing: Schema["Timing"] }) {
  return (
    <div className="timing">
      {[
        ["Setup starts", timing.lab_start_at],
        ["Execution starts", timing.execution_start_at],
        ["Reservation ends", timing.lab_end_at],
        ["Review ready", timing.review_ready_at],
      ].map(([k, v]) => (
        <div key={k}>
          <span>{k}</span>
          <strong>{date(v)}</strong>
        </div>
      ))}
    </div>
  );
}
export function Audit({ events }: { events: Schema["AuditEvent"][] }) {
  const { data } = useData();
  return events.length ? (
    <div className="activity">
      {[...events].reverse().map((e) => (
        <div className="event" key={e.id}>
          <span className="event-sequence">{e.sequence}</span>
          <div>
            <strong>{human(e.action)}</strong>
            <p>
              {e.actor_id || "Unknown actor"} · {e.domain}
            </p>
            <small>
              Scenario {date(e.scenario_at)}
              <br />
              {e.changes.provenance
                ? "Synthetic import timestamp "
                : "Recorded "}
              {date(e.wall_clock_at)}
            </small>
            {e.plan_id && (
              <Link
                className="record-link"
                to={"/engineering/plans/" + e.plan_id}
              >
                {e.plan_id}
              </Link>
            )}
            <details className="audit-details">
              <summary>Event details · {e.sequence}</summary>
              <Facts
                items={[
                  ["Event", e.id],
                  ["Request ID", e.request_id],
                  ["Correlation ID", e.correlation_id],
                  ["Idempotency hash", e.idempotency_hash || "Not supplied"],
                  ["Affected resource", e.resource_id || "Not recorded"],
                ]}
              />
              <div className="button-row">
                {data?.cases
                  .flatMap((c) => c.change.plans)
                  .filter(
                    (p) =>
                      p.decision_id &&
                      (p.decision_id === e.approval_id ||
                        p.decision_id === e.resource_id),
                  )
                  .map((p) => (
                    <Link
                      key={p.id}
                      to={
                        "/engineering/plans/" +
                        p.id +
                        "#decision-" +
                        p.decision_id
                      }
                    >
                      Open decision {p.decision_id}
                    </Link>
                  ))}
                {e.job_id &&
                  data?.cases.some((c) =>
                    c.jobs.some((j) => j.id === e.job_id),
                  ) && (
                    <Link to={"/validation/jobs/" + e.job_id}>
                      Open job {e.job_id}
                    </Link>
                  )}
                {data?.cases
                  .flatMap((c) => c.links)
                  .filter((l) => l.id === e.resource_id)
                  .map((l) => (
                    <Link
                      key={l.id}
                      to={"/programs/" + l.program_id + "#link-" + l.id}
                    >
                      Open Planner record {l.id}
                    </Link>
                  ))}
              </div>
              {Object.keys(e.changes).length ? (
                <Table
                  headers={["Recorded change", "Before / detail", "After"]}
                >
                  {Object.entries(e.changes).map(([key, value]) => (
                    <tr key={key}>
                      <td>{human(key)}</td>
                      <td>
                        <FieldValue
                          value={
                            Array.isArray(value) && value.length === 2
                              ? value[0]
                              : value
                          }
                        />
                      </td>
                      <td>
                        {Array.isArray(value) && value.length === 2 ? (
                          <FieldValue value={value[1]} />
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </Table>
              ) : (
                <p>
                  No field changes recorded for this event
                  {e.outcome === "replay"
                    ? "; the original action was recovered"
                    : ""}
                  .
                </p>
              )}
            </details>
          </div>
          <Badge value={e.outcome} />
        </div>
      ))}
    </div>
  ) : (
    <Empty>No activity recorded for this change.</Empty>
  );
}
export function DocumentView({ id }: { id: string }) {
  const { persona, fetchedAt } = useData();
  const [record, setRecord] = useState<Schema["Document"] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setRecord(null);
    setError("");
    api(persona)
      .get<Schema["Document"]>("/engineering/documents/" + enc(id))
      .then((d) => {
        if (active) setRecord(d);
      })
      .catch((e) => {
        if (active) setError(errorMessage(e));
      });
    return () => {
      active = false;
    };
  }, [id, persona, fetchedAt]);
  if (error) return <Banner tone="danger">{error}</Banner>;
  if (!record) return <Empty>Loading business document…</Empty>;
  return (
    <Panel
      title={human(record.document_type)}
      aside={<Badge value={record.status} />}
    >
      <div className="document-meta">
        {record.id} · Document v{record.document_version}
        <br />
        <Fresh record={record} />
      </div>
      <article className="markdown">
        <ReactMarkdown
          skipHtml
          components={{
            img: () => null,
            a: ({ children }) => <span>{children}</span>,
          }}
        >
          {record.content}
        </ReactMarkdown>
      </article>
    </Panel>
  );
}
