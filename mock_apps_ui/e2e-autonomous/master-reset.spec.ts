import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";

const headers = { Origin: "http://127.0.0.1:5231", "X-Stratos-Action": "1", "X-Stratos-Demo-Profile": "automation", "X-Stratos-Demo-Maintainer": "local-demo-reset" };
const shots = "../docs/screenshots/phase10-master-reset";

test("masthead reset restores New cases and automatically restarts the moving QE-011 workspace", async ({ page, request, context }) => {
  page.setDefaultTimeout(15000);
  await context.addInitScript(() => {
    class NoSpeech { start() { throw Error("No real speech in tests"); } stop() {} abort() {} }
    Object.assign(window, { SpeechRecognition: NoSpeech, webkitSpeechRecognition: NoSpeech });
  });
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  const epoch = (await (await request.get("/control-api/demo")).json()).epoch;
  expect((await request.post("/control-api/demo/reset", { headers, data: { scope: "full", confirmation: "RESET", expected_epoch: epoch } })).ok()).toBeTruthy();
  // Maintenance entry keeps the fixture idle while preparing a completed case.
  await page.goto("/control/operations/demo");
  await expect(page.getByRole("button", { name: "Reset demo", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page.getByRole("dialog", { name: "Demo access" }).getByRole("button", { name: /^Program operator/ }).click();
  expect(await page.evaluate(() => sessionStorage.getItem("stratos:control-profile"))).toBe("automation");
  await page.getByRole("navigation", { name: "Control plane navigation" }).getByRole("link", { name: "Overview", exact: true }).click();
  await page.getByRole("link", { name: "Inspect case CR-019", exact: true }).click();
  await page.getByRole("button", { name: "Start connected investigation", exact: true }).click();
  await expect(page.getByText("Handoff verified", { exact: true }).first()).toBeVisible({ timeout: 30000 });
  await page.getByRole("navigation", { name: "Control plane navigation" }).getByRole("link", { name: "Overview", exact: true }).click();
  await expect(page.locator('.cp-attention [data-case-id="CR-019"]')).toHaveCount(0);
  await page.getByRole("button", { name: "Reset demo", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Reset and restart demo" });
  await expect(dialog.getByRole("button", { name: "Reset and restart", exact: true })).toBeEnabled();
  await mkdir(shots, { recursive: true });
  for (const [width, height] of [[1440, 900], [1920, 1080], [1280, 800]]) {
    await page.setViewportSize({ width, height });
    await page.screenshot({ path: `${shots}/confirmation-${width}.png` });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await dialog.getByRole("button", { name: "Reset and restart", exact: true }).click();
  await expect(page).toHaveURL(/\/control\/overview$/);
  await expect(page.getByText(/Demo reset complete\. All four cases are New/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Demo profile", exact: true })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem("stratos:control-profile"))).toBe("automation");
  for (const id of ["CR-017", "CR-019", "QE-004", "DR-009"]) {
    await expect(page.locator(`.cp-attention [data-case-id="${id}"]`)).toContainText("New");
  }
  await expect(page.locator(".cp-program-row").filter({ hasText: "Northstar Boreal" })).toContainText("On track");
  const initial = await (await request.get("/control-api/cases/CR-019")).json();
  expect(initial.runs).toEqual([]);
  expect(initial.eligibility).toBeNull();
  expect(initial.handoffs).toEqual([]);
  const workspace = page.getByRole("region", { name: "Agent workspace", exact: true });
  await expect(workspace.locator('[data-agent-id="coordinator"]')).toHaveAttribute("data-display-state", "processing", { timeout: 15000 });
  await expect(workspace.locator(".aw-flowing")).toHaveCount(4, { timeout: 20000 });
  const dot = workspace.locator(".aw-flowing circle").first();
  const before = await dot.evaluate(el => getComputedStyle(el).offsetDistance);
  await expect.poll(() => dot.evaluate(el => getComputedStyle(el).offsetDistance)).not.toBe(before);
  await page.screenshot({ path: `${shots}/restarted-1440.png`, fullPage: true });
  const first = (await (await request.get("/control-api/demo/autonomous", { headers })).json()).generation;
  // Reset works during an active opening too; the old run must not survive.
  await page.getByRole("button", { name: "Reset demo", exact: true }).click();
  await dialog.getByRole("button", { name: "Reset and restart", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(workspace).toContainText("QE-011 starts automatically");
  const second = (await (await request.get("/control-api/demo/autonomous", { headers })).json()).generation;
  expect(second).not.toBe(first);
  await page.reload();
  await expect(page.getByRole("button", { name: "Demo profile", exact: true })).toBeVisible();
  await expect(workspace).toContainText("QE-011 starts automatically");
  expect((await (await request.get("/control-api/demo/autonomous", { headers })).json()).generation).toBe(second);
  expect(errors).toEqual([]);
});
