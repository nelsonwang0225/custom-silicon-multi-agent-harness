import { ActionAccess } from "./persona";
import { agentName, traceStatus } from "./trace-language";
import { deliveryCasePath } from "./delivery-case";
import { qualityCasePath } from "./quality-case";
import { standardCasePath } from "./standard-case";
import { useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Link } from "./access";
import {
  ArrowRight,
  Play,
  Plus,
  Workflow,
  Database,
  Users,
} from "lucide-react";
import "./rethink-utilities.css";
import { catalog } from "./catalog";
import { date, words } from "./data";
import { connectedCasePath, type HostSchema, useHost } from "./host";
import { Crumbs, Empty, Facts, Heading, Section, StatusText } from "./ui";
import { HostReadState } from "./decisions";
import { AutomationEditor, AutomationPage } from "./automation-editor";
export { AutomationPage };
export type WorkflowDefinition = HostSchema["CatalogWorkflow"];
export type Automation = HostSchema["AutomationView"];
export const workflowPath = (id: string) =>
  `/control/workflows/${encodeURIComponent(id)}`;
export const runPath = (id: string) =>
  `/control/runs/${encodeURIComponent(id)}`;
export const automationPath = (id: string) =>
  `/control/automations/${encodeURIComponent(id)}`;
export const authorityName = (a: string) =>
  ({
    read_only: "Read only",
    proposal_only: "Proposal only",
    bounded_execution: "Bounded execution",
  })[a] || a;
export const runMode = (r: HostSchema["RunView"]) =>
  r.execution_mode === "deterministic_test"
    ? "Connected · Deterministic test double"
    : "Connected · Recorded model run";
export const roleName = (r: string) =>
  ({
    change_impact: "Change impact",
    validation_evidence: "Validation & evidence",
    manufacturing: "Manufacturing",
    program_commercial: "Program & commercial",
  })[r] || words(r);

export function AutomationList({ workflowId }: { workflowId?: string }) {
  const host = useHost();
  const items =
    host?.data?.automations?.filter(
      (a) => !workflowId || a.workflow_id === workflowId,
    ) || [];
  return (
    <Section
      title="Automation configurations"
      note="Saved configuration only. Schedule, event and condition runners are inactive."
    >
      {!items.length ? (
        <Empty>
          {host?.data
            ? "No saved configurations for this workflow."
            : "Connect the control host to read saved configurations."}
        </Empty>
      ) : (
        <div className="cp-automation-list">
          {items.map((a) => (
            <Link
              key={a.automation_id}
              to={automationPath(a.automation_id)}
              className="cp-automation-row"
            >
              <div>
                <strong>{a.name}</strong>
                <small>
                  {a.workflow_name} · {a.program_id}
                  {a.case_scope ? ` / ${a.case_scope}` : ""}
                </small>
                <span>{a.trigger_summary}</span>
              </div>
              <div>
                <StatusText>
                  {a.configuration_state === "paused" ? "Paused" : "Configured"}{" "}
                  · Preview
                </StatusText>
                <small>
                  {authorityName(a.authority)}
                  {a.workflow_mode === "Preview" ? " · Planned authority" : ""}
                </small>
                <small>
                  {a.workflow_mode} workflow ·{" "}
                  {a.trigger.type === "source_event"
                    ? "Trigger listener not active"
                    : a.trigger.type === "schedule"
                      ? "Schedule configured · runner inactive"
                      : "Runner inactive"}{" "}
                </small>
              </div>
              <ArrowRight size={17} />
            </Link>
          ))}
        </div>
      )}
    </Section>
  );
}

