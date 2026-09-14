import { DemoControlsPage } from "./demo-controls";
import { AutonomousEntry } from "./autonomous-entry";
import { WorkspaceBoundary } from "../workspace-boundary";
import { lazy, Suspense } from "react";
const Operations = lazy(() =>
  import("./operations").then((m) => ({ default: m.Operations })),
);
const OperationsRun = lazy(() =>
  import("./operations").then((m) => ({ default: m.OperationsRun })),
);
const OperationsSession = lazy(() =>
  import("./operations").then((m) => ({ default: m.OperationsSession })),
);
import { Workflows, AutomationPage } from "./workflows";
import { EvidenceDecision } from "./physical-validation";
import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
  Navigate,
} from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { ControlData, useControl } from "./data";
import { Empty, ReadStamp, SourceContext } from "./ui";
import { Portfolio } from "./portfolio";
import { ProgramPage } from "./program";
import { CasePage } from "./case";
import { Knowledge, Scenarios } from "./previews";
import { Masthead, type ConciergeRequest } from "./masthead";
import { navigation } from "./catalog";
import type { Persona } from "../api";
import { Decisions, DecisionReview } from "./decisions";
import { HostData, useHost } from "./host";
import { routeAllowed } from "./access";
import { Concierge } from "./assistant";
import { EXPLAIN_AGENT } from "./agent-workspace";
import "./style.css";
import "./polish.css";
import "./agent-workspace.css";
import "./traceability.css";
import "./rethink.css";
function Shell({
  profile,
  onProfile,
}: {
  profile: Persona | null;
  onProfile: (p: Persona | null) => void;
}) {
  const { data, error, freshness } = useControl();
  const host = useHost();
  const location = useLocation();
  const isOverview =
    location.pathname.replace(/\/$/, "") === "/control/overview";
  const [conciergeRequest, setConciergeRequest] = useState<ConciergeRequest>({
    id: 0,
    query: "",
    context: "",
  });
  useEffect(() => {
    const explain = (event: Event) => {
      const { query, context } = (event as CustomEvent).detail;
      if (
        typeof query === "string" &&
        typeof context === "string" &&
        routeAllowed(host?.capabilities, context)
      )
        setConciergeRequest((previous) => ({
          id: previous.id + 1,
          query,
          context,
          origin: "agent",
        }));
    };
    window.addEventListener(EXPLAIN_AGENT, explain);
    return () => window.removeEventListener(EXPLAIN_AGENT, explain);
  }, [host?.capabilities]);
  useEffect(() => {
    document.title = `${location.pathname.endsWith("/overview") ? "Overview" : "Program control plane"} · Stratos Silicon`;
    window.scrollTo(0, 0);
  }, [location.pathname]);
  return (
    <div className="cp-root cp-rethink">
      <a href="#cp-main" className="cp-skip">
        Skip to content
      </a>
      <Masthead
        profile={profile}
        onProfile={onProfile}
        ask={(query) =>
          setConciergeRequest((previous) => ({
            id: previous.id + 1,
            query,
            context: location.pathname,
          }))
        }
      />
      <nav className="cp-nav" aria-label="Control plane navigation">
        {navigation
          .filter(([, path]) => routeAllowed(host?.capabilities, path))
          .map(([name, path, Icon]) => (
            <NavLink key={path} end={path === "/control/overview"} to={path}>
              <Icon
                size={17}
                strokeWidth={1.75}
                aria-hidden="true"
                focusable="false"
              />
              {name}
            </NavLink>
          ))}
      </nav>
      <div className="cp-layout">
        <main id="cp-main" tabIndex={-1}>
          <AutonomousEntry />
          {!isOverview && <SourceContext />}
          {error && (
            <div className="cp-error" role="alert">
              Source connection unavailable.{" "}
              {data
                ? "Stale last-read records are retained with their timestamps."
                : "No source records were retrieved."}{" "}
              Refresh to retry.
            </div>
          )}
          {!error && freshness === "Stale" && (
            <div className="cp-error" role="status">
              These reads are over five minutes old. Refresh before relying on
              current state.
            </div>
          )}
          <WorkspaceBoundary key={location.pathname}>
            <Suspense fallback={<div role="status">Loading workspace…</div>}>
              {!host?.capabilities ? (
                <div role="status">
                  {host?.error || "Checking demo access…"}
                </div>
              ) : !routeAllowed(host.capabilities, location.pathname) ? (
                <Navigate to="/control/overview" replace />
              ) : (
                <Routes>
                  <Route
                    index
                    element={<Navigate to="/control/overview" replace />}
                  />
                  <Route path="overview" element={<Portfolio />} />
                  <Route
                    path="portfolio"
                    element={<Navigate to="/control/overview" replace />}
                  />
                  <Route path="programs" element={<Portfolio directory />} />
                  <Route path="programs/:programId" element={<ProgramPage />} />
                  <Route
                    path="programs/:programId/cases/:caseId"
                    element={<CasePage />}
                  />
                  <Route path="runs/:runId" element={<OperationsRun />} />
                  <Route
                    path="automations/:automationId"
                    element={<AutomationPage />}
                  />
                  <Route path="workflows" element={<Workflows />} />
                  <Route path="workflows/:workflowId" element={<Workflows />} />
                  <Route path="decisions" element={<Decisions />} />
                  <Route
                    path="decisions/evidence/:digest"
                    element={<EvidenceDecision />}
                  />
                  <Route
                    path="decisions/:proposalId/:version"
                    element={<DecisionReview />}
                  />
                  <Route path="scenarios" element={<Scenarios />} />
                  <Route path="knowledge" element={<Knowledge />} />
                  <Route path="operations" element={<Operations />} />
                  <Route
                    path="operations/demo"
                    element={<DemoControlsPage />}
                  />
                  <Route path="operations/evals" element={<Operations />} />
                  <Route
                    path="operations/sessions/:sessionId"
                    element={<OperationsSession />}
                  />
                  <Route
                    path="*"
                    element={
                      <Empty>
                        This page is not available.{" "}
                        <Link to="/control/overview">
                          Return to overview <ArrowRight size={15} />
                        </Link>
                      </Empty>
                    }
                  />
                </Routes>
              )}
            </Suspense>
          </WorkspaceBoundary>
          <footer className="cp-footer">
            <span>
              Stratos Silicon · Fictional enterprise
              <br />
              Demo identities · Not production authentication
            </span>
            <ReadStamp />
          </footer>
        </main>
      </div>
      <Concierge openRequest={conciergeRequest} />
    </div>
  );
}
export function ControlPlane() {
  const [profile, setProfile] = useState<Persona | null>(() => {
      const retained = sessionStorage.getItem("stratos:control-profile");
      if (retained === "automation" || retained === "engineer" || retained === "program_owner" || retained === "reader")
        return retained;
      return sessionStorage.getItem("stratos:demo-restart-operator") === "1"
        ? "automation"
        : null;
    }),
    [generation, setGeneration] = useState(0);
  useEffect(() => {
    sessionStorage.removeItem("stratos:demo-restart-operator");
  }, []);
  useEffect(() => {
    // Scoped opening reset invalidates every draft/action/read, while retaining
    // the selected demo persona. Full reset still remounts this component.
    const reset = () => setGeneration((n) => n + 1);
    window.addEventListener("stratos:demo-reset", reset);
    return () => window.removeEventListener("stratos:demo-reset", reset);
  }, []);
  const chooseProfile = (next: Persona | null) => {
    // Clear only control-plane invocation drafts; source app sessions are independent.
    for (const key of Object.keys(sessionStorage))
      if (
        key.startsWith("stratos.workflow-invocation.") ||
        key.startsWith("stratos.standard-invocation.") ||
        key.startsWith("stratos.quality.invocation") ||
        [
          "stratos-cr017-invocation",
          "stratos.quality.invocation",
          "stratos.delivery.invocation",
        ].includes(key)
      )
        sessionStorage.removeItem(key);
    if (next) sessionStorage.setItem("stratos:control-profile", next);
    else sessionStorage.removeItem("stratos:control-profile");
    setProfile(next);
    setGeneration((n) => n + 1);
    // Remount scoped reads, dialogs, chat and voice. Shell redirects forbidden routes.
  };
  return (
    <ControlData key={generation}>
      <HostData profile={profile}>
        <Shell profile={profile} onProfile={chooseProfile} />
      </HostData>
    </ControlData>
  );
}
