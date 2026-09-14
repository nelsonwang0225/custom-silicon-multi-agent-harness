import React, { useEffect } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { DEMO_CHANGED, observeDemoEpoch, isAutonomousEpoch } from "./demo-epoch";
import { WorkspaceBoundary } from "./workspace-boundary";
import "./style.css";
const ControlPlane = React.lazy(() => import("./control/app").then(m => ({ default: m.ControlPlane })));
const SourceApps = React.lazy(() => import("./source-app").then(m => ({ default: m.SourceApps })));
function Root() {
  const [demoGeneration, setDemoGeneration] = React.useState(0);
  const [resetNotice, setResetNotice] = React.useState(() => sessionStorage.getItem("stratos:demo-restart-notice") || "");
  useEffect(() => {
    sessionStorage.removeItem("stratos:demo-restart-notice");
    let active = true;
    let enabled = false;
    const changed = () => {
      if (!isAutonomousEpoch()) setDemoGeneration(n => n + 1);
      setResetNotice(sessionStorage.getItem("stratos:demo-restart-notice") || "Demo state changed. Previous drafts, proposals and action cards are no longer current. Check Demo controls for reset status.");
    };
    const read = async () => {
      try {
        const response = await fetch("/control-api/demo", { cache: "no-store" });
        const value = response.ok ? await response.json() : null;
        if (active && value?.enabled) { enabled = true; observeDemoEpoch(value.epoch); }
      } catch { /* A source-only deployment does not have a control host. */ }
    };
    window.addEventListener(DEMO_CHANGED, changed);
    window.addEventListener("focus", read);
    const timer = setInterval(() => { if (enabled && document.visibilityState === "visible") void read(); }, 5000);
    void read();
    return () => { active = false; clearInterval(timer); window.removeEventListener(DEMO_CHANGED, changed); window.removeEventListener("focus", read); };
  }, []);
  return (
    <>
    {resetNotice && <div className="demo-reset-notice" role="status">{resetNotice} <button onClick={() => setResetNotice("")}>Dismiss</button></div>}
    <WorkspaceBoundary key={demoGeneration}>
    <Routes>
      <Route
        path="/overview"
        element={<Navigate to="/control/overview" replace />}
      />
      <Route
        path="/portfolio"
        element={<Navigate to="/control/overview" replace />}
      />
      <Route
        path="/control/*"
        element={
          <React.Suspense
            fallback={<div role="status">Loading program control plane…</div>}
          >
            <ControlPlane />
          </React.Suspense>
        }
      />
      <Route
        path="*"
        element={
          <React.Suspense fallback={<div role="status">Loading source applications…</div>}><SourceApps /></React.Suspense>
        }
      />
    </Routes>
    </WorkspaceBoundary>
    </>
  );
}
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Root />
    </BrowserRouter>
  </React.StrictMode>,
);
