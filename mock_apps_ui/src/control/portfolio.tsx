import {
  caseFact,
  casePresentation,
  caseNames,
  nextBusinessStep,
  standardRunHandoff,
} from "./experience-model";
import { caseTone } from "./integration";
import { useHost } from "./host";
import { overviewSummary } from "./presentation-model";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Link, needsYourReview } from "./access";
import {
  ArrowRight,
  ChevronRight,
  SlidersHorizontal,
  Check,
  Layers3,
  CalendarClock,
} from "lucide-react";
import {
  casePath,
  date,
  programPath,
  ranked,
  useControl,
  words,
  type CaseData,
  type Program,
} from "./data";
import {
  StatusText,
  Empty,
  Heading,
  Section,
  SourceLink,
  SourceState,
  SourceContext,
} from "./ui";
import { AgentActivity } from "./agent-activity";
import {
  attentionSummary,
  healthTone,
  nextGate,
  overviewMetrics,
  shortCaseTitle,
} from "./overview-model";
export function Attention({
  cases,
  limit = 4,
  status = "attention",
}: {
  cases: CaseData[];
  limit?: number;
  status?: string;
}) {
  const host = useHost();
  const programs = new Set(cases.map((c) => c.change.program_id));
  const connected =
    host?.data?.case_summaries?.filter((c) => programs.has(c.program_id)) || [];
  const ids = new Set(connected.map((c) => c.change_id));
  const standard = host?.data?.standard;
  const standardHandoff = standardRunHandoff(standard);
  const standardRun = standard?.runs[0];
  const standardFallback =
    programs.has("PRG-A17") &&
    standard &&
    !ids.has("CR-019") &&
    standardHandoff?.status !== "handoff_verified"
      ? [
          {
            id: "CR-019",
            title: caseNames["CR-019"],
            detail: !standard.source_available
              ? "Current source unavailable"
              : standardRun?.status === "running"
                ? "Checking approved scope and evidence"
                : standardRun?.status === "completed"
                  ? `${standard.eligibility?.reusable_evidence_ids.length || 0} reusable evidence records`
                  : "Policy eligibility not assessed",
            label: !standard.source_available
              ? "Current state unavailable"
              : standardRun?.status === "running"
                ? "Investigating"
                : "New",
            next: !standard.source_available
              ? "Restore the source connection and refresh before acting."
              : standardRun?.status === "running"
                ? "Agent investigation in progress"
                : "Ready for investigation",
            to: "/control/programs/PRG-A17/cases/CR-019",
            priority: 45,
            tone: "warning" as const,
            state: standardRun?.status === "running" ? "investigating" : "new",
          },
        ]
      : [];
  const items = [
    ...connected
      .filter(
        (c) => status !== "attention" || c.attention !== "none" || host?.error,
      )
      .map((c) => ({
        id: c.change_id,
        title: casePresentation(
          host?.data,
          c.change_id,
          cases.find((v) => v.change.id === c.change_id),
          c.title,
        ).title,
        detail: host?.error
          ? "Stale read · Refresh current sources"
          : caseFact(
              host?.data,
              c,
              cases.find((v) => v.change.id === c.change_id),
            ),
        label: host?.error ? "Current state unavailable" : c.state_label,
        next: nextBusinessStep(host?.data, c),
        to: c.href,
        priority:
          c.change_id === "CR-019"
            ? c.state === "new"
              ? 5
              : 45
            : host?.error
              ? 25
              : host?.data?.decision_summaries?.some(
                    (d) =>
                      d.change_id === c.change_id &&
                      needsYourReview(host.capabilities, d),
                  )
                ? -1
                : c.priority,
        tone: c.state === "new" ? ("action" as const) : caseTone(c),
        state: c.state,
      })),
    ...standardFallback,
    ...(status === "attention"
      ? ranked(cases.filter((c) => !ids.has(c.change.id)))
      : cases.filter((c) => !ids.has(c.change.id))
    ).map((c) => ({
      id: c.change.id,
      title: shortCaseTitle(c),
      detail: attentionSummary(c).reason,
      label: attentionSummary(c).reason,
      next: c.change.owner || "Owner unrecorded",
      to: casePath(c),
      priority: 50,
      tone: attentionSummary(c).tone,
      state: c.change.workflow_state,
    })),
  ]
    .filter(
      (c) => status === "attention" || status === "all" || c.state === status,
    )
    .sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id))
    .slice(0, limit);
  return items.length ? (
    <ol className="cp-attention">
      {items.map((c) => (
        <li key={c.id} data-case-id={c.id} data-case-state={c.state}>
          <div className="cp-attention-main">
            <strong>
              {c.id} · {c.title}
            </strong>
            <StatusText tone={c.tone}>{c.label}</StatusText>
            <p>{c.detail}</p>
            <div className="cp-attention-followup">
              <small>{c.next}</small>
              <Link
                className="cp-text-link"
                to={c.to}
                aria-label={`Inspect case ${c.id}`}
              >
                Inspect case <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </li>
      ))}
    </ol>
  ) : (
    <Empty>
      {status === "attention"
        ? "No cases need attention in this scope."
        : "No cases match this status."}
    </Empty>
  );
}

