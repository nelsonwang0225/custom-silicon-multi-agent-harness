import "./rethink-cases.css";
import { useLocation } from "react-router-dom";
import { Link, needsYourReview } from "./access";
import {
  Check,
  ArrowRight,
  FileText,
  LockKeyhole,
  AlertTriangle,
  ShieldCheck,
  Layers3,
  FlaskConical,
  PackageCheck,
} from "lucide-react";
import { useEffect, type ReactNode } from "react";
import { useHost } from "./host";
import { useControl, type CaseData, money, words } from "./data";
import { Crumbs, Heading, StatusText, Empty, SourceLink } from "./ui";
import { caseTone } from "./integration";
import {
  caseQuestions,
  casePresentation,
  humanDecision,
  lifecycle,
  nextBusinessStep,
  standardRunHandoff,
} from "./experience-model";
import { ActionAccess } from "./persona";

export function CaseHeader({
  id,
  title,
  action,
}: {
  id: string;
  title: string;
  action?: ReactNode;
}) {
  const host = useHost(),
    { data } = useControl(),
    s = host?.data?.case_summaries?.find((s) => s.change_id === id);
  const location = useLocation();
  useEffect(() => {
    if (location.hash !== "#decision" || !host?.data) return;
    const frame = requestAnimationFrame(() => {
      const el = document.getElementById("decision");
      if (el) {
        el.setAttribute("tabindex", "-1");
        el.focus({ preventScroll: true });
        el.scrollIntoView({ block: "start" });
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [location.pathname, location.search, location.hash, !!host?.data]);
  const d = ["completed_technical", "completed_recovery"].includes(
      s?.state || "",
    )
      ? undefined
      : humanDecision(host?.data, id),
    presentation = casePresentation(
      host?.data,
      id,
      data?.cases.find((c) => c.change.id === id),
      title,
    ),
    standardComplete =
      id === "CR-019" &&
      standardRunHandoff(host?.data?.standard)?.status === "handoff_verified",
    steps =
      host?.data && !host.error && s?.source_available
        ? lifecycle(host.data, id)
        : [];
  const path =
    d?.href +
    (d && ["QE-004", "QE-011", "DR-009"].includes(id) ? "#decision" : "");
  return (
    <div className="cp-case-hero" data-case-hero={id}>
      <Crumbs
        items={[
          { label: "Overview", to: "/control/overview" },
          { label: "Helios Atlas Inference", to: "/control/programs/PRG-A17" },
          { label: id },
        ]}
      />
      <Heading
        eyebrow={`${id} · Helios Atlas Inference`}
        title={presentation.title}
        description={presentation.summary || caseQuestions[id]}
        action={action}
      />
      {presentation.originalDescription && (
        <details className="cp-original-request">
          <summary>
            <FileText size={15} aria-hidden="true" /> View original request
          </summary>
          <div>
            <small>Original source description</small>
            <p>{presentation.originalDescription}</p>
          </div>
        </details>
      )}
      {s ? (
        <section
          className="cp-case-outcome"
          aria-label={`${id} current case state`}
          data-case-state={s.state}
        >
          <div>
            <StatusText tone={host?.error ? "warning" : caseTone(s)}>
              {host?.error
                ? "Stale read · Refresh required"
                : standardComplete
                  ? "Workflow complete"
                  : s.state_label}
            </StatusText>
            <p>
              {host?.error
                ? "Current source unavailable. Refresh before acting."
                : standardComplete
                  ? "Validation Operations received and verified the handoff package."
                  : s.detail}
            </p>
          </div>
          <div className="cp-case-next">
            <small>
              {standardComplete ? "Downstream status" : "Next step"}
            </small>
            <strong>
              {standardComplete
                ? "Lab authorization owned by Validation Operations"
                : nextBusinessStep(host?.data, s)}
            </strong>
            {d && (
              <Link className="cp-text-link" to={path}>
                {needsYourReview(host?.capabilities, d) ? "Review" : "Inspect"}{" "}
                {d.kind === "engineering_evidence" ? "evidence" : "decision"}{" "}
                <ArrowRight size={15} />
              </Link>
            )}
            {!d && id === "QE-004" && s.state === "draft_ready" && (
              <Link className="cp-text-link" to="#operator-handoff">
                Review recommendation <ArrowRight size={15} />
              </Link>
            )}
          </div>
        </section>
      ) : (
        <Empty>{host?.error || "Reading current workflow state…"}</Empty>
      )}
      {steps.length > 0 && (
        <ol className="cp-lifecycle" aria-label={`${id} lifecycle`}>
          {steps.map((step, i) => (
            <li
              key={step.label}
              data-stage-state={step.state}
              aria-current={step.state === "current" ? "step" : undefined}
            >
              <span className="cp-stage-icon">
                {step.state === "done" ? (
                  <Check size={15} />
                ) : step.state === "failed" ? (
                  <AlertTriangle size={15} />
                ) : (
                  <span>{i + 1}</span>
                )}
              </span>
              <span>
                <strong>{step.label}</strong>
                <small>{step.detail}</small>
              </span>
            </li>
          ))}
        </ol>
      )}
      <CaseVisual id={id} c={data?.cases.find((c) => c.change.id === id)} />
      {d && (
        <ActionAccess
          caseId={id}
          action={
            d.kind === "engineering_evidence" ? "review_evidence" : "review"
          }
        />
      )}
      {s && (
        <details className="cp-boundary">
          <summary>
            <LockKeyhole size={14} /> Authority & source
          </summary>
          <p>{s.boundary}</p>
          <SourceLink to={s.source_href}>Open source record</SourceLink>
        </details>
      )}
    </div>
  );
}
function EvidenceCell({
  assessed,
  match,
  value,
}: {
  assessed: boolean;
  match: boolean;
  value: string;
}) {
  return (
    <span
      className="cp-coverage-cell"
      data-match={assessed ? String(match) : "pending"}
    >
      {assessed ? (
        match ? (
          <Check size={15} aria-hidden="true" />
        ) : (
          <AlertTriangle size={14} aria-hidden="true" />
        )
      ) : (
        <span aria-hidden="true">—</span>
      )}
      <span>
        {value}
        <small>{assessed ? (match ? "Matches" : "Gap") : "Not assessed"}</small>
      </span>
    </span>
  );
}

export function CaseVisual({ id, c }: { id: string; c?: CaseData }) {
  const host = useHost(),
    h = host?.data,
    source = useControl();
  if (source.error)
    return (
      <Empty>Current comparison unavailable. Refresh source records.</Empty>
    );
  if (id === "CR-017" && c) {
    const run = h?.runs.find(
      (item) => !item.invocation_id.startsWith("ui_evidence_"),
    );
    const assessed =
      !host?.error &&
      h?.source_available !== false &&
      run?.status === "completed" &&
      !!run.specialists?.some(
        (item) =>
          item.specialist === "validation_evidence" &&
          item.status === "completed",
      );
    return (
      <section
        className="cp-case-story cp-change-story"
        aria-label="Requirement and evidence comparison"
      >
        <article className="cp-story-surface cp-scope-story">
          <div className="cp-story-kicker">
            <FlaskConical size={17} /> Workload scope
          </div>
          <h2>The request changes. The criteria stay.</h2>
          <div className="cp-scope-comparison">
            <div>
              <small>Approved workload</small>
              <strong>
                {Math.max(...c.baselineWorkload.context_bins).toLocaleString()}
              </strong>
              <span>tokens · {c.baselineWorkload.total_suite_minutes} min</span>
            </div>
            <ArrowRight size={21} aria-hidden="true" />
            <div>
              <small>Requested workload</small>
              <strong>
                {Math.max(...c.targetWorkload.context_bins).toLocaleString()}
              </strong>
              <span>tokens · {c.targetWorkload.total_suite_minutes} min</span>
            </div>
          </div>
          <p className="cp-story-boundary">
            <ShieldCheck size={16} /> Existing acceptance criteria remain
            unchanged.
          </p>
          <SourceLink to="/engineering/changes/CR-017">
            Read customer requirement
          </SourceLink>
        </article>
        <article className="cp-story-surface cp-coverage-story">
          <div className="cp-story-heading">
            <div>
              <div className="cp-story-kicker">Evidence coverage</div>
              <h2>Does each record apply?</h2>
            </div>
            <StatusText tone={assessed ? "warning" : "neutral"}>
              {assessed
                ? "Assessment recorded"
                : run?.status === "running"
                  ? "Assessing"
                  : "Not assessed"}
            </StatusText>
          </div>
          <div className="cp-coverage-scroll">
            <table className="cp-coverage-matrix">
              <thead>
                <tr>
                  <th>Evidence</th>
                  <th>Configuration</th>
                  <th>Workload</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {c.coverage.items.map((item) => (
                  <tr key={item.result.id}>
                    <th scope="row">
                      <Link to={`?tab=evidence&evidence=${item.result.id}`}>
                        {item.result.id}
                      </Link>
                    </th>
                    <td>
                      <EvidenceCell
                        assessed={assessed}
                        match={item.result.configuration_id === c.config.id}
                        value={item.result.configuration_id}
                      />
                    </td>
                    <td>
                      <EvidenceCell
                        assessed={assessed}
                        match={
                          item.result.workload_profile_id ===
                          c.targetWorkload.id
                        }
                        value={item.result.workload_profile_id}
                      />
                    </td>
                    <td>
                      <EvidenceCell
                        assessed={assessed}
                        match={
                          item.result.actual_suite_minutes >=
                          c.targetWorkload.total_suite_minutes
                        }
                        value={`${item.result.actual_suite_minutes} / ${c.targetWorkload.total_suite_minutes} min`}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="cp-story-caption">
            {assessed
              ? "A passing record must match the full requested scope. Open a record for all coverage checks."
              : "Source observations are available. Applicability appears after the investigation finishes."}
          </p>
          <Link className="cp-text-link" to="?tab=options">
            Compare timing and options <ArrowRight size={14} />
          </Link>
        </article>
      </section>
    );
  }
  if (!h) return null;
  const summary = h.case_summaries?.find((item) => item.change_id === id);
  if (!summary?.source_available || host?.error)
    return (
      <Empty>Current comparison unavailable. Refresh source records.</Empty>
    );
  if (id === "CR-019") {
    const v = h.standard,
      eligibility =
        v?.runs[0]?.status === "completed" ? v.eligibility : undefined,
      handoff = standardRunHandoff(v);
    const verified = handoff?.status === "handoff_verified";
    return (
      <section
        className="cp-case-story cp-standard-story"
        aria-label="Standard policy and handoff"
      >
        <article className="cp-story-surface">
          <div className="cp-story-kicker">
            <ShieldCheck size={17} /> Approved scope
          </div>
          <strong className="cp-story-number">
            {eligibility
              ? `${eligibility.checks.filter((check) => check.passed).length} / ${eligibility.checks.length}`
              : "—"}
          </strong>
          <h2>
            {eligibility ? "Scope checks matched" : "Scope match pending"}
          </h2>
          <p>
            {eligibility
              ? eligibility.touchless_eligible
                ? "Approved profile and procedure."
                : "Applicability requires review."
              : "The investigation has not established eligibility."}
          </p>
          {eligibility && (
            <a className="cp-text-link" href="#touchless-policy">
              Inspect policy checks <ArrowRight size={14} />
            </a>
          )}
        </article>
        <article className="cp-story-surface">
          <div className="cp-story-kicker">
            <Layers3 size={17} /> Evidence reuse
          </div>
          <strong className="cp-story-number">
            {eligibility ? eligibility.reusable_evidence_ids.length : "—"}
          </strong>
          <h2>
            {eligibility ? "Reusable evidence records" : "Eligibility pending"}
          </h2>
          <p>
            {eligibility
              ? "Historical evidence. No new test is implied."
              : "Reusable evidence is identified after assessment."}
          </p>
        </article>
        <article
          className="cp-story-surface cp-story-destination"
          data-verified={verified}
        >
          <div className="cp-story-kicker">
            <PackageCheck size={17} /> Validation Operations
          </div>
          <StatusText tone={verified ? "good" : "neutral"}>
            {verified
              ? "Handoff verified"
              : handoff?.package
                ? "Package prepared"
                : "Package pending"}
          </StatusText>
          <h2>{verified ? "Intake received." : "A bounded handoff."}</h2>
          <p>Lab authorization and physical testing remain downstream.</p>
          {handoff?.intake && (
            <SourceLink to={`/validation/intakes/${handoff.intake.id}`}>
              View created intake
            </SourceLink>
          )}
        </article>
      </section>
    );
  }
  if (id === "QE-011") {
    const view = h.autonomous_quality,
      context = view?.context,
      run = view?.runs?.[0],
      progress = view?.progress?.[0];
    if (!context) return null;
    const verified = progress?.status === "handoff_verified";
    return (
      <section
        className="cp-case-story cp-autonomous-story"
        aria-label="Autonomous investigation and source handoff"
      >
        <article className="cp-story-surface">
          <div className="cp-story-kicker">
            <ShieldCheck size={17} /> Autonomous quality investigation
          </div>
          <h2>A source event starts the work.</h2>
          <div className="cp-autonomous-journey">
            <div data-state="done">
              <Check size={17} />
              <strong>Manufacturing exception</strong>
              <span>
                {context.exception.id} · {context.exception.lot_id}
              </span>
            </div>
            <ArrowRight size={17} aria-hidden="true" />
            <div
              data-state={
                run?.status === "completed" ? "done" : run?.status || "pending"
              }
            >
              <FlaskConical size={17} />
              <strong>Specialist investigation</strong>
              <span>{run ? words(run.status) : "Waiting to start"}</span>
            </div>
            <ArrowRight size={17} aria-hidden="true" />
            <div data-state={verified ? "done" : "pending"}>
              <PackageCheck size={17} />
              <strong>Source handoff</strong>
              <span>
                {verified
                  ? "Routing independently verified"
                  : "Verification pending"}
              </span>
            </div>
          </div>
          <p className="cp-story-boundary">
            <LockKeyhole size={16} /> Only policy-qualified standard
            investigation routing is touchless.
          </p>
        </article>
        <article
          className="cp-story-surface cp-story-destination"
          data-verified={verified}
        >
          <div className="cp-story-kicker">Current responsibility</div>
          <StatusText
            tone={
              verified ? "good" : run?.status === "failed" ? "danger" : "agent"
            }
          >
            {verified
              ? "Handoff verified"
              : run?.status === "failed"
                ? "Investigation needs attention"
                : run?.status === "running"
                  ? "Agents investigating"
                  : "Source event received"}
          </StatusText>
          <h2>
            {verified
              ? "Manufacturing owns the next work."
              : "Check the scope, then route."}
          </h2>
          <p>
            Lot disposition, physical testing and customer commitments retain
            their existing authority.
          </p>
          <SourceLink to="/manufacturing/quality/QE-011">
            View Manufacturing investigation
          </SourceLink>
        </article>
      </section>
    );
  }
  if (id === "QE-004" || id === "QE-011") {
    const context = (id === "QE-011" ? h.autonomous_quality : h.quality)
        ?.context,
      a = context?.analysis;
    if (!context || !a) return null;
    const drop =
      a.baseline_rate_bps == null
        ? null
        : (a.baseline_rate_bps - a.observed_rate_bps) / 100;
    return (
      <section
        className="cp-case-story cp-yield-story"
        aria-label="Quality comparison and held material"
      >
        <article className="cp-story-surface">
          <div className="cp-story-kicker">First-pass final-test yield</div>
          <div className="cp-yield-headline">
            <strong className="cp-story-number">
              {a.observed_rate_bps / 100}
              <span>%</span>
            </strong>
            <div>
              <strong>
                {drop == null
                  ? "Baseline unavailable"
                  : `${Math.abs(drop)} percentage points ${drop >= 0 ? "below" : "above"} baseline`}
              </strong>
              <p>
                {a.comparable === "true"
                  ? "Comparable test conditions"
                  : "Comparison requires review"}
              </p>
            </div>
          </div>
          <div
            className="cp-yield-comparison"
            role="img"
            aria-label={`Observed ${a.observed_rate_bps / 100} percent; baseline ${a.baseline_rate_bps == null ? "unknown" : a.baseline_rate_bps / 100} percent`}
          >
            <div>
              <span>Baseline</span>
              <div>
                <i style={{ width: `${(a.baseline_rate_bps ?? 0) / 100}%` }} />
              </div>
              <strong>
                {a.baseline_rate_bps == null
                  ? "—"
                  : `${a.baseline_rate_bps / 100}%`}
              </strong>
            </div>
            <div>
              <span>{context.exception.lot_id}</span>
              <div>
                <i
                  className="cp-yield-observed"
                  style={{ width: `${a.observed_rate_bps / 100}%` }}
                />
              </div>
              <strong>{a.observed_rate_bps / 100}%</strong>
            </div>
          </div>
          <p className="cp-story-caption">
            {context.observation.passed_quantity} passed /{" "}
            {context.observation.tested_quantity} tested · First attempt
          </p>
          {!!Object.keys(context.observation.site_counts).length && (
            <div className="cp-site-comparison">
              <div className="cp-story-heading">
                <h3>Compare test sites</h3>
                <span>Source observations</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Site</th>
                    <th>Passed / tested</th>
                    <th>Pass rate</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(context.observation.site_counts).map(
                    ([site, counts]) => (
                      <tr key={site}>
                        <th scope="row">{site}</th>
                        <td>
                          {counts[1]} / {counts[0]}
                        </td>
                        <td>
                          <strong>
                            {counts[0] > 0
                              ? `${Math.round((counts[1] / counts[0]) * 1000) / 10}%`
                              : "Unknown"}
                          </strong>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
          <p className="cp-story-boundary">
            <FlaskConical size={16} />{" "}
            {a.root_cause
              ? `Recorded cause: ${a.root_cause}`
              : "A site pattern is evidence to investigate, not an established cause."}
          </p>
        </article>
        <article className="cp-story-surface cp-yield-stakes">
          <div className="cp-story-kicker">What is at stake</div>
          {id === "QE-004" && (
            <>
              <h2>Potential shipment value at risk</h2>
              <strong className="cp-story-number">
                {a.first_pass_shortfall_value_cents == null
                  ? "Not valued"
                  : new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: "USD",
                      notation: "compact",
                      maximumFractionDigits: 1,
                    }).format(a.first_pass_shortfall_value_cents / 100)}
              </strong>
              <details className="cp-story-assumptions">
                <summary>Assumptions & limits</summary>
                <p>
                  {a.first_pass_shortfall_quantity} fewer first-pass passes ×{" "}
                  {a.planning_unit_value_cents == null
                    ? "unvalued"
                    : money(a.planning_unit_value_cents)}{" "}
                  synthetic planning value. This is not booked revenue loss,
                  verified scrap or guaranteed recovery.
                </p>
              </details>
            </>
          )}
          <div className="cp-stakes-metrics">
            <div>
              <strong>{a.held_quantity.toLocaleString()}</strong>
              <span>Units held</span>
              <small>
                {a.first_pass_pass_quantity} first-pass passes remain held
              </small>
            </div>
            <div>
              <strong>{a.gap_quantity.toLocaleString()}</strong>
              <span>Unit supply gap</span>
              <small>
                {a.eligible_quantity} eligible / {a.requested_quantity}{" "}
                requested
              </small>
            </div>
          </div>
          <p className="cp-story-boundary">
            <LockKeyhole size={16} /> Held does not mean failed. Quality owns
            lot disposition.
          </p>
          <SourceLink to={`/manufacturing/quality/${id}`}>
            View Manufacturing record
          </SourceLink>
        </article>
      </section>
    );
  }
  if (id === "DR-009") {
    const a = h.delivery?.context?.analysis;
    if (!a) return null;
    const groups = [
      { label: "Held", value: a.held_quantity, tone: "amber" },
      { label: "Allocated", value: a.allocated_quantity, tone: "blue" },
      { label: "Eligible", value: a.eligible_quantity, tone: "green" },
      {
        label: "Wrong configuration",
        value: a.configuration_mismatch_quantity,
        tone: "gray",
      },
      {
        label: "Other unavailable",
        value: a.other_unavailable_quantity,
        tone: "gray",
      },
    ].filter((item) => item.value > 0);
    return (
      <section
        className="cp-case-story cp-delivery-story"
        aria-label="Delivery inventory reconciliation"
      >
        <article className="cp-story-surface">
          <div className="cp-story-kicker">Physical inventory</div>
          <strong className="cp-story-number">
            {a.physical_total.toLocaleString()}
            <span> units</span>
          </strong>
          <h2>Physical inventory is not eligible supply.</h2>
          <div
            className="cp-stock-bar cp-stock-decomposition"
            role="img"
            aria-label={groups
              .map((item) => `${item.value} ${item.label.toLowerCase()}`)
              .join(", ")}
          >
            {groups.map((item) => (
              <span
                key={item.label}
                className={`cp-fill-${item.tone}`}
                style={{
                  width: `${a.physical_total ? (item.value / a.physical_total) * 100 : 0}%`,
                }}
              >
                <b>{item.value}</b>
              </span>
            ))}
          </div>
          <div className="cp-stock-legend">
            {groups.map((item) => (
              <span key={item.label}>
                <i className={`cp-fill-${item.tone}`} />
                {item.label} · {item.value}
              </span>
            ))}
          </div>
          <div className="cp-stakes-metrics">
            <div>
              <small>Customer request</small>
              <strong>{a.requested_quantity ?? "—"}</strong>
            </div>
            <div>
              <small>Eligible supply</small>
              <strong>{a.eligible_quantity}</strong>
            </div>
            <div data-gap="true">
              <small>Remaining gap</small>
              <strong>{a.gap_quantity ?? "—"}</strong>
            </div>
          </div>
          <SourceLink to="/erp/delivery/DR-009">
            Read customer demand
          </SourceLink>
        </article>
        <article className="cp-story-surface cp-readiness-story">
          <div className="cp-story-kicker">
            <ShieldCheck size={17} /> Commitment gates
          </div>
          <h2>A promise needs more than inventory.</h2>
          <div className="cp-readiness-gate">
            <StatusText
              tone={a.technical_readiness === "READY" ? "good" : "warning"}
            >
              {a.technical_readiness === "READY"
                ? "Technical readiness cleared"
                : words(a.technical_readiness)}
            </StatusText>
            <p>{a.customer_ready_quantity} customer-ready units</p>
          </div>
          <div className="cp-readiness-gate">
            <strong>Quantity and timing</strong>
            <p>Confirm eligible supply and the exact delivery date.</p>
          </div>
          <div className="cp-readiness-gate">
            <strong>Program Owner decides</strong>
            <p>Review the exact commitment after investigation.</p>
          </div>
          <p className="cp-story-boundary">
            <LockKeyhole size={16} /> Lot release and allocation retain separate
            authority.
          </p>
        </article>
      </section>
    );
  }
  return null;
}
