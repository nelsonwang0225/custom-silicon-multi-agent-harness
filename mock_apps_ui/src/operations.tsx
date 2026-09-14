import { usePortfolioFilter, ProgramCell } from "./portfolio-filters";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useData } from "./data";
import type { Schema } from "./api";
import "./source-operations.css";
import {
  Badge,
  Banner,
  date,
  Empty,
  Facts,
  Fresh,
  Heading,
  money,
  human,
  Panel,
  Reasons,
  SearchField,
  Table,
} from "./ui";
function HoldContext({ record }: { record: Schema["Lot"] }) {
  return (
    <>
      {record.restrictions.map((restriction) => {
        const detail = record.hold_details?.find(
          (d) => d.restriction === restriction,
        );
        return (
          <div className="hold-context" key={restriction}>
            <h3>{human(restriction)} · disposition context</h3>
            {detail ? (
              <Facts
                items={[
                  ["Rationale", detail.rationale],
                  ["Responsible team", detail.responsible_team],
                  ["Release conditions", detail.release_conditions],
                ]}
              />
            ) : (
              <p>
                Rationale, responsible team and release conditions were not
                supplied in this source record. The restriction remains in
                effect.
              </p>
            )}
          </div>
        );
      })}
    </>
  );
}
export function Manufacturing() {
  const { data } = useData();
  const scope = usePortfolioFilter();
  const [state, setState] = useState("all");
  const params = useParams();
  const [search, setSearch] = useState(""),
    [revision, setRevision] = useState("all"),
    [restriction, setRestriction] = useState("all");
  if (!data) return null;
  const unit = params.unitId
    ? data.units.find((u) => u.id === params.unitId)
    : null;
  const lot = params.lotId
    ? data.lots.find((l) => l.id === params.lotId)
    : unit
      ? data.lots.find((l) => l.id === unit.source_lot_id)
      : null;
  const partner = (updated: string) => {
    const p = data.programs[0];
    const age =
      (new Date(p.scenario_at).getTime() - new Date(updated).getTime()) / 60000;
    return (
      <Badge
        value={
          age >= 0 && age <= p.partner_freshness_limit_minutes
            ? `${age} min old at scenario time`
            : "partner refresh outside policy"
        }
        tone={
          age >= 0 && age <= p.partner_freshness_limit_minutes
            ? "neutral"
            : "warning"
        }
      />
    );
  };
  if (params.unitId || params.lotId) {
    if (!lot) return <Empty>Manufacturing record not found.</Empty>;
    const genealogyUnits = unit
      ? [unit]
      : data.units.filter((u) => u.source_lot_id === lot.id);
    return (
      <>
        <Heading
          eyebrow="Lot tracking / Material genealogy"
          title={unit?.id || lot.id}
          action={<Badge value="read only" />}
        >
          <Fresh record={unit || lot} />
        </Heading>
        <div className="mes-provenance-header">
          <div>
            <span className="source-field-label">Product / revision</span>
            <strong>
              {lot.product_id} · {lot.product_revision}
            </strong>
          </div>
          <div>
            <span className="source-field-label">Program</span>
            <strong>
              <Link to={"/programs/" + lot.program_id}>{lot.program_id}</Link>
            </strong>
          </div>
          <div>
            <span className="source-field-label">
              Manufacturing restrictions
            </span>
            <strong>
              {lot.restrictions.length || unit?.restrictions.length ? (
                <Badge value="hold or restriction recorded" tone="warning" />
              ) : (
                "No recorded restrictions"
              )}
            </strong>
          </div>
        </div>
        <div className="source-section-heading">
          <h2>Lot → unit genealogy</h2>
          <span className="source-field-label">Recorded lineage</span>
        </div>
        <div className="genealogy">
          <Link to={"/manufacturing/lots/" + lot.id}>
            {lot.id}
            <small>Source lot · {lot.product_revision}</small>
          </Link>
          {genealogyUnits.length > 0 ? (
            <span aria-hidden="true">→</span>
          ) : (
            <span>No individual unit records are published for this lot.</span>
          )}
          {genealogyUnits.map((u) => (
            <Link key={u.id} to={"/manufacturing/units/" + u.id}>
              {u.id}
              <small>Physical unit · {u.product_revision}</small>
            </Link>
          ))}
        </div>
        <div className={unit ? "split" : "source-lot-details"}>
          {unit && (
            <Panel title="Unit restrictions">
              <div className="padded">
                <Reasons values={unit.restrictions} />
              </div>
              <HoldContext record={unit} />
              <Facts
                items={[
                  [
                    "Product / revision",
                    unit.product_id + " / " + unit.product_revision,
                  ],
                  ["Program", unit.program_id],
                  ["Partner refreshed", date(unit.updated_at)],
                  ["Freshness", partner(unit.updated_at)],
                ]}
              />
            </Panel>
          )}
          <Panel
            title="Source-lot restrictions"
            aside={
              <Badge
                value={
                  lot.restrictions.length
                    ? lot.restrictions.join(", ")
                    : "no lot restrictions"
                }
                tone={lot.restrictions.length ? "warning" : "good"}
              />
            }
          >
            <div className="padded">
              <Reasons values={lot.restrictions} />
            </div>
            <HoldContext record={lot} />
            <Facts
              items={[
                [
                  "Product / revision",
                  lot.product_id + " / " + lot.product_revision,
                ],
                ["Program", lot.program_id],
                ["Partner refreshed", date(lot.updated_at)],
                ["Freshness", partner(lot.updated_at)],
              ]}
            />
          </Panel>
        </div>
        <Banner
          tone={
            lot.restrictions.length || unit?.restrictions.length
              ? "warning"
              : "info"
          }
        >
          Unit and source-lot restrictions are independent. Lab availability
          does not override a manufacturing hold. Source records are read-only.
        </Banner>
      </>
    );
  }
  if (params.screen && params.screen !== "lots")
    return <Empty>Manufacturing page not found.</Empty>;
  const lots = params.screen === "lots";
  const rows = (lots ? data.lots : data.units).filter(
    (r) =>
      (r.id + " " + r.product_id + " " + scope.text(r.program_id))
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      scope.matches(r.program_id) &&
      (state === "all" || r.inventory_state === state) &&
      (revision === "all" || r.product_revision === revision) &&
      (restriction === "all" ||
        (r.restrictions.length > 0 ||
          ("source_lot_id" in r &&
            !!data.lots.find((l) => l.id === r.source_lot_id)?.restrictions
              .length)) ===
          (restriction === "held")),
  );
  return (
    <>
      <Heading
        eyebrow="Manufacturing operations / Material tracking"
        title={lots ? "Source lots" : "Unit inventory"}
        action={<Badge value="read only" />}
      >
        Lots, physical units and recorded manufacturing restrictions.
      </Heading>
      <div
        className="mes-register-summary"
        aria-label="Manufacturing register summary"
      >
        <div>
          <span>Source lots</span>
          <strong>
            {data.lots.filter((r) => scope.matches(r.program_id)).length}
          </strong>
          <small>In the current portfolio scope</small>
        </div>
        <div>
          <span>Tracked unit records</span>
          <strong>
            {data.units.filter((r) => scope.matches(r.program_id)).length}
          </strong>
          <small>Recorded unit genealogy</small>
        </div>
        <div className="has-holds">
          <span>Restricted lots</span>
          <strong>
            {
              data.lots.filter(
                (r) => scope.matches(r.program_id) && r.restrictions.length > 0,
              ).length
            }
          </strong>
          <small>Recorded restrictions remain in effect</small>
        </div>
      </div>
      <div className="mes-quality-entry">
        <div>
          <strong>Quality & yield records</strong>
          <p>
            Inspect exception material, first-pass yield and source-owned
            investigation work.
          </p>
        </div>
        <Link to="/manufacturing/quality/QE-004">QE-004 →</Link>
        <Link to="/manufacturing/quality/QE-011">QE-011 →</Link>
      </div>
      <nav className="source-anchor-nav" aria-label="Material views">
        <Link to="/manufacturing" aria-current={!lots ? "page" : undefined}>
          Unit inventory
        </Link>
        <Link to="/manufacturing/lots" aria-current={lots ? "page" : undefined}>
          Source lots
        </Link>
        <Link to="/manufacturing/delivery/DR-009">Delivery material</Link>
      </nav>
      <div className="toolbar">
        {scope.controls}
        <SearchField
          value={search}
          onChange={setSearch}
          label={lots ? "Search lots" : "Search units"}
        />
        <select
          aria-label="Product revision"
          value={revision}
          onChange={(e) => setRevision(e.target.value)}
        >
          <option value="all">All revisions</option>
          {[...new Set(data.units.map((u) => u.product_revision))].map((r) => (
            <option key={r}>{r}</option>
          ))}
        </select>
        <select
          aria-label="Restriction filter"
          value={restriction}
          onChange={(e) => setRestriction(e.target.value)}
        >
          <option value="all">All restrictions</option>
          <option value="held">Restricted</option>
          <option value="clear">No recorded restriction</option>
        </select>
      </div>
      <div className="toolbar">
        <select
          aria-label="Inventory state"
          value={state}
          onChange={(e) => setState(e.target.value)}
        >
          <option value="all">All inventory states</option>
          {[
            ...new Set(
              [...data.lots, ...data.units]
                .map((r) => r.inventory_state)
                .filter(Boolean),
            ),
          ].map((s) => (
            <option key={s} value={s!}>
              {human(s!)}
            </option>
          ))}
        </select>
        <span className="muted">{rows.length} records</span>
      </div>
      <Panel
        title={lots ? "Lot register" : "Physical units"}
        aside={
          <span className="source-field-label">{rows.length} records</span>
        }
      >
        <Table
          headers={
            lots
              ? [
                  "Lot",
                  "Customer / program",
                  "Product / revision",
                  "Lot restrictions",
                  "Partner refresh",
                ]
              : [
                  "Unit",
                  "Customer / program",
                  "Product / revision",
                  "Source genealogy",
                  "Unit / lot restrictions",
                  "Partner refresh",
                ]
          }
        >
          {rows.map((r) => {
            const l =
              "source_lot_id" in r
                ? data.lots.find((l) => l.id === r.source_lot_id)
                : null;
            return (
              <tr key={r.id}>
                <td>
                  <Link
                    className="strong-link"
                    to={"/manufacturing/" + (lots ? "lots/" : "units/") + r.id}
                  >
                    {r.id}
                  </Link>
                </td>
                <td>
                  <ProgramCell id={r.program_id} />
                </td>
                <td>
                  {r.product_id}
                  <span className="cell-secondary">{r.product_revision}</span>
                  {r.inventory_state && <Badge value={r.inventory_state} />}
                </td>
                {!lots && (
                  <td>
                    <Link to={"/manufacturing/lots/" + l?.id}>{l?.id}</Link>
                  </td>
                )}
                <td>
                  {!lots && <small>Unit</small>}
                  <Reasons values={r.restrictions} />
                  {l && (
                    <>
                      <small>Source lot</small>
                      {l.restrictions.length ? (
                        <Badge value={l.restrictions.join(", ")} />
                      ) : (
                        <span className="cell-secondary">
                          No restrictions recorded
                        </span>
                      )}
                    </>
                  )}
                </td>
                <td>
                  {date(r.updated_at)}
                  <span className="cell-secondary">
                    {partner(r.updated_at)}
                  </span>
                </td>
              </tr>
            );
          })}
        </Table>
        {!rows.length && (
          <Empty>No manufacturing records match these filters.</Empty>
        )}
      </Panel>
      <Banner>
        Partner records are evaluated against the fixed scenario clock.
        Restrictions on either the unit or its source lot can block lab
        eligibility.
      </Banner>
    </>
  );
}
export function ERP() {
  const { data } = useData();
  const scope = usePortfolioFilter();
  const [state, setState] = useState("all");
  const params = useParams();
  const [search, setSearch] = useState("");
  if (!data) return null;
  if (params.orderId) {
    const order = data.orders.find((o) => o.id === params.orderId);
    if (!order) return <Empty>Order not found.</Empty>;
    const p = data.programs.find((p) => p.id === order.program_id);
    return (
      <>
        <Heading
          eyebrow="Sales / Customer order"
          title={order.id}
          action={<Badge value={order.status} />}
        >
          <Fresh record={order} />
        </Heading>
        <section
          className="erp-object-header"
          aria-label="Customer order header"
        >
          <div className="erp-object-identity">
            <span className="source-field-label">Customer</span>
            <h2>{p?.customer_name || order.customer_id}</h2>
            <p>{order.customer_id}</p>
          </div>
          <div>
            <span>Order quantity</span>
            <strong>
              {order.quantity.toLocaleString()} <small>units</small>
            </strong>
          </div>
          <div>
            <span>Customer delivery commitment</span>
            <strong className="object-date">
              {date(order.committed_delivery_at)}
            </strong>
          </div>
          <div>
            <span>Program</span>
            <strong className="object-date">
              <Link to={"/programs/" + order.program_id}>
                {order.program_id}
              </Link>
            </strong>
          </div>
        </section>
        <nav className="source-anchor-nav" aria-label="Customer order sections">
          <a href="#order-overview">Overview</a>
          <a href="#order-line-items">Line items</a>
          <a href="#order-commitment">Commitment</a>
        </nav>
        <Panel
          title="Order details"
          id="order-overview"
          className="erp-order-facts"
        >
          <Facts
            items={[
              ["Customer", p?.customer_name],
              ["Customer ID", order.customer_id],
              [
                "Program",
                <Link to={"/programs/" + order.program_id}>
                  {order.program_id}
                </Link>,
              ],
              ["Supplier", p?.supplier_name],
              ["Quantity", order.quantity],
              ["Quantity unit", human(order.quantity_unit)],
              [
                "Product / revision",
                order.product_id + " / " + order.product_revision,
              ],
              ["Source content version", order.content_version],
            ]}
          />
        </Panel>
        <Panel title="Line items" id="order-line-items">
          <Table
            headers={[
              "Product",
              "Revision",
              "Quantity",
              "Unit",
              "Delivery commitment",
            ]}
          >
            <tr>
              <td>
                <strong>{order.product_id}</strong>
              </td>
              <td>{order.product_revision}</td>
              <td className="numeric">{order.quantity.toLocaleString()}</td>
              <td>{human(order.quantity_unit)}</td>
              <td>{date(order.committed_delivery_at)}</td>
            </tr>
          </Table>
        </Panel>
        <Panel title="Commitment authority" id="order-commitment">
          <Facts
            items={[
              ["Customer-facing commitment", date(order.committed_delivery_at)],
              ["Authority", "ERP · Read-only source record"],
              ["Internal forecasts", "Separate from the customer commitment"],
            ]}
          />
          <p className="padded source-boundary">
            Validation scheduling and ProgramOps forecasts do not edit this
            date. Internal forecasts depend on successful testing and
            Engineering review.
          </p>
        </Panel>
      </>
    );
  }
  if (params.screen && params.screen !== "rates")
    return <Empty>ERP page not found.</Empty>;
  const rates = params.screen === "rates";
  return (
    <>
      <Heading
        eyebrow={
          rates
            ? "Commercial services / Rate records"
            : "Sales / Order management"
        }
        title={rates ? "Approved validation cost rates" : "Customer orders"}
        action={<Badge value="read only" />}
      >
        {rates
          ? "Approved service scope, effective dates and incremental charges."
          : "Customer demand and authoritative delivery commitments."}
      </Heading>
      {!rates && (
        <div className="erp-list-summary" aria-label="Order book summary">
          <div>
            <span>Customer orders</span>
            <strong>
              {data.orders.filter((o) => scope.matches(o.program_id)).length}
            </strong>
          </div>
          <div>
            <span>Customers</span>
            <strong>
              {
                new Set(
                  data.orders
                    .filter((o) => scope.matches(o.program_id))
                    .map((o) => o.customer_id),
                ).size
              }
            </strong>
          </div>
          <div>
            <span>Programs</span>
            <strong>
              {
                new Set(
                  data.orders
                    .filter((o) => scope.matches(o.program_id))
                    .map((o) => o.program_id),
                ).size
              }
            </strong>
          </div>
          <Link to="/erp/delivery/DR-009">
            DR-009 · Supply & release commitment →
          </Link>
        </div>
      )}
      <div className="toolbar">
        {scope.controls}
        {!rates && (
          <select
            aria-label="Order status"
            value={state}
            onChange={(e) => setState(e.target.value)}
          >
            <option value="all">All order states</option>
            {[...new Set(data.orders.map((o) => o.status))].map((s) => (
              <option key={s} value={s}>
                {human(s)}
              </option>
            ))}
          </select>
        )}
        <SearchField
          value={search}
          onChange={setSearch}
          label={rates ? "Search rates" : "Search orders"}
        />
      </div>
      {rates ? (
        <>
          <Banner>
            Approved rates effective at the scenario time. Validation also
            checks that each rate covers the full reservation interval.
          </Banner>
          <Panel title="Incremental validation costs">
            <Table
              headers={[
                "Rate record",
                "Amount / currency",
                "Effective from",
                "Effective until",
                "Status",
              ]}
            >
              {data.rates
                .filter((r) => scope.matches(r.program_id))
                .filter((r) =>
                  (
                    r.id +
                    " " +
                    (r.service_name || "") +
                    " " +
                    (r.service_description || "")
                  )
                    .toLowerCase()
                    .includes(search.toLowerCase()),
                )
                .map((r) => (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.id}</strong>
                      <span className="cell-secondary">
                        {scope.text(r.program_id)}
                      </span>
                      <span className="cell-secondary">
                        <strong>
                          {r.service_name || "Service label not supplied"}
                        </strong>
                      </span>
                      <p className="erp-rate-description">
                        {r.service_description ||
                          "No service description supplied in this source record."}
                      </p>
                      <span className="cell-secondary">
                        Content v{r.content_version}
                      </span>
                    </td>
                    <td className="amount">
                      {money(r.incremental_cost_cents)}
                      <span className="cell-secondary">
                        {r.incremental_cost_cents.toLocaleString()} cents ·{" "}
                        {r.currency}
                      </span>
                    </td>
                    <td>{date(r.effective_from)}</td>
                    <td>{date(r.effective_to)}</td>
                    <td>
                      <Badge value={r.status} />
                    </td>
                  </tr>
                ))}
            </Table>
            {!data.rates.some((r) =>
              (
                r.id +
                " " +
                (r.service_name || "") +
                " " +
                (r.service_description || "")
              )
                .toLowerCase()
                .includes(search.toLowerCase()),
            ) && <Empty>No rates match this search.</Empty>}
          </Panel>
        </>
      ) : (
        <Panel title="Order book">
          <Table
            headers={[
              "Order",
              "Customer / program",
              "Product",
              "Quantity",
              "Committed delivery",
              "Status",
            ]}
          >
            {data.orders
              .filter(
                (o) =>
                  scope.matches(o.program_id) &&
                  (state === "all" || state === o.status),
              )
              .filter((o) =>
                (
                  o.id +
                  " " +
                  o.customer_id +
                  " " +
                  o.product_id +
                  " " +
                  scope.text(o.program_id)
                )
                  .toLowerCase()
                  .includes(search.toLowerCase()),
              )
              .map((o) => (
                <tr key={o.id}>
                  <td>
                    <Link className="strong-link" to={"/erp/orders/" + o.id}>
                      {o.id}
                    </Link>
                  </td>
                  <td>
                    {
                      data.programs.find((p) => p.id === o.program_id)
                        ?.customer_name
                    }
                    <span className="cell-secondary">{o.program_id}</span>
                  </td>
                  <td>
                    {o.product_id}
                    <span className="cell-secondary">{o.product_revision}</span>
                  </td>
                  <td className="numeric">
                    {o.quantity}
                    <span className="cell-secondary">
                      {human(o.quantity_unit).toLowerCase()}
                    </span>
                  </td>
                  <td>
                    <strong>{date(o.committed_delivery_at)}</strong>
                    <span className="cell-secondary">
                      Authoritative · read-only
                    </span>
                  </td>
                  <td>
                    <Badge value={o.status} />
                  </td>
                </tr>
              ))}
          </Table>
          {!data.orders.some((o) =>
            (
              o.id +
              " " +
              o.customer_id +
              " " +
              o.product_id +
              " " +
              scope.text(o.program_id)
            )
              .toLowerCase()
              .includes(search.toLowerCase()),
          ) && <Empty>No orders match this search.</Empty>}
        </Panel>
      )}
    </>
  );
}
