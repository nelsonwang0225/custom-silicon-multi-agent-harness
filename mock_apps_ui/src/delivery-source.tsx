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

const sourceDate = (value: unknown) =>
  date(typeof value === "string" ? value : null);
const quantity = (value: number | null | undefined) =>
  value == null ? "Unknown" : value.toLocaleString();

function SupplyAccounting({
  analysis,
}: {
  analysis: HostSchema["DeliveryAnalysis"];
}) {
  return (
    <section
      className="erp-supply-accounting"
      aria-label="Supply and demand accounting"
    >
      <div className="erp-supply-equation">
        <div>
          <span>Physical</span>
          <strong>{quantity(analysis.physical_total)}</strong>
          <small>units in source material</small>
        </div>
        <span className="accounting-operator" aria-hidden="true">
          −
        </span>
        <div className="held">
          <span>Held</span>
          <strong>{quantity(analysis.held_quantity)}</strong>
          <small>excluded from supply</small>
        </div>
        <span className="accounting-operator" aria-hidden="true">
          −
        </span>
        <div>
          <span>Allocated</span>
          <strong>{quantity(analysis.allocated_quantity)}</strong>
          <small>existing order allocations</small>
        </div>
        {(analysis.configuration_mismatch_quantity > 0 ||
          analysis.other_unavailable_quantity > 0) && (
          <>
            <span className="accounting-operator" aria-hidden="true">
              −
            </span>
            <div>
              <span>Other unavailable</span>
              <strong>
                {quantity(
                  analysis.configuration_mismatch_quantity +
                    analysis.other_unavailable_quantity,
                )}
              </strong>
              <small>configuration or availability</small>
            </div>
          </>
        )}
        <span className="accounting-operator" aria-hidden="true">
          {analysis.inventory_consistent ? "=" : "→"}
        </span>
        <div className="eligible">
          <span>Eligible</span>
          <strong>{quantity(analysis.eligible_quantity)}</strong>
          <small>eligible for this request</small>
        </div>
      </div>
      <div className="erp-demand-gap">
        <div>
          <span>Demand</span>
          <strong>{quantity(analysis.requested_quantity)}</strong>
        </div>
        <div className={analysis.gap_quantity ? "gap" : ""}>
          <span>Gap</span>
          <strong>{quantity(analysis.gap_quantity)}</strong>
        </div>
      </div>
      {!analysis.inventory_consistent && (
        <p className="accounting-note">
          Source inventory needs reconciliation.{" "}
          {analysis.inventory_reasons.map(human).join(" · ")}
        </p>
      )}
    </section>
  );
}

function MaterialTable({ data }: { data: HostSchema["DeliveryContext"] }) {
  return (
    <Table
      headers={[
        "Material / lot",
        "Disposition",
        "Physical",
        "Released",
        "Held",
        "Allocated",
        "Eligible",
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
            <span className="cell-secondary">{m.configuration_id}</span>
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
          <td className="numeric">{quantity(m.physical_quantity)}</td>
          <td className="numeric">{quantity(m.released_quantity)}</td>
          <td className="numeric">{quantity(m.held_quantity)}</td>
          <td className="numeric">{quantity(m.allocated_quantity)}</td>
          <td className="numeric strong-number">
            {quantity(m.eligible_unallocated_quantity)}
          </td>
        </tr>
      ))}
    </Table>
  );
}

