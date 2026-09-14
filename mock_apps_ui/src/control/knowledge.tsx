import { KnowledgeRunEvidence, type KnowledgeEvent } from "./knowledge-runs";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search,
  FileText,
  Database,
  ArrowRight,
  BookOpen,
  Network,
} from "lucide-react";
import { Link } from "./access";
import { agentName } from "./trace-language";
import "./rethink-utilities.css";
import { useHost, type HostSchema } from "./host";
import { DEMO_CHANGED } from "../demo-epoch";
import { DocumentContent } from "./previews";
import {
  Drawer,
  Empty,
  Facts,
  Heading,
  Section,
  SourceLink,
  StatusText,
} from "./ui";
import { words } from "./data";
import "./knowledge.css";
type Status = HostSchema["IndexStatus"];
type Result = HostSchema["KnowledgeResult"];
type Response = HostSchema["SearchResponse"];
type Verification = HostSchema["Verification"];
const knowledgeCategories = [
  "All knowledge",
  "Policies & procedures",
  "Request context",
  "Historical",
] as const;
function knowledgeCategory(document: Status["documents"][number]) {
  if (document.metadata.historical) return "Historical";
  return /(?:^|_)(policy|procedure|playbook|sop)(?:$|_)/.test(
    document.metadata.document_type.toLowerCase(),
  )
    ? "Policies & procedures"
    : "Request context";
}
const profiles = [
  "CHANGE_IMPACT",
  "VALIDATION_EVIDENCE",
  "MANUFACTURING_QUALITY",
  "PROGRAM_COMMERCIAL",
] as const;
export function Knowledge() {
  const host = useHost()!,
    read = host?.read,
    act = host?.act;
  const [params, setParams] = useSearchParams();
  const [events, setEvents] = useState<KnowledgeEvent[]>([]);
  const [usedOnly, setUsedOnly] = useState(false);
  const [category, setCategory] =
    useState<(typeof knowledgeCategories)[number]>("All knowledge");
  const [programFilter, setProgramFilter] = useState("");
  const [approvalFilter, setApprovalFilter] = useState("");
  const [status, setStatus] = useState<Status | null>(null);
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const questionInput = useRef<HTMLInputElement>(null);
  const [profile, setProfile] = useState<(typeof profiles)[number]>(
    "VALIDATION_EVIDENCE",
  );
  const [historical, setHistorical] = useState(false);
  const [prior, setPrior] = useState(false);
  const [response, setResponse] = useState<Response | null>(null);
  const [selected, setSelected] = useState<Result | null>(null);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [confirm, setConfirm] = useState(false);
  const serial = useRef(0),
    alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    const token = ++serial.current;
    setStatus(null);
    setEvents([]);
    if (read)
      read<KnowledgeEvent[]>("/knowledge/events")
        .then((v) => {
          if (alive.current && token === serial.current) setEvents(v);
        })
        .catch(() => {});
    setResponse(null);
    setSelected(null);
    setVerification(null);
    setError("");
    if (read)
      read<Status>("/knowledge")
        .then((v) => {
          if (alive.current && token === serial.current) setStatus(v);
        })
        .catch((e) => {
          if (alive.current && token === serial.current) setError(e.message);
        });
    const reset = () => {
      const resetToken = ++serial.current;
      setResponse(null);
      setSelected(null);
      setVerification(null);
      setStatus(null);
      setBusy("");
      setConfirm(false);
      void read?.<Status>("/knowledge")
        .then((v) => {
          if (alive.current && resetToken === serial.current) setStatus(v);
        })
        .catch((e) => {
          if (alive.current && resetToken === serial.current)
            setError(e.message);
        });
    };
    window.addEventListener(DEMO_CHANGED, reset);
    return () => {
      alive.current = false;
      ++serial.current;
      window.removeEventListener(DEMO_CHANGED, reset);
    };
  }, [read]);
  async function search() {
    if (!act || busy || !query.trim()) return;
    const token = ++serial.current;
    setBusy("Searching");
    setError("");
    setResponse(null);
    setSelected(null);
    try {
      const v = await act<Response>("/knowledge/search", {
        query: query.trim(),
        retrieval_profile: profile,
        metadata_filters: {
          include_historical: historical,
          include_prior_versions: prior,
        },
      });
      if (alive.current && token === serial.current) setResponse(v);
    } catch (e) {
      if (alive.current && token === serial.current)
        setError((e as Error).message);
    } finally {
      if (alive.current && token === serial.current) setBusy("");
    }
  }
  async function reindex() {
    if (!act || busy) return;
    const token = ++serial.current;
    setBusy("Indexing");
    setError("");
    setResponse(null);
    try {
      const v = await act<Status>("/knowledge/reindex", {
        confirm: "REINDEX KNOWLEDGE",
      });
      if (alive.current && token === serial.current) {
        setStatus(v);
        setConfirm(false);
      }
    } catch (e) {
      if (alive.current && token === serial.current)
        setError((e as Error).message);
    } finally {
      if (alive.current && token === serial.current) setBusy("");
    }
  }
  async function inspect(result: Result) {
    if (!read) return;
    const token = ++serial.current;
    setSelected(result);
    setVerification(null);
    setError("");
    try {
      const v = await read<Verification>(
        `/knowledge/verify/${encodeURIComponent(result.chunk_id)}`,
      );
      if (alive.current && token === serial.current) setVerification(v);
    } catch (e) {
      if (alive.current && token === serial.current)
        setError((e as Error).message);
    }
  }
  const chunkId = params.get("chunk");
  useEffect(() => {
    let active = true;
    if (chunkId && read)
      read<Result>(`/knowledge/passages/${encodeURIComponent(chunkId)}`)
        .then((v) => {
          if (active) void inspect(v);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [chunkId, read]);
  const used = new Set(
    events.flatMap((e) =>
      (e.passages || [])
        .filter((p) => p.used_in_finding && e.run_id)
        .map((p) => p.document_id),
    ),
  );
  const docId = params.get("document"),
    filter = (params.get("q") || "").toLowerCase();
  const documents =
    status?.documents.filter(
      (d) =>
        (!usedOnly || used.has(d.metadata.document_id)) &&
        (category === "All knowledge" || knowledgeCategory(d) === category) &&
        (!programFilter || d.metadata.program_id === programFilter) &&
        (!approvalFilter || d.metadata.approval_status === approvalFilter) &&
        `${d.metadata.title} ${d.metadata.document_id} ${d.metadata.document_type} ${d.metadata.program_id}`
          .toLowerCase()
          .includes(filter),
    ) || [];
  const recentCitation = events
    .flatMap((event) =>
      (event.passages || [])
        .filter((passage) => passage.used_in_finding && event.run_id)
        .map((passage) => ({ event, passage })),
    )
    .sort((a, b) => b.event.at.localeCompare(a.event.at))[0];
  return (
    <div className="rt-utilities rt-knowledge">
      <Heading
        eyebrow="Knowledge & evidence"
        title="Knowledge & Evidence"
        description="Find the evidence behind a recommendation. Check its source, version and intended use."
        action={
          <button
            onClick={() => {
              setSearchOpen(true);
              requestAnimationFrame(() => questionInput.current?.focus());
            }}
          >
            <Search size={16} aria-hidden="true" /> Search evidence
          </button>
        }
      />
      {error && (
        <p className="cp-error" role="alert">
          {error}
        </p>
      )}
      <Section
        title="From source to finding"
        className="rt-knowledge-path"
        note="Operational records establish the facts. Controlled documents explain the rules. The recorded finding shows how the agent used them."
      >
        <div className="rt-evidence-path">
          <div>
            <Database size={22} aria-hidden="true" />
            <small>Source</small>
            <strong>
              {recentCitation
                ? words(recentCitation.passage.metadata.source_system)
                : "Current business records"}
            </strong>
            <span>
              {recentCitation
                ? `v${recentCitation.passage.document_version} · ${["verified", "exact_source_verified"].includes(recentCitation.passage.verification_state) ? "Exact version checked" : `Source check: ${words(recentCitation.passage.verification_state)}`}`
                : "Exact record and version"}
            </span>
          </div>
          <ArrowRight className="rt-path-arrow" size={20} aria-hidden="true" />
          <div>
            <BookOpen size={22} aria-hidden="true" />
            <small>Knowledge</small>
            {recentCitation ? (
              <Link
                to={`/control/knowledge?chunk=${encodeURIComponent(recentCitation.passage.chunk_id)}`}
              >
                {recentCitation.passage.title}
              </Link>
            ) : (
              <strong>Scoped policy and evidence</strong>
            )}
            <span>
              {recentCitation
                ? `${words(recentCitation.passage.metadata.approval_status)} · ${recentCitation.passage.metadata.historical ? "Historical context" : "Inspect source applicability"}`
                : "Approval and applicability matter"}
            </span>
          </div>
          <ArrowRight className="rt-path-arrow" size={20} aria-hidden="true" />
          <div>
            <Network size={22} aria-hidden="true" />
            <small>Finding</small>
            <strong>
              {recentCitation
                ? `Cited by ${agentName(recentCitation.event.specialist)}`
                : "A traceable conclusion"}
            </strong>
            {recentCitation ? (
              <Link to={`/control/runs/${recentCitation.event.run_id}`}>
                Open recorded finding <ArrowRight size={14} />
              </Link>
            ) : (
              <span>No cited run is available yet</span>
            )}
          </div>
        </div>
      </Section>
      <Section
        title="Document library"
        note="Approved, historical and request material stay distinct."
        action={
          <span className="rt-result-count">
            {status
              ? `${documents.length} documents`
              : error
                ? "Library unavailable"
                : "Reading library…"}
          </span>
        }
      >
        <div
          className="rt-segmented"
          role="group"
          aria-label="Knowledge categories"
        >
          {knowledgeCategories.map((value) => (
            <button
              key={value}
              aria-pressed={category === value}
              onClick={() => setCategory(value)}
            >
              {value}
            </button>
          ))}
        </div>
        <div className="kn-library-tools">
          <label className="rt-filter">
            <span>Program</span>
            <select
              value={programFilter}
              onChange={(event) => setProgramFilter(event.target.value)}
            >
              <option value="">All programs</option>
              {[
                ...new Set(
                  status?.documents.map(
                    (document) => document.metadata.program_id,
                  ) || [],
                ),
              ]
                .sort()
                .map((program) => (
                  <option key={program} value={program}>
                    {program}
                  </option>
                ))}
            </select>
          </label>
          <label className="rt-filter">
            <span>Approval</span>
            <select
              value={approvalFilter}
              onChange={(event) => setApprovalFilter(event.target.value)}
            >
              <option value="">All statuses</option>
              {[
                ...new Set(
                  status?.documents.map(
                    (document) => document.metadata.approval_status,
                  ) || [],
                ),
              ]
                .sort()
                .map((approval) => (
                  <option key={approval} value={approval}>
                    {words(approval)}
                  </option>
                ))}
            </select>
          </label>
          <input
            className="kn-library-search"
            aria-label="Search evidence documents"
            placeholder="Search title, type, ID or program"
            value={params.get("q") || ""}
            onChange={(e) => setParams({ q: e.target.value })}
          />
          <label className="cp-inline kn-run-filter">
            <input
              type="checkbox"
              checked={usedOnly}
              onChange={(e) => setUsedOnly(e.target.checked)}
            />
            Used in agent runs
          </label>
        </div>
        {!status && !error && <Empty>Reading the controlled library…</Empty>}
        <div className="cp-case-list kn-library-list">
          {documents.length > 0 && (
            <div className="kn-library-header" aria-hidden="true">
              <span>Document</span>
              <span>Type</span>
              <span>Version</span>
              <span>Approval</span>
            </div>
          )}
          {documents.map(({ metadata: m, current, superseded }) => (
            <button
              className="kn-library-row"
              key={`${m.document_id}:${m.document_version}`}
              onClick={() => setParams({ q: filter, document: m.document_id })}
            >
              <span className="kn-library-document">
                <FileText size={18} />
                <span>
                  <strong>{m.title}</strong>
                  <small>{m.document_id}</small>
                </span>
              </span>
              <span className="kn-library-cell" data-label="Type">
                {words(m.document_type)}
                {m.historical && <small>Historical · Non-normative</small>}
                {used.has(m.document_id) && (
                  <small>Used by recent agent runs</small>
                )}
              </span>
              <span className="kn-library-cell" data-label="Version">
                v{m.document_version}
                <small>
                  {superseded
                    ? "Superseded"
                    : current
                      ? "Current"
                      : "Source check needed"}
                </small>
              </span>
              <span
                className="kn-library-cell kn-library-approval"
                data-label="Approval"
              >
                <StatusText>{words(m.approval_status)}</StatusText>
              </span>
            </button>
          ))}
        </div>
        {status && documents.length === 0 && (
          <Empty>No matching controlled documents.</Empty>
        )}
      </Section>
      <details
        className="rt-disclosure"
        open={searchOpen}
        onToggle={(event) => setSearchOpen(event.currentTarget.open)}
      >
        <summary>
          Search knowledge{" "}
          <span>Ask a question within a specialist’s evidence scope</span>
        </summary>
        <Section
          title="Search knowledge"
          note="Current operational facts and approval rules remain authoritative in the source systems."
        >
          <form
            className="kn-search"
            onSubmit={(e) => {
              e.preventDefault();
              void search();
            }}
          >
            <label>
              Knowledge question
              <input
                ref={questionInput}
                aria-label="Search knowledge"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Supplemental validation approval procedure"
                maxLength={1000}
              />
            </label>
            <label>
              Retrieval profile
              <select
                value={profile}
                onChange={(e) => {
                  ++serial.current;
                  setBusy("");
                  setResponse(null);
                  setSelected(null);
                  setProfile(e.target.value as typeof profile);
                }}
              >
                {profiles.map((p) => (
                  <option key={p} value={p}>
                    {words(p.toLowerCase())}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              disabled={!!busy || query.trim().length < 2 || !status}
            >
              <Search size={16} />
              {busy === "Searching" ? "Searching…" : "Search"}
            </button>
            <label className="kn-check">
              <input
                type="checkbox"
                checked={historical}
                onChange={(e) => setHistorical(e.target.checked)}
              />
              Include historical reports
            </label>
            <label className="kn-check">
              <input
                type="checkbox"
                checked={prior}
                onChange={(e) => setPrior(e.target.checked)}
              />
              Include prior / superseded versions
            </label>
          </form>
          <p className="kn-provider">
            {status?.provider === "openai_vector_store"
              ? "OpenAI semantic retrieval"
              : "Deterministic offline retrieval · Transparent term and synonym ranking; no model calls"}{" "}
            · Index: {words(status?.state || "loading")}
          </p>
          {response && (
            <div aria-live="polite">
              <p>
                {response.result_count} matching passages. Open one to verify
                its source and applicability.
              </p>
              {response.index_state !== "current" && (
                <p role="status">
                  Index {words(response.index_state)}. An operator can sync the
                  source corpus.
                </p>
              )}
              {response.results.length === 0 && (
                <Empty>
                  No eligible evidence found. Try another question or retrieval
                  profile.
                </Empty>
              )}
              {response.results.map((result) => (
                <button
                  key={result.chunk_id}
                  className="kn-result"
                  onClick={() => void inspect(result)}
                >
                  <span>
                    <strong>{result.title}</strong>
                    <small>
                      {result.document_id} · v{result.document_version} ·{" "}
                      {result.section || "Section not recorded"}
                    </small>
                  </span>
                  <span className="kn-passage">{result.passage}</span>
                  <small>
                    {result.metadata.program_id} ·{" "}
                    {result.metadata.approval_status} ·{" "}
                    {result.current
                      ? "Current source version"
                      : "Prior / superseded version"}{" "}
                  </small>
                  <span>Open exact document and passage →</span>
                </button>
              ))}
            </div>
          )}
        </Section>
      </details>
      <KnowledgeRunEvidence onEvents={setEvents} />
      {status?.can_reindex && (
        <details className="kn-admin">
          <summary>Knowledge index administration</summary>
          <p>
            Local demo index only. Reindexing reads the existing allowlisted
            corpus and preserves version history.
          </p>
          <button disabled={!!busy} onClick={() => setConfirm(true)}>
            Reindex knowledge corpus
          </button>
          {confirm && (
            <div>
              <p>Sync the shared index from current source documents?</p>
              <button disabled={!!busy} onClick={() => void reindex()}>
                {busy === "Indexing" ? "Indexing…" : "Confirm reindex"}
              </button>
              <button disabled={!!busy} onClick={() => setConfirm(false)}>
                Cancel
              </button>
            </div>
          )}
        </details>
      )}
      {docId && (
        <Drawer
          title={docId}
          close={() => setParams(filter ? { q: filter } : {})}
        >
          {documents.some((d) => d.metadata.document_id === docId) ? (
            <DocumentContent docId={docId} />
          ) : (
            <Empty>Document not found in the authorized library.</Empty>
          )}
        </Drawer>
      )}
      {selected && (
        <Drawer
          title={selected.title}
          close={() => {
            ++serial.current;
            setSelected(null);
            setVerification(null);
            if (chunkId) setParams({});
          }}
        >
          <div className="kn-preview">
            <section>
              <h3>Exact source document</h3>
              {verification ? (
                verification.verified && verification.document ? (
                  <>
                    <StatusText tone="good">
                      Document matches the current source version
                    </StatusText>
                    <Facts
                      rows={[
                        [
                          "Source",
                          verification.document.metadata.source_system,
                        ],
                        [
                          "Document version",
                          verification.document.metadata.document_version,
                        ],
                        [
                          "Lifecycle",
                          words(verification.document.metadata.approval_status),
                        ],
                        [
                          "Use as",
                          verification.document.metadata.historical
                            ? "Historical context; not a current approval rule"
                            : "Current source document; check the approval status and scope",
                        ],
                      ]}
                    />
                    <div className="cp-document-content">
                      {verification.document.content}
                    </div>
                    <SourceLink
                      to={`/engineering/documents/${selected.document_id}`}
                    >
                      Open source document
                    </SourceLink>
                  </>
                ) : (
                  <Empty>
                    The authoritative source document or metadata changed.
                    Reindex and search again before relying on this passage.
                  </Empty>
                )
              ) : (
                <Empty>
                  {error || "Verifying exact document and version…"}
                </Empty>
              )}
            </section>
            <section>
              <h3>Retrieved passage</h3>
              <p className="kn-passage">{selected.passage}</p>
              <Facts
                rows={[
                  ["Section", selected.section || "Not recorded"],
                  ["Document version", selected.document_version],
                  ["Approval status", selected.metadata.approval_status],
                  ["Program", selected.metadata.program_id],
                  [
                    "Configuration",
                    selected.metadata.configuration_id || "Not recorded",
                  ],
                  [
                    "Owner team",
                    selected.metadata.owner_team || "Not recorded",
                  ],
                  [
                    "Effective date",
                    selected.metadata.effective_date || "Not recorded",
                  ],
                  [
                    "Current / superseded",
                    selected.current ? "Current" : "Prior / superseded",
                  ],
                ]}
              />
              <p>
                This passage is supporting material. The applicable policy and
                source-system approvals still determine what can be done.
              </p>
              <details className="tr-details">
                <summary>Search and verification details</summary>
                <Facts
                  rows={[
                    ["Search ranking score", selected.score ?? "Not provided"],
                    ["Search provider", response?.provider || "Unknown"],
                    ["Passage ID", selected.chunk_id],
                    ["Search reference", response?.query_id || "Unknown"],
                    [
                      "Content fingerprint",
                      verification?.document?.metadata.content_hash ||
                        "Not recorded",
                    ],
                  ]}
                />
                <p>
                  The ranking score measures search relevance, not factual
                  accuracy or permission to act.
                </p>
              </details>
            </section>
          </div>
        </Drawer>
      )}
    </div>
  );
}
