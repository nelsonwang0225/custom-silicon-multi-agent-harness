import "./source-testops.css";
import { LabCompletion } from "./lab-completion";
import { usePortfolioFilter, ProgramCell } from "./portfolio-filters";
import { LabPortfolio } from "./lab-portfolio";
import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { type Schema } from "./api";
import { useData, type Case } from "./data";
import { ScheduledWork } from "./case-progress";
import { OptionSummary } from "./engineering";
import { useMutation } from "./mutations";
import {
  Badge,
  Banner,
  date,
  Empty,
  Facts,
  Fresh,
  Heading,
  human,
  money,
  number,
  Panel,
  Reasons,
  SearchField,
  Table,
  Timing,
} from "./ui";
export function Validation() {
  const { data } = useData();
  const params = useParams();
  const scope = usePortfolioFilter();
  const [query, setQuery] = useSearchParams();
  const [resourceState, setResourceState] = useState("all");
  const [lab, setLab] = useState("all");
  const [configuration, setConfiguration] = useState("all");
  useEffect(() => {
    setLab("all");
    setConfiguration("all");
  }, [scope.key]);
  useEffect(() => {
    setResourceState("all");
  }, [params.screen]);
  const [search, setSearch] = useState(""),
    [filter, setFilter] = useState("all");
  const candidates =
    data?.cases.filter((c) => scope.matches(c.change.program_id)) || [];
  const c =
    candidates.find((c) => c.change.id === query.get("change")) ||
    candidates[0];
  useEffect(() => {
    if (c && c.change.id !== (query.get("change") || data?.cases[0]?.change.id))
      setQuery({ change: c.change.id }, { replace: true });
  }, [c?.change.id, query, setQuery]);
  if (!data) return null;
  if (params.historyId) {
    const j = data.history.find((j) => j.id === params.historyId);
    return j ? (
      <>
        <Heading eyebrow="Stratos TestOps / Recorded execution" title={j.id}>
          <Badge value={j.status} />
        </Heading>
        <TestLifecycle
          steps={[
            ["Execution", "Completed", "done"],
            ["Results", `${j.result_ids.length} observations`, "done"],
            [
              "Engineering review",
              j.status === "engineering_disposition_pending"
                ? "Pending"
                : "See source disposition",
              "pending",
            ],
            ["Customer acceptance", "Separate decision", "pending"],
          ]}
        />
        <Panel title="Imported lab record">
          <Facts
            items={[
              ["Program", <ProgramCell id={j.program_id} />],
              ["Recorded by", j.recorded_by],
              ["Source reference", j.source_reference],
              ["Configuration", j.configuration_id],
              ["Sample", j.sample_id],
              ["Procedure", j.procedure_id],
              ["Lab", j.lab_id],
              ["Started", date(j.started_at)],
              ["Completed", date(j.completed_at)],
              [
                "Observations",
                j.result_ids.map((id) => (
                  <Link key={id} to={"/validation/results/" + id}>
                    {id}{" "}
                  </Link>
                )),
              ],
              ["Disposition note", j.note],
            ]}
          />
        </Panel>
        <Banner>
          Execution and passing observations do not establish engineering or
          customer acceptance.
        </Banner>
      </>
    ) : (
      <Empty>Historical job not found.</Empty>
    );
  }
  if (!c)
    return <Empty>No change requests are available for validation.</Empty>;
  const screen = params.screen || "coverage";
  if (params.jobId) {
    const job = data.cases
      .flatMap((c) => c.jobs)
      .find((j) => j.id === params.jobId);
    return job ? (
      <JobDetail job={job} />
    ) : (
      <Empty>Job not found. Refresh to retrieve newly scheduled work.</Empty>
    );
  }
  if (params.resultId) {
    const evidence = data.cases
      .flatMap((c) => c.coverage.items)
      .find((r) => r.result.id === params.resultId);
    if (!evidence) return <Empty>Evidence record not found.</Empty>;
    const r = evidence.result;
    const completion = data.cases
      .flatMap((c) => c.jobs)
      .find((j) => j.completion?.result_id === r.id)?.completion;
    const historicalJob = data.history.find((j) => j.result_ids.includes(r.id));
    return (
      <>
        <Heading eyebrow="Stratos TestOps / Result record" title={r.id}>
          <Badge value={r.status} /> <Fresh record={r} />
        </Heading>
        <div className="testops-object-summary">
          <div>
            <span>Execution state</span>
            <strong>{human(r.status)}</strong>
          </div>
          <div>
            <span>Recorded criteria</span>
            <strong>{r.criteria_passed ? "Passed" : "Not passed"}</strong>
          </div>
          <div>
            <span>Observed suite</span>
            <strong>{r.actual_suite_minutes} min</strong>
          </div>
          <div>
            <span>Sample</span>
            <strong>{r.sample_id}</strong>
          </div>
          <div>
            <span>Completed · UTC</span>
            <strong>{date(r.completed_at)}</strong>
          </div>
        </div>
        <Banner tone={evidence.satisfies ? "good" : "warning"}>
          {evidence.satisfies
            ? "This result satisfies the coverage obligation."
            : "This historical result does not satisfy the requested evidence obligation."}
          <Reasons values={evidence.mismatch_reasons} />
        </Banner>
        <div className="split">
          <Panel title="Observed evidence">
            <Facts
              items={[
                [
                  "Configuration",
                  r.configuration_id + " · v" + r.configuration_content_version,
                ],
                ["Product revision", r.product_revision],
                [
                  "Workload",
                  r.workload_profile_id +
                    " · v" +
                    r.workload_profile_content_version,
                ],
                ["Sample", r.sample_id],
                ["Observed duration", r.actual_suite_minutes + " min"],
                [
                  "Historical criteria evaluation",
                  r.criteria_passed
                    ? "Passed for this recorded run"
                    : "Not passed",
                ],
                ["Completed", date(r.completed_at)],
              ]}
            />
            <Table headers={["Input tokens", "Observed minutes"]}>
              {Object.entries(r.observed_minutes_by_context_bin).map(
                ([k, v]) => (
                  <tr key={k}>
                    <td>{number(Number(k))}</td>
                    <td>{v}</td>
                  </tr>
                ),
              )}
            </Table>
          </Panel>
          <Panel title="Captured configuration">
            <Facts
              items={[
                ["Model", r.configuration_snapshot.model_bundle_id],
                ["Firmware", r.configuration_snapshot.firmware],
                ["Runtime", r.configuration_snapshot.runtime],
                ["Memory", r.configuration_snapshot.memory_configuration],
                ["Quantization", r.configuration_snapshot.quantization],
                ["Devices", r.configuration_snapshot.device_count],
                [
                  "Criteria",
                  r.acceptance_limits_ref +
                    " · v" +
                    r.acceptance_criteria_content_version,
                ],
                ["Criteria scope", r.criteria_snapshot.scope],
                [
                  "Procedure provenance",
                  completion
                    ? `${completion.procedure_id} · v${completion.procedure_content_version}`
                    : historicalJob
                      ? `${historicalJob.procedure_id} · Version not recorded`
                      : "Not recorded with this evidence",
                ],
                [
                  "Execution record",
                  historicalJob ? (
                    <Link to={"/validation/history/" + historicalJob.id}>
                      {historicalJob.id}
                    </Link>
                  ) : completion ? (
                    <Link to={"/validation/jobs/" + completion.job_id}>
                      {completion.job_id}
                    </Link>
                  ) : (
                    "No linked execution record"
                  ),
                ],
              ]}
            />
          </Panel>
        </div>
      </>
    );
  }
  if (
    !["coverage", "options", "samples", "schedule", "jobs", "history"].includes(
      screen,
    )
  )
    return (
      <Empty>Validation page not found. Choose a page in the navigation.</Empty>
    );
  const titles: Record<string, string> = {
    coverage: "Lab overview",
    options: "Validation options",
    samples: "Sample inventory",
    schedule: "Lab schedule",
    jobs: "Jobs queue",
    history: "Lab execution history",
  };
  return (
    <>
      <Heading
        eyebrow="Stratos TestOps / Validation & qualification"
        title={titles[screen] || "Stratos TestOps"}
        action={
          screen === "options" && c.options.some((o) => o.resource_eligible) ? (
            <Link
              className="button primary"
              to={"/engineering/changes/" + c.change.id + "/draft"}
            >
              Draft assessment
            </Link>
          ) : undefined
        }
      >
        <span>
          {c.change.id} · {c.config.id} · {c.targetWorkload.id}
        </span>
      </Heading>
      <div className="toolbar testops-filters">
        {scope.controls}
        {["jobs", "history", "samples", "schedule"].includes(screen) && (
          <select
            aria-label="Product configuration"
            value={configuration}
            onChange={(e) => setConfiguration(e.target.value)}
          >
            <option value="all">All products / revisions</option>
            {[
              ...new Map(
                data.cases
                  .flatMap((c) => [
                    c.config,
                    ...c.coverage.items.map(
                      (i) => i.result.configuration_snapshot,
                    ),
                  ])
                  .map((c) => [c.id, c]),
              ).values(),
            ]
              .filter((c) => scope.matches(c.program_id))
              .map((c) => (
                <option key={c.id} value={c.id}>
                  {c.product_id} · {c.product_revision} · {c.id}
                </option>
              ))}
          </select>
        )}
        {["jobs", "history"].includes(screen) && (
          <SearchField
            label="Search jobs"
            value={search}
            onChange={setSearch}
          />
        )}

        {["jobs", "history", "samples", "schedule"].includes(screen) && (
          <>
            <select
              aria-label="Lab filter"
              value={lab}
              onChange={(e) => setLab(e.target.value)}
            >
              <option value="all">All labs</option>
              {data.labs
                .filter((l) => scope.matches(l.program_id))
                .map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.id} · {l.campus}
                  </option>
                ))}
            </select>
            <select
              aria-label="Resource status"
              value={resourceState}
              onChange={(e) => setResourceState(e.target.value)}
            >
              <option value="all">All states</option>
              {(screen === "jobs"
                ? ["scheduled"]
                : screen === "history"
                  ? ["completed", "engineering_disposition_pending"]
                  : ["available", "reserved", "unavailable"]
              ).map((s) => (
                <option key={s} value={s}>
                  {human(s)}
                </option>
              ))}
            </select>
          </>
        )}
      </div>
      {screen === "coverage" && <TestOpsOverview matches={scope.matches} />}
      {["coverage", "options", "jobs"].includes(screen) &&
        data.cases.length > 1 && (
          <label>
            Change
            <select
              aria-label="Change"
              value={c.change.id}
              onChange={(e) => setQuery({ change: e.target.value })}
            >
              {candidates.map((x) => (
                <option key={x.change.id} value={x.change.id}>
                  {x.change.id} · {x.change.title}
                </option>
              ))}
            </select>
          </label>
        )}
      {screen === "coverage" && (
        <section id="coverage" className="testops-coverage">
          <div className="testops-section-heading">
            <div>
              <div className="eyebrow">Qualification evidence</div>
              <h2>Evidence & coverage</h2>
            </div>
            <span className="metadata">
              {c.change.id} · {c.target.configuration_id}
            </span>
          </div>
          <Banner tone={c.coverage.coverage_satisfied ? "good" : "warning"}>
            {c.coverage.coverage_satisfied
              ? "Requested coverage is satisfied; engineering disposition is separate."
              : "Requested evidence is incomplete. Missing coverage does not establish a hardware failure."}
          </Banner>
          <div className="split wide-left">
            <Panel title="Existing test evidence">
              <Table
                headers={[
                  "Result / configuration",
                  "Profile / duration",
                  "Applicability",
                ]}
              >
                {c.coverage.items.map((i) => (
                  <tr key={i.result.id}>
                    <td>
                      <Link
                        className="strong-link"
                        to={"/validation/results/" + i.result.id}
                      >
                        {i.result.id}
                      </Link>
                      <span className="cell-secondary">
                        {i.result.product_revision} ·{" "}
                        {i.result.configuration_id} v
                        {i.result.configuration_content_version}
                      </span>
                    </td>
                    <td>
                      {i.result.workload_profile_id}
                      <span className="cell-secondary">
                        {i.result.actual_suite_minutes} min observed
                      </span>
                    </td>
                    <td>
                      <Badge
                        value={
                          i.satisfies ? "applicable" : "insufficient coverage"
                        }
                      />
                      <Reasons values={i.mismatch_reasons} />
                    </td>
                  </tr>
                ))}
              </Table>
            </Panel>
            <Panel title="Required coverage">
              <Facts
                items={[
                  ["Requested workload", c.targetWorkload.id],
                  ["Configuration", c.target.configuration_id],
                  [
                    "Total suite",
                    c.targetWorkload.total_suite_minutes + " min",
                  ],
                  [
                    "Required bins",
                    c.targetWorkload.context_bins.map(number).join(" / "),
                  ],
                  [
                    "Per-bin duration",
                    c.procedures
                      .map((p) => p.per_bin_minutes + " min")
                      .join(", "),
                  ],
                  ["Review deadline", date(c.milestone.baseline_at)],
                ]}
              />
              <div className="testops-procedures">
                <span className="metadata">Controlled test procedures</span>
                {c.procedures.map((p) => (
                  <Link
                    key={p.id}
                    to={"/engineering/documents/" + p.document_id}
                  >
                    <strong>{p.id}</strong>
                    <span>
                      v{p.content_version} · {human(p.status)}
                    </span>
                  </Link>
                ))}
                {!c.procedures.length && (
                  <span className="muted">
                    No procedure loaded for this selection.
                  </span>
                )}
              </div>
              <div className="padded">
                <Link
                  className="button primary"
                  to={"/validation/options?change=" + c.change.id}
                >
                  Compare validation options
                </Link>
              </div>
            </Panel>
          </div>
        </section>
      )}
      {screen === "options" && (
        <>
          <ScheduledWork c={c} />
          {!c.options.some((o) => o.resource_eligible) && (
            <Banner tone="warning">
              No resources are currently eligible for a new draft. Review the
              restrictions below
              {c.jobs.length
                ? " or inspect the existing reservation above"
                : ""}
              .
            </Banner>
          )}
          <div className="toolbar">
            <SearchField
              value={search}
              onChange={setSearch}
              label="Search options"
            />
            <select
              aria-label="Option eligibility"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All combinations</option>
              <option value="eligible">Resource eligible</option>
              <option value="ineligible">Resource ineligible</option>
            </select>
          </div>
          <Banner>
            Costs, eligibility and forecasts are calculated by the API. A
            qualified late option remains eligible; no option is preselected.
          </Banner>
          <div className="options-grid">
            {c.options
              .filter(
                (o) =>
                  (o.slot.id + " " + o.sample.id + " " + o.lab.id)
                    .toLowerCase()
                    .includes(search.toLowerCase()) &&
                  (filter === "all" ||
                    o.resource_eligible === (filter === "eligible")),
              )
              .map((o) => (
                <Panel
                  key={o.slot.id + o.sample.id}
                  title={o.slot.id}
                  aside={
                    <Badge
                      value={o.resource_eligible ? "eligible" : "ineligible"}
                      tone={o.resource_eligible ? "good" : "warning"}
                    />
                  }
                >
                  <OptionSummary option={o} />
                  <div className="padded metadata">
                    Slot {human(o.slot.availability)} · Sample{" "}
                    {human(o.sample.availability)}
                    <br />
                    <Fresh record={o.slot} />
                  </div>
                </Panel>
              ))}
          </div>
          {!c.options.some(
            (o) =>
              (o.slot.id + " " + o.sample.id + " " + o.lab.id)
                .toLowerCase()
                .includes(search.toLowerCase()) &&
              (filter === "all" ||
                o.resource_eligible === (filter === "eligible")),
          ) && <Empty>No options match these filters.</Empty>}
        </>
      )}
      {screen === "samples" && (
        <>
          <ResourceStrip matches={scope.matches} />
          <div className="toolbar">
            <SearchField
              value={search}
              onChange={setSearch}
              label="Search samples"
            />
          </div>
          <Panel title="Lab samples">
            <Table
              headers={[
                "Sample",
                "Configuration",
                "Location / availability",
                "Manufacturing provenance",
                "Relevant restrictions",
              ]}
            >
              {data.samples
                .filter(
                  (s) =>
                    scope.matches(s.program_id) &&
                    (configuration === "all" ||
                      s.configuration_id === configuration) &&
                    (resourceState === "all" ||
                      s.availability === resourceState) &&
                    (lab === "all" ||
                      data.labs.find((l) => l.id === lab)?.campus === s.campus),
                )
                .filter((s) =>
                  (s.id + " " + s.configuration_id)
                    .toLowerCase()
                    .includes(search.toLowerCase()),
                )
                .map((s) => {
                  const unit = data.units.find((u) => u.id === s.unit_id),
                    lot = data.lots.find((l) => l.id === unit?.source_lot_id);
                  return (
                    <tr key={s.id}>
                      <td>
                        <strong>{s.id}</strong>
                        <span className="cell-secondary">
                          <ProgramCell id={s.program_id} />
                        </span>
                        <span className="cell-secondary">
                          Availability v{s.availability_version}
                        </span>
                      </td>
                      <td>{s.configuration_id}</td>
                      <td>
                        {s.campus}
                        <span className="cell-secondary">
                          <Badge value={s.availability} />
                        </span>
                        {s.reserved_by_job_id && (
                          <Link
                            className="record-link"
                            to={"/validation/jobs/" + s.reserved_by_job_id}
                          >
                            Reserved job
                          </Link>
                        )}
                      </td>
                      <td>
                        <Link to={"/manufacturing/units/" + s.unit_id}>
                          {s.unit_id}
                        </Link>
                        <span className="cell-secondary">
                          <Link
                            to={"/manufacturing/lots/" + unit?.source_lot_id}
                          >
                            {unit?.source_lot_id}
                          </Link>
                        </span>
                      </td>
                      <td>
                        <strong>Unit</strong>
                        <Reasons values={unit?.restrictions || []} />
                        <strong>Lot</strong>
                        <Reasons values={lot?.restrictions || []} />
                      </td>
                    </tr>
                  );
                })}
            </Table>
            {!data.samples.some((s) =>
              (s.id + " " + s.configuration_id)
                .toLowerCase()
                .includes(search.toLowerCase()),
            ) && <Empty>No samples match this search.</Empty>}
          </Panel>
        </>
      )}
      {screen === "schedule" && (
        <>
          <ResourceStrip matches={scope.matches} />
          <Panel title="Slot calendar — UTC">
            <Table
              headers={[
                "Slot / lab",
                "Reservation window",
                "Availability",
                "Supported configuration",
                "Booking",
              ]}
            >
              {data.slots
                .filter(
                  (s) =>
                    scope.matches(s.program_id) &&
                    (configuration === "all" ||
                      ("configuration_id" in s
                        ? s.configuration_id === configuration
                        : data.labs
                            .find((l) => l.id === s.lab_id)
                            ?.supported_configuration_ids.includes(
                              configuration,
                            ))) &&
                    (resourceState === "all" ||
                      s.availability === resourceState) &&
                    (lab === "all" || s.lab_id === lab),
                )
                .sort((a, b) => a.starts_at.localeCompare(b.starts_at))
                .map((s) => (
                  <tr key={s.id}>
                    <td>
                      <strong>{s.id}</strong>
                      <span className="cell-secondary">{s.lab_id}</span>
                      <ProgramCell id={s.program_id} />
                    </td>
                    <td>
                      {date(s.starts_at)}
                      <span className="cell-secondary">
                        through {date(s.ends_at)}
                      </span>
                    </td>
                    <td>
                      <Badge value={s.availability} />
                    </td>
                    <td>
                      {data.labs
                        .find((l) => l.id === s.lab_id)
                        ?.supported_configuration_ids.join(", ")}
                    </td>
                    <td>
                      {s.reserved_by_job_id ? (
                        <Link to={"/validation/jobs/" + s.reserved_by_job_id}>
                          {s.reserved_by_job_id}
                        </Link>
                      ) : (
                        "No reservation"
                      )}
                    </td>
                  </tr>
                ))}
            </Table>
          </Panel>
          <Panel title="Reservation details">
            {c.jobs.length ? (
              <Table
                headers={["Reservation", "Sample", "Setup + execution", "Job"]}
              >
                {c.jobs.map((j) => (
                  <tr key={j.id}>
                    <td className="record-link">{j.reservation.id}</td>
                    <td>{j.reservation.sample_id}</td>
                    <td>
                      {date(j.reservation.starts_at)}
                      <span className="cell-secondary">
                        to {date(j.reservation.ends_at)}
                      </span>
                    </td>
                    <td>
                      <Link to={"/validation/jobs/" + j.id}>Open job</Link>
                    </td>
                  </tr>
                ))}
              </Table>
            ) : (
              <Empty>
                No reservations have been created. Slots show current
                availability.
              </Empty>
            )}
          </Panel>
        </>
      )}
      {screen === "jobs" && (
        <>
          <LabPortfolio
            matches={scope.matches}
            status={resourceState}
            lab={lab}
            configuration={configuration}
            search={search}
          />
          <Jobs key={c.change.id} c={c} />
        </>
      )}
      {screen === "history" && (
        <>
          <Banner>
            Imported lab history and recorded lab completions. Booking, criteria
            evaluation and engineering approval remain separate.
          </Banner>
          <LabPortfolio
            matches={scope.matches}
            history
            status={resourceState}
            lab={lab}
            configuration={configuration}
            search={search}
          />
        </>
      )}
    </>
  );
}
function Jobs({ c }: { c: Case }) {
  const { persona, error, loading } = useData();
  const navigate = useNavigate();
  const [selected, setSelected] = useState("");
  const mutation = useMutation("booking:" + c.change.id, (r) =>
    navigate("/validation/jobs/" + r.id),
  );
  const plan = c.change.plans.find((p) => p.id === selected);
  const currentOption = c.options.find(
    (o) => o.slot.id === plan?.slot_id && o.sample.id === plan?.sample_id,
  );
  const canSchedule = (p: Schema["PlanView"]) => {
    const option = c.options.find(
      (o) => o.slot.id === p.slot_id && o.sample.id === p.sample_id,
    );
    return (
      p.state === "approved" &&
      !p.job_id &&
      !!option?.approval_eligible &&
      option.cost_cents === p.cost_cents &&
      JSON.stringify(option.timing) === JSON.stringify(p.timing)
    );
  };
  return (
    <>
      <Banner>
        A scheduled job reserves resources. It does not execute tests, generate
        results or qualify hardware.
      </Banner>
      <Panel title="Scheduled work">
        {c.jobs.length ? (
          <Table
            headers={[
              "Job",
              "Resources",
              "Review-ready forecast",
              "Status",
              "Follow-through",
            ]}
          >
            {c.jobs.map((j) => (
              <tr key={j.id}>
                <td>
                  <Link className="record-link" to={"/validation/jobs/" + j.id}>
                    {j.id}
                  </Link>
                </td>
                <td>
                  {j.slot_id}
                  <span className="cell-secondary">{j.sample_id}</span>
                </td>
                <td>{date(j.timing.review_ready_at)}</td>
                <td>
                  <Badge value={j.status} />
                </td>
                <td>
                  <Badge
                    value={
                      c.links.some((l) => l.job_id === j.id)
                        ? "linked"
                        : "pending planner link"
                    }
                  />
                </td>
              </tr>
            ))}
          </Table>
        ) : (
          <Empty>
            No jobs scheduled. Select an approved plan below to reserve its
            exact slot and sample.
          </Empty>
        )}
      </Panel>
      {mutation.pending ||
      !c.jobs.length ||
      c.change.plans.some(canSchedule) ? (
        <div className="split">
          <Panel title="Schedule approved plan">
            {mutation.feedback}
            <form
              className="form"
              onSubmit={(e) => {
                e.preventDefault();
                if (plan?.decision_id) {
                  const body: Schema["JobInput"] = {
                    plan_id: plan.id,
                    approval_id: plan.decision_id,
                  };
                  void mutation.submit("/validation/jobs", body);
                }
              }}
            >
              {persona !== "automation" && (
                <p className="permission-note">
                  Select Program operator to schedule. An engineer decision is
                  required first.
                </p>
              )}
              <fieldset
                disabled={
                  persona !== "automation" ||
                  !!error ||
                  loading ||
                  mutation.busy ||
                  mutation.pending
                }
              >
                <label>
                  Approved plan
                  <select
                    required
                    aria-label="Approved plan"
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    <option value="">Choose an approved plan</option>
                    {c.change.plans.map((p) => (
                      <option
                        value={p.id}
                        key={p.id}
                        disabled={!canSchedule(p)}
                      >
                        {p.id} · {p.slot_id} · {money(p.cost_cents)} ·{" "}
                        {p.job_id
                          ? "already scheduled"
                          : p.state === "approved" && !canSchedule(p)
                            ? "resources unavailable or changed"
                            : p.state}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="primary"
                  type="submit"
                  disabled={!plan || !canSchedule(plan)}
                >
                  Schedule exact validation job
                </button>
              </fieldset>
            </form>
          </Panel>
          <Panel title="Selected work">
            {plan && !plan.job_id && !canSchedule(plan) && (
              <Banner tone="warning">
                This plan cannot currently be scheduled. Refresh and reassess
                changed resources or obtain an approved decision.
                <Reasons
                  values={[
                    ...(currentOption?.eligibility_reasons || []),
                    ...(currentOption?.approval_reasons || []),
                  ]}
                />
              </Banner>
            )}
            {plan ? (
              <>
                <Facts
                  items={[
                    [
                      "Plan",
                      <Link
                        className="record-link"
                        to={"/engineering/plans/" + plan.id}
                      >
                        {plan.id}
                      </Link>,
                    ],
                    ["Configuration", plan.configuration_id],
                    ["Sample / slot", plan.sample_id + " / " + plan.slot_id],
                    ["Cost", money(plan.cost_cents)],
                    ["Decision", <Badge value={plan.state} />],
                  ]}
                />
                <Timing timing={plan.timing} />
              </>
            ) : (
              <Empty>Select a plan to inspect its approved work.</Empty>
            )}
          </Panel>
        </div>
      ) : (
        <ScheduledWork c={c} />
      )}
    </>
  );
}
function JobDetail({ job }: { job: Schema["JobView"] }) {
  const { data } = useData();
  const c = data!.cases.find((c) => c.change.id === job.change_id)!;
  const observation = c.coverage.items.find(
    (e) => e.result.id === job.completion?.result_id,
  )?.result;
  return (
    <>
      <Heading
        eyebrow="Stratos TestOps / Job record"
        title="Validation job"
        action={
          <Link className="button" to="/validation/jobs">
            Jobs queue
          </Link>
        }
      >
        <span className="record-link">{job.id}</span> ·{" "}
        <Badge value={observation?.status || job.status} />
      </Heading>
      <div className="testops-object-summary">
        <div>
          <span>Configuration</span>
          <strong>{job.configuration_id}</strong>
        </div>
        <div>
          <span>Sample</span>
          <strong>{job.sample_id}</strong>
        </div>
        <div>
          <span>Procedure</span>
          <strong>{job.procedure_id}</strong>
        </div>
        <div>
          <span>Resource</span>
          <strong>{job.lab_id}</strong>
          <small>{job.slot_id}</small>
        </div>
        <div>
          <span>Scheduled start · UTC</span>
          <strong>{date(job.timing.lab_start_at)}</strong>
        </div>
      </div>
      <TestLifecycle
        steps={[
          ["Scheduled", "Reservation confirmed", "done"],
          [
            "Execution",
            job.completion ? "Completion recorded" : "Not recorded",
            job.completion ? "done" : "pending",
          ],
          [
            "Result",
            observation
              ? human(observation.status)
              : job.completion
                ? "Received"
                : "Not available",
            job.completion ? "done" : "pending",
          ],
          [
            "Engineering review",
            c.physical?.job?.id === job.id
              ? human(c.physical.engineering_status)
              : "Not recorded",
            c.physical?.job?.id === job.id &&
            c.physical.engineering_status === "approved"
              ? "done"
              : "pending",
          ],
          ["Customer acceptance", "Separate decision", "pending"],
        ]}
      />
      <p className="testops-boundary-note">
        Booking remains scheduled. Lab completion, criteria evaluation and
        engineering approval are separate records.
      </p>
      <LabCompletion key={job.id} job={job} />
      {!c.links.some((l) => l.job_id === job.id) && (
        <Banner tone="warning">
          Lab booking is complete; Stratos ProgramOps follow-through is missing.{" "}
          <Link to={"/programs/" + job.program_id}>
            Link this scheduled job
          </Link>
          .
        </Banner>
      )}
      <div className="split">
        <Panel title="Scheduled scope">
          <Facts
            items={[
              [
                "Plan",
                <Link
                  className="record-link"
                  to={"/engineering/plans/" + job.plan_id}
                >
                  {job.plan_id}
                </Link>,
              ],
              [
                "Approval",
                <span className="record-link">{job.approval_id}</span>,
              ],
              [
                "Configuration / workload",
                job.configuration_id + " / " + job.workload_profile_id,
              ],
              ["Procedure", job.procedure_id],
              ["Lab / slot", job.lab_id + " / " + job.slot_id],
              ["Sample", job.sample_id],
              ["Incremental cost", money(job.cost_cents)],
              ["Engineering review", job.review_minutes + " min"],
            ]}
          />
          <Timing timing={job.timing} />
        </Panel>
        <Panel title="Confirmed resource reservation">
          <Facts
            items={[
              [
                "Reservation",
                <span className="record-link">{job.reservation.id}</span>,
              ],
              [
                "Reserved interval",
                date(job.reservation.starts_at) +
                  " → " +
                  date(job.reservation.ends_at),
              ],
              [
                "Slot availability version",
                `${job.reservation.slot_version_before} → ${job.reservation.slot_version_after}`,
              ],
              [
                "Sample availability version",
                `${job.reservation.sample_version_before} → ${job.reservation.sample_version_after}`,
              ],
              ["Recorded", date(job.updated_at)],
            ]}
          />
        </Panel>
      </div>
    </>
  );
}

function TestLifecycle({
  steps,
}: {
  steps: [string, string, "done" | "pending"][];
}) {
  return (
    <ol className="testops-lifecycle" aria-label="Validation lifecycle">
      {steps.map(([label, detail, state], index) => (
        <li className={state} key={label}>
          <span className="testops-step-index" aria-hidden="true">
            {index + 1}
          </span>
          <div>
            <strong>{label}</strong>
            <span>{detail}</span>
          </div>
        </li>
      ))}
    </ol>
  );
}

function TestOpsOverview({ matches }: { matches: (id: string) => boolean }) {
  const { data } = useData();
  if (!data) return null;
  const cases = data.cases.filter((c) => matches(c.change.program_id));
  const jobs = cases.flatMap((c) => c.jobs);
  const pending = jobs.filter((j) => !j.completion);
  const historical = data.history.filter((j) => matches(j.program_id));
  const results = [
    ...new Map(
      cases.flatMap((c) =>
        c.coverage.items.map((i) => [i.result.id, i.result] as const),
      ),
    ).values(),
  ];
  const running = results.filter((r) => r.status === "running");
  const completed = new Set([
    ...historical.map((j) => j.id),
    ...jobs.filter((j) => j.completion).map((j) => j.id),
  ]).size;
  const incomplete = cases.filter((c) => !c.coverage.coverage_satisfied);
  const recent = [...historical]
    .sort((a, b) => b.completed_at.localeCompare(a.completed_at))
    .slice(0, 3);
  const scheduled = [...pending]
    .sort((a, b) => a.timing.lab_start_at.localeCompare(b.timing.lab_start_at))
    .slice(0, 3);
  return (
    <div className="testops-overview">
      <div
        className="testops-operation-counts"
        aria-label="Lab operational summary"
      >
        <Link to="/validation/jobs">
          <span>Scheduled</span>
          <strong>{pending.length}</strong>
          <small>Awaiting a completion record</small>
        </Link>
        <a href="#coverage">
          <span>Running results</span>
          <strong>{running.length}</strong>
          <small>Source observations in progress</small>
        </a>
        <Link to="/validation/history">
          <span>Completed executions</span>
          <strong>{completed}</strong>
          <small>Includes imported lab history</small>
        </Link>
        <a href="#coverage" className={incomplete.length ? "attention" : ""}>
          <span>Evidence gaps</span>
          <strong>{incomplete.length}</strong>
          <small>Changes with incomplete coverage</small>
        </a>
      </div>
      <div className="testops-operations-grid">
        <Panel
          title={pending.length ? "Upcoming jobs" : "Recent execution"}
          aside={
            <Link
              to={pending.length ? "/validation/jobs" : "/validation/history"}
            >
              {pending.length ? "All jobs" : "Execution history"}
            </Link>
          }
        >
          <Table
            headers={[
              "Job / configuration",
              "Sample / resource",
              pending.length ? "Scheduled start · UTC" : "Completed · UTC",
            ]}
          >
            {scheduled.map((j) => (
              <tr key={j.id}>
                <td>
                  <Link className="strong-link" to={"/validation/jobs/" + j.id}>
                    {j.id}
                  </Link>
                  <span className="cell-secondary">{j.configuration_id}</span>
                </td>
                <td>
                  {j.sample_id}
                  <span className="cell-secondary">{j.lab_id}</span>
                </td>
                <td>
                  {date(j.timing.lab_start_at)}
                  <span className="cell-secondary">Reservation confirmed</span>
                </td>
              </tr>
            ))}
            {!pending.length &&
              recent.map((j) => (
                <tr key={j.id}>
                  <td>
                    <Link
                      className="strong-link"
                      to={"/validation/history/" + j.id}
                    >
                      {j.id}
                    </Link>
                    <span className="cell-secondary">{j.configuration_id}</span>
                  </td>
                  <td>
                    {j.sample_id}
                    <span className="cell-secondary">{j.lab_id}</span>
                  </td>
                  <td>
                    {date(j.completed_at)}
                    <span className="cell-secondary">
                      Imported execution · {j.result_ids.length} observations
                    </span>
                  </td>
                </tr>
              ))}
          </Table>
          {!pending.length && !recent.length && (
            <Empty>No scheduled or completed jobs in this portfolio.</Empty>
          )}
        </Panel>
        <Panel
          title="Resource readiness"
          aside={<Link to="/validation/schedule">Schedule</Link>}
        >
          <ResourceStrip matches={matches} compact />
          <div className="testops-resource-note">
            Availability describes resources. Qualification comes from
            applicable evidence and review.
          </div>
        </Panel>
      </div>
    </div>
  );
}

function ResourceStrip({
  matches,
  compact = false,
}: {
  matches: (id: string) => boolean;
  compact?: boolean;
}) {
  const { data } = useData();
  if (!data) return null;
  const samples = data.samples.filter((s) => matches(s.program_id));
  const slots = data.slots.filter((s) => matches(s.program_id));
  const labs = data.labs.filter((l) => matches(l.program_id));
  return (
    <div
      className={"testops-resource-strip" + (compact ? " compact" : "")}
      aria-label="Lab resources in selected portfolio"
    >
      <div>
        <span>Available samples</span>
        <strong>
          {samples.filter((s) => s.availability === "available").length}
          <small> / {samples.length}</small>
        </strong>
      </div>
      <div>
        <span>Available slots</span>
        <strong>
          {slots.filter((s) => s.availability === "available").length}
          <small> / {slots.length}</small>
        </strong>
      </div>
      <div>
        <span>Reserved samples</span>
        <strong>
          {samples.filter((s) => s.availability === "reserved").length}
        </strong>
      </div>
      <div>
        <span>Lab resources</span>
        <strong>{labs.length}</strong>
      </div>
    </div>
  );
}
