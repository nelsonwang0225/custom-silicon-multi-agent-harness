import { test, expect, type Page } from "@playwright/test";
import { spawn, type ChildProcess } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir, open } from "node:fs/promises";
const root = ".cache/phase09-1/browser/" + randomUUID();
const cases = "/control/programs/PRG-A17/cases/";
let processHandle: ChildProcess;
async function start() {
  await mkdir("../" + root, { recursive: true });
  const log = await open("../" + root + "/services.log", "a");
  processHandle = spawn(
    "coordinator/.venv/bin/python",
    ["-m", "coordinator.evals.phase09_1.serve", "--root", root],
    {
      cwd: "..",
      env: { ...process.env, PYTHONPATH: "src:." },
      stdio: ["ignore", log.fd, log.fd],
    },
  );
  await log.close();
  await expect
    .poll(
      async () => {
        try {
          return (await fetch("http://127.0.0.1:18191/control-api/health"))
            .status;
        } catch {
          return 0;
        }
      },
      { timeout: 30000 },
    )
    .toBe(200);
}
async function stop() {
  if (!processHandle || processHandle.exitCode != null) return;
  const stopped = new Promise<void>((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error("Owned reset fixture did not stop")),
      15000,
    );
    processHandle.once("exit", () => {
      clearTimeout(timer);
      resolve();
    });
  });
  processHandle.kill("SIGTERM");
  await stopped;
}
test.beforeAll(start);
test.afterAll(stop);
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    class MockSpeechRecognition {
      start() {
        throw new Error("No microphone is permitted in reset testing");
      }
      abort() {}
      stop() {}
    }
    Object.assign(window, {
      SpeechRecognition: MockSpeechRecognition,
      webkitSpeechRecognition: MockSpeechRecognition,
    });
  });
});
async function post(
  page: Page,
  path: string,
  body: unknown,
  role = "automation",
) {
  return page.request.post("/control-api/" + path, {
    data: body,
    headers: {
      Origin: "http://127.0.0.1:5191",
      "X-Stratos-Action": "1",
      "X-Stratos-Demo-Profile": role,
    },
  });
}
async function invoke(page: Page, id: string) {
  const response = await post(page, "cases/" + id + "/investigations", {
    invocation_id: "ui_reset_browser_" + randomUUID().replaceAll("-", ""),
    change_id: id,
    workflow_id:
      id === "QE-004"
        ? "yield_exception_recovery"
        : id === "DR-009"
          ? "delivery_readiness"
          : "requirement_change_analysis",
  });
  expect(response.status()).toBe(202);
  const run = (await response.json()).run_id;
  let state: any;
  await expect
    .poll(
      async () => {
        state = await (
          await page.request.get("/control-api/cases/" + id)
        ).json();
        return state.runs.find((r: any) => r.run_id === run)?.status;
      },
      { timeout: 60000 },
    )
    .toBe("completed");
  if (id === "CR-017")
    await expect
      .poll(async () => {
        state = await (
          await page.request.get("/control-api/cases/CR-017")
        ).json();
        return state.proposals.length;
      })
      .toBeGreaterThan(0);
  return state;
}
async function operator(page: Page) {
  await page.goto("/control/overview");
  const login = page.getByRole("button", { name: "Log in", exact: true });
  await expect(page.locator("main h1")).toBeVisible();
  if (await login.isVisible()) {
    await login.click();
    await page
      .getByRole("dialog", { name: "Demo access" })
      .getByRole("button", { name: /^Program operator/ })
      .click();
  }
  await expect(
    page
      .getByRole("navigation", { name: "Control plane navigation" })
      .getByRole("link", { name: "Operations", exact: true }),
  ).toBeVisible();
}
async function operations(page: Page, path = "/control/operations") {
  await operator(page);
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Operations", exact: true })
    .click();
  if (path !== "/control/operations")
    await page.locator(`a[href="${path}"]`).first().click();
}
async function uiReset(page: Page) {
  await operations(page, "/control/operations/demo");
  await page.getByRole("button", { name: "Review reset…" }).click();
  const dialog = page.getByRole("dialog", { name: "Reset full demo" });
  await expect(dialog).toContainText("Historical Phase 07");
  await expect(
    dialog.getByRole("button", { name: "Confirm demo reset" }),
  ).toBeDisabled();
  await dialog.getByLabel("Type RESET to confirm").fill("RESET");
  await capture(page, "confirmation");
  await dialog.getByRole("button", { name: "Confirm demo reset" }).click();
  await expect(dialog).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Log in", exact: true }),
  ).toBeVisible();
  await operations(page, "/control/operations/demo"); // Reset deliberately discards the previous UI persona.
  await expect(page.locator("main")).toContainText(
    "Passed at reset completion",
  );
  await page.getByRole("button", { name: "Verify baseline" }).click();
  await expect(
    page.getByRole("heading", { name: "Baseline valid · full" }),
  ).toBeVisible();
}
async function capture(page: Page, name: string) {
  await expect(page.locator("main")).toBeVisible();
  await mkdir("../docs/screenshots/phase09-1", { recursive: true });
  await page.screenshot({
    path: "../docs/screenshots/phase09-1/" + name + ".png",
    fullPage: true,
  });
}

