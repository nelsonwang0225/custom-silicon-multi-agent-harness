import { test as base, expect, type Page } from "@playwright/test";
import { spawn, type ChildProcess } from "node:child_process";
import { mkdir } from "node:fs/promises";
import path from "node:path";
const root = path.resolve(".."),
  origin = "http://127.0.0.1:5175";
const basePath = "/control/programs/PRG-A17/cases/CR-017";
const shots = path.join(root, "docs/phase08/workflows/screenshots");
const test = base.extend<{ fault: string; isolated: void }>({
  fault: ["none", { option: true }],
  isolated: [
    async ({ request, fault }, use) => {
      let proc: ChildProcess | undefined;
      if (!process.env.PHASE08_REUSE_PREVIEW) {
        proc = spawn(
          path.join(root, "coordinator/.venv/bin/python"),
          [
            "-m",
            "coordinator.evals.phase08_2.serve",
            "--fault",
            fault,
            "--delay",
            "1.5",
          ],
          {
            cwd: root,
            env: { ...process.env, PYTHONPATH: "src:." },
            stdio: "pipe",
          },
        );
        let logs = "";
        proc.stdout?.on("data", (x) => (logs += x));
        proc.stderr?.on("data", (x) => (logs += x));
        await expect
          .poll(
            async () => {
              if (proc?.exitCode !== null) throw new Error(logs);
              return (
                await request
                  .get("http://127.0.0.1:18083/control-api/health")
                  .catch(() => null)
              )?.status();
            },
            { timeout: 20000 },
          )
          .toBe(200);
      }
      await mkdir(shots, { recursive: true });
      await use();
      if (proc) {
        proc.kill("SIGTERM");
        await new Promise<void>((resolve) =>
          proc!.once("exit", () => resolve()),
        );
      }
    },
    { auto: true },
  ],
});
async function profile(page: Page, name: string) {
  await expect(
    page.getByRole("button", { name: /^(Log in|Demo profile)$/ }),
  ).toBeVisible();
  if (await page.getByRole("button", { name: "Log in", exact: true }).count())
    await page.getByRole("button", { name: "Log in", exact: true }).click();
  else {
    await page
      .getByRole("button", { name: "Demo profile", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Switch profile", exact: true })
      .click();
  }
  await page
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: new RegExp(name) })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Demo access", exact: true }),
  ).toHaveCount(0);
}
async function capture(page: Page, name: string) {
  await expect(
    page.getByText("Connected demo · Current read", { exact: true }),
  ).toBeVisible({ timeout: 20000 });
  const reduce = page.getByRole("button", {
    name: "Reduce Stratos Concierge",
    exact: true,
  });
  if ((await reduce.count()) && !(await page.locator("dialog[open]").count()))
    await reduce.click();
  await page.screenshot({
    path: path.join(shots, name + ".png"),
    fullPage: !(await page.locator("dialog[open]").count()),
  });
}
async function next(page: Page) {
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Continue", exact: true })
    .click();
}
async function newConfig(page: Page, name: string, type = "schedule") {
  await page.goto("/control/workflows");
  await profile(page, "Program operator");
  await page
    .getByRole("button", { name: "New automation", exact: true })
    .click();
  const dialog = page.getByRole("dialog", {
    name: "New automation configuration",
  });
  await dialog.getByLabel("Name", { exact: true }).fill(name);
  await next(page);
  await dialog.getByLabel("Trigger type").selectOption(type);
  return dialog;
}
async function saveConfig(page: Page) {
  await next(page);
  await next(page);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save automation", exact: true })
    .click();
  await expect(page).toHaveURL(/\/control\/automations\/automation_/);
  await expect(
    page.getByRole("heading", { name: "Configuration preview", exact: true }),
  ).toBeVisible();
}
async function search(page: Page, term: string, title: RegExp) {
  await expect(page.getByLabel("Search Stratos", { exact: true })).toHaveValue(
    "",
  );
  await page.getByLabel("Search Stratos", { exact: true }).fill(term);
  await page
    .getByRole("dialog", { name: "Search results" })
    .getByRole("button", { name: title })
    .click();
}

