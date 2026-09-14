import { KnowledgeRunEvidence } from "./knowledge-runs";
import { traceStatus } from "./trace-language";
import { CaseHeader } from "./case-experience";
import { ActionAccess } from "./persona";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Link, AllowedAction, canAct } from "./access";
import {
  ArrowRight,
  CheckCircle2,
  Play,
  Send,
  ShieldCheck,
} from "lucide-react";
import { useHost, type HostSchema } from "./host";
import { RuntimeLabel } from "./runtime-label";
import { words, date, money } from "./data";
import { Empty, Heading, Section, Facts, SourceLink, StatusText } from "./ui";
import { RunFindings } from "./connected-case";
export const qualityCasePath = "/control/programs/PRG-A17/cases/QE-004";
export const qualityAttention = (v: HostSchema["QualityCaseView"]) =>
  [
    "draft_ready",
    "awaiting_review",
    "outcome_unknown",
    "failed",
    "verification_failed",
    "stale",
  ].includes(v.status) || v.runs?.[0]?.status === "failed";
export function QualitySummary() {
  const v = useHost()?.data?.quality;
  if (!v) return null;
  return (
    <Section
      title="QE-004 · Yield exception"
      note="Helios Atlas Inference · Connected"
    >
      <StatusText tone={qualityAttention(v) ? "warning" : "neutral"}>
        {words(v.status)}
      </StatusText>
      <p>
        {v.context
          ? `${v.context.exception.lot_id} · ${words(v.context.material.find((m) => m.lot_id === v.context!.exception.lot_id)?.disposition || "unknown")} · ${v.context.analysis?.gap_quantity ?? "Unknown"}-unit supply exposure`
          : "Current source unavailable"}
      </p>
      <Link className="cp-text-link" to={qualityCasePath}>
        Inspect quality recovery <ArrowRight size={15} />
      </Link>
    </Section>
  );
}
export function QualityDecisions() {
  const v = useHost()?.data?.quality;
  if (!v?.records?.plans.length) return null;
  return (
    <Section
      title="Quality recovery decisions"
      note="Program Owner · Exact source plans"
    >
      {v.records.plans.map((p) => {
        const d = v.records!.decisions.find((d) => d.plan_id === p.id);
        const progress = v.progress?.find((item) => item.plan_id === p.id);
        return (
          <article className="cp-record" key={p.id}>
            <strong>QE-004 · Recovery plan v{p.plan_version}</strong>
            <p>
              {d
                ? `${words(d.decision)} · ${d.signer_identity}`
                : v.status === "stale"
                  ? "Source changed · Reassessment required"
                  : progress?.submitted_at
                    ? "Program Owner review required"
                    : "Program Operator submission required"}
            </p>
            <Link to={`${qualityCasePath}#decision`}>
              Review recovery plan · {p.id}
            </Link>
          </article>
        );
      })}
    </Section>
  );
}
export function QualityCase({
  caseId = "QE-004",
}: {
  caseId?: "QE-004" | "QE-011";
}) {
  const host = useHost(),
    v =
      caseId === "QE-011"
        ? host?.data?.autonomous_quality
        : host?.data?.quality;
  const [error, setError] = useState(""),
    [comment, setComment] = useState(""),
    [submissionSubject, setSubmissionSubject] = useState(""),
    [submissionRecommendation, setSubmissionRecommendation] = useState(""),
    [submissionContext, setSubmissionContext] = useState(""),
    [operatorNotes, setOperatorNotes] = useState("");
  const lock = useRef(false);
  const [params] = useSearchParams();
  const selectedPlan = params.get("plan");
  const draftContext = v?.context,
    draftAnalysis = draftContext?.analysis,
    draftProgress = selectedPlan
      ? v?.progress?.find((progress) => progress.plan_id === selectedPlan)
      : v?.progress?.[0],
    draftPlan = v?.records?.plans.find(
      (candidate) => candidate.id === draftProgress?.plan_id,
    ),
    draftRun = v?.runs?.find((run) => run.run_id === draftProgress?.run_id),
    recordedRecommendation = draftRun?.recommendation?.recommended_next_step;
  useEffect(() => {
    if (
      caseId !== "QE-004" ||
      !draftPlan ||
      !draftContext ||
      !draftAnalysis ||
      draftProgress?.submitted_at
    )
      return;
    const observed = draftAnalysis.observed_rate_bps / 100;
    const baseline =
      draftAnalysis.baseline_rate_bps === null
        ? "an unknown baseline"
        : `${draftAnalysis.baseline_rate_bps / 100}% baseline`;
    setSubmissionSubject(
      `QE-004 recovery proposal for ${draftContext.exception.lot_id}`,
    );
    setSubmissionRecommendation(
      recordedRecommendation ||
        `Keep ${draftContext.exception.lot_id} on hold, investigate and qualify the affected test setup, execute only a Quality-authorized controlled recovery, and protect ${draftContext.exception.milestone_id} using ${draftAnalysis.eligible_quantity} eligible units while resolving the ${draftAnalysis.gap_quantity}-unit gap.`,
    );
    setSubmissionContext(
      `Final-test yield is ${observed}% versus the approved ${baseline}. ${draftAnalysis.held_quantity} units remain held and contribute no eligible supply. Current eligible released supply is ${draftAnalysis.eligible_quantity} units against ${draftAnalysis.requested_quantity} requested. ${draftAnalysis.gap_value_exposure_cents == null ? "The financial exposure has not been valued." : `${money(draftAnalysis.gap_value_exposure_cents)} of potential shipment value is exposed by the ${draftAnalysis.gap_quantity}-unit gap, using the disclosed synthetic ${money(draftAnalysis.planning_unit_value_cents || 0)} per-unit planning assumption.`} ${draftAnalysis.first_pass_shortfall_value_cents == null ? "" : `${draftAnalysis.first_pass_shortfall_quantity} fewer first-pass passes than baseline represent ${money(draftAnalysis.first_pass_shortfall_value_cents)} of potential shipment value deferred.`} These are planning exposures, not realized lost revenue or margin. Failure concentration is evidence to investigate, not an established root cause. Customer commitment, allocation, and lot disposition remain unchanged.`,
    );
    setOperatorNotes("");
  }, [
    caseId,
    draftPlan?.id,
    draftProgress?.submitted_at,
    draftContext?.context_digest,
    draftAnalysis,
    draftContext,
    recordedRecommendation,
  ]);
  if (!host || !v)
    return (
      <Empty>
        {caseId} source context is not available.{" "}
        <button onClick={() => void host?.refresh()}>Refresh</button>
      </Empty>
    );
  const c = v.context,
    a = c?.analysis,
    p = selectedPlan
      ? v.progress?.find((p) => p.plan_id === selectedPlan)
      : v.progress?.[0],
    plan = v.records?.plans.find((x) => x.id === p?.plan_id),
    decision = v.records?.decisions.find((x) => x.plan_id === plan?.id);
  const current =
      !!c &&
      !!v.source_available &&
      !host.error &&
      v.status !== "stale" &&
      (!selectedPlan || !!p) &&
      v.runs?.find((r) => r.run_id === p?.run_id)?.business_outcome !== "stale",
    busy = !!host.busy || (v.runs || []).some((r) => r.status === "running");
  const ref =
    p && plan
      ? {
          run_id: p.run_id,
          plan_id: plan.id,
          plan_version: plan.plan_version,
          plan_digest: plan.plan_digest,
        }
      : null;
  const action = async (path: string, body: unknown) => {
    if (lock.current) return;
    lock.current = true;
    setError("");
    try {
      await host.act(path, body);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
    }
  };
  const start = async () => {
    const key = `stratos.quality.invocation.${caseId}`;
    let id = sessionStorage.getItem(key);
    if (!id) {
      id = "ui_" + crypto.randomUUID().replaceAll("-", "");
      sessionStorage.setItem(key, id);
    }
    if (lock.current) return;
    lock.current = true;
    setError("");
    try {
      await host.act(`/cases/${caseId}/investigations`, {
        invocation_id: id,
        change_id: caseId,
        workflow_id: "yield_exception_recovery",
      });
      sessionStorage.removeItem(key);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
    }
  };
  const submitRecovery = async () => {
    if (!ref || !host || lock.current) return;
    const key = `stratos.quality.submission.${ref.run_id}`;
    let submissionId = sessionStorage.getItem(key);
    if (!submissionId) {
      submissionId = "ui_" + crypto.randomUUID().replaceAll("-", "");
      sessionStorage.setItem(key, submissionId);
    }
    await action("/quality-recovery/submit", {
      ...ref,
      submission_id: submissionId,
      subject: submissionSubject,
      recommendation: submissionRecommendation,
      business_context: submissionContext,
      operator_notes: operatorNotes,
    });
    sessionStorage.removeItem(key);
  };
  return (
    <div className="cp-case-page cp-case-quality">
      <CaseHeader
        id={caseId}
        title={
          caseId === "QE-011"
            ? "Final-test anomaly"
            : "Yield / Quality Exception"
        }
        action={
          <div className="cp-case-heading-actions">
            {caseId === "QE-004" && (
              <AllowedAction caseId={caseId} action="investigate">
                <button
                  className={
                    plan &&
                    ((!p?.submitted_at &&
                      canAct(host.capabilities, caseId, "escalate")) ||
                      (!decision &&
                        p?.submitted_at &&
                        canAct(host.capabilities, caseId, "review")))
                      ? "cp-button"
                      : "cp-primary"
                  }
                  disabled={
                    !current ||
                    busy ||
                    !canAct(host.capabilities, caseId, "investigate")
                  }
                  onClick={() => void start()}
                >
                  <Play size={15} />
                  {v.runs?.some((r) => r.status === "running")
                    ? "Investigating…"
                    : "Run investigation"}
                </button>
              </AllowedAction>
            )}
            {caseId === "QE-004" &&
              plan &&
              !p?.submitted_at &&
              canAct(host.capabilities, caseId, "escalate") && (
                <a
                  className="cp-button cp-primary cp-handoff-shortcut"
                  href="#operator-handoff"
                >
                  <Send size={16} /> Review & submit recommendation
                </a>
              )}
            {caseId === "QE-004" &&
              plan &&
              p?.submitted_at &&
              !decision &&
              canAct(host.capabilities, caseId, "review") && (
                <a className="cp-button cp-primary" href="#decision">
                  Review recovery plan <ArrowRight size={15} />
                </a>
              )}
          </div>
        }
      />
      {selectedPlan && !p && (
        <p className="cp-error" role="alert">
          This exact source plan is unavailable. No replacement has been
          selected.
        </p>
      )}
      <ActionAccess
        caseId={caseId}
        action="investigate"
        ready={current && !busy}
        reason={
          busy
            ? "Investigation or action in progress."
            : "Refresh current sources before acting."
        }
      />
      <div className="cp-inline cp-case-command">
        <StatusText tone={qualityAttention(v) ? "warning" : "neutral"}>
          {words(v.status)}
        </StatusText>
        <button onClick={() => void host.refresh()}>
          Refresh source state
        </button>
      </div>
      <RuntimeLabel caseId={caseId} run={v.runs?.[0]} />
      {(error || host.error) && (
        <p className="cp-error" role="alert">
          {error || host.error}
        </p>
      )}
      {!current && (
        <p role="alert">
          Current source unavailable or changed. Refresh and reassess before
          acting.
        </p>
      )}
      {v.runs?.[0] && <RunFindings run={v.runs[0]} />}
      {c && a && (
        <>
          <details className="cp-secondary-content">
            <summary>Signal & comparison</summary>
            <Section
              title="Signal & comparison"
              note={`${words(c.observation.test_stage)} · ${c.observation.test_program_version || "Program unknown"}`}
            >
              <div className="cp-quality-signal">
                <strong>{a.observed_rate_bps / 100}%</strong>
                <span>
                  vs{" "}
                  {a.baseline_rate_bps === null
                    ? "unknown"
                    : `${a.baseline_rate_bps / 100}%`}{" "}
                  approved baseline
                </span>
              </div>
              <StatusText
                tone={a.comparable === "true" ? "neutral" : "warning"}
              >
                Comparable: {a.comparable} ·{" "}
                {a.confirmed_degradation
                  ? "Comparable pass-rate decline"
                  : "Degradation not confirmed"}
              </StatusText>
              <p>{a.comparison_reasons.map(words).join(" · ")}</p>
              <Facts
                rows={[
                  [
                    "Configuration",
                    `${c.exception.configuration_id} · ${c.observation.product_revision} · Source version ${c.observation.configuration_content_version}`,
                  ],
                  [
                    "Conditions / population",
                    `${c.observation.conditions_id || "Unknown"} / ${c.observation.population || "Unknown"}`,
                  ],
                  [
                    "Equipment / sites",
                    `${c.observation.equipment_family || "Unknown"} / ${c.observation.sites.join(", ")}`,
                  ],
                  [
                    "Observed results",
                    `${c.observation.passed_quantity} passed / ${c.observation.tested_quantity} tested · ${c.observation.failed_quantity} failed`,
                  ],
                ]}
              />
            </Section>
          </details>
          <details className="cp-secondary-content">
            <summary>Material & supply impact</summary>
            <Section
              title="Material & supply impact"
              note="First-pass passes and released inventory are separate source states."
            >
              <div className="cp-quality-quantities">
                {[
                  ["Affected physical lot", a.affected_physical_quantity],
                  ["First-pass passes · held", a.first_pass_pass_quantity],
                  ["Held quantity", a.held_quantity],
                  ["Eligible from affected lot", a.affected_eligible_quantity],
                  ["Current eligible supply", a.eligible_quantity],
                  ["Requested milestone", a.requested_quantity],
                  ["Current gap", a.gap_quantity],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
              <div
                className="cp-quality-bar"
                role="img"
                aria-label={`${a.eligible_quantity} eligible supply against ${a.requested_quantity} requested; ${a.gap_quantity} gap`}
              >
                <span
                  style={{
                    width: `${Math.min(100, (a.eligible_quantity / Math.max(1, a.requested_quantity)) * 100)}%`,
                  }}
                />
              </div>
              <p>
                {c.exception.lot_id} remains{" "}
                {words(
                  c.material.find((m) => m.lot_id === c.exception.lot_id)
                    ?.disposition || "unknown",
                )}
                . First-pass passes do not authorize shipment. Current eligible
                supply {a.gap_quantity ? "does not cover" : "covers"} the
                requested milestone quantity.
              </p>
              <Facts
                rows={[
                  [
                    "Milestone",
                    `${c.exception.milestone_id} · Baseline ${date(String(c.milestone.baseline_at))}`,
                  ],
                  [
                    "Customer demand",
                    `${c.exception.order_id} · ${c.order.quantity} units · ${date(String(c.order.committed_delivery_at))}`,
                  ],
                  ["Customer commitment", "Unchanged by this workflow"],
                ]}
              />
            </Section>
          </details>
          <details className="cp-secondary-content">
            <summary>Evidence, hypotheses & approved procedure</summary>
            <Section
              title="Evidence & investigation"
              note="Facts, hypotheses and established cause remain distinct."
            >
              <Facts
                rows={[
                  [
                    "Failures by site",
                    Object.entries(a.failed_by_site)
                      .map(([k, n]) => `${k}: ${n}`)
                      .join(" · "),
                  ],
                  [
                    "Interpretation",
                    "Site concentration is a correlation. Equipment contribution remains a hypothesis requiring investigation.",
                  ],
                  ["Established root cause", a.root_cause || "Not established"],
                  [
                    "Historical Validation evidence",
                    a.evidence_status === "available"
                      ? c.evidence.map((e) => String(e.id)).join(", ")
                      : "Missing · Unknown",
                  ],
                  [
                    "Approved procedure",
                    c.procedure
                      ? `${c.procedure.id} · ${c.procedure.owner}`
                      : "Missing · No standard handoff authorized",
                  ],
                ]}
              />
              <p>
                Historical validation evidence does not grant lot release or
                customer acceptance.
              </p>
              {c.procedure && (
                <ul>
                  {c.procedure.tasks.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              )}
            </Section>
          </details>
          <Section
            title="Recovery options"
            note="Parallel investigation and supply planning; quantity effects are planning context."
          >
            <div className="cp-business-options" aria-label="Recovery options">
              {a.options.map((option) => (
                <article className="cp-business-option" key={String(option.id)}>
                  <div className="cp-option-top">
                    <StatusText tone="neutral">
                      {option.required_role
                        ? words(String(option.required_role))
                        : "Standard coordination"}
                    </StatusText>
                    <span>{String(option.scope)}</span>
                  </div>
                  <h3>{words(String(option.id))}</h3>
                  <p>{String(option.expected_effect)}</p>
                  <div className="cp-option-bottom">
                    <strong>
                      {String(option.quantity_impact)}{" "}
                      <small>units · planning context</small>
                    </strong>
                    <span>{String(option.owner)}</span>
                  </div>
                  <details>
                    <summary>Timing, prerequisites & authority</summary>
                    <p>{String(option.schedule_impact)}</p>
                    <ul>
                      {(Array.isArray(option.prerequisites)
                        ? option.prerequisites
                        : []
                      ).map((item) => (
                        <li key={String(item)}>{String(item)}</li>
                      ))}
                    </ul>
                    <p>
                      Cost:{" "}
                      {option.cost_cents == null
                        ? "Unknown"
                        : money(Number(option.cost_cents))}
                    </p>
                  </details>
                </article>
              ))}
            </div>
          </Section>
          {caseId === "QE-004" && plan && (
            <div id="operator-handoff">
              <Section
                title="Review & submit recovery recommendation"
                note="Program Operator → Program Owner. Your submitted words become the review proposal."
              >
                {p?.submitted_at ? (
                  <div className="cp-quality-submission" data-state="submitted">
                    <StatusText tone="good">
                      Submitted to Program Owner
                    </StatusText>
                    <h3>{p.submission_subject}</h3>
                    <p>
                      <strong>Recommended action</strong>
                      <span className="cp-preserve-lines">
                        {p.submitted_recommendation}
                      </span>
                    </p>
                    <p>
                      <strong>Evidence and business context</strong>
                      {p.submitted_business_context}
                    </p>
                    {p.operator_notes && (
                      <p>
                        <strong>Operator notes</strong>
                        {p.operator_notes}
                      </p>
                    )}
                    <small>
                      Submitted by {p.submitted_by} ·{" "}
                      {date(p.submitted_at, true)}
                    </small>
                  </div>
                ) : canAct(host.capabilities, caseId, "escalate") ? (
                  <form
                    className="cp-escalation-form cp-quality-handoff-form"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void submitRecovery();
                    }}
                  >
                    <div className="cp-form-callout">
                      <span className="tr-label">
                        Agent recommendation · Draft
                      </span>
                      <strong>
                        Review the full recovery recommendation below.
                      </strong>
                      <p>
                        Edit the recommendation and context below. Submission
                        creates the Program Owner queue item; it does not
                        approve or execute the plan.
                      </p>
                    </div>
                    <label>
                      Proposal title
                      <input
                        value={submissionSubject}
                        onChange={(event) =>
                          setSubmissionSubject(event.target.value)
                        }
                        required
                        minLength={3}
                        maxLength={180}
                      />
                    </label>
                    <label>
                      Recommended recovery action
                      <textarea
                        value={submissionRecommendation}
                        onChange={(event) =>
                          setSubmissionRecommendation(event.target.value)
                        }
                        required
                        rows={5}
                        maxLength={3000}
                      />
                    </label>
                    <label>
                      Evidence and business context
                      <textarea
                        value={submissionContext}
                        onChange={(event) =>
                          setSubmissionContext(event.target.value)
                        }
                        required
                        rows={5}
                        maxLength={3000}
                      />
                    </label>
                    <label>
                      Operator notes
                      <textarea
                        value={operatorNotes}
                        onChange={(event) =>
                          setOperatorNotes(event.target.value)
                        }
                        rows={3}
                        maxLength={2000}
                      />
                    </label>
                    <div className="cp-form-actions">
                      <small>
                        The Program Owner will receive these exact words
                        together with the immutable source plan and its evidence
                        binding.
                      </small>
                      <button
                        className="cp-primary"
                        type="submit"
                        disabled={!current || busy}
                      >
                        <Send size={16} /> Submit to Program Owner
                      </button>
                    </div>
                  </form>
                ) : (
                  <Empty>
                    The recovery draft has not been submitted. A Program
                    Operator must review and send it before Program Owner
                    approval is available.
                  </Empty>
                )}
              </Section>
            </div>
          )}
        </>
      )}
      {caseId === "QE-011" && !plan ? (
        <Section
          title="Standard investigation handoff"
          note="Touchless / standard quality investigation"
        >
          <p>
            {p?.status === "handoff_verified"
              ? "Handoff verified. No human approval required for executed actions. Lot remains on hold; root cause unresolved; customer commitment unchanged."
              : p?.status === "review_required"
                ? "Standard policy ineligible. Review the policy findings before any handoff."
                : "Agents validate the approved standard policy before routing the Manufacturing investigation."}
          </p>
          {p?.policy_reasons?.map((reason) => (
            <p key={reason}>{reason}</p>
          ))}
        </Section>
      ) : (
        <div id="decision">
          <Section
            title="Recovery decision"
            note="Program Owner approval is separate from Quality, allocation and commercial authority."
          >
            {!plan ? (
              <Empty>
                No current recovery plan. Complete the connected investigation
                first.
              </Empty>
            ) : (
              <>
                <div className="cp-quality-decision-hero">
                  <div>
                    <StatusText
                      tone={
                        decision?.decision === "approve"
                          ? "good"
                          : decision?.decision === "reject"
                            ? "warning"
                            : p?.submitted_at
                              ? "warning"
                              : "neutral"
                      }
                    >
                      {decision
                        ? words(decision.decision)
                        : p?.submitted_at
                          ? "Program Owner review"
                          : "Awaiting operator submission"}
                    </StatusText>
                    <h3>
                      {p?.submission_subject ||
                        `Recovery planning for ${c?.exception.lot_id || "the held lot"}`}
                    </h3>
                    <p>
                      <span className="cp-preserve-lines">
                        {p?.submitted_recommendation ||
                          "The agent draft must be reviewed and submitted by the Program Operator before this decision becomes available."}
                      </span>
                    </p>
                  </div>
                  <div className="cp-quality-decision-impact">
                    <span>Planning quantity</span>
                    <strong>{a?.eligible_quantity ?? "—"} units</strong>
                    <small>
                      {a?.gap_quantity ?? "—"}-unit gap remains open
                    </small>
                  </div>
                </div>
                {p?.submitted_business_context && (
                  <div className="cp-quality-review-context">
                    <strong>Evidence and business context</strong>
                    <p>{p.submitted_business_context}</p>
                    {p.operator_notes && (
                      <p>
                        <strong>Operator notes:</strong> {p.operator_notes}
                      </p>
                    )}
                  </div>
                )}
                <div className="cp-quality-boundaries">
                  <article>
                    <CheckCircle2 size={20} aria-hidden="true" />
                    <div>
                      <strong>If approved</strong>
                      <p>
                        Stratos may create one Program Planner recovery task
                        tied to this exact plan and the open investigation.
                      </p>
                    </div>
                  </article>
                  <article>
                    <ShieldCheck size={20} aria-hidden="true" />
                    <div>
                      <strong>Still requires separate authority</strong>
                      <p>
                        Lot release, Quality disposition, retest authorization,
                        inventory allocation and customer commitment changes.
                      </p>
                    </div>
                  </article>
                </div>
                <details className="tr-details">
                  <summary>Exact source binding</summary>
                  <p>
                    {plan.id} · Version {plan.plan_version}
                  </p>
                  <p className="cp-digest">
                    Content fingerprint: {plan.plan_digest}
                  </p>
                  {p?.submission_digest && (
                    <p className="cp-digest">
                      Operator handoff fingerprint: {p.submission_digest}
                    </p>
                  )}
                </details>
                {decision && (
                  <p className="cp-quality-decision-result">
                    <strong>{words(decision.decision)}</strong> by{" "}
                    {decision.signer_identity}
                    {decision.comment ? ` · ${decision.comment}` : ""}
                  </p>
                )}
                {!decision &&
                  p?.submitted_at &&
                  canAct(host.capabilities, caseId, "review") && (
                    <div className="cp-quality-review-actions">
                      <label>
                        Decision comment
                        <textarea
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                          maxLength={1500}
                          rows={3}
                          placeholder="Summarize the reason for this decision"
                        />
                      </label>
                      <ActionAccess
                        caseId={caseId}
                        action="review"
                        ready={current && !busy}
                        reason="Refresh current source records before deciding."
                      />
                      <div className="cp-inline">
                        <button
                          className="cp-primary"
                          disabled={!current || busy}
                          onClick={() =>
                            void action("/quality-recovery/review", {
                              ...ref,
                              decision: "approve",
                              comment,
                            })
                          }
                        >
                          Approve recovery plan
                        </button>
                        <button
                          disabled={!current || busy}
                          onClick={() =>
                            void action("/quality-recovery/review", {
                              ...ref,
                              decision: "reject",
                              comment,
                            })
                          }
                        >
                          Reject recovery plan
                        </button>
                      </div>
                    </div>
                  )}
                {!decision &&
                  !p?.submitted_at &&
                  canAct(host.capabilities, caseId, "review") && (
                    <div
                      className="cp-quality-review-actions"
                      aria-label="Program Owner decision controls"
                    >
                      <p>
                        The Program Operator has not submitted this recovery
                        recommendation yet. These controls become available
                        after submission.
                      </p>
                      <div className="cp-inline">
                        <button className="cp-primary" disabled>
                          Approve recovery plan
                        </button>
                        <button disabled>Reject recovery plan</button>
                      </div>
                    </div>
                  )}
                {decision?.decision === "approve" && (
                  <ActionAccess
                    caseId={caseId}
                    action="execute"
                    ready={current && p?.status !== "verified"}
                    reason={
                      p?.status === "verified"
                        ? "Recovery task readback already verified. Quality disposition remains open."
                        : "Refresh the current plan and decision before execution."
                    }
                  />
                )}
                {decision?.decision === "approve" && (
                  <AllowedAction caseId={caseId} action="execute">
                    <button
                      className="cp-primary"
                      disabled={
                        !current ||
                        busy ||
                        !canAct(host.capabilities, caseId, "execute") ||
                        p?.status === "verified"
                      }
                      onClick={() =>
                        void action("/quality-recovery/execute", ref)
                      }
                    >
                      Execute approved recovery task
                    </button>
                  </AllowedAction>
                )}
              </>
            )}
          </Section>
        </div>
      )}
      <Section
        title="Handoff & verification"
        note="Each business action is confirmed by reading the resulting source-system record."
      >
        {p && (
          <div className="cp-verification-summary">
            <StatusText tone={p.status === "verified" ? "good" : "neutral"}>
              {p.status === "draft_ready"
                ? "Draft ready"
                : p.status === "awaiting_review"
                  ? "Waiting for Program Owner"
                  : p.status === "approved"
                    ? "Approved · Planner task pending"
                    : p.status === "verified"
                      ? "Recovery coordination complete"
                      : words(p.status)}
            </StatusText>
            <p>
              {p.status === "draft_ready"
                ? "The quality investigation is routed and the recovery draft is ready for Program Operator review. Nothing has been sent to the Program Owner yet."
                : p.status === "awaiting_review"
                  ? "The Program Operator submitted the recommendation. The Program Owner must decide before a Planner task can be created."
                  : p.status === "approved"
                    ? "The Program Owner approved the exact plan. The authorized Planner task has not been created yet."
                    : p.status === "verified"
                      ? "The approved four-part recovery recommendation was written to Program Planner and independently matched to the Manufacturing decision. Assigned downstream work is now visible in the source systems. Product Quality investigation and lot disposition remain open."
                      : "Review the action cards below for the latest confirmed source state."}
            </p>
          </div>
        )}
        {p &&
          Object.values(p.steps || {}).map((s) => (
            <article className="cp-verification-step" key={s.operation}>
              <CheckCircle2
                size={21}
                aria-hidden="true"
                data-confirmed={s.status === "verified"}
              />
              <div>
                <strong>
                  {s.operation === "investigate"
                    ? "Manufacturing received the investigation"
                    : s.operation === "prepare"
                      ? "Recovery draft recorded"
                      : s.operation === "review"
                        ? "Program Owner decision recorded"
                        : "Program Planner recovery task recorded"}
                </strong>
                <p>
                  {s.operation === "investigate"
                    ? "The approved investigation procedure was routed to Product / Test Engineering."
                    : s.operation === "prepare"
                      ? "The source-bound recovery plan was created for operator review."
                      : s.operation === "review"
                        ? "The decision matches the exact submitted plan version."
                        : "The task links the approved plan, open investigation and current supply context."}
                </p>
                <small>{traceStatus(s.status)}</small>
                <details className="tr-details">
                  <summary>Source receipt</summary>
                  <p>{s.source_id || "No source receipt recorded"}</p>
                  {s.error_code && <p>{s.error_code}</p>}
                </details>
              </div>
            </article>
          ))}
        {p &&
          !p.decision &&
          ["outcome_unknown", "failed", "verification_failed"].includes(
            p.status,
          ) && (
            <AllowedAction caseId={caseId} action="reconcile">
              <button
                disabled={
                  !current ||
                  busy ||
                  !canAct(host.capabilities, caseId, "reconcile")
                }
                onClick={() =>
                  void action("/quality-recovery/reconcile", {
                    run_id: p.run_id,
                  })
                }
              >
                Reconcile investigation handoff
              </button>
            </AllowedAction>
          )}
        {!!v.records?.investigations.length && (
          <p className="cp-source-outcome">
            <strong>Investigation owner:</strong>{" "}
            {v.records.investigations[0].owner} ·{" "}
            {v.records.investigations[0].queue_id}
          </p>
        )}
        {!!v.records?.tasks.length && (
          <>
            <p className="cp-source-outcome">
              <strong>Planner outcome:</strong> Recovery task{" "}
              {v.records.tasks[0].id} is recorded for {v.records.tasks[0].owner}
              . No allocation, lot release or customer commitment changed.
            </p>
            <p className="cp-source-outcome">
              <strong>Validation status:</strong> No new lab job or result is
              created by QE-004. Historical evidence is reference material; the
              open Manufacturing investigation owns the next physical work.
            </p>
          </>
        )}
        <div className="cp-inline">
          {[
            ["manufacturing", "Manufacturing exception & investigation"],
            ["engineering", "Engineering procedure"],
            ["validation", "Historical validation evidence · Reference only"],
            ["programs", "Planner recovery task"],
            ["erp", "Customer demand"],
          ].map(([path, label]) => (
            <SourceLink key={path} to={`/${path}/quality/${caseId}`}>
              {label}
            </SourceLink>
          ))}
        </div>
      </Section>
      {(v.runs || []).length > 1 && (
        <details className="cp-secondary-content">
          <summary>Earlier investigations ({v.runs!.length - 1})</summary>
          {v.runs!.slice(1).map((run) => (
            <p key={run.run_id}>
              <Link to={`/control/runs/${run.run_id}`}>
                {words(run.status)} · {date(run.started_at, true)}
              </Link>
            </p>
          ))}
        </details>
      )}
      <KnowledgeRunEvidence caseId={caseId} />
    </div>
  );
}