test("mutate four connected paths, persist across restart, explicitly reset and verify every surface", async ({
  page,
  context,
}) => {
  await uiReset(page);
  const baseline = await (
    await page.request.get("/control-api/demo/verify", {
      headers: { "X-Stratos-Demo-Profile": "automation" },
    })
  ).json();
  await page.goto("/control/overview");
  await expect(page.locator("main")).toContainText("Overview");
  const standard = await invoke(page, "CR-019");
  expect(standard.handoffs[0].status).toBe("handoff_verified");
  const quality = await invoke(page, "QE-004");
  expect(quality.records.investigations).toHaveLength(1);
  const delivery = await invoke(page, "DR-009");
  const plan = delivery.records.plans[0];
  const exact = {
    run_id: delivery.progress[0].run_id,
    plan_id: plan.id,
    plan_version: plan.plan_version,
    plan_digest: plan.plan_digest,
  };
  expect(
    (
      await post(
        page,
        "delivery-commitment/review",
        { ...exact, decision: "approve", comment: "Scripted demo review" },
        "program_owner",
      )
    ).status(),
  ).toBe(200);
  expect(
    (
      await post(page, "delivery-commitment/execute", exact, "program_owner")
    ).status(),
  ).toBe(200);
  const cr = await invoke(page, "CR-017");
  const reference = cr.proposals[0].execution.reference;
  expect(
    (
      await post(
        page,
        "proposals/review",
        { reference, decision: "approve", comment: "Scripted demo review" },
        "engineer",
      )
    ).status(),
  ).toBe(200);
  expect((await post(page, "proposals/execute", { reference })).status()).toBe(
    200,
  );
  const oldRun = cr.runs[0].run_id;
  for (const id of ["CR-019", "QE-004", "DR-009", "CR-017"]) {
    await page.goto(cases + id);
    await expect(page.locator("main")).toContainText(id);
    if (id === "CR-019")
      await expect(page.locator("main")).toContainText(
        "Handed to Validation Operations",
      );
    if (id === "QE-004")
      await expect(page.locator("main")).toContainText(/hold/i);
    if (id === "DR-009")
      await expect(page.locator("main")).toContainText("600");
  }
  const stale = await context.newPage();
  await stale.goto(cases + "CR-017");
  await stale
    .getByRole("button", { name: /Open Stratos Concierge|Open Concierge/ })
    .click();
  await stale.getByLabel("Your draft").fill("Draft from the previous demo");
  await stop();
  await start();
  const persisted = await (
    await page.request.get("/control-api/cases/CR-017")
  ).json();
  expect(persisted.proposals[0].execution.status).toBe("completed_execution");
  expect(persisted.runs[0].run_id).toBe(oldRun);
  expect(
    (
      await (
        await page.request.get("/control-api/demo/verify", {
          headers: { "X-Stratos-Demo-Profile": "automation" },
        })
      ).json()
    ).baseline_valid,
  ).toBe(false);
  await uiReset(page);
  await expect(
    stale.getByRole("status").filter({ hasText: "Demo state changed" }),
  ).toBeVisible({ timeout: 15000 });
  await stale
    .getByRole("button", { name: /Open Stratos Concierge|Open Concierge/ })
    .click();
  await expect(stale.getByLabel("Your draft")).toHaveValue("");
  await capture(page, "baseline");
  const check = await (
    await page.request.get("/control-api/demo/verify", {
      headers: { "X-Stratos-Demo-Profile": "automation" },
    })
  ).json();
  expect(check.baseline_valid).toBe(true);
  expect(check.source_digest).toBe(baseline.source_digest);
  for (const id of ["CR-017", "CR-019", "QE-004", "DR-009"]) {
    const value = await (
      await page.request.get("/control-api/cases/" + id)
    ).json();
    expect(value.runs).toHaveLength(0);
    await page.goto(cases + id);
    await expect(page.locator("main")).toContainText(id);
  }
  await page.goto("/control/decisions");
  expect(
    (await (await page.request.get("/control-api/cases/CR-017")).json())
      .proposals,
  ).toHaveLength(0);
  await operations(page);
  await expect(page.locator("main")).toContainText("Demo controls");
  const search = page.getByRole("textbox", { name: "Search Stratos" });
  await search.fill(oldRun);
  await expect(
    page.getByRole("button", { name: new RegExp("^CR-017 · " + oldRun) }),
  ).toHaveCount(0);
  await search.fill("CR-019");
  await expect(
    page.getByRole("button", { name: /CR-019/ }).first(),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: /Notifications|alerts/i }).click();
  await expect(page.getByLabel("Source alerts")).toContainText(
    "Hard gate failed",
  );
  await page.keyboard.press("Escape");
  await operations(page, "/control/operations/evals");
  await expect(page.locator("main")).toContainText("4/6 — FAIL");
  await capture(page, "preserved-history");
  await stop();
  await start();
  await page.reload();
  const restarted = await (
    await page.request.get("/control-api/demo/verify", {
      headers: { "X-Stratos-Demo-Profile": "automation" },
    })
  ).json();
  expect(restarted.baseline_valid).toBe(true);
  expect(restarted.source_digest).toBe(check.source_digest);
  await operations(page, "/control/operations/demo");
  await expect(
    page.getByRole("heading", { name: "Demo controls", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Review reset…" }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Verify baseline" }).click();
  await expect(
    page.getByRole("heading", { name: "Baseline valid · full" }),
  ).toBeVisible();
  await expect(page.locator(".cp-concierge-dock")).toHaveClass(
    /cp-dock-minimal/,
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth + 1,
    ),
  ).toBe(true);
  await capture(page, "mobile");
  await stale.close();
});
