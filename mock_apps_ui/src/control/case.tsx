import { CaseRunLink } from "./operations-data";
import { evidenceReason } from "./trace-language";
import { DeliveryCase } from "./delivery-case";
import { QualityCase } from "./quality-case";
import { StandardCase } from "./standard-case";
import { useHost } from "./host";
import { ConnectedCase } from "./connected-case";
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { Link } from "./access";
import { ArrowRight, FileText } from "lucide-react";
import type { Schema } from "../api";
import {
  currentPlan,
  date,
  money,
  nextStep,
  programPath,
  read,
  reason,
  stories,
  useControl,
  words,
  type CaseData,
} from "./data";
import {
  StatusText,
  Crumbs,
  Drawer,
  Empty,
  Facts,
  Heading,
  Notice,
  Section,
  SourceLink,
  SourceState,
  Steps,
  Truth,
} from "./ui";
import { Activity } from "./portfolio";

import { caseStages } from "./overview-model";
export function Evidence({
  c,
  modalOnly = false,
  assessment = "complete",
}: {
  c: CaseData;
  modalOnly?: boolean;
  assessment?: "unassessed" | "running" | "complete";
}) {
  const downstream = useHost()?.data?.downstream;
  const [params, setParams] = useSearchParams();
  const { freshness } = useControl();
  const id = params.get("evidence");
  const item = c.coverage.items.find((i) => i.result.id === id);
  const close = () => {
    const next = new URLSearchParams(params);
    next.delete("evidence");
    setParams(next);
  };
  const open = (id: string) => {
    const next = new URLSearchParams(params);
    next.set("evidence", id);
    return `?${next}`;
  };
  return (
    <>
      {!modalOnly && (
        <>
          <Section
            title="Does the evidence cover this request?"
            note="Does each observation apply to this requested configuration and workload?"
          >
            <div className="cp-table-wrap">
              <table>
                <caption>
                  {assessment === "complete"
                    ? `The completed investigation compared each result with ${c.target.id}. A passing test may cover a different configuration, workload, or duration.`
                    : assessment === "running"
                      ? `Agents are comparing these source observations with ${c.target.id}. Applicability conclusions will appear when the investigation finishes.`
                      : `These source observations are available for review. Run the investigation to determine whether they apply to ${c.target.id}.`}
                </caption>
                <thead>
                  <tr>
                    <th>Source observation</th>
                    <th>Captured scope</th>
                    <th>Test duration</th>
                    <th>Applies to request</th>
                    <th>Inspect</th>
                  </tr>
                </thead>
                <tbody>
                  {c.coverage.items.map((i) => (
                    <tr key={i.result.id}>
                      <td>
                        <strong>{i.result.id}</strong>
                        <small>
                          v{i.result.content_version} ·{" "}
                          {date(i.result.completed_at)}
                        </small>
                      </td>
                      <td>
                        {i.result.configuration_id}
                        <small>{i.result.workload_profile_id}</small>
                      </td>
                      <td>{i.result.actual_suite_minutes} min</td>
                      <td>
                        <StatusText
                          tone={
                            assessment === "complete"
                              ? i.satisfies
                                ? "good"
                                : "warning"
                              : "neutral"
                          }
                        >
                          {assessment === "complete"
                            ? i.satisfies
                              ? "Sufficient"
                              : "Insufficient"
                            : assessment === "running"
                              ? "Assessing"
                              : "Not assessed"}
                        </StatusText>
                        <small>
                          {assessment === "complete"
                            ? i.mismatch_reasons
                                .map(evidenceReason)
                                .join(" · ") ||
                              "Covers the requested test scope"
                            : assessment === "running"
                              ? "Applicability check in progress"
                              : "Applicability has not been evaluated"}
                        </small>
                      </td>
                      <td>
                        <Link
                          className="cp-text-link"
                          to={open(i.result.id)}
                          aria-label={`Inspect evidence ${i.result.id}`}
                        >
                          <FileText size={16} />
                          Evidence
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!c.coverage.items.length && (
              <Empty>
                No evidence observations are available for this scope.
              </Empty>
            )}
          </Section>
        </>
      )}
      {id && modalOnly && (
        <Drawer title={item?.result.id || "Evidence not found"} close={close}>
          {item ? (
            <>
              <div className="cp-evidence-preview">
                <div className="cp-source-preview">
                  <article className="cp-source-page">
                    <span className="cp-document-label">
                      Validation Lab · Source record
                    </span>
                    <h3>{item.result.id}</h3>
                    <p>
                      Recorded observation ·{" "}
                      {date(item.result.completed_at, true)}
                    </p>
                    <StatusText
                      tone={item.result.criteria_passed ? "good" : "warning"}
                    >
                      {words(item.result.status)} · criteria{" "}
                      {item.result.criteria_passed
                        ? "passed for recorded scope"
                        : "not passed"}
                    </StatusText>
                    <Facts
                      rows={[
                        [
                          "Configuration",
                          `${item.result.configuration_id} · v${item.result.configuration_content_version} · ${item.result.product_revision}`,
                        ],
                        [
                          "Workload",
                          `${item.result.workload_profile_id} · v${item.result.workload_profile_content_version}`,
                        ],
                        ["Model bundle", item.result.model_bundle_id],
                        [
                          "Acceptance criteria",
                          `${item.result.acceptance_limits_ref} · v${item.result.acceptance_criteria_content_version}`,
                        ],
                        [
                          "Observed suite",
                          `${item.result.actual_suite_minutes} minutes`,
                        ],
                      ]}
                    />
                    <h4>Observed exposure by context bin</h4>
                    <Facts
                      rows={Object.entries(
                        item.result.observed_minutes_by_context_bin,
                      ).map(([bin, minutes]) => [
                        Number(bin).toLocaleString() + " tokens",
                        `${minutes} min`,
                      ])}
                    />
                    <p className="cp-caption">
                      This is a structured source record, not a PDF. Historical
                      versions remain bound to this observation.
                    </p>
                  </article>
                </div>
                <div className="cp-evidence-finding">
                  <Truth recorded />
                  <h3>Applicability to {c.change.id}</h3>
                  {assessment === "complete" ? (
                    <>
                      <StatusText tone={item.satisfies ? "good" : "warning"}>
                        {item.satisfies
                          ? "Applicable evidence"
                          : "Applicability gap"}
                      </StatusText>
                      <p>
                        {item.satisfies
                          ? "This observation satisfies the requested evidence scope. Engineering disposition and acceptance remain separate."
                          : "This observation does not satisfy the complete requested evidence scope."}
                      </p>
                      <Facts
                        rows={[
                          ["Source", "Validation Lab"],
                          ...(downstream?.physical.result?.id === item.result.id
                            ? ([
                                [
                                  "Job / plan",
                                  `${downstream.physical.job?.id} / ${downstream.physical.job?.plan_id}`,
                                ],
                                [
                                  "Provenance",
                                  downstream.physical.completion
                                    ?.source_reference || "Not recorded",
                                ],
                                [
                                  "Generated by",
                                  "Explicit synthetic demo lab action",
                                ],
                                [
                                  "Recorded at",
                                  date(
                                    downstream.physical.completion?.recorded_at,
                                    true,
                                  ),
                                ],
                                [
                                  "Engineering review",
                                  downstream.physical.current_review
                                    ? words(
                                        downstream.physical.engineering_status,
                                      )
                                    : downstream.review_ready
                                      ? "Ready"
                                      : "Pending reassessment",
                                ],
                              ] as [string, React.ReactNode][])
                            : []),
                          ["Source ID", item.result.id],
                          ["Content version", item.result.content_version],
                          [
                            "Observation freshness",
                            `${freshness} of a recorded result`,
                          ],
                          ["Completed", date(item.result.completed_at, true)],
                          [
                            "Source updated",
                            date(item.result.updated_at, true),
                          ],
                          [
                            "Finding",
                            item.mismatch_reasons
                              .map(evidenceReason)
                              .join("; ") || "Complete scope matched",
                          ],
                          [
                            "Runtime",
                            `${item.result.actual_suite_minutes} minutes observed; ${c.targetWorkload.total_suite_minutes} minutes requested`,
                          ],
                        ]}
                      />
                    </>
                  ) : (
                    <>
                      <StatusText tone="neutral">
                        {assessment === "running"
                          ? "Assessment in progress"
                          : "Not assessed"}
                      </StatusText>
                      <p>
                        {assessment === "running"
                          ? "Agents are checking whether this source observation applies to the requested workload. The conclusion will appear after the investigation finishes."
                          : "Run the investigation to determine whether this source observation applies to the requested workload."}
                      </p>
                    </>
                  )}
                  <SourceLink to={`/validation/results/${item.result.id}`}>
                    Open source result
                  </SourceLink>
                  {assessment === "complete" && (
                    <details>
                      <summary>Technical evidence references</summary>
                      <p>
                        Recorded check codes:{" "}
                        {item.mismatch_reasons.join(", ") || "No mismatch"}
                      </p>
                      <p>Evidence fingerprint</p>
                      <code className="cp-digest">
                        {c.coverage.evidence_set_digest}
                      </code>
                    </details>
                  )}
                </div>
              </div>
            </>
          ) : (
            <Empty>
              This evidence ID is not in the current case. No other case's
              evidence is substituted.
            </Empty>
          )}
        </Drawer>
      )}
    </>
  );
}
export function Options({ c }: { c: CaseData }) {
  const [result, setResult] = useState<Schema["Options"] | null>(null),
    [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    setResult(null);
    setError(false);
    read<Schema["Options"]>(
      `/validation/options?change_id=${encodeURIComponent(c.change.id)}`,
    )
      .then((v) => {
        if (active) setResult(v);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [c.change.id]);
  return (
    <>
      <Section
        title="Source options"
        note="Calculated by Validation. This read does not select, recommend or approve an option."
      >
        {error ? (
          <Empty>
            Options unavailable. No cost or timing has been assumed.{" "}
            <SourceLink to={`/validation/options?change=${c.change.id}`}>
              Inspect in Validation
            </SourceLink>
          </Empty>
        ) : !result ? (
          <Empty>Reading current option calculations…</Empty>
        ) : (
          <div className="cp-table-wrap">
            <table>
              <caption>
                All returned slot/sample combinations, including ineligible
                resources. Costs are source USD cents.
              </caption>
              <thead>
                <tr>
                  <th>Lab / sample</th>
                  <th>Scope</th>
                  <th>Cost</th>
                  <th>Review ready</th>
                  <th>Constraint</th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((o) => (
                  <tr key={o.slot.id + o.sample.id}>
                    <td>
                      {o.lab.id}
                      <small>
                        {o.slot.id} / {o.sample.id}
                      </small>
                    </td>
                    <td>
                      {o.configuration_id}
                      <small>{o.procedure_id}</small>
                    </td>
                    <td>{money(o.cost_cents)}</td>
                    <td>{date(o.timing?.review_ready_at, true)}</td>
                    <td>
                      {!o.resource_eligible
                        ? o.eligibility_reasons.map(words).join("; ")
                        : !o.approval_eligible
                          ? o.approval_reasons.map(words).join("; ")
                          : o.meets_deadline
                            ? "Eligible · meets deadline"
                            : "Eligible · misses deadline"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
      <Section
        title="Recorded plans & decisions"
        note="Source plan state is separate from host recommendation and exact proposal review."
      >
        {c.change.plans.length ? (
          c.change.plans.map((p) => (
            <article className="cp-record" key={p.id}>
              <div className="cp-inline">
                <h3>{p.id}</h3>
                <StatusText>{words(p.state)}</StatusText>
              </div>
              <Facts
                rows={[
                  ["Immutable version", p.plan_version],
                  [
                    "Scope",
                    `${p.configuration_id} / ${p.procedure_id} / ${p.sample_id}`,
                  ],
                  ["Cost", money(p.cost_cents)],
                  ["Review ready", date(p.timing.review_ready_at, true)],
                  [
                    "Decision reference",
                    p.decision_id || "No decision recorded",
                  ],
                  ["Execution state", words(p.execution_state)],
                ]}
              />
              <SourceLink to={`/engineering/plans/${p.id}`}>
                Inspect exact source plan
              </SourceLink>
            </article>
          ))
        ) : (
          <Empty>No plan or decision is recorded for this source change.</Empty>
        )}
        <Notice>
          Source plans are separate from exact host proposals. Review connected
          CR-017 proposals in Decisions. Demo identities are role-test
          stand-ins.
        </Notice>
      </Section>
    </>
  );
}
export function CasePage() {
  const { programId, caseId } = useParams();
  const { data } = useControl();
  const [params, setParams] = useSearchParams();

  if (
    programId === "PRG-A17" &&
    ["CR-019", "preview-1A"].includes(caseId || "")
  )
    return (
      <>
        <StandardCase />
        <CaseRunLink caseId="CR-019" />
      </>
    );
  if (
    programId === "PRG-A17" &&
    ["QE-004", "QE-011", "preview-QE-004"].includes(caseId || "")
  )
    return (
      <>
        <QualityCase caseId={caseId === "QE-011" ? "QE-011" : "QE-004"} />
        <CaseRunLink caseId={caseId === "QE-011" ? "QE-011" : "QE-004"} />
      </>
    );
  if (
    programId === "PRG-A17" &&
    ["DR-009", "preview-DR-009"].includes(caseId || "")
  )
    return (
      <>
        <DeliveryCase />
        <CaseRunLink caseId="DR-009" />
      </>
    );
  if (!data) return <SourceState>{null}</SourceState>;
  const c = data.cases.find(
      (c) => c.change.id === caseId && c.change.program_id === programId,
    ),
    program = data.programs.find((p) => p.id === programId);
  if (!c || !program)
    return (
      <Empty>
        Case not found in this program.{" "}
        <Link to="/control/programs">Browse authorized programs</Link>
      </Empty>
    );
  if (c.change.id === "CR-017" && c.change.customer_id === "CUST-FML01")
    return (
      <>
        <ConnectedCase c={c} program={program} />
        <CaseRunLink caseId={caseId || ""} />
      </>
    );
  const tab = params.get("tab") || "summary",
    plan = currentPlan(c);
  const title =
    caseId === "CR-017" ? "Long-context evidence change" : c.change.title;
  const select = (value: string) => {
    const next = new URLSearchParams(params);
    next.set("tab", value);
    next.delete("evidence");
    setParams(next);
  };
  return (
    <>
      <Crumbs
        items={[
          { label: "Overview", to: "/control/overview" },
          { label: program.name || program.id, to: programPath(program.id) },
          { label: c.change.id },
        ]}
      />
      <Heading
        eyebrow={`${c.change.id} / Requirement change`}
        title={title}
        description="What evidence and engineering decision are needed for the requested scope?"
        action={
          <SourceLink to={`/engineering/changes/${c.change.id}`}>
            Open Engineering Hub
          </SourceLink>
        }
      />
      <div className="cp-program-context">
        <span>Owner · {c.change.owner || program.owner}</span>
        <span>
          {c.config.id} · {c.config.product_revision}
        </span>
        <StatusText tone="warning">
          {words(
            c.change.execution_state === "not_scheduled"
              ? c.change.workflow_state
              : c.change.execution_state,
          )}
        </StatusText>
      </div>
      <Steps steps={caseStages(c)} />
      <div className="cp-case-workpanel">
        <div className="cp-case-requirement">
          <span className="cp-document-label">Requested evidence</span>
          <h2>
            {c.coverage.coverage_satisfied
              ? "Review the applicable evidence"
              : "Close the workload evidence gap"}
          </h2>
          <p>{c.change.title}</p>
          <Facts
            rows={[
              [
                "Requested suite",
                `${c.targetWorkload.total_suite_minutes} minutes`,
              ],
              [
                "Context bins",
                c.targetWorkload.context_bins
                  .map((n) => n.toLocaleString())
                  .join(" / ") + " tokens",
              ],
              [
                "Configuration",
                `${c.config.id} · ${c.config.product_revision}`,
              ],
            ]}
          />
          <Link
            className="cp-button cp-primary"
            to={(() => {
              const query = new URLSearchParams(params);
              const first = c.coverage.items[0]?.result.id;
              if (first) query.set("evidence", first);
              else query.set("tab", "evidence");
              return `?${query}`;
            })()}
          >
            View evidence <FileText size={18} />
          </Link>
        </div>
        <div className="cp-case-finding">
          <span className="cp-document-label">Current finding</span>
          <h2>
            {c.change.execution_state !== "not_scheduled"
              ? "Work scheduled. Results remain separate."
              : c.coverage.coverage_satisfied
                ? "Evidence available for engineering disposition."
                : "Supplemental evidence is needed."}
          </h2>
          <p>{reason(c)}</p>
          <h3>Next step</h3>
          <p>{nextStep(c)}</p>
          <small>
            Engineering review and customer acceptance retain their own
            authority.
          </small>
        </div>
      </div>
      <nav className="cp-tabs" aria-label="Case sections">
        {[
          ["summary", "Summary"],
          ["evidence", "Evidence"],
          ["options", "Options & decisions"],
          ["activity", "Activity"],
        ].map(([id, label]) => (
          <button
            key={id}
            aria-current={tab === id ? "page" : undefined}
            onClick={() => select(id)}
          >
            {label}
          </button>
        ))}
      </nav>
      {tab === "summary" ? (
        <>
          <Section
            title="What changed?"
            note="Requested evidence expands; the approved requirement baseline stays intact."
          >
            <div className="cp-compare">
              {[
                {
                  label: "Approved baseline",
                  req: c.baseline,
                  workload: c.baselineWorkload,
                },
                {
                  label: "Requested revision",
                  req: c.target,
                  workload: c.targetWorkload,
                },
              ].map((x) => (
                <article key={x.label}>
                  <div className="cp-eyebrow">{x.label}</div>
                  <h3>{x.req.id}</h3>
                  <p>{x.req.summary || `${x.workload.id} workload evidence`}</p>
                  <Facts
                    rows={[
                      [
                        "Context bins",
                        x.workload.context_bins
                          .map((v) => v.toLocaleString())
                          .join(" / ") + " tokens",
                      ],
                      [
                        "Suite duration",
                        `${x.workload.total_suite_minutes} minutes`,
                      ],
                      ["Configuration", x.req.configuration_id],
                      ["Status", words(x.req.status)],
                    ]}
                  />
                </article>
              ))}
            </div>
          </Section>
          <Section
            title="From requirement to action"
            note="Follow the dependency. Each stage retains its own authority."
          >
            <div className="cp-dependencies">
              {[
                {
                  label: c.target.id,
                  sub: "Requested requirement",
                  to: `/engineering/changes/${c.change.id}`,
                },
                {
                  label: c.coverage.coverage_satisfied
                    ? "Applicable evidence"
                    : "Evidence gap",
                  sub: "Validation applicability",
                  to: "?tab=evidence",
                },
                {
                  label: plan ? `Plan ${plan.state}` : "Review pending",
                  sub: "Engineering decision",
                  to: "?tab=options",
                },
                {
                  label: c.jobs.length ? "Scheduled work" : "Not scheduled",
                  sub: "Validation + Planner",
                  to: `/validation/jobs?change=${c.change.id}`,
                },
              ].map((x) => (
                <Link key={x.sub} to={x.to}>
                  <small>{x.sub}</small>
                  <strong>{x.label}</strong>
                  <ArrowRight size={16} />
                </Link>
              ))}
            </div>
          </Section>
          <Evidence c={c} />
        </>
      ) : tab === "evidence" ? (
        <Evidence c={c} />
      ) : tab === "options" ? (
        <Options c={c} />
      ) : tab === "activity" ? (
        <Section
          title="Case activity"
          note="Recorded business events only. Host run completion and verified execution are not inferred."
        >
          <Activity cases={[c]} limit={20} />
          <div className="cp-inline">
            <SourceLink to={`/validation/jobs?change=${c.change.id}`}>
              Source jobs
            </SourceLink>
            <SourceLink to={`/programs/${program.id}`}>
              Planner readback
            </SourceLink>
          </div>
        </Section>
      ) : (
        <Empty>
          Unknown case section.{" "}
          <button onClick={() => select("summary")}>Return to summary</button>
        </Empty>
      )}
      <Evidence c={c} modalOnly />
      <Notice>
        Scheduling is not testing, passing, acceptance or case closure. Governed
        host investigation, review and execution are limited to CR-017 in this
        slice.
      </Notice>
    </>
  );
}
