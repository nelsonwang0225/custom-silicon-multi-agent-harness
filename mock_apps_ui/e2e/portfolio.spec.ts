import { test, expect, type Page } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
const API = "http://127.0.0.1:18000/api/v1";
const auth = (role = "reader") => ({
  Authorization: `Bearer demo-portfolio-${role}-local-only`,
});
async function ready(page: Page) {
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText(/Last API refresh/)).toBeVisible();
}

test("portfolio queues load persisted records and fit both desktop viewports", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const reads: { path: string; status: number }[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/api/v1/"))
      reads.push({ path: new URL(r.url()).pathname, status: r.status() });
  });
  const response = await request.get(API + "/portfolio", { headers: auth() });
  expect(response.status()).toBe(200);
  const portfolio = await response.json();
  expect(portfolio.cases).toHaveLength(41);
  expect(portfolio.history).toHaveLength(10);
  expect(portfolio.milestones).toHaveLength(91);
  mkdirSync("../docs/phase08/workflows/regression-08-2-1/regression-source", {
    recursive: true,
  });
  for (const [name, path] of [
    ["launcher", "/"],
    ["engineering-queue", "/engineering"],
    ["validation-jobs", "/validation/jobs"],
    ["validation-history", "/validation/history"],
    ["manufacturing-register", "/manufacturing"],
    ["erp-orders", "/erp"],
    ["program-portfolio", "/programs"],
  ]) {
    const start = Date.now();
    await page.goto(path);
    await ready(page);
    expect(Date.now() - start).toBeLessThan(10000);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    for (const [width, height] of [
      [1440, 900],
      [1280, 800],
    ]) {
      await page.setViewportSize({ width, height });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBeTruthy();
      await page.screenshot({
        path: `../docs/phase08/workflows/regression-08-2-1/regression-source/enrichment-${name}-${width}.png`,
      });
    }
  }
  expect(errors).toEqual([]);
  expect(
    reads.some((r) => r.path === "/api/v1/portfolio" && r.status === 200),
  ).toBeTruthy();
  writeFileSync(
    "../.cache/data-enrichment-browser-network.json",
    JSON.stringify(reads, null, 2),
  );
});

test("customer, program, priority and status filters expose real operating scope", async ({
  page,
}) => {
  await page.goto("/engineering");
  await ready(page);
  await expect(page.getByText("Page 1 of 4 · 41 changes")).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Page 2 of 4 · 41 changes")).toBeVisible();
  await page.getByLabel("Customer filter").selectOption("CUST-FML01");
  await expect(
    page.locator(".plm-worklist").getByRole("link", { name: /CR-017/ }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page.getByLabel("Priority filter").selectOption("low");
  await expect(page.getByText("No changes match these filters.")).toBeVisible();
  await page.getByLabel("Priority filter").selectOption("high");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page.getByLabel("Customer filter").selectOption("CUST-VELA");
  await page.getByLabel("Priority filter").selectOption("all");
  await page.getByLabel("Program filter").selectOption("PRG-P02");
  await expect(page.locator("tbody tr")).toHaveCount(4);
  await page.getByLabel("Search changes").fill("Power-envelope");
  await expect(page.locator("tbody tr")).toHaveCount(4);
  await page.goto("/manufacturing");
  await ready(page);
  await page.getByLabel("Customer filter").selectOption("CUST-NORTH");
  await expect(page.locator("tbody tr")).toHaveCount(11);
  await page.getByLabel("Restriction filter").selectOption("held");
  await expect(page.locator("tbody tr")).toHaveCount(2);
  await page.goto("/erp");
  await ready(page);
  await page.getByLabel("Customer filter").selectOption("CUST-NORTH");
  await expect(page.locator("tbody tr")).toHaveCount(2);
  await page.getByLabel("Order status").selectOption("allocation_pending");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page.goto("/programs");
  await ready(page);
  await page.getByLabel("Customer filter").selectOption("CUST-VELA");
  await expect(page.locator("tbody tr")).toHaveCount(2);
});

test("case selection computes options for that program and historical observations remain separate", async ({
  page,
}) => {
  await page.goto("/validation/options");
  await ready(page);
  await page.getByLabel("Change", { exact: true }).selectOption("CR-105");
  await ready(page);
  await expect(page).toHaveURL(/change=CR-105/);
  await expect(
    page.getByRole("heading", { name: "SLOT-P01-2", exact: true }),
  ).toHaveCount(5);
  await expect(
    page.getByRole("heading", { name: "SLOT-PRIORITY", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Work already scheduled", { exact: true }),
  ).toBeVisible();
  await page.goto("/validation/jobs");
  await ready(page);
  await page.getByLabel("Lab filter").selectOption("LAB-P01-0");
  await page.getByLabel("Product configuration").selectOption("CFG-P01");
  await page.getByLabel("Customer filter").selectOption("CUST-VELA");
  await expect(page.getByLabel("Lab filter")).toHaveValue("all");
  await expect(page.getByLabel("Product configuration")).toHaveValue("all");
  await page.goto("/validation/jobs?change=CR-105");
  await ready(page);
  await expect(
    page.getByRole("button", {
      name: "Schedule exact validation job",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Work already scheduled", { exact: true }),
  ).toBeVisible();
  await page.goto("/validation/history");
  await ready(page);
  await page.getByLabel("Customer filter").selectOption("CUST-NORTH");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page.getByRole("link", { name: "HJOB-P01", exact: true }).click();
  await ready(page);
  await expect(
    page.getByText("Northstar Boreal Lab Operations", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "RES-P01-2", exact: true }).click();
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "RES-P01-2", exact: true }),
  ).toBeVisible();
  await page.goto("/programs/PRG-P01/milestones/MS-P01-9");
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "Dependency review", exact: true }),
  ).toBeVisible();
  await page.getByText("Preview REQ-P01-1-V1", { exact: true }).click();
  await expect(
    page.getByText("approved", { exact: true }).first(),
  ).toBeVisible();
});