export function ProgramRows({
  programs,
  compact = false,
}: {
  programs: Program[];
  compact?: boolean;
}) {
  const { data } = useControl();
  return (
    <div className="cp-program-rows">
      {programs.map((p) => {
        const gate = nextGate(p.id, data!.milestones);
        return (
          <Link to={programPath(p.id)} className="cp-program-row" key={p.id}>
            <div className="cp-card-title">
              <strong>{p.name || p.id}</strong>
              <ChevronRight size={18} aria-hidden="true" />
            </div>
            <div className="cp-card-status">
              <small>{words(p.lifecycle)}</small>
              <StatusText tone={healthTone(p.health)}>
                {words(p.health)}
              </StatusText>
            </div>
            <div className="cp-card-gate">
              <small>
                Next gate ·{" "}
                {gate ? `${date(gate.baseline_at)} baseline` : "Unavailable"}
              </small>
              {!compact && (
                <span>{gate?.name || "No open milestone recorded"}</span>
              )}
            </div>
            {!compact && p.next_action && <p>{p.next_action}</p>}
          </Link>
        );
      })}
    </div>
  );
}
export function Timeline({ programs }: { programs: Program[] }) {
  const { data } = useControl();
  const milestones = programs
    .flatMap((p) => {
      const m = data!.milestones
        .filter((m) => m.program_id === p.id && m.health !== "completed")
        .sort((a, b) => a.baseline_at.localeCompare(b.baseline_at))[0];
      return m ? [{ ...m, programName: p.name || p.id }] : [];
    })
    .sort((a, b) => a.baseline_at.localeCompare(b.baseline_at));
  return (
    <div className="cp-milestones">
      {milestones.map((m) => (
        <div key={m.id}>
          <span className="cp-timeline-dot" />
          <small>{date(m.baseline_at)} · baseline</small>
          <strong>{m.programName}</strong>
          <p>{m.name}</p>
          <SourceLink to={`/programs/${m.program_id}/milestones/${m.id}`}>
            Inspect milestone
          </SourceLink>
          <small>
            Forecast {date(m.current_forecast_at)}
            <br />
            {words(m.forecast_status)}
          </small>
        </div>
      ))}
    </div>
  );
}
export function Activity({
  cases,
  programIds,
  limit = 4,
}: {
  cases?: CaseData[];
  programIds?: string[];
  limit?: number;
}) {
  const { data } = useControl();
  const events = (cases ? cases.flatMap((c) => c.audit) : data?.activity || [])
    .filter((a) => !programIds || programIds.includes(a.program_id || ""))
    .sort((a, b) => b.sequence - a.sequence)
    .slice(0, limit);
  return events.length ? (
    <ol className="cp-activity">
      {events.map((e) => (
        <li key={e.id}>
          <span className="cp-activity-dot" />
          <div>
            <strong>{words(e.action)}</strong>
            <p>
              {e.resource_id} · {words(e.domain)} · {e.outcome}
            </p>
            <small>
              {date(e.scenario_at, true)} · Recorded source activity
            </small>
          </div>
          {e.change_id && e.program_id && (
            <Link
              className="cp-text-link"
              to={`${programPath(e.program_id)}/cases/${e.change_id}`}
            >
              Inspect <ChevronRight size={14} />
            </Link>
          )}
        </li>
      ))}
    </ol>
  ) : (
    <Empty>
      No source activity recorded for this scope. No investigation run is
      implied.
    </Empty>
  );
}
function ProgramDirectory() {
  const directory = true;
  const { data } = useControl();
  const [params, setParams] = useSearchParams();
  const scope = params.get("scope") || (directory ? "all" : "focus"),
    search = params.get("q") || "",
    stage = params.get("stage") || "all",
    health = params.get("health") || "all";
  const filter = (key: string, value: string) => {
    // Read the committed URL so rapid edits cannot resurrect a cleared filter
    // while React Router is still rendering its preceding transition.
    const next = new URLSearchParams(window.location.search);
    value ? next.set(key, value) : next.delete(key);
    setParams(next);
  };
  const programs = (data?.programs || []).filter(
    (p) =>
      (scope !== "focus" || ["PRG-A17", "PRG-P01", "PRG-P02"].includes(p.id)) &&
      (stage === "all" || p.lifecycle === stage) &&
      (health === "all" || p.health === health) &&
      `${p.name} ${p.customer_name} ${p.id} ${p.owner}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const ids = programs.map((p) => p.id),
    cases = data?.cases.filter((c) => ids.includes(c.change.program_id)) || [];
  const metrics = overviewMetrics(programs, cases)
    .filter((metric) => metric.label !== "Active investigations")
    .map((metric) =>
      metric.label === "Needs review"
        ? { ...metric, label: "Source plan drafts" }
        : metric,
    );
  const hasFilters =
    search ||
    stage !== "all" ||
    health !== "all" ||
    scope !== (directory ? "all" : "focus");
  return (
    <>
      <div className="cp-portfolio-header">
        <Heading
          eyebrow="Portfolio"
          title="Every program. One clear view."
          description="Track health, upcoming gates and the next action across your programs."
        />
        <div className="cp-filters">
          <span>
            <SlidersHorizontal size={16} aria-hidden="true" />
            View
          </span>
          <select
            aria-label="Program scope"
            value={scope}
            onChange={(e) => filter("scope", e.target.value)}
          >
            <option value="focus">Focus programs</option>
            <option value="all">All source programs</option>
          </select>
          <select
            aria-label="Lifecycle filter"
            value={stage}
            onChange={(e) => filter("stage", e.target.value)}
          >
            <option value="all">All lifecycle stages</option>
            {[
              ...new Set(
                data?.programs.map((p) => p.lifecycle).filter(Boolean),
              ),
            ].map((s) => (
              <option key={s} value={s!}>
                {words(s)}
              </option>
            ))}
          </select>
          <select
            aria-label="Program status"
            value={health}
            onChange={(e) => filter("health", e.target.value)}
          >
            <option value="all">All statuses</option>
            {[
              ...new Set(data?.programs.map((p) => p.health).filter(Boolean)),
            ].map((value) => (
              <option key={value} value={value!}>
                {words(value)}
              </option>
            ))}
          </select>
          <input
            aria-label="Search programs"
            placeholder="Search programs or customers"
            value={search}
            onChange={(e) => filter("q", e.target.value)}
          />
          {hasFilters && (
            <button onClick={() => setParams({})}>Clear filters</button>
          )}
        </div>
      </div>
      <SourceState>
        <div className="cp-metrics" aria-label="Scoped source metrics">
          {metrics.map(({ label, value, tone }) => (
            <div key={label} data-metric={label}>
              <span>{label}</span>
              <strong
                className={
                  value === null
                    ? "cp-metric-unavailable"
                    : value > 0
                      ? `cp-metric-${tone}`
                      : ""
                }
              >
                {value ?? "Unavailable"}
              </strong>
            </div>
          ))}
        </div>
        <details className="cp-metric-definitions">
          <summary>Metric definitions</summary>
          <p>
            Counts cover only the {programs.length} filtered source programs.
            Illustrative entries are excluded. Stale reads retain their last
            observed values.
          </p>
          <dl>
            <div>
              <dt>Programs</dt>
              <dd>Distinct displayed source programs.</dd>
            </div>
            <div>
              <dt>Source plan drafts</dt>
              <dd>
                Distinct current draft source plans on open cases. A source plan
                does not establish a reviewable host proposal.
              </dd>
            </div>
            <div>
              <dt>At risk</dt>
              <dd>
                Programs with source health: validation risk, at risk,
                manufacturing constraint, recovery active, blocked or waiting on
                customer. Unknown health makes this metric unavailable; on track
                and completed are excluded.
              </dd>
            </div>
          </dl>
        </details>
        {programs.length ? (
          <>
            <Section
              title={directory ? "Program directory" : "Program overview"}
              className="cp-overview-section"
              action={
                !directory && (
                  <Link className="cp-text-link" to="/control/programs">
                    All programs <ArrowRight size={15} />
                  </Link>
                )
              }
            >
              <ProgramRows programs={programs} />
            </Section>
            <details className="cp-secondary-content">
              <summary>Upcoming gates</summary>
              <p className="cp-caption">
                Earliest open milestone per program; baseline, forecast and
                commitment remain separate.
              </p>
              <Timeline programs={programs.slice(0, 3)} />
            </details>
            <details className="cp-secondary-content">
              <summary>Recent source activity</summary>
              <p className="cp-caption">
                Recorded source events. These are not agent runs or decisions.
              </p>
              <Activity programIds={ids} limit={3} />
            </details>
          </>
        ) : (
          <Empty>No matching programs. Adjust the directory filters.</Empty>
        )}
      </SourceState>
    </>
  );
}

export function Portfolio({ directory = false }: { directory?: boolean }) {
  return directory ? <ProgramDirectory /> : <Overview />;
}
const overviewVoices: Record<
  string,
  { persona: string; title: string; description: string }
> = {
  automation: {
    persona: "Program operator",
    title: "Move every program forward.",
    description:
      "Follow the work, resolve the exceptions, and keep the next decision moving.",
  },
  engineer: {
    persona: "Engineering approver",
    title: "Engineering decisions, in focus.",
    description:
      "Review the evidence, choose the path, and keep acceptance accountable.",
  },
  program_owner: {
    persona: "Program owner",
    title: "Protect delivery. Choose the path.",
    description:
      "See the business exposure and decide which recovery or delivery plan to pursue.",
  },
  reader: {
    persona: "Viewer",
    title: "Your programs, at a glance.",
    description:
      "See what is moving, what needs attention, and what has been verified.",
  },
};
function Overview() {
  const host = useHost();
  const { data, freshness } = useControl();
  const summary = data ? overviewSummary(data) : null;
  const [status, setStatus] = useState("attention");
  const role = host?.capabilities?.role || "reader";
  useEffect(() => setStatus("attention"), [role]);
  const voice = overviewVoices[role] || overviewVoices.reader;
  const current =
    !host?.error &&
    host?.data?.source_available &&
    freshness === "Current read";
  const scopedCases = (host?.data?.case_summaries || []).filter((c) =>
    summary?.programs.some((p) => p.id === c.program_id),
  );
  const statusLabels = new Map<string, string>([
    ...scopedCases.map((c) => [c.state, c.state_label] as [string, string]),
    ...(summary?.cases || [])
      .filter((c) => !scopedCases.some((h) => h.change_id === c.change.id))
      .map(
        (c) =>
          [c.change.workflow_state, words(c.change.workflow_state)] as [
            string,
            string,
          ],
      ),
  ]);
  // A completed run may remove the last occurrence of the selected status.
  // Retain its label so the empty filtered state stays understandable.
  if (!["all", "attention"].includes(status) && !statusLabels.has(status))
    statusLabels.set(status, words(status));
  const statuses = [...statusLabels.entries()];
  const verified = current
    ? scopedCases.filter(
        (c) =>
          c.source_available &&
          [
            "completed_technical",
            "completed_recovery",
            "handoff_verified",
          ].includes(c.state),
      )
    : [];
  const needsReview = current
    ? (host?.data?.decision_summaries || []).filter((d) =>
        needsYourReview(host?.capabilities, d),
      ).length
    : null;
  const focus =
    summary?.programs.find((p) => p.id === "PRG-A17") || summary?.programs[0];
  const gate = focus && data ? nextGate(focus.id, data.milestones) : null;
  return (
    <div className="rb-overview">
      <div className="rb-read-context">
        <SourceContext />
      </div>
      <Heading
        eyebrow={`Overview · ${voice.persona}`}
        title={voice.title}
        description={voice.description}
        action={
          <Link to="/control/programs" className="cp-button cp-primary">
            <Layers3 size={17} /> All programs <ArrowRight size={17} />
          </Link>
        }
      />
      <SourceState>
        {summary && (
          <>
            {focus && (
              <section
                className="rb-program-ribbon"
                aria-label="Program in focus"
              >
                <div className="rb-ribbon-program">
                  <Layers3 size={23} aria-hidden="true" />
                  <div>
                    <strong>{focus.name || focus.id}</strong>
                    <small>
                      {focus.customer_name} · {words(focus.lifecycle)}
                    </small>
                  </div>
                </div>
                <StatusText tone={healthTone(focus.health)}>
                  {words(focus.health)}
                </StatusText>
                <div className="rb-ribbon-gate">
                  <CalendarClock size={18} aria-hidden="true" />
                  <div>
                    <strong>{gate?.name || "No open gate recorded"}</strong>
                    <small>
                      {gate
                        ? `Baseline · ${date(gate.baseline_at)}`
                        : "Check source milestones"}
                    </small>
                  </div>
                </div>
                <Link to={programPath(focus.id)} className="cp-text-link">
                  Open program <ArrowRight size={16} />
                </Link>
              </section>
            )}
            <div className="cp-work-grid cp-overview-work rb-work-grid">
              <AgentActivity
                scope="Overview focus programs"
                programIds={summary.programs.map((p) => p.id)}
              />
              <Section
                title={
                  status === "attention" ? "Needs attention" : "Case activity"
                }
                className="cp-attention-section rb-attention-panel"
                action={
                  <label className="rb-status-filter">
                    <SlidersHorizontal size={14} aria-hidden="true" />
                    <select
                      aria-label="Case status"
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                    >
                      <option value="attention">Needs attention</option>
                      <option value="all">All statuses</option>
                      {statuses.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                }
              >
                {needsReview !== null && needsReview > 0 && (
                  <Link className="rb-review-link" to="/control/decisions">
                    {needsReview}{" "}
                    {needsReview === 1 ? "decision needs" : "decisions need"}{" "}
                    your review <ArrowRight size={14} />
                  </Link>
                )}
                <Attention
                  cases={summary.cases}
                  limit={status === "attention" ? 5 : 50}
                  status={status}
                />
              </Section>
            </div>
            <Section
              title="Verified outcomes"
              className="rb-outcomes"
              note="Completed work confirmed in the source systems."
            >
              {verified.length ? (
                <div className="rb-outcome-list">
                  {verified.map((c) => (
                    <article key={c.change_id} data-verified-case={c.change_id}>
                      <span className="rb-outcome-check">
                        <Check size={17} aria-hidden="true" />
                      </span>
                      <div>
                        <Link to={c.href}>
                          <strong>
                            {c.change_id} · {c.state_label}
                          </strong>
                        </Link>
                        <p>{c.detail}</p>
                        <SourceLink to={c.source_href}>
                          View source record
                        </SourceLink>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="rb-outcome-empty">
                  {current
                    ? "Verified outcomes will appear here as work is completed."
                    : "Refresh current sources to confirm completed outcomes."}
                </p>
              )}
            </Section>
            <Section
              title="Programs in focus"
              className="cp-overview-section rb-focus-programs"
              action={
                <Link className="cp-text-link" to="/control/programs">
                  All programs <ArrowRight size={16} />
                </Link>
              }
            >
              <ProgramRows programs={summary.programs} compact />
            </Section>
            <details className="cp-secondary-content rb-portfolio-context">
              <summary>Portfolio health & upcoming gates</summary>
              <div className="rb-health-summary">
                <div data-metric="Programs">
                  <strong>{summary.programs.length}</strong>
                  <span>Programs in focus</span>
                </div>
                <div data-metric="At risk">
                  <strong>
                    {summary.metrics.find((m) => m.label === "At risk")
                      ?.value ?? "—"}
                  </strong>
                  <span>At risk</span>
                </div>
                <div data-metric="Needs review">
                  <strong>{needsReview ?? "—"}</strong>
                  <span>Needs your review</span>
                </div>
              </div>
              <p className="cp-caption">
                Source health for the three focus programs. Program health,
                baseline dates and technical acceptance remain separate.
              </p>
              <Timeline programs={summary.programs} />
            </details>
            <details className="cp-secondary-content">
              <summary>Recent source activity</summary>
              <Activity
                programIds={summary.programs.map((p) => p.id)}
                limit={3}
              />
            </details>
          </>
        )}
      </SourceState>
    </div>
  );
}
