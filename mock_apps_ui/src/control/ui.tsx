import { Dialog } from "./dialog";
import { type ReactNode } from "react";
import { Link } from "./access";
import { ArrowUpRight, ChevronRight, Info, RefreshCw } from "lucide-react";
import { date, useControl, type ExecutionMode } from "./data";
export function StatusText({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "warning" | "good" | "danger" | "agent" | "action";
}) {
  return <span className={`cp-status cp-${tone}`}>{children}</span>;
}
export function Truth({
  mode = "Connected demo",
  recorded = false,
}: {
  mode?: ExecutionMode;
  recorded?: boolean;
}) {
  const { freshness } = useControl();
  return (
    <div className="cp-truth">
      <span>Synthetic demo data</span>
      <StatusText>
        {mode}
        {mode === "Connected demo" ? " · read only" : ""}
      </StatusText>
      <span>
        {mode === "Preview only"
          ? "Freshness unavailable · preview"
          : recorded && freshness === "Current read"
            ? "Recorded result"
            : freshness}
      </span>
    </div>
  );
}
export function Heading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="cp-heading">
      <div>
        {eyebrow && <div className="cp-eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="cp-heading-action">{action}</div>}
    </div>
  );
}
export function Section({
  id,
  title,
  note,
  action,
  children,
  className = "",
}: {
  id?: string;
  title: string;
  note?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`cp-section ${className}`}>
      <div className="cp-section-heading">
        <div>
          <h2>{title}</h2>
          {note && <p>{note}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function SourceLink({
  to,
  children,
}: {
  to: string;
  children: ReactNode;
}) {
  return (
    <Link className="cp-text-link" to={to}>
      {children}
      <ArrowUpRight size={14} aria-hidden="true" />
    </Link>
  );
}
export function Crumbs({ items }: { items: { label: string; to?: string }[] }) {
  return (
    <nav className="cp-crumbs" aria-label="Breadcrumb">
      {items.map((v, i) => (
        <span key={i}>
          {i > 0 && <ChevronRight size={13} aria-hidden="true" />}
          {v.to ? (
            <Link to={v.to}>{v.label}</Link>
          ) : (
            <span aria-current="page">{v.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
export function Notice({ children }: { children: ReactNode }) {
  return (
    <div className="cp-notice">
      <Info size={17} aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return <div className="cp-empty">{children}</div>;
}
export function SourceState({ children }: { children: ReactNode }) {
  const { data, loading, refresh } = useControl();
  if (!data)
    return (
      <Empty>
        {loading ? (
          "Reading source records…"
        ) : (
          <>
            Source records are unavailable.{" "}
            <button onClick={() => void refresh()}>Retry source reads</button>
          </>
        )}
      </Empty>
    );
  return <>{children}</>;
}
export function Facts({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <dl className="cp-facts">
      {rows.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}
export function Steps({
  steps,
  className = "",
}: {
  className?: string;
  steps: {
    label: string;
    detail: string;
    state?: "current" | "done" | "pending";
    to?: string;
  }[];
}) {
  return (
    <ol className={`cp-steps ${className}`}>
      {steps.map((s, i) => (
        <li key={s.label} className={`cp-step-${s.state || "pending"}`}>
          <span className="cp-step-number" aria-hidden="true">
            {i + 1}
          </span>
          <div>
            {s.to ? (
              <Link to={s.to}>{s.label}</Link>
            ) : (
              <strong>{s.label}</strong>
            )}
            <small>{s.detail}</small>
          </div>
        </li>
      ))}
    </ol>
  );
}
export function Drawer({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  return (
    <Dialog title={title} close={close} closeLabel="Close evidence">
      {children}
    </Dialog>
  );
}
export function ReadStamp() {
  const { fetchedAt, freshness } = useControl();
  return (
    <span>
      {freshness} · {fetchedAt ? date(fetchedAt, true) : "No successful read"}
    </span>
  );
}

// Shared source context; the Overview places it beside its page title.
export function SourceContext() {
  const { data, loading, freshness, fetchedAt, refresh } = useControl();
  return (
    <div className="cp-connection">
      <details className="cp-data-context">
        <summary>Connected demo · {loading ? "Reading…" : freshness}</summary>
        <dl>
          <div>
            <dt>Origin</dt>
            <dd>Synthetic Stratos source records · read only</dd>
          </div>
          <div>
            <dt>Scenario time</dt>
            <dd>{date(data?.programs[0]?.scenario_at, true)}</dd>
          </div>
          <div>
            <dt>Actual source read</dt>
            <dd>{fetchedAt ? date(fetchedAt, true) : "Unavailable"}</dd>
          </div>
          <div>
            <dt>Freshness</dt>
            <dd>
              {freshness}. Reads become stale after five minutes or a failed
              refresh. All times UTC.
            </dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>
              Mock reader identity; no investigation or business writes.
              Recorded evidence retains its own timestamp.
            </dd>
          </div>
        </dl>
      </details>
      <button
        onClick={() => void refresh()}
        disabled={loading}
        aria-label="Refresh source records"
      >
        <RefreshCw size={13} className={loading ? "cp-spin" : ""} />
        <span>Refresh</span>
      </button>
    </div>
  );
}