test("workflow discovery, shared manual launch, real run detail and search", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/control/workflows");
  await expect(
    page.getByRole("heading", { name: "Workflow catalog", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".cp-workflow-catalog > a")).toHaveCount(13);
  await expect(page.locator(".cp-workflow-counts")).toContainText(
    "4 Connected",
  );
  await expect(page.locator(".cp-workflow-counts")).toContainText(
    "0 Simulated",
  );
  await expect(page.locator(".cp-workflow-counts")).toContainText("9 Preview");
  await capture(page, "01-catalog");
  await page
    .locator(".cp-workflow-catalog > a")
    .filter({
      has: page.getByRole("heading", {
        name: "Requirement Change Analysis",
        exact: true,
      }),
    })
    .click();
  await expect(
    page.getByRole("button", { name: "Run workflow", exact: true }),
  ).toBeDisabled();
  await profile(page, "Program operator");
  await expect(
    page.getByRole("button", { name: "Run workflow", exact: true }),
  ).toBeEnabled();
  await capture(page, "02-connected-detail");
  await page
    .getByRole("button", { name: "Run workflow", exact: true })
    .dblclick();
  await expect(page).toHaveURL(/\/control\/runs\/run_/);
  await expect(
    page.getByRole("heading", { name: "Workflow run", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Waiting for human review",
      exact: true,
    }),
  ).toBeVisible({ timeout: 30000 });
  await expect(
    page.getByText("Completed", { exact: true }).first(),
  ).toBeVisible();
  const state = await (
    await page.request.get("/control-api/cases/CR-017")
  ).json();
  expect(state.runs).toHaveLength(1);
  expect(state.runs[0].business_outcome).toBe("Waiting for review");
  expect(state.runs[0].specialists).toHaveLength(4);
  await capture(page, "03-run-detail");
  await page
    .getByRole("link", { name: "Open CR-017", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(new RegExp(basePath));
  await search(
    page,
    state.runs[0].run_id,
    new RegExp("^CR-017 · " + state.runs[0].run_id),
  );
  await expect(page).toHaveURL(
    new RegExp("/control/runs/" + state.runs[0].run_id),
  );
  await search(page, "requirement change", /^Requirement Change Analysis/);
  await expect(page).toHaveURL(
    /\/control\/workflows\/requirement_change_analysis/,
  );
  await page.goto("/control/workflows");
  await page
    .getByRole("region", { name: "Run history table", exact: true })
    .scrollIntoViewIfNeeded();
  await capture(page, "04-run-history");
  expect(errors).toEqual([]);
});

test("schedule configuration create, edit, pause, resume, delete and persistence", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/control/workflows");
  await profile(page, "Program operator");
  const dialog = await newConfig(page, "Weekly CR-017 review");
  await dialog.getByLabel("Cadence", { exact: true }).selectOption("weekly");
  await dialog.getByLabel("Day of week").selectOption("2");
  await dialog.getByLabel("Time", { exact: true }).fill("08:15");
  await dialog
    .getByLabel("Timezone", { exact: true })
    .selectOption("America/Chicago");
  await dialog.getByLabel("Start date (optional)").fill("2026-11-18");
  await expect(dialog).toContainText("Would run: Wednesday at 8:15 AM");
  await capture(page, "05-schedule-editor");
  await next(page);
  await expect(
    dialog.getByLabel("Authority", { exact: true }).locator("option"),
  ).toHaveCount(1);
  await next(page);
  await expect(dialog).toContainText(
    "Saved configuration — background execution not enabled",
  );
  await capture(page, "06-review-configuration");
  await dialog
    .getByRole("button", { name: "Save automation", exact: true })
    .click();
  await expect(page).toHaveURL(/\/control\/automations\/automation_/);
  await expect(
    page.getByRole("dialog", { name: "New automation configuration" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Weekly CR-017 review", exact: true }),
  ).toBeVisible();
  const url = page.url();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Weekly CR-017 review", exact: true }),
  ).toBeVisible();
  await profile(page, "Program operator");
  await page
    .getByRole("button", { name: "Edit configuration", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByLabel("Name", { exact: true })
    .fill("Daily CR-017 review");
  await next(page);
  await page
    .getByRole("dialog")
    .getByLabel("Cadence", { exact: true })
    .selectOption("daily");
  await next(page);
  await next(page);
  // Hold a read from before the edit. A successful write must wait and refetch,
  // so the next pause uses the new version rather than this stale response.
  let releaseRead!: () => void, observedRead!: () => void;
  const release = new Promise<void>((resolve) => {
    releaseRead = resolve;
  });
  const observed = new Promise<void>((resolve) => {
    observedRead = resolve;
  });
  let held = false;
  await page.route("**/control-api/cases/CR-017", async (route) => {
    if (held) {
      await route.continue();
      return;
    }
    held = true;
    const response = await route.fetch();
    observedRead();
    await release;
    await route.fulfill({ response });
  });
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await observed;
  const updateReply = page.waitForResponse(
    (r) => r.url().endsWith("/update") && r.request().method() === "POST",
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await updateReply;
  releaseRead();
  await expect(
    page.getByRole("dialog", { name: "Edit automation configuration" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Daily CR-017 review", exact: true }),
  ).toBeVisible();
  await page.unroute("**/control-api/cases/CR-017");
  await page
    .getByRole("button", { name: "Pause configuration", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Resume configuration", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Resume configuration", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Pause configuration", exact: true }),
  ).toBeVisible();
  await search(page, "Daily CR-017 review", /^Daily CR-017 review/);
  await expect(page).toHaveURL(url);
  await page.goto("/control/workflows");
  await profile(page, "Program operator");
  await page
    .getByRole("heading", { name: "Automation configurations", exact: true })
    .scrollIntoViewIfNeeded();
  await capture(page, "07-automation-list");
  await page.getByRole("link", { name: /^Daily CR-017 review/ }).click();
  await page
    .getByRole("button", { name: "Delete configuration", exact: true })
    .click();
  await expect(page).toHaveURL(/\/control\/workflows$/);
  await expect(
    page.getByRole("link", { name: /^Daily CR-017 review/ }),
  ).toHaveCount(0);
  const state = await (
    await page.request.get("/control-api/cases/CR-017")
  ).json();
  expect(state.runs).toEqual([]);
  expect(state.proposals).toEqual([]);
  expect(state.automations).toHaveLength(3);
  expect(errors).toEqual([]);
});

test("event and condition previews, future workflows blocked, no scheduler alerts", async ({
  page,
}) => {
  const writes: string[] = [];
  page.on("request", (r) => {
    if (r.method() !== "GET" && r.url().includes("/api/v1"))
      writes.push(r.url());
  });
  await page.goto("/control/workflows");
  await profile(page, "Program operator");
  const event = await newConfig(page, "Result arrival preview", "source_event");
  await event
    .getByLabel("Source system", { exact: true })
    .selectOption("validation");
  await event
    .getByLabel("Source event", { exact: true })
    .selectOption("result_received");
  await expect(event).toContainText("listener is not active");
  await saveConfig(page);
  const condition = await newConfig(page, "Evidence age preview", "condition");
  await condition
    .getByLabel("Business field")
    .selectOption("evidence_age_hours");
  await condition.getByLabel("Threshold (hours)").fill("36");
  await expect(condition).toContainText("No background evaluator");
  await capture(page, "08-condition-editor");
  await saveConfig(page);
  for (const id of ["tapeout_readiness", "specification_drift"]) {
    await page.goto(`/control/workflows/${id}`);
    await expect(
      page.getByText("This workflow is not connected yet.", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Run workflow", exact: true }),
    ).toBeDisabled();
    const denial = await page.request.post(
      `/control-api/workflows/${id}/runs`,
      {
        data: { invocation_id: "ui_blocked" },
        headers: {
          Origin: origin,
          "X-Stratos-Action": "1",
          "X-Stratos-Demo-Profile": "automation",
        },
      },
    );
    expect(denial.status()).toBe(409);
  }
  await page.goto("/control/overview");
  await expect(
    page.getByRole("link", {
      name: "5 automation configurations",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Alerts,/ }).click();
  await expect(
    page.getByRole("dialog", { name: "Source alerts" }),
  ).not.toContainText(
    /automation failed|scheduler|Result arrival preview|Evidence age preview/i,
  );
  await page.keyboard.press("Escape");
  await page.goto("/control/workflows");
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await expect(
    page.getByRole("button", {
      name: "What workflows are available?",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "What would this automation do?",
      exact: true,
    }),
  ).toBeVisible();
  const state = await (
    await page.request.get("/control-api/cases/CR-017")
  ).json();
  expect(state.runs).toEqual([]);
  expect(state.proposals).toEqual([]);
  expect(state.automations).toHaveLength(5);
  expect(
    state.automations.every(
      (a: { background_execution_enabled: boolean }) =>
        !a.background_execution_enabled,
    ),
  ).toBe(true);
  expect(writes).toEqual([]);
});
