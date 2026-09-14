// Presentation regression against the isolated deterministic rethink harness.
// No approval, execution, live model, or working-demo (5211) requests are made.
import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
import type { HostCase, HostSchema } from "../src/control/host";

const origin = "http://127.0.0.1:5221";
const casePath = (id: string) => `/control/programs/PRG-A17/cases/${id}`;
const readHost = async (request: APIRequestContext): Promise<HostCase> => {
  const response = await request.get("/control-api/cases/CR-017");
  expect(response.ok()).toBeTruthy();
  return response.json();
};

async function investigate(
  request: APIRequestContext,
  id: "CR-017" | "QE-004",
) {
  const response = await request.post(
    `/control-api/cases/${id}/investigations`,
    {
      headers: {
        Origin: origin,
        "X-Stratos-Action": "1",
        "X-Stratos-Demo-Profile": "automation",
      },
      data: {
        invocation_id: `ui_rethink_review_${randomUUID().replaceAll("-", "")}`,
        change_id: id,
        workflow_id:
          id === "QE-004"
            ? "yield_exception_recovery"
            : "requirement_change_analysis",
      },
    },
  );
  expect(response.status()).toBe(202);
  const { run_id: runId } = await response.json();
  await expect
    .poll(
      async () => {
        const host = await readHost(request);
        const runs = id === "CR-017" ? host.runs : host.quality?.runs;
        const run = runs?.find((item) => item.run_id === runId);
        if (run?.status === "failed")
          throw Error(
            `${id} deterministic investigation failed: ${run.error_code}`,
          );
        return (
          run?.status === "completed" &&
          (id !== "QE-004" ||
            host.quality?.progress?.some(
              (item) => item.run_id === runId && item.status === "draft_ready",
            ))
        );
      },
      {
        timeout: 45000,
        message: `${id} should produce its editable operator draft`,
      },
    )
    .toBe(true);
  return runId as string;
}

async function openAsOperator(page: Page, id: string) {
  await page.goto(casePath(id));
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: /^Program operator/ })
    .click();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  await expect(page.locator(".cp-case-story")).toBeVisible();
}