export function RunHistory({ workflowId }: { workflowId?: string }) {
  const host = useHost();
  const runs = [
    ...(host?.data?.runs || []),
    ...(host?.data?.standard?.runs || []),
    ...(host?.data?.quality?.runs || []),
    ...(host?.data?.autonomous_quality?.runs || []),
    ...(host?.data?.delivery?.runs || []),
  ]
    .filter(
      (r) =>
        !workflowId ||
        (workflowId === "standard_change"
          ? r.change_id === "CR-019"
          : r.workflow_id === workflowId),
    )
    .sort((a, b) => b.started_at.localeCompare(a.started_at));
  return (
    <Section
      title="Run history"
      note="Actual persisted runs. Runtime completion and business outcome are shown separately."
    >
      {!runs.length ? (
        <Empty>
          {host?.data
            ? "No recorded runs in this scope."
            : "Run history unavailable until the host is connected."}
        </Empty>
      ) : (
        <div
          className="cp-workflow-table"
          tabIndex={0}
          role="region"
          aria-label="Run history table"
        >
          <table>
            <thead>
              <tr>
                <th>Run / scope</th>
                <th>Initiated</th>
                <th>Runtime</th>
                <th>Business outcome</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run_id}>
                  <td>
                    <Link to={runPath(r.run_id)}>
                      {r.change_id} · Investigation
                    </Link>
                    <small>
                      {catalog.find((w) => w.workflow_id === r.workflow_id)
                        ?.name || words(r.workflow_id)}
                    </small>
                    <small>
                      {r.program_id} · {r.change_id || "CR-017"}
                    </small>
                    <small>
                      {traceStatus(
                        r.policy_route || "material_change_human_review",
                      )}
                    </small>
                  </td>
                  <td>
                    {date(r.started_at, true)}
                    <small>
                      {r.trigger.kind === "source_event"
                        ? "Manufacturing source event"
                        : agentName(r.actor_id)}{" "}
                      · {words(r.trigger.kind)}
                      {r.trigger.kind === "source_event" && (
                        <small>
                          {r.trigger.event_name} · {r.trigger.source_reference}{" "}
                          · v{r.trigger.event_version}
                        </small>
                      )}
                    </small>
                  </td>
                  <td>
                    {traceStatus(r.status)}
                    <small>{runMode(r)}</small>
                    <small>
                      {r.completed_at
                        ? `Finished ${date(r.completed_at, true)}`
                        : "Completion not recorded"}
                    </small>
                  </td>
                  <td>
                    <strong>{traceStatus(r.business_outcome)}</strong>
                    <small>
                      {r.change_id === "CR-019"
                        ? "No human approval · Bounded pre-authorized handoff"
                        : "Customer acceptance remains separate"}
                    </small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Section>
  );
}

function ManualLaunch({ item }: { item: WorkflowDefinition }) {
  const host = useHost(),
    navigate = useNavigate();
  const [error, setError] = useState("");
  const lock = useRef(false);
  const [program, setProgram] = useState("PRG-A17"),
    [change, setChange] = useState(item.cases?.[0] || "CR-017");
  const running = [
    ...(host?.data?.runs || []),
    ...(host?.data?.standard?.runs || []),
    ...(host?.data?.quality?.runs || []),
    ...(host?.data?.autonomous_quality?.runs || []),
    ...(host?.data?.delivery?.runs || []),
  ].find((r) => r.status === "running" && r.change_id === change);
  const allowed =
    item.manual_available &&
    !!host?.data?.source_available &&
    !host.error &&
    !host.busy &&
    !!host.capabilities?.automation_save;
  const start = async () => {
    if (!host || !allowed || lock.current) return;
    lock.current = true;
    setError("");
    const key = `stratos.workflow-invocation.${host.profile}.${item.workflow_id}.${change}`;
    // Retry metadata only; an interrupted reply retains the exact invocation across reloads.
    let invocation = sessionStorage.getItem(key);
    if (!invocation) {
      invocation = `ui_${crypto.randomUUID().replaceAll("-", "")}`;
      sessionStorage.setItem(key, invocation);
    }
    try {
      const result = await host.act<HostSchema["StartResponse"]>(
        `/workflows/${item.workflow_id}/runs`,
        {
          invocation_id: invocation,
          workflow_id: item.invocation_workflow_id || item.workflow_id,
          definition_version: item.definition_version,
          operation: "analyze",
          customer_id: "CUST-FML01",
          program_id: program,
          change_id: change,
        },
      );
      sessionStorage.removeItem(key);
      navigate(runPath(result.run_id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
    }
  };
  return (
    <Section
      title="Manual invocation"
      note={
        item.manual_available
          ? item.workflow_id === "delivery_readiness"
            ? "DR-009 reconciles technical readiness and source supply before exact human commitment review."
            : item.workflow_id === "yield_exception_recovery"
              ? "QE-004 validates the signal, routes a standard investigation and retains exact human recovery review."
              : "CR-019 can complete the policy-authorized standard intake. CR-017 uses exact human review before governed execution."
          : "This workflow is not connected yet."
      }
    >
      {item.manual_available && (
        <>
          <div className="cp-form-grid">
            <label>
              Program
              <select
                aria-label="Program"
                value={program}
                onChange={(e) => setProgram(e.target.value)}
              >
                <option value="PRG-A17">
                  Helios Atlas Inference · PRG-A17
                </option>
              </select>
            </label>
            <label>
              Existing case
              <select
                aria-label="Existing case"
                value={change}
                onChange={(e) => setChange(e.target.value)}
              >
                {(item.cases || []).map((id) => (
                  <option key={id} value={id}>
                    {id} ·{" "}
                    {id === "DR-009"
                      ? "Delivery readiness"
                      : id === "QE-004"
                        ? "Yield / quality exception"
                        : id === "CR-019"
                          ? "Standard approved-profile package"
                          : "Material requirement change"}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p className="cp-caption">
            {host?.data?.mode === "deterministic_test"
              ? "Deterministic test double · No paid model"
              : "Explicit launch uses the configured model runtime"}{" "}
            · Program operator or Engineering approver demo profile required.
          </p>
        </>
      )}
      <ActionAccess
        caseId={change}
        action="investigate"
        ready={allowed && !running}
        reason={
          running
            ? "An investigation is already running. Open its recorded activity."
            : !item.manual_available
              ? "This workflow is a preview. Manual execution is not connected."
              : "Choose an available scope with current source records."
        }
      />
      <div className="cp-inline">
        <button
          className="cp-primary"
          disabled={!allowed || !!running}
          onClick={() => void start()}
        >
          <Play size={15} /> Run workflow
        </button>
        {running && (
          <Link to={runPath(running.run_id)}>
            Open running investigation <ArrowRight size={15} />
          </Link>
        )}
        {item.manual_available && (
          <Link
            to={
              change === "DR-009"
                ? deliveryCasePath
                : change === "QE-004"
                  ? qualityCasePath
                  : change === "CR-019"
                    ? standardCasePath
                    : connectedCasePath
            }
          >
            Open {change} workbench <ArrowRight size={15} />
          </Link>
        )}
      </div>
      {error && (
        <p className="cp-error" role="alert">
          {error} Retry retains the same invocation.
        </p>
      )}
    </Section>
  );
}

export function Workflows() {
  const { workflowId } = useParams(),
    host = useHost();
  const [params, setParams] = useSearchParams();
  const [programFilter, setProgramFilter] = useState("");
  const [modeFilter, setModeFilter] = useState("");
  const definitions = host?.data?.workflows || catalog;
  const filteredDefinitions = definitions.filter(
    (definition) =>
      (!programFilter || definition.programs?.includes(programFilter)) &&
      (!modeFilter || definition.mode === modeFilter),
  );
  const item = definitions.find((w) => w.workflow_id === workflowId);
  const canEdit =
    !!host?.data && !host.error && !!host.capabilities?.automation_save;
  const create = () =>
    setParams({ new: "1", ...(workflowId ? { workflow: workflowId } : {}) });
  const decisionBoundary = (workflow: WorkflowDefinition) =>
    ({
      requirement_change_analysis: "Engineering review or approved policy",
      yield_exception_recovery: "Program Owner or standard routing",
      delivery_readiness: "Exact Program Owner approval",
      standard_change: "Approved scope policy",
    })[workflow.workflow_id] || workflow.approvals;
  const workflowCard = (workflow: WorkflowDefinition) => (
    <article className="rt-workflow-card" key={workflow.workflow_id}>
      <div className="rt-workflow-card-head">
        <span className="rt-utility-icon">
          <Workflow size={22} aria-hidden="true" />
        </span>
        <StatusText tone={workflow.mode === "Connected" ? "agent" : "neutral"}>
          {workflow.mode}
        </StatusText>
        <small>
          {(workflow.cases || []).join(" · ") ||
            workflow.story ||
            "Future capability"}
        </small>
      </div>
      <h3>
        <Link to={workflowPath(workflow.workflow_id)}>{workflow.name}</Link>
      </h3>
      <p>{workflow.purpose}</p>
      <div className="rt-workflow-route">
        <div>
          <small>Start</small>
          <strong>
            {workflow.manual_available
              ? "Manual investigation"
              : "Configuration only"}
          </strong>
          {workflow.source_event_scope && (
            <span>
              {workflow.workflow_id === "yield_exception_recovery"
                ? "Bounded QE-011 source event"
                : workflow.source_event_scope}
            </span>
          )}
        </div>
        <ArrowRight size={18} aria-hidden="true" />
        <div>
          <small>Decision boundary</small>
          <strong>{decisionBoundary(workflow)}</strong>
        </div>
      </div>
      <div className="rt-workflow-support">
        <Database size={16} aria-hidden="true" />
        <span>
          {(workflow.source_systems || []).join(" · ") ||
            "No sources connected"}
        </span>
      </div>
      <details className="rt-inline-details">
        <summary>Agent team, scope and authority</summary>
        <p>{workflow.approvals}</p>
        {workflow.source_event_scope && <p>{workflow.source_event_scope}</p>}
        <p>
          {(workflow.specialists || []).map(roleName).join(" · ") ||
            "Specialists not configured"}
        </p>
        <p>
          {(workflow.programs || []).join(" · ") ||
            "Program scope not configured"}
        </p>
        <p>{workflow.limits}</p>
      </details>
      <div className="rt-card-actions">
        <Link className="cp-text-link" to={workflowPath(workflow.workflow_id)}>
          Open workflow <ArrowRight size={16} />
        </Link>
        {workflow.latest_run_id && (
          <Link to={runPath(workflow.latest_run_id)}>Latest run</Link>
        )}
      </div>
    </article>
  );
  if (workflowId && !item)
    return (
      <Empty>
        Unknown workflow. <Link to="/control/workflows">Browse workflows</Link>
      </Empty>
    );
  return (
    <div className="rt-utilities rt-workflows">
      {item && (
        <Crumbs
          items={[
            { label: "Workflows & Automations", to: "/control/workflows" },
            { label: item.name },
          ]}
        />
      )}
      <Heading
        eyebrow={item?.story || "Capabilities & triggers"}
        title={item?.name || "Workflows & Automations"}
        description={
          item?.purpose ||
          "See how each workflow starts, what the agents do and where a decision is required."
        }
        action={
          <button onClick={create} disabled={!canEdit}>
            <Plus size={17} /> New automation
          </button>
        }
      />
      <HostReadState />
      <ActionAccess
        caseId="CR-017"
        action="prepare"
        ready={canEdit}
        reason="A current host connection is required to save configuration metadata."
      />
      {item ? (
        <>
          <Section
            title="What this workflow does"
            className="rt-workflow-overview"
            action={
              <StatusText
                tone={item.mode === "Connected" ? "agent" : "neutral"}
              >
                {item.mode}
              </StatusText>
            }
          >
            <ol
              className="rt-mini-flow rt-workflow-flow"
              aria-label="Workflow stages"
            >
              <li>
                <Database size={17} aria-hidden="true" /> Read scoped sources
              </li>
              <li>
                <Workflow size={17} aria-hidden="true" /> Specialist assessment
              </li>
              <li>
                <Users size={17} aria-hidden="true" />{" "}
                {item.mode === "Connected"
                  ? "Policy or exact decision"
                  : "Planned authority"}
              </li>
            </ol>
            <Facts
              rows={[
                [
                  "Supported scope",
                  `${(item.programs || []).join(", ")}${(item.cases || []).length ? ` · ${(item.cases || []).join(", ")}` : " · Illustrative program scope"}`,
                ],
                [
                  item.mode === "Connected"
                    ? "Participating specialists"
                    : "Planned specialists",
                  (item.specialists || []).map(roleName).join(" · ") ||
                    "Not configured",
                ],
                [
                  item.mode === "Connected"
                    ? "Allowed source systems"
                    : "Planned source systems",
                  (item.source_systems || []).join(" · ") || "None connected",
                ],
                [
                  "Current authority",
                  item.mode === "Connected"
                    ? item.connected_route
                      ? "Bounded pre-authorized intake handoff"
                      : "Shared investigation · Standard intake or exact human review"
                    : "Configuration only",
                ],
                ["Approvals", item.approvals],
              ]}
            />
            <details>
              <summary>Inputs, outputs & boundaries</summary>
              <div className="cp-context-grid cp-three">
                {[
                  ["Inputs", item.inputs],
                  ["Outputs", item.outputs],
                  ["Allowed actions", item.actions],
                ].map(([title, values]) => (
                  <article key={title as string}>
                    <h3>{title}</h3>
                    <ul>
                      {(values as string[]).map((v) => (
                        <li key={v}>{words(v)}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
              <p>{item.limits}</p>
            </details>
          </Section>
          <ManualLaunch key={item.workflow_id} item={item} />
          <Section title="Initiation methods">
            <div className="cp-trigger-methods">
              {["Manual", "Scheduled", "Source event", "Condition", "Chat"].map(
                (t) => (
                  <div key={t}>
                    <strong>{t}</strong>
                    <small>
                      {t === "Manual" && item.manual_available
                        ? "Connected · Explicit launch"
                        : t === "Source event"
                          ? item.source_event_scope ||
                            "Preview · Listener not active"
                          : t === "Condition"
                            ? "Preview · No evaluator"
                            : t === "Chat"
                              ? item.manual_available
                                ? "Connected · Explicit Concierge request"
                                : "Preview · Workflow not connected"
                              : "Preview · No background execution"}
                    </small>
                  </div>
                ),
              )}
            </div>
          </Section>
        </>
      ) : (
        <>
          <div className="rt-filter-bar">
            <label className="rt-filter">
              <span>Program</span>
              <select
                value={programFilter}
                onChange={(event) => setProgramFilter(event.target.value)}
              >
                <option value="">All programs</option>
                {[
                  ...new Set(
                    definitions.flatMap((workflow) => workflow.programs || []),
                  ),
                ]
                  .sort()
                  .map((id) => (
                    <option key={id} value={id}>
                      {id}
                    </option>
                  ))}
              </select>
            </label>
            <label className="rt-filter">
              <span>Connection status</span>
              <select
                value={modeFilter}
                onChange={(event) => setModeFilter(event.target.value)}
              >
                <option value="">All statuses</option>
                {[...new Set(definitions.map((workflow) => workflow.mode))].map(
                  (mode) => (
                    <option key={mode} value={mode}>
                      {mode}
                    </option>
                  ),
                )}
              </select>
            </label>
            <span className="rt-result-count">
              {filteredDefinitions.length} workflows
            </span>
          </div>
          <Section
            title="Workflow catalog"
            note="Connected capabilities come from the installed registry. Saved triggers retain their own activation state."
            className="rt-workflow-catalog-section"
          >
            <div className="rt-workflow-catalog">
              {filteredDefinitions
                .filter((workflow) => workflow.mode !== "Preview")
                .map(workflowCard)}
            </div>
            {filteredDefinitions.some(
              (workflow) => workflow.mode === "Preview",
            ) && (
              <details
                className="rt-disclosure rt-future-workflows"
                key={modeFilter}
                open={modeFilter === "Preview"}
              >
                <summary>
                  Future workflow concepts{" "}
                  <span>
                    {
                      filteredDefinitions.filter(
                        (workflow) => workflow.mode === "Preview",
                      ).length
                    }{" "}
                    · Configuration only
                  </span>
                </summary>
                <p>
                  Explore planned capabilities. These concepts do not run
                  investigations or take source actions.
                </p>
                <div className="rt-workflow-catalog">
                  {filteredDefinitions
                    .filter((workflow) => workflow.mode === "Preview")
                    .map(workflowCard)}
                </div>
              </details>
            )}
            {!filteredDefinitions.length && (
              <Empty>No workflows match these filters.</Empty>
            )}
          </Section>
        </>
      )}
      <AutomationList workflowId={workflowId} />
      <RunHistory workflowId={workflowId} />
      {params.get("new") === "1" && (
        <AutomationEditor
          workflowId={params.get("workflow") || workflowId}
          close={() => setParams({})}
        />
      )}
    </div>
  );
}
