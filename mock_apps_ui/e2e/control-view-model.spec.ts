import { test, expect } from "@playwright/test";
import {
  attentionSummary,
  caseStages,
  healthTone,
  nextGate,
  overviewMetrics,
} from "../src/control/overview-model";
import type { CaseData, Program, Snapshot } from "../src/control/data";

// Small explicit view-model fixtures, never shipped or served as business state.
const program = (id: string, health: string) => ({ id, health }) as Program;
const sourceCase = (
  state: string,
  planState: string,
  execution = "not_started",
  covered = false,
  programId = "A",
  id = "C",
) =>
  ({
    change: {
      id,
      program_id: programId,
      workflow_state: state,
      execution_state: execution,
      current_plan_id: "current",
      plans: [
        { id: "current", state: planState },
        { id: "obsolete", state: "draft" },
      ],
    },
    coverage: { coverage_satisfied: covered },
  }) as CaseData;

test("case stages require observed plan decisions and jobs; coverage never implies acceptance", () => {
  const c = sourceCase("pending_impact_assessment", "draft");
  c.jobs = [];
  expect(caseStages(c).map((stage) => stage.state)).toEqual([
    "current",
    "current",
    "pending",
    "pending",
  ]);
  c.change.plans[0].state = "approved";
  expect(caseStages(c)[1].state).toBe("current");
  c.change.plans[0].decision_id = "source-decision";
  c.change.execution_state = "scheduled_awaiting_execution";
  expect(caseStages(c)[1].state).toBe("done");
  expect(caseStages(c)[2].state).toBe("pending");
  c.jobs = [{ id: "source-job" }] as CaseData["jobs"];
  expect(caseStages(c)[2].state).toBe("done");
  expect(caseStages(c)[3]).toMatchObject({
    state: "pending",
    detail: "Requested evidence still missing",
  });
  c.coverage.coverage_satisfied = true;
  expect(caseStages(c)[3]).toMatchObject({
    state: "pending",
    detail: "Applicable evidence · Acceptance separate",
  });
  c.change.plans[0].state = "rejected";
  expect(caseStages(c)[1]).toMatchObject({
    state: "current",
    detail: "Source plan rejected",
  });
});

test("metrics exclude obsolete, closed, superseded and out-of-scope plans; missing run state is not zero", () => {
  const programs = [
    program("A", "waiting_on_customer"),
    program("B", "on_track"),
  ];
  const cases = [
    sourceCase("open", "draft"),
    sourceCase("closed", "draft", "not_started", false, "A", "closed"),
    sourceCase("superseded", "draft", "not_started", false, "A", "old"),
    sourceCase("open", "approved", "not_started", true, "B"),
    sourceCase("open", "draft", "not_started", false, "preview-X"),
  ];
  expect(overviewMetrics(programs, cases).map((m) => m.value)).toEqual([
    2,
    null,
    1,
    1,
  ]);
  expect(
    overviewMetrics([program("A", "unrecognized")], cases)[3].value,
  ).toBeNull();
  expect(overviewMetrics([], cases).map((m) => m.value)).toEqual([
    0,
    null,
    0,
    0,
  ]);
  expect(healthTone("blocked")).toBe("danger");
  expect(healthTone("on_track")).toBe("good");
  expect(healthTone("unrecognized")).toBe("neutral");
});

test("source attention retains scheduling, review, rejection and acceptance distinctions", () => {
  expect(
    attentionSummary(
      sourceCase("open", "approved", "scheduled_awaiting_execution"),
    ).reason,
  ).toBe("Scheduled · Results pending");
  expect(
    attentionSummary(
      sourceCase("open", "approved", "lab_scheduled_pending_planner"),
    ).reason,
  ).toBe("Scheduled · Planner link missing");
  expect(attentionSummary(sourceCase("open", "draft")).reason).toBe(
    "Plan awaiting review",
  );
  expect(attentionSummary(sourceCase("open", "rejected")).tone).toBe("danger");
  expect(
    attentionSummary(sourceCase("open", "approved", "not_started", true))
      .reason,
  ).toBe("Evidence covered · Acceptance separate");
  expect(attentionSummary(sourceCase("open", "approved")).reason).toBe(
    "Evidence gap",
  );
});

test("next gate is the earliest open baseline in scope, never a forecast or completed gate", () => {
  const milestones = [
    {
      id: "closed",
      program_id: "A",
      health: "completed",
      baseline_at: "2026-11-01",
    },
    {
      id: "elsewhere",
      program_id: "B",
      health: "at_risk",
      baseline_at: "2026-11-02",
    },
    {
      id: "later",
      program_id: "A",
      health: "at_risk",
      baseline_at: "2026-11-22",
      current_forecast_at: "2026-11-10",
    },
    {
      id: "next",
      program_id: "A",
      health: "at_risk",
      baseline_at: "2026-11-19",
      current_forecast_at: "2026-11-23",
    },
  ] as Snapshot["milestones"];
  expect(nextGate("A", milestones)?.id).toBe("next");
  expect(nextGate("missing", milestones)).toBeUndefined();
});