export function DeliverySource() {
  const system = useLocation().pathname.split("/")[1];
  const [data, setData] = useState<HostSchema["DeliveryContext"] | null>(null),
    [records, setRecords] = useState<HostSchema["DeliveryRecords"] | null>(
      null,
    ),
    [error, setError] = useState("");
  const load = () => {
    setError("");
    Promise.all([
      request<HostSchema["DeliveryContext"]>(
        "/erp/delivery-requests/DR-009/context",
        "reader",
      ),
      request<HostSchema["DeliveryRecords"]>(
        "/erp/delivery-requests/DR-009/records",
        "reader",
      ),
    ])
      .then(([c, r]) => {
        setData(c);
        setRecords(r);
      })
      .catch(() => setError("Current delivery source unavailable."));
  };
  useEffect(load, []);
  return (
    <div className="source-record-page delivery-source-page">
      <Heading
        eyebrow={
          system === "erp"
            ? "Order management / Delivery request"
            : "Related source records / Delivery"
        }
        title="DR-009 · Source records"
        action={<button onClick={load}>Refresh source records</button>}
      >
        {data ? (
          <>
            <Link to={`/programs/${data.program_id}`}>{data.program_id}</Link> ·{" "}
            {data.request.order_id} / {data.request.line_id} ·{" "}
            <Fresh record={data.request} />
          </>
        ) : (
          "ERP delivery request"
        )}
      </Heading>
      {error && <Banner tone="danger">{error}</Banner>}
      {!data && !error && <Empty>Loading delivery source records…</Empty>}
      {data && records && (
        <>
          {system === "erp" && (
            <>
              <section
                className="erp-object-header"
                aria-label="Delivery order header"
              >
                <div className="erp-object-identity">
                  <span className="source-field-label">Customer order</span>
                  <h2>{data.request.order_id}</h2>
                  <p>
                    {data.customer_id} · {data.program_id}
                  </p>
                </div>
                <div>
                  <span>Requested quantity</span>
                  <strong>
                    {quantity(data.request.quantity)} <small>units</small>
                  </strong>
                </div>
                <div>
                  <span>Requested {data.request.date_semantics}</span>
                  <strong className="object-date">
                    {date(data.request.requested_at)}
                  </strong>
                </div>
                <div>
                  <span>Destination</span>
                  <strong className="object-date">
                    {data.request.destination || "Not supplied"}
                  </strong>
                </div>
              </section>
              <nav
                className="source-anchor-nav"
                aria-label="Delivery order sections"
              >
                <a href="#delivery-overview">Overview</a>
                <a href="#delivery-line-items">Line items</a>
                <a href="#delivery-supply">Supply</a>
                <a href="#delivery-allocations">Allocations</a>
                <a href="#delivery-commitment">Commitments</a>
              </nav>
              <Panel
                title="Delivery request & commercial commitment"
                id="delivery-overview"
              >
                <p className="padded">{data.request.summary}</p>
                <Facts
                  items={[
                    [
                      "Original order commitment",
                      sourceDate(data.order.committed_delivery_at),
                    ],
                    ["Commitment owner", data.request.commitment_owner],
                    [
                      "Customer agreement",
                      human(
                        data.commitment?.customer_agreement ||
                          data.request.customer_agreement,
                      ),
                    ],
                  ]}
                />
              </Panel>
              <Panel title="Line items" id="delivery-line-items">
                <Table
                  headers={[
                    "Order / line",
                    "Configuration",
                    "Requested quantity",
                    "Requested date",
                    "Destination",
                  ]}
                >
                  <tr>
                    <td>
                      <strong>{data.request.order_id}</strong>
                      <span className="cell-secondary">
                        {data.request.line_id}
                      </span>
                    </td>
                    <td>
                      {data.request.configuration_id}
                      <span className="cell-secondary">
                        {data.request.requirement_revision_id}
                      </span>
                    </td>
                    <td className="numeric">
                      {quantity(data.request.quantity)} units
                    </td>
                    <td>
                      {date(data.request.requested_at)}
                      <span className="cell-secondary">
                        {human(data.request.date_semantics)}
                      </span>
                    </td>
                    <td>{data.request.destination || "Not supplied"}</td>
                  </tr>
                </Table>
              </Panel>
              <div id="delivery-supply">
                <div className="source-section-heading">
                  <h2>Supply position</h2>
                  <Link to="/manufacturing/delivery/DR-009">
                    Manufacturing material ↗
                  </Link>
                </div>
                {data.analysis ? (
                  <SupplyAccounting analysis={data.analysis} />
                ) : (
                  <Empty>Supply analysis not available.</Empty>
                )}
              </div>
              <Panel
                title="Existing allocations"
                id="delivery-allocations"
                aside={
                  <span className="source-field-label">
                    ERP allocation records
                  </span>
                }
              >
                {data.allocations.length ? (
                  <Table
                    headers={[
                      "Allocation",
                      "Material",
                      "Order",
                      "Quantity",
                      "Release reference",
                    ]}
                  >
                    {data.allocations.map((a) => (
                      <tr key={a.id}>
                        <td>
                          <strong>{a.id}</strong>
                          <span className="cell-secondary">
                            {human(a.status)}
                          </span>
                        </td>
                        <td>{a.material_id}</td>
                        <td>{a.order_id}</td>
                        <td className="numeric">
                          {quantity(a.quantity)} units
                        </td>
                        <td>{a.release_reference}</td>
                      </tr>
                    ))}
                  </Table>
                ) : (
                  <Empty>No allocation records supplied.</Empty>
                )}
              </Panel>
              <Panel
                title="Authorized release commitment"
                id="delivery-commitment"
                aside={
                  data.commitment ? (
                    <Badge value={data.commitment.status} />
                  ) : (
                    <span className="source-field-label">
                      No revised commitment
                    </span>
                  )
                }
              >
                {data.commitment ? (
                  <>
                    <div className="erp-commitment-summary">
                      <div>
                        <span>Committed release</span>
                        <strong>
                          {quantity(data.commitment.quantity)}{" "}
                          <small>units</small>
                        </strong>
                      </div>
                      <div>
                        <span>
                          {human(data.commitment.date_semantics)} commitment
                        </span>
                        <strong className="object-date">
                          {date(data.commitment.committed_at)}
                        </strong>
                      </div>
                      <div>
                        <span>Remaining uncommitted</span>
                        <strong>
                          {quantity(
                            data.commitment.remaining_uncommitted_quantity,
                          )}{" "}
                          <small>units</small>
                        </strong>
                      </div>
                    </div>
                    <Facts
                      items={[
                        ["Commitment", data.commitment.id],
                        [
                          "Customer agreement",
                          human(data.commitment.customer_agreement),
                        ],
                        ["Exact proposal", data.commitment.plan_id],
                        ["Program Owner decision", data.commitment.decision_id],
                        ["Source version", <Fresh record={data.commitment} />],
                      ]}
                    />
                  </>
                ) : (
                  <Empty>No revised release commitment recorded.</Empty>
                )}
                <p className="padded source-boundary">
                  Original order obligation is retained. A release commitment
                  does not ship goods, change allocations or establish customer
                  agreement.
                </p>
              </Panel>
              <Panel title="Exact proposals & decisions">
                <Table
                  headers={[
                    "Proposal",
                    "Quantity",
                    "Proposed commitment",
                    "Decision",
                  ]}
                >
                  {records.plans.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <strong>{p.id}</strong>
                        <span className="cell-secondary">
                          Version {p.plan_version}
                        </span>
                      </td>
                      <td className="numeric">{quantity(p.quantity)} units</td>
                      <td>{date(p.committed_at)}</td>
                      <td>
                        <Badge
                          value={
                            records.decisions.find((d) => d.plan_id === p.id)
                              ?.decision || "Decision required"
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </Table>
                {!records.plans.length && (
                  <Empty>No commitment proposal recorded.</Empty>
                )}
              </Panel>
              {records.commitments.length > 0 && (
                <Panel title="Commitment history">
                  <Table
                    headers={[
                      "Commitment",
                      "Quantity",
                      "Commitment date",
                      "Customer agreement",
                      "Replaces",
                    ]}
                  >
                    {records.commitments.map((c) => (
                      <tr key={c.id}>
                        <td>
                          <strong>{c.id}</strong>
                          <span className="cell-secondary">
                            v{c.content_version}
                          </span>
                        </td>
                        <td className="numeric">
                          {quantity(c.quantity)} units
                        </td>
                        <td>
                          {date(c.committed_at)}
                          <span className="cell-secondary">
                            {human(c.date_semantics)}
                          </span>
                        </td>
                        <td>{human(c.customer_agreement)}</td>
                        <td>
                          {c.supersedes_commitment_id ||
                            "Initial release commitment"}
                        </td>
                      </tr>
                    ))}
                  </Table>
                </Panel>
              )}
            </>
          )}
          {system === "programs" && (
            <>
              <Panel title="Delivery milestone & commitment links">
                <Facts
                  items={[
                    ["Milestone", data.request.milestone_id],
                    ["Name", String(data.milestone.name)],
                    ["Baseline", sourceDate(data.milestone.baseline_at)],
                    [
                      "Forecast",
                      sourceDate(data.milestone.current_forecast_at),
                    ],
                  ]}
                />
              </Panel>
              {records.links.length ? (
                records.links.map((l) => (
                  <Panel
                    key={l.id}
                    title={l.id}
                    aside={<Badge value={l.status} />}
                  >
                    <Facts
                      items={[
                        ["Quantity", `${l.quantity} units`],
                        [
                          "Commitment",
                          `${date(l.committed_at)} · ${l.date_semantics}`,
                        ],
                        [
                          "Remaining uncommitted",
                          `${l.remaining_uncommitted_quantity} units`,
                        ],
                        ["ERP commitment", l.commitment_id],
                        ["Proposal", l.plan_id],
                        ["Decision", l.decision_id],
                      ]}
                    />
                  </Panel>
                ))
              ) : (
                <Empty>No delivery commitment link recorded.</Empty>
              )}
              <Panel title="Logistics source">
                <Facts
                  items={[
                    ["Record", data.logistics?.id],
                    ["State", data.logistics?.state],
                    ["Destination", data.logistics?.destination],
                  ]}
                />
              </Panel>
            </>
          )}
          {system === "manufacturing" && (
            <>
              <Panel
                title="Shared material & disposition"
                aside={
                  <Link to="/manufacturing/quality/QE-004">
                    Quality exception QE-004 ↗
                  </Link>
                }
              >
                <MaterialTable data={data} />
                <p className="padded source-boundary">
                  Held material is excluded from eligible supply. ERP
                  commitments do not change Manufacturing disposition.
                </p>
              </Panel>
              <Panel title="Future expected supply">
                {data.future_supply.length ? (
                  <Table
                    headers={[
                      "Receipt",
                      "Expected quantity",
                      "Expected date",
                      "State",
                    ]}
                  >
                    {data.future_supply.map((f) => (
                      <tr key={f.id}>
                        <td>
                          <strong>{f.id}</strong>
                        </td>
                        <td className="numeric">
                          {quantity(f.quantity)} units
                        </td>
                        <td>{date(f.expected_at)}</td>
                        <td>
                          <Badge value={f.status} />
                          <span className="cell-secondary">
                            Release prerequisites pending
                          </span>
                        </td>
                      </tr>
                    ))}
                  </Table>
                ) : (
                  <Empty>No future receipt modeled.</Empty>
                )}
              </Panel>
            </>
          )}
          {system === "engineering" && (
            <>
              <Panel title="Configuration & Engineering clearance">
                <Facts
                  items={[
                    ["Configuration", data.request.configuration_id],
                    [
                      "Firmware / runtime",
                      `${String(data.configuration.firmware)} / ${String(data.configuration.runtime)}`,
                    ],
                    ["Requirement", data.request.requirement_revision_id],
                    [
                      "Technical state",
                      <Badge
                        value={data.analysis?.technical_readiness || "UNKNOWN"}
                      />,
                    ],
                  ]}
                />
                {data.request.technical_change_id ? (
                  <p className="padded">
                    CR-017 · Current Engineering review{" "}
                    {String(
                      (
                        data.technical_dependency?.physical as
                          Record<string, unknown> | undefined
                      )?.engineering_status || "pending",
                    )}
                  </p>
                ) : (
                  <Facts
                    items={[
                      ["Clearance", data.clearance?.id],
                      ["Status", data.clearance?.status],
                      ["Review digest", data.clearance?.review_digest],
                    ]}
                  />
                )}
                {!!data.analysis?.technical_reasons.length && (
                  <p className="padded source-boundary">
                    {data.analysis.technical_reasons.join(" · ")}
                  </p>
                )}
              </Panel>
            </>
          )}
          {system === "validation" && (
            <Panel title="Applicable evidence & technical dependency">
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
              {!data.evidence.length && (
                <Empty>No applicable evidence supplied.</Empty>
              )}
              <Facts
                items={[
                  ["Technical state", data.analysis?.technical_readiness],
                  ["Reasons", data.analysis?.technical_reasons.join(" · ")],
                ]}
              />
              <p className="padded source-boundary">
                Technical acceptance is separate from commercial commitment.
              </p>
            </Panel>
          )}
        </>
      )}
      <div className="source-footer-actions">
        <Link to="/control/programs/PRG-A17/cases/DR-009">
          Open connected delivery workbench <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}
