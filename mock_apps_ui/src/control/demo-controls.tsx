import { useEffect, useState } from "react";
import { Link } from "./access";
import { useHost, type HostSchema } from "./host";
import { Dialog } from "./dialog";
import { Heading, Section, Facts } from "./ui";
import { observeDemoEpoch } from "../demo-epoch";
import { caseRuntime } from "./runtime-label";
import { Play, RotateCcw, ClipboardCheck } from "lucide-react";
import "./rethink-utilities.css";

type Controls = HostSchema["DemoControls"];
type Scope = HostSchema["DemoResetRequest"]["scope"];
type Preview = HostSchema["DemoPreview"];
type Check = HostSchema["BaselineCheck"];
type Result = HostSchema["DemoResetResult"];

type Opening = HostSchema["AutonomousState"];
const openingLabels = {
  idle: "Idle",
  armed: "Armed",
  event_emitted: "Event emitted",
  workflow_running: "Workflow running",
  touchless_handoff_verified: "Touchless handoff verified",
  escalated: "Escalated",
  human_handoff_ready: "Human review required",
  failed: "Failed",
};

function AutonomousControls() {
  const host = useHost(),
    read = host?.read;
  const [value, setValue] = useState<Opening | null>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    if (!read) return;
    let mounted = true;
    const refresh = () => {
      if (document.visibilityState === "visible")
        void read<Opening>("/demo/autonomous")
          .then((v) => {
            if (mounted) setValue(v);
          })
          .catch((e) => {
            if (mounted) setError(e.message);
          });
    };
    refresh();
    const timer =
      value &&
      ["armed", "event_emitted", "workflow_running"].includes(value.status)
        ? setInterval(refresh, 1500)
        : undefined;
    document.addEventListener("visibilitychange", refresh);
    return () => {
      mounted = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [read, value?.status]);
  const act = async (action: "prepare" | "reset") => {
    if (!host || busy) return;
    setBusy(true);
    setError("");
    try {
      const controls = await host.read<Controls>("/demo");
      const response = await fetch(`/control-api/demo/autonomous/${action}`, {
        method: "POST",
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
          "X-Stratos-Action": "1",
          "X-Stratos-Demo-Profile": host.profile!,
          "X-Stratos-Demo-Maintainer": "local-demo-reset",
        },
        body: JSON.stringify({ expected_epoch: controls.epoch }),
      });
      const result = await response.json();
      observeDemoEpoch(
        response.headers.get("X-Stratos-Demo-Epoch") || controls.epoch,
      );
      if (!response.ok)
        throw Error(
          result.error?.code === "DEMO_BASELINE_INVALID"
            ? "Prepare the main demo baseline with Full Demo Reset, then try again."
            : (result.error?.code || "Opening unavailable").replaceAll(
                "_",
                " ",
              ),
        );
      setValue(result);
      await host.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section
      className="cp-autonomous-opening rt-presenter-opening"
      aria-labelledby="autonomous-title"
    >
      <div className="cp-inline">
        <h2 id="autonomous-title">Autonomous opening</h2>
        <strong role="status">
          {value ? openingLabels[value.status] : "Reading…"}
        </strong>
      </div>
      <ol className="rt-mini-flow" aria-label="Autonomous opening sequence">
        <li>Manufacturing event</li>
        <li>Agent investigation</li>
        <li>Verified standard handoff</li>
      </ol>
      <p>
        QE-011 starts 8 seconds after entering the demo. The bounded
        investigation handoff requires no human approval; material stays on
        hold.
      </p>
      <div className="cp-demo-actions">
        <button
          className="cp-primary"
          disabled={
            busy ||
            !value ||
            ["armed", "event_emitted", "workflow_running"].includes(
              value.status,
            )
          }
          onClick={() => void act("prepare")}
        >
          <Play size={16} aria-hidden="true" /> Replay autonomous opening
        </button>
        <button disabled={busy || !value} onClick={() => void act("reset")}>
          <RotateCcw size={16} aria-hidden="true" /> Reset autonomous opening
        </button>
        <Link to="/control/overview#agent-workspace">Open Overview →</Link>
      </div>
      {value && <p role="status">{value.message}</p>}
      {value?.run_id && (
        <Link to={`/control/runs/${value.run_id}`}>
          Inspect event and run →
        </Link>
      )}
      <details className="rt-inline-details">
        <summary>Opening runtime and replay behavior</summary>
        <p>
          {caseRuntime(host?.data, "QE-011") === "live_model"
            ? "Live runtime: opening the demo or replaying QE-011 may use paid model calls. One event, one bounded workflow; no automatic retries."
            : "QE-011 opening · No model calls · Two-minute processing sequence."}{" "}
          Completed openings stay recorded. Use the reset icon beside Alerts to
          reset all cases and automatically restart QE-011, or Replay to restart
          only this opening.
        </p>
      </details>
      {error && (
        <p role="alert" className="cp-error">
          {error}
        </p>
      )}
    </section>
  );
}

