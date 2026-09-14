import { test, expect, type Page } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
import {
  actionExplanation,
  operationLabel,
  findingText,
  versionLabel,
  failureLabel,
  evidenceReason,
  savedStandardFinding,
  gateLabel,
} from "../src/control/trace-language";

const root = "/control/programs/PRG-A17/cases/";
const shots = "../docs/screenshots/trace-readability";
const runs: Record<string, string> = {};
const headers = {
  Origin: "http://127.0.0.1:5194",
  "X-Stratos-Action": "1",
  "X-Stratos-Demo-Profile": "automation",
};
test.beforeAll(async ({ request }) => {
  await mkdir(shots, { recursive: true });
  for (const id of ["CR-019", "QE-004", "DR-009", "CR-017"]) {
    const response = await request.post(
      `/control-api/cases/${id}/investigations`,
      {
        headers,
        data: {
          invocation_id: "ui_trace_" + randomUUID().replaceAll("-", ""),
          change_id: id,
          workflow_id:
            id === "QE-004"
              ? "yield_exception_recovery"
              : id === "DR-009"
                ? "delivery_readiness"
                : "requirement_change_analysis",
        },
      },
    );
    expect(response.status()).toBe(202);
    runs[id] = (await response.json()).run_id;
    await expect
      .poll(
        async () => {
          const h = await (
            await request.get("/control-api/cases/CR-017")
          ).json();
          return h.case_summaries.find((s: any) => s.change_id === id)?.state;
        },
        { timeout: 45000 },
      )
      .not.toBe("investigating");
  }
});
test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    class NoSpeech {
      start() {
        throw Error("No microphone in tests");
      }
      stop() {}
      abort() {}
    }
    Object.assign(window, {
      SpeechRecognition: NoSpeech,
      webkitSpeechRecognition: NoSpeech,
    });
  });
});
async function ready(page: Page, path: string) {
  await page.goto(path);
  await expect(page.locator("main h1")).toBeVisible();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
}
async function operator(page: Page, caseId = "CR-019") {
  await ready(
    page,
    root + caseId + (caseId === "CR-017" ? "?tab=activity" : ""),
  );
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page
    .getByRole("dialog", { name: "Demo access" })
    .getByRole("button", { name: /^Program operator/ })
    .click();
  await expect(
    page.getByRole("button", { name: "Demo profile", exact: true }),
  ).toBeVisible();
}
test("traceability labels preserve unknown, incomplete, and unverified states", () => {
  expect(operationLabel("get_program_milestone")).toBe(
    "Read the milestone dates and dependencies",
  );
  expect(operationLabel("unfamiliar_tool")).toBe("Unfamiliar tool");
  expect(versionLabel(null, null)).toBe("Version not recorded");
  expect(versionLabel(1, null)).not.toContain("unrecorded");
  expect(
    findingText("Exact source-backed standard package assessment."),
  ).toContain("does not include a detailed conclusion");
  expect(
    actionExplanation({ status: "Succeeded", verification: "Pending" }),
  ).toContain("has not yet confirmed");
  expect(
    actionExplanation({ status: "Succeeded", verification: "Mismatch" }),
  ).toContain("differs");
  expect(
    actionExplanation({ status: "Succeeded", verification: "Verified" }),
  ).toContain("matched the expected change");
  expect(
    actionExplanation({
      status: "Failed",
      verification: "Pending",
      error: "FAILED",
    }),
  ).toContain("problem");
  expect(failureLabel("false_validation_pass")).toContain(
    "without supporting evidence",
  );
  expect(evidenceReason("INSUFFICIENT_DURATION")).toBe(
    "Test duration is shorter than required",
  );
  expect(gateLabel("UNKNOWN")).toBe("Required-check result unavailable");
});
test("traceability source summaries use only complete policy checks saved with the same run", async ({
  request,
}) => {
  const data = await (await request.get("/control-api/cases/CR-017")).json();
  const h = data.standard.handoffs.find(
    (h: any) => h.run_id === runs["CR-019"],
  );
  expect(
    savedStandardFinding(runs["CR-019"], "change_impact", "completed", h),
  ).toContain("match the approved scope");
  expect(
    savedStandardFinding("a_different_run", "change_impact", "completed", h),
  ).toBeUndefined();
  expect(
    savedStandardFinding(runs["CR-019"], "change_impact", "failed", h),
  ).toBeUndefined();
  const failed = structuredClone(h);
  failed.eligibility.checks.find(
    (c: any) => c.code === "EXACT_SOFTWARE_BASELINE",
  ).passed = false;
  expect(
    savedStandardFinding(runs["CR-019"], "change_impact", "completed", failed),
  ).toContain("Checks needing review");
  failed.eligibility.checks = [];
  expect(
    savedStandardFinding(runs["CR-019"], "change_impact", "completed", failed),
  ).toBeUndefined();
});
test("traceability findings and exact source records are readable across all four cases", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const [width, height] of [
    [1440, 900],
    [1920, 1080],
    [1280, 800],
  ]) {
    await page.setViewportSize({ width, height });
    for (const id of ["CR-019", "QE-004", "DR-009", "CR-017"]) {
      await ready(page, root + id + (id === "CR-017" ? "?tab=activity" : ""));
      const findings = page.getByRole("heading", {
        name: "Agent findings",
        exact: true,
      });
      await expect(findings).toBeVisible();
      const branches = page.getByLabel("Recorded specialist work");
      await expect(branches).toContainText("Assigned task");
      await expect(branches).toContainText("What was found");
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      ).toBe(true);
      if (id === "CR-019") {
        const card = branches.locator("article").first();
        await card.getByText(/^Sources consulted \(/).click();
        await expect(card.locator(".tr-sources")).toContainText(
          "Change request",
        );
        expect(await card.innerText()).not.toContain("get_program");
        await card
          .getByText("Source record & versions", { exact: true })
          .first()
          .click();
        await expect(card).toContainText("get_program");
        await expect(card).toContainText("Document / content version 1");
        await page
          .getByRole("heading", { name: "Agent findings", exact: true })
          .scrollIntoViewIfNeeded();
        await page
          .locator("section.cp-section")
          .filter({ has: findings })
          .screenshot({ path: `${shots}/findings-${width}.png` });
      }
    }
  }
  expect(errors).toEqual([]);
});
test("traceability Operations explains actions and retains historical failures", async ({
  page,
}) => {
  for (const id of ["CR-019", "CR-017", "QE-004", "DR-009"]) {
    await operator(page, id);
    await page
      .getByRole("link", { name: "See what happened", exact: true })
      .click();
    await expect(page).toHaveURL(new RegExp("/control/runs/" + runs[id]));
    await expect(
      page.getByRole("heading", { name: "What each agent did" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "What happened", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Sources the agents consulted" }),
    ).toBeVisible();
    if (id === "CR-019") {
      const actions = page.locator("#run-actions");
      await expect(actions).toContainText("matched the expected change");
      expect(await actions.innerText()).not.toContain("standard_");
      await actions.getByText("Compare expected and saved records").click();
      await expect(actions).toContainText("intake-");
      await actions.scrollIntoViewIfNeeded();
      await page.screenshot({ path: `${shots}/confirmed-action.png` });
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
  }
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Operations", exact: true })
    .click();
  await page
    .getByRole("link", { name: "Evals & Reliability", exact: true })
    .click();
  const failed = page.locator("#eval-live-original");
  await failed.getByText("What was tested and what failed").click();
  await expect(failed).toContainText("Required checks failed");
  await expect(failed).toContainText(
    "Claimed a passing test without supporting evidence",
  );
  await expect(failed).toContainText("Evidence already covers the request");
  expect(await failed.innerText()).not.toContain("false_validation_pass");
  await failed.getByText("Check reference", { exact: true }).first().click();
  await expect(failed).toContainText("approval_bypass");
  await failed.scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${shots}/evals.png` });
});
