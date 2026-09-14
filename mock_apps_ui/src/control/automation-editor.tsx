import { useId, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Link } from "./access";
import { catalog } from "./catalog";
import { Dialog } from "./dialog";
import {
  Crumbs,
  Empty,
  Facts,
  Heading,
  Notice,
  Section,
  StatusText,
} from "./ui";
import { type HostSchema, useHost } from "./host";
import { date, words } from "./data";
import {
  authorityName,
  automationPath,
  workflowPath,
  type Automation,
} from "./workflows";
import { HostReadState } from "./decisions";
type Config = HostSchema["AutomationInput"];
type Trigger = Config["trigger"];
const events: Record<string, string[]> = {
  engineering: ["requirement_changed", "engineering_decision_updated"],
  validation: ["result_received", "job_status_changed"],
  manufacturing: ["quality_exception_created", "lot_status_changed"],
  erp: ["order_commitment_changed"],
  planner: ["milestone_changed"],
};
const systemNames: Record<string, string> = {
  engineering: "Engineering Hub",
  validation: "Validation Lab",
  manufacturing: "Manufacturing Portal",
  erp: "Commercial ERP",
  planner: "Program Planner",
};
export function triggerSummary(t: Trigger) {
  if (t.type === "schedule") {
    const [hour, minute] = t.time.split(":").map(Number);
    const days = [
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
      "Sunday",
    ];
    return `${t.cadence === "weekly" ? days[t.weekday ?? 0] : words(t.cadence)} at ${hour % 12 || 12}:${String(minute).padStart(2, "0")} ${hour < 12 ? "AM" : "PM"} · ${t.timezone}${t.start_date ? ` · from ${t.start_date}` : ""}`;
  }
  if (t.type === "source_event")
    return `${systemNames[t.system]} · ${words(t.event)}`;
  if (t.type === "condition")
    return `${words(t.condition.field)} ${t.condition.operator.replaceAll("_", " ")} ${String(t.condition.value).replaceAll("_", " ")}`;
  return t.type === "manual"
    ? "Explicit manual request"
    : "Explicit Concierge request";
}
function defaultTrigger(type: Trigger["type"]): Trigger {
  if (type === "schedule")
    return {
      type,
      cadence: "weekdays",
      time: "07:00",
      timezone: "America/Chicago",
      weekday: null,
      start_date: null,
    };
  if (type === "source_event")
    return { type, system: "validation", event: "result_received" };
  if (type === "condition")
    return {
      type,
      condition: {
        field: "evidence_age_hours",
        operator: "greater_than",
        value: 24,
      },
    };
  return { type };
}
function configuration(a: Automation): Config {
  return {
    name: a.name,
    workflow_id: a.workflow_id,
    customer_id: a.customer_id,
    program_id: a.program_id,
    case_scope: a.case_scope,
    trigger: a.trigger,
    authority: a.authority,
    notification_preference: a.notification_preference,
    configuration_state: a.configuration_state,
    safeguards: a.safeguards,
  };
}
export function AutomationEditor({
  existing,
  workflowId,
  close,
}: {
  existing?: Automation;
  workflowId?: string;
  close: () => void;
}) {
  const host = useHost(),
    navigate = useNavigate();
  const definitions = host?.data?.workflows || catalog;
  const initialWorkflow =
    definitions.find((w) => w.workflow_id === workflowId) || definitions[0];
  const [draft, setDraft] = useState<Config>(
    existing
      ? configuration(existing)
      : {
          name: "",
          workflow_id: initialWorkflow.workflow_id,
          customer_id: "CUST-FML01",
          program_id: "PRG-A17",
          case_scope: initialWorkflow.manual_available
            ? initialWorkflow.cases?.[0] || "CR-017"
            : null,
          trigger: defaultTrigger("schedule"),
          authority: "read_only",
          notification_preference: "important_changes",
          configuration_state: "configured",
          safeguards: {
            deduplicate_by: "case",
            reopen_resolved_case: false,
            suppress_duplicate_notifications: true,
            minimum_recheck_minutes: 60,
          },
        },
  );
  const [step, setStep] = useState(0),
    [error, setError] = useState(""),
    [pending, setPending] = useState(false);
  const request = useRef<
    HostSchema["CreateAutomation"] | HostSchema["UpdateAutomation"] | null
  >(null);
  const item = definitions.find((w) => w.workflow_id === draft.workflow_id)!;
  const canSave =
    !!host?.data &&
    !host.error &&
    !host.busy &&
    !!host.capabilities?.automation_save;
  const change = (value: Partial<Config>) =>
    setDraft((d) => ({ ...d, ...value }));
  const trigger = draft.trigger;
  const save = async () => {
    if (!host || !canSave) return;
    setError("");
    setPending(true);
    request.current ||= {
      request_id: `config_${crypto.randomUUID().replaceAll("-", "")}`,
      configuration: draft,
      ...(existing ? { expected_version: existing.version } : {}),
    };
    try {
      const saved = await host.act<Automation>(
        existing
          ? `/automations/${existing.automation_id}/update`
          : "/automations",
        request.current,
      );
      close();
      navigate(automationPath(saved.automation_id));
    } catch (e) {
      setError((e as Error).message);
    }
    // After an uncertain response the immutable submitted configuration remains reviewable/retryable.
  };
  const formId = useId();
  const steps = [
    "Workflow & scope",
    "Trigger",
    "Authority & notifications",
    "Review",
  ];
  return (
    <Dialog
      title={
        existing
          ? "Edit automation configuration"
          : "New automation configuration"
      }
      close={close}
      closeLabel="Close automation editor"
      note="Configuration preview · Nothing runs when saved"
      showDone={false}
      footer={
        <>
          <button type="button" onClick={close}>
            Cancel
          </button>
          {step > 0 && (
            <button
              type="button"
              disabled={pending}
              onClick={() => setStep((s) => s - 1)}
            >
              Back
            </button>
          )}
          <button
            className="cp-primary"
            form={formId}
            type="submit"
            disabled={!canSave}
          >
            {host?.busy
              ? "Saving…"
              : step < 3
                ? "Continue"
                : pending
                  ? "Retry same save"
                  : existing
                    ? "Save changes"
                    : "Save automation"}
          </button>
        </>
      }
    >
      <form
        id={formId}
        className="cp-automation-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (step < 3) setStep((s) => s + 1);
          else void save();
        }}
      >
        {!canSave && (
          <p role="status">
            {host?.busy
              ? "A save is in progress. Wait for its recorded response."
              : host?.error
                ? "Host connection unavailable. Close this dialog and refresh before saving."
                : "Program operator or Engineering approver identity required to save configuration metadata."}
          </p>
        )}
        <ol className="cp-editor-steps" aria-label="Configuration steps">
          {steps.map((name, i) => (
            <li key={name} aria-current={step === i ? "step" : undefined}>
              <span>{i + 1}</span>
              {name}
            </li>
          ))}
        </ol>
        {step === 0 && (
          <fieldset disabled={pending}>
            <legend>Workflow & scope</legend>
            <label>
              Name
              <input
                autoComplete="off"
                value={draft.name}
                maxLength={100}
                required
                pattern=".*\S.*"
                onChange={(e) => change({ name: e.target.value })}
                placeholder="Morning evidence review"
              />
            </label>
            <label>
              Workflow
              <select
                aria-label="Workflow"
                value={draft.workflow_id}
                onChange={(e) => {
                  const w = definitions.find(
                    (w) => w.workflow_id === e.target.value,
                  )!;
                  change({
                    workflow_id: w.workflow_id,
                    case_scope: w.manual_available
                      ? w.cases?.[0] || "CR-017"
                      : null,
                    authority: "read_only",
                  });
                }}
              >
                {definitions.map((w) => (
                  <option key={w.workflow_id} value={w.workflow_id}>
                    {w.name} · {w.mode}
                  </option>
                ))}
              </select>
            </label>
            <div className="cp-form-grid">
              <label>
                Program
                <select
                  aria-label="Program"
                  value={draft.program_id}
                  onChange={(e) => change({ program_id: e.target.value })}
                >
                  <option value="PRG-A17">
                    Helios Atlas Inference · PRG-A17
                  </option>
                </select>
              </label>
              <label>
                Case scope
                <select
                  aria-label="Case scope"
                  value={draft.case_scope || ""}
                  onChange={(e) =>
                    change({ case_scope: e.target.value || null })
                  }
                >
                  {item.manual_available ? (
                    (item.cases || []).map((id) => (
                      <option key={id} value={id}>
                        {id} ·{" "}
                        {id === "CR-019"
                          ? "Standard package"
                          : "Material change"}
                      </option>
                    ))
                  ) : (
                    <option value="">Program scope · Future workflow</option>
                  )}
                </select>
              </label>
            </div>
            <p className="cp-caption">
              Configurations use the current host’s authorized PRG-A17 scope.
              Future stories do not create business cases.
            </p>
          </fieldset>
        )}
        {step === 1 && (
          <fieldset disabled={pending}>
            <legend>Trigger configuration</legend>
            <label>
              Trigger type
              <select
                aria-label="Trigger type"
                value={trigger.type}
                onChange={(e) =>
                  change({
                    trigger: defaultTrigger(e.target.value as Trigger["type"]),
                    safeguards: {
                      ...draft.safeguards!,
                      deduplicate_by: "case",
                    },
                  })
                }
              >
                {[
                  ["manual", "Manual"],
                  ["schedule", "Scheduled"],
                  ["source_event", "Source event"],
                  ["condition", "Condition"],
                  ["chat", "Chat"],
                ].map(([v, n]) => (
                  <option key={v} value={v}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            {trigger.type === "schedule" && (
              <>
                <div className="cp-form-grid">
                  <label>
                    Cadence
                    <select
                      aria-label="Cadence"
                      value={trigger.cadence}
                      onChange={(e) =>
                        change({
                          trigger: {
                            ...trigger,
                            cadence: e.target.value as typeof trigger.cadence,
                            weekday: e.target.value === "weekly" ? 0 : null,
                          },
                        })
                      }
                    >
                      {["daily", "weekdays", "weekly"].map((c) => (
                        <option key={c} value={c}>
                          {words(c)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Time
                    <input
                      type="time"
                      required
                      value={trigger.time}
                      onChange={(e) =>
                        change({
                          trigger: { ...trigger, time: e.target.value },
                        })
                      }
                    />
                  </label>
                </div>
                {trigger.cadence === "weekly" && (
                  <label>
                    Day of week
                    <select
                      aria-label="Day of week"
                      value={trigger.weekday ?? 0}
                      onChange={(e) =>
                        change({
                          trigger: {
                            ...trigger,
                            weekday: Number(e.target.value),
                          },
                        })
                      }
                    >
                      {[
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                      ].map((d, i) => (
                        <option key={d} value={i}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <div className="cp-form-grid">
                  <label>
                    Timezone
                    <select
                      aria-label="Timezone"
                      value={trigger.timezone}
                      onChange={(e) =>
                        change({
                          trigger: { ...trigger, timezone: e.target.value },
                        })
                      }
                    >
                      {[
                        ...new Set([
                          "America/Chicago",
                          "America/New_York",
                          "America/Denver",
                          "America/Los_Angeles",
                          "Europe/London",
                          "Asia/Taipei",
                          "Asia/Tokyo",
                          "UTC",
                          trigger.timezone,
                        ]),
                      ].map((t) => (
                        <option key={t}>{t}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Start date (optional)
                    <input
                      type="date"
                      value={trigger.start_date || ""}
                      onChange={(e) =>
                        change({
                          trigger: {
                            ...trigger,
                            start_date: e.target.value || null,
                          },
                        })
                      }
                    />
                  </label>
                </div>
                <Notice>
                  Would run: {triggerSummary(trigger)}. No scheduler is enabled.
                </Notice>
              </>
            )}
            {trigger.type === "source_event" && (
              <>
                <label>
                  Source system
                  <select
                    aria-label="Source system"
                    value={trigger.system}
                    onChange={(e) =>
                      change({
                        trigger: {
                          type: "source_event",
                          system: e.target.value as typeof trigger.system,
                          event: events[
                            e.target.value
                          ][0] as typeof trigger.event,
                        },
                      })
                    }
                  >
                    {Object.entries(systemNames).map(([v, n]) => (
                      <option value={v} key={v}>
                        {n}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Source event
                  <select
                    aria-label="Source event"
                    value={trigger.event}
                    onChange={(e) =>
                      change({
                        trigger: {
                          ...trigger,
                          event: e.target.value as typeof trigger.event,
                        },
                      })
                    }
                  >
                    {events[trigger.system].map((v) => (
                      <option key={v} value={v}>
                        {words(v)}
                      </option>
                    ))}
                  </select>
                </label>
                <Notice>
                  Trigger preview · Configured listener is not active.
                </Notice>
              </>
            )}
            {trigger.type === "condition" && (
              <>
                <label>
                  Business field
                  <select
                    aria-label="Business field"
                    value={trigger.condition.field}
                    onChange={(e) => {
                      const field = e.target
                        .value as typeof trigger.condition.field;
                      change({
                        trigger: {
                          type: "condition",
                          condition:
                            field === "milestone_risk"
                              ? { field, operator: "equals", value: "high" }
                              : field === "eligible_quantity"
                                ? {
                                    field,
                                    operator: "less_than",
                                    value: "requested_quantity",
                                  }
                                : {
                                    field,
                                    operator: "greater_than",
                                    value: 24,
                                  },
                        },
                      });
                    }}
                  >
                    {[
                      "milestone_risk",
                      "evidence_age_hours",
                      "eligible_quantity",
                      "approval_pending_hours",
                      "validation_missing_hours",
                    ].map((v) => (
                      <option key={v} value={v}>
                        {words(v)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="cp-form-grid">
                  <label>
                    Operator
                    <select
                      aria-label="Operator"
                      value={trigger.condition.operator}
                      onChange={() => {}}
                    >
                      <option value={trigger.condition.operator}>
                        {words(trigger.condition.operator)}
                      </option>
                    </select>
                  </label>
                  {typeof trigger.condition.value === "number" ? (
                    <label>
                      Threshold (hours)
                      <input
                        type="number"
                        min={1}
                        max={8760}
                        step={1}
                        required
                        value={trigger.condition.value}
                        onChange={(e) => {
                          if (
                            "value" in trigger.condition &&
                            typeof trigger.condition.value === "number"
                          )
                            change({
                              trigger: {
                                ...trigger,
                                condition: {
                                  ...trigger.condition,
                                  value: Number(e.target.value),
                                },
                              },
                            });
                        }}
                      />
                    </label>
                  ) : (
                    <label>
                      Value
                      <select
                        aria-label="Value"
                        value={trigger.condition.value}
                        onChange={() => {}}
                      >
                        <option value={trigger.condition.value}>
                          {words(trigger.condition.value)}
                        </option>
                      </select>
                    </label>
                  )}
                </div>
                <Notice>
                  Condition preview · No background evaluator or monitoring.
                </Notice>
              </>
            )}
            {(trigger.type === "manual" || trigger.type === "chat") && (
              <Notice>
                {trigger.type === "manual"
                  ? "Saving does not launch a run. Use the workflow’s explicit manual action where connected."
                  : "Concierge can save this configuration after explicit confirmation. Saving does not start a run or activate a background trigger."}
              </Notice>
            )}
            <details>
              <summary>Future duplicate & storm safeguards</summary>
              <label>
                Deduplicate by
                <select
                  aria-label="Deduplicate by"
                  value={draft.safeguards?.deduplicate_by}
                  onChange={(e) =>
                    change({
                      safeguards: {
                        ...draft.safeguards!,
                        deduplicate_by: e.target.value as "case" | "event",
                      },
                    })
                  }
                >
                  <option value="case">Case</option>
                  {trigger.type === "source_event" && (
                    <option value="event">Event</option>
                  )}
                </select>
              </label>
              <label>
                Minimum recheck interval (minutes)
                <input
                  type="number"
                  min={5}
                  max={10080}
                  step={1}
                  required
                  value={draft.safeguards?.minimum_recheck_minutes}
                  onChange={(e) =>
                    change({
                      safeguards: {
                        ...draft.safeguards!,
                        minimum_recheck_minutes: Number(e.target.value),
                      },
                    })
                  }
                />
              </label>
              <label className="cp-checkbox">
                <input
                  type="checkbox"
                  checked={draft.safeguards?.suppress_duplicate_notifications}
                  onChange={(e) =>
                    change({
                      safeguards: {
                        ...draft.safeguards!,
                        suppress_duplicate_notifications: e.target.checked,
                      },
                    })
                  }
                />{" "}
                Suppress duplicate notifications
              </label>
              <p>
                Resolved cases will not reopen automatically. Safeguards are
                stored for future activation only.
              </p>
            </details>
          </fieldset>
        )}
        {step === 2 && (
          <fieldset disabled={pending}>
            <legend>Authority & notifications</legend>
            <label>
              Authority
              <select
                aria-label="Authority"
                value={draft.authority}
                onChange={(e) =>
                  change({ authority: e.target.value as Config["authority"] })
                }
              >
                {(item.configuration_authorities || ["read_only"]).map((a) => (
                  <option key={a} value={a}>
                    {authorityName(a)}
                    {item.mode === "Preview" ? " · Planned" : ""}
                  </option>
                ))}
              </select>
            </label>
            <p>
              {draft.authority === "proposal_only"
                ? "Planned proposal preparation with human review. This future workflow is not executable."
                : "Future triggers may investigate and produce findings only. Saved settings cannot authorize execution."}
            </p>
            <p>{item.approvals}</p>
            <label>
              Notification preference
              <select
                aria-label="Notification preference"
                value={draft.notification_preference}
                onChange={(e) =>
                  change({
                    notification_preference: e.target
                      .value as Config["notification_preference"],
                  })
                }
              >
                <option value="important_changes">
                  Important changes only
                </option>
                <option value="all_outcomes">All outcomes</option>
                <option value="none">None</option>
              </select>
            </label>
            <p className="cp-caption">
              Preference saved for future use. No notifications are sent by
              these configurations.
            </p>
            <label>
              Configuration state
              <select
                aria-label="Configuration state"
                value={draft.configuration_state}
                onChange={(e) =>
                  change({
                    configuration_state: e.target
                      .value as Config["configuration_state"],
                  })
                }
              >
                <option value="configured">Configured</option>
                <option value="paused">Paused</option>
              </select>
            </label>
          </fieldset>
        )}
        {step === 3 && (
          <>
            <h3>{draft.name}</h3>
            <Facts
              rows={[
                ["Workflow", `${item.name} · ${item.mode}`],
                [
                  "Program / case",
                  `${draft.program_id}${draft.case_scope ? ` / ${draft.case_scope}` : " · Program scope"}`,
                ],
                ["Would run", triggerSummary(trigger)],
                [
                  "Authority",
                  `${authorityName(draft.authority || "read_only")}${item.mode === "Preview" ? " · Planned only" : ""}`,
                ],
                [
                  "What it would do",
                  draft.authority === "proposal_only"
                    ? "Prepare findings and a proposal for human review, once implemented"
                    : "Read scoped evidence and produce findings, once the trigger is connected",
                ],
                ["Cannot do", item.limits],
                ["Human approvals", item.approvals],
                [
                  "Notifications",
                  `${words(draft.notification_preference || "important_changes")} · Preference only`,
                ],
                [
                  "State",
                  `${words(draft.configuration_state || "configured")} · Configuration preview`,
                ],
              ]}
            />
            <Notice>
              Saved configuration — background execution not enabled in this
              demo.
            </Notice>
          </>
        )}
        {error && (
          <p className="cp-error" role="alert">
            {error} The submitted configuration is retained for an exact retry.
            Refresh the saved record if its version changed.
          </p>
        )}
        {!canSave && (
          <p className="cp-caption">
            A connected host and Program operator or Engineering approver
            profile are required.
          </p>
        )}
      </form>
    </Dialog>
  );
}

export function AutomationPage() {
  const host = useHost(),
    { automationId } = useParams(),
    navigate = useNavigate();
  const [edit, setEdit] = useState(false),
    [error, setError] = useState(""),
    [pendingAction, setPendingAction] = useState<string | null>(null);
  const item = host?.data?.automations?.find(
    (a) => a.automation_id === automationId,
  );
  const pending = useRef<{ action: string; body: unknown } | null>(null);
  if (!item)
    return (
      <>
        <HostReadState />
        <Empty>
          {host?.data
            ? "Configuration not found."
            : "Reading saved configuration…"}{" "}
          <Link to="/control/workflows">Browse workflows</Link>
        </Empty>
      </>
    );
  const canEdit =
    !host!.error && !host!.busy && !!host!.capabilities?.automation_save;
  const mutate = async (action: "state" | "delete") => {
    if (!canEdit || !host) return;
    setError("");
    pending.current ||= {
      action,
      body: {
        request_id: `config_${crypto.randomUUID().replaceAll("-", "")}`,
        expected_version: item.version,
        ...(action === "state"
          ? {
              configuration_state:
                item.configuration_state === "paused" ? "configured" : "paused",
            }
          : {}),
      },
    };
    setPendingAction(pending.current.action);
    try {
      await host.act(
        `/automations/${item.automation_id}/${pending.current.action}`,
        pending.current.body,
      );
      if (pending.current.action === "delete") navigate("/control/workflows");
      pending.current = null;
      setPendingAction(null);
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <>
      <Crumbs
        items={[
          { label: "Workflows & Automations", to: "/control/workflows" },
          { label: item.name },
        ]}
      />
      <Heading
        title={item.name}
        description="Saved automation configuration"
        action={
          <button
            disabled={!canEdit || !!pendingAction}
            onClick={() => setEdit(true)}
          >
            Edit configuration
          </button>
        }
      />
      <HostReadState />
      <Section
        title="Configuration preview"
        action={<StatusText>{words(item.configuration_state)}</StatusText>}
      >
        <Notice>
          Saved configuration — background execution not enabled in this demo.
        </Notice>
        <Facts
          rows={[
            [
              "Workflow",
              <Link to={workflowPath(item.workflow_id)}>
                {item.workflow_name} · {item.workflow_mode}
              </Link>,
            ],
            [
              "Scope",
              `${item.program_id}${item.case_scope ? ` / ${item.case_scope}` : " · Program scope"}`,
            ],
            ["Trigger preview", triggerSummary(item.trigger)],
            [
              "Authority",
              `${authorityName(item.authority)}${item.workflow_mode === "Preview" ? " · Planned authority" : ""}`,
            ],
            [
              "Execution mode",
              "Configuration preview · No worker, listener or evaluator",
            ],
            [
              "Notifications",
              `${words(item.notification_preference)} · Preference only`,
            ],
            [
              "Owner",
              `${item.owner_actor_id}${item.seeded_example ? " · Seeded example" : " · Demo actor"}`,
            ],
            ["Created", date(item.created_at, true)],
            ["Updated", `${date(item.updated_at, true)} · ${item.updated_by}`],
            ["Version", item.version],
          ]}
        />
        <details>
          <summary>Saved safeguards</summary>
          <Facts
            rows={[
              ["Deduplicate by", words(item.safeguards!.deduplicate_by)],
              ["Reopen resolved cases", "No"],
              [
                "Suppress duplicate notifications",
                item.safeguards!.suppress_duplicate_notifications
                  ? "Yes"
                  : "No",
              ],
              [
                "Minimum recheck",
                `${item.safeguards!.minimum_recheck_minutes} minutes · Configuration only`,
              ],
            ]}
          />
        </details>
        <div className="cp-inline cp-editor-actions">
          <button
            disabled={
              !canEdit || (!!pendingAction && pendingAction !== "state")
            }
            onClick={() => void mutate("state")}
          >
            {pendingAction === "state"
              ? "Retry same state change"
              : item.configuration_state === "paused"
                ? "Resume configuration"
                : "Pause configuration"}
          </button>
          <button
            disabled={
              !canEdit || (!!pendingAction && pendingAction !== "delete")
            }
            onClick={() => void mutate("delete")}
          >
            {pendingAction === "delete"
              ? "Retry same delete"
              : "Delete configuration"}
          </button>
        </div>
        <p className="cp-caption">
          These controls change configuration metadata only. Existing cases,
          jobs and approvals retain their state.
        </p>
        {error && (
          <p className="cp-error" role="alert">
            {error}
          </p>
        )}
      </Section>
      {edit && (
        <AutomationEditor existing={item} close={() => setEdit(false)} />
      )}
    </>
  );
}
