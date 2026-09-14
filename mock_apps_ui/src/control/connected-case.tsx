import { KnowledgeRunEvidence } from "./knowledge-runs";
import { RecordedText, FindingSummary } from "./traceability";
import { consultedSources, eventLabel, agentName } from "./trace-language";
import { agentRoles } from "./agent-activity";
import { CaseHeader } from "./case-experience";
import { ActionAccess } from "./persona";
import {
  PhysicalValidationPanel,
  downstreamLabel,
} from "./physical-validation";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Link, AllowedAction, canAct } from "./access";
import {
  Play,
  ArrowRight,
  CheckCircle2,
  Clock3,
  DollarSign,
  GitBranch,
  ShieldCheck,
  Send,
} from "lucide-react";
import {
  type CaseData,
  type Program,
  date,
  money,
  words,
  programPath,
  useControl,
} from "./data";
import {
  Heading,
  Section,
  Facts,
  Empty,
  Steps,
  StatusText,
  SourceLink,
  Crumbs,
} from "./ui";
import { Evidence, Options } from "./case";
import { HostReadState, ExecutionDetails, References } from "./decisions";
import {
  useHost,
  decisionPath,
  executionLabel,
  type HostCase,
  type HostSchema,
} from "./host";
import { RuntimeLabel } from "./runtime-label";

function overallFindings(
  run: HostSchema["RunView"],
  host: HostCase | null | undefined,
  caseData: CaseData | undefined,
) {
  if (run.status === "running")
    return {
      finding: "The investigation is still in progress.",
      impact:
        "The Coordinator and specialists are checking current source records. No final conclusion or business action has been recorded.",
      next: "Wait for the investigation to finish, then review the recorded findings and proposed next step.",
    };
  if (run.status !== "completed")
    return {
      finding: `The investigation ${run.status === "cancelled" ? "was cancelled" : "did not complete"}.`,
      impact:
        "Incomplete findings cannot support a recommendation, approval, or source-system action.",
      next: "Review the run activity, resolve the reported issue, and start a new investigation.",
    };

  if (run.change_id === "CR-017") {
    const physical = host?.downstream?.physical;
    if (physical?.result && physical.applicability === "confirmed")
      return {
        finding:
          "The passing Validation Lab result matches the exact approved configuration, workload, sample, duration, and source-bound plan.",
        impact:
          "The supplemental validation obligation is satisfied and CR-017 is technically complete for this demo workflow.",
        next: "No additional Program Operator or agent action is required.",
      };
    const latest = caseData?.coverage.items
      .filter(
        (item) =>
          item.result.configuration_id === caseData.config.id &&
          item.result.workload_profile_id === caseData.targetWorkload.id,
      )
      .sort((a, b) =>
        b.result.completed_at.localeCompare(a.result.completed_at),
      )[0];
    return {
      finding: latest
        ? `Current evidence covers ${latest.result.actual_suite_minutes} of the requested ${caseData?.targetWorkload.total_suite_minutes} test minutes. It does not cover the complete WF-LC-V2 workload.`
        : "The agents did not find evidence that covers the complete requested WF-LC-V2 workload.",
      impact:
        "Supplemental validation is required before Engineering can decide whether the evidence is adequate. Testing and final customer acceptance remain separate decisions.",
      next: "Prepare the supported supplemental-validation proposal and route it to Engineering for approval.",
    };
  }

  if (run.change_id === "CR-019") {
    const eligibility = host?.standard?.eligibility;
    const passed = eligibility?.checks.filter((check) => check.passed).length;
    const reusable = eligibility?.reusable_evidence_ids.length;
    const handoff = host?.standard?.handoffs.find(
      (item) => item.run_id === run.run_id,
    );
    return {
      finding: eligibility
        ? `All ${passed} of ${eligibility.checks.length} approved-scope checks matched, and the agents identified ${reusable} reusable evidence record${reusable === 1 ? "" : "s"}.`
        : "The agents completed the standard-package assessment.",
      impact:
        "The request matches the approved profile and procedure, so policy allows a bounded handoff to Validation Operations without a new approval. This does not authorize lab work or customer acceptance.",
      next:
        handoff?.status === "handoff_verified"
          ? "Validation Operations now owns the separate lab-authorization and confirmation process."
          : "Create and independently verify the Validation Operations intake package.",
    };
  }

  if (run.change_id === "QE-004" || run.change_id === "QE-011") {
    const view =
      run.change_id === "QE-011" ? host?.autonomous_quality : host?.quality;
    const analysis = view?.context?.analysis;
    const progress = view?.progress?.find((item) => item.run_id === run.run_id);
    return {
      finding: analysis
        ? `The comparable final-test pass rate fell from ${(analysis.baseline_rate_bps ?? 0) / 100}% to ${analysis.observed_rate_bps / 100}%. All ${analysis.held_quantity} affected units remain on hold, and the root cause is ${analysis.root_cause || "not yet confirmed"}.`
        : "The agents completed the quality-exception assessment.",
      impact: analysis
        ? `Held material is excluded from eligible supply, leaving ${analysis.eligible_quantity} eligible units against ${analysis.requested_quantity} requested and a ${analysis.gap_quantity}-unit gap. No release, reallocation, or customer-commitment change was authorized.`
        : "The lot remains governed by Product Quality while the investigation continues.",
      next:
        run.change_id === "QE-011"
          ? "Product Quality continues the approved investigation; the lot remains on hold until a separate disposition."
          : progress?.decision
            ? "Follow the approved recovery task and keep the held lot under separate Product Quality disposition."
            : analysis
              ? `Keep ${view?.context?.exception.lot_id} on hold, investigate and qualify the affected test setup, execute only a Quality-authorized controlled recovery, and protect the ${analysis.requested_quantity}-unit requirement while resolving the ${analysis.gap_quantity}-unit gap.`
              : "Route the standard investigation and present the exact recovery task to the Program Owner for review.",
    };
  }

  if (run.change_id === "DR-009") {
    const analysis = host?.delivery?.context?.analysis;
    const progress = host?.delivery?.progress?.find(
      (item) => item.run_id === run.run_id,
    );
    return {
      finding: analysis
        ? `${analysis.eligible_quantity} of ${analysis.requested_quantity ?? "the requested"} units are eligible for the Helios delivery, leaving a ${analysis.gap_quantity ?? "remaining"}-unit gap. Technical readiness is ${words(analysis.technical_readiness)}.`
        : "The agents completed the delivery-readiness assessment.",
      impact:
        "The full request cannot be committed from current eligible supply. Any partial commitment requires exact Program Owner approval and separate customer agreement; existing allocations remain protected.",
      next: progress?.decision
        ? "Track the authorized partial commitment and resolve the remaining supply gap separately."
        : "Present the exact supported partial commitment to the Program Owner and retain the uncovered quantity as an open gap.",
    };
  }

  return {
    finding: run.business_outcome || "The investigation completed.",
    impact:
      "The recorded findings summarize the source state checked by the agents for this run.",
    next:
      run.recommendation?.recommended_next_step ||
      "Review the recorded findings and the next authorized step.",
  };
}

