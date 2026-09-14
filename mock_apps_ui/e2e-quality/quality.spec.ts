import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const path = "/control/programs/PRG-A17/cases/QE-004",
  variant = process.env.QUALITY_VARIANT || "comparable";
const artifactDir =
  process.env.SOURCE_BROWSER_ARTIFACT_DIR || "../docs/screenshots/phase08-4b";
async function login(page: any, role: string) {
  await page
    .locator('button[aria-label="Log in"], button[aria-label="Demo profile"]')
    .waitFor({ state: "visible" });
  const button = page.getByRole("button", { name: "Log in", exact: true });
  if (await button.isVisible()) {
    await button.click();
  } else {
    await page
      .getByRole("button", { name: "Demo profile", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Switch profile", exact: true })
      .click();
  }
  await page
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: role, exact: false })
    .click();
}
test("QE-004 source to investigation, exact human recovery and independent readback", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/control/overview");
  await page.getByRole("link", { name: "Inspect case QE-004" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Final-test pass-rate exception for held lot LOT-B-204",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      /Investigate the final-test pass-rate exception affecting held lot LOT-B-204/,
    ),
  ).toBeVisible();
  await expect(
    page.getByText("View original request", { exact: true }),
  ).toBeVisible();
  await login(page, "Program operator");
  await page
    .getByRole("button", { name: "Run investigation", exact: true })
    .click();
  await expect
    .poll(
      async () => {
        const r = await request.get("/control-api/cases/QE-004");
        return (await r.json()).status;
      },
      { timeout: 45000 },
    )
    .toBe("draft_ready");
  await page.reload();
  await login(page, "Program operator");
  await expect(
    page.getByRole("heading", { name: "Agent findings", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/affected units remain on hold/)).toBeVisible();
  await expect(
    page.getByText("Agent recommendation · Proposed actions", { exact: true }),
  ).toBeVisible();
  const agentRecommendation = page.locator(".cp-agent-recommendation");
  await expect(
    agentRecommendation.getByRole("heading", { level: 3 }),
  ).toHaveText([
    "Contain LOT-B-204",
    "Investigate SITE-2",
    "Execute a controlled recovery",
    "Protect MS-HEL-800",
  ]);
  await expect(
    page.getByRole("button", { name: "Approve recovery plan", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", {
      name: "Review & submit recovery recommendation",
    }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Operator notes" })
    .fill("Reviewed for the Helios milestone.");
  await page.getByRole("button", { name: "Submit to Program Owner" }).click();
  await expect(
    page.getByText("Submitted to Program Owner", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Alerts,/ }).click();
  await expect(
    page
      .getByRole("dialog", { name: "Source alerts" })
      .locator('article:has(a[href$="/cases/QE-004"])'),
  ).toContainText("Needs review");
  await page.getByRole("button", { name: "Close alerts" }).click();
  const state = await (await request.get("/control-api/cases/QE-004")).json();
  expect(state.status).toBe("awaiting_review");
  const p = state.progress[0];
  expect(state.context.analysis.comparable).toBe(
    variant === "incomparable" ? "false" : "true",
  );
  expect(state.context.analysis.affected_eligible_quantity).toBe(0);
  expect(state.context.analysis.gap_quantity).toBe(
    variant === "no_alternative_supply" ? 800 : 200,
  );
  const ref = {
    run_id: p.run_id,
    plan_id: p.plan_id,
    plan_version: p.plan_version,
    plan_digest: p.plan_digest,
  };
  const wrong = await request.post("/control-api/quality-recovery/review", {
    data: { ...ref, decision: "approve" },
    headers: {
      Origin: "http://127.0.0.1:5177",
      "X-Stratos-Action": "1",
      "X-Stratos-Demo-Profile": "automation",
    },
  });
  expect(wrong.status()).toBe(403);
  // Switching through the existing local demo identity UI is an explicit human test action.
  await page.getByRole("button", { name: "Demo profile", exact: true }).click();
  await page
    .getByRole("button", { name: "Switch profile", exact: true })
    .click();
  await page
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: "Program Owner", exact: false })
    .click();
  await page
    .getByRole("textbox", { name: "Decision comment" })
    .fill(
      "Record recovery planning with released supply; retain the Quality hold.",
    );
  await page
    .getByRole("button", { name: "Approve recovery plan", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Execute approved recovery task" }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Execute approved recovery task" })
    .click();
  await expect
    .poll(async () => {
      const r = await request.get("/control-api/cases/QE-004");
      return (await r.json()).status;
    })
    .toBe("verified");
  const final = await (await request.get("/control-api/cases/QE-004")).json();
  expect(final.context).toEqual(state.context);
  expect(final.records.tasks).toHaveLength(1);
  expect(final.records.tasks[0].lot_released).toBe(false);
  const release = await request.post(
    "/api/v1/manufacturing/lots/LOT-B-204/release",
    {
      data: {},
      headers: {
        Authorization: "Bearer demo-automation-local-only",
        "Idempotency-Key": "browser-release-denied",
      },
    },
  );
  expect([404, 405]).toContain(release.status());
  await page.reload();
  await expect(
    page.getByRole("heading", {
      name: "Final-test pass-rate exception for held lot LOT-B-204",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.locator(".cp-source-outcome").filter({ hasText: "Planner outcome" }),
  ).toContainText(final.records.tasks[0].id);
  await mkdir(artifactDir, { recursive: true });
  await page.screenshot({
    path: `${artifactDir}/${variant}.png`,
    fullPage: true,
  });
  await page.goto("/control/decisions");
  await login(page, "Program Owner");
  await page.getByRole("link", { name: "Decisions", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Decision status", exact: true })
    .selectOption("Needs review");
  await expect(
    page.locator('.cp-decision-row[data-case-id="QE-004"]'),
  ).toHaveCount(0);
  await page
    .getByRole("combobox", { name: "Decision status", exact: true })
    .selectOption("Executed / Completed");
  await expect(
    page.locator('.cp-decision-row[data-case-id="QE-004"]'),
  ).toHaveCount(1);
  await page.goto("/control/workflows/yield_exception_recovery");
  await login(page, "Program operator");
  await page
    .getByRole("link", { name: "Workflows & Automations", exact: true })
    .click();
  await page
    .locator('a[href="/control/workflows/yield_exception_recovery"]')
    .first()
    .click();
  await expect(
    page.getByText("Connected", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByText(/Connected workflow · Trigger listener not active/),
  ).toBeVisible();
  const runLink = page.locator(`a[href="/control/runs/${p.run_id}"]`);
  await expect(runLink).toBeVisible();
  await runLink.click();
  await expect(page).toHaveURL(new RegExp(`/control/runs/${p.run_id}$`));
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Run history", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Search Stratos", { exact: true }).fill("LOT-B-204");
  await page
    .getByRole("dialog", { name: "Search results" })
    .getByRole("button", { name: /QE-004 · Yield/ })
    .click();
  await expect(page).toHaveURL(new RegExp(`${path}$`));
  await page.goto("/control/overview");
  const summary = (
    await (await request.get("/control-api/cases/CR-017")).json()
  ).case_summaries.find((item: any) => item.change_id === "QE-004");
  expect(summary.state).toBe("completed_recovery");
  expect(summary.attention).toBe("none");
  await expect(
    page.locator(
      '.cp-attention [data-case-id="QE-004"][data-case-state="needs_review"]',
    ),
  ).toHaveCount(0);
  await page.getByRole("button", { name: /^Alerts,/ }).click();
  await expect(
    page
      .getByRole("dialog", { name: "Source alerts" })
      .locator('article:has(a[href$="/cases/QE-004"])'),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Close alerts" }).click();
  await page.goto("/manufacturing/quality/QE-004");
  await expect(
    page.getByRole("heading", { name: "Quality investigations" }),
  ).toBeVisible();
  await expect(
    page.getByText(final.records.investigations[0].id, { exact: true }),
  ).toBeVisible();
  await page.goto("/programs/quality/QE-004");
  await expect(
    page.getByRole("heading", { name: final.records.tasks[0].id }),
  ).toBeVisible();
  await page.goto(path);
  await expect(
    page.getByRole("heading", {
      name: "Final-test pass-rate exception for held lot LOT-B-204",
      exact: true,
    }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect(errors).toEqual([]);
});
