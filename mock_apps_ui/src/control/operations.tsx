import { KnowledgeRunEvidence } from "./knowledge-runs";
import {
  RecordedText,
  SourceReferenceList,
  FindingSummary,
} from "./traceability";
import {
  agentName,
  operationLabel,
  traceStatus,
  eventLabel,
  actionExplanation,
  failureLabel,
  evalCaseLabel,
  consultedSources,
  gateLabel,
} from "./trace-language";
import { DemoEntry } from "./demo-controls";
import { HandoffDetails } from "./standard-case";
import { useCallback, useEffect, useState } from "react";
import {
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { Link } from "./access";
import {
  ArrowRight,
  RefreshCw,
  Activity,
  ShieldCheck,
  Database,
  AlertCircle,
} from "lucide-react";
import "./rethink-utilities.css";
import { useHost, type HostSchema } from "./host";
import { date, words } from "./data";
import { Empty, Facts, Heading, Section, Crumbs } from "./ui";
import { useOperations } from "./operations-data";

type Index = HostSchema["OpsIndex"];
type Run = HostSchema["OpsRun"];
const runPath = (id: string) => "/control/runs/" + encodeURIComponent(id);
const roles: Record<string, string> = {
  coordinator: "Program Coordinator",
  change_impact: "Change Impact",
  validation_evidence: "Validation & Evidence",
  program_commercial: "Program & Commercial",
  manufacturing: "Manufacturing",
};
const elapsed = (ms: number | null | undefined) =>
  ms == null
    ? "Unavailable"
    : ms < 1000
      ? `${Math.round(ms)} ms`
      : ms < 60000
        ? `${(ms / 1000).toFixed(1)} s`
        : `${(ms / 60000).toFixed(1)} min`;
const count = (n: number | null | undefined) =>
  n == null ? "Unavailable" : n.toLocaleString();

function RunTable({ runs }: { runs: Run[] }) {
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState(""),
    [program, setProgram] = useState(""),
    [caseId, setCase] = useState(""),
    [state, setState] = useState(""),
    [from, setFrom] = useState(""),
    [to, setTo] = useState("");
  const filtered = runs.filter(
    (r) =>
      (!workflow || r.workflow_id === workflow) &&
      (!program || r.program_id === program) &&
      (!caseId || r.case_id === caseId) &&
      (!state || r.runtime_state === state) &&
      (!from || r.started_at.slice(0, 10) >= from) &&
      (!to || r.started_at.slice(0, 10) <= to),
  );
  return (
    <>
      <div className="cp-ops-filters">
        {(
          [
            ["Workflow", workflow, setWorkflow, runs.map((r) => r.workflow_id)],
            ["Program", program, setProgram, runs.map((r) => r.program_id)],
            ["Case", caseId, setCase, runs.map((r) => r.case_id)],
            [
              "Runtime state",
              state,
              setState,
              runs.map((r) => r.runtime_state),
            ],
          ] as const
        ).map(([title, value, update, values]) => (
          <label key={title}>
            {title}
            <select
              aria-label={title}
              value={value}
              onChange={(e) => update(e.target.value)}
            >
              <option value="">
                {title === "Program"
                  ? "All programs"
                  : title === "Runtime state"
                    ? "All statuses"
                    : `All ${String(title).toLowerCase()}s`}
              </option>
              {[...new Set(values)].map((v) => (
                <option key={v} value={v}>
                  {title === "Runtime state"
                    ? traceStatus(v)
                    : title === "Workflow"
                      ? words(v)
                      : v}
                </option>
              ))}
            </select>
          </label>
        ))}
        <label>
          From
          <input
            aria-label="From date"
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
        <label>
          Through
          <input
            aria-label="Through date"
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />
        </label>
      </div>
      {!filtered.length ? (
        <Empty>No runs match these filters.</Empty>
      ) : (
        <div
          className="cp-table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Run history"
        >
          <table className="cp-ops-table rt-run-table">
            <thead>
              <tr>
                <th>Case / workflow</th>
                <th>Business outcome</th>
                <th>Decision / source confirmation</th>
                <th>Investigation / timing</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((run) => (
                <tr
                  key={run.run_id}
                  tabIndex={0}
                  aria-label={`${run.case_id} · ${run.business_outcome}`}
                  onClick={(event) => {
                    if (
                      !(event.target as HTMLElement).closest(
                        "a, button, summary, details, select, input",
                      )
                    )
                      navigate(runPath(run.run_id));
                  }}
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" &&
                      event.target === event.currentTarget
                    )
                      navigate(runPath(run.run_id));
                  }}
                >
                  <td>
                    <Link to={runPath(run.run_id)}>
                      {run.case_id}{" "}
                      <span className="cp-text-link">View run →</span>
                    </Link>
                    <small>{words(run.workflow_id)}</small>
                    <small>{run.program_id}</small>
                  </td>
                  <td>
                    <strong>{run.business_outcome}</strong>
                    <small>
                      Current case: {run.current_case_label || "Unavailable"}
                    </small>
                  </td>
                  <td>
                    <strong>{run.decision_state}</strong>
                    <small>Source: {traceStatus(run.verification_state)}</small>
                    <small>
                      {run.source_checked_at
                        ? `Checked ${date(run.source_checked_at, true)}`
                        : "Current read unavailable"}
                    </small>
                  </td>
                  <td>
                    <span
                      className="rt-runtime-state"
                      data-state={run.runtime_state}
                    >
                      {traceStatus(run.runtime_state)}
                    </span>
                    <small>{date(run.started_at, true)}</small>
                    <small>{elapsed(run.duration_ms)}</small>
                  </td>
                  <td>
                    <details className="rt-run-metadata">
                      <summary>Run details</summary>
                      <dl>
                        <dt>Origin</dt>
                        <dd>{run.invocation_source}</dd>
                        <dt>Started by</dt>
                        <dd>{agentName(run.actor)}</dd>
                        <dt>Model</dt>
                        <dd>{run.model || "Unavailable"}</dd>
                        <dt>Mode</dt>
                        <dd>{words(run.execution_mode)}</dd>
                        <dt>Run ID</dt>
                        <dd>{run.run_id}</dd>
                      </dl>
                      {(run.session_ids || []).map((id) => (
                        <Link
                          key={id}
                          to={`/control/operations/sessions/${id}`}
                        >
                          Concierge session
                        </Link>
                      ))}
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function Evals({ data }: { data: Index }) {
  const [params] = useSearchParams();
  const selected = params.get("eval");
  const offline = data.evals
    .filter((e) => e.mode === "offline")
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  const latest = offline[0];
  return (
    <>
      <Section
        title="Latest automated checks"
        note="These checks use scripted inputs to test workflow rules and recovery. They do not measure a live model's reasoning."
      >
        {latest ? (
          <p>
            <strong>
              {latest.passed} of {latest.total} checks passed ·{" "}
              {gateLabel(latest.hard_gate)}
            </strong>{" "}
            · {latest.critical_failures.length} critical failures ·{" "}
            {date(latest.timestamp, true)}
          </p>
        ) : (
          <Empty>No indexed offline result available.</Empty>
        )}
      </Section>
      {(["live", "offline"] as const).map((mode) => (
        <Section
          title={
            mode === "live"
              ? "Live evaluation history"
              : "Offline evaluation history"
          }
          key={mode}
          note={
            mode === "live"
              ? "Tests that used the model. A later successful retest covers only its listed cases; earlier failures remain part of the history."
              : undefined
          }
        >
          {!data.evals.some((e) => e.mode === mode) && (
            <Empty>No {mode} evaluation recorded.</Empty>
          )}
          {data.evals
            .filter((e) => e.mode === mode)
            .map((e) => (
              <article
                className="cp-record"
                key={e.eval_id}
                id={"eval-" + e.eval_id}
              >
                <h3>{e.label}</h3>
                <p>
                  <strong>
                    {e.passed} of {e.total} checks passed ·{" "}
                    {gateLabel(e.hard_gate)}
                  </strong>{" "}
                  · {e.failed} failed · {e.critical_failures.length} critical
                  failures
                </p>
                <small>
                  {date(e.timestamp, true)} · {e.model || "Model unavailable"} ·
                  Answer quality review: {e.semantic}
                </small>
                <details open={selected === e.eval_id || undefined}>
                  <summary>What was tested and what failed</summary>
                  <div className="cp-table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Case</th>
                          <th>Result</th>
                          <th>Critical failures</th>
                          <th>Answer quality review</th>
                        </tr>
                      </thead>
                      <tbody>
                        {e.cases.map((c) => (
                          <tr key={c.case_id}>
                            <td>
                              {evalCaseLabel(c.case_id)}
                              <details className="tr-details">
                                <summary>Test reference</summary>
                                {c.case_id}
                              </details>
                            </td>
                            <td>{c.passed ? "Passed" : "Failed"}</td>
                            <td>
                              {c.critical_failures.length ? (
                                <ul className="tr-bullets">
                                  {c.critical_failures.map((f) => (
                                    <li key={f}>
                                      {failureLabel(f)}
                                      <details className="tr-details">
                                        <summary>Check reference</summary>
                                        {f}
                                      </details>
                                    </li>
                                  ))}
                                </ul>
                              ) : c.passed ? (
                                "None recorded"
                              ) : (
                                "A check failed; no critical failure reason was retained here."
                              )}
                            </td>
                            <td>{c.semantic}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              </article>
            ))}
        </Section>
      ))}
      {!!data.unavailable_artifacts.length && (
        <details className="cp-secondary-content">
          <summary>
            Unavailable indexed results ({data.unavailable_artifacts.length})
          </summary>
          <p>{data.unavailable_artifacts.join(" · ")}</p>
        </details>
      )}
    </>
  );
}

export function Operations() {
  const ops = useOperations(),
    host = useHost(),
    location = useLocation();
  const [checking, setChecking] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState("");
  const selectedRun =
    ops.data?.runs.find((run) => run.run_id === selectedRunId) ||
    [...(ops.data?.runs || [])].sort((a, b) =>
      b.started_at.localeCompare(a.started_at),
    )[0];
  const evalView = location.pathname.endsWith("/evals");
  const read = host?.read;
  const running = ops.data?.runs.some((r) => r.runtime_state === "running");
  useEffect(() => {
    if (!running || !read) return;
    let alive = true;
    const timer = setInterval(() => {
      void read<Run[]>("/operations/runs")
        .then((runs) => {
          if (alive)
            ops.setData((d) =>
              d
                ? {
                    ...d,
                    runs: runs.map((r) => {
                      const old = d.runs.find((v) => v.run_id === r.run_id);
                      return old &&
                        old.runtime_state === r.runtime_state &&
                        old.decision_state === r.decision_state &&
                        old.verification_state === r.verification_state
                        ? {
                            ...r,
                            business_outcome: old.business_outcome,
                            current_case_state: old.current_case_state,
                            current_case_label: old.current_case_label,
                            source_checked_at: old.source_checked_at,
                            attention: old.attention,
                          }
                        : r;
                    }),
                  }
                : d,
            );
        })
        .catch(() => {});
    }, 1500);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [running, read, ops.setData]);
  const check = async () => {
    if (!read) return;
    setChecking(true);
    try {
      const health = await read<Index["health"]>("/operations/health");
      ops.setData((d) => (d ? { ...d, health } : d));
    } finally {
      setChecking(false);
    }
  };
  return (
    <div className="cp-operations rt-utilities">
      <Heading
        eyebrow="Recorded activity"
        title={evalView ? "Evals & Reliability" : "Operations"}
        description="Start with the business outcome. Inspect the agents, decisions and source confirmation behind it."
        action={
          <button onClick={() => void ops.refresh()}>
            <RefreshCw size={16} /> Refresh Operations
          </button>
        }
      />
      <DemoEntry />
      <div
        role="navigation"
        className="cp-inline cp-ops-nav"
        aria-label="Operations views"
      >
        <Link to="/control/operations">Runs & system health</Link>
        <Link to="/control/operations/evals">Evals & Reliability</Link>
      </div>
      {ops.error && (
        <p role="alert" className="cp-error">
          {ops.error} · Last-read observations may be stale.
        </p>
      )}
      {!ops.data ? (
        <Empty>Reading Operations records…</Empty>
      ) : evalView ? (
        <Evals data={ops.data} />
      ) : (
        <>
          {selectedRun && (
            <Section
              title="Recorded outcome"
              className="rt-operation-outcome"
              action={
                <label className="rt-filter">
                  <span>Investigation</span>
                  <select
                    aria-label="Select recorded run"
                    value={selectedRun.run_id}
                    onChange={(event) => setSelectedRunId(event.target.value)}
                  >
                    {ops.data.runs.map((run) => (
                      <option key={run.run_id} value={run.run_id}>
                        {run.case_id} · {date(run.started_at, true)} ·{" "}
                        {traceStatus(run.runtime_state)}
                      </option>
                    ))}
                  </select>
                </label>
              }
            >
              <div className="rt-operation-summary">
                <span className="rt-utility-icon">
                  {selectedRun.attention ? (
                    <AlertCircle size={26} aria-hidden="true" />
                  ) : (
                    <Activity size={26} aria-hidden="true" />
                  )}
                </span>
                <div>
                  <small>
                    {selectedRun.case_id} · {words(selectedRun.workflow_id)}
                  </small>
                  <h3>{selectedRun.business_outcome}</h3>
                  <p>
                    Current case:{" "}
                    <strong>
                      {selectedRun.current_case_label || "Unavailable"}
                    </strong>
                    {selectedRun.source_checked_at
                      ? ` · Source checked ${date(selectedRun.source_checked_at, true)}`
                      : " · Current source check unavailable"}
                  </p>
                </div>
              </div>
              <div className="rt-outcome-stages">
                <div>
                  <Activity size={18} aria-hidden="true" />
                  <span>
                    <small>Investigation</small>
                    <strong>{traceStatus(selectedRun.runtime_state)}</strong>
                  </span>
                </div>
                <div>
                  <ShieldCheck size={18} aria-hidden="true" />
                  <span>
                    <small>Decision</small>
                    <strong>{selectedRun.decision_state}</strong>
                  </span>
                </div>
                <div>
                  <Database size={18} aria-hidden="true" />
                  <span>
                    <small>Source confirmation</small>
                    <strong>
                      {traceStatus(selectedRun.verification_state)}
                    </strong>
                  </span>
                </div>
              </div>
              <div className="rt-card-actions">
                <Link className="cp-text-link" to={runPath(selectedRun.run_id)}>
                  Inspect this run <ArrowRight size={16} />
                </Link>
                <Link to={selectedRun.case_link}>
                  Open {selectedRun.case_id}
                </Link>
              </div>
            </Section>
          )}
          <details className="rt-disclosure rt-outcomes-review">
            <summary>
              Run outcomes to review{" "}
              <span>
                {ops.data.runs.filter((run) => run.attention).length} recorded
              </span>
            </summary>
            <p>
              Recorded failures stay visible after a retry. Current case status
              is shown separately.
            </p>
            {ops.data.runs
              .filter((run) => run.attention)
              .map((run) => (
                <div className="cp-ops-attention" key={run.run_id}>
                  <Link to={runPath(run.run_id)}>
                    {run.case_id} · {run.business_outcome}
                  </Link>
                  <small>Investigation: {traceStatus(run.runtime_state)}</small>
                </div>
              ))}
            {!ops.data.runs.some((run) => run.attention) && (
              <p>No run failures or escalations recorded.</p>
            )}
          </details>
          <Section title="Run history">
            <RunTable runs={ops.data.runs} />
          </Section>
          <div className="cp-ops-health-grid">
            <Section title="Reliability">
              {ops.data.evals
                .filter((e) => e.mode === "offline")
                .slice(-1)
                .map((e) => (
                  <p key={e.eval_id}>
                    Latest automated checks:{" "}
                    <strong>
                      {e.passed} of {e.total} passed · {gateLabel(e.hard_gate)}
                    </strong>
                    <br />
                    {e.critical_failures.length} critical failures ·{" "}
                    {date(e.timestamp, true)}
                  </p>
                ))}
              <Link to="/control/operations/evals">
                Inspect offline and live history <ArrowRight size={14} />
              </Link>
            </Section>
            <Section
              title="System health"
              action={
                <button onClick={() => void check()} disabled={checking}>
                  {checking ? "Checking…" : "Check source reads"}
                </button>
              }
            >
              <p>{ops.data.runtime}</p>
              {ops.data.health.map((h) => (
                <div className="cp-ops-health" key={h.system}>
                  <strong>{h.system}</strong>
                  <span>{h.status}</span>
                  <small>
                    {h.checked_at
                      ? date(h.checked_at, true)
                      : "No check timestamp"}
                  </small>
                </div>
              ))}
              {ops.data.observability_error && (
                <p role="alert">{ops.data.observability_error}</p>
              )}
            </Section>
          </div>
          <Section
            title="Concierge sessions"
            note="Visible conversation history. A chat message is not a workflow run."
          >
            {ops.data.sessions.length ? (
              ops.data.sessions.map((s) => (
                <div className="cp-record" key={s.session_id}>
                  <Link to={"/control/operations/sessions/" + s.session_id}>
                    Conversation · {date(s.updated_at, true)}
                  </Link>
                  <small>
                    {s.turn_count} messages · {s.run_ids.length} linked
                    workflows · {date(s.updated_at, true)}
                  </small>
                </div>
              ))
            ) : (
              <Empty>No retained Concierge sessions.</Empty>
            )}
          </Section>
          <Section
            title="Automation configurations"
            note="No scheduler active. Preview triggers do not execute workflows."
          >
            {host?.data?.automations?.map((a) => (
              <div className="cp-record" key={a.automation_id}>
                <Link to={"/control/automations/" + a.automation_id}>
                  {a.name}
                </Link>
                <small>
                  {words(a.configuration_state)} · Preview trigger · No
                  scheduler active
                </small>
              </div>
            ))}
          </Section>
        </>
      )}
    </div>
  );
}

export function OperationsRun() {
  const { runId } = useParams(),
    host = useHost(),
    read = host?.read;
  const [data, setData] = useState<HostSchema["OpsRunDetail"] | null>(null),
    [error, setError] = useState("");
  const refresh = useCallback(async () => {
    if (!read || !runId) return;
    try {
      setData(
        await read<HostSchema["OpsRunDetail"]>(
          "/operations/runs/" + encodeURIComponent(runId),
        ),
      );
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [read, runId]);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  const running = data?.run.runtime_state === "running";
  useEffect(() => {
    if (!read || !running) return;
    const timer = setInterval(
      () =>
        void read<Run[]>("/operations/runs")
          .then((rows) => {
            const next = rows.find((r) => r.run_id === runId);
            if (next && next.runtime_state !== "running") void refresh();
          })
          .catch((e) => setError((e as Error).message)),
      1500,
    );
    return () => clearInterval(timer);
  }, [read, running, runId, refresh]);
  if (!data || data.run.run_id !== runId)
    return <Empty>{error || "Reading run detail…"}</Empty>;
  const r = data.run;
  const recordedRun = [
    ...(host?.data?.runs || []),
    ...(host?.data?.standard?.runs || []),
    ...(host?.data?.quality?.runs || []),
    ...(host?.data?.autonomous_quality?.runs || []),
    ...(host?.data?.delivery?.runs || []),
  ].find((run) => run.run_id === r.run_id);
  return (
    <div className="cp-operations rt-utilities">
      <Crumbs
        items={[
          { label: "Operations", to: "/control/operations" },
          { label: r.case_id + " · Workflow run" },
        ]}
      />
      <Heading
        title="Workflow run"
        description={`${r.case_id} · ${r.business_outcome}`}
        action={
          <Link className="cp-button" to={r.case_link}>
            Open {r.case_id} <ArrowRight size={16} />
          </Link>
        }
      />
      {error && <p role="alert">{error} · Last-read detail retained.</p>}
      <Section
        title={r.business_outcome}
        action={
          <button onClick={() => void refresh()}>Refresh run detail</button>
        }
        note="A record of the investigation, the actions it led to, and the source checks that confirmed those actions."
      >
        <p>{data.question || "Original question unavailable"}</p>
        <div className="tr-outcome">
          <strong>At a glance</strong>
          <ul className="tr-bullets">
            <li>
              {
                (data.agents || []).filter((a) => a.status === "completed")
                  .length
              }{" "}
              of {(data.agents || []).length} recorded agent tasks completed.
            </li>
            <li>
              {(data.calls || []).length} source reads and service calls
              recorded.
            </li>
            <li>
              {(data.actions || []).length
                ? `${data.actions!.filter((a) => a.verification.toLowerCase() === "verified").length} of ${data.actions!.length} action records confirmed in the source system.`
                : "No business action recorded."}
            </li>
          </ul>
          <a className="cp-text-link" href="#run-actions">
            Review actions and source confirmation →
          </a>
        </div>
        <details className="rt-inline-details">
          <summary>Run, decision and source details</summary>
          <Facts
            rows={[
              ["Investigation", traceStatus(r.runtime_state)],
              ["Business outcome", r.business_outcome],
              ["Workflow", words(r.workflow_id)],
              [
                "Program / case",
                <Link to={r.case_link}>
                  {r.program_id} / {r.case_id}
                </Link>,
              ],
              ["Invocation source", r.invocation_source],
              ...(r.event_id
                ? ([
                    ["Event", r.event_name || "Source event"],
                    [
                      "Event ID / version",
                      `${r.event_id} · v${r.event_version}`,
                    ],
                  ] as [string, string][])
                : []),
              ["Started by", agentName(r.actor)],
              ["Started", date(r.started_at, true)],
              [
                "Completed",
                r.completed_at ? date(r.completed_at, true) : "Not recorded",
              ],
              [
                "Approval route",
                r.policy_route ? traceStatus(r.policy_route) : "Not assessed",
              ],
              ["Human approval", r.decision_state],
              ["Source confirmation", traceStatus(r.verification_state)],
            ]}
          />
        </details>
      </Section>
      {!!(data.failure || []).length && (
        <Section title="Failure & recovery">
          <Facts rows={data.failure || []} />
        </Section>
      )}
      <Section
        id="run-actions"
        title="Actions taken and confirmed"
        note="The host carries out authorized changes. Each source system is then read again to check what was actually saved."
      >
        {(data.actions || []).map((a, i) => (
          <article className="tr-action" key={i}>
            <h3>{operationLabel(a.name)}</h3>
            <p className="tr-prose">{actionExplanation(a)}</p>
            <Facts
              rows={[
                ["Action status", traceStatus(a.status)],
                ["Source confirmation", traceStatus(a.verification)],
              ]}
            />
            <details className="tr-details">
              <summary>Compare expected and saved records</summary>
              <Facts
                rows={[
                  ["Expected", a.expected],
                  ["Found in source", a.actual],
                  ["Source record", a.source_id || "Not recorded"],
                ]}
              />
            </details>
            {a.error && <p className="cp-error">{a.error}</p>}
            <details>
              <summary>Attempts and duplicate prevention</summary>
              <p>{a.idempotency_key || "Key unavailable"}</p>
              {(a.attempts || []).length ? (
                (a.attempts || []).map(([at, status], j) => (
                  <p key={j}>
                    {date(at, true)} · {status}
                  </p>
                ))
              ) : (
                <p>
                  Attempt timestamps unavailable; retained step receipt shown
                  above.
                </p>
              )}
            </details>
          </article>
        ))}
        {!(data.actions || []).length && (
          <Empty>No business action is recorded for this investigation.</Empty>
        )}
      </Section>
      <details className="rt-disclosure">
        <summary>
          Agent team and findings{" "}
          <span>{(data.agents || []).length} recorded tasks</span>
        </summary>
        <Section
          title="What each agent did"
          note="Only tasks recorded for this investigation appear below."
        >
          <div className="cp-ops-agents">
            {(data.agents || []).map((a, i) => {
              const task = recordedRun?.specialists?.find(
                (s) => s.invocation_id === a.invocation_id,
              );
              return (
                <article
                  key={a.invocation_id || i}
                  className={i ? "cp-ops-specialist" : ""}
                >
                  <h3>{agentName(a.name)}</h3>
                  <strong>{traceStatus(a.status)}</strong>
                  <small>
                    {a.caller
                      ? "From " + (roles[a.caller] || a.caller)
                      : "Coordinator-owned run"}{" "}
                    · {elapsed(a.duration_ms)}
                  </small>
                  {task && (
                    <>
                      <span className="tr-label">Assigned task</span>
                      <RecordedText
                        text={task.task}
                        label="Full assigned task"
                      />
                    </>
                  )}
                  <span className="tr-label">What was found</span>
                  <FindingSummary
                    summary={
                      a.summary ||
                      (a.name === "Program Coordinator"
                        ? recordedRun?.recommendation?.change_summary
                        : null)
                    }
                    runId={r.run_id}
                    role={a.name}
                    status={a.status}
                    handoff={host?.data?.standard?.handoffs.find(
                      (h) => h.run_id === r.run_id,
                    )}
                  />
                  {task && (
                    <p className="cp-caption">
                      {consultedSources(task.source_references)}
                    </p>
                  )}
                  {a.error && <p>{a.error}</p>}
                </article>
              );
            })}
          </div>
          {!(data.agents || []).length && (
            <Empty>Agent participation unavailable.</Empty>
          )}
        </Section>
      </details>
      <Section
        title="What happened"
        note="Recorded events in order. Preparing or requesting an action is separate from saving and confirming it."
      >
        <ol className="cp-run-timeline">
          {(data.timeline || []).map((e, i) => (
            <li key={i}>
              <strong>{eventLabel(e.stage)}</strong>
              <small>
                {e.timestamp
                  ? date(e.timestamp, true)
                  : "Timestamp unavailable"}{" "}
                · {e.actor ? agentName(e.actor) : "Actor not recorded"}
              </small>
              {e.status && <span>{traceStatus(e.status)}</span>}
              {e.error && <span>{e.error}</span>}
            </li>
          ))}
        </ol>
      </Section>
      <details className="rt-disclosure">
        <summary>Knowledge retrieval and cited documents</summary>
        <KnowledgeRunEvidence runId={runId} detailed />
      </details>
      <details className="rt-disclosure">
        <summary>
          Source records and applicability{" "}
          <span>{(data.evidence || []).length} references</span>
        </summary>
        <Section
          id="evidence"
          title="Sources the agents consulted"
          note="Records read during this investigation. Reading a record alone does not establish that it satisfies the request."
        >
          <SourceReferenceList
            refs={(data.evidence || []).map((e) => ({
              ...e,
              tool_name: e.tool,
              record_id: e.record_id ?? null,
              content_version: e.content_version ?? null,
              record_version: e.record_version ?? null,
            }))}
            href={(r) =>
              data.evidence?.find((e) => e.source_id === r.source_id)?.link
            }
          />
          {(data.evidence || []).some(
            (e) =>
              e.applicability !==
              "Referenced in analysis; inspect source for applicability",
          ) && (
            <details className="tr-details">
              <summary>Recorded evidence applicability</summary>
              {data.evidence?.map((e) => (
                <p key={e.source_id}>
                  {e.record_id || e.source_id}: {e.applicability}
                </p>
              ))}
            </details>
          )}
          {!(data.evidence || []).length && (
            <Empty>No evidence references recorded.</Empty>
          )}
        </Section>
      </details>
      <details className="cp-secondary-content rt-disclosure">
        <summary>Source reads and service calls</summary>
        <Section title="Source reads and service calls">
          <div className="cp-table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Operation</th>
                  <th>Caller / target</th>
                  <th>Result</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {(data.calls || []).map((c, i) => (
                  <tr key={i}>
                    <td>
                      {c.link ? (
                        <Link to={c.link}>{operationLabel(c.name)}</Link>
                      ) : (
                        operationLabel(c.name)
                      )}
                      <small>{(c.identifiers || []).join(" · ")}</small>
                      <details className="tr-details">
                        <summary>Technical operation</summary>
                        {c.name}
                      </details>
                    </td>
                    <td>
                      {roles[c.caller] || c.caller}
                      <small>{c.target}</small>
                    </td>
                    <td>{traceStatus(c.status)}</td>
                    <td>{elapsed(c.duration_ms)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!(data.calls || []).length && (
            <Empty>Tool/service receipts unavailable.</Empty>
          )}
        </Section>
      </details>
      {(host?.data?.standard?.handoffs || [])
        .filter((h) => h.run_id === r.run_id)
        .map((h) => (
          <HandoffDetails key={h.run_id} handoff={h} />
        ))}
      <details className="cp-secondary-content">
        <summary>Decision & authorized manifest</summary>
        <Section title="Decision & authorized manifest">
          {(data.decision || []).length ? (
            <Facts rows={data.decision || []} />
          ) : (
            <Empty>No human proposal/decision recorded for this run.</Empty>
          )}
        </Section>
      </details>
      <Section
        title="Current business context"
        note={
          data.source_checked_at
            ? "Source read " + date(data.source_checked_at, true)
            : "Current source unavailable"
        }
      >
        <Facts
          rows={(data.facts || [])
            .filter(([label]) =>
              [
                "Current case state",
                "Current source",
                "Next step",
                "Lot",
              ].includes(label),
            )
            .map(([label, value]) => [
              label,
              label === "Current case state" ? traceStatus(value) : value,
            ])}
        />
        <details className="rt-inline-details">
          <summary>All current source facts</summary>
          <Facts
            rows={(data.facts || []).map(([label, value]) => {
              if (
                ["Observed rate bps", "Baseline rate bps"].includes(label) &&
                /^\d+$/.test(value)
              )
                return [
                  label === "Observed rate bps"
                    ? "Observed pass rate"
                    : "Comparable baseline",
                  `${Number(value) / 100}%`,
                ];
              return [
                label,
                [
                  "Current case state",
                  "Runtime",
                  "Verification",
                  "Business outcome",
                ].includes(label)
                  ? traceStatus(value)
                  : value,
              ];
            })}
          />
        </details>
        <div className="cp-inline">
          {(data.links || []).map((l, i) => (
            <Link key={i} to={l.href}>
              {l.label}
            </Link>
          ))}
        </div>
      </Section>
      <details className="cp-secondary-content">
        <summary>Technical details</summary>
        <Facts
          rows={[
            ["Trace ID", r.trace_id || "Unavailable"],
            ["Run ID", r.run_id],
            ["Model", r.model || "Unavailable"],
            ["Mode", words(r.execution_mode)],
            ["Agent execution elapsed", elapsed(r.duration_ms)],
            ["Model calls cumulative latency", elapsed(data.model_latency_ms)],
            ["Human wait", elapsed(data.human_wait_ms)],
            ["External wait", elapsed(data.external_wait_ms)],
            ["Input tokens", count(data.input_tokens)],
            ["Output tokens", count(data.output_tokens)],
            ["Total tokens", count(data.total_tokens)],
            ["Artifacts", data.artifact_state],
          ]}
        />
        <p>
          Token totals cover completed recorded generations. Concurrent model
          latencies are cumulative, not elapsed runtime. Human wait is separate.
          No cost estimate or platform trace availability is inferred.
        </p>
      </details>
    </div>
  );
}

export function OperationsSession() {
  const { sessionId } = useParams(),
    host = useHost(),
    read = host?.read;
  const [data, setData] = useState<HostSchema["ObservedSession"] | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    if (read && sessionId)
      void read<HostSchema["ObservedSession"]>(
        "/operations/sessions/" + encodeURIComponent(sessionId),
      )
        .then(setData)
        .catch((e) => setError(e.message));
  }, [read, sessionId]);
  if (!data || data.session_id !== sessionId)
    return <Empty>{error || "Reading session…"}</Empty>;
  return (
    <>
      <Crumbs
        items={[
          { label: "Operations", to: "/control/operations" },
          { label: "Concierge session" },
        ]}
      />
      <Heading
        title="Concierge session"
        description={`Conversation recorded ${date(data.created_at, true)}`}
      />
      <details className="tr-details">
        <summary>Session reference</summary>
        <p>{data.session_id}</p>
      </details>
      <p>
        Historical user-visible messages and cards. Source values may have
        changed since the conversation.
      </p>
      <Section title="Linked workflows">
        {(data.run_ids || []).map((id, i) => (
          <p key={id}>
            <Link to={runPath(id)}>Open linked investigation {i + 1}</Link>
          </p>
        ))}
        {!(data.run_ids || []).length && <p>No workflow invoked.</p>}
      </Section>
      <Section title="Visible conversation">
        {(data.turns || []).map((t) => (
          <article className="cp-record" key={t.message_id}>
            <h3>{t.user_text}</h3>
            <RecordedText text={t.text} label="Full saved reply" />
            <small>
              {t.error_code ? t.error_code + " · " : ""}
              {words(t.status)} · {date(t.timestamp, true)} ·{" "}
              <Link to={t.context}>Original context</Link>
            </small>
            {(t.cards || []).map((c, i) => (
              <div className="cp-ops-card" key={i}>
                <h4>{c.title}</h4>
                <Facts rows={c.facts || []} />
                {(c.links || []).map(([name, path], j) => (
                  <p key={j}>
                    <Link to={path}>{name}</Link>
                  </p>
                ))}
              </div>
            ))}
            <details>
              <summary>Model & service metadata</summary>
              <Facts
                rows={[
                  ["Model", t.model || "Unavailable"],
                  ["Latency", elapsed(t.latency_ms)],
                  ["Input tokens", count(t.input_tokens)],
                  ["Output tokens", count(t.output_tokens)],
                  ["Model calls", count(t.model_calls)],
                  [
                    "Services",
                    (t.service_calls || []).join(" · ") || "Not recorded",
                  ],
                ]}
              />
            </details>
          </article>
        ))}
      </Section>
      <Section title="Structured confirmations">
        {(data.confirmations || []).map((c, i) => (
          <div className="cp-record" key={i}>
            <strong>
              {words(c.operation)} · {words(c.status)}
            </strong>
            <small>
              {c.actor_id} · {date(c.timestamp, true)}
            </small>
            {c.plan_id && <p>Exact proposal: {c.plan_id}</p>}
            {c.automation_id && (
              <Link to={"/control/automations/" + c.automation_id}>
                Open saved configuration
              </Link>
            )}
          </div>
        ))}
        {!(data.confirmations || []).length && (
          <p>No structured actions confirmed.</p>
        )}
      </Section>
    </>
  );
}
