import { usePortfolioFilter, ProgramCell } from "./portfolio-filters";
import { caseNextAction } from "./case-progress";
import { SourceReference } from "./sources";
import { useEffect, useState, type CSSProperties } from "react";
import { Link, useParams } from "react-router-dom";
import { api, enc, errorMessage, request, type Schema } from "./api";
import { useData, type Case } from "./data";
import type { HostSchema } from "./control/host";
import { CalendarDays, Flag, GitBranch, Layers, ListTodo } from "lucide-react";
import "./source-programops.css";
import { useMutation } from "./mutations";
import {
  Audit,
  Badge,
  Banner,
  date,
  Empty,
  Facts,
  Fresh,
  Heading,
  Panel,
  SearchField,
  Table,
  human,
} from "./ui";
export function Programs() {
  const { data, persona } = useData();
  const scope = usePortfolioFilter();
  const [health, setHealth] = useState("all");
  const params = useParams();
  const [search, setSearch] = useState("");
  if (!data) return null;
  if (!params.programId) {
    const programs = data.programs.filter(
      (p) =>
        scope.matches(p.id) &&
        scope.text(p.id).toLowerCase().includes(search.toLowerCase()) &&
        (health === "all" || p.health === health),
    );
    return (
      <>
        <Heading eyebrow="ProgramOps / Portfolio" title="Program workspaces">
          Program readiness, accountable owners and upcoming gates.
        </Heading>
        <div className="source-fact-strip programops-portfolio-summary">
          <div>
            <small>
              <Layers />
              Programs in scope
            </small>
            <strong className="source-count">{programs.length}</strong>
          </div>
          <div>
            <small>
              <Flag />
              Needs attention
            </small>
            <strong className="source-count">
              {
                programs.filter((p) =>
                  /risk|constraint|blocked/.test(p.health || ""),
                ).length
              }
            </strong>
          </div>
          <div>
            <small>
              <CalendarDays />
              Recorded milestones
            </small>
            <strong className="source-count">
              {
                data.milestones.filter((m) =>
                  programs.some((p) => p.id === m.program_id),
                ).length
              }
            </strong>
          </div>
          <div>
            <small>
              <GitBranch />
              Planning basis
            </small>
            <strong>Baseline / forecast</strong>
          </div>
        </div>
        <div className="toolbar">
          {scope.controls}
          <SearchField
            value={search}
            onChange={setSearch}
            label="Search programs"
          />
          <select
            aria-label="Program health"
            value={health}
            onChange={(e) => setHealth(e.target.value)}
          >
            <option value="all">All health states</option>
            {[
              ...new Set(data.programs.map((p) => p.health).filter(Boolean)),
            ].map((h) => (
              <option key={h} value={h!}>
                {h!.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </div>
        <Panel
          title="Active program portfolio"
          aside={<span>{programs.length} programs</span>}
        >
          <Table
            headers={[
              "Customer / program",
              "Product / revision",
              "Program lead",
              "Lifecycle / health",
              "Next milestone / action",
            ]}
          >
            {programs.map((p) => {
              const next = data.milestones
                .filter(
                  (m) => m.program_id === p.id && m.health !== "completed",
                )
                .sort((a, b) => a.baseline_at.localeCompare(b.baseline_at))[0];
              return (
                <tr key={p.id}>
                  <td>
                    <ProgramCell id={p.id} />
                    <Link className="button" to={"/programs/" + p.id}>
                      Open program
                    </Link>
                  </td>
                  <td>
                    {p.product_id}
                    <span className="cell-secondary">{p.product_revision}</span>
                  </td>
                  <td>{p.owner}</td>
                  <td>
                    {p.lifecycle?.replaceAll("_", " ")}
                    <span className="cell-secondary">
                      <Badge value={p.health || "Not supplied"} />
                    </span>
                  </td>
                  <td>
                    {next && (
                      <Link to={"/programs/" + p.id + "/milestones/" + next.id}>
                        {next.name} · {date(next.baseline_at)}
                      </Link>
                    )}
                    <p>
                      {data.cases.find((c) => c.milestone.id === next?.id)
                        ? caseNextAction(
                            data.cases.find(
                              (c) => c.milestone.id === next?.id,
                            )!,
                          )
                        : p.next_action}
                    </p>
                  </td>
                </tr>
              );
            })}
          </Table>
          {!programs.length && <Empty>No programs match these filters.</Empty>}
        </Panel>
      </>
    );
  }
  const p = data.programs.find((p) => p.id === params.programId);
  if (!p) return <Empty>Program not found.</Empty>;
  const cases = data.cases.filter(
    (c) =>
      c.change.program_id === p.id &&
      (!params.milestoneId || c.milestone.id === params.milestoneId),
  );
  const milestones = data.milestones.filter(
    (m) =>
      m.program_id === p.id &&
      (!params.milestoneId || m.id === params.milestoneId),
  );
  if (params.milestoneId && !milestones.length)
    return <Empty>Milestone not found in this program.</Empty>;
  return (
    <>
      <Heading
        eyebrow={"ProgramOps / " + p.id + (p.name ? " / " + p.name : "")}
        title={p.product_id + " program"}
        action={
          <Link className="button" to={"/erp/orders/" + p.order_id}>
            Customer order
          </Link>
        }
      >
        {p.customer_name} · {p.owner} · <Fresh record={p} />
      </Heading>
      <div className="source-fact-strip programops-object-summary">
        <div>
          <small>Program state</small>
          <strong>
            <Badge value={p.health || "Not supplied"} />
          </strong>
        </div>
        <div>
          <small>Program owner</small>
          <strong>{p.owner}</strong>
        </div>
        <div>
          <small>Product stage</small>
          <strong>{human(p.lifecycle || "Not supplied")}</strong>
        </div>
        <div>
          <small>Open dependencies</small>
          <strong>
            {milestones.reduce(
              (n, m) =>
                n +
                m.dependencies.filter(
                  (d) => !/^(completed|satisfied|accepted)$/.test(d.state),
                ).length,
              0,
            )}
          </strong>
        </div>
      </div>
      <nav className="source-anchor-nav" aria-label="Program sections">
        <a href="#program-timeline">Milestone timeline</a>
        <a href="#program-milestones">Milestones</a>
        <a href="#program-dependencies">Dependencies & actions</a>
        {p.id === "PRG-A17" && !params.milestoneId && (
          <a href="#program-recovery">Recovery work</a>
        )}
      </nav>
      <MilestoneTimeline milestones={milestones} programId={p.id} />
      <Panel id="program-milestones" title="Milestone register">
        <Table
          headers={[
            "Milestone / owner",
            "Health",
            "Baseline",
            "Internal forecast",
            "Dependencies / next action",
          ]}
        >
          {milestones.map((m) => (
            <tr key={m.id}>
              <td>
                <Link to={"/programs/" + p.id + "/milestones/" + m.id}>
                  {m.name}
                </Link>
                <span className="cell-secondary">
                  {m.id} · {m.owner || p.owner}
                </span>
              </td>
              <td>
                <Badge value={m.health || m.forecast_status} />
              </td>
              <td>{date(m.baseline_at)}</td>
              <td>
                {date(m.current_forecast_at)}
                <span className="cell-secondary">
                  <Badge value={m.forecast_status} />
                </span>
              </td>
              <td>
                {m.dependencies.length} dependencies
                <p>
                  {data.cases.find((c) => c.milestone.id === m.id)
                    ? caseNextAction(
                        data.cases.find((c) => c.milestone.id === m.id)!,
                      )
                    : m.next_action}
                </p>
              </td>
            </tr>
          ))}
        </Table>
      </Panel>
      <div id="program-dependencies" className="programops-dependency-heading">
        <GitBranch size={17} />
        <h2>Dependencies & actions</h2>
      </div>
      {params.milestoneId && !cases.length && (
        <Panel title="Dependency review">
          <Table headers={["Source", "State", "Owner / next action"]}>
            {milestones[0].dependencies.map((d, i) => (
              <tr key={i}>
                <td>
                  {d.job_id ? (
                    <Link to={"/validation/jobs/" + d.job_id}>{d.job_id}</Link>
                  ) : (
                    d.requirement_revision_id && (
                      <SourceReference
                        source={{
                          resource_type: "engineering.requirement",
                          resource_id: d.requirement_revision_id,
                        }}
                      />
                    )
                  )}
                </td>
                <td>
                  <Badge value={d.state} />
                </td>
                <td>
                  {d.owner}
                  <p>{d.note}</p>
                </td>
              </tr>
            ))}
          </Table>
        </Panel>
      )}
      {cases.map((c) =>
        cases.length === 1 ? (
          <ProgramCase key={c.change.id} c={c} />
        ) : (
          <details className="program-case" key={c.change.id}>
            <summary>
              {c.change.id} · {c.milestone.name} ·{" "}
              {c.jobs.some((j) => !c.links.some((l) => l.job_id === j.id))
                ? "Planner action required"
                : "Review dependencies"}
            </summary>
            <ProgramCase c={c} />
          </details>
        ),
      )}
      {p.id === "PRG-A17" && !params.milestoneId && (
        <QualityRecoveryTasks persona={persona} />
      )}
      {data.activity.some((e) => e.program_id === p.id && !e.change_id) && (
        <Panel title="Source-system activity">
          <Audit
            events={data.activity.filter(
              (e) => e.program_id === p.id && !e.change_id,
            )}
          />
        </Panel>
      )}
    </>
  );
}

function MilestoneTimeline({
  milestones,
  programId,
}: {
  milestones: Schema["Milestone"][];
  programId: string;
}) {
  const dated = milestones.filter(
    (m) =>
      Number.isFinite(Date.parse(m.baseline_at)) &&
      Number.isFinite(Date.parse(m.current_forecast_at)),
  );
  if (!dated.length) return null;
  const points = dated.flatMap((m) => [
    Date.parse(m.baseline_at),
    Date.parse(m.current_forecast_at),
  ]);
  const lo = Math.min(...points),
    hi = Math.max(...points),
    pad = Math.max((hi - lo) * 0.08, 86400000);
  const from = lo - pad,
    to = hi + pad;
  const position = (value: string) =>
    `${((Date.parse(value) - from) / (to - from)) * 100}%`;
  const day = (value: number | string) =>
    new Date(value).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    });
  return (
    <section
      id="program-timeline"
      className="panel programops-timeline"
      aria-label="Source milestone timeline"
    >
      <div className="panel-heading">
        <h2>Milestone timeline</h2>
        <div className="programops-timeline-legend">
          <span>
            <i className="baseline-symbol" />
            Baseline
          </span>
          <span>
            <i className="forecast-symbol" />
            Internal forecast
          </span>
          <small>UTC · Source dates</small>
        </div>
      </div>
      <div className="programops-timeline-axis">
        <span>Milestone / accountable owner</span>
        <div>
          <span>{day(from)}</span>
          <span>{day((from + to) / 2)}</span>
          <span>{day(to)}</span>
        </div>
      </div>
      {dated
        .slice()
        .sort((a, b) => a.baseline_at.localeCompare(b.baseline_at))
        .map((m) => (
          <div className="programops-timeline-row" key={m.id}>
            <div>
              <Link to={`/programs/${programId}/milestones/${m.id}`}>
                {m.name}
              </Link>
              <small>
                {m.owner || "Owner not recorded"} ·{" "}
                <Badge value={m.health || m.forecast_status} />
              </small>
            </div>
            <div
              className="programops-timeline-track"
              role="img"
              aria-label={`${m.name}: baseline ${date(m.baseline_at)}; internal forecast ${date(m.current_forecast_at)}; ${human(m.forecast_status)}`}
              style={
                {
                  "--milestone-base": position(m.baseline_at),
                  "--milestone-forecast": position(m.current_forecast_at),
                } as CSSProperties
              }
            >
              <i className="programops-base-marker" />
              <i className="programops-forecast-marker" />
              <span className="programops-timeline-date">
                {day(m.current_forecast_at)}
              </span>
            </div>
          </div>
        ))}
    </section>
  );
}

function QualityRecoveryTasks({
  persona,
}: {
  persona: Parameters<typeof request>[1];
}) {
  const [records, setRecords] = useState<HostSchema["QualityRecords"] | null>(
    null,
  );
  const [readError, setReadError] = useState("");
  useEffect(() => {
    let current = true;
    setReadError("");
    request<HostSchema["QualityRecords"]>(
      "/manufacturing/quality-exceptions/QE-004/records",
      persona,
    )
      .then((value) => current && setRecords(value))
      .catch(
        () =>
          current && setReadError("QE-004 recovery records are unavailable."),
      );
    return () => {
      current = false;
    };
  }, [persona]);
  const tasks = records?.tasks || [];
  return (
    <Panel id="program-recovery" title="QE-004 · Yield recovery task">
      {readError ? (
        <Banner tone="warning">{readError}</Banner>
      ) : tasks.length ? (
        <>
          <Banner tone="good">
            The approved QE-004 recovery task is recorded in Stratos ProgramOps.
            Program Owner approval was completed in Stratos before this task was
            created.
          </Banner>
          <Table headers={["Task", "Owner", "Planning position", "Status"]}>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>
                  <Link className="record-link" to="/programs/quality/QE-004">
                    {task.id}
                  </Link>
                  <span className="cell-secondary">
                    Approved plan {task.plan_id}
                  </span>
                </td>
                <td>{task.owner}</td>
                <td>
                  {task.eligible_quantity} eligible units
                  <span className="cell-secondary">
                    {task.gap_quantity}-unit gap remains open
                  </span>
                </td>
                <td>
                  <Badge value={task.status} />
                </td>
              </tr>
            ))}
          </Table>
          <div className="padded">
            <p>
              <strong>What happens here:</strong> the task tracks recovery
              planning against currently released supply while Product Quality
              continues the investigation. It does not release the held lot,
              allocate supply, or change the customer commitment.
            </p>
            <h3>Approved action plan</h3>
            <div className="programops-workstreams">
              {(tasks.at(-1)?.workstreams ?? []).map((workstream) => (
                <article key={workstream.id}>
                  <ListTodo size={17} />
                  <strong>{workstream.objective}</strong>
                  <span className="cell-secondary">{workstream.owner}</span>
                  <ul>
                    {workstream.actions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                  <small>Complete when: {workstream.completion_criteria}</small>
                </article>
              ))}
            </div>
            <Link className="button" to="/programs/quality/QE-004">
              Open QE-004 recovery record
            </Link>
          </div>
        </>
      ) : records ? (
        <Empty>
          No QE-004 recovery task has been recorded. Complete the Program
          Operator submission, Program Owner approval, and execution in the
          Stratos QE-004 case first.
        </Empty>
      ) : (
        <Empty>Reading QE-004 recovery task…</Empty>
      )}
    </Panel>
  );
}
function ProgramCase({ c }: { c: Case }) {
  const { data, persona, error, loading } = useData();
  const [selected, setSelected] = useState(""),
    [readError, setReadError] = useState(""),
    [preparing, setPreparing] = useState(false);
  const mutation = useMutation("link:" + c.change.id);
  const job = c.jobs.find((j) => j.id === selected),
    order = data!.orders.find((o) => o.id === c.change.order_id)!;
  const pending = c.jobs.filter((j) => !c.links.some((l) => l.job_id === j.id));
  const milestone = c.milestone;
  const submit = async () => {
    if (!job) return;
    setPreparing(true);
    setReadError("");
    try {
      const latest = await api(persona).get<Schema["Milestone"]>(
        `/programs/${enc(job.program_id)}/milestones/${enc(milestone.id)}`,
      );
      const body: Schema["LinkInput"] = {
        plan_id: job.plan_id,
        approval_id: job.approval_id,
        job_id: job.id,
        expected_milestone_record_version: latest.record_version,
      };
      await mutation.submit(
        `/programs/${enc(job.program_id)}/implementation-links`,
        body,
      );
    } catch (e) {
      setReadError(errorMessage(e));
    } finally {
      setPreparing(false);
    }
  };
  return (
    <>
      {pending.length > 0 && (
        <Banner tone="warning">
          {pending.length} lab job is scheduled with no planner link. Complete
          only the missing follow-through; the lab booking is already persisted.
        </Banner>
      )}
      <div className="milestone-strip">
        <div>
          <span>Baseline evidence deadline</span>
          <strong>{date(milestone.baseline_at)}</strong>
          <small>Preserved baseline</small>
        </div>
        <div className="forecast">
          <span>Internal forecast</span>
          <strong>{date(milestone.current_forecast_at)}</strong>
          <Badge value={milestone.forecast_status} />
        </div>
        <div>
          <span>Customer delivery commitment</span>
          <strong>{date(order.committed_delivery_at)}</strong>
          <small>ERP · authoritative, read-only</small>
        </div>
      </div>
      <Panel
        title={milestone.name}
        aside={
          <span className="metadata">Record v{milestone.record_version}</span>
        }
      >
        <div className="padded">
          <Link
            to={
              "/programs/" + c.change.program_id + "/milestones/" + milestone.id
            }
          >
            {milestone.id}
          </Link>{" "}
          ·{" "}
          <Link to={"/engineering/changes/" + c.change.id}>{c.change.id}</Link>
        </div>
        <Table
          headers={[
            "Dependency",
            "Required record",
            "Execution state",
            "Evidence obligation",
          ]}
        >
          {milestone.dependencies.map((d, i) => (
            <tr key={i}>
              <td>
                {d.kind === "requirement_evidence"
                  ? "Requested requirement evidence"
                  : "Validation job"}
              </td>
              <td>
                {d.job_id ? (
                  <Link
                    className="record-link"
                    to={"/validation/jobs/" + d.job_id}
                  >
                    {d.job_id}
                  </Link>
                ) : (
                  d.requirement_revision_id
                )}
              </td>
              <td>
                <Badge value={d.state} />
              </td>
              <td>
                {d.kind === "requirement_evidence"
                  ? d.requirement_revision_id !== c.target.id
                    ? "Baseline / recorded dependency status retained"
                    : c.coverage.coverage_satisfied
                      ? "Coverage available; disposition separate"
                      : "Still unsatisfied"
                  : "Scheduled; execution pending"}
              </td>
            </tr>
          ))}
        </Table>
      </Panel>
      <div className="planner-work">
        <Panel title="Validation schedule">
          <Table
            headers={[
              "Activity",
              "Starts / baseline",
              "Completes / forecast",
              "State",
            ]}
          >
            {c.jobs.map((j) => (
              <tr key={j.id}>
                <td>
                  <Link className="record-link" to={"/validation/jobs/" + j.id}>
                    {j.id}
                  </Link>
                  <span className="cell-secondary">
                    Setup, execution and engineering review
                  </span>
                </td>
                <td>{date(j.timing.lab_start_at)}</td>
                <td>{date(j.timing.review_ready_at)}</td>
                <td>
                  <Badge value="scheduled" />
                </td>
              </tr>
            ))}
            <tr>
              <td>Acceptance evidence & review</td>
              <td>{date(milestone.baseline_at)}</td>
              <td>{date(milestone.current_forecast_at)}</td>
              <td>
                <Badge value={milestone.forecast_status} />
              </td>
            </tr>
            <tr>
              <td>Customer order delivery</td>
              <td>{date(order.committed_delivery_at)}</td>
              <td>Authoritative ERP commitment</td>
              <td>
                <Badge value={order.status} />
              </td>
            </tr>
          </Table>
        </Panel>
        <Panel title="Apply implementation link">
          {mutation.feedback}
          {readError && <Banner tone="danger">{readError}</Banner>}
          {!pending.length && !mutation.pending ? (
            <Empty>
              {c.jobs.length ? (
                "All scheduled jobs are linked to this milestone."
              ) : (
                <>
                  No scheduled job is ready to link.{" "}
                  <Link to="/validation/jobs">Open the jobs queue</Link> to
                  schedule approved work.
                </>
              )}
            </Empty>
          ) : (
            <form
              className="form"
              onSubmit={(e) => {
                e.preventDefault();
                void submit();
              }}
            >
              {persona !== "automation" && (
                <p className="permission-note">
                  Select Program operator to link approved scheduled work.
                </p>
              )}
              <fieldset
                disabled={
                  persona !== "automation" ||
                  !!error ||
                  loading ||
                  mutation.busy ||
                  mutation.pending ||
                  preparing
                }
              >
                <label>
                  Approved scheduled job
                  <select
                    required
                    aria-label="Approved scheduled job"
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    <option value="">Choose a scheduled job</option>
                    {c.jobs.map((j) => (
                      <option
                        key={j.id}
                        value={j.id}
                        disabled={c.links.some((l) => l.job_id === j.id)}
                      >
                        {j.id} ·{" "}
                        {c.links.some((l) => l.job_id === j.id)
                          ? "already linked"
                          : j.slot_id}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="muted">
                  Linking adds the scheduled work to this milestone. Its
                  forecast remains conditional on testing and engineering
                  review.
                </p>
                <button
                  className="primary"
                  type="submit"
                  disabled={!job || !pending.some((j) => j.id === job.id)}
                >
                  Link job to program plan
                </button>
              </fieldset>
            </form>
          )}
        </Panel>
      </div>
      <Panel title="Linked validation tasks">
        {c.links.length ? (
          <Table headers={["Task", "Job", "Forecast", "Status"]}>
            {c.links.map((l) => (
              <tr key={l.id} id={"link-" + l.id}>
                <td>
                  <strong>{l.task.name}</strong>
                  <span className="record-link cell-secondary">
                    {l.task.id}
                  </span>
                  <span className="record-link cell-secondary">
                    Planner link: {l.id}
                  </span>
                </td>
                <td>
                  <Link
                    className="record-link"
                    to={"/validation/jobs/" + l.job_id}
                  >
                    {l.job_id}
                  </Link>
                </td>
                <td>{date(l.task.forecast_at)}</td>
                <td>
                  <Badge value={l.task.status} />
                </td>
              </tr>
            ))}
          </Table>
        ) : (
          <Empty>
            No implementation links recorded. The baseline and evidence
            dependency are preserved.
          </Empty>
        )}
      </Panel>
      <Banner>
        Scheduling leaves the evidence obligation open. Forecasts are
        conditional on successful testing and engineering review.
      </Banner>
      <Panel title="Program activity">
        <Audit events={c.audit} />
      </Panel>
    </>
  );
}
