import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { call, useHost, type HostSchema } from "./host";
import { DEMO_CHANGED } from "../demo-epoch";

// Page-lifetime latch survives route/persona/reset remounts and StrictMode.
// Reload creates a new entry attempt; the host deduplicates across tabs/reloads.
let entryRequest: Promise<HostSchema["AutonomousState"] | null> | undefined;
let connected = false;
// A direct maintenance visit can be redirected to Overview before login. Keep
// its intent across that redirect so signing in to reset never starts work.
let suppressed = window.location.pathname.replace(/\/$/, "") === "/control/operations/demo";

export function AutonomousEntry() {
  const host = useHost();
  const location = useLocation();
  const [error, setError] = useState("");
  const [legacyRun, setLegacyRun] = useState(false);
  const source = host?.data?.source_url;
  const program = host?.capabilities?.program_id;
  const refresh = host?.refresh;
  useEffect(() => {
    const reset = () => {
      if (connected) suppressed = true;
      setError("");
      setLegacyRun(false);
    };
    window.addEventListener(DEMO_CHANGED, reset);
    return () => window.removeEventListener(DEMO_CHANGED, reset);
  }, []);
  useEffect(() => {
    if (!source || !program || !refresh) return;
    connected = true;
    // Let a user open Demo controls directly to inspect/reset without launching.
    if (suppressed || location.pathname === "/control/operations/demo") return;
    let mounted = true;
    entryRequest ??= (async () => {
      const controls = await call<HostSchema["DemoControls"]>("/demo", null);
      if (!controls.enabled || suppressed) return null;
      return call<HostSchema["AutonomousState"]>("/demo/autonomous/enter", null, { expected_epoch: controls.epoch });
    })();
    void entryRequest.then(async (opening) => {
      if (mounted && !suppressed) {
        setLegacyRun(opening?.status === "human_handoff_ready");
        await refresh();
      }
    }).catch((e: Error) => {
      if (mounted && !suppressed) setError(e.message);
    });
    return () => { mounted = false; };
  }, [source, program, refresh, location.pathname]);
  if (error) return <p className="cp-error" role="alert">Automatic QE-011 opening could not start: {error}. Check Demo controls.</p>;
  return legacyRun ? <p role="status">This is an earlier QE-011 demo run. Use Full demo reset, then reload Overview to start the touchless opening.</p> : null;
}
