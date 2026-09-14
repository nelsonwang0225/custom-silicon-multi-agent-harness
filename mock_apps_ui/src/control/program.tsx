import { caseTone, ProgramDependencies } from "./integration";
import {
  caseFact,
  casePresentation,
  nextBusinessStep,
} from "./experience-model";
import "./rethink-workspace.css";
import { useHost } from "./host";
import { useParams, useSearchParams } from "react-router-dom";
import { Link } from "./access";
import {
  ArrowLeft,
  ArrowRight,
  CalendarClock,
  Boxes,
  ClipboardCheck,
  FlaskConical,
  Layers,
} from "lucide-react";
import {
  casePath,
  date,
  programPath,
  stories,
  useControl,
  words,
} from "./data";
import {
  StatusText,
  Crumbs,
  Empty,
  Heading,
  Section,
  SourceLink,
  SourceState,
} from "./ui";
import { Activity } from "./portfolio";
import { healthTone, nextGate } from "./overview-model";
export function ProgramPage() {
  const { programId } = useParams();
  const { data } = useControl();
  const host = useHost();
  const [params, setParams] = useSearchParams();
  const program = data?.programs.find((p) => p.id === programId),
    filter = params.get("cases") || "all",
    statusFilter = params.get("status") || "all";
  const setFilter = (name: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value === "all") next.delete(name);
    else next.set(name, value);
    setParams(next);
  };
  if (!data) return <SourceState>{null}</SourceState>;
  if (!program)
    return (
      <Empty>
        Program not found in authorized source records.{" "}
        <Link to="/control/programs">Browse programs</Link>
      </Empty>
    );
  const cases = data.cases.filter((c) => c.change.program_id === program.id);
  const connected =
    host?.data?.case_summaries?.filter((c) => c.program_id === program.id) ||
    [];
  const connectedIds = new Set(connected.map((c) => c.change_id));
  const connectedShown =
    filter === "source"
      ? []
      : connected.filter(
          (c) => statusFilter === "all" || c.state === statusFilter,
        );
  const sourceCases =
    filter === "connected" || filter === "preview"
      ? []
      : cases.filter(
          (c) =>
            (filter === "source" || !connectedIds.has(c.change.id)) &&
            (statusFilter === "all" ||
              c.change.workflow_state === statusFilter),
        );
  const statusOptions = new Map<string, string>([
    ...(filter === "source" ? [] : connected).map(
      (c) => [c.state, c.state_label] as [string, string],
    ),
    ...(filter === "connected" ? [] : cases)
      .filter((c) => filter === "source" || !connectedIds.has(c.change.id))
      .map(
        (c) =>
          [c.change.workflow_state, words(c.change.workflow_state)] as [
            string,
            string,
          ],
      ),
  ]);
  const milestone = nextGate(program.id, data.milestones);
  const gateCase = cases.find((c) =>
    milestone?.dependencies.some(
      (d) => d.requirement_revision_id === c.target.id,
    ),
  );
  const gateState = host?.data?.case_summaries?.find(
    (c) => c.change_id === gateCase?.change.id,
  );
  const orders = data.orders
      .filter((o) => o.program_id === program.id)
      .sort((a, b) =>
        a.committed_delivery_at.localeCompare(b.committed_delivery_at),
      ),
    units = data.units.filter((u) => u.program_id === program.id),
    lots = data.lots.filter((l) => l.program_id === program.id);
  return (
    <div className="rp-program-page">
      <Link to="/control/programs" className="rp-back-link">
        <ArrowLeft size={16} /> All programs
      </Link>
      <Crumbs
        items={[
          { label: "Overview", to: "/control/overview" },
          { label: program.name || program.id },
        ]}
      />
      <Heading
        eyebrow={`${program.customer_name} / ${program.id}`}
        title={program.name || program.id}
        description={`Led by ${program.owner} · Technical evidence, supply and delivery decisions`}
        action={
          <SourceLink to={`/programs/${program.id}`}>
            Open Program Planner
          </SourceLink>
        }
      />
      <div className="cp-program-context">
        <StatusText>{words(program.lifecycle)}</StatusText>
        <StatusText tone={healthTone(program.health)}>
          {words(program.health)}
        </StatusText>
        <span>Source updated {date(program.updated_at, true)}</span>
      </div>
      <section className="rp-gate-panel" aria-label="Next program gate">
        <div className="rp-gate-heading">
          <span className="rp-gate-icon">
            <CalendarClock size={23} />
          </span>
          <div>
            <span className="rp-eyebrow">Next program gate</span>
            <h2>{milestone?.name || "No open milestone recorded"}</h2>
            <p>
              {gateState && !host?.error
                ? gateState.next_action
                : milestone?.next_action ||
                  program.next_action ||
                  "No next action recorded"}
            </p>
          </div>
        </div>
        <div className="rp-gate-dates">
          <div>
            <span>Baseline</span>
            <strong>{date(milestone?.baseline_at, true)}</strong>
          </div>
          <div>
            <span>Current forecast</span>
            <strong>{date(milestone?.current_forecast_at, true)}</strong>
            <small>{words(milestone?.forecast_status)}</small>
          </div>
          <div>
            <span>
              {orders.length > 1
                ? "Earliest customer commitment"
                : "Customer commitment"}
            </span>
            <strong>
              {orders[0]
                ? date(orders[0].committed_delivery_at, true)
                : "Not recorded"}
            </strong>
            <small>
              {orders[0]
                ? orders.length > 1
                  ? `${orders.length} source orders · Details below`
                  : `${orders[0].quantity} units · ${orders[0].id}`
                : "No source order available"}
            </small>
          </div>
        </div>
        {milestone && (
          <SourceLink to={`/programs/${program.id}/milestones/${milestone.id}`}>
            Inspect gate in Program Planner
          </SourceLink>
        )}
      </section>
      <Section
        title="Work moving this program"
        note="Each case shows its current result and the next responsible step."
        className="rp-case-register"
        action={
          <div className="rp-case-filters">
            <label>
              <span>Case status</span>
              <select
                aria-label="Case status filter"
                value={statusFilter}
                onChange={(event) => setFilter("status", event.target.value)}
              >
                <option value="all">All</option>
                {[...statusOptions].map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
                {statusFilter !== "all" && !statusOptions.has(statusFilter) && (
                  <option value={statusFilter}>{words(statusFilter)}</option>
                )}
              </select>
            </label>
            <label>
              <span>Case type</span>
              <select
                aria-label="Case filter"
                value={filter}
                onChange={(event) => setFilter("cases", event.target.value)}
              >
                <option value="all">All entries</option>
                <option value="source">Source cases</option>
                <option value="connected">Connected workflows</option>
              </select>
            </label>
          </div>
        }
      >
        <div className="rp-case-rows" aria-label="Connected workflow cases">
          {connectedShown.map((c) => (
            <Link
              key={c.change_id}
              to={c.href}
              className="rp-case-row"
              data-case-id={c.change_id}
              data-case-state={c.state}
            >
              <div className="rp-case-identity">
                <span className="rp-case-code">{c.change_id}</span>
                <strong>
                  {
                    casePresentation(
                      host?.data,
                      c.change_id,
                      cases.find((item) => item.change.id === c.change_id),
                      c.title,
                    ).title
                  }
                </strong>
              </div>
              <div className="rp-case-outcome">
                <StatusText
                  tone={
                    host?.error
                      ? "warning"
                      : c.state === "handoff_verified"
                        ? "good"
                        : caseTone(c)
                  }
                >
                  {host?.error ? "Current state unavailable" : c.state_label}
                </StatusText>
                <p>
                  {host?.error
                    ? "Last-read information · Refresh required"
                    : [
                          "handoff_verified",
                          "completed_technical",
                          "completed_recovery",
                        ].includes(c.state)
                      ? c.detail
                      : caseFact(
                          host?.data,
                          c,
                          cases.find((item) => item.change.id === c.change_id),
                        )}
                </p>
              </div>
              <div className="rp-case-next">
                <span>Next step</span>
                <strong>
                  {host?.error
                    ? "Refresh current sources"
                    : nextBusinessStep(host?.data, c)}
                </strong>
              </div>
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
          ))}
          {sourceCases.map((c) => (
            <Link
              key={c.change.id}
              to={casePath(c)}
              className="rp-case-row"
              data-case-id={c.change.id}
            >
              <div className="rp-case-identity">
                <span className="rp-case-code">{c.change.id}</span>
                <strong>{c.change.title}</strong>
              </div>
              <div className="rp-case-outcome">
                <StatusText>{words(c.change.workflow_state)}</StatusText>
                <p>{c.change.owner || program.owner}</p>
              </div>
              <div className="rp-case-next">
                <span>Source case</span>
                <strong>Inspect evidence and dependencies</strong>
              </div>
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
          ))}
          {filter !== "source" &&
            statusFilter === "all" &&
            program.id === "PRG-A17" &&
            stories.map((story) => (
              <Link
                to={`${programPath(program.id)}/cases/${story.id}`}
                key={story.id}
                className="rp-case-row"
              >
                <div className="rp-case-identity">
                  <span className="rp-case-code">{story.code}</span>
                  <strong>{story.title}</strong>
                </div>
                <StatusText>Preview only</StatusText>
                <p>{story.next}</p>
                <ArrowRight size={18} />
              </Link>
            ))}
        </div>
        {!connectedShown.length && !sourceCases.length && (
          <Empty>
            {statusFilter !== "all"
              ? "No cases match this status."
              : host?.error || "No case records in this view."}
            {(statusFilter !== "all" || filter !== "all") && (
              <button
                onClick={() => {
                  const next = new URLSearchParams(params);
                  next.delete("status");
                  next.delete("cases");
                  setParams(next);
                }}
              >
                Show all cases
              </button>
            )}
          </Empty>
        )}
      </Section>
      <ProgramDependencies programId={program.id} />
      <Section
        title="Source facts"
        note="Technical scope, evidence, material and customer commitments."
        className="rp-program-sources"
      >
        <div className="cp-context-grid">
          <article>
            <Layers size={20} />
            <h3>Technical scope</h3>
            <p>
              {program.configuration_id} / {program.product_revision}.
              Requirements and criteria stay under Engineering authority.
            </p>
            <SourceLink
              to={
                cases[0]
                  ? `/engineering/changes/${cases[0].change.id}`
                  : "/engineering"
              }
            >
              Engineering scope
            </SourceLink>
          </article>
          <article>
            <FlaskConical size={20} />
            <h3>Validation</h3>
            <p>
              {cases.filter((c) => !c.coverage.coverage_satisfied).length}{" "}
              source changes without full applicable coverage. Scheduling does
              not establish a pass.
            </p>
            <SourceLink
              to={
                cases[0]
                  ? `/validation?change=${cases[0].change.id}`
                  : "/validation"
              }
            >
              Evidence & coverage
            </SourceLink>
          </article>
          <article>
            <Boxes size={20} />
            <h3>Supply constraints</h3>
            <p>
              {units.length} serialized units observed;{" "}
              {lots.filter((l) => l.restrictions.length > 0).length} restricted
              lots. These are not delivery-eligible quantity totals.
            </p>
            <SourceLink
              to={
                lots[0] ? `/manufacturing/lots/${lots[0].id}` : "/manufacturing"
              }
            >
              Units & lot restrictions
            </SourceLink>
          </article>
          <article>
            <ClipboardCheck size={20} />
            <h3>Customer commitment</h3>
            {orders.map((order) => (
              <p key={order.id}>
                <SourceLink to={`/erp/orders/${order.id}`}>
                  {order.id}
                </SourceLink>{" "}
                · {order.quantity} units · Original commitment{" "}
                {date(order.committed_delivery_at)}
              </p>
            ))}
            {!orders.length && <p>Order records unavailable.</p>}
            <small>
              Original order obligations remain separate from exact release
              commitments.
            </small>
          </article>
        </div>
      </Section>
      <details className="rp-source-activity">
        <summary>Source activity</summary>
        <p>Source observations retain their original timestamps.</p>
        <Activity programIds={[program.id]} />
      </details>
    </div>
  );
}