export function DemoEntry() {
  const read = useHost()?.read;
  const [data, setData] = useState<Controls | null>(null);
  useEffect(() => {
    if (read)
      void read<Controls>("/demo")
        .then(setData)
        .catch(() => {});
  }, [read]);
  const access = useHost()?.capabilities;
  if (!data?.enabled || !access?.demo_controls) return null;
  return (
    <p className="cp-demo-entry">
      <Link to="/control/operations/demo">Demo controls</Link>
      {data.recovery_required && " Reset incomplete — reconciliation required."}
    </p>
  );
}

export function DemoControlsPage() {
  const host = useHost();
  const [data, setData] = useState<Controls | null>(null);
  const [scope, setScope] = useState<Scope>("full");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [confirmation, setConfirmation] = useState("");
  const [check, setCheck] = useState<Check | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const refresh = async () => {
    if (host) setData(await host.read<Controls>("/demo"));
  };
  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, [host?.read]);
  const verify = async () => {
    if (!host) return;
    setBusy(true);
    setError("");
    try {
      setCheck(await host.read<Check>("/demo/verify?scope=" + scope));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const prepare = async () => {
    if (!host) return;
    setBusy(true);
    setError("");
    setConfirmation("");
    try {
      setPreview(await host.read<Preview>("/demo/preview?scope=" + scope));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const reset = async () => {
    if (!preview || confirmation !== "RESET") return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/control-api/demo/reset", {
        method: "POST",
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
          "X-Stratos-Action": "1",
          ...(host?.profile ? { "X-Stratos-Demo-Profile": host.profile } : {}),
          "X-Stratos-Demo-Maintainer": "local-demo-reset",
        },
        body: JSON.stringify({
          scope: preview.scope,
          confirmation: "RESET",
          expected_epoch: preview.epoch,
          restart_opening: preview.scope === "full",
        }),
      });
      const result = await response.json();
      if (result.error) throw new Error(result.error.code.replaceAll("_", " "));
      const value = result as Result;
      setCheck(value.validation);
      setPreview(null);
      await refresh();
      // Global remount clears editable drafts, voice capture and old action cards.
      observeDemoEpoch(value.epoch);
    } catch (e) {
      setError(
        (e as Error).message + ". Check current demo state before retrying.",
      );
      await refresh().catch(() => {});
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="rt-utilities rt-demo-controls">
      <Heading
        eyebrow="Presenter tools"
        title="Demo controls"
        description="Prepare the walkthrough, verify the starting state or restore a previous run."
      />
      <p>
        <Link to="/control/operations">Back to Operations</Link>
      </p>
      {error && (
        <p className="cp-error" role="alert">
          {error}
        </p>
      )}
      {!data?.enabled ? (
        <p>
          Demo management is unavailable. Start the local host with explicit
          demo controls enabled.
        </p>
      ) : (
        <>
          <AutonomousControls />
          <details className="rt-disclosure">
            <summary>
              Current demo generation{" "}
              <span>
                {data.recovery_required
                  ? "Recovery required"
                  : data.demo_baseline_version}
              </span>
            </summary>
            <Section title="Current demo generation">
              <Facts
                rows={[
                  ["Baseline", data.demo_baseline_version],
                  [
                    "Last reset",
                    data.latest
                      ? `${data.latest.scope} · ${data.latest.result} · ${data.latest.timestamp}`
                      : "No reset recorded",
                  ],
                  [
                    "Last reset validation",
                    data.latest?.baseline_valid
                      ? "Passed at reset completion; verify for current state"
                      : "Not confirmed",
                  ],
                  [
                    "Archived demo generations",
                    String(data.archived_reset_count),
                  ],
                ]}
              />
              {data.recovery_required && (
                <p className="cp-error" role="alert">
                  Reset incomplete at {data.latest?.stage}. The baseline is not
                  confirmed. Retry {data.pending_scope} or Full Demo Reset
                  before continuing business actions.
                </p>
              )}
              <p>
                Historical project verification remains preserved, including the
                original 4/6 live smoke and the later targeted passes. Archived
                demo records are retained locally and excluded from current
                runs, decisions and search.
              </p>
            </Section>
          </details>
          <Section
            title="Restore the walkthrough"
            note="Choose the scope, check the baseline, then review exactly what will be reset."
            className="rt-reset-panel"
          >
            <div className="cp-demo-actions">
              <label>
                Reset scope{" "}
                <select
                  value={scope}
                  onChange={(e) => {
                    setScope(e.target.value as Scope);
                    setCheck(null);
                  }}
                  disabled={busy}
                >
                  <option value="full">Full demo · All demo cases</option>
                  {(
                    ["CR-017", "CR-019", "QE-004", "DR-009", "QE-011"] as const
                  ).map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <button onClick={verify} disabled={busy}>
                <ClipboardCheck size={16} aria-hidden="true" /> Verify baseline
              </button>
              <button onClick={prepare} disabled={busy}>
                <RotateCcw size={16} aria-hidden="true" /> Review reset…
              </button>
            </div>
            <details className="rt-inline-details">
              <summary>Reset scope and restart behavior</summary>
              <p>
                Full reset restores shared material, technical-readiness
                references and all four workflows together. Single-scenario
                reset refuses conflicting shared state. Curated automation
                examples remain configuration previews. Full reset also disarms
                and clears QE-011. The reset leaves this page at baseline.
                Reload Overview to start a new automatic QE-011 opening, or use
                Replay above. The reset icon beside Alerts combines full reset
                and automatic QE-011 restart.
              </p>
            </details>
            {busy && <p role="status">Checking demo state…</p>}
            {check && (
              <div role="status" className="cp-demo-check">
                <h3>
                  {check.baseline_valid
                    ? "Baseline valid"
                    : "Baseline not valid"}{" "}
                  · {check.scope}
                </h3>
                <p>{check.checked_at}</p>
                <Facts
                  rows={Object.entries(check.scenario_checks || {}).map(
                    ([caseId, valid]) => [
                      caseId,
                      valid ? "Matches baseline" : "Discrepancy",
                    ],
                  )}
                />
                {check.quantities?.requested_quantity != null && (
                  <p>
                    Physical {check.quantities.physical_quantity} · Held{" "}
                    {check.quantities.held_quantity} · Allocated{" "}
                    {check.quantities.allocated_quantity} · Eligible{" "}
                    {check.quantities.eligible_unallocated_quantity} / Requested{" "}
                    {check.quantities.requested_quantity} · Gap{" "}
                    {check.quantities.gap_quantity}
                  </p>
                )}
                <ul>
                  {(check.discrepancies || []).map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </Section>
        </>
      )}
      {preview && (
        <Dialog
          title={
            preview.scope === "full"
              ? "Reset full demo"
              : "Reset " + preview.scope
          }
          close={() => {
            if (!busy) setPreview(null);
          }}
          note="Local demo maintenance · Not a business approval"
          closeLabel="Cancel reset"
          showDone={false}
          footer={
            <button
              disabled={busy || !preview.allowed || confirmation !== "RESET"}
              onClick={reset}
            >
              Confirm demo reset
            </button>
          }
        >
          <h3>What will be reset</h3>
          <ul>
            {preview.resets.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          <h3>What will be preserved</h3>
          <ul>
            {preview.preserves.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          <p>Affected source systems: {preview.affected_systems.join(", ")}.</p>
          <h3>Shared dependencies</h3>
          <ul>
            {preview.shared_dependencies.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          {!preview.allowed ? (
            <div className="cp-error" role="alert">
              {(preview.discrepancies || []).map((t) => (
                <p key={t}>{t}</p>
              ))}
            </div>
          ) : (
            <label className="cp-demo-confirm">
              Type RESET to confirm{" "}
              <input
                autoComplete="off"
                value={confirmation}
                disabled={busy}
                onChange={(e) => setConfirmation(e.target.value)}
              />
            </label>
          )}
          {error && <p role="alert">{error}</p>}
        </Dialog>
      )}
    </div>
  );
}
