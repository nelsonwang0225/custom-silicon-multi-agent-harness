import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { api, enc, errorMessage, type Schema } from "./api";
import { useData, type Workspace } from "./data";
import { Banner, date, Empty, human, money } from "./ui";

type Ref = Schema["SourceRef"];
export const sourceKey = (s: Ref) => s.resource_type + "|" + s.resource_id;
const routes: Partial<Record<Ref["resource_type"], string>> = {
  "engineering.change": "/engineering/changes/",
  "engineering.requirement": "/engineering/requirements/",
  "engineering.configuration": "/engineering/configurations/",
  "engineering.workload": "/engineering/workloads/",
  "engineering.criteria": "/engineering/acceptance-criteria/",
  "engineering.procedure": "/engineering/procedures/",
  "engineering.policy": "/engineering/policies/",
  "engineering.document": "/engineering/documents/",
  "validation.result": "/validation/results/",
  "manufacturing.unit": "/manufacturing/units/",
  "manufacturing.lot": "/manufacturing/lots/",
  "erp.order": "/erp/orders/",
  "planner.program": "/programs/",
};

function embeddedSource(data: Workspace, ref: Ref): unknown {
  const options = data.cases.flatMap((c) => c.options);
  const records: Partial<Record<Ref["resource_type"], unknown[]>> = {
    "validation.slot": options.map((o) => o.slot),
    "validation.lab": options.map((o) => o.lab),
    "validation.sample": data.samples,
    "erp.rate": data.rates,
    "planner.milestone": data.cases.map((c) => c.milestone),
    "engineering.customer": data.programs.map((p) => ({
      id: p.customer_id,
      name: p.customer_name,
    })),
    "engineering.supplier": data.programs.map((p) => ({
      id: p.supplier_id,
      name: p.supplier_name,
    })),
  };
  return records[ref.resource_type]?.find(
    (r) => (r as { id: string }).id === ref.resource_id,
  );
}

/** Readable, escaped fields for optional source and audit drill-downs. */
export function FieldValue({
  value,
  name = "",
}: {
  value: unknown;
  name?: string;
}) {
  if (value === null || value === undefined)
    return <span className="muted">Not supplied</span>;
  if (typeof value === "boolean") return <>{value ? "Yes" : "No"}</>;
  if (typeof value === "number")
    return (
      <>
        {name.endsWith("_cents") ? money(value) : value.toLocaleString("en-US")}
      </>
    );
  if (typeof value === "string") {
    if (name === "content")
      return (
        <article className="markdown source-markdown">
          <ReactMarkdown
            skipHtml
            components={{
              img: () => null,
              a: ({ children }) => <span>{children}</span>,
            }}
          >
            {value}
          </ReactMarkdown>
        </article>
      );
    return (
      <span className="field-text">
        {name.endsWith("_at") ||
        ["effective_from", "effective_to"].includes(name)
          ? date(value)
          : value}
      </span>
    );
  }
  if (Array.isArray(value))
    return value.length ? (
      <ul className="field-list">
        {value.map((v, i) => (
          <li key={i}>
            <FieldValue value={v} />
          </li>
        ))}
      </ul>
    ) : (
      <span className="muted">None recorded</span>
    );
  return <RecordFields record={value as Record<string, unknown>} />;
}

export function RecordFields({ record }: { record: Record<string, unknown> }) {
  return (
    <dl className="source-fields">
      {Object.entries(record)
        .filter(
          ([key]) =>
            ![
              "content_hash",
              "content_digest",
              "plans",
              "source_snapshot",
              "configuration_snapshot",
              "workload_snapshot",
              "criteria_snapshot",
            ].includes(key),
        )
        .map(([key, value]) => (
          <div key={key}>
            <dt>{human(key)}</dt>
            <dd>
              <FieldValue name={key} value={value} />
            </dd>
          </div>
        ))}
    </dl>
  );
}

export function SourceReference({
  source,
  snapshot,
  expectedVersion,
}: {
  source: Ref;
  snapshot?: Schema["Snapshot"];
  expectedVersion?: number;
}) {
  const { data, persona, fetchedAt } = useData();
  const [open, setOpen] = useState(false);
  const [record, setRecord] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!open || snapshot) return;
    let active = true;
    setError("");
    setRecord(null);
    const route = routes[source.resource_type];
    const read = route
      ? api(persona).get<Record<string, unknown>>(
          route + enc(source.resource_id),
        )
      : Promise.resolve(
          embeddedSource(data!, source) as Record<string, unknown> | undefined,
        );
    read
      .then((r) => {
        if (!active) return;
        if (r) setRecord(r);
        else
          setError(
            "This source is not available in the retrieved workspace. Refresh its source system.",
          );
      })
      .catch((e) => {
        if (active) setError(errorMessage(e));
      });
    return () => {
      active = false;
    };
  }, [
    open,
    source.resource_id,
    source.resource_type,
    snapshot,
    persona,
    fetchedAt,
    data,
  ]);
  const content = snapshot?.content || record;
  const version = snapshot?.content_version ?? record?.content_version;
  return (
    <details
      className="source-reference"
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary>Preview {source.resource_id}</summary>
      {open && (
        <div className="source-preview">
          <p className="metadata">
            {human(source.resource_type)} ·{" "}
            {snapshot
              ? "Captured with this immutable plan"
              : "Current source record"}
            {version
              ? " · Content v" + version
              : " · Name from program directory"}
          </p>
          {!snapshot &&
            !!expectedVersion &&
            typeof version === "number" &&
            version !== expectedVersion && (
              <Banner tone="warning">
                Source content changed since the option was retrieved. Refresh
                and reassess before submitting.
              </Banner>
            )}
          {error ? (
            <Banner tone="danger">{error}</Banner>
          ) : content ? (
            source.resource_type === "engineering.document" &&
            typeof content.content === "string" ? (
              <>
                <FieldValue name="content" value={content.content} />
                <details>
                  <summary>Source metadata</summary>
                  <RecordFields
                    record={Object.fromEntries(
                      Object.entries(content).filter(
                        ([key]) => key !== "content",
                      ),
                    )}
                  />
                </details>
              </>
            ) : (
              <RecordFields record={content} />
            )
          ) : (
            <Empty>Retrieving source…</Empty>
          )}
          {source.resource_type === "engineering.document" && (
            <Link to={"/engineering/documents/" + source.resource_id}>
              Open current document
            </Link>
          )}
        </div>
      )}
    </details>
  );
}
