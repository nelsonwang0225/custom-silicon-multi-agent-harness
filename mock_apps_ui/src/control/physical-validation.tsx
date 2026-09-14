import { useState } from "react";
import { useParams } from "react-router-dom";
import { ActionAccess } from "./persona";
import { Link, AllowedAction, canAct } from "./access";
import { useHost, connectedCasePath, type HostSchema } from "./host";
import { Heading, Section, Facts, StatusText, Empty, SourceLink } from "./ui";
import { date, words } from "./data";
import { HostReadState } from "./decisions";

type Downstream = HostSchema["DownstreamView"];
const evidenceReason = (code: string) =>
  ({
    NOT_COMPLETED_PASS: "Completed passing evidence has not been established",
    WRONG_CONFIGURATION: "The recorded configuration does not match",
    WRONG_PROFILE: "The recorded workload does not match",
    WRONG_MODEL: "The recorded model does not match",
    STALE_EVIDENCE_BINDING: "The recorded source version is no longer current",
    STALE_APPROVED_SCOPE: "The approved engineering scope has changed",
    RESULT_BINDING_MISMATCH:
      "The result no longer matches its scheduled job and approved plan",
    CONFLICTING_RESULT: "Conflicting observations need investigation",
    INSUFFICIENT_DURATION: "The required test duration was not completed",
    MISSING_CONTEXT_BINS: "Required workload bins are missing",
  })[code] || words(code.toLowerCase());
export const evidenceDecisionPath = (digest: string) =>
  "/control/decisions/evidence/" + digest;
