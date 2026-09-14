import { ActionAccess } from "./persona";
import { SourceReferenceList, RecordedText } from "./traceability";
import "./rethink-utilities.css";
import { useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { Link, AllowedAction, canAct, needsYourReview } from "./access";
import { ArrowRight, RefreshCw, ShieldCheck } from "lucide-react";
import { personas } from "../api";
import { date, money, words, useControl } from "./data";
import { Heading, Section, Facts, Empty, StatusText, SourceLink } from "./ui";
import {
  useHost,
  connectedCasePath,
  decisionPath,
  reviewable,
  executionLabel,
  type HostProposal,
  type HostSchema,
} from "./host";

export function HostReadState() {
  const host = useHost();
  if (!host) return null;
  return (
    <div className="cp-host-read">
      <details>
        <summary>Source & runtime</summary>
        <p>
          {host.data?.mode === "deterministic_test"
            ? "Deterministic test double · No paid model"
            : host.data
              ? "Configured model runtime · Only explicit investigations invoke a model"
              : "Reading host records…"}
        </p>
      </details>
      <span>
        {host.error
          ? "Stale / unavailable host read"
          : host.refreshing && host.data
            ? "Refreshing current records…"
            : host.data
              ? `Read ${date(host.data.fetched_at, true)}`
              : "Reading host records…"}
      </span>
      <button className="cp-text-link" onClick={() => void host.refresh()}>
        <RefreshCw size={14} /> Refresh workflow
      </button>
      {host.error && (
        <p className="cp-error" role="alert">
          {host.error}{" "}
          {host.data && "Last-read host records retained; actions disabled."}
        </p>
      )}
      {host.data && !host.data.source_available && (
        <p className="cp-error" role="alert">
          Source unavailable. Proposal freshness cannot be confirmed; actions
          are disabled.
        </p>
      )}
    </div>
  );
}
export function References({
  refs,
}: {
  refs: HostSchema["SourceReference"][];
}) {
  const { data } = useControl();
  const c = data?.cases.find(
    (c) => c.change.id === "CR-017" && c.change.program_id === "PRG-A17",
  );
  return (
    <SourceReferenceList
      refs={refs}
      href={(r) =>
        c?.coverage.items.some((e) => e.result.id === r.record_id)
          ? `${connectedCasePath}?tab=evidence&evidence=${encodeURIComponent(r.record_id!)}`
          : r.record_id?.startsWith("DOC-")
            ? `/engineering/documents/${encodeURIComponent(r.record_id)}`
            : undefined
      }
    />
  );
}
export function ExecutionDetails({
  item,
  onSubmitToLab,
  submitting = false,
}: {
  item: HostProposal;
  onSubmitToLab?: () => void;
  submitting?: boolean;
}) {
  const e = item.execution;
  return (
    <Section
      title="Execution & independent verification"
      note="See what was saved, then check whether a fresh source read confirmed the expected result."
    >
      <StatusText
        tone={
          e.status === "completed_execution" &&
          item.effective_status === "completed_execution"
            ? "good"
            : "warning"
        }
      >
        {executionLabel(item)}
      </StatusText>
      {onSubmitToLab && e.status === "approved" && (
        <div className="cp-execution-submit">
          <div>
            <strong>Engineering approved the exact validation plan.</strong>
            <p>
              Submit it explicitly to Validation Lab. After the lab record is
              verified, the approved plan will be linked in Program Planner.
            </p>
          </div>
          <button
            className="cp-button cp-primary"
            disabled={submitting}
            onClick={onSubmitToLab}
          >
            {submitting
              ? "Submitting to Validation Lab…"
              : "Submit to Validation Lab"}
          </button>
        </div>
      )}
      {e.error_code && (
        <p role="alert" className="cp-error">
          {e.error_code === "VERIFICATION_MISMATCH"
            ? "Verification failed: source readback does not match the approved action."
            : words(e.error_code)}
          . Safe reconciliation is required.
        </p>
      )}
      <div className="cp-execution-actions">
        {(item.proposal.manifest || []).map((a, i) => {
          const step = e.steps.find((s) => s.action_id === a.action_id);
          const verifications = item.verification.filter(
            (v) => v.action_id === a.action_id,
          );
          return (
            <article className="cp-record" key={a.action_id}>
              <h3>
                {i + 1}.{" "}
                {a.target_system === "validation"
                  ? "Validation Lab — schedule approved job"
                  : "Program Planner — link approved plan"}
              </h3>
              <Facts
                rows={[
                  ["Action result", words(step?.status || "not_attempted")],
                  ["Source record", step?.resource_id || "Not recorded"],
                  [
                    "Readback",
                    step?.verification
                      ? words(step.verification)
                      : "Not verified",
                  ],
                ]}
              />
              {step?.status === "unknown" && (
                <p className="cp-error">
                  Outcome unknown / reconciliation required. No blind write
                  retry.
                </p>
              )}
              {verifications.map((v) => (
                <p key={v.verification_id}>
                  <strong>{words(v.outcome)}</strong> · {v.explanation}
                  <small>Verified {date(v.verified_at, true)}</small>
                </p>
              ))}
              <details>
                <summary>Expected source parameters</summary>
                <pre>{JSON.stringify(a.expected, null, 2)}</pre>
              </details>
              {step?.resource_id && (
                <SourceLink
                  to={
                    a.target_system === "validation"
                      ? `/validation/jobs/${encodeURIComponent(step.resource_id)}`
                      : "/programs/PRG-A17"
                  }
                >
                  View source record
                </SourceLink>
              )}
              {verifications.some((v) => v.source_references.length) && (
                <details>
                  <summary>Readback source references</summary>
                  <References
                    refs={verifications.flatMap((v) => v.source_references)}
                  />
                </details>
              )}
            </article>
          );
        })}
      </div>
      {e.steps.some((s) => s.resource_id) && (
        <p>
          Physical testing and engineering review remain separate. Customer
          acceptance: {words(e.customer_acceptance)}.
        </p>
      )}
    </Section>
  );
}
const filters = [
  "All statuses",
  "Needs review",
  "Approved",
  "Rejected",
  "Executed / Completed",
  "Superseded / Stale",
  "Needs attention",
] as const;
function matches(p: HostProposal, filter: string) {
  if (filter === "Needs review") return reviewable(p);
  if (filter === "Approved")
    return ["approved", "resuming", "executing", "verifying"].includes(
      p.effective_status,
    );
  if (filter === "Rejected") return p.effective_status === "rejected";
  if (filter === "Executed / Completed")
    return p.effective_status === "completed_execution";
  if (filter === "Superseded / Stale")
    return ["superseded", "stale"].includes(p.effective_status);
  return (
    ["attention_required", "execution_failed", "partially_executed"].includes(
      p.effective_status,
    ) || p.current_check === "SOURCE_READ_FAILED"
  );
}
export function Decisions() {
  const host = useHost()!,
    [params, setParams] = useSearchParams();
  const filter =
    filters.find((value) => value === params.get("filter")) || "All statuses";
  const program = params.get("program") || "";
  const states: Record<string, string[]> = {
    "Needs review": ["needs_review"],
    Approved: ["approved"],
    Rejected: ["rejected"],
    "Executed / Completed": ["executed"],
    "Superseded / Stale": ["stale"],
    "Needs attention": [
      "partial_failure",
      "verification_required",
      "unavailable",
    ],
  };
  const permitted = (host.data?.decision_summaries || []).filter(
    (decision) => !!host.capabilities?.decision_kinds.includes(decision.kind),
  );
  const programFor = (caseId: string) =>
    host.data?.case_summaries?.find((item) => item.change_id === caseId)
      ?.program_id ||
    host.data?.program_id ||
    "";
  const rows = permitted.filter(
    (decision) =>
      (!program || programFor(decision.change_id) === program) &&
      (filter === "All statuses" ||
        (filter === "Needs review"
          ? decision.requires_human
          : states[filter].includes(decision.status))),
  );
  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    value ? next.set(key, value) : next.delete(key);
    setParams(next);
  };
  const consequence = (decision: HostSchema["DecisionSummary"]) =>
    decision.kind === "engineering_escalation"
      ? "Review the operator’s recommendation, evidence gaps and proposed path."
      : decision.kind === "engineering_evidence"
        ? "Record whether this exact validation result satisfies the requested workload."
        : decision.change_id === "CR-017"
          ? "Authorize the exact Validation Lab job and Program Planner link."
          : ["QE-004", "QE-011"].includes(decision.change_id)
            ? "Create one recovery task linked to the approved plan and investigation."
            : "Record the exact ERP delivery commitment and matching Planner link.";
  return (
    <div className="rt-utilities rt-decisions">
      <Heading
        eyebrow="Accountable decisions"
        title="Decisions"
        description="Review the recommendation, evidence and exact consequence before deciding."
      />
      <HostReadState />
      <div className="rt-filter-bar">
        <label className="rt-filter">
          <span>Program</span>
          <select
            value={program}
            onChange={(event) => setFilter("program", event.target.value)}
          >
            <option value="">All programs</option>
            {[
              ...new Set(
                permitted.map((decision) => programFor(decision.change_id)),
              ),
            ]
              .filter(Boolean)
              .sort()
              .map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
          </select>
        </label>
        <label className="rt-filter">
          <span>Decision status</span>
          <select
            value={filter}
            onChange={(event) => setFilter("filter", event.target.value)}
          >
            {filters.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <button
          className="rt-review-shortcut"
          aria-pressed={filter === "Needs review"}
          onClick={() =>
            setFilter(
              "filter",
              filter === "Needs review" ? "All statuses" : "Needs review",
            )
          }
        >
          <ShieldCheck size={16} aria-hidden="true" /> Needs review{" "}
          <strong>
            {
              permitted.filter(
                (decision) =>
                  decision.requires_human &&
                  (!program || programFor(decision.change_id) === program),
              ).length
            }
          </strong>
        </button>
        <span className="rt-result-count">{rows.length} decisions</span>
      </div>
      <Section
        title={filter === "All statuses" ? "Decision queue" : filter}
        className="rt-decision-queue"
      >
        {rows.map((decision) => (
          <Link
            className="cp-decision-row rt-decision-brief"
            to={
              decision.href +
              (["QE-004", "QE-011", "DR-009"].includes(decision.change_id)
                ? "#decision"
                : "")
            }
            key={`${decision.id}/${decision.digest}`}
            data-case-id={decision.change_id}
            aria-label={`${decision.change_id} · ${decision.title}`}
          >
            <div className="rt-decision-topic">
              <small>
                {decision.change_id} · {programFor(decision.change_id)} ·{" "}
                {decision.kind === "engineering_escalation"
                  ? "Operator escalation"
                  : decision.version == null
                    ? "Exact evidence"
                    : `Proposal v${decision.version}`}
              </small>
              <h3>{decision.title}</h3>
              <p>{consequence(decision)}</p>
              <span className="cp-text-link">
                {needsYourReview(host.capabilities, decision)
                  ? "Review and decide"
                  : "View decision"}{" "}
                <ArrowRight size={15} />
              </span>
            </div>
            <div className="rt-decision-owner">
              <small>Decision owner</small>
              <strong>
                {decision.required_role === "engineer"
                  ? "Engineering approver"
                  : "Program Owner"}
              </strong>
              <span>
                {host.error
                  ? "Stale read · Refresh required"
                  : decision.current
                    ? "Current source binding"
                    : "Binding needs review"}
              </span>
              {decision.reviewer && (
                <small>Reviewed by {decision.reviewer}</small>
              )}
              <small>Execution: {words(decision.execution)}</small>
            </div>
            <StatusText
              tone={
                decision.requires_human
                  ? "warning"
                  : decision.status === "executed" ||
                      decision.status === "approved"
                    ? "good"
                    : "neutral"
              }
            >
              {words(decision.status)}
            </StatusText>
          </Link>
        ))}
        {!rows.length && (
          <Empty>
            {host.error || !host.data
              ? "Decision records unavailable."
              : "No decisions match these filters."}{" "}
            <Link to="/control/programs/PRG-A17">Inspect connected cases</Link>
          </Empty>
        )}
      </Section>
    </div>
  );
}

export function DecisionReview() {
  const host = useHost()!,
    { proposalId, version } = useParams(),
    [params] = useSearchParams();
  const [comment, setComment] = useState(""),
    [error, setError] = useState(""),
    [success, setSuccess] = useState("");
  const item = host.data?.proposals.find(
    (p) =>
      p.proposal.proposal_id === proposalId &&
      p.proposal.proposal_version === Number(version) &&
      p.proposal.proposal_digest === params.get("digest"),
  );
  if (!item)
    return (
      <>
        <Heading title="Exact proposal review" />
        <HostReadState />
        <Empty>
          {!host.data
            ? "Reading the requested proposal…"
            : "This exact proposal ID, version and digest is unavailable. No replacement has been selected."}{" "}
          <Link to="/control/decisions">Browse recorded decisions</Link>
        </Empty>
      </>
    );
  const p = item.proposal,
    e = item.execution;
  const operatorHandoff = host.data?.operator_escalations?.find(
    (value) => value.run_id === p.origin.run_id,
  );
  const connected = !!host.data?.source_available && !host.error,
    canReview = connected && reviewable(item) && !host.busy;
  const canExecute =
    connected &&
    item.current_check === "current" &&
    item.review?.status === "approved" &&
    !["stale", "superseded", "rejected"].includes(item.effective_status) &&
    !host.busy &&
    ["engineer", "automation"].includes(host.profile || "");
  const submit = async (action: "approve" | "reject" | "execute") => {
    setError("");
    setSuccess("");
    try {
      await host.act(
        `/proposals/${action === "execute" ? "execute" : "review"}`,
        {
          reference: e.reference,
          ...(action === "execute" ? {} : { decision: action, comment }),
        },
      );
      setSuccess(
        action === "execute"
          ? "Execution request completed. Inspect the persisted action and readback outcomes below."
          : `${action === "approve" ? "Approval" : "Rejection"} recorded for this exact proposal.`,
      );
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <>
      <Link className="cp-text-link" to="/control/decisions">
        ← Decisions
      </Link>
      <Heading
        eyebrow={`CR-017 · Proposal v${p.proposal_version}`}
        title="Review validation plan"
        description={`Review ${p.source_plan.slot_id} / ${p.source_plan.sample_id} for supplemental validation. Approval authorizes the exact lab schedule and Planner link; test evidence and customer acceptance remain separate.`}
      />
      <HostReadState />
      <div className="cp-review-summary">
        <StatusText tone={reviewable(item) ? "warning" : "neutral"}>
          {executionLabel(item)}
        </StatusText>
        <span>
          Demo identity ·{" "}
          {host.profile ? personas[host.profile] : "No profile selected"}
        </span>
      </div>
      {item.current_check !== "current" &&
        item.current_check !== "completed_before_lab_result" && (
          <p className="cp-error" role="alert">
            This exact proposal cannot be approved or executed:{" "}
            {words(item.current_check)}.{" "}
            {item.replacement && (
              <Link
                to={`/control/decisions/${item.replacement.proposal_id}/${item.replacement.proposal_version}?digest=${item.replacement.proposal_digest}`}
              >
                Inspect current proposal
              </Link>
            )}
          </p>
        )}
      <div
        className="cp-business-visual"
        aria-label="Validation decision consequences"
      >
        <div>
          <small>Incremental cost</small>
          <strong>{money(p.source_plan.cost_cents)}</strong>
          <span>Exact proposed lab option</span>
        </div>
        <div>
          <small>Review-ready forecast</small>
          <strong>{date(p.source_plan.timing.review_ready_at)}</strong>
          <span>Conditional on testing and engineering review</span>
        </div>
        <div>
          <small>Approval authorizes</small>
          <strong>Schedule + link</strong>
          <span>Validation Lab job and Program Planner link</span>
        </div>
      </div>
      <ActionAccess
        caseId="CR-017"
        action="review"
        ready={canReview}
        reason="This exact proposal is not currently reviewable. Inspect its recorded decision or source binding."
      />
      {operatorHandoff && (
        <Section
          title="Program Operator escalation"
          note="The Program Operator reviewed and edited the agent's recommendation before sending this exact proposal to Engineering."
        >
          <StatusText tone="good">Submitted to Engineering</StatusText>
          <h3>{operatorHandoff.subject}</h3>
          <span className="tr-label">Recommended action</span>
          <RecordedText
            text={operatorHandoff.recommendation}
            label="Full submitted recommendation"
          />
          <span className="tr-label">Evidence and business context</span>
          <RecordedText
            text={operatorHandoff.business_context}
            label="Full submitted context"
          />
          {operatorHandoff.operator_notes && (
            <p>
              <strong>Operator notes:</strong> {operatorHandoff.operator_notes}
            </p>
          )}
          <small>
            Submitted by {operatorHandoff.submitted_by} ·{" "}
            {date(operatorHandoff.submitted_at, true)}
          </small>
        </Section>
      )}
      <Section title="The decision brief" className="rt-decision-focus">
        <div className="rt-consequence-grid">
          <div>
            <small>If approved</small>
            <h3>Authorize the exact validation plan</h3>
            <p>
              Use {p.source_plan.slot_id} with {p.source_plan.sample_id}. Submit
              to Validation Lab explicitly, then confirm the matching Planner
              link.
            </p>
          </div>
          <div>
            <small>Separate downstream authority</small>
            <h3>Testing and customer acceptance</h3>
            <p>
              A scheduled job is not test evidence. The lab owns its result;
              customer acceptance remains separate.
            </p>
          </div>
        </div>
        <h3>Why this option</h3>
        <RecordedText text={p.rationale} label="Full investigation rationale" />
        <a className="cp-text-link" href="#decision-review">
          Go to human decision <ArrowRight size={15} />
        </a>
        <details className="rt-inline-details">
          <summary>Exact scope, timing and source policy</summary>
          <Facts
            rows={[
              [
                "Case / program / customer",
                `${p.origin.case_id} / ${p.origin.program_id} / ${p.origin.customer_id}`,
              ],
              [
                "Configuration / procedure",
                `${p.source_plan.configuration_id} / ${p.source_plan.procedure_id}`,
              ],
              [
                "Slot / sample",
                `${p.source_plan.slot_id} / ${p.source_plan.sample_id}`,
              ],
              ["Incremental cost", money(p.source_plan.cost_cents)],
              [
                "Baseline milestone",
                date(p.milestone_before?.baseline_at, true),
              ],
              [
                "Current forecast before proposal",
                date(p.milestone_before?.current_forecast_at, true),
              ],
              [
                "Proposed review-ready forecast",
                date(p.source_plan.timing.review_ready_at, true),
              ],
              [
                "Required review policy",
                `${p.required_policy_id} v${p.required_policy_version} · ${p.required_role}`,
              ],
            ]}
          />
        </details>
        <h3>Material assumptions</h3>
        <ul>
          {p.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
        <h3>Preconditions</h3>
        <ul>
          {p.preconditions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
        <p>
          Customer commitments retain their source authority. This forecast is
          conditional on physical testing and engineering review.
        </p>
      </Section>
      <Section
        title="Exact authorized actions"
        note="Approval binds these ordered actions and the immutable proposal below."
      >
        {(p.manifest || []).map((a) => (
          <article className="cp-record" key={a.action_id}>
            <h3>
              {a.sequence}.{" "}
              {a.target_system === "validation"
                ? "Validation Lab"
                : "Program Planner"}
            </h3>
            <p>{words(a.operation)}</p>
            <Facts
              rows={[
                ["Target", a.target],
                ["Depends on", a.depends_on || "Exact human approval"],
              ]}
            />
            <details>
              <summary>Exact action arguments</summary>
              <pre>{JSON.stringify(a.arguments, null, 2)}</pre>
            </details>
          </article>
        ))}
        <Facts
          rows={[
            ["Proposal ID", p.proposal_id],
            ["Immutable version", p.proposal_version],
            [
              "Proposal digest",
              <code className="cp-digest">{p.proposal_digest}</code>,
            ],
            [
              "Source plan digest",
              <code className="cp-digest">{p.source_plan.plan_digest}</code>,
            ],
            [
              "Analysis run",
              <Link
                to={`${connectedCasePath}?tab=activity&run=${p.origin.run_id}`}
              >
                {p.origin.run_id}
              </Link>,
            ],
          ]}
        />
      </Section>
      <Section title="Supporting evidence">
        <details>
          <summary>Recorded investigation rationale</summary>
          <p>{p.rationale}</p>
        </details>
        <References refs={p.evidence_references} />
        {!p.evidence_references.length && (
          <Empty>No evidence references were retained by this run.</Empty>
        )}
      </Section>
      <Section
        id="decision-review"
        className="rt-human-decision"
        title="Human decision"
        action={<ShieldCheck size={24} />}
      >
        <p>
          Demo identity:{" "}
          <strong>
            {host.profile ? personas[host.profile] : "No profile selected"}
          </strong>
          . The host checks its installed trusted actor and the exact proposal
          before recording a source decision.
        </p>
        {!item.review && canAct(host.capabilities, "CR-017", "review") && (
          <>
            <label className="cp-review-comment">
              Review comment
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                maxLength={1500}
                placeholder="Optional rationale for your decision"
              />
            </label>
            <ActionAccess
              caseId="CR-017"
              action="review"
              ready={canReview}
              reason="A fresh, current and unreviewed proposal is required."
            />
            <div className="cp-inline">
              <AllowedAction caseId="CR-017" action="review">
                <button
                  className="cp-button cp-primary"
                  disabled={
                    !canReview || !canAct(host.capabilities, "CR-017", "review")
                  }
                  onClick={() => void submit("approve")}
                >
                  Approve this proposal
                </button>
              </AllowedAction>
              <AllowedAction caseId="CR-017" action="review">
                <button
                  className="cp-button"
                  disabled={
                    !canReview || !canAct(host.capabilities, "CR-017", "review")
                  }
                  onClick={() => void submit("reject")}
                >
                  Reject this proposal
                </button>
              </AllowedAction>
            </div>
          </>
        )}
        {item.review && (
          <Facts
            rows={[
              ["Decision", words(item.review.status)],
              ["Reviewer", item.review.actor_id],
              [
                "Source decision",
                item.review.source_decision_id ||
                  "Recording / reconcile required",
              ],
              ["Comment", item.review.comment],
              ["Recorded", date(item.review.decided_at, true)],
            ]}
          />
        )}
        {item.review?.status === "recording" && (
          <AllowedAction caseId="CR-017" action="review">
            <button
              className="cp-button"
              disabled={
                !connected ||
                !canAct(host.capabilities, "CR-017", "review") ||
                !!host.busy
              }
              onClick={async () => {
                setError("");
                try {
                  await host.act("/proposals/review", {
                    reference: e.reference,
                    decision: item.review!.decision,
                    comment: item.review!.comment,
                  });
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Reconcile exact review
            </button>
          </AllowedAction>
        )}
        {host.busy && (
          <p role="status">
            {host.busy.endsWith("execute")
              ? "Executing / verifying the exact approved manifest…"
              : "Recording exact proposal decision…"}
          </p>
        )}
        {error && (
          <p role="alert" className="cp-error">
            {error}
          </p>
        )}
        {success && <p role="status">{success}</p>}
      </Section>
      <Section title="Governed execution">
        <ActionAccess
          caseId="CR-017"
          action="execute"
          ready={canExecute}
          reason={
            item.review?.status !== "approved"
              ? "Exact Engineering approval is required before execution."
              : "The approved proposal must still match current source records."
          }
        />
        <p>
          Schedule in Validation Lab, verify it, then link Program Planner and
          verify its records.
        </p>
        <AllowedAction caseId="CR-017" action="execute">
          <button
            className="cp-button cp-primary"
            disabled={!canExecute}
            onClick={() => void submit("execute")}
          >
            {e.status === "completed_execution"
              ? "Recheck source readback"
              : e.steps.some((s) => s.status !== "not_attempted")
                ? "Reconcile / resume exact proposal"
                : "Submit approved plan to Validation Lab"}
          </button>
        </AllowedAction>
        {!item.review && (
          <p>
            Execution requires the recorded approval of this exact proposal.
          </p>
        )}
      </Section>
      <ExecutionDetails item={item} />
      <Link className="cp-text-link" to={connectedCasePath}>
        Return to CR-017 workbench <ArrowRight size={16} />
      </Link>
    </>
  );
}
