import { Link } from "react-router-dom";
import type { Case } from "./data";
import { useData } from "./data";
import { Badge, Banner, date, Facts, number, Panel } from "./ui";

export const currentPlan = (c: Case) =>
  c.change.plans.find((p) => p.id === c.change.current_plan_id);

export function caseStatus(c: Case) {
  if (c.physical?.result) return c.physical.technical_state;
  const p = currentPlan(c);
  if (p?.job_id) return p.execution_state;
  return p?.state === "approved"
    ? "approved_awaiting_scheduling"
    : p?.state === "rejected"
      ? "plan_rejected"
      : p
        ? "plan_drafted"
        : c.change.workflow_state;
}

export function caseNextAction(c: Case) {
  const p = currentPlan(c);
  if (c.jobs.some((j) => !c.links.some((l) => l.job_id === j.id)))
    return "Operator: link the existing job in Planner";
  if (c.physical?.result) return c.physical.engineering_status === "approved"
    ? "Await separate customer acceptance"
    : c.physical.applicability === "gap_remains"
      ? "Review current validation evidence mismatches"
      : "Reassess recorded evidence and obtain Engineering review";
  if (p?.job_id) return "Await lab execution and engineering review";
  if (p?.state === "approved") return "Operator: schedule the approved plan";
  if (p?.state === "draft") return "Engineer: review the exact immutable plan";
  if (p?.state === "rejected")
    return "Operator: reassess scope and create a revised plan";
  return c.change.next_action || "Assess the customer request";
}

export function CaseState({ c }: { c: Case }) {
  const p = currentPlan(c);
  return (
    <span className="case-state">
      <span>
        Current plan decision:{" "}
        <Badge value={p?.state || c.change.workflow_state} />
      </span>
      <span>
        Scheduling record: <Badge value={p?.execution_state || "not_scheduled"} />
      </span>
      {c.physical?.result && <span>Validation: <Badge value={c.physical.technical_state} /></span>}
    </span>
  );
}

export function CurrentValidationEvidence({ c }: { c: Case }) {
  const p=c.physical;
  if (!p?.result) return null;
  return <Panel title="Current validation evidence">
    <Facts items={[
      ["Technical state", <Badge value={p.technical_state} />],
      ["Physical job", <Badge value={p.job_status} />],
      ["Result", <Link to={"/validation/results/"+p.result.id}>{p.result.id}</Link>],
      ["Evidence applicability", <Badge value={p.applicability} />],
      ["Engineering evidence review", <Badge value={p.engineering_status} />],
      ["Source decision", p.current_review?.id || "Not recorded"],
      ["Customer acceptance", <Badge value={p.customer_acceptance} />],
    ]} />
    <p className="padded">The scheduling record is retained separately from the lab result and exact Engineering evidence decision. Customer acceptance remains separate.</p>
    <p className="padded"><Link to={"/control/programs/"+c.change.program_id+"/cases/"+c.change.id}>Open evidence reassessment and review</Link></p>
  </Panel>;
}

