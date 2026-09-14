import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import { Dialog } from "./dialog";
import { hostError, useHost, type HostSchema } from "./host";
import { observeDemoEpoch } from "../demo-epoch";
import { caseRuntime } from "./runtime-label";

export function MasterReset() {
  const host = useHost(), read = host?.read;
  const permitted = host?.capabilities?.demo_controls;
  const [enabled, setEnabled] = useState(false);
  const [open, setOpen] = useState(false), [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<HostSchema["DemoPreview"] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    if (read && permitted) void read<HostSchema["DemoControls"]>("/demo")
      .then(value => { if (active) setEnabled(value.enabled); }).catch(() => {});
    return () => { active = false; };
  }, [read, permitted]);
  if (!enabled || !permitted || !host) return null;

  const review = async () => {
    setOpen(true); setBusy(true); setError(""); setPreview(null);
    try { setPreview(await host.read<HostSchema["DemoPreview"]>("/demo/preview?scope=full")); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  };
  const restart = async () => {
    if (!preview?.allowed || busy) return;
    setBusy(true); setError("");
    try {
      const response = await fetch("/control-api/demo/reset", {
        method: "POST", cache: "no-store",
        headers: { "Content-Type": "application/json", "X-Stratos-Action": "1",
          "X-Stratos-Demo-Profile": host.profile!, "X-Stratos-Demo-Maintainer": "local-demo-reset" },
        body: JSON.stringify({ scope: "full", confirmation: "RESET", expected_epoch: preview.epoch, restart_opening: true }),
      });
      const value = await response.json();
      if (!value.validation) throw Error(hostError(value.error?.code || "HOST_UNAVAILABLE"));
      const result = value as HostSchema["DemoResetResult"];
      const restored = response.ok && result.result === "restored" && result.validation.baseline_valid;
      const started = restored && result.opening_status === "armed";
      const message = !restored
        ? "Demo reset could not finish. QE-011 has not started. Review Demo controls and retry the full reset."
        : started
          ? "Demo reset complete. All four cases are New. QE-011 starts automatically in 8 seconds."
          : `All four cases were reset. QE-011 could not start: ${hostError(result.opening_error || "AUTONOMOUS_START_FAILED")}. Use Replay autonomous opening to retry.`;
      // Preserve only the selected public demo persona, never old work or action
      // drafts. A fresh page also clears local source caches and entry latches.
      sessionStorage.setItem("stratos:demo-restart-notice", message);
      sessionStorage.setItem("stratos:demo-restart-operator", "1");
      if (!restored) {
        sessionStorage.removeItem("stratos:demo-restart-notice");
        sessionStorage.removeItem("stratos:demo-restart-operator");
        setError(message);
        setPreview(null);
        setBusy(false);
        await host.refresh().catch(() => {});
        return;
      }
      // Navigation replaces the page; avoid a competing remount consuming the
      // one-use persona handoff before the replacement page can read it.
      observeDemoEpoch(result.epoch, false);
      window.location.assign("/control/overview");
    } catch (e) {
      setError(`${(e as Error).message}. Refresh the reset preview before trying again.`);
      setPreview(null);
      setBusy(false);
    }
  };
  return <>
    <button className="cp-bell" aria-label="Reset demo" title="Reset demo" onClick={() => void review()}>
      <RotateCcw size={20} aria-hidden="true" />
    </button>
    {open && <Dialog title="Reset and restart demo" className="cp-master-reset-modal" close={() => { if (!busy) setOpen(false); }}
      closeLabel="Cancel reset" note="Demo controls" showDone={false}
      footer={<>
        <button disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
        <button className="cp-primary" disabled={busy || !preview?.allowed} onClick={() => void restart()}>Reset and restart</button>
      </>}>
      <p>Start a fresh walkthrough:</p>
      <ul>
        <li>Return CR-017, CR-019, QE-004 and DR-009 to <strong>New</strong>.</li>
        <li>Restore their original records across all five source systems, including shared inventory and validation data.</li>
        <li>Clear current investigations, decisions, results and chat drafts. Active demo work will stop.</li>
        <li>Return to Overview and automatically start QE-011 after 8 seconds.</li>
      </ul>
      <p>Previous demo activity is archived. Historical evaluations and product settings are preserved.</p>
      <p>{caseRuntime(host.data, "QE-011") === "live_model" ? "QE-011 will use the configured live model, which may incur usage charges." : "QE-011 is a scripted opening and makes no model calls."}</p>
      {busy && <p role="status">{preview ? "Resetting cases and source records, then starting QE-011…" : "Checking demo reset…"}</p>}
      {preview && !preview.allowed && <p role="alert">{preview.discrepancies?.join(" ")}</p>}
      {error && <p className="cp-error" role="alert">{error} <button onClick={() => void review()}>Refresh preview</button></p>}
    </Dialog>}
  </>;
}
