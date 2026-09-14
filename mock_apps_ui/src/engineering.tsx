import { usePortfolioFilter, ProgramCell } from "./portfolio-filters";
import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { DraftPlan, ScopeChanges } from "./assessment-form";
import { SourceReference } from "./sources";
import {
  ArrowRight,
  ChevronRight,
  CircuitBoard,
  FileText,
  Layers3,
  Plus,
} from "lucide-react";
import { api, enc, errorMessage, type Schema } from "./api";
import { useData, useFormState, type Case } from "./data";
import {
  CaseState,
  CurrentValidationEvidence,
  caseStatus,
  caseNextAction,
  ScheduledWork,
} from "./case-progress";
import { useMutation } from "./mutations";
import {
  Audit,
  Badge,
  Banner,
  date,
  DocumentView,
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
import "./source-plm.css";

function ProductStructure({ cases }: { cases: Case[] }) {
  const products = [...new Set(cases.map((c) => c.config.product_id))];
  return (
    <aside className="plm-structure" aria-label="Product structure">
      <div className="plm-structure-heading">
        <Layers3 size={17} aria-hidden="true" />
        <h2>Product structure</h2>
      </div>
      <p className="plm-structure-caption">
        Configurations referenced by these changes
      </p>
      <div className="plm-structure-tree">
        {products.map((product) => {
          const productCases = cases.filter(
            (c) => c.config.product_id === product,
          );
          const configs = [
            ...new Map(
              productCases.map((c) => [c.config.id, c.config]),
            ).values(),
          ];
          return (
            <details key={product} open>
              <summary>
                <CircuitBoard size={16} aria-hidden="true" />
                <span>{product}</span>
              </summary>
              <ul>
                {configs.map((config) => (
                  <li key={config.id}>
                    <div className="plm-tree-config">
                      <span>{config.product_revision}</span>
                      <strong>{config.id}</strong>
                    </div>
                    <ul>
                      {productCases
                        .filter((c) => c.config.id === config.id)
                        .map((c) => (
                          <li key={c.change.id}>
                            <Link
                              aria-label={
                                "Open change " +
                                c.change.id +
                                " in product structure"
                              }
                              to={"/engineering/changes/" + c.change.id}
                            >
                              <FileText size={13} aria-hidden="true" />
                              {c.change.id}
                            </Link>
                          </li>
                        ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </details>
          );
        })}
        {!cases.length && <p className="muted">No matching configurations.</p>}
      </div>
    </aside>
  );
}

function EngineeringSections({ plan = false }: { plan?: boolean }) {
  const sections = plan
    ? [
        ["scope", "Scope"],
        ["assessment", "Assessment"],
        ["decision", "Decision"],
        ["sources", "Source versions"],
        ["history", "History"],
      ]
    : [
        ["overview", "Overview"],
        ["requirements", "Requirements"],
        ["configuration", "Configuration"],
        ["plans", "Plans"],
        ["documents", "Documents"],
        ["history", "History"],
      ];
  return (
    <nav
      className="plm-section-nav"
      aria-label={plan ? "Plan sections" : "Engineering object sections"}
    >
      {sections.map(([id, label]) => (
        <a key={id} href={"#plm-" + id}>
          {label}
        </a>
      ))}
    </nav>
  );
}

export function Engineering() {
  const { data } = useData();
  const scope = usePortfolioFilter();
  const [priority, setPriority] = useState("all");
  const [sort, setSort] = useState("priority");
  const [page, setPage] = useState(0);
  const params = useParams();
  const [query] = useSearchParams();
  const [search, setSearch] = useState(""),
    [status, setStatus] = useState("all");
  if (!data) return null;
  if (params.documentId)
    return (
      <>
        <Heading
          eyebrow="Stratos PLM / Controlled documents"
          title={params.documentId}
        />
        <DocumentView id={params.documentId} />
      </>
    );
  if (params.planId) {
    const c = data.cases.find((c) =>
      c.change.plans.some((p) => p.id === params.planId),
    );
    const plan = c?.change.plans.find((p) => p.id === params.planId);
    return c && plan ? (
      <PlanDetail key={plan.id} c={c} plan={plan} />
    ) : (
      <Empty>
        Plan not found in the authorized workspace. Refresh to check for
        external changes.
      </Empty>
    );
  }
  if (params.changeId) {
    if (params["*"] && params["*"] !== "draft")
      return <Empty>Engineering page not found.</Empty>;
    const c = data.cases.find((c) => c.change.id === params.changeId);
    if (!c) return <Empty>Change not found in this workspace.</Empty>;
    const supersedes = query.get("supersedes");
    const previous = c.change.plans.find((p) => p.id === supersedes);
    if (params["*"] === "draft" && supersedes && !previous)
      return (
        <Empty>
          Preceding plan not found in this change. No revision can be created
          from this reference.
        </Empty>
      );
    return params["*"] === "draft" ? (
      <DraftPlan
        key={c.change.id + (supersedes || "")}
        c={c}
        previous={previous}
      />
    ) : (
      <ChangeDetail c={c} />
    );
  }
  const cases = data.cases.filter(
    (c) =>
      (
        c.change.id +
        " " +
        c.change.title +
        " " +
        scope.text(c.change.program_id) +
        " " +
        c.change.owner
      )
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (status === "all" || caseStatus(c) === status) &&
      scope.matches(c.change.program_id) &&
      (priority === "all" || c.change.priority === priority),
  );
  cases.sort((a, b) =>
    sort === "updated"
      ? b.change.updated_at.localeCompare(a.change.updated_at)
      : { critical: 0, high: 1, medium: 2, low: 3 }[
          a.change.priority || "medium"
        ] -
          { critical: 0, high: 1, medium: 2, low: 3 }[
            b.change.priority || "medium"
          ] || a.milestone.baseline_at.localeCompare(b.milestone.baseline_at),
  );
  const pages = Math.max(1, Math.ceil(cases.length / 12));
  const visiblePage = Math.min(page, pages - 1);
  return (
    <div className="plm-registry">
      <Heading
        eyebrow="Stratos PLM / Engineering registry"
        title="Change requests"
      >
        Controlled requirements, configurations and engineering changes.
      </Heading>
      <div className="plm-registry-layout">
        <ProductStructure cases={cases} />
        <div className="plm-registry-main">
          <div className="toolbar" onChange={() => setPage(0)}>
            {scope.controls}
            <select
              aria-label="Priority filter"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            >
              <option value="all">All priorities</option>
              {["critical", "high", "medium", "low"].map((p) => (
                <option key={p} value={p}>
                  {human(p)}
                </option>
              ))}
            </select>
            <select
              aria-label="Sort changes"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="priority">Priority, then milestone</option>
              <option value="updated">Recently updated</option>
            </select>
            <SearchField
              value={search}
              onChange={setSearch}
              label="Search changes"
            />
            <select
              aria-label="Change status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="all">All case states</option>
              {[...new Set(data.cases.map(caseStatus))].map((s) => (
                <option key={s} value={s}>
                  {human(s)}
                </option>
              ))}
            </select>
            <span className="muted">
              {cases.length} change{cases.length === 1 ? "" : "s"}
            </span>
          </div>
          <Panel
            title="Change worklist"
            className="plm-worklist"
            aside={
              <span className="metadata">
                Source records · {cases.length} in view
              </span>
            }
          >
            <Table
              headers={[
                "Change / category",
                "Customer / program",
                "Product / revision",
                "Owner / updated",
                "Priority",
                "Status / next action",
              ]}
            >
              {cases.slice(visiblePage * 12, visiblePage * 12 + 12).map((c) => (
                <tr key={c.change.id}>
                  <td>
                    <Link
                      className="strong-link"
                      to={"/engineering/changes/" + c.change.id}
                    >
                      {c.change.id} <ArrowRight size={14} />
                    </Link>
                    <p>{c.change.title}</p>
                  </td>
                  <td>
                    <ProgramCell id={c.change.program_id} />
                  </td>
                  <td>
                    {c.config.product_id}
                    <span className="cell-secondary">
                      {c.config.product_revision} · {c.config.id}
                    </span>
                  </td>
                  <td>
                    {c.change.owner || "Unassigned"}
                    <span className="cell-secondary">
                      {date(c.change.updated_at)}
                    </span>
                  </td>
                  <td>
                    <Badge value={c.change.priority || "Not supplied"} />
                  </td>
                  <td>
                    <Badge value={caseStatus(c)} />
                    <span className="cell-secondary">{caseNextAction(c)}</span>
                  </td>
                </tr>
              ))}
            </Table>
            {!cases.length && <Empty>No changes match these filters.</Empty>}
            <div className="pagination">
              <button
                disabled={!visiblePage}
                onClick={() => setPage(visiblePage - 1)}
              >
                Previous
              </button>
              <span>
                Page {visiblePage + 1} of {pages} · {cases.length} changes
              </span>
              <button
                disabled={visiblePage + 1 >= pages}
                onClick={() => setPage(visiblePage + 1)}
              >
                Next
              </button>
            </div>
          </Panel>
        </div>
      </div>
      <div className="plm-registry-support">
        <Panel
          title="Controlled documents"
          aside={
            <Link to="/engineering/documents">
              Open library <ArrowRight size={13} aria-hidden="true" />
            </Link>
          }
        >
          <div className="link-list">
            {data.documents
              .filter((d) => scope.matches(d.program_id))
              .slice(0, 6)
              .map((d) => (
                <Link key={d.id} to={"/engineering/documents/" + d.id}>
                  <FileText size={17} />
                  <span>
                    {human(d.document_type)}
                    <small>
                      {d.id} · v{d.document_version}
                    </small>
                  </span>
                  <Badge value={d.status} />
                </Link>
              ))}
          </div>
        </Panel>
        <aside className="plm-review-boundary">
          <h2>Review boundary</h2>
          <p>
            A validation-plan decision authorizes the named lab work and program
            link only. The approved requirement baseline and customer acceptance
            remain separate.
          </p>
        </aside>
      </div>
    </div>
  );
}
function Comparison({ c }: { c: Case }) {
  return (
    <Panel
      title="Requirement and workload comparison"
      className="requirement-comparison"
      id="plm-requirements"
      aside={<Badge value="requested" />}
    >
      <Table
        headers={["Requirement", "Approved baseline", "Requested revision"]}
      >
        <tr>
          <td>Reference</td>
          <td>
            {c.baseline.id} · <Badge value={c.baseline.status} />
          </td>
          <td>
            {c.target.id} · <Badge value={c.target.status} />
          </td>
        </tr>
        {(
          [
            ["Workload profile", c.baselineWorkload.id, c.targetWorkload.id],
            [
              "Input context bins",
              c.baselineWorkload.context_bins.map(number).join(" / "),
              c.targetWorkload.context_bins.map(number).join(" / "),
            ],
            [
              "Suite duration",
              `${number(c.baselineWorkload.total_suite_minutes)} min total`,
              `${number(c.targetWorkload.total_suite_minutes)} min total`,
            ],
            [
              "Concurrency",
              c.baselineWorkload.concurrency,
              c.targetWorkload.concurrency,
            ],
            [
              "Output tokens per request",
              number(c.baselineWorkload.output_tokens),
              number(c.targetWorkload.output_tokens),
            ],
            [
              "Configuration",
              c.baseline.configuration_id,
              c.target.configuration_id,
            ],
            [
              "Acceptance criteria",
              c.baseline.acceptance_limits_ref,
              c.target.acceptance_limits_ref,
            ],
          ] as [string, string | number, string | number][]
        ).map(([k, a, b]) => (
          <tr key={k}>
            <td>{k}</td>
            <td>{a}</td>
            <td className={a !== b ? "changed-value" : ""}>{b}</td>
          </tr>
        ))}
      </Table>
    </Panel>
  );
}
function ChangeDetail({ c }: { c: Case }) {
  const { data } = useData();
  return (
    <div className="plm-object-page">
      <div className="plm-object-header" id="plm-overview">
        <Heading
          eyebrow={"Stratos PLM / Changes / " + c.change.id}
          title={c.change.title}
          action={
            c.options.some((o) => o.resource_eligible) ? (
              <Link
                className="button primary"
                to={"/engineering/changes/" + c.change.id + "/draft"}
              >
                <Plus size={17} />
                Draft assessment
              </Link>
            ) : (
              <Link className="button" to="/validation/options">
                Review resources and scheduled work
              </Link>
            )
          }
        >
          <CaseState c={c} /> <Fresh record={c.change} />
        </Heading>
        <Facts
          items={[
            ["Change", <span className="record-link">{c.change.id}</span>],
            [
              "Program",
              <Link to={"/programs/" + c.change.program_id}>
                {c.change.program_id}
              </Link>,
            ],
            ["Owner", c.change.owner || "Unassigned"],
            ["Product revision", c.config.product_revision],
            ["Configuration", <a href="#plm-configuration">{c.config.id}</a>],
            ["Record version", c.change.record_version],
          ]}
        />
      </div>
      <EngineeringSections />
      <div
        className="plm-applicability"
        aria-label="Engineering record relationships"
      >
        <div className="plm-applicability-label">
          <Layers3 size={17} aria-hidden="true" />
          <span>Applicability</span>
        </div>
        <a href="#plm-requirements">
          <small>Requested requirement</small>
          <strong>{c.target.id}</strong>
        </a>
        <ChevronRight size={15} aria-hidden="true" />
        <a href="#plm-configuration">
          <small>Applies to configuration</small>
          <strong>{c.config.id}</strong>
        </a>
        <ChevronRight size={15} aria-hidden="true" />
        <div>
          <small>Controlled change</small>
          <strong>{c.change.id}</strong>
        </div>
        <ChevronRight size={15} aria-hidden="true" />
        <a href="#plm-evidence">
          <small>Validation evidence</small>
          <strong>
            {c.coverage.coverage_satisfied
              ? "Coverage satisfied"
              : "Evidence missing"}
          </strong>
        </a>
      </div>
      <CurrentValidationEvidence c={c} />
      <ScheduledWork c={c} />
      <Comparison c={c} />
      <div className="split plm-configuration-grid">
        <Panel title="Product configuration" id="plm-configuration">
          <Facts
            items={[
              [
                "Product",
                c.config.product_id + " · " + c.config.product_revision,
              ],
              [
                "Configuration",
                c.config.id + " · content v" + c.config.content_version,
              ],
              ["Model bundle", c.config.model_bundle_id],
              [
                "Firmware / runtime",
                c.config.firmware + " / " + c.config.runtime,
              ],
              [
                "Quantization / memory",
                c.config.quantization + " / " + c.config.memory_configuration,
              ],
              ["Device count", c.config.device_count],
              ["Acceptance criteria", c.criteria.scope],
            ]}
          />
        </Panel>
        <Panel
          title="Evidence obligation"
          id="plm-evidence"
          aside={
            <Badge
              value={
                c.coverage.coverage_satisfied
                  ? "coverage satisfied"
                  : "evidence missing"
              }
            />
          }
        >
          <p className="padded">
            Review deadline <strong>{date(c.milestone.baseline_at)}</strong>.
            Existing evidence must match the exact requested configuration and
            workload.
          </p>
          <div className="compact-list">
            {c.coverage.items.map((item) => (
              <Link
                key={item.result.id}
                to={"/validation/results/" + item.result.id}
              >
                <strong>{item.result.id}</strong>
                <Reasons values={item.mismatch_reasons} />
              </Link>
            ))}
          </div>
        </Panel>
      </div>
      <Panel
        title="Immutable plans"
        id="plm-plans"
        aside={
          <span className="metadata">{c.change.plans.length} persisted</span>
        }
      >
        {c.change.plans.length ? (
          <Table
            headers={[
              "Plan",
              "Sample / slot",
              "Incremental cost",
              "Decision",
              "Scheduling record",
            ]}
          >
            {c.change.plans.map((p) => (
              <tr key={p.id}>
                <td>
                  <Link
                    className="record-link"
                    to={"/engineering/plans/" + p.id}
                  >
                    {p.id}
                  </Link>
                  <small>Version {p.plan_version}</small>
                </td>
                <td>
                  {p.sample_id}
                  <span className="cell-secondary">{p.slot_id}</span>
                </td>
                <td>{money(p.cost_cents)}</td>
                <td>
                  <Badge value={p.state} />
                </td>
                <td>
                  <Badge value={p.execution_state} />
                </td>
              </tr>
            ))}
          </Table>
        ) : (
          <Empty>
            No assessments have been persisted. A program operator can draft a
            plan for engineering review.
          </Empty>
        )}
      </Panel>
      <div className="split plm-reference-grid">
        <Panel title="Related documents" id="plm-documents">
          <div className="link-list">
            {data!.documents
              .filter((d) => d.program_id === c.change.program_id)
              .map((d) => (
                <Link key={d.id} to={"/engineering/documents/" + d.id}>
                  <FileText size={17} />
                  <span>
                    {human(d.document_type)}
                    <small>
                      {d.id} · v{d.document_version}
                    </small>
                  </span>
                  <Badge value={d.status} />
                </Link>
              ))}
          </div>
        </Panel>
        <Panel title="Activity history" id="plm-history">
          <Audit events={c.audit} />
        </Panel>
      </div>
    </div>
  );
}
export function OptionSummary({ option }: { option: Schema["Option"] }) {
  return (
    <>
      <Facts
        items={[
          ["Lab / campus", option.lab.id + " / " + option.lab.campus],
          [
            "Sample / configuration",
            option.sample.id + " / " + option.sample.configuration_id,
          ],
          ["Target configuration", option.configuration_id],
          ["Incremental cost", money(option.cost_cents)],
          [
            "Approval eligibility",
            <Badge
              value={
                option.approval_eligible
                  ? "within delegated policy"
                  : "approval unavailable"
              }
            />,
          ],
          [
            "Deadline",
            option.timing ? (
              <Badge
                value={`${Math.abs(option.timing.deadline_slack_minutes) / 60} hours ${option.timing.deadline_slack_minutes >= 0 ? "before" : "after"} baseline`}
                tone={option.meets_deadline ? "good" : "warning"}
              />
            ) : (
              "No eligible forecast"
            ),
          ],
        ]}
      />
      {option.timing && <Timing timing={option.timing} />}
      <div className="padded">
        <Reasons
          values={[...option.eligibility_reasons, ...option.approval_reasons]}
        />
      </div>
    </>
  );
}
function PlanDetail({ c, plan }: { c: Case; plan: Schema["PlanView"] }) {
  const { persona, fetchedAt, error: sourceError, loading } = useData();
  const [decision, setDecision] = useState<Schema["Decision"] | null>(null);
  const [decisionError, setDecisionError] = useState("");
  const [form, setForm] = useFormState("decision:" + plan.id, {
    choice: "approve",
    reason: "",
    reviewed: false,
  });
  const mutation = useMutation("decision:" + plan.id);
  const previous = c.change.plans.find((p) => p.id === plan.supersedes_plan_id);
  const revisions = c.change.plans.filter(
    (p) => p.supersedes_plan_id === plan.id,
  );
  const policy = c.policies.find((p) => p.id === plan.policy_id),
    option = c.options.find(
      (o) => o.slot.id === plan.slot_id && o.sample.id === plan.sample_id,
    );
  useEffect(() => {
    let active = true;
    setDecision(null);
    setDecisionError("");
    if (plan.decision_id)
      api(persona)
        .get<Schema["Decision"]>(
          "/engineering/decisions/" + enc(plan.decision_id),
        )
        .then((d) => {
          if (active) setDecision(d);
        })
        .catch((e) => {
          if (active) setDecisionError(errorMessage(e));
        });
    return () => {
      active = false;
    };
  }, [plan.decision_id, persona, fetchedAt]);
  const approvalBlocked =
    form.choice === "approve" && !option?.approval_eligible;
  return (
    <div className="plm-object-page plm-plan-page">
      <div className="plm-object-header">
        <Heading
          eyebrow={"Stratos PLM / " + c.change.id + " / Immutable plan"}
          title="Validation plan review"
          action={
            <Link className="button" to={"/engineering/changes/" + c.change.id}>
              Change workspace
            </Link>
          }
        >
          <span className="record-link">{plan.id}</span> · Version{" "}
          {plan.plan_version} · <Badge value={plan.state} />
        </Heading>
        <Facts
          items={[
            [
              "Change",
              <Link to={"/engineering/changes/" + c.change.id}>
                {c.change.id}
              </Link>,
            ],
            ["Configuration", plan.configuration_id],
            ["Plan version", plan.plan_version],
            ["Creator", plan.created_by],
            ["Incremental cost", money(plan.cost_cents)],
          ]}
        />
      </div>
      <EngineeringSections plan />
      <Banner>
        Approval covers the exact supplemental validation work below. It does
        not approve the requested requirement baseline or product acceptance.
      </Banner>
      <Panel title="Plan revision lineage">
        <div className="padded">
          {plan.supersedes_plan_id ? (
            <p>
              Revises{" "}
              <Link
                className="record-link"
                to={"/engineering/plans/" + plan.supersedes_plan_id}
              >
                {plan.supersedes_plan_id}
              </Link>
              . Approval does not transfer between plans.
            </p>
          ) : (
            <p>Original plan in this revision lineage.</p>
          )}
          {revisions.map((r) => (
            <p key={r.id}>
              Revised by{" "}
              <Link className="record-link" to={"/engineering/plans/" + r.id}>
                {r.id}
              </Link>{" "}
              · <Badge value={r.state} />
            </p>
          ))}
          <Link
            className="button"
            to={
              "/engineering/changes/" +
              c.change.id +
              "/draft?supersedes=" +
              plan.id
            }
          >
            Create revised plan
          </Link>
          <p className="metadata">
            A program operator can create a new immutable plan. Previous
            decisions and bookings remain intact.
          </p>
        </div>
      </Panel>
      {previous && <ScopeChanges previous={previous} current={plan} />}
      <div className="split wide-left">
        <div>
          <Panel
            title="Exact plan scope"
            id="plm-scope"
            aside={<strong>{money(plan.cost_cents)}</strong>}
          >
            <Facts
              items={[
                [
                  "Requirement / configuration",
                  plan.target_requirement_revision_id +
                    " / " +
                    plan.configuration_id,
                ],
                ["Procedure", plan.procedure_id],
                ["Sample / slot", plan.sample_id + " / " + plan.slot_id],
                ["Milestone", plan.milestone_id],
                [
                  "Authorized actions",
                  plan.permitted_actions.map(human).join("; "),
                ],
                ["Creator", plan.created_by],
                ["Scheduling record", <Badge value={plan.execution_state} />],
                ["Review duration", `${plan.review_minutes} min`],
                [
                  "Deadline margin",
                  `${Math.abs(plan.timing.deadline_slack_minutes) / 60} hours ${plan.timing.deadline_slack_minutes >= 0 ? "before" : "after"} baseline`,
                ],
              ]}
            />
            <Timing timing={plan.timing} />
          </Panel>
          <Panel title="Authored assessment" id="plm-assessment">
            <div className="padded prose">
              <h3>Facts</h3>
              {plan.assessment.facts.map((f, i) => (
                <div key={i}>
                  <p>{f.text}</p>
                  <div className="assessment-sources">
                    {f.source_refs.map((s) => (
                      <SourceReference
                        key={s.resource_type + s.resource_id}
                        source={s}
                        snapshot={plan.source_snapshot.find(
                          (r) =>
                            r.resource_type === s.resource_type &&
                            r.resource_id === s.resource_id,
                        )}
                      />
                    ))}
                  </div>
                </div>
              ))}
              <h3>Evidence gaps</h3>
              {plan.assessment.evidence_gaps.length ? (
                plan.assessment.evidence_gaps.map((g) => <p key={g}>{g}</p>)
              ) : (
                <p>No gap statement entered.</p>
              )}
              <h3>Unresolved questions</h3>
              {plan.assessment.unresolved_questions.length ? (
                plan.assessment.unresolved_questions.map((q) => (
                  <p key={q}>{q}</p>
                ))
              ) : (
                <p>No question entered.</p>
              )}
            </div>
          </Panel>
          <Panel title="Evidence at drafting">
            <div className="compact-list">
              {plan.coverage.items.map((i) => (
                <Link
                  key={i.result.id}
                  to={"/validation/results/" + i.result.id}
                >
                  <strong>{i.result.id}</strong>
                  <Reasons values={i.mismatch_reasons} />
                </Link>
              ))}
            </div>
          </Panel>
        </div>
        <div id="plm-decision">
          <Panel
            title="Engineering decision"
            className="engineering-decision"
            id={plan.decision_id ? "decision-" + plan.decision_id : undefined}
            aside={<Badge value={plan.state} />}
          >
            {mutation.feedback}
            {decisionError && <Banner tone="danger">{decisionError}</Banner>}
            {decision ? (
              <>
                <Facts
                  items={[
                    ["Decision", human(decision.decision)],
                    ["Simulated signer", decision.signer_identity],
                    ["Recorded", date(decision.updated_at)],
                    [
                      "Policy",
                      decision.policy_id +
                        " · v" +
                        decision.policy_content_version,
                    ],
                    ["Reason", decision.reason],
                  ]}
                />
                <p className="padded metadata record-link">{decision.id}</p>
              </>
            ) : plan.state !== "draft" ? (
              <Empty>Retrieving the recorded decision…</Empty>
            ) : (
              <form
                className="form"
                onSubmit={(e) => {
                  e.preventDefault();
                  const body: Schema["DecisionInput"] = {
                    decision: form.choice as "approve" | "reject",
                    expected_plan_version: plan.plan_version,
                    expected_plan_digest: plan.plan_digest,
                    reason: form.reason,
                  };
                  void mutation.submit(
                    `/engineering/plans/${enc(plan.id)}/decisions`,
                    body,
                  );
                }}
              >
                <p>
                  Delegated limit:{" "}
                  {policy
                    ? money(policy.max_incremental_cost_cents)
                    : "Unavailable"}
                  .
                </p>
                {persona !== "engineer" && (
                  <p className="permission-note">
                    Select Engineering approver to record a decision. The
                    program operator cannot self-approve.
                  </p>
                )}
                <fieldset
                  disabled={
                    persona !== "engineer" ||
                    !!sourceError ||
                    loading ||
                    mutation.busy ||
                    mutation.pending
                  }
                >
                  <label>
                    Decision
                    <select
                      value={form.choice}
                      onChange={(e) =>
                        setForm({ ...form, choice: e.target.value })
                      }
                    >
                      <option value="approve">Approve exact plan</option>
                      <option value="reject">Reject plan</option>
                    </select>
                  </label>
                  {approvalBlocked && (
                    <Banner tone="warning">
                      Approval is unavailable for the current resources or
                      policy.
                      <Reasons
                        values={[
                          ...(option?.eligibility_reasons || []),
                          ...(option?.approval_reasons || []),
                        ]}
                      />
                    </Banner>
                  )}
                  <label>
                    Decision reason
                    <textarea
                      required
                      maxLength={2000}
                      value={form.reason}
                      onChange={(e) =>
                        setForm({ ...form, reason: e.target.value })
                      }
                    />
                  </label>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={form.reviewed}
                      onChange={(e) =>
                        setForm({ ...form, reviewed: e.target.checked })
                      }
                    />
                    I reviewed this immutable plan’s scope, timing, cost and
                    evidence.
                  </label>
                  <button
                    type="submit"
                    className="primary"
                    disabled={
                      !form.reviewed || !form.reason.trim() || approvalBlocked
                    }
                  >
                    Record{" "}
                    {form.choice === "approve" ? "approval" : "rejection"}
                  </button>
                </fieldset>
              </form>
            )}
          </Panel>
          <Panel title="Next operational step">
            <div className="padded">
              {plan.job_id ? (
                <>
                  <p>
                    <Badge value={plan.execution_state} />
                  </p>
                  <Link
                    className="button"
                    to={"/validation/jobs/" + plan.job_id}
                  >
                    Open scheduled job
                  </Link>
                  {!plan.implementation_link_id && (
                    <Link
                      className="button"
                      to={"/programs/" + plan.program_id}
                    >
                      Complete planner link
                    </Link>
                  )}
                </>
              ) : (
                <>
                  <p>
                    {plan.state === "approved"
                      ? "An operator can schedule this exact plan."
                      : "An approved decision is required before scheduling."}
                  </p>
                  <Link className="button" to="/validation/jobs">
                    Open jobs queue
                  </Link>
                </>
              )}
            </div>
          </Panel>
        </div>
      </div>
      <Panel title="Bound source versions" id="plm-sources">
        <details className="padded">
          <summary>
            {plan.source_snapshot.length} immutable source records · inspect
            versions
          </summary>
          <p className="metadata break-all">Plan digest: {plan.plan_digest}</p>
          <Table
            headers={[
              "Source",
              "Type",
              "Content version",
              "Availability version",
            ]}
          >
            {plan.source_snapshot.map((s) => (
              <tr key={s.resource_type + s.resource_id}>
                <td>
                  <SourceReference source={s} snapshot={s} />
                </td>
                <td>{human(s.resource_type)}</td>
                <td>{s.content_version}</td>
                <td>{s.availability_version ?? "—"}</td>
              </tr>
            ))}
          </Table>
        </details>
      </Panel>
      <Panel title="Plan activity" id="plm-history">
        <Audit events={c.audit.filter((e) => e.plan_id === plan.id)} />
      </Panel>
    </div>
  );
}
