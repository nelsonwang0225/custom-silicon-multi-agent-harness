import type { HostCase, HostSchema } from "./host";
import type { CaseData } from "./data";
export type Summary = HostSchema["CaseSummary"];
export const caseNames: Record<string, string> = {
  "CR-017": "Material workload change",
  "CR-019": "Standard touchless change",
  "QE-004": "Yield / quality exception",
  "QE-011": "Final-test anomaly",
  "DR-009": "Delivery readiness",
};
export const caseQuestions: Record<string, string> = {
  "CR-017":
    "What evidence is needed to support Helios’s longer-context workload?",
  "CR-019":
    "Can the approved validation package be handed off without a new human decision?",
  "QE-011":
    "What did the Manufacturing event reveal, and what requires human judgment?",
  "QE-004":
    "What changed in final test, and what recovery work can safely proceed?",
  "DR-009":
    "How much of Helios’s request can we commit, and what remains uncovered?",
};
const cr017CustomerRequest =
  "Our updated long-context inference release uses workload manifest WF-LC-V2 with model bundle MODEL-LAB-07. Before the initial acceptance review, please provide validation evidence on ACCELERATOR-X REV-B in configuration CFG-B-01 across the 32,768, 65,536, and 131,072 input-token bins. The suite runs for 480 minutes total, with concurrency 4 across the configured system and 1,024 output tokens per request. Please retain existing operating and acceptance limits. We are requesting evidence, not authorizing a silicon redesign or a change to the delivery commitment. Evidence and its engineering review are due by 2026-11-19T18:00:00Z. Please assess the coverage gap and propose a permissible validation plan with any additional cost. Completion of testing does not by itself constitute our final acceptance.";