export function ScheduledWork({ c }: { c: Case }) {
  if (!c.jobs.length) return null;
  return (
    <Banner>
      <strong>{c.physical?.result ? "Scheduled record · Result received" : "Work already scheduled"}</strong>
      <p>
        {c.physical?.result
          ? "The original reservation is retained. The separate lab result and Engineering evidence decision determine current validation progress."
          : "Each sample is reserved for one outstanding job. Its reservation can make other slot combinations unavailable. Scheduling does not create test results."}
      </p>
      <ul className="scheduled-work">
        {c.jobs.map((job) => {
          const linked = c.links.find((l) => l.job_id === job.id);
          return (
            <li key={job.id}>
              <Link to={"/validation/jobs/" + job.id}>
                Open scheduled job {job.id}
              </Link>
              <span>
                {job.sample_id} · {job.slot_id} ·{" "}
                {date(job.timing.lab_start_at)}
              </span>
              <Link
                to={
                  "/programs/" +
                  job.program_id +
                  (linked ? "#link-" + linked.id : "")
                }
              >
                {linked ? "View Planner link" : "Complete missing Planner link"}
              </Link>
              {job.plan_id !== c.change.current_plan_id && (
                <span>
                  Booked under an earlier plan; its reservation is preserved.
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </Banner>
  );
}

export function CaseOverview({ c }: { c: Case }) {
  const { data } = useData();
  const p = currentPlan(c);
  const program = data!.programs.find((r) => r.id === c.change.program_id);
  const changePath = "/engineering/changes/" + c.change.id;
  const planPath = p ? "/engineering/plans/" + p.id : changePath + "/draft";
  const missing = c.jobs.find((j) => !c.links.some((l) => l.job_id === j.id));
  const eligible = c.options.some((o) => o.resource_eligible);
  const next = missing
    ? {
        title: "Update Planner for the scheduled job",
        owner: "Program operator",
        path: "/programs/" + c.change.program_id,
      }
    : c.physical?.result
      ? { title: caseNextAction(c), owner: c.physical.engineering_status === "approved" ? "Customer program owner" : "Engineering approver",
          path: "/control/programs/"+c.change.program_id+"/cases/"+c.change.id }
    : p?.job_id
      ? {
          title: "Await test execution and engineering review",
          owner: "Validation lab and Engineering",
          path: "/validation/jobs/" + p.job_id,
        }
      : p?.state === "approved"
        ? eligible
          ? {
              title: "Schedule the approved plan",
              owner: "Program operator",
              path: "/validation/jobs?change=" + c.change.id,
            }
          : {
              title: "Review resource restrictions before scheduling",
              owner: "Program operator",
              path: "/validation/options?change=" + c.change.id,
            }
        : p?.state === "draft"
          ? {
              title: "Review the exact draft plan",
              owner: "Engineering approver",
              path: planPath,
            }
          : eligible
            ? {
                title: p
                  ? "Revise the rejected plan"
                  : "Assess the customer change",
                owner: "Program operator",
                path: p
                  ? changePath + "/draft?supersedes=" + p.id
                  : changePath + "/draft",
              }
            : {
                title: "Review resource restrictions",
                owner: "Program operator",
                path: "/validation/options?change=" + c.change.id,
              };
  const stages = [
    {
      label: "Assess",
      path: p ? planPath : changePath,
      state: p ? "Draft recorded" : "Assessment needed",
    },
    {
      label: "Approve",
      path: planPath,
      state:
        p?.state === "approved"
          ? "Approved"
          : p?.state === "rejected"
            ? "Rejected — revision needed"
            : p
              ? "Decision needed"
              : "Awaiting assessment",
    },
    {
      label: "Schedule",
      path: p?.job_id ? "/validation/jobs/" + p.job_id : "/validation/jobs",
      state: p?.job_id ? "Job scheduled" : "Awaiting approved booking",
    },
    {
      label: "Update Planner",
      path: "/programs/" + c.change.program_id,
      state: p?.implementation_link_id
        ? c.physical?.result ? "Linked · See current validation state" : "Linked · execution pending"
        : "Link needed after scheduling",
    },
  ];
  return (
    <Panel
      title={c.change.id + " · " + c.change.title}
      className="case-overview"
    >
      <div className="padded">
        <p>
          <strong>{program?.customer_name}</strong> requests{" "}
          {number(c.targetWorkload.total_suite_minutes)} minutes of evidence for
          context bins {c.targetWorkload.context_bins.map(number).join(" / ")}{" "}
          on {c.config.id}. The approved baseline remains {c.baseline.id}.
        </p>
        <div className="button-row">
          <Link to={changePath}>Inspect customer change</Link>
          <Link to={"/engineering/documents/" + c.change.request_document_id}>
            Read customer request
          </Link>
        </div>
        <Facts
          items={[
            ["Evidence / review deadline", date(c.milestone.baseline_at)],
            ["Current progress", <CaseState c={c} />],
            ["Next responsible role", next.owner],
          ]}
        />
        <ol className="case-stages" aria-label="Case stages">
          {stages.map((stage, i) => (
            <li key={stage.label}>
              <Link to={stage.path}>
                <span>{i + 1}</span>
                {stage.label}
              </Link>
              <small>{stage.state}</small>
            </li>
          ))}
        </ol>
        <div className="next-action">
          <div>
            <small>Next outstanding action</small>
            <strong>{next.title}</strong>
          </div>
          <Link className="button primary" to={next.path}>
            {p?.job_id && !missing
              ? "Inspect scheduled work"
              : "Open next step"}
          </Link>
        </div>
        {p?.job_id && !missing && (
          <p className="muted">
            {c.physical?.result ? "Coordination is recorded. Current validation and Engineering review are shown separately; customer acceptance remains pending."
              : "All four coordination stages are recorded. Execution and evidence review are still pending."}
          </p>
        )}
      </div>
      <CurrentValidationEvidence c={c} />
      {!!c.jobs.length && <ScheduledWork c={c} />}
    </Panel>
  );
}
