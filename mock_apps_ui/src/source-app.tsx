import { DeliverySource } from "./delivery-source";
import { QualitySource } from "./quality-source";
import { ValidationIntakes } from "./validation-intakes";
import React, { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  ArrowUpRight,
  BookOpen,
  CalendarDays,
  FileText,
  Factory,
  ListChecks,
  PackageSearch,
  Route as RouteIcon,
  Truck,
  Waypoints,
  Boxes,
  BriefcaseBusiness,
  ChevronRight,
  CircuitBoard,
  ClipboardList,
  FlaskConical,
  Grid2X2,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { personas, type Persona } from "./api";
import { DataProvider, useData } from "./data";
import { CaseOverview } from "./case-progress";
import { Engineering } from "./engineering";
import { Validation } from "./validation";
import { ERP, Manufacturing } from "./operations";
import { Programs } from "./programs";
import { Badge, Banner, date, Empty, Panel, SearchField, Table } from "./ui";
import "./style.css";
import "./source-suite.css";
const apps = [
  {
    path: "engineering",
    name: "Stratos PLM",
    short: "Engineering records",
    icon: CircuitBoard,
    subtitle: "Product Lifecycle & Engineering Change",
    summary: "Controlled changes, requirements and configuration records.",
    nav: [
      ["Change requests", "/engineering"],
      ["Controlled documents", "/engineering/documents"],
    ],
  },
  {
    path: "validation",
    name: "Stratos TestOps",
    short: "Test operations",
    icon: FlaskConical,
    subtitle: "Validation & Qualification",
    summary: "Validation jobs, samples, resources and test evidence.",
    nav: [
      ["Overview & evidence", "/validation"],
      ["Validation options", "/validation/options"],
      ["Sample inventory", "/validation/samples"],
      ["Lab schedule", "/validation/schedule"],
      ["Jobs queue", "/validation/jobs"],
      ["Operations intake", "/validation/intakes"],
      ["Execution history", "/validation/history"],
    ],
  },
  {
    path: "manufacturing",
    name: "Stratos MES",
    short: "Production & quality",
    icon: Boxes,
    subtitle: "Manufacturing & Quality",
    summary: "Lots, material holds, yield exceptions and traceability.",
    nav: [
      ["Operations / units", "/manufacturing"],
      ["Source lots", "/manufacturing/lots"],
      ["Quality exceptions", "/manufacturing/quality/QE-004"],
      ["QE-011 source event", "/manufacturing/quality/QE-011"],
      ["Delivery material", "/manufacturing/delivery/DR-009"],
    ],
  },
  {
    path: "erp",
    name: "Stratos ERP",
    short: "Commercial operations",
    icon: BriefcaseBusiness,
    subtitle: "Commercial, Orders & Supply",
    summary: "Customer orders, eligible supply and commercial commitments.",
    nav: [
      ["Customer orders", "/erp"],
      ["Supply & commitments", "/erp/delivery/DR-009"],
      ["Validation cost rates", "/erp/rates"],
    ],
  },
  {
    path: "programs",
    name: "Stratos ProgramOps",
    short: "Program planning",
    icon: ClipboardList,
    subtitle: "Program Planning & Readiness",
    summary: "Program milestones, dependencies and recovery work.",
    nav: [
      ["Portfolio", "/programs"],
      ["Recovery tasks", "/programs/quality/QE-004"],
      ["Delivery readiness", "/programs/delivery/DR-009"],
    ],
  },
];
const navIcon = (path: string) =>
  path.includes("documents")
    ? BookOpen
    : path.includes("quality")
      ? ShieldCheck
      : path.includes("delivery")
        ? Truck
        : path.includes("schedule")
          ? CalendarDays
          : path.includes("samples") || path.includes("lots")
            ? PackageSearch
            : path.includes("jobs") || path.includes("intakes")
              ? ListChecks
              : path.includes("history")
                ? RouteIcon
                : path.includes("options")
                  ? FileText
                  : path.includes("manufacturing")
                    ? Factory
                    : path.includes("programs")
                      ? Waypoints
                      : ClipboardList;

function App() {
  const { data, persona, setPersona, refresh, loading, error, fetchedAt } =
    useData();
  const location = useLocation(),
    navigate = useNavigate();
  const current = apps.find((a) => location.pathname.split("/")[1] === a.path);
  useEffect(() => {
    if (!location.hash) window.scrollTo(0, 0);
  }, [location.pathname, location.hash]);
  useEffect(() => {
    document.title = current
      ? current.name + " · Synthetic enterprise"
      : "Enterprise applications · Synthetic demo";
  }, [current]);
  useEffect(() => {
    if (location.hash && data) {
      document
        .getElementById(decodeURIComponent(location.hash.slice(1)))
        ?.scrollIntoView({ block: "start" });
    }
  }, [location.pathname, location.hash, data]);
  return (
    <div className={"app-shell " + (current?.path || "launcher")}>
      <aside className="sidebar">
        <Link className="brand" to="/">
          <div className="brand-mark">
            <CircuitBoard size={25} />
          </div>
          <span>
            {data?.programs[0]?.supplier_name || "Source systems"}
            <small>
              {data?.programs[0]?.business_unit || "Enterprise workspace"}
            </small>
          </span>
        </Link>
        <label className="app-switch-label">
          APPLICATION
          <select
            aria-label="App switcher"
            value={current?.path || ""}
            onChange={(e) => navigate("/" + e.target.value)}
          >
            <option value="">All applications</option>
            {apps.map((a) => (
              <option value={a.path} key={a.path}>
                {a.name}
              </option>
            ))}
          </select>
        </label>
        <div className="sidebar-rule" />
        <div className="navigation-label">{current?.short || "Workspace"}</div>
        <nav>
          {current
            ? current.nav.map(([label, path]) => {
                const Icon = navIcon(path);
                return (
                  <NavLink end key={path} to={path}>
                    <Icon size={17} />
                    <span>{label}</span>
                    <ChevronRight className="source-nav-chevron" size={13} />
                  </NavLink>
                );
              })
            : apps.map((a) => (
                <NavLink key={a.path} to={"/" + a.path}>
                  <a.icon size={18} />
                  <span>{a.name}</span>
                </NavLink>
              ))}
        </nav>
        {current && (
          <div className="app-tab-link">
            <a
              href={location.pathname + location.search}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open app in new tab
              <ArrowUpRight size={15} />
            </a>
          </div>
        )}
        <div className="sidebar-footer">
          <ShieldCheck size={18} />
          <div>
            Synthetic enterprise demo
            <small>
              Local mock identities
              <br />
              No production authentication
            </small>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span className="app-title">
            {current ? (
              <>
                <current.icon size={20} />
                <span>
                  {current.name}
                  <small>{current.subtitle}</small>
                </span>
              </>
            ) : (
              <>
                <Grid2X2 size={20} />
                Applications
              </>
            )}
          </span>
          <div className="top-actions">
            <label>
              Simulated persona
              <select
                aria-label="Simulated persona"
                value={persona}
                onChange={(e) => setPersona(e.target.value as Persona)}
              >
                {Object.entries(personas).map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="refresh"
              onClick={() => void refresh()}
              disabled={loading}
              aria-label="Refresh"
            >
              <RefreshCw size={16} className={loading ? "spin" : ""} />
              Refresh
            </button>
          </div>
        </header>
        <div className="contextbar">
          <span>
            {data ? `${data.programs.length} programs` : "Authorized workspace"}
            <span className="context-divider">/</span>
            {data?.programs[0]?.business_unit || "Connecting to local API"}
          </span>
          <span>
            Scenario{" "}
            {data ? date(data.programs[0]?.scenario_at) : "loading"}{" "}
          </span>
        </div>
        <main>
          {error && (
            <Banner tone="danger">
              {error}{" "}
              {data
                ? "Last retrieved records are shown; actions are unavailable until refresh succeeds."
                : ""}
            </Banner>
          )}
          {!data ? (
            loading ? (
              <Empty>Loading persisted enterprise records…</Empty>
            ) : (
              <Empty>
                Business data is unavailable. Start the local backend and use
                Refresh.
              </Empty>
            )
          ) : (
            <Routes>
              <Route path="/" element={<Launcher />} />
              <Route path="/engineering" element={<Engineering />} />
              <Route path="/engineering/documents" element={<Documents />} />
              <Route
                path="/engineering/documents/:documentId"
                element={<Engineering />}
              />
              <Route
                path="/engineering/changes/:changeId/*"
                element={<Engineering />}
              />
              <Route
                path="/engineering/plans/:planId"
                element={<Engineering />}
              />
              <Route path="/validation" element={<Validation />} />
              <Route
                path="/validation/intakes"
                element={<ValidationIntakes />}
              />
              <Route
                path="/validation/intakes/:intakeId"
                element={<ValidationIntakes />}
              />
              <Route path="/validation/:screen" element={<Validation />} />
              <Route
                path="/validation/results/:resultId"
                element={<Validation />}
              />
              <Route path="/validation/jobs/:jobId" element={<Validation />} />
              <Route
                path="/validation/history/:historyId"
                element={<Validation />}
              />
              {[
                "manufacturing",
                "engineering",
                "validation",
                "programs",
                "erp",
              ].map((system) => (
                <Route
                  key={system}
                  path={`/${system}/quality/:exceptionId`}
                  element={<QualitySource />}
                />
              ))}
              {[
                "manufacturing",
                "engineering",
                "validation",
                "programs",
                "erp",
              ].map((system) => (
                <Route
                  key={`delivery-${system}`}
                  path={`/${system}/delivery/DR-009`}
                  element={<DeliverySource />}
                />
              ))}
              <Route path="/manufacturing" element={<Manufacturing />} />
              <Route
                path="/manufacturing/:screen"
                element={<Manufacturing />}
              />
              <Route
                path="/manufacturing/units/:unitId"
                element={<Manufacturing />}
              />
              <Route
                path="/manufacturing/lots/:lotId"
                element={<Manufacturing />}
              />
              <Route path="/erp" element={<ERP />} />
              <Route path="/erp/:screen" element={<ERP />} />
              <Route path="/erp/orders/:orderId" element={<ERP />} />
              <Route path="/programs" element={<Programs />} />
              <Route path="/programs/:programId" element={<Programs />} />
              <Route
                path="/programs/:programId/milestones/:milestoneId"
                element={<Programs />}
              />
              <Route
                path="*"
                element={
                  <Empty>
                    Page not found.{" "}
                    <Link to="/">Open application launcher</Link>.
                  </Empty>
                }
              />
            </Routes>
          )}
        </main>
        <footer className="page-footer">
          <span>
            Mock identity: demo-portfolio-{persona} ·{" "}
            {persona === "automation"
              ? "automation API role"
              : persona + " API role"}
          </span>
          <span aria-live="polite">
            {loading
              ? "Refreshing from APIs…"
              : fetchedAt
                ? "Last API refresh " + date(fetchedAt)
                : "No successful API refresh"}
          </span>
        </footer>
      </div>
    </div>
  );
}
function Launcher() {
  const { data } = useData();
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">Source-system applications</div>
          <h1>{data!.programs[0]?.supplier_name}</h1>
          <p>{data!.programs[0]?.business_unit}</p>
        </div>
      </div>
      {data!.cases.slice(0, 1).map((c) => (
        <CaseOverview key={c.change.id} c={c} />
      ))}
      <div className="launcher-grid">
        {apps.map((a) => (
          <section className={"app-card " + a.path} key={a.path}>
            <a.icon size={25} />
            <h2>{a.name}</h2>
            <p>{a.summary}</p>
            <div>
              <Link className="button primary" to={"/" + a.path}>
                Open application
              </Link>
              <a
                className="icon-link"
                href={"/" + a.path}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={"Open " + a.name + " in new tab"}
              >
                <ArrowUpRight size={20} />
              </a>
            </div>
          </section>
        ))}
      </div>
      <Banner>
        Use the explicit persona selector in each tab. Program operators draft
        and schedule work; engineering approvers record decisions. All apps read
        the same persisted business state.
      </Banner>
    </>
  );
}
function Documents() {
  const { data } = useData();
  const [search, setSearch] = useState("");
  const documents = data!.documents.filter((d) =>
    `${d.id} ${d.title || ""} ${d.document_type}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">PLM / Controlled library</div>
          <h1>Controlled documents</h1>
          <p>Versioned requirements, procedures and supporting publications.</p>
        </div>
      </div>
      <div className="toolbar">
        <SearchField
          value={search}
          onChange={setSearch}
          label="Search documents"
        />
      </div>
      <Panel
        title="Document register"
        aside={<span className="metadata">{documents.length} records</span>}
      >
        <Table headers={["Document / title", "Type", "Version", "Status"]}>
          {documents.map((d) => (
            <tr key={d.id}>
              <td>
                <Link
                  className="record-link"
                  to={"/engineering/documents/" + d.id}
                >
                  {d.id}
                </Link>
                <span className="cell-secondary">{d.title}</span>
              </td>
              <td>{d.document_type.replaceAll("_", " ")}</td>
              <td>{d.document_version}</td>
              <td>
                <Badge value={d.status} />
              </td>
            </tr>
          ))}
        </Table>
        {!documents.length && <Empty>No documents match this search.</Empty>}
      </Panel>
    </>
  );
}

export function SourceApps() {
  return (
    <DataProvider>
      <App />
    </DataProvider>
  );
}
