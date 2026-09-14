import { useEffect, useId, useState, useRef, useLayoutEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Workflow,
  FileDiff,
  FlaskConical,
  CalendarClock,
  Boxes,
  Check,
  CircleHelp,
  CircleAlert,
  Pause,
  ArrowUpRight,
  Info,
  RefreshCw,
  GitBranch,
  MessageSquare,
} from "lucide-react";
import { agentRoles } from "./agent-roles";
import { FindingSummary, SourceReferenceList } from "./traceability";
import {
  useAgentWorkspace,
  type WorkAgent,
  type WorkRun,
} from "./agent-workspace-data";
import { useHost } from "./host";
import { Link, needsYourReview } from "./access";
import { Dialog } from "./dialog";
import { Facts } from "./ui";
import { date, words } from "./data";
import { nextBusinessStep } from "./experience-model";
import "./rethink-workspace.css";
export const EXPLAIN_AGENT = "stratos:explain-agent";
const icons = {
  coordinator: Workflow,
  change_impact: FileDiff,
  validation_evidence: FlaskConical,
  program_commercial: CalendarClock,
  manufacturing: Boxes,
};
const aliases = {
  coordinator: "Coordinator",
  change_impact: "Change impact",
  validation_evidence: "Validation",
  program_commercial: "Program & commercial",
  manufacturing: "Manufacturing",
};
const stateNames = {
  working: "Processing",
  delegated: "With specialists",
  queued: "Requested",
  completed: "Task complete",
  failed: "Task failed",
  cancelled: "Task cancelled",
  not_invoked: "Not invoked",
  idle: "Idle",
  unknown: "Not observed",
};
export function AgentWorkspace({
  scope,
  programIds,
}: {
  scope: string;
  programIds?: string[];
}) {
  const headingId = useId();
  const location = useLocation();
  useEffect(() => {
    if (location.hash !== "#agent-workspace") return;
    const frame = requestAnimationFrame(() =>
      stageRef.current
        ?.closest(".aw-workspace")
        ?.scrollIntoView({ block: "start" }),
    );
    return () => cancelAnimationFrame(frame);
  }, [location.hash]);
  const stageRef = useRef<HTMLDivElement>(null);
  const [connections, setConnections] = useState<
    { id: string; path: string }[]
  >([]);
  const host = useHost(),
    navigate = useNavigate();
  const enabled =
    !!host?.capabilities &&
    (!programIds || programIds.includes(host.capabilities.program_id));
  const view = useAgentWorkspace(enabled),
    data = view.data;
  const [inspector, setInspector] = useState<string | null>(null),
    [showHealth, setShowHealth] = useState(false),
    [runFilter, setRunFilter] = useState("all");
  useEffect(() => {
    setInspector(null);
    setShowHealth(false);
  }, [view.resetVersion, view.selection, runFilter]);
  useEffect(() => setRunFilter("all"), [view.resetVersion]);
  const runs = data?.runs || [];
  const runStatuses = [...new Set(runs.map((run) => run.status))];
  const filteredRuns = runs.filter(
    (run) => runFilter === "all" || run.status === runFilter,
  );
  // A status filter changes only the observed list. Each graph still represents
  // exactly one permitted run; filtering never invokes or combines workflows.
  const selected =
    filteredRuns.find(
      (r) => r.run_id === (view.selection ?? data?.selected_run_id),
    ) || filteredRuns[0];
  const active = (data?.runs || []).filter((r) => r.status === "running");
  const relevant = selected ? [selected] : [];
  const uncertain = !enabled || !!view.error || !data || view.stale;
  const agents: WorkAgent[] = agentRoles.map(
    (role) =>
      selected?.agents.find((agent) => agent.id === role.id) || {
        id: role.id,
        name: role.name,
        short_name: aliases[role.id],
        state: uncertain || selected ? "unknown" : "idle",
        label: uncertain || selected ? "Not observed" : "Idle",
        tasks: [],
        callers: [],
      },
  );
  // Keep the complete roster visible. Only this selected run supplies tasks.
  const rendered = agents.map((a) =>
    uncertain &&
    ["working", "delegated", "queued", "idle", "not_invoked"].includes(a.state)
      ? {
          ...a,
          state: "unknown" as const,
          label: view.stale ? "Read out of date" : "Not observed",
        }
      : a,
  );
  const appearance = (agent: WorkAgent) => {
    const freshActive =
      !uncertain &&
      relevant.some(
        (run) =>
          run.status === "running" &&
          run.telemetry === "current" &&
          run.agents.some(
            (observed) =>
              observed.id === agent.id && observed.state === agent.state,
          ),
      );
    if (agent.state === "working")
      return freshActive ? "processing" : "unknown";
    if (["delegated", "queued"].includes(agent.state) && !freshActive)
      return "unknown";
    if (agent.state === "completed") return "completed";
    if (["cancelled", "not_invoked", "idle"].includes(agent.state))
      return "idle";
    return agent.state;
  };
  const statusLabel = (agent: WorkAgent) => {
    const state = appearance(agent);
    if (state === "processing") return "Processing";
    if (state === "completed") return "Completed";
    if (state === "idle") return "Idle";
    if (state === "unknown")
      return view.stale ? "Read out of date" : "Status unknown";
    if (state === "queued") return "Queued";
    return agent.label;
  };
  useLayoutEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    const measure = () => {
      const bounds = stage.getBoundingClientRect();
      const manager = stage.querySelector<HTMLElement>(
        ".aw-manager .aw-agent",
      )!;
      if (!manager) {
        setConnections([]);
        return;
      }
      const origin = manager.getBoundingClientRect();
      const x = origin.x + origin.width / 2 - bounds.x;
      const y = origin.bottom - bounds.y + 2;
      const specialists = Array.from(
        stage.querySelectorAll<HTMLElement>(".aw-specialist-row .aw-agent"),
      );
      const firstTop = specialists[0]?.getBoundingClientRect().top ?? 0;
      setConnections(
        specialists.map((el, index) => {
          const target = el.getBoundingClientRect();
          const tx = target.x + target.width / 2 - bounds.x;
          const ty = target.top - bounds.y;
          const mid = y + 16;
          // Lower mobile row routes around the outside of the upper agents.
          const outer = index % 2 === 0 ? 2 : bounds.width - 2;
          const path =
            target.top > firstTop + 20
              ? `M ${x} ${y} V ${mid} H ${outer} V ${ty - 12} H ${tx} V ${ty}`
              : `M ${x} ${y} V ${mid} H ${tx} V ${ty}`;
          return { id: el.dataset.agentId!, path };
        }),
      );
    };
    const observer = new ResizeObserver(measure);
    observer.observe(stage);
    stage
      .querySelectorAll(".aw-agent")
      .forEach((node) => observer.observe(node));
    measure();
    return () => observer.disconnect();
  }, [rendered.map((agent) => agent.id).join("|")]);
  // Latest checkpoint observations only: this API does not retain transitions.
  const observations = relevant
    .flatMap((run) =>
      run.agents.flatMap((agent) =>
        agent.tasks
          .filter(
            (task) =>
              task.observed_at && Number.isFinite(Date.parse(task.observed_at)),
          )
          .map((task, index) => ({
            run,
            agent,
            task,
            key: `${run.run_id}:${agent.id}:${index}`,
          })),
      ),
    )
    .sort(
      (a, b) =>
        Date.parse(b.task.observed_at!) - Date.parse(a.task.observed_at!),
    )
    .slice(0, 5);
  const tasks = relevant.flatMap((run) =>
    run.agents.flatMap((agent) => agent.tasks),
  );
  const countsKnown =
    !uncertain &&
    relevant.every(
      (run) =>
        !["stale", "unavailable"].includes(run.telemetry) &&
        run.agents.every(
          (agent) =>
            agent.state !== "unknown" &&
            agent.tasks.every((task) => task.state !== "unknown"),
        ),
    );
  const workload = (agent: WorkAgent) => {
    if (agent.state === "completed") {
      const completed = agent.tasks.filter(
        (task) => task.state === "completed",
      ).length;
      return completed > 1
        ? `${completed} completed tasks`
        : agent.id === "coordinator"
          ? "Run complete"
          : "Task complete";
    }
    if (agent.state === "cancelled") return "Task cancelled";
    if (appearance(agent) === "idle")
      return selected ? "Not used in this run" : "No assigned task";
    if (uncertain || appearance(agent) === "unknown") return "Workload unknown";
    if (agent.id === "coordinator" && appearance(agent) === "processing")
      return agent.label;
    const working = agent.tasks.filter(
      (task) => task.state === "working",
    ).length;
    const queued = agent.tasks.filter((task) => task.state === "queued").length;
    if (working) return `${working} active task${working === 1 ? "" : "s"}`;
    if (queued) return `${queued} requested task${queued === 1 ? "" : "s"}`;
    if (agent.state === "delegated") return "With specialists";
    const completed = agent.tasks.filter(
      (task) => task.state === "completed",
    ).length;
    return `${completed} completed task${completed === 1 ? "" : "s"}`;
  };
  const taskLabel = (agent: WorkAgent) => {
    if (uncertain || appearance(agent) === "unknown")
      return "Current task unavailable";
    const task =
      [...agent.tasks].reverse().find((item) => item.state === agent.state) ||
      agent.tasks.at(-1);
    return task?.label || workload(agent);
  };
  const current = rendered.find((a) => a.id === inspector);
  const runsForAgent = selected ? [selected] : [];
  const snapshotCurrent =
    host?.data &&
    !host.error &&
    Date.now() - Date.parse(host.data.fetched_at) < 30000;
  const review =
    selected && snapshotCurrent
      ? host?.data?.decision_summaries?.find(
          (d) =>
            d.run_id === selected.run_id &&
            d.id === selected.handoff?.record_id &&
            d.version === selected.handoff?.version &&
            d.digest === selected.handoff?.digest &&
            d.current &&
            d.requires_human &&
            needsYourReview(host.capabilities, d),
        )
      : undefined;
  const selectedCase =
    selected && snapshotCurrent
      ? host?.data?.case_summaries?.find(
          (item) =>
            item.change_id === selected.case_id &&
            item.run_id === selected.run_id,
        )
      : undefined;
  const footer = selected
    ? `${selected.case_id} · ${review ? "Awaiting your review" : selected.handoff?.label || (selected.telemetry === "stale" ? "Observation stale" : selected.status === "running" ? "Investigation in progress" : "Recorded result")}`
    : data && !uncertain
      ? active.length
        ? `${active.length} active runs · Select a run to inspect its work`
        : "No active investigation"
      : enabled
        ? "Current activity unavailable"
        : "Activity not connected for this program";
  function explain(run: WorkRun, agent: WorkAgent) {
    const context = run.links.find((l) => l.label === "Open case")!.href;
    setInspector(null);
    navigate(context);
    window.dispatchEvent(
      new CustomEvent(EXPLAIN_AGENT, {
        detail: {
          context,
          query: `Explain the recorded ${agent.name} findings for ${run.case_id}, run ${run.run_id}. Keep this run separate from current case state.`,
        },
      }),
    );
  }
  function node(a: WorkAgent) {
    const Icon = icons[a.id];
    const state = appearance(a);
    const label = statusLabel(a);
    return (
      <button
        key={a.id}
        type="button"
        className={`aw-agent aw-${state}`}
        data-agent-id={a.id}
        data-state={a.state}
        data-display-state={state}
        onClick={() => setInspector(a.id)}
        aria-label={`${a.name} · ${label}${selected ? " · " + selected.case_id : ""} · Open details`}
      >
        <span className="aw-ring">
          <Icon size={23} strokeWidth={1.65} aria-hidden="true" />
          {state === "completed" ? (
            <Check className="aw-marker" size={17} />
          ) : state === "failed" ? (
            <CircleAlert className="aw-marker" size={17} />
          ) : state === "unknown" ? (
            <CircleHelp className="aw-marker" size={16} />
          ) : a.state === "delegated" ? (
            <GitBranch className="aw-marker" size={16} />
          ) : ["queued", "cancelled"].includes(a.state) ? (
            <Pause className="aw-marker" size={16} />
          ) : null}
        </span>
        <span className="aw-agent-copy">
          <strong>{a.short_name}</strong>
          <span>{label}</span>
          <small className="aw-task-label" title={taskLabel(a)}>
            {taskLabel(a)}
          </small>
        </span>
      </button>
    );
  }
  return (
    <section
      className="cp-section aw-workspace"
      aria-labelledby={headingId}
      data-selection={selected?.run_id || "all"}
    >
      <header className="aw-heading">
        <h2 id={headingId}>Agent workspace</h2>
        <div>
          <button
            className="aw-icon-button"
            onClick={() => setShowHealth(true)}
            aria-label="Workspace telemetry details"
          >
            <Info size={18} />
          </button>
          <button
            className="aw-icon-button"
            onClick={() => void view.refresh()}
            aria-label="Refresh agent activity"
            disabled={!enabled}
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </header>
      <div className="aw-scope">
        <label className="aw-status-filter">
          <span>Run status</span>
          <select
            aria-label="Run status filter"
            value={runFilter}
            disabled={!data}
            onChange={(event) => setRunFilter(event.target.value)}
          >
            <option value="all">All</option>
            {runStatuses.map((status) => (
              <option key={status} value={status}>
                {words(status)}
              </option>
            ))}
            {runFilter !== "all" && !runStatuses.includes(runFilter) && (
              <option value={runFilter}>{words(runFilter)}</option>
            )}
          </select>
        </label>
        <label className="aw-run-selector">
          <span>Investigation</span>
          <select
            aria-label="Agent work scope"
            value={selected?.run_id || ""}
            disabled={!data || !filteredRuns.length}
            onChange={(event) => {
              setInspector(null);
              view.select(event.target.value);
            }}
          >
            {!selected && (
              <option value="">
                {runs.length ? "No matching runs" : "No investigations"}
              </option>
            )}
            {filteredRuns.map((run, index) => (
              <option key={run.run_id} value={run.run_id}>
                {run.case_id} · {words(run.status)} ·{" "}
                {date(run.started_at, true)} · {index + 1}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="aw-run-context">
        <span
          className={`aw-observation-state ${uncertain ? "aw-read-uncertain" : ""}`}
        >
          {uncertain
            ? view.stale
              ? "Read out of date"
              : "Activity unavailable"
            : selected
              ? selected.telemetry === "current" &&
                selected.status === "running"
                ? "Current observation"
                : selected.telemetry === "stale" ||
                    selected.telemetry === "unavailable"
                  ? "Recorded observation · Refresh required"
                  : "Recorded run"
              : runs.length
                ? "No runs match this filter"
                : "Ready for an investigation"}
        </span>
        {active.length > 0 && selected?.status !== "running" && (
          <button
            className="cp-text-link"
            onClick={() => {
              setRunFilter("all");
              view.select(undefined);
            }}
          >
            Back to live activity
          </button>
        )}
      </div>
      {host?.data?.pending_source_event && (
        <p className="aw-opening" role="status">
          QE-011 starts automatically after the 8-second Manufacturing event
          delay.
        </p>
      )}
      <div
        className="aw-stage"
        ref={stageRef}
        aria-live="polite"
        aria-label={
          selected
            ? `Agents for ${selected.case_id} selected run`
            : "Agent workspace idle"
        }
      >
        <div className="aw-manager">
          {rendered[0] ? (
            node(rendered[0])
          ) : (
            <p className="aw-empty">
              {uncertain
                ? "Reading agent activity…"
                : "No active investigation"}
            </p>
          )}
        </div>
        <svg className="aw-relationship-lines" aria-hidden="true">
          {connections.map(({ id, path }) => {
            const agent = rendered.find((agent) => agent.id === id);
            const state = agent ? appearance(agent) : "unknown";
            const flowing = state === "processing";
            return (
              <g
                key={id}
                data-connection={id}
                className={`${flowing ? "aw-flowing" : ""} aw-branch-${id} aw-line-${state}`}
              >
                <path d={path} />
                {flowing && (
                  <circle r="4" style={{ offsetPath: `path('${path}')` }} />
                )}
              </g>
            );
          })}
        </svg>
        <div
          className={`aw-specialist-row aw-participants-${Math.max(0, rendered.length - 1)}`}
        >
          {rendered.slice(1).map(node)}
        </div>
      </div>
      <footer
        className={`aw-handoff aw-handoff-${selected?.handoff?.kind || "idle"}`}
        aria-live="polite"
      >
        <span>
          {selected?.handoff?.kind === "attention" ? (
            <CircleAlert size={18} />
          ) : selected?.handoff?.kind === "complete" ? (
            <Check size={18} />
          ) : (
            <Pause size={18} />
          )}
          <span className="aw-handoff-copy">
            <strong>
              {selectedCase
                ? `${selectedCase.change_id} · ${selectedCase.state_label}`
                : footer}
            </strong>
            {selectedCase && (
              <small>{nextBusinessStep(host?.data, selectedCase)}</small>
            )}
            {!selectedCase && selected && (
              <small>
                {selected.status === "running"
                  ? "Findings will appear as work is recorded."
                  : "Open the case for its current outcome and next step."}
              </small>
            )}
          </span>
        </span>
        {selected && !uncertain && (
          <Link
            to={review?.href || selected.links[0].href}
            aria-label={
              review
                ? "Inspect your exact decision"
                : "Inspect " + selected.case_id
            }
          >
            <span>{review ? "Review" : "Open case"}</span>
            <ArrowUpRight size={16} />
          </Link>
        )}
      </footer>
      <details className="aw-activity-details">
        <summary>Activity details</summary>
        <div className="aw-observations" aria-label="Latest task observations">
          <div className="aw-observation-heading">
            <span>Latest observations</span>
            <span>
              {data
                ? `Read at ${new Date(data.read_at).toLocaleTimeString("en-GB", { timeZone: "UTC", hour: "2-digit", minute: "2-digit", second: "2-digit" })} UTC`
                : "No current read"}
            </span>
          </div>
          {observations.length ? (
            <div className="aw-observation-strip">
              {observations.map(({ run, agent, task, key }) => (
                <button
                  key={key}
                  className={`aw-observation aw-event-${task.state}`}
                  title={`${run.case_id} · ${agent.short_name} · ${task.label} · ${date(task.observed_at!, true)} · Latest checkpoint observation`}
                  onClick={() => setInspector(agent.id)}
                  aria-label={`${run.case_id} · ${agent.short_name} · ${task.label} · ${date(task.observed_at!, true)} · Open agent details`}
                >
                  <span className="aw-event-dot" aria-hidden="true" />
                  <span>{agent.short_name}</span>
                  <time dateTime={task.observed_at!}>
                    {new Date(task.observed_at!).toLocaleTimeString("en-GB", {
                      timeZone: "UTC",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}{" "}
                    UTC
                  </time>
                </button>
              ))}
            </div>
          ) : (
            <p>No task observations in this scope</p>
          )}
        </div>
        <div className="aw-metrics" aria-label="Workload in selected scope">
          <div>
            <strong>
              {countsKnown
                ? relevant.filter((run) => run.status === "running").length
                : "—"}
            </strong>
            <span>Active runs</span>
          </div>
          <div>
            <strong>
              {countsKnown
                ? tasks.filter((task) => task.state === "working").length
                : "—"}
            </strong>
            <span>Active tasks</span>
          </div>
          <div>
            <strong>
              {countsKnown
                ? tasks.filter((task) => task.state === "failed").length
                : "—"}
            </strong>
            <span>Failed tasks</span>
          </div>
        </div>
        <p className="aw-count-scope">
          {selected
            ? `${selected.case_id} · Selected run`
            : "Permitted active runs"}{" "}
          · {countsKnown ? "Observed task counts" : "Counts unavailable"}
        </p>
      </details>
      {current && (
        <Dialog
          title={current.name}
          close={() => setInspector(null)}
          closeLabel="Close agent inspector"
          note="Recorded business observations"
          footer={
            selected && (
              <>
                <Link to={selected.links[0].href} className="cp-text-link">
                  Open case
                </Link>
                {selected.links
                  .filter((l) => l.label === "View run")
                  .map((l) => (
                    <Link key={l.href} to={l.href} className="cp-text-link">
                      View run
                    </Link>
                  ))}
                {!uncertain && (
                  <button onClick={() => explain(selected, current)}>
                    <MessageSquare size={16} /> Explain in Concierge
                  </button>
                )}
              </>
            )
          }
        >
          <div className="aw-inspector">
            <p className="aw-inspector-state">
              {current.label}
              {selected ? " · " + selected.case_id : ""}
            </p>
            <Facts
              rows={[
                ["Identity", current.id],
                ["Scope", `${data?.program_id || "Unavailable"} · ${scope}`],
                [
                  "Selection",
                  selected
                    ? `${selected.status === "running" ? "Active" : "Recorded"} run · ${selected.run_id}`
                    : "All permitted active work",
                ],
                [
                  "Observed",
                  selected?.observed_at
                    ? date(selected.observed_at, true)
                    : "No checkpoint observation",
                ],
                ["Read", data ? date(data.read_at, true) : "Unavailable"],
              ]}
            />
            {uncertain && (
              <p role="status">
                Current telemetry is unavailable or out of date. Recorded
                findings do not establish active work.
              </p>
            )}
            {runsForAgent.map((run) => {
              const a = run.agents.find((a) => a.id === current.id) || current;
              return (
                <section key={run.run_id}>
                  <h3>
                    {run.case_id} ·{" "}
                    {run.status === "running" ? "Active" : "Recorded"}
                  </h3>

                  {!a.tasks.length && (
                    <p>
                      {a.state === "unknown"
                        ? "Invocation details are unavailable for this read."
                        : "No invocation recorded for this agent in the selected run."}
                    </p>
                  )}
                  {a.tasks.map((task, i) => (
                    <article
                      key={task.invocation_id || i}
                      className="aw-finding"
                    >
                      <p>
                        <strong>{task.label}</strong>
                      </p>
                      <span className="tr-label">What was found</span>
                      <FindingSummary
                        summary={task.finding}
                        runId={run.run_id}
                        role={current.id}
                        status={task.state}
                        handoff={host?.data?.standard?.handoffs.find(
                          (h) => h.run_id === run.run_id,
                        )}
                      />
                      {task.invocation_id && (
                        <details className="tr-details">
                          <summary>Task reference</summary>
                          <p>{task.invocation_id}</p>
                        </details>
                      )}
                      {task.error && <p className="cp-error">{task.error}</p>}
                      {task.dependencies.length > 0 && (
                        <>
                          <h4>Next dependency</h4>
                          <ul>
                            {task.dependencies.map((d, j) => (
                              <li key={j}>{d}</li>
                            ))}
                          </ul>
                        </>
                      )}
                      {task.evidence.length > 0 && (
                        <>
                          <h4>Sources consulted</h4>
                          <SourceReferenceList
                            refs={task.evidence}
                            href={() =>
                              run.links[0]
                                ? run.links[0].href + "?tab=evidence"
                                : undefined
                            }
                          />
                        </>
                      )}
                    </article>
                  ))}
                  {run.handoff && (
                    <p>
                      <Pause size={16} /> {run.handoff.label}
                    </p>
                  )}
                </section>
              );
            })}
            {!runsForAgent.length && (
              <p>
                {data && !uncertain
                  ? "No active task is recorded in this scope."
                  : "No task or finding can be established from this read."}
              </p>
            )}
          </div>
        </Dialog>
      )}
      {showHealth && (
        <Dialog
          title="Workspace telemetry"
          close={() => setShowHealth(false)}
          closeLabel="Close telemetry details"
          note="Read-only observations · No model health probe"
          footer={
            host?.capabilities?.surfaces.includes("operations") && (
              <Link to="/control/operations">Open Operations</Link>
            )
          }
        >
          <Facts
            rows={[
              [
                "Host",
                view.error
                  ? "Unavailable"
                  : data
                    ? "Available at " + date(data.read_at, true)
                    : "Not checked",
              ],
              ["Model", data?.model_state || "Not checked"],
              [
                "Last completed model run",
                data?.last_completed_model_run_at
                  ? date(data.last_completed_model_run_at, true)
                  : "Not recorded",
              ],
              [
                "Source checks",
                data?.fresh_source_count == null
                  ? "Not checked"
                  : `${data.fresh_source_count}/5 fresh successful checks`,
              ],
              ["Scope", host?.capabilities?.program_id || "Unavailable"],
              [
                "Recorded runs",
                data
                  ? `${data.total_permitted_runs}; showing ${data.runs.length} recent or active runs`
                  : "Unknown",
              ],
            ]}
          />
          <p>
            Run completion and configured runtime do not prove current model
            connectivity. Agent rings indicate categories, never percent
            complete.
          </p>
          <Facts
            rows={(data?.sources || []).map((s) => [
              s.system || "Source",
              `${s.status} · ${s.checked_at ? date(s.checked_at, true) : "Not checked"}`,
            ])}
          />
        </Dialog>
      )}
    </section>
  );
}