function concise(
  text: string | null | undefined,
  fallback: string,
  limit = 190,
) {
  if (!text) return fallback;
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [];
  const first = sentences[0]?.trim() || text.trim();
  if (first.length <= limit) return first;
  const cut = first.slice(0, limit).lastIndexOf(" ");
  return `${first.slice(0, cut > 80 ? cut : limit).trim()}…`;
}

function recommendationSections(text: string) {
  return text
    .trim()
    .split(/\n{2,}(?=\d+\.\s)/)
    .map((section) => {
      const lines = section
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
      let title = lines.shift() || "Recommendation";
      const recommendation: string[] = [];
      const actions: string[] = [];
      let target = recommendation;
      const inline = title.split(/\s+—\s+/, 2);
      if (inline.length === 2) {
        title = inline[0];
        recommendation.push(inline[1]);
      }
      for (const line of lines) {
        if (/^recommendation:?$/i.test(line)) {
          target = recommendation;
          continue;
        }
        if (/^actions the agents can take:?$/i.test(line)) {
          target = actions;
          continue;
        }
        target.push(line.replace(/^[•*-]\s*/, ""));
      }
      return { title, recommendation, actions };
    })
    .filter(
      (section) => section.recommendation.length || section.actions.length,
    );
}

function AgentRecommendation({ text }: { text: string }) {
  const sections = recommendationSections(text);
  if (!sections.length)
    return <RecordedText text={text} label="Full agent recommendation" />;
  return (
    <ol className="cp-recommendation-list cp-recommendation-cards">
      {sections.map((section, index) => (
        <li key={section.title}>
          <span className="cp-recommendation-index">
            {String(index + 1).padStart(2, "0")} / RECOMMENDATION
          </span>
          <h3>{section.title.replace(/^\d+\.\s*/, "")}</h3>
          <div className="cp-recommendation-content">
            <div>
              <h4>Recommendation</h4>
              <ul>
                {section.recommendation.slice(0, 2).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="cp-agent-actions">
              <h4>Agent actions</h4>
              {section.actions.length ? (
                <ul>
                  {section.actions.slice(0, 2).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p>No separate agent actions recorded.</p>
              )}
            </div>
          </div>
          <details className="cp-recommendation-detail">
            <summary>Full recommendation & scope</summary>
            <h4>Recommendation</h4>
            <ul>
              {section.recommendation.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            {!!section.actions.length && (
              <>
                <h4>Agent actions</h4>
                <ul>
                  {section.actions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            )}
          </details>
        </li>
      ))}
    </ol>
  );
}

function specialistTask(s: HostSchema["SpecialistView"]) {
  if (s.result_kind === "validation_clarification")
    return "Verify the selected option against its authoritative source record.";
  return (
    {
      change_impact:
        "Compare the approved baseline with the requested workload.",
      validation_evidence:
        "Check evidence coverage, lab options, cost, and timing.",
      program_commercial:
        "Check milestones, ownership, cost, and customer commitments.",
      manufacturing: "Verify unit, lot, availability, and hold restrictions.",
    }[s.specialist] ||
    concise(s.task, "Review the assigned source records.", 120)
  );
}

function specialistWaves(items: HostSchema["SpecialistView"][]) {
  const sorted = [...items].sort(
    (a, b) => (a.started_ms || 0) - (b.started_ms || 0),
  );
  return sorted.reduce<HostSchema["SpecialistView"][][]>((waves, item) => {
    const latest = waves.at(-1);
    const first = latest?.[0];
    if (
      latest &&
      Math.abs((item.started_ms || 0) - (first?.started_ms || 0)) <= 1200
    )
      latest.push(item);
    else waves.push([item]);
    return waves;
  }, []);
}

export function RunFindings({ run }: { run: HostSchema["RunView"] }) {
  const host = useHost();
  const source = useControl();
  const handoff = host?.data?.standard?.handoffs.find(
    (h) => h.run_id === run.run_id,
  );
  const overview = overallFindings(
    run,
    host?.data,
    source.data?.cases.find((item) => item.change.id === run.change_id),
  );
  const specialists = run.specialists || [];
  const waves = specialistWaves(specialists);
  const completed = specialists.filter((s) => s.status === "completed").length;
  const progress = !specialists.length
    ? "The Coordinator is checking the request. Recorded activity updates automatically."
    : completed === specialists.length
      ? "Specialist assessments complete · Preparing the recommendation."
      : `Checking source records · ${completed} of ${specialists.length} specialist assessments complete.`;
  const roles: Record<string, string> = {
    change_impact: "Change Impact",
    validation_evidence: "Validation & Evidence",
    program_commercial: "Program & Commercial",
    manufacturing: "Manufacturing",
  };
  return (
    <Section
      title="Agent findings"
      className="cp-case-findings"
      note={
        run.status === "running"
          ? progress
          : `What the agents checked and found · ${date(run.started_at, true)}. These are saved findings; source records may have changed.`
      }
    >
      <div className="tr-outcome">
        <div>
          <span className="tr-label">Finding</span>
          <strong>{overview.finding}</strong>
        </div>
        <div>
          <span className="tr-label">Business impact</span>
          <p>{overview.impact}</p>
        </div>
        <div className="tr-outcome-next">
          <span className="tr-label">Next step</span>
          <p>{overview.next}</p>
        </div>
      </div>
      {run.change_id === "QE-004" &&
        run.status === "completed" &&
        run.recommendation?.recommended_next_step && (
          <div className="cp-agent-recommendation">
            <span className="tr-label">
              Agent recommendation · Proposed actions
            </span>
            <AgentRecommendation
              text={run.recommendation.recommended_next_step}
            />
            <small>
              The Program Operator may edit this draft before submitting it to
              the Program Owner. Engineering, Product Quality, allocation, and
              commercial authorities remain separate.
            </small>
          </div>
        )}
      {run.error_code && (
        <p role="alert" className="cp-error">
          Investigation {words(run.status)} · {run.error_code}. Incomplete
          findings do not authorize a proposal.
        </p>
      )}
      <details
        className="cp-case-trace"
        open={run.status === "running" || run.status === "failed"}
      >
        <summary>
          Agent sequence & source checks{" "}
          <span>
            {completed} of {specialists.length} specialists complete
          </span>
        </summary>
        <div className="cp-agent-sequence" aria-label="Agent run sequence">
          <div className="cp-agent-wave cp-coordinator-step">
            <div className="cp-sequence-marker">1</div>
            <div className="cp-wave-heading">
              <div>
                <small>Coordinator</small>
                <strong>
                  Understood the request and assigned specialist work
                </strong>
              </div>
              <StatusText
                tone={
                  run.status === "failed"
                    ? "danger"
                    : run.status === "running"
                      ? "agent"
                      : "good"
                }
              >
                {run.status === "running" ? "Coordinating" : words(run.status)}
              </StatusText>
            </div>
          </div>
          {waves.map((wave, waveIndex) => {
            const nested = wave.some((s) => !!s.parent_invocation_id);
            const clarification = wave.some(
              (s) => s.result_kind === "validation_clarification",
            );
            const label =
              wave.length > 1
                ? `${wave.length} agents ran in parallel`
                : clarification
                  ? "Evidence clarification"
                  : nested
                    ? "Specialist consultation"
                    : "Specialist analysis";
            return (
              <div className="cp-agent-wave" key={wave[0].invocation_id}>
                <div className="cp-sequence-marker">{waveIndex + 2}</div>
                <div className="cp-wave-heading">
                  <div>
                    <small>{label}</small>
                    <strong>
                      {wave.length > 1
                        ? "Independent source checks"
                        : specialistTask(wave[0])}
                    </strong>
                  </div>
                  <span className="cp-time-tag">
                    +{Math.max(0, Math.round((wave[0].started_ms || 0) / 1000))}
                    s
                  </span>
                </div>
                <div
                  className={`cp-agent-branches cp-wave-${Math.min(wave.length, 3)}`}
                >
                  {wave.map((s) => (
                    <article
                      key={s.invocation_id}
                      data-specialist={s.specialist}
                    >
                      <div className="cp-inline">
                        <h3>{roles[s.specialist] || words(s.specialist)}</h3>
                        <StatusText
                          tone={
                            s.status === "failed"
                              ? "warning"
                              : s.status === "completed"
                                ? "good"
                                : "agent"
                          }
                        >
                          {words(s.status)}
                        </StatusText>
                      </div>
                      <p className="cp-agent-task">{specialistTask(s)}</p>
                      <div className="cp-agent-finding">
                        <span className="tr-label">Result</span>
                        <p>
                          {concise(
                            s.summary,
                            s.status === "running"
                              ? "Checking source records…"
                              : "No finding was recorded yet.",
                          )}
                        </p>
                      </div>
                      <div className="cp-agent-meta">
                        <span>{s.source_references?.length || 0} sources</span>
                        {s.ended_ms != null && s.started_ms != null && (
                          <span>
                            {Math.max(
                              1,
                              Math.round((s.ended_ms - s.started_ms) / 1000),
                            )}
                            s
                          </span>
                        )}
                      </div>
                      <details>
                        <summary>View task, full finding, and sources</summary>
                        <span className="tr-label">Assigned task</span>
                        <RecordedText
                          text={s.task}
                          label="Full assigned task"
                        />
                        <span className="tr-label">Full recorded finding</span>
                        <FindingSummary
                          summary={s.summary}
                          runId={run.run_id}
                          role={s.specialist}
                          status={s.status}
                          handoff={handoff}
                        />
                        <p className="cp-caption">
                          {consultedSources(s.source_references)}
                        </p>
                        <References refs={s.source_references || []} />
                      </details>
                      {!!(s.unresolved_questions || []).length && (
                        <details className="cp-agent-unresolved">
                          <summary>
                            {(s.unresolved_questions || []).length} open
                            question
                            {(s.unresolved_questions || []).length === 1
                              ? ""
                              : "s"}
                          </summary>
                          <ul>
                            {(s.unresolved_questions || []).map((q) => (
                              <li key={q}>{q}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                      {s.error_code && (
                        <p role="alert">Needs review · {words(s.error_code)}</p>
                      )}
                    </article>
                  ))}
                </div>
              </div>
            );
          })}
          <Link
            className="cp-text-link cp-run-detail-link"
            to={`/control/runs/${run.run_id}`}
          >
            Open full activity log <ArrowRight size={14} />
          </Link>
        </div>
      </details>
      {!(run.specialists || []).length && (
        <Empty>
          {run.findings_state === "unavailable"
            ? "The scoped specialist checkpoint is unavailable."
            : "No specialist activity has been recorded yet."}
        </Empty>
      )}
      {!(run.specialists || []).length &&
        !!run.recommendation?.specialist_findings.length &&
        run.recommendation.specialist_findings.map((s) => (
          <p key={s.invocation_id}>
            <strong>{roles[s.specialist]}</strong> · Recorded synthesis:{" "}
            {s.summary}
          </p>
        ))}
    </Section>
  );
}
export function ConnectedCase({
  c,
  program,
}: {
  c: CaseData;
  program: Program;
}) {
  const host = useHost()!,
    [params, setParams] = useSearchParams(),
    [error, setError] = useState("");
  const submitting = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const runId = params.get("run"),
    latest = host.data?.runs.find(
      (r) => !r.invocation_id.startsWith("ui_evidence_"),
    ),
    run = runId ? host.data?.runs.find((r) => r.run_id === runId) : latest;
  const preparedItem =
    host.data?.proposals.find(
      (p) =>
        (!run || p.proposal.origin.run_id === run.run_id) &&
        p.effective_status !== "superseded",
    ) ||
    host.data?.proposals.find((p) => p.proposal.origin.run_id === run?.run_id);
  const currentProposal = host.data?.proposals.find(
    (p) => p.effective_status !== "superseded",
  );
  const anyRunning = host.data?.runs.some((r) => r.status === "running");
  const complete = run?.status === "completed",
    recommendation = run?.recommendation;
  const evidenceReviewed =
    (run?.specialists || []).some(
      (s) => s.specialist === "validation_evidence" && s.status === "completed",
    ) ||
    !!(
      complete &&
      recommendation?.specialist_findings.some(
        (s) => s.specialist === "validation_evidence",
      )
    );
  const evidenceAssessment: "unassessed" | "running" | "complete" =
    run?.status === "running"
      ? "running"
      : complete && evidenceReviewed
        ? "complete"
        : "unassessed";
  const decisionOverview = run ? overallFindings(run, host.data, c) : undefined;
  const agentOption = recommendation?.available_options
    .filter(
      (option) =>
        option.resource_eligible &&
        option.approval_eligible &&
        option.meets_deadline,
    )
    .sort(
      (a, b) =>
        (a.cost_cents ?? Number.MAX_SAFE_INTEGER) -
          (b.cost_cents ?? Number.MAX_SAFE_INTEGER) ||
        (a.timing?.review_ready_at || "").localeCompare(
          b.timing?.review_ready_at || "",
        ) ||
        a.slot_id.localeCompare(b.slot_id) ||
        a.sample_id.localeCompare(b.sample_id),
    )[0];
  const agentRecommendationDraft = recommendation
    ? agentOption
      ? [
          `Recommend Engineering approve supplemental validation using ${agentOption.slot_id} and ${agentOption.sample_id} for ${c?.targetWorkload.id || "the requested workload"} on ${agentOption.configuration_id} under ${agentOption.procedure_id}.`,
          `The incremental cost is ${agentOption.cost_cents == null ? "not yet confirmed" : money(agentOption.cost_cents)}, with evidence expected to be ready for review ${date(agentOption.timing?.review_ready_at, true)}.`,
          "If approved, schedule the exact Validation Lab job and link the approved plan in Program Planner. Recheck resource eligibility and source versions immediately before execution.",
          "Keep the existing acceptance criteria and customer commitment unchanged. Scheduling, a completed test, Engineering evidence acceptance, and customer acceptance remain separate decisions.",
        ].join("\n\n")
      : recommendation.recommended_next_step
    : "";
  const agentContextDraft = recommendation
    ? [
        `Finding: ${decisionOverview?.finding || concise(recommendation.change_summary, "Review the recorded finding.", 400)}`,
        `Business impact: ${decisionOverview?.impact || "Engineering review is required before any governed action."}`,
        recommendation.evidence_gaps.length
          ? `Evidence gaps:\n${recommendation.evidence_gaps.map((gap) => `• ${concise(gap.statement, "Evidence gap recorded.", 220)}`).join("\n")}`
          : "Evidence gaps: None recorded.",
        recommendation.unresolved_questions.length
          ? `Open questions:\n${recommendation.unresolved_questions.map((question) => `• ${concise(question, "Open question recorded.", 220)}`).join("\n")}`
          : "Open questions: None recorded.",
        [
          ...recommendation.relevant_constraints,
          ...recommendation.program_impact,
        ].length
          ? `Constraints and program impact:\n${[...recommendation.relevant_constraints, ...recommendation.program_impact].map((item) => `• ${concise(item.statement, "Constraint recorded.", 180)}`).join("\n")}`
          : "Constraints and program impact: None recorded.",
      ]
        .join("\n\n")
        .slice(0, 3000)
    : "";
  const submittedEscalation = host.data?.operator_escalations?.find(
    (value) => value.run_id === run?.run_id,
  );
  // A prepared source draft is intentionally withheld from the decision UI
  // until the Program Operator submits the editable handoff.
  const item = submittedEscalation ? preparedItem : undefined;
  const [escalationSubject, setEscalationSubject] = useState("");
  const [escalationRecommendation, setEscalationRecommendation] = useState("");
  const [escalationContext, setEscalationContext] = useState("");
  const [operatorNotes, setOperatorNotes] = useState("");
  const tab = params.get("tab") || "summary";
  useEffect(() => {
    if (!run || !recommendation || submittedEscalation) return;
    setEscalationSubject(
      recommendation.policy_path === "escalation_required"
        ? "Resolve CR-017 evidence and source-state conflicts"
        : "Review the supported CR-017 validation path",
    );
    setEscalationRecommendation(agentRecommendationDraft);
    setEscalationContext(agentContextDraft);
    setOperatorNotes(
      "Please review the agent findings and determine the authorized next step. Customer acceptance remains separate.",
    );
  }, [
    run?.run_id,
    recommendation?.policy_path,
    agentRecommendationDraft,
    agentContextDraft,
    submittedEscalation?.escalation_id,
  ]);
  useEffect(() => {
    if (tab !== "options" || params.get("focus") !== "human-decision") return;
    requestAnimationFrame(() =>
      document
        .getElementById("human-decision")
        ?.scrollIntoView({ behavior: "smooth", block: "start" }),
    );
  }, [tab, params.get("focus")]);
  const start = async () => {
    if (submitting.current) return;
    submitting.current = true;
    setError("");
    const retryKey = "stratos-cr017-invocation";
    let id = sessionStorage.getItem(retryKey);
    if (id && host.data?.runs.some((r) => r.invocation_id === id)) {
      sessionStorage.removeItem(retryKey);
      id = null;
    }
    if (!id) {
      id = "ui_" + crypto.randomUUID().replaceAll("-", "");
      sessionStorage.setItem(retryKey, id);
    }
    try {
      await host.act("/cases/CR-017/investigations", { invocation_id: id });
      sessionStorage.removeItem(retryKey);
      if (mounted.current) setParams({ tab: "activity" });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      submitting.current = false;
    }
  };
  const openEscalation = () => {
    const q = new URLSearchParams(params);
    q.set("tab", "options");
    q.set("focus", "human-decision");
    setParams(q);
  };
  const submitEscalation = async () => {
    setError("");
    try {
      await host.act("/cases/CR-017/escalations", {
        submission_id: "ui_" + crypto.randomUUID().replaceAll("-", ""),
        run_id: run!.run_id,
        subject: escalationSubject,
        recommendation: escalationRecommendation,
        business_context: escalationContext,
        operator_notes: operatorNotes,
      });
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const submitToValidationLab = async () => {
    if (!item) return;
    setError("");
    try {
      await host.act("/proposals/execute", {
        reference: item.execution.reference,
      });
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <div className="cp-case-page cp-case-change">
      <CaseHeader
        id="CR-017"
        title="Long-context evidence change"
        action={
          <div className="cp-case-heading-actions">
            <AllowedAction caseId="CR-017" action="investigate">
              <button
                className={`cp-button ${complete && recommendation && !submittedEscalation ? "" : "cp-primary"}`}
                disabled={
                  !canAct(host.capabilities, "CR-017", "investigate") ||
                  !host.data?.source_available ||
                  !!host.error ||
                  !!host.busy ||
                  anyRunning
                }
                onClick={() => void start()}
              >
                <Play size={16} />
                {host.busy.endsWith("investigations")
                  ? "Starting investigation…"
                  : anyRunning
                    ? "Investigating…"
                    : run
                      ? "Reassess CR-017"
                      : "Run investigation"}
              </button>
            </AllowedAction>
            {complete && recommendation && !submittedEscalation && (
              <AllowedAction caseId="CR-017" action="escalate">
                <button
                  className="cp-button cp-primary"
                  onClick={openEscalation}
                >
                  Review & submit proposal <ArrowRight size={16} />
                </button>
              </AllowedAction>
            )}
            <SourceLink to="/engineering/changes/CR-017">
              Open Engineering Hub
            </SourceLink>
          </div>
        }
      />
      <HostReadState />
      <ActionAccess
        caseId="CR-017"
        action="investigate"
        ready={!!host.data?.source_available && !host.error && !anyRunning}
        reason={
          anyRunning
            ? "Investigation running. Read the current activity."
            : "Current source records are required."
        }
      />
      <div className="cp-connected-command">
        <div>
          <h2>
            {!host.data
              ? "Workflow state unavailable"
              : runId && !run
                ? "Requested run unavailable"
                : anyRunning
                  ? "Investigation running"
                  : !run
                    ? "Not investigated"
                    : run.status === "failed"
                      ? "Investigation failed"
                      : recommendation?.policy_path === "escalation_required"
                        ? "Escalation required"
                        : item
                          ? executionLabel(item)
                          : complete
                            ? "Investigation completed"
                            : words(run.status)}
          </h2>
          <p>
            {anyRunning
              ? "Specialists are checking the current source records."
              : host.data?.downstream?.physical.job
                ? downstreamLabel(host.data.downstream)
                : "Run an investigation to assess evidence coverage and prepare validation options."}
          </p>
          {!canAct(host.capabilities, "CR-017", "investigate") && (
            <small>
              Investigation is available to the permitted case roles.
            </small>
          )}
        </div>
      </div>
      <RuntimeLabel caseId="CR-017" run={run} />
      {error && (
        <p className="cp-error" role="alert">
          {error}
        </p>
      )}
      {runId && !run && host.data && (
        <p className="cp-error" role="alert">
          The requested run is not recorded for CR-017. No newer run has been
          substituted.
        </p>
      )}
      {!item && currentProposal && (
        <p>
          A current proposal belongs to an earlier investigation.{" "}
          <Link className="cp-text-link" to={decisionPath(currentProposal)}>
            Inspect that exact proposal · v
            {currentProposal.proposal.proposal_version}
          </Link>
        </p>
      )}
      {item && (
        <p>
          <Link className="cp-text-link" to={decisionPath(item)}>
            View exact proposal · v{item.proposal.proposal_version}{" "}
            <ArrowRight size={16} />
          </Link>
        </p>
      )}

      <nav className="cp-tabs" aria-label="Case sections">
        {[
          ["summary", "Summary"],
          ["evidence", "Evidence"],
          ["options", "Options & decisions"],
          ["activity", "Activity"],
        ].map(([id, label]) => (
          <button
            key={id}
            aria-current={tab === id ? "page" : undefined}
            onClick={() => {
              const q = new URLSearchParams(params);
              q.set("tab", id);
              q.delete("evidence");
              setParams(q);
            }}
          >
            {label}
          </button>
        ))}
      </nav>
      {tab === "summary" && (
        <>
          <details className="cp-secondary-content">
            <summary>Full requirement comparison & source evidence</summary>
            <Section
              title="What changed?"
              note="The requested workload changes; approved acceptance criteria retain their source authority."
            >
              <div className="cp-compare">
                {[
                  {
                    label: "Approved baseline",
                    req: c.baseline,
                    w: c.baselineWorkload,
                  },
                  {
                    label: "Requested revision",
                    req: c.target,
                    w: c.targetWorkload,
                  },
                ].map((x) => (
                  <article key={x.label}>
                    <small>{x.label}</small>
                    <h3>{x.req.id}</h3>
                    <p>{x.req.summary}</p>
                    <Facts
                      rows={[
                        [
                          "Context bins",
                          x.w.context_bins
                            .map((n) => n.toLocaleString())
                            .join(" / ") + " tokens",
                        ],
                        [
                          "Suite duration",
                          `${x.w.total_suite_minutes} minutes`,
                        ],
                        ["Configuration", x.req.configuration_id],
                        ["Status", words(x.req.status)],
                      ]}
                    />
                  </article>
                ))}
              </div>
            </Section>
            <Evidence c={c} assessment={evidenceAssessment} />
          </details>
          {run && <RunFindings run={run} />}
        </>
      )}
      {tab === "evidence" && (
        <>
          <h2>Structured source evidence</h2>
          <Evidence c={c} assessment={evidenceAssessment} />
          <KnowledgeRunEvidence caseId="CR-017" />
        </>
      )}
      {(tab === "summary" || tab === "options") && (
        <>
          <Section
            title="Recommendation & options"
            note="Recorded investigation output. Fresh source eligibility is checked again before proposal preparation and execution."
          >
            {!recommendation ? (
              <Empty>No completed recommendation is recorded.</Empty>
            ) : (
              <div className="cp-decision-board">
                <div
                  className="cp-decision-hero"
                  data-policy={recommendation.policy_path}
                >
                  <div>
                    <span className="tr-label">Agent recommendation</span>
                    <StatusText
                      tone={
                        recommendation.policy_path === "escalation_required"
                          ? "warning"
                          : recommendation.policy_path ===
                              "human_review_required"
                            ? "agent"
                            : "good"
                      }
                    >
                      {recommendation.policy_path === "human_review_required"
                        ? "Engineering decision needed"
                        : words(recommendation.policy_path)}
                    </StatusText>
                    <h3>
                      {recommendation.policy_path === "escalation_required"
                        ? "Resolve the flagged issue before proposing work"
                        : "Supplemental validation is the supported path"}
                    </h3>
                    <p>
                      {decisionOverview?.finding ||
                        concise(
                          recommendation.change_summary,
                          "Review the recorded recommendation.",
                        )}
                    </p>
                  </div>
                  <div className="cp-decision-next">
                    <span>Recommended next step</span>
                    <strong>
                      {decisionOverview?.next || "Review the recommendation."}
                    </strong>
                  </div>
                </div>

                <div className="cp-decision-metrics">
                  <div>
                    <GitBranch size={20} />
                    <span>
                      <strong>{recommendation.available_options.length}</strong>{" "}
                      viable option
                      {recommendation.available_options.length === 1 ? "" : "s"}
                    </span>
                  </div>
                  <div>
                    <ShieldCheck size={20} />
                    <span>
                      <strong>Engineering</strong> owns approval
                    </span>
                  </div>
                  <div>
                    <CheckCircle2 size={20} />
                    <span>
                      <strong>Fresh check</strong> before execution
                    </span>
                  </div>
                </div>

                {!!recommendation.available_options.length && (
                  <div
                    className="cp-option-cards"
                    aria-label="Viable validation options"
                  >
                    {recommendation.available_options.map((o) => {
                      const eligible =
                        o.resource_eligible &&
                        o.approval_eligible &&
                        o.meets_deadline;
                      const recommended =
                        o.slot_id === agentOption?.slot_id &&
                        o.sample_id === agentOption?.sample_id;
                      return (
                        <article
                          key={o.slot_id + o.sample_id}
                          data-eligible={eligible}
                        >
                          <div className="cp-option-heading">
                            <div>
                              <small>
                                {recommended
                                  ? "Recommended option"
                                  : "Available option"}
                              </small>
                              <h3>{o.slot_id.replace("SLOT-", "")}</h3>
                              <span>{o.sample_id}</span>
                            </div>
                            <StatusText tone={eligible ? "good" : "warning"}>
                              {eligible ? "Eligible" : "Not eligible"}
                            </StatusText>
                          </div>
                          <div className="cp-option-facts">
                            <div>
                              <DollarSign size={18} />
                              <span>
                                <small>Incremental cost</small>
                                <strong>
                                  {o.cost_cents === null
                                    ? "Unavailable"
                                    : money(o.cost_cents)}
                                </strong>
                              </span>
                            </div>
                            <div>
                              <Clock3 size={18} />
                              <span>
                                <small>Review ready</small>
                                <strong>
                                  {date(o.timing?.review_ready_at, true)}
                                </strong>
                              </span>
                            </div>
                          </div>
                          <div className="cp-tag-row">
                            <span
                              data-tone={
                                o.resource_eligible ? "good" : "warning"
                              }
                            >
                              Resource{" "}
                              {o.resource_eligible ? "available" : "blocked"}
                            </span>
                            <span
                              data-tone={o.meets_deadline ? "good" : "warning"}
                            >
                              {o.meets_deadline
                                ? "Meets deadline"
                                : "Deadline risk"}
                            </span>
                          </div>
                          {recommended && (
                            <div className="cp-option-recommendation">
                              <small>Agent recommendation</small>
                              <p>{agentRecommendationDraft}</p>
                            </div>
                          )}
                        </article>
                      );
                    })}
                  </div>
                )}

                <div className="cp-decision-detail-grid">
                  <details>
                    <summary>
                      Evidence gaps{" "}
                      <span>{recommendation.evidence_gaps.length}</span>
                    </summary>
                    {recommendation.evidence_gaps.length ? (
                      <ul>
                        {recommendation.evidence_gaps.map((f, i) => (
                          <li key={i}>{f.statement}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No additional evidence gaps were recorded.</p>
                    )}
                  </details>
                  <details>
                    <summary>
                      Open questions{" "}
                      <span>{recommendation.unresolved_questions.length}</span>
                    </summary>
                    {recommendation.unresolved_questions.length ? (
                      <ul>
                        {recommendation.unresolved_questions.map((q) => (
                          <li key={q}>{q}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No open questions were recorded.</p>
                    )}
                  </details>
                  <details>
                    <summary>
                      Constraints and program impact{" "}
                      <span>
                        {recommendation.relevant_constraints.length +
                          recommendation.program_impact.length}
                      </span>
                    </summary>
                    <ul>
                      {[
                        ...recommendation.relevant_constraints,
                        ...recommendation.program_impact,
                      ].map((f, i) => (
                        <li key={i}>{f.statement}</li>
                      ))}
                    </ul>
                  </details>
                  {(recommendation.escalation_reason ||
                    recommendation.change_summary) && (
                    <details>
                      <summary>Full recorded recommendation</summary>
                      <p>{recommendation.change_summary}</p>
                      {recommendation.escalation_reason && (
                        <p>{recommendation.escalation_reason}</p>
                      )}
                      <p>{recommendation.recommended_next_step}</p>
                    </details>
                  )}
                </div>
              </div>
            )}
          </Section>
          <div id="human-decision" className="cp-anchor-target">
            <Section
              title="Review & submit to Engineering"
              note="Edit the proposed action, then send the exact recommendation for a decision."
            >
              {submittedEscalation && item ? (
                <>
                  <div className="cp-submitted-handoff">
                    <StatusText tone="good">
                      Submitted to Engineering
                    </StatusText>
                    <h3>{submittedEscalation.subject}</h3>
                    <p>
                      <strong>Operator recommendation:</strong>{" "}
                      {submittedEscalation.recommendation}
                    </p>
                    <p>{submittedEscalation.business_context}</p>
                    {submittedEscalation.operator_notes && (
                      <p>
                        <strong>Operator notes:</strong>{" "}
                        {submittedEscalation.operator_notes}
                      </p>
                    )}
                  </div>
                  <Facts
                    rows={[
                      [
                        "Proposal",
                        `${item.proposal.proposal_id} · v${item.proposal.proposal_version}`,
                      ],
                      ["State", executionLabel(item)],
                      [
                        "Required reviewer",
                        `Engineer · ${item.proposal.required_policy_id}`,
                      ],
                    ]}
                  />
                  <Link
                    className="cp-button cp-primary"
                    to={decisionPath(item)}
                  >
                    View exact proposal <ArrowRight size={16} />
                  </Link>
                </>
              ) : submittedEscalation ? (
                <div className="cp-submitted-handoff">
                  <StatusText tone="good">Submitted to Engineering</StatusText>
                  <h3>{submittedEscalation.subject}</h3>
                  <p>
                    <strong>Operator recommendation:</strong>{" "}
                    {submittedEscalation.recommendation}
                  </p>
                  <p>{submittedEscalation.business_context}</p>
                  {submittedEscalation.operator_notes && (
                    <p>
                      <strong>Operator notes:</strong>{" "}
                      {submittedEscalation.operator_notes}
                    </p>
                  )}
                  <Link className="cp-button" to="/control/decisions">
                    View Engineering queue <ArrowRight size={16} />
                  </Link>
                </div>
              ) : recommendation && complete ? (
                <form
                  className="cp-escalation-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void submitEscalation();
                  }}
                >
                  <h3>Prepare review proposal</h3>
                  {preparedItem && (
                    <p className="cp-form-callout">
                      <strong>
                        A technical draft exists, but it has not been sent to
                        Engineering.
                      </strong>{" "}
                      Review and submit the operator handoff below.
                    </p>
                  )}
                  <div className="cp-form-callout">
                    <span className="tr-label">
                      Agent recommendation · pre-populated
                    </span>
                    <strong>
                      {decisionOverview?.next ||
                        recommendation.recommended_next_step}
                    </strong>
                    <p>
                      The fields below are an operator-authored handoff. Editing
                      them does not change source evidence or grant approval.
                    </p>
                  </div>
                  <label>
                    Escalation title
                    <input
                      value={escalationSubject}
                      onChange={(e) => setEscalationSubject(e.target.value)}
                      required
                      minLength={3}
                      maxLength={180}
                    />
                  </label>
                  <label>
                    Recommended action
                    <textarea
                      value={escalationRecommendation}
                      onChange={(e) =>
                        setEscalationRecommendation(e.target.value)
                      }
                      required
                      rows={3}
                      maxLength={3000}
                    />
                  </label>
                  <label>
                    Evidence and business context
                    <textarea
                      value={escalationContext}
                      onChange={(e) => setEscalationContext(e.target.value)}
                      required
                      rows={5}
                      maxLength={3000}
                    />
                  </label>
                  <label>
                    Operator notes
                    <textarea
                      value={operatorNotes}
                      onChange={(e) => setOperatorNotes(e.target.value)}
                      rows={3}
                      maxLength={2000}
                    />
                  </label>
                  <div className="cp-form-actions">
                    <small>
                      Engineering will see this case only after submission.
                      Submission does not approve or execute work.
                    </small>
                    <AllowedAction caseId="CR-017" action="escalate">
                      <button
                        className="cp-button cp-primary"
                        type="submit"
                        disabled={
                          !!host.busy ||
                          !!host.error ||
                          !host.data?.source_available ||
                          !canAct(host.capabilities, "CR-017", "escalate")
                        }
                      >
                        <Send size={16} />{" "}
                        {host.busy.endsWith("escalations")
                          ? "Submitting…"
                          : "Submit to Engineering"}
                      </button>
                    </AllowedAction>
                  </div>
                </form>
              ) : (
                <>
                  <Empty>No host proposal is recorded for this run.</Empty>
                </>
              )}
            </Section>
          </div>
          {tab === "options" &&
            (evidenceAssessment === "complete" ? (
              <details className="cp-source-options">
                <summary>Compare every source-calculated option</summary>
                <Options c={c} />
              </details>
            ) : (
              <Section
                title="Source options"
                note="Validation calculates cost, timing, and eligibility after the evidence assessment is complete."
              >
                <Empty>
                  {evidenceAssessment === "running"
                    ? "Options will appear when the investigation finishes."
                    : "Run the investigation to calculate validation options."}
                </Empty>
              </Section>
            ))}
          {item && (
            <ExecutionDetails
              item={item}
              onSubmitToLab={
                item.review?.status === "approved" &&
                item.execution.status === "approved" &&
                canAct(host.capabilities, "CR-017", "execute")
                  ? () => void submitToValidationLab()
                  : undefined
              }
              submitting={host.busy.endsWith("execute")}
            />
          )}
        </>
      )}
      {tab === "activity" && (
        <>
          {run && <RunFindings run={run} />}
          <Section title="Recorded runs">
            {host.data?.runs.map((r) => (
              <p key={r.run_id}>
                <Link to={`?tab=activity&run=${r.run_id}`}>
                  Investigation · {date(r.started_at, true)}
                </Link>{" "}
                · {words(r.status)} · {date(r.started_at, true)}
              </p>
            ))}
          </Section>
          <Section
            title="Case activity"
            note="What happened, who acted, and whether the source system confirmed the result."
          >
            {host.data?.activity
              .filter((a) => !runId || a.run_id === runId)
              .slice()
              .reverse()
              .map((a) => (
                <article className="cp-record" key={a.event_id}>
                  <strong>{eventLabel(a.event_type)}</strong>
                  <small>
                    {date(a.timestamp, true)} · {agentName(a.actor_id)}
                  </small>
                  {Object.keys(a.details || {}).length > 0 && (
                    <details>
                      <summary>Technical event details</summary>
                      <p>
                        {a.event_type} · {a.actor_id}
                      </p>
                      <pre>{JSON.stringify(a.details, null, 2)}</pre>
                    </details>
                  )}
                </article>
              ))}
          </Section>
        </>
      )}
      <PhysicalValidationPanel />
      <Evidence c={c} modalOnly assessment={evidenceAssessment} />
    </div>
  );
}
