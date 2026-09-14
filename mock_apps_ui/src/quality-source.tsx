import { useEffect, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { request } from "./api";
import type { HostSchema } from "./control/host";
import {
  Badge,
  Banner,
  date,
  Empty,
  Facts,
  Fresh,
  Heading,
  human,
  Panel,
  Table,
} from "./ui";
import "./source-operations.css";

const usd = (cents: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(cents / 100);
const percent = (bps: number) => `${Number((bps / 100).toFixed(2))}%`;
const sourceDate = (value: unknown) =>
  date(typeof value === "string" ? value : null);

function ApprovedWork({
  records,
  system,
}: {
  records: HostSchema["QualityRecords"];
  system: "manufacturing" | "engineering" | "planner";
}) {
  const task = records.tasks.at(-1);
  const work = (task?.workstreams ?? []).filter(
    (item) => item.source_system === system,
  );
  if (!task || !work.length) return null;
  return (
    <Panel title="Approved downstream work" className="source-record-section">
      <p className="padded source-boundary">
        Assigned work from the exact Program Owner decision. Physical execution
        and Quality disposition remain separate.
      </p>
      <div className="source-work-list">
        {work.map((item) => (
          <article key={item.id}>
            <div className="source-work-heading">
              <h3>{item.objective}</h3>
              <Badge value={item.status} />
            </div>
            <p className="muted">{item.owner}</p>
            <ul>
              {item.actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
            <p>
              <strong>Complete when:</strong> {item.completion_criteria}
            </p>
          </article>
        ))}
      </div>
    </Panel>
  );
}

function QualityManufacturing({
  data,
  records,
}: {
  data: HostSchema["QualityContext"];
  records: HostSchema["QualityRecords"];
}) {
  const analysis = data.analysis;
  const affected = data.material.find(
    (m) => m.lot_id === data.exception.lot_id,
  );
  const observedBps =
    analysis?.observed_rate_bps ??
    (data.observation.tested_quantity > 0
      ? (data.observation.passed_quantity / data.observation.tested_quantity) *
        10000
      : null);
  const baselineBps =
    analysis?.baseline_rate_bps ??
    (data.baseline && data.baseline.tested_quantity > 0
      ? (data.baseline.passed_quantity / data.baseline.tested_quantity) * 10000
      : null);
  const comparable = analysis?.comparable === "true";
  const delta =
    comparable && observedBps != null && baselineBps != null
      ? (observedBps - baselineBps) / 100
      : null;
  const sites = Object.entries(analysis?.failed_by_site ?? {});
  return (
    <>
      <section
        className={
          "mes-lot-focus " + (affected?.disposition === "hold" ? "is-held" : "")
        }
        aria-label="Quality exception and affected lot"
      >
        <div className="mes-lot-identity">
          <span className="source-field-label">Affected lot</span>
          <h2>{data.exception.lot_id}</h2>
          <p>
            {affected
              ? `${affected.physical_quantity.toLocaleString()} units`
              : "Quantity not supplied"}{" "}
            · {data.observation.product_revision}
          </p>
          <span
            className={
              "mes-disposition " +
              (affected?.disposition === "hold" ? "held" : "")
            }
          >
            {affected
              ? affected.disposition.toUpperCase()
              : "DISPOSITION UNKNOWN"}
          </span>
          <small>
            {affected?.held_quantity ?? "Unknown"} held ·{" "}
            {affected?.eligible_unallocated_quantity ?? "Unknown"} eligible
          </small>
        </div>
        <div
          className="mes-yield-comparison"
          aria-label="First-pass yield comparison"
        >
          <div className="mes-yield-numbers">
            <div>
              <span>First-pass yield</span>
              <strong>
                {observedBps == null ? "Unknown" : percent(observedBps)}
              </strong>
              <small>
                {data.observation.passed_quantity} /{" "}
                {data.observation.tested_quantity} passed
              </small>
            </div>
            <div>
              <span>
                {comparable ? "Comparable baseline" : "Baseline reference"}
              </span>
              <strong>
                {baselineBps == null ? "Unknown" : percent(baselineBps)}
              </strong>
              <small>{data.baseline?.id || "No baseline supplied"}</small>
            </div>
            <div className={delta != null && delta < 0 ? "yield-below" : ""}>
              <span>Difference</span>
              <strong>
                {delta == null
                  ? "—"
                  : `${delta > 0 ? "+" : ""}${Number(delta.toFixed(2))}`}
                <em>{delta == null ? "" : " pts"}</em>
              </strong>
              <small>
                {comparable
                  ? "Comparable populations"
                  : "Comparison not established"}
              </small>
            </div>
          </div>
          <div className="mes-yield-bars" aria-hidden="true">
            <span>Observed</span>
            <div>
              <i
                style={{
                  width: `${Math.max(0, Math.min(100, (observedBps ?? 0) / 100))}%`,
                }}
              />
            </div>
            <span>Baseline</span>
            <div className="baseline">
              <i
                style={{
                  width: `${Math.max(0, Math.min(100, (baselineBps ?? 0) / 100))}%`,
                }}
              />
            </div>
          </div>
        </div>
      </section>
      <nav className="source-anchor-nav" aria-label="Quality record sections">
        <a href="#quality-observation">Observation</a>
        <a href="#quality-material">Material</a>
        <a href="#quality-investigations">Investigations</a>
        <a href="#quality-decisions">Recovery & decisions</a>
        <a href="#quality-traceability">Traceability</a>
      </nav>
      <div className="mes-observation-grid" id="quality-observation">
        <Panel title="Observed facts">
          <p className="padded">{data.exception.summary}</p>
          <Facts
            items={[
              ["Test stage", human(data.observation.test_stage)],
              ["Test program", data.observation.test_program_version],
              ["Configuration", data.observation.configuration_id],
              ["Observation", data.observation.id],
            ]}
          />
        </Panel>
        <Panel title="Signals & hypotheses">
          {sites.length > 0 && (
            <Table headers={["Test site", "First-pass failures"]}>
              {sites.map(([site, failed]) => (
                <tr key={site}>
                  <td>{site}</td>
                  <td className="numeric">{failed}</td>
                </tr>
              ))}
            </Table>
          )}
          <div className="mes-root-cause">
            <span className="source-field-label">Root cause</span>
            <strong>{data.observation.root_cause || "Not established"}</strong>
            <p>Site-level counts do not establish a physical cause.</p>
          </div>
        </Panel>
      </div>
      <Panel
        title="Quality exception & material"
        id="quality-material"
        aside={
          <span className="source-field-label">Manufacturing disposition</span>
        }
      >
        <Table
          headers={[
            "Lot / material",
            "Disposition",
            "Physical",
            "First-pass passes",
            "Released",
            "Held",
            "Allocated",
            "Eligible unallocated",
          ]}
        >
          {data.material.map((m) => (
            <tr
              key={m.id}
              className={m.disposition === "hold" ? "material-held" : ""}
            >
              <td>
                <strong>{m.lot_id}</strong>
                <span className="cell-secondary">{m.id}</span>
              </td>
              <td>
                <Badge
                  value={m.disposition}
                  tone={
                    m.disposition === "hold"
                      ? "warning"
                      : m.disposition === "released"
                        ? "good"
                        : "neutral"
                  }
                />
              </td>
              <td className="numeric">
                {m.physical_quantity.toLocaleString()}
              </td>
              <td className="numeric">
                {m.first_pass_pass_quantity.toLocaleString()}
              </td>
              <td className="numeric">
                {m.released_quantity.toLocaleString()}
              </td>
              <td className="numeric">{m.held_quantity.toLocaleString()}</td>
              <td className="numeric">
                {m.allocated_quantity.toLocaleString()}
              </td>
              <td className="numeric strong-number">
                {m.eligible_unallocated_quantity.toLocaleString()}
              </td>
            </tr>
          ))}
        </Table>
        <p className="padded source-boundary">
          First-pass passes do not release held material.
        </p>
      </Panel>
      <Panel
        title="Quality investigations"
        id="quality-investigations"
        aside={
          <span className="source-field-label">
            {records.investigations.length} recorded
          </span>
        }
      >
        {!records.investigations.length && (
          <Empty>No investigation routed yet.</Empty>
        )}
        <div className="source-work-list">
          {records.investigations.map((i) => (
            <article key={i.id}>
              <div className="source-work-heading">
                <h3>{i.id}</h3>
                <Badge value={i.status} />
              </div>
              <Facts
                items={[
                  ["Owner", i.owner],
                  ["Queue", i.queue_id],
                  ["Lot", i.lot_id],
                  ["Observation", i.observation_id],
                ]}
              />
              <ul>
                {i.tasks.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
              <Fresh record={i} />
            </article>
          ))}
        </div>
      </Panel>
      <Panel title="Recovery plans & human decisions" id="quality-decisions">
        {!records.plans.length && <Empty>No recovery plan recorded.</Empty>}
        <div className="source-work-list">
          {records.plans.map((p) => (
            <article key={p.id}>
              <div className="source-work-heading">
                <h3>
                  {p.id} · v{p.plan_version}
                </h3>
                <span className="source-field-label">Exact plan</span>
              </div>
              {(() => {
                const decision = records.decisions.find(
                  (d) => d.plan_id === p.id,
                );
                return decision ? (
                  <>
                    <p>
                      <Badge value={decision.decision} />{" "}
                      <span>{decision.signer_identity}</span>
                    </p>
                    <details className="source-record-disclosure" open>
                      <summary>Approved recommendation</summary>
                      {(
                        decision.recommendation ||
                        "No recommendation text recorded."
                      )
                        .split("\n\n")
                        .map((part) => (
                          <p key={part}>{part}</p>
                        ))}
                    </details>
                  </>
                ) : (
                  <p>Awaiting Program Owner review</p>
                );
              })()}
            </article>
          ))}
        </div>
      </Panel>
      <ApprovedWork records={records} system="manufacturing" />
      <Panel title="Traceability" id="quality-traceability">
        <div className="source-record-chain">
          <div>
            <span>Lot</span>
            <strong>{data.exception.lot_id}</strong>
          </div>
          <span aria-hidden="true">→</span>
          <div>
            <span>Test observation</span>
            <strong>{data.observation.id}</strong>
          </div>
          <span aria-hidden="true">→</span>
          <div>
            <span>Quality exception</span>
            <strong>{data.exception.id}</strong>
          </div>
          <span aria-hidden="true">→</span>
          <Link to={`/engineering/quality/${data.exception.id}`}>
            <span>Investigation procedure · PLM</span>
            <strong>{data.exception.investigation_procedure_id}</strong>
          </Link>
        </div>
        <Facts
          items={[
            [
              "Program",
              <Link to={`/programs/${data.program_id}`}>
                {data.program_id}
              </Link>,
            ],
            [
              "Customer demand · ERP",
              <Link to={`/erp/quality/${data.exception.id}`}>
                {data.exception.order_id}
              </Link>,
            ],
            [
              "Milestone · ProgramOps",
              <Link to={`/programs/quality/${data.exception.id}`}>
                {data.exception.milestone_id}
              </Link>,
            ],
            ["Received", date(data.exception.received_at)],
          ]}
        />
      </Panel>
    </>
  );
}

export function QualitySource() {
  const caseId =
    useLocation().pathname.split("/").at(-1) === "QE-011" ? "QE-011" : "QE-004";
  const system = useLocation().pathname.split("/")[1];
  const [data, setData] = useState<HostSchema["QualityContext"] | null>(null),
    [records, setRecords] = useState<HostSchema["QualityRecords"] | null>(null),
    [error, setError] = useState("");
  const load = () => {
    setError("");
    Promise.all([
      request<HostSchema["QualityContext"]>(
        `/manufacturing/quality-exceptions/${caseId}/context`,
        "reader",
      ),
      request<HostSchema["QualityRecords"]>(
        `/manufacturing/quality-exceptions/${caseId}/records`,
        "reader",
      ),
    ])
      .then(([c, r]) => {
        setData(c);
        setRecords(r);
      })
      .catch(() => setError("Current quality source unavailable."));
  };
  useEffect(load, [caseId]);
  const current =
    data?.exception_id === caseId && records?.exception_id === caseId;
  return (
    <div className="source-record-page quality-source-page">
      <Heading
        eyebrow={
          system === "manufacturing"
            ? "Quality management / Exception record"
            : "Related source records / Quality"
        }
        title={`${caseId} · Source records`}
        action={<button onClick={load}>Refresh source records</button>}
      >
        {current && data ? (
          <>
            <Link to={`/programs/${data.program_id}`}>{data.program_id}</Link> ·{" "}
            {data.exception.configuration_id} ·{" "}
            <Fresh record={data.exception} />
          </>
        ) : (
          "Manufacturing quality exception"
        )}
      </Heading>
      {error && <Banner tone="danger">{error}</Banner>}
      {!current && !error && <Empty>Loading quality source records…</Empty>}
      {current && data && records && (
        <>
          {system === "manufacturing" && (
            <QualityManufacturing data={data} records={records} />
          )}
          {system === "engineering" && (
            <>
              <Panel
                title="Approved investigation procedure"
                aside={<Badge value={data.procedure?.status || "unknown"} />}
              >
                <Facts
                  items={[
                    ["Procedure", data.procedure?.id],
                    ["Configuration", data.procedure?.configuration_id],
                    ["Owner", data.procedure?.owner],
                  ]}
                />
                <div className="source-work-list">
                  <ul>
                    {data.procedure?.tasks.map((t) => (
                      <li key={t}>{t}</li>
                    ))}
                  </ul>
                </div>
              </Panel>
              <ApprovedWork records={records} system="engineering" />
              <Panel title="Configuration revision">
                <Facts
                  items={[
                    [
                      "Product revision",
                      String(data.configuration.product_revision),
                    ],
                    ["Firmware", String(data.configuration.firmware)],
                    ["Runtime", String(data.configuration.runtime)],
                  ]}
                />
              </Panel>
            </>
          )}
          {system === "validation" && (
            <Panel title="Historical evidence">
              <p className="padded source-boundary">
                Historical applicability does not authorize lot release or
                establish physical root cause.
              </p>
              {data.evidence.length ? (
                <Table
                  headers={["Result", "Configuration", "Workload", "Status"]}
                >
                  {data.evidence.map((e) => (
                    <tr key={String(e.id)}>
                      <td>
                        <strong>{String(e.id)}</strong>
                      </td>
                      <td>{String(e.configuration_id)}</td>
                      <td>{String(e.workload_profile_id)}</td>
                      <td>
                        <Badge value={String(e.status)} />
                      </td>
                    </tr>
                  ))}
                </Table>
              ) : (
                <Empty>Evidence missing · Unknown</Empty>
              )}
            </Panel>
          )}
          {system === "programs" && (
            <>
              <Panel title={`${caseId} recovery task record`}>
                <Facts
                  items={[
                    ["Milestone", data.exception.milestone_id],
                    ["Name", String(data.milestone.name)],
                    ["Baseline", sourceDate(data.milestone.baseline_at)],
                  ]}
                />
                <p className="padded source-boundary">
                  Program Owner approval is recorded in the Stratos case
                  workspace. Only an executed, verified decision creates a
                  recovery task.
                </p>
              </Panel>
              {records.tasks.length ? (
                records.tasks.map((t) => (
                  <Panel
                    key={t.id}
                    title={`Recovery task · ${t.id}`}
                    aside={<Badge value={t.status} />}
                  >
                    <Facts
                      items={[
                        [
                          "What changed",
                          `A recovery planning task was added for ${caseId}.`,
                        ],
                        ["Owner", t.owner],
                        [
                          "Planning position",
                          `${t.eligible_quantity} eligible units; ${t.gap_quantity}-unit gap remains open`,
                        ],
                        ["Held lot", `${t.lot_id} remains held`],
                        ["Approved plan", t.plan_id],
                        ["Program Owner decision", t.decision_id],
                        ["Source version", <Fresh record={t} />],
                        [
                          "Protected controls",
                          "No lot release, allocation change, or customer commitment change",
                        ],
                      ]}
                    />
                    <div className="padded">
                      <h3>Approved recommendation</h3>
                      {(
                        t.approved_recommendation ||
                        "No recommendation text recorded."
                      )
                        .split("\n\n")
                        .map((part) => (
                          <p key={part}>{part}</p>
                        ))}
                    </div>
                    <p className="padded source-boundary">
                      <strong>Next operational step:</strong> track recovery
                      planning with released supply while Product Quality
                      completes the separate investigation and disposition.
                    </p>
                  </Panel>
                ))
              ) : (
                <Empty>
                  No approved recovery task recorded.{" "}
                  {caseId === "QE-004"
                    ? "Return to the Stratos QE-004 case to complete the Program Operator handoff and Program Owner decision."
                    : "The standard investigation route does not create a Planner recovery task."}
                </Empty>
              )}
              <ApprovedWork records={records} system="planner" />
            </>
          )}
          {system === "erp" && (
            <>
              <Panel
                title="Customer demand"
                aside={<span className="source-field-label">ERP order</span>}
              >
                <Facts
                  items={[
                    ["Order", data.exception.order_id],
                    ["Demand", `${String(data.order.quantity)} units`],
                    [
                      "Customer commitment",
                      sourceDate(data.order.committed_delivery_at),
                    ],
                    ["Program", data.program_id],
                  ]}
                />
              </Panel>
              {data.analysis?.gap_value_exposure_cents != null && (
                <Panel title="Planning exposure">
                  <div className="erp-exposure">
                    <span className="source-field-label">
                      Potential shipment value at risk
                    </span>
                    <strong>
                      {usd(data.analysis.gap_value_exposure_cents)}
                    </strong>
                    <p>
                      {data.analysis.gap_quantity} uncovered units ×{" "}
                      {usd(data.analysis.planning_unit_value_cents || 0)} per
                      unit.
                    </p>
                  </div>
                  <Facts
                    items={[
                      [
                        "First-pass shortfall",
                        `${data.analysis.first_pass_shortfall_quantity} fewer passes than baseline`,
                      ],
                      [
                        "Potential value deferred",
                        usd(
                          data.analysis.first_pass_shortfall_value_cents || 0,
                        ),
                      ],
                      ["Planning basis", data.analysis.planning_value_basis],
                    ]}
                  />
                </Panel>
              )}
              <Banner>
                Customer commitment unchanged by recovery planning.
              </Banner>
            </>
          )}
        </>
      )}
      <div className="source-footer-actions">
        <Link to={`/control/programs/PRG-A17/cases/${caseId}`}>
          Open connected quality workbench <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}