export function downstreamLabel(d?: Downstream | null) {
  const p = d?.physical;
  if (!p?.job) return "Physical validation pending";
  if (!p.result) return "Physical validation pending";
  if (p.applicability === "gap_remains")
    return "Lab result does not match the approved plan";
  if (p.applicability === "confirmed") return "Technical validation complete";
  return "Lab result received · Verification pending";
}
export function PhysicalValidationPanel() {
  const host = useHost()!,
    d = host.data?.downstream,
    p = d?.physical;
  const complete = !!p?.result && p.applicability === "confirmed";
  return (
    <Section
      title="Lab result & Engineering acceptance"
      className="cp-physical-outcome"
      note="The lab produces the result. Its match to the exact approved plan determines completion."
    >
      <StatusText tone={complete ? "good" : p?.result ? "warning" : "neutral"}>
        {downstreamLabel(d)}
      </StatusText>
      {!p || !p.available ? (
        <Empty>
          Downstream source records are unavailable. Refresh the source
          connection.
        </Empty>
      ) : (
        <>
          <div
            className="cp-validation-path"
            aria-label="Lab result and acceptance status"
          >
            <article data-complete={!!p.job}>
              <span>01 / VALIDATION LAB</span>
              <h3>{p.job ? "Task received" : "Task pending"}</h3>
              <p>
                {p.job
                  ? `${p.job.id} · ${words(p.job_status)}`
                  : "Submit the approved task to the lab."}
              </p>
            </article>
            <article data-complete={!!p.result?.criteria_passed}>
              <span>02 / LAB RESULT</span>
              <h3>
                {p.result
                  ? p.result.criteria_passed
                    ? "Result passed"
                    : "Result did not pass"
                  : "Result pending"}
              </h3>
              <p>
                {p.result
                  ? `${p.result.id} · Version ${p.result.content_version}`
                  : "The Validation Lab owns physical test results."}
              </p>
            </article>
            <article data-complete={complete}>
              <span>03 / ENGINEERING ACCEPTANCE</span>
              <h3>
                {complete
                  ? "Complete"
                  : p.result
                    ? "Match requires review"
                    : "Awaiting result"}
              </h3>
              <p>
                {complete
                  ? "The result matches the exact approved plan."
                  : "Completion requires matching scope and evidence."}
              </p>
            </article>
          </div>
          <details className="cp-secondary-content">
            <summary>Approved job, scope & source references</summary>
            <Facts
              rows={[
                [
                  "Validation job",
                  p.job
                    ? `${p.job.id} · ${words(p.job_status)}`
                    : "Not scheduled",
                ],
                [
                  "Approved option",
                  p.job
                    ? `${p.job.lab_id} / ${p.job.slot_id} / ${p.job.sample_id}`
                    : "Not recorded",
                ],
                [
                  "Configuration / workload",
                  p.job
                    ? `${p.job.configuration_id} / ${p.job.workload_profile_id}`
                    : "Not recorded",
                ],
                [
                  "Lab result",
                  p.result
                    ? `${p.result.id} · v${p.result.content_version} · ${p.result.criteria_passed ? "Passed" : "Did not pass"}`
                    : "Pending",
                ],
                [
                  "Approved-plan match",
                  p.result
                    ? p.applicability === "confirmed"
                      ? "Confirmed"
                      : "Mismatch found"
                    : "Pending",
                ],
                ["Technical completion", complete ? "Complete" : "Pending"],
              ]}
            />
          </details>
          {p.completion && (
            <p className="cp-caption">
              Demo lab event · Simulated completion{" "}
              {date(p.completion.completed_at, true)} · Recorded{" "}
              {date(p.completion.recorded_at, true)}. The result was checked
              against the approved plan; agents did not physically perform the
              test.
            </p>
          )}
          {!!(p.mismatch_reasons || []).length && (
            <p role="alert">
              {(p.mismatch_reasons || []).map(evidenceReason).join(" · ")}.
              CR-017 remains open because the result does not match the approved
              plan.
            </p>
          )}
          <div className="cp-inline">
            {p.job && (
              <SourceLink to={"/validation/jobs/" + p.job.id}>
                Open Validation Lab
              </SourceLink>
            )}
            {p.result && (
              <Link
                className="cp-button"
                to={`${connectedCasePath}?tab=evidence&evidence=${p.result.id}`}
              >
                View validation result
              </Link>
            )}
          </div>
          {complete && (
            <div className="cp-form-callout">
              <span>Case complete</span>
              <strong>
                The passing lab result satisfies the exact approved validation
                plan.
              </strong>
              <p>
                No second agent assessment, Program Operator handoff, or
                evidence-review decision is required in this shortened demo
                flow.
              </p>
            </div>
          )}
        </>
      )}
    </Section>
  );
}
export function EvidenceDecisions() {
  const host = useHost(),
    d = host?.data?.downstream,
    p = d?.physical;
  if (!p?.result && !p?.reviews?.length) return null;
  const reviews = p.reviews || [],
    hasCurrent = reviews.some((r) => r.evidence_digest === p.evidence_digest);
  return (
    <Section
      title="Review completed validation evidence"
      note="A separate decision from authorization to schedule validation."
    >
      {d?.review_ready &&
        !hasCurrent &&
        p.evidence_digest &&
        host?.data?.operator_escalations?.some(
          (value) =>
            value.stage === "evidence_review" &&
            value.evidence_digest === p.evidence_digest,
        ) && (
          <p>
            <Link to={evidenceDecisionPath(p.evidence_digest)}>
              CR-017 · Engineering evidence review
            </Link>{" "}
            · Needs review
          </p>
        )}
      {!d?.review_ready && !hasCurrent && <p>{downstreamLabel(d)}</p>}
      {reviews.map((r) => (
        <p key={r.id}>
          <Link to={evidenceDecisionPath(r.evidence_digest)}>
            CR-017 · Engineering evidence review
          </Link>{" "}
          ·{" "}
          {r.evidence_digest === p.evidence_digest
            ? r.decision === "approve"
              ? "Approved"
              : "Rejected"
            : "Historical / stale"}{" "}
          · {date(r.recorded_at, true)}
        </p>
      ))}
    </Section>
  );
}
export function EvidenceDecision() {
  const host = useHost()!,
    { digest } = useParams(),
    d = host.data?.downstream,
    p = d?.physical;
  const [comment, setComment] = useState(""),
    [error, setError] = useState("");
  const exact = p?.evidence_digest === digest;
  const review = p?.reviews?.find((r) => r.evidence_digest === digest);
  const evidenceHandoff = host.data?.operator_escalations?.find(
    (value) =>
      value.stage === "evidence_review" && value.evidence_digest === digest,
  );
  const canReview =
    exact &&
    d?.review_ready &&
    !!evidenceHandoff &&
    !review &&
    canAct(host.capabilities, "CR-017", "review_evidence") &&
    !host.error &&
    host.data?.source_available &&
    !host.busy;
  async function decide(decision: "approve" | "reject") {
    setError("");
    try {
      await host.act("/cases/CR-017/evidence-review", {
        expected_evidence_digest: digest,
        decision,
        comment,
      });
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <Link className="cp-text-link" to="/control/decisions">
        ← Decisions
      </Link>
      <Heading
        eyebrow="CR-017 · Engineering evidence decision"
        title="Review completed validation evidence"
        description="Does the completed, applicable evidence satisfy the engineering requirement for CR-017?"
      />
      <HostReadState />
      {!exact && !review ? (
        <Empty>
          This exact evidence review is unavailable. No current version is
          substituted.
        </Empty>
      ) : (
        <>
          {evidenceHandoff && (
            <Section
              title="Program Operator escalation"
              note="This is the operator-edited agent recommendation submitted for the final Engineering evidence decision."
            >
              <StatusText tone="good">Submitted to Engineering</StatusText>
              <h3>{evidenceHandoff.subject}</h3>
              <p>
                <strong>Recommended action:</strong>{" "}
                {evidenceHandoff.recommendation}
              </p>
              <p>
                <strong>Evidence and business context:</strong>{" "}
                {evidenceHandoff.business_context}
              </p>
              {evidenceHandoff.operator_notes && (
                <p>
                  <strong>Operator notes:</strong>{" "}
                  {evidenceHandoff.operator_notes}
                </p>
              )}
              <small>
                Submitted by {evidenceHandoff.submitted_by} ·{" "}
                {date(evidenceHandoff.submitted_at, true)}
              </small>
            </Section>
          )}
          <Section title="Exact evidence for engineering review">
            <p>
              Demo identity ·{" "}
              {host.profile === "engineer"
                ? "Engineering approver"
                : host.profile === "automation"
                  ? "Program operator"
                  : "Read-only viewer"}
            </p>
            {!exact && (
              <p role="alert">
                Historical evidence binding. Source records have changed; this
                decision does not approve current evidence.
              </p>
            )}
            {exact && (
              <Facts
                rows={[
                  ["Review policy", p?.evidence_binding?.review_policy],
                  ["Requirement", p?.completion?.requirement_revision_id],
                  ["Job", p?.job?.id],
                  ["Scheduled plan", p?.job?.plan_id],
                  [
                    "Configuration / workload",
                    `${p?.result?.configuration_id} / ${p?.result?.workload_profile_id}`,
                  ],
                  [
                    "Result version",
                    `${p?.result?.id} · v${p?.result?.content_version}`,
                  ],
                  [
                    "Criteria",
                    `${p?.result?.acceptance_limits_ref} · v${p?.result?.acceptance_criteria_content_version}`,
                  ],
                  [
                    "Applicability",
                    d?.assessment?.confirmed
                      ? "Confirmed by reassessment"
                      : "Not confirmed",
                  ],
                  ["Customer acceptance", "Pending / separate"],
                  ["Customer commitment", "Unchanged"],
                ]}
              />
            )}
            {exact && p?.result && (
              <Link
                to={`${connectedCasePath}?tab=evidence&evidence=${p.result.id}`}
              >
                Inspect structured result and provenance
              </Link>
            )}
            <details>
              <summary>Exact evidence and version details</summary>
              <p className="cp-digest">Evidence fingerprint · {digest}</p>
              <pre>
                {JSON.stringify(
                  review?.evidence_binding ||
                    (exact ? p?.evidence_binding : {}),
                  null,
                  2,
                )}
              </pre>
            </details>
          </Section>
          <Section title="Engineering disposition">
            {review ? (
              <Facts
                rows={[
                  [
                    "Decision",
                    review.decision === "approve" ? "Approved" : "Rejected",
                  ],
                  ["Engineering approver", review.signer_identity],
                  ["Recorded at", date(review.recorded_at, true)],
                  ["Comment", review.reason],
                  ["Source decision", review.id],
                  ["Customer acceptance", "Pending"],
                ]}
              />
            ) : !canAct(host.capabilities, "CR-017", "review_evidence") ? (
              <p>
                {evidenceHandoff
                  ? "Awaiting Engineering evidence review."
                  : "Awaiting the Program Operator's evidence-review handoff."}
              </p>
            ) : (
              <>
                <p>
                  Only the Engineering approver may record this consequential
                  decision. The Program operator may coordinate reassessment.
                </p>
                <label className="cp-review-comment">
                  Review comment
                  <textarea
                    aria-label="Engineering evidence review comment"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    maxLength={1500}
                    disabled={!canReview}
                  />
                </label>
                <ActionAccess
                  caseId="CR-017"
                  action="review_evidence"
                  ready={canReview && !!comment.trim()}
                  reason={
                    !comment.trim()
                      ? "Add a review comment explaining the evidence decision."
                      : "Current evidence and a completed reassessment are required."
                  }
                />
                <div className="cp-inline">
                  <AllowedAction caseId="CR-017" action="review_evidence">
                    <button
                      className="cp-button cp-primary"
                      disabled={!canReview || !comment.trim()}
                      onClick={() => void decide("approve")}
                    >
                      Approve validation evidence
                    </button>
                  </AllowedAction>
                  <AllowedAction caseId="CR-017" action="review_evidence">
                    <button
                      className="cp-button"
                      disabled={!canReview || !comment.trim()}
                      onClick={() => void decide("reject")}
                    >
                      Reject validation evidence
                    </button>
                  </AllowedAction>
                </div>
              </>
            )}
            {error && (
              <p role="alert" className="cp-error">
                {error}
              </p>
            )}
          </Section>
        </>
      )}
    </>
  );
}