test("case redesign keeps completed agent recommendations editable before operator submission", async ({
  page,
  request,
  baseURL,
}) => {
  test.setTimeout(120000);
  // Fail before any mutation if this test is pointed at a different application.
  expect(baseURL).toBe(origin);
  expect((await readHost(request)).mode).toBe("deterministic_test");
  const shots = "../.cache/rethink-implementation/screenshots";
  await mkdir(shots, { recursive: true });
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/control-api/demo", (route) =>
    route.fulfill({ json: { enabled: false } }),
  );
  await page.addInitScript(() => {
    Object.defineProperty(window, "SpeechRecognition", { value: undefined });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      value: undefined,
    });
  });

  const changeRunId = await investigate(request, "CR-017");
  await openAsOperator(page, "CR-017");
  const originalRequest = page.locator(".cp-original-request");
  await originalRequest.locator("summary").click();
  await expect(originalRequest).toHaveAttribute("open", "");
  await expect(originalRequest.locator("p")).not.toBeEmpty();

  const comparison = page
    .locator("details")
    .filter({
      has: page.locator("summary", {
        hasText: "Full requirement comparison & source evidence",
      }),
    })
    .first();
  await comparison.locator(":scope > summary").click();
  await expect(
    comparison.getByRole("heading", { name: "What changed?", exact: true }),
  ).toBeVisible();
  await expect(
    comparison.getByRole("link", { name: /^Inspect evidence / }).first(),
  ).toBeVisible();
  await comparison.locator(":scope > summary").click();

  await page
    .getByRole("button", { name: "Review & submit proposal", exact: true })
    .click();
  const engineeringForm = page.locator("#human-decision form");
  await expect(engineeringForm).toBeVisible();
  const changeRecommendation = engineeringForm.getByRole("textbox", {
    name: "Recommended action",
    exact: true,
  });
  await expect(changeRecommendation).toBeEditable();
  await expect(changeRecommendation).not.toHaveValue("");
  const changeDraft = await changeRecommendation.inputValue();
  await changeRecommendation.fill(
    `${changeDraft}\nOperator review: preserve the approved acceptance criteria.`,
  );
  await expect(changeRecommendation).toHaveValue(
    /Operator review: preserve the approved acceptance criteria\./,
  );
  await engineeringForm
    .getByRole("textbox", { name: "Operator notes", exact: true })
    .fill("Layout regression: editable handoff retained.");
  await expect(
    engineeringForm.getByRole("button", {
      name: "Submit to Engineering",
      exact: true,
    }),
  ).toBeEnabled();
  await engineeringForm.screenshot({
    path: `${shots}/cr017-operator-review-form.png`,
  });
  const change = await readHost(request);
  expect(change.runs.find((run) => run.run_id === changeRunId)?.status).toBe(
    "completed",
  );

  const qualityRunId = await investigate(request, "QE-004");
  await openAsOperator(page, "QE-004");
  const quality = (await (
    await request.get("/control-api/cases/QE-004")
  ).json()) as HostSchema["QualityCaseView"];
  const qualityRun = quality.runs?.find((run) => run.run_id === qualityRunId);
  expect(qualityRun?.recommendation?.recommended_next_step).toBeTruthy();
  const cards = page.locator(".cp-recommendation-cards > li");
  await expect(cards).toHaveCount(4);
  await expect(
    cards.first().getByRole("heading", { name: "Agent actions", exact: true }),
  ).toBeVisible();
  const recommendationBlock = await cards
    .first()
    .locator(".cp-recommendation-content > div")
    .first()
    .boundingBox();
  const agentActionsBlock = await cards
    .first()
    .locator(".cp-agent-actions")
    .boundingBox();
  expect(recommendationBlock).not.toBeNull();
  expect(agentActionsBlock).not.toBeNull();
  expect(agentActionsBlock!.x).toBeGreaterThanOrEqual(
    recommendationBlock!.x + recommendationBlock!.width - 1,
  );
  await cards.first().locator("summary").click();
  await expect(cards.first().locator("details")).toHaveAttribute("open", "");

  await page
    .getByRole("link", { name: "Review & submit recommendation", exact: true })
    .click();
  const recoveryForm = page.locator("#operator-handoff form");
  await expect(recoveryForm).toBeVisible();
  const recoveryRecommendation = recoveryForm.getByRole("textbox", {
    name: "Recommended recovery action",
    exact: true,
  });
  await expect(recoveryRecommendation).toBeEditable();
  await expect(recoveryRecommendation).toHaveValue(
    qualityRun!.recommendation!.recommended_next_step,
  );
  await recoveryRecommendation.fill(
    `${await recoveryRecommendation.inputValue()}\nOperator review: Quality retains lot disposition.`,
  );
  await expect(recoveryRecommendation).toHaveValue(
    /Operator review: Quality retains lot disposition\./,
  );
  await recoveryForm
    .getByRole("textbox", { name: "Operator notes", exact: true })
    .fill("Review before sending to Program Owner.");
  await expect(
    recoveryForm.getByRole("button", {
      name: "Submit to Program Owner",
      exact: true,
    }),
  ).toBeEnabled();

  await recoveryForm.screenshot({
    path: `${shots}/qe004-operator-recovery-form.png`,
  });
  await page
    .locator(".cp-recommendation-cards")
    .screenshot({ path: `${shots}/qe004-recommendation-cards.png` });

  // The investigation itself may route an approved source task; its proof stays accessible.
  if (quality.records?.investigations.length) {
    await expect(
      page.getByRole("link", {
        name: "View Manufacturing record",
        exact: true,
      }),
    ).toHaveAttribute("href", "/manufacturing/quality/QE-004");
    const proof = page
      .locator(".cp-verification-step")
      .filter({ hasText: "Manufacturing received the investigation" });
    await proof.getByText("Source receipt", { exact: true }).click();
    await expect(proof).toContainText(quality.records.investigations[0].id);
  }
  expect(
    quality.progress?.find((item) => item.run_id === qualityRunId)
      ?.submitted_at,
  ).toBeFalsy();
  expect(quality.records?.decisions).toHaveLength(0);
  expect(quality.records?.tasks).toHaveLength(0);
  expect(errors).toEqual([]);
  await page.unrouteAll({ behavior: "ignoreErrors" });
});