test("scripted portfolio API write is visible after UI refresh without changing evidence", async ({
  page,
  request,
}) => {
  console.log(
    "SCRIPTED INTEGRATION CHECK — NO AI; MOCK ROLES; EXISTING HTTP API WRITE.",
  );
  const before = await (
    await request.get(API + "/validation/coverage?change_id=CR-106", {
      headers: auth(),
    })
  ).json();
  await page.goto("/programs/PRG-P01");
  await ready(page);
  const body = {
    plan_id: "plan-P01-2",
    approval_id: "decision-P01-2",
    job_id: "job-P01-2",
    expected_milestone_record_version: 1,
  };
  const key = crypto.randomUUID();
  const r = await request.post(API + "/programs/PRG-P01/implementation-links", {
    headers: { ...auth("automation"), "Idempotency-Key": key },
    data: body,
  });
  expect(r.status()).toBe(201);
  const linked = await r.json();
  expect(linked.program_id).toBe("PRG-P01");
  const replay = await request.post(
    API + "/programs/PRG-P01/implementation-links",
    { headers: { ...auth("automation"), "Idempotency-Key": key }, data: body },
  );
  expect(replay.headers()["idempotency-replayed"]).toBe("true");
  expect(await replay.json()).toEqual(linked);
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await ready(page);
  await page
    .locator(".program-case summary")
    .filter({ hasText: "CR-106" })
    .click();
  await expect(page.locator("#link-" + linked.id)).toBeVisible();
  await page.reload();
  await ready(page);
  await page
    .locator(".program-case summary")
    .filter({ hasText: "CR-106" })
    .click();
  await expect(page.locator("#link-" + linked.id)).toBeVisible();
  const after = await (
    await request.get(API + "/validation/coverage?change_id=CR-106", {
      headers: auth(),
    })
  ).json();
  expect(after).toEqual(before);
  writeFileSync(
    "../.cache/data-enrichment-api-receipt.json",
    JSON.stringify(
      {
        label: "Scripted integration, no AI, simulated roles",
        plan: body.plan_id,
        job: body.job_id,
        link: linked.id,
        task: linked.task_id,
        replay: true,
        evidenceUnchanged: true,
      },
      null,
      2,
    ),
  );
});
