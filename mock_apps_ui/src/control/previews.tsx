import { useHost } from "./host";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Link } from "./access";
import {
  ArrowRight,
  FileText,
  GitBranch,
  FlaskConical,
  ShieldCheck,
  Truck,
} from "lucide-react";
import "./rethink-utilities.css";
import type { Schema } from "../api";
import {
  casePath,
  date,
  programPath,
  read,
  stories,
  useControl,
  words,
} from "./data";
import {
  StatusText,
  Crumbs,
  Drawer,
  Empty,
  Facts,
  Heading,
  Notice,
  Section,
  SourceLink,
  SourceState,
  Steps,
  Truth,
} from "./ui";
export function Scenarios() {
  const host = useHost();
  const allowed = host?.capabilities?.scenario_ids || [];
  const scenarios = [
    {
      id: "CR-019",
      icon: GitBranch,
      title: "Standard change, verified handoff",
      question: "Can existing evidence support this approved request?",
      route: [
        "Check approved scope",
        "Reuse evidence",
        "Verify Operations intake",
      ],
      owner: "Policy-qualified handoff",
      boundary:
        "Intake confirmation is separate from lab testing and customer acceptance.",
    },
    {
      id: "CR-017",
      icon: FlaskConical,
      title: "Close a workload evidence gap",
      question: "What validation is needed for the expanded workload?",
      route: [
        "Investigate",
        "Operator submits",
        "Engineering approves",
        "Lab handoff",
      ],
      owner: "Engineering approver",
      boundary:
        "Submit the approved plan to the lab explicitly. A matching lab result supports technical completion; customer acceptance remains separate.",
    },
    {
      id: "QE-004",
      icon: ShieldCheck,
      title: "Protect yield and available supply",
      question: "How should we respond to the held lot’s yield exception?",
      route: [
        "Investigate",
        "Operator submits",
        "Owner approves",
        "Verify recovery task",
      ],
      owner: "Program Owner",
      boundary:
        "Recovery coordination leaves Quality disposition, held material and customer commitments under their own authority.",
    },
    {
      id: "DR-009",
      icon: Truck,
      title: "Make a supportable delivery commitment",
      question: "What quantity and date can we responsibly commit?",
      route: [
        "Reconcile readiness",
        "Owner decides",
        "Update ERP",
        "Verify Planner link",
      ],
      owner: "Program Owner",
      boundary:
        "The exact approved commitment is recorded. Any remaining supply gap stays visible.",
    },
  ].filter((scenario) => allowed.includes(scenario.id));
  return (
    <div className="rt-utilities rt-scenarios">
      <Heading
        eyebrow="Program journeys"
        title="Scenarios"
        description="Choose the business question. Follow the evidence, decision and confirmed outcome."
      />
      <div className="rt-scenario-list">
        {scenarios.map((scenario) => {
          const current = host?.data?.case_summaries?.find(
            (item) => item.change_id === scenario.id,
          );
          const Icon = scenario.icon;
          return (
            <article className="rt-scenario" key={scenario.id}>
              <div className="rt-scenario-main">
                <span className="rt-utility-icon">
                  <Icon size={24} aria-hidden="true" />
                </span>
                <div>
                  <small>
                    {scenario.id} · {scenario.owner}
                  </small>
                  <h2>
                    <Link
                      to={
                        current?.href ||
                        `${programPath("PRG-A17")}/cases/${scenario.id}`
                      }
                    >
                      {scenario.title}
                    </Link>
                  </h2>
                  <p>{scenario.question}</p>
                </div>
                <StatusText
                  tone={
                    current?.attention === "human_review"
                      ? "warning"
                      : "neutral"
                  }
                >
                  {host?.error
                    ? "Source read stale"
                    : current?.state_label || "State unavailable"}
                </StatusText>
                <Link
                  to={
                    current?.href ||
                    `${programPath("PRG-A17")}/cases/${scenario.id}`
                  }
                  aria-label={`Open ${scenario.id}`}
                >
                  <ArrowRight size={20} />
                </Link>
              </div>
              <ol
                className="rt-mini-flow"
                aria-label={`${scenario.id} workflow`}
              >
                {scenario.route.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <details className="rt-inline-details">
                <summary>What completes this journey?</summary>
                <p>{scenario.boundary}</p>
                {current && (
                  <p>
                    <strong>Current next step:</strong> {current.next_action}
                  </p>
                )}
              </details>
            </article>
          );
        })}
      </div>
      {stories
        .filter((story) => allowed.includes(story.id))
        .map((story) => (
          <Section
            title={story.title}
            key={story.id}
            action={<StatusText>Preview only</StatusText>}
          >
            <p>{story.question}</p>
            <Link to={`${programPath("PRG-A17")}/cases/${story.id}`}>
              Explore {story.code} <ArrowRight size={16} />
            </Link>
          </Section>
        ))}
      {!scenarios.length && (
        <Empty>No scenarios are available for this persona.</Empty>
      )}
    </div>
  );
}
export function DocumentContent({ docId }: { docId: string }) {
  const [doc, setDoc] = useState<Schema["Document"] | null>(null),
    [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    setDoc(null);
    setError(false);
    read<Schema["Document"]>(
      `/engineering/documents/${encodeURIComponent(docId)}`,
    )
      .then((d) => {
        if (active) setDoc(d);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [docId]);
  return error ? (
    <Empty>Document unavailable. No cached content has been substituted.</Empty>
  ) : !doc ? (
    <Empty>Reading controlled document…</Empty>
  ) : (
    <>
      <Truth />
      <Facts
        rows={[
          ["Source", "Engineering Hub"],
          ["Program", doc.program_id],
          ["Document version", doc.document_version],
          ["Content version", doc.content_version],
          ["Status", doc.status],
          ["Updated", date(doc.updated_at, true)],
          [
            "Applicability",
            "Read the controlled scope below; document availability alone is not evidence sufficiency.",
          ],
        ]}
      />
      <div className="cp-document-content">{doc.content}</div>
      <SourceLink to={`/engineering/documents/${doc.id}`}>
        Open source document
      </SourceLink>
    </>
  );
}
export { Knowledge } from "./knowledge";
export function OperationsPreview() {
  const host = useHost();
  const [params] = useSearchParams();
  const selectedRun = host?.data?.runs.find(
    (r) => r.run_id === params.get("run"),
  );
  const { fetchedAt, freshness } = useControl();
  return (
    <>
      <Heading
        eyebrow="Service visibility"
        title="Operations"
        description="Understand the read boundary now; runtime and evaluation visibility arrive in 08.6."
      />
      <Truth mode="Preview only" />
      <Section
        title="Connection & capability"
        note="This connection state is observed by the shell. No model run is launched."
      >
        <Facts
          rows={[
            ["Source API reads", freshness],
            ["Last successful retrieval", date(fetchedAt, true)],
            [
              "Host case/run metadata",
              host?.data && !host.error
                ? "Connected · Recorded runs"
                : "Unavailable",
            ],
            ["Assistant", "UI preview · no model connection"],
            ["Schedules and event workers", "None active"],
          ]}
        />
        <Link className="cp-button" to="/">
          Open five source applications <ArrowRight size={16} />
        </Link>
      </Section>
      {selectedRun && (
        <Notice>
          Selected run:{" "}
          <Link to={`/control/runs/${encodeURIComponent(selectedRun.run_id)}`}>
            {selectedRun.run_id}
          </Link>
          . Reuse this run detail for future Operations visibility.
        </Notice>
      )}
      <Section
        title="Reliability history"
        note="Historical handoff context, not a fresh evaluation scorecard."
      >
        <div className="cp-context-grid cp-three">
          <article>
            <StatusText>Recorded result</StatusText>
            <h3>40-case offline suite</h3>
            <p>
              The historical handoff reports passing hard gates. Deterministic
              contract tests do not measure fresh live-model quality.
            </p>
          </article>
          <article>
            <StatusText tone="warning">
              Recorded result · hard gate failed
            </StatusText>
            <h3>Original six-case smoke</h3>
            <p>
              4 of 6 passed. This failed report is preserved and has not become
              a fresh six-case pass.
            </p>
          </article>
          <article>
            <StatusText>Recorded result</StatusText>
            <h3>Two targeted exit cases</h3>
            <p>
              The approved Phase 08 request reports that both targeted cases
              passed after stabilization. No new live run is performed by this
              UI.
            </p>
          </article>
        </div>
      </Section>
      <Section title="Inspect the boundaries">
        <div className="cp-case-list">
          <Link to="/control/workflows/requirement_change_analysis">
            <span>
              <strong>Governed workflow</strong>
              <small>Shared invocation, exact host review and execution</small>
            </span>
            <ArrowRight size={16} />
          </Link>
          <Link to="/control/knowledge">
            <span>
              <strong>Business evidence provenance</strong>
              <small>Source versions and controlled documents</small>
            </span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </Section>
    </>
  );
}