export function casePresentation(
  h: HostCase | undefined | null,
  id: string,
  c: CaseData | undefined,
  fallbackTitle: string,
) {
  if (id === "CR-017")
    return {
      title: c?.change.title || fallbackTitle,
      summary:
        "Assess whether current validation evidence covers Helios’s expanded long-context workload, and identify any additional testing, cost, and approval required.",
      originalDescription: cr017CustomerRequest,
    };
  if (id === "CR-019") {
    const request = h?.standard?.context?.request;
    return {
      title: request
        ? `Add approved ${request.workload_profile_id} profile to the Helios acceptance package`
        : fallbackTitle,
      summary:
        "Confirm whether this already-approved workload profile can move into Validation Operations through the standard process without a new human decision.",
      originalDescription:
        request?.summary ||
        "Add an already-approved workload profile to the next Helios acceptance validation package and route the standard confirmation work to Validation Operations.",
    };
  }
  if (id === "QE-004" || id === "QE-011") {
    const context =
      id === "QE-011" ? h?.autonomous_quality?.context : h?.quality?.context;
    const analysis = context?.analysis;
    const yieldExposure = analysis?.first_pass_shortfall_value_cents;
    const impact =
      id === "QE-004" && analysis && yieldExposure != null
        ? ` The 16 percentage-point yield drop puts ${new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            notation: "compact",
            maximumFractionDigits: 1,
          }).format(yieldExposure / 100)} in potential shipment value at risk.`
        : "";
    return {
      title: context
        ? `Final-test pass-rate exception for held lot ${context.exception.lot_id}`
        : fallbackTitle,
      summary: context
        ? `Investigate the final-test pass-rate exception affecting held lot ${context.exception.lot_id}, determine its supply impact, and define the permitted recovery path.${impact}`
        : "Investigate the final-test exception, determine its supply impact, and define the permitted recovery path while the affected material remains on hold.",
      originalDescription:
        context?.exception.summary ||
        "Investigate the final-test exception, confirm the affected material, and identify the governed recovery path while the lot remains on hold.",
    };
  }
  if (id === "DR-009") {
    const request = h?.delivery?.context?.request;
    return {
      title: request
        ? `Plan Helios’s ${request.quantity}-unit delivery release`
        : fallbackTitle,
      summary: request
        ? `Determine how much of Helios’s ${request.quantity}-unit request can be committed from eligible supply, what remains uncovered, and which decision is required.`
        : "Determine how much of the customer request can be committed from eligible supply, what remains uncovered, and which decision is required.",
      originalDescription:
        request?.summary ||
        "Reconcile eligible supply against the customer request before proposing an exact delivery commitment.",
    };
  }
  return {
    title: fallbackTitle,
    summary: caseQuestions[id],
    originalDescription: caseQuestions[id],
  };
}
export function caseRun(h: HostCase | undefined | null, id: string) {
  return (
    id === "CR-017"
      ? h?.runs
      : id === "CR-019"
        ? h?.standard?.runs
        : id === "QE-004"
          ? h?.quality?.runs
          : id === "QE-011"
            ? h?.autonomous_quality?.runs
            : h?.delivery?.runs
  )?.[0];
}
export function standardRunHandoff(
  v: HostSchema["StandardCaseView"] | null | undefined,
) {
  return v?.handoffs.find((handoff) => handoff.run_id === v.runs[0]?.run_id);
}
export function humanDecision(h: HostCase | undefined | null, id: string) {
  return h?.decision_summaries?.find(
    (d) => d.change_id === id && d.requires_human,
  );
}
export function caseFact(
  h: HostCase | undefined | null,
  s: Summary,
  c?: CaseData,
): string {
  if (!s.source_available) return "Current source unavailable";
  if (s.change_id === "CR-017")
    return s.state === "completed_technical"
      ? "Validation complete"
      : h?.downstream?.physical.result
        ? "Physical result received"
        : c
          ? `${c.targetWorkload.total_suite_minutes} min requested · ${c.coverage.coverage_satisfied ? "Applicable evidence available" : "Evidence gap"}`
          : s.detail;
  if (s.change_id === "CR-019") {
    const count = h?.standard?.eligibility?.reusable_evidence_ids.length ?? 0;
    return standardRunHandoff(h?.standard)?.status === "handoff_verified"
      ? "Handoff verified"
      : caseRun(h, "CR-019")
        ? `${count} reusable evidence record${count === 1 ? "" : "s"}`
        : "Policy eligibility not assessed";
  }
  const a =
    s.change_id === "QE-004"
      ? h?.quality?.context?.analysis
      : s.change_id === "QE-011"
        ? h?.autonomous_quality?.context?.analysis
        : h?.delivery?.context?.analysis;
  if (!a) return "Current source unavailable";
  return ["QE-004", "QE-011"].includes(s.change_id)
    ? `${a.held_quantity} held · ${a.gap_quantity} unit supply gap`
    : `${a.eligible_quantity} / ${a.requested_quantity ?? "?"} eligible · ${a.gap_quantity ?? "?"} gap`;
}
export function nextBusinessStep(h: HostCase | undefined | null, s: Summary) {
  if (["completed_technical", "completed_recovery"].includes(s.state)) return "Workflow complete";
  const d = humanDecision(h, s.change_id);
  if (d)
    return d.required_role === "engineer"
      ? "Engineering approver required"
      : "Program Owner decision required";
  if (s.state === "waiting_external")
    return s.change_id === "CR-019"
      ? "Lab authorization downstream"
      : ["QE-004", "QE-011"].includes(s.change_id)
        ? "Quality investigation remains open"
        : s.change_id === "DR-009"
          ? "Remaining supply gap unresolved"
          : h?.downstream?.physical.result
            ? "Reassessment before engineering review"
            : "Awaiting Validation Lab result";
  if (s.state === "new") return "Ready for investigation";
  if (s.state === "investigating") return "Agent investigation in progress";
  return s.next_action;
}
export type Stage = {
  label: string;
  state: "done" | "current" | "pending" | "failed";
  detail: string;
};
export function lifecycle(h: HostCase, id: string): Stage[] {
  const run = caseRun(h, id),
    summary = h.case_summaries?.find((c) => c.change_id === id);
  const stale = summary?.state === "stale" || summary?.state === "unavailable";
  const stage = (
    label: string,
    done: boolean,
    current = false,
    detail = "",
  ): Stage => ({
    label,
    state: stale ? "pending" : done ? "done" : current ? "current" : "pending",
    detail: stale
      ? "Refresh current source"
      : detail ||
        (done ? "Recorded" : current ? "In progress" : "Not yet complete"),
  });
  const investigation = stage(
    "Investigation",
    run?.status === "completed",
    run?.status === "running",
    run?.status === "running"
      ? "Running"
      : run?.status === "completed"
        ? "Findings recorded"
        : "Not investigated",
  );
  if (run?.status === "failed" || run?.status === "cancelled") {
    investigation.state = "failed";
    investigation.detail = run.status;
  }
  if (id === "CR-017") {
    const p = h.proposals.find(
        (p) =>
          p.current_check === "current" ||
          p.current_check === "completed_before_lab_result",
      ),
      v = h.downstream?.physical;
    return [
      investigation,
      stage(
        "Validation plan",
        p?.review?.status === "approved",
        !!p && !p.review,
        p?.review?.status || "Engineering approval required",
      ),
      stage(
        "Scheduling",
        p?.effective_status === "completed_execution",
        p?.execution.status === "executing",
        v?.job ? "Job recorded" : "Not scheduled",
      ),
      stage(
        "Lab result",
        !!v?.result,
        false,
        v?.result ? "Result received" : "Awaiting physical work",
      ),
      stage(
        "Technical completion",
        !!v?.result && v?.applicability === "confirmed",
        false,
        v?.result && v?.applicability === "confirmed"
          ? "Approved plan satisfied"
          : v?.result
            ? "Result mismatch"
            : "Awaiting lab result",
      ),
    ];
  }
  if (id === "CR-019") {
    const p = standardRunHandoff(h.standard);
    return [
      investigation,
      stage(
        "Policy",
        !!p?.eligibility?.touchless_eligible,
        false,
        p?.eligibility ? "Recorded policy check" : "Not assessed",
      ),
      stage("Package", !!p?.package),
      stage(
        "Intake",
        p?.status === "handoff_verified",
        p?.status === "action_started",
        p?.status === "handoff_verified" ? "Handoff verified" : "Not verified",
      ),
    ];
  }
  const v =
      id === "QE-004"
        ? h.quality
        : id === "QE-011"
          ? h.autonomous_quality
          : h.delivery,
    p = v?.progress?.[0],
    review = v?.records?.decisions.find((d) => d.plan_id === p?.plan_id),
    verified = p?.status === "verified" || p?.status === "commitment_current";
  const execution = stage(
    ["QE-004", "QE-011"].includes(id) ? "Recovery task" : "ERP + Planner",
    verified,
    !!p?.status.endsWith("_started"),
    verified ? "Readback verified" : "Not verified",
  );
  if (
    summary?.state === "partial_failure" ||
    summary?.state === "verification_required"
  ) {
    execution.state = "failed";
    execution.detail =
      summary.state === "partial_failure"
        ? "Partial execution · Reconcile"
        : "Readback required";
  }
  const stages = [
    investigation,
    stage(
      "Human decision",
      review?.decision === "approve",
      p?.status === "awaiting_review",
      review?.decision === "approve"
        ? "Approved"
        : review?.decision === "reject"
          ? "Rejected"
          : "Program Owner required",
    ),
    execution,
  ];
  if (id !== "QE-004")
    stages.push(
      stage(
        id === "QE-011" ? "Quality disposition" : "Remaining demand",
        false,
        false,
        id === "QE-011"
          ? "Hold remains governed"
          : "Gap / customer agreement remain",
      ),
    );
  return stages;
}
