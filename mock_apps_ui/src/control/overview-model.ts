import type { CaseData, Program, Snapshot } from "./data";

// Presentation classifications of source health, not calculated readiness.
export const riskHealth = [
  "validation_risk",
  "at_risk",
  "manufacturing_constraint",
  "recovery_active",
  "blocked",
  "waiting_on_customer",
] as const;
export function healthTone(health?: string | null) {
  if (health === "blocked") return "danger";
  if (health === "on_track" || health === "completed") return "good";
  if (riskHealth.some((value) => value === health)) return "warning";
  return "neutral";
}
export function overviewMetrics(programs: Program[], cases: CaseData[]) {
  const ids = new Set(programs.map((p) => p.id));
  const scoped = cases.filter((c) => ids.has(c.change.program_id));
  const draftPlans = new Set(
    scoped.flatMap((c) =>
      ["closed", "superseded"].includes(c.change.workflow_state)
        ? []
        : c.change.plans
            .filter(
              (p) => p.id === c.change.current_plan_id && p.state === "draft",
            )
            .map((p) => `${c.change.program_id}/${c.change.id}/${p.id}`),
    ),
  );
  const knownHealth = programs.every(
    (p) =>
      p.health === "on_track" ||
      p.health === "completed" ||
      riskHealth.some((h) => h === p.health),
  );
  return [
    { label: "Programs", value: programs.length, tone: "neutral" },
    // No existing safe host HTTP run interface. Source cases are not runs.
    { label: "Active investigations", value: null, tone: "neutral" },
    { label: "Needs review", value: draftPlans.size, tone: "warning" },
    {
      label: "At risk",
      value: knownHealth
        ? programs.filter((p) => riskHealth.some((h) => h === p.health)).length
        : null,
      tone: "warning",
    },
  ] as const;
}
export function nextGate(
  programId: string,
  milestones: Snapshot["milestones"],
) {
  return milestones
    .filter((m) => m.program_id === programId && m.health !== "completed")
    .sort((a, b) => a.baseline_at.localeCompare(b.baseline_at))[0];
}
export function attentionSummary(c: CaseData) {
  const plan = c.change.plans.find((p) => p.id === c.change.current_plan_id);
  if (c.change.execution_state === "lab_scheduled_pending_planner")
    return {
      reason: "Scheduled · Planner link missing",
      tone: "warning",
    } as const;
  if (c.change.execution_state === "scheduled_awaiting_execution")
    return { reason: "Scheduled · Results pending", tone: "warning" } as const;
  if (plan?.state === "draft")
    return { reason: "Plan awaiting review", tone: "warning" } as const;
  if (plan?.state === "rejected")
    return {
      reason: "Plan rejected · Reassess scope",
      tone: "danger",
    } as const;
  return {
    reason: c.coverage.coverage_satisfied
      ? "Evidence covered · Acceptance separate"
      : "Evidence gap",
    tone: "warning",
  } as const;
}
export function shortCaseTitle(c: CaseData) {
  if (c.change.category === "Long-context workload validation")
    return "Workload change";
  return c.change.title.split(" — ")[0];
}

// Only source observations can advance these stages. No host run completion is inferred.
export function caseStages(
  c: CaseData,
): { label: string; detail: string; state: "current" | "done" | "pending" }[] {
  const plan = c.change.plans.find((p) => p.id === c.change.current_plan_id);
  const scheduled = c.jobs.length > 0;
  return [
    {
      label: "Evidence review",
      detail: c.coverage.coverage_satisfied
        ? "Coverage available · Review separate"
        : "Applicability gap",
      state:
        c.change.workflow_state === "pending_impact_assessment"
          ? "current"
          : "pending",
    },
    {
      label: "Human decision",
      detail: plan ? `Source plan ${plan.state}` : "No source plan recorded",
      state:
        plan?.state === "approved" && Boolean(plan.decision_id)
          ? "done"
          : plan
            ? "current"
            : "pending",
    },
    {
      label: "Lab scheduling",
      detail: scheduled
        ? `${c.jobs.length} source job(s) recorded`
        : "No job recorded",
      state: scheduled ? "done" : "pending",
    },
    {
      label: "Test results",
      detail: c.coverage.coverage_satisfied
        ? "Applicable evidence · Acceptance separate"
        : "Requested evidence still missing",
      state: "pending",
    },
  ];
}
