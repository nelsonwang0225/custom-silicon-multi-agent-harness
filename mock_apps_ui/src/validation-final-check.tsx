import { useState } from "react";
import { ArrowRight, CheckCircle2, Move, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { type Case } from "./data";
import { type Schema } from "./api";
import { number } from "./ui";
import {
  ValidationChipCanvas,
  type ChipRegion,
  type ChipScopeMode,
} from "./validation-chip-canvas";
import "./validation-final-check.css";

type Props = {
  job: Schema["JobView"];
  caseData: Case | undefined;
  unavailable: boolean;
};
const regions: { id: ChipRegion; label: string; number: string }[] = [
  { id: "context", label: "Context & memory", number: "01" },
  { id: "compute", label: "Compute", number: "02" },
  { id: "io", label: "I/O & scheduling", number: "03" },
];
const modes: { id: ChipScopeMode; label: string }[] = [
  { id: "before", label: "Original" },
  { id: "after", label: "Updated" },
  { id: "changes", label: "Changes" },
];

export function ValidationFinalCheck({ job, caseData: c, unavailable }: Props) {
  const [region, setRegion] = useState<ChipRegion>("context");
  const [mode, setMode] = useState<ChipScopeMode>("changes");
  const plan = c?.change.plans.find((p) => p.id === job.plan_id);
  const procedure = c?.procedures.find((p) => p.id === job.procedure_id);
  const matches = (
    type: Schema["Snapshot"]["resource_type"],
    record: { id: string; content_version: number },
  ) =>
    plan?.source_snapshot.some(
      (s) =>
        s.resource_type === type &&
        s.resource_id === record.id &&
        s.content_version === record.content_version,
    );
  // Presentation follows the exact job and current source versions. The server
  // still owns authorization, freshness checks, publication and result readback.
  const currentScope =
    c &&
    plan &&
    procedure &&
    c.change.id === job.change_id &&
    plan.state === "approved" &&
    c.change.current_plan_id === plan.id &&
    plan.plan_digest === job.plan_digest &&
    plan.target_requirement_revision_id === c.target.id &&
    job.configuration_id === c.config.id &&
    job.workload_profile_id === c.targetWorkload.id &&
    c.target.workload_profile_id === c.targetWorkload.id &&
    c.baseline.workload_profile_id === c.baselineWorkload.id &&
    matches("engineering.configuration", c.config) &&
    matches("engineering.requirement", c.baseline) &&
    matches("engineering.requirement", c.target) &&
    matches("engineering.workload", c.baselineWorkload) &&
    matches("engineering.workload", c.targetWorkload) &&
    matches("engineering.procedure", procedure) &&
    matches("engineering.criteria", c.criteria);

  if (unavailable || !currentScope || !c || !procedure)
    return (
      <div className="vfc-unavailable" role="status">
        The final-check summary needs current records for this approved job.
        Refresh the sources to review its exact scope.
      </div>
    );

  const before = c.baselineWorkload,
    after = c.targetWorkload;
  const bins = (values: number[]) => values.map(number).join(" / ");
  const sameConfiguration =
    c.baseline.configuration_id === c.target.configuration_id;
  const sameCriteria =
    c.baseline.acceptance_limits_ref === c.target.acceptance_limits_ref;
  const sameIO =
    before.concurrency === after.concurrency &&
    before.output_tokens === after.output_tokens;
  const parts = {
    context: {
      title: "Context & memory path",
      change: "Expanded test coverage",
      description: "Input lengths included in the simulated validation result.",
      before: bins(before.context_bins),
      after: bins(after.context_bins),
      beforeSub: `${before.context_bins.length} input-token bins`,
      afterSub: `${after.context_bins.length} input-token bins · ${number(procedure.per_bin_minutes)} minutes each`,
      facts: [
        [
          "Maximum context",
          `${number(Math.max(...before.context_bins))} → ${number(Math.max(...after.context_bins))} tokens`,
        ],
        ["Memory configuration", c.config.memory_configuration],
      ],
    },
    compute: {
      title: "Compute array",
      change: "Extended workload testing",
      description:
        "Total validation duration across the requested context bins.",
      before: `${number(before.total_suite_minutes)} min`,
      after: `${number(procedure.suite_minutes)} min`,
      beforeSub: "Original total suite",
      afterSub: "Updated total suite · not per bin",
      facts: [
        ["Procedure", `${procedure.id} · v${procedure.content_version}`],
        [
          "Acceptance criteria",
          `${c.criteria.id}${sameCriteria ? " · unchanged" : ""}`,
        ],
      ],
    },
    io: {
      title: "I/O & scheduling",
      change: sameIO ? "Settings unchanged" : "Updated workload settings",
      description:
        "Concurrent requests and output length used for the comparison.",
      before: `${number(before.concurrency)} × ${number(before.output_tokens)}`,
      after: `${number(after.concurrency)} × ${number(after.output_tokens)}`,
      beforeSub: `${number(before.concurrency)} requests · ${number(before.output_tokens)} output tokens each`,
      afterSub: `${number(after.concurrency)} requests · ${number(after.output_tokens)} output tokens each`,
      facts: [
        [
          "Lab configuration",
          `${number(c.config.device_count)} device${c.config.device_count === 1 ? "" : "s"}`,
        ],
        ["Firmware / runtime", `${c.config.firmware} / ${c.config.runtime}`],
      ],
    },
  };
  const selected = parts[region];
  return (
    <div className="validation-final-check">
      <div className="vfc-heading">
        <div>
          <div className="vfc-eyebrow">
            {job.change_id} / VALIDATION SUMMARY
          </div>
          <strong>
            {c.config.product_id} · {c.config.product_revision} ·{" "}
            {job.configuration_id}
          </strong>
          <div className="vfc-summary">
            {after.context_bins.length} context bins ·{" "}
            {number(procedure.suite_minutes)} minutes · {procedure.id}
          </div>
        </div>
        <div className="vfc-result-preview">
          <span>
            <CheckCircle2 size={18} aria-hidden="true" />
            Passing result preview
          </span>
          <small>Simulated result · Not yet published</small>
        </div>
      </div>
      <p className="vfc-intro">
        Review the updated requirement and the passing result this demo will
        publish for the approved test scope.
      </p>
      <div className="vfc-toolbar">
        <div
          className="vfc-modes"
          role="group"
          aria-label="Requirement comparison"
        >
          {modes.map((m) => (
            <button
              key={m.id}
              type="button"
              aria-pressed={mode === m.id}
              onClick={() => setMode(m.id)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <span className="vfc-hint">
          <Move size={14} aria-hidden="true" />
          Drag to rotate · Scroll to zoom · Click to inspect
        </span>
      </div>
      <div className="vfc-workspace">
        <div className="vfc-diagram">
          <ValidationChipCanvas
            region={region}
            mode={mode}
            onRegionChange={setRegion}
          />
          <div className="vfc-regions" role="group" aria-label="Chip regions">
            {regions.map((r) => (
              <button
                key={r.id}
                type="button"
                aria-pressed={region === r.id}
                onClick={() => setRegion(r.id)}
              >
                <span>{r.number}</span>
                {r.label}
              </button>
            ))}
          </div>
        </div>
        <div className="vfc-inspector" aria-live="polite">
          <div className="vfc-selection-heading">
            <h3>{selected.title}</h3>
            <span>{selected.change}</span>
          </div>
          <p>{selected.description}</p>
          <div className="vfc-comparison">
            <div
              data-scope="before"
              className={mode === "after" ? "vfc-secondary-scope" : ""}
            >
              <div className="vfc-value-label">Original · {c.baseline.id}</div>
              <strong>{selected.before}</strong>
              <small>{selected.beforeSub}</small>
            </div>
            <ArrowRight className="vfc-arrow" size={17} aria-hidden="true" />
            <div
              data-scope="after"
              className={mode === "before" ? "vfc-secondary-scope" : ""}
            >
              <div className="vfc-value-label">Updated · {c.target.id}</div>
              <strong>{selected.after}</strong>
              <small>{selected.afterSub}</small>
            </div>
          </div>
          <dl className="vfc-facts">
            {selected.facts.map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
      <div className="vfc-scope-footer">
        <span>
          <ShieldCheck size={15} aria-hidden="true" />
          {sameConfiguration
            ? "Same chip configuration"
            : "Review configuration scope"}{" "}
          ·{" "}
          {sameCriteria
            ? "Acceptance limits unchanged"
            : "Review acceptance criteria"}
        </span>
        <Link to={`/engineering/changes/${encodeURIComponent(job.change_id)}`}>
          View requirement
          <ArrowRight size={14} aria-hidden="true" />
        </Link>
      </div>
      <div className="vfc-illustration-note">
        Illustrative block layout. Highlights represent workload validation, not
        physical design changes. A recorded test result is created only when you
        publish.
      </div>
    </div>
  );
}
