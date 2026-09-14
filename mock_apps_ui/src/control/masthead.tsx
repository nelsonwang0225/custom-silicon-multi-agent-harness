import { CHOOSE_IDENTITY, IdentityChoices, identityDetails } from "./persona";
import { MasterReset } from "./master-reset";
import {
  useOperations,
  operationsSearch,
  operationsAlerts,
} from "./operations-data";
import { useHost } from "./host";
import { hostSearch, hostAlerts } from "./host-presentation";
import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Link, routeAllowed } from "./access";
import {
  Search,
  Bell,
  UserRound,
  ArrowUpRight,
  ArrowRight,
  MessageSquare,
  X,
  Check,
} from "lucide-react";
import { personas, type Persona } from "../api";
import { date, useControl } from "./data";
import { Dialog, MODAL_OPEN } from "./dialog";
import { AgentDetails, agentRoles } from "./agent-activity";
import {
  matchSearch,
  searchIndex,
  sourceAlerts,
  type SearchRecord,
} from "./presentation-model";
export type ConciergeRequest = {
  id: number;
  query: string;
  context: string;
  origin?: "agent";
};
export function Masthead({
  profile,
  onProfile,
  ask,
}: {
  profile: Persona | null;
  onProfile: (p: Persona | null) => void;
  ask: (query: string) => void;
}) {
  const host = useHost();
  const { data, error, freshness } = useControl(),
    location = useLocation(),
    navigate = useNavigate();
  const [panel, setPanel] = useState<"search" | "alerts" | "profile" | null>(
      null,
    ),
    [query, setQuery] = useState(""),
    [access, setAccess] = useState(false),
    [agent, setAgent] = useState<string | null>(null);
  const [recommended, setRecommended] = useState<Persona[]>([]);
  useEffect(() => {
    const open = (e: Event) => {
      setRecommended((e as CustomEvent<Persona[]>).detail || []);
      setPanel(null);
      setAccess(true);
    };
    window.addEventListener(CHOOSE_IDENTITY, open);
    return () => window.removeEventListener(CHOOSE_IDENTITY, open);
  }, []);
  const [readIds, setReadIds] = useState<Set<string>>(new Set());
  const activePanel = useRef(panel);
  activePanel.current = panel;
  const header = useRef<HTMLElement>(null),
    input = useRef<HTMLInputElement>(null),
    bell = useRef<HTMLButtonElement>(null),
    account = useRef<HTMLButtonElement>(null);
  const operations = useOperations(panel === "search" || panel === "alerts");
  const results = matchSearch(
      [
        ...searchIndex(data, host?.data?.workflows),
        ...hostSearch(host?.data || null).filter(
          (r) => r.group !== "Recorded runs" || !operations.data,
        ),
        ...operationsSearch(operations.data),
      ].filter((r) =>
        r.to ? routeAllowed(host?.capabilities, r.to) : !!host?.capabilities,
      ),
      query,
    ),
    groups = [...new Set(results.map((r) => r.group))];
  const connectedIds = new Set(
    host?.data?.case_summaries?.map((c) => c.change_id),
  );
  const alerts = [
      ...new Map(
        [
          ...(host?.error
            ? [
                {
                  id: "host/connection",
                  title: "Connected workflow state unavailable",
                  context: "Refresh current sources before acting",
                  to: "/control/operations",
                  kind: "host",
                  priority: 0,
                },
              ]
            : hostAlerts(host?.data || null)),
          ...operationsAlerts(operations.data),
          ...sourceAlerts(data).filter(
            (a) => !a.caseId || !connectedIds.has(a.caseId),
          ),
        ].map((a) => [a.id, a]),
      ).values(),
    ]
      .filter((a) => routeAllowed(host?.capabilities, a.to))
      .sort((a, b) => (a.priority ?? 80) - (b.priority ?? 80)),
    unread = alerts.filter((a) => !readIds.has(a.id)).length;
  const role = agentRoles.find((r) => r.id === agent);
  const dismiss = (focus = false) => {
    if (focus)
      (panel === "search"
        ? input
        : panel === "alerts"
          ? bell
          : account
      ).current?.focus();
    setPanel(null);
  };
  const reveal = (next: typeof panel) => {
    if (document.querySelector(".cp-root dialog[open]")) return;
    // Shared focus-task notification also stops dictation before a popover opens.
    window.dispatchEvent(new Event(MODAL_OPEN));
    setPanel(next);
  };
  useEffect(() => {
    setPanel(null);
    setQuery("");
  }, [location.pathname, location.search]);
  useEffect(() => {
    const outside = (e: PointerEvent) => {
      if (!header.current?.contains(e.target as Node)) setPanel(null);
    };
    const modal = () => setPanel(null);
    const key = (e: KeyboardEvent) => {
      if (
        e.key === "Escape" &&
        activePanel.current &&
        !document.querySelector(".cp-root dialog[open]")
      ) {
        e.preventDefault();
        (activePanel.current === "search"
          ? input
          : activePanel.current === "alerts"
            ? bell
            : account
        ).current?.focus();
        setPanel(null);
        return;
      }
      if (
        (e.metaKey || e.ctrlKey) &&
        e.key.toLowerCase() === "k" &&
        !document.querySelector(".cp-root dialog[open]")
      ) {
        e.preventDefault();
        reveal("search");
        input.current?.focus();
      }
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", key);
    window.addEventListener(MODAL_OPEN, modal);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", key);
      window.removeEventListener(MODAL_OPEN, modal);
    };
  }, []);
  const choose = (item: SearchRecord) => {
    input.current?.focus();
    setPanel(null);
    if (item.agent) setAgent(item.agent);
    else if (item.to) navigate(item.to);
  };
  const askQuery = () => {
    dismiss();
    ask(query.trim());
  };
  const alertRow = (a: (typeof alerts)[number]) => (
    <article key={a.id} data-alert-id={a.id}>
      <strong>{a.title}</strong>
      <small>{a.context}</small>
      {a.time && <small>Source updated {date(a.time, true)}</small>}
      <div>
        <Link to={a.to}>
          Inspect <ArrowRight size={14} />
        </Link>
        {readIds.has(a.id) ? (
          <span>
            <Check size={14} /> Read
          </span>
        ) : (
          <button onClick={() => setReadIds((all) => new Set([...all, a.id]))}>
            Mark read
          </button>
        )}
      </div>
    </article>
  );
  const initials = profile
    ? personas[profile]
        .split(" ")
        .map((w) => w[0])
        .join("")
        .slice(0, 2)
    : "";
  return (
    <header
      className="cp-header"
      ref={header}
      onKeyDown={(e) => {
        if (e.key === "Escape" && panel) {
          e.preventDefault();
          e.stopPropagation();
          dismiss(true);
        }
      }}
      onBlur={(e) => {
        if (e.relatedTarget && !e.currentTarget.contains(e.relatedTarget))
          setPanel(null);
      }}
    >
      <div className="cp-masthead-brand">
        <Link
          className="cp-brand"
          to="/control/overview"
          aria-label="Stratos Silicon overview"
        >
          <span className="cp-brand-symbol" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span>
            STRATOS<span className="cp-brand-sub">SILICON</span>
          </span>
        </Link>
        <span className="cp-product-name">Program control plane</span>
      </div>
      <div className="cp-global-search">
        <Search size={19} aria-hidden="true" />
        <input
          ref={input}
          aria-label="Search Stratos"
          placeholder="Search Stratos..."
          aria-expanded={panel === "search"}
          aria-controls={panel === "search" ? "cp-search-panel" : undefined}
          aria-haspopup="dialog"
          value={query}
          onFocus={() => {
            if (panel !== "search") reveal("search");
          }}
          onChange={(e) => {
            setQuery(e.target.value);
            if (panel !== "search") reveal("search");
          }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              header.current
                ?.querySelector<HTMLButtonElement>("#cp-search-panel button")
                ?.focus();
            }
            if (e.key === "Enter") {
              e.preventDefault();
              reveal("search");
            }
          }}
        />
        <kbd aria-hidden="true">⌘ / Ctrl K</kbd>
        {panel === "search" && (
          <section
            id="cp-search-panel"
            className="cp-popover cp-search-panel"
            role="dialog"
            aria-label="Search results"
            onKeyDown={(e) => {
              if (!["ArrowDown", "ArrowUp"].includes(e.key)) return;
              e.preventDefault();
              const buttons = Array.from(
                e.currentTarget.querySelectorAll<HTMLButtonElement>("button"),
              );
              const index = buttons.indexOf(
                document.activeElement as HTMLButtonElement,
              );
              buttons[
                (index + (e.key === "ArrowDown" ? 1 : buttons.length - 1)) %
                  buttons.length
              ]?.focus();
            }}
          >
            <div className="cp-popover-heading">
              <strong>Search Stratos</strong>
              <button aria-label="Close search" onClick={() => dismiss(true)}>
                <X size={18} />
              </button>
            </div>
            <p className="cp-search-coverage">
              {data
                ? `${freshness} · Accessible record metadata & definitions`
                : "Source metadata unavailable · Definitions only"}
            </p>
            <div className="cp-search-results">
              {groups.map((group) => (
                <section key={group} aria-label={group}>
                  <h3>{group}</h3>
                  {results
                    .filter((r) => r.group === group)
                    .map((item) => (
                      <button
                        key={item.id}
                        onClick={() => choose(item)}
                        className="cp-search-result"
                      >
                        <span>
                          <strong>{item.title}</strong>
                          <small>
                            {item.context} · {item.mode}
                          </small>
                        </span>
                        <ArrowUpRight size={17} />
                      </button>
                    ))}
                </section>
              ))}
              {!results.length && (
                <p className="cp-search-empty">
                  No matches in the available metadata.
                </p>
              )}
            </div>
            <button className="cp-search-ask" onClick={askQuery}>
              <MessageSquare size={20} />
              <span>
                {query.trim()
                  ? `Ask Stratos Concierge about “${query.trim()}”`
                  : "Open Stratos Concierge"}
              </span>
              <ArrowRight size={17} />
            </button>
            <details className="cp-search-limits">
              <summary>Search coverage</summary>
              <p>
                Titles, IDs and customer/context metadata from current
                accessible reads; workflow and agent definitions. Document
                bodies are not indexed. Recorded proposals, decisions, runs,
                trace IDs, Concierge sessions, eval results and automation
                configurations are included when the host is available. Business
                cases appear before technical activity. Queries never execute
                work.
              </p>
            </details>
          </section>
        )}
      </div>
      <div className="cp-header-actions">
        <div className="cp-utility">
          <button
            ref={bell}
            className="cp-bell"
            aria-label={
              error || !data ? "Alerts unavailable" : `Alerts, ${unread} unread`
            }
            aria-expanded={panel === "alerts"}
            aria-controls={panel === "alerts" ? "cp-alerts-panel" : undefined}
            onClick={() => (panel === "alerts" ? dismiss() : reveal("alerts"))}
          >
            <Bell size={21} />
            {!error && data && unread > 0 && (
              <span className="cp-unread-count">{unread}</span>
            )}
          </button>
          {panel === "alerts" && (
            <section
              id="cp-alerts-panel"
              className="cp-popover cp-alerts-panel"
              role="dialog"
              aria-label="Source alerts"
            >
              <div className="cp-popover-heading">
                <strong>Alerts</strong>
                <button aria-label="Close alerts" onClick={() => dismiss(true)}>
                  <X size={18} />
                </button>
              </div>
              <p>
                Source signals · {freshness}. Read status is for this visit.
              </p>
              {error || !data ? (
                <p role="status">
                  Alerts unavailable. Refresh source records to retry.
                </p>
              ) : (
                <>
                  <div className="cp-alert-list">
                    {alerts.slice(0, 6).map(alertRow)}
                    {alerts.length > 6 && (
                      <details className="cp-more-alerts">
                        <summary>More alerts ({alerts.length - 6})</summary>
                        {alerts.slice(6).map(alertRow)}
                      </details>
                    )}

                    {!alerts.length && <p>No current source alerts.</p>}
                  </div>
                  {unread > 0 && (
                    <button
                      onClick={() =>
                        setReadIds(new Set(alerts.map((a) => a.id)))
                      }
                    >
                      Mark all read
                    </button>
                  )}
                </>
              )}
            </section>
          )}
        </div>
        <MasterReset />
        <div className="cp-utility">
          <button
            ref={account}
            className="cp-account"
            aria-label={profile ? "Demo profile" : "Log in"}
            aria-expanded={panel === "profile" || access}
            onClick={() => {
              if (profile) panel === "profile" ? dismiss() : reveal("profile");
              else {
                dismiss();
                setAccess(true);
              }
            }}
          >
            {profile ? (
              <>
                <span className="cp-avatar">{initials}</span>
                <span className="cp-active-identity">
                  <strong>{personas[profile]}</strong>
                  <small>{identityDetails[profile].name}</small>
                </span>
              </>
            ) : (
              <>
                <UserRound size={20} />
                <span>Log in</span>
              </>
            )}
          </button>
          {panel === "profile" && profile && (
            <section
              className="cp-popover cp-profile-panel"
              role="dialog"
              aria-label="Demo profile"
            >
              <div className="cp-popover-heading">
                <strong>{personas[profile]}</strong>
                <button
                  aria-label="Close profile"
                  onClick={() => dismiss(true)}
                >
                  <X size={18} />
                </button>
              </div>
              <p>
                Demo identity ·{" "}
                {profile === "automation" ? "automation" : profile} role
              </p>
              <small>
                {identityDetails[profile].purpose}{" "}
                {identityDetails[profile].boundary}
              </small>
              <button
                onClick={() => {
                  dismiss();
                  account.current?.focus();
                  setAccess(true);
                }}
              >
                Switch profile
              </button>
              <button onClick={() => onProfile(null)}>Exit demo</button>
            </section>
          )}
        </div>
        <Link to="/" className="cp-source-switch">
          Source apps <ArrowUpRight size={14} />
        </Link>
      </div>
      {access && (
        <Dialog
          title="Demo access"
          note="Synthetic demo identities · Role checks apply"
          close={() => setAccess(false)}
          closeLabel="Close demo access"
        >
          <div className="cp-demo-access">
            <p>
              Choose an existing demo identity. Each role has different
              authority; switching does not approve or execute work.
            </p>
            <IdentityChoices
              profile={profile}
              onProfile={onProfile}
              recommended={recommended}
            />
            <p className="cp-caption">
              Synthetic demo identities, not production authentication. The host
              checks every action. Switching clears local drafts and voice while
              retaining this page. Quality disposition remains with
              Manufacturing; no hold-release control is installed.
            </p>
          </div>
        </Dialog>
      )}
      {role && (
        <AgentDetails
          role={role}
          scope="Accessible workspace · Definition only"
          close={() => setAgent(null)}
        />
      )}
    </header>
  );
}
