// UI regression checks: isolated source HTTP state, deterministic harness, no paid models.
import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const shots = "../.cache/rethink-implementation/screenshots";
const attention = (page: Page) => page.locator(".rb-attention-panel");
async function ready(page: Page, path = "/control/overview") {
  await page.goto(path);
  await expect(page.locator("#cp-main h1")).toBeVisible();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  if (path === "/control/operations")
    await expect(
      page.getByRole("heading", { name: "Run history", exact: true }),
    ).toBeVisible();
  if (path === "/control/knowledge") {
    await expect(
      page.getByText("Reading the controlled library…", { exact: true }),
    ).toHaveCount(0);
    await expect(page.locator(".kn-library-row").first()).toBeVisible();
  }
}
async function choose(page: Page, name: string) {
  const login = page.getByRole("button", { name: "Log in", exact: true });
  if (await login.isVisible()) await login.click();
  else {
    await page
      .getByRole("button", { name: "Demo profile", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Switch profile", exact: true })
      .click();
  }
  await page
    .getByRole("dialog", { name: "Demo access" })
    .getByRole("button", { name: new RegExp("^" + name) })
    .click();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
}
test.beforeEach(async ({ page }) => {
  await page.route("**/control-api/demo", (route) =>
    route.fulfill({ json: { enabled: false } }),
  );
  await page.addInitScript(() => {
    Object.defineProperty(window, "SpeechRecognition", { value: undefined });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      value: undefined,
    });
  });
});
test.afterEach(async ({ page }) => {
  await page.unrouteAll({ behavior: "ignoreErrors" });
});
test("All statuses restores completed cases, while attention excludes a verified handoff", async ({
  page,
}) => {
  await page.route("**/control-api/cases/CR-017", async (route) => {
    const response = await route.fetch(),
      data = await response.json();
    const standard = data.case_summaries.find(
      (c: any) => c.change_id === "CR-019",
    );
    Object.assign(standard, {
      state: "handoff_verified",
      state_label: "Handoff verified",
      attention: "none",
      detail: "Validation Operations intake confirmed in the source system.",
      source_available: true,
    });
    await route.fulfill({ response, json: data });
  });
  await ready(page);
  await expect(attention(page).locator('[data-case-id="CR-019"]')).toHaveCount(
    0,
  );
  await expect(page.locator('[data-verified-case="CR-019"]')).toContainText(
    "Validation Operations intake confirmed",
  );
  await page
    .getByRole("combobox", { name: "Case status", exact: true })
    .selectOption("all");
  await expect(
    attention(page).locator('[data-case-id="CR-019"]'),
  ).toContainText("Handoff verified");
  await page
    .getByRole("combobox", { name: "Case status", exact: true })
    .selectOption("handoff_verified");
  await expect(attention(page).locator("[data-case-id]")).toHaveCount(1);
  await page
    .getByRole("combobox", { name: "Case status", exact: true })
    .selectOption("attention");
  await expect(attention(page).locator('[data-case-id="CR-019"]')).toHaveCount(
    0,
  );
  await page
    .getByRole("link", { name: "All programs", exact: true })
    .first()
    .click();
  await expect(page.locator(".cp-program-row")).toHaveCount(11);
  await page
    .getByRole("combobox", { name: "Program status", exact: true })
    .selectOption("on_track");
  for (const row of await page.locator(".cp-program-row").all())
    await expect(row.locator(".cp-status")).toHaveText("On track");
  await page
    .getByRole("combobox", { name: "Program status", exact: true })
    .selectOption("all");
  await expect(page.locator(".cp-program-row")).toHaveCount(11);
  await expect(page.locator(".aw-workspace")).toHaveCount(0);
});
test("Freshness failures cannot appear as verified outcomes", async ({
  page,
}) => {
  await page.route("**/control-api/cases/CR-017", async (route) => {
    const response = await route.fetch(),
      data = await response.json();
    data.source_available = false;
    Object.assign(
      data.case_summaries.find((c: any) => c.change_id === "CR-019"),
      { state: "handoff_verified", attention: "none", source_available: false },
    );
    await route.fulfill({ response, json: data });
  });
  await ready(page);
  await expect(page.locator("[data-verified-case]")).toHaveCount(0);
  await expect(page.locator(".rb-outcome-empty")).toContainText(
    "Refresh current sources",
  );
});
test("Persona overview follows real capability navigation", async ({
  page,
}) => {
  await ready(page);
  const nav = page.getByRole("navigation", {
    name: "Control plane navigation",
  });
  await expect(nav.getByRole("link")).toHaveCount(3);
  await choose(page, "Engineering approver");
  await expect(
    page.getByRole("heading", { name: "Engineering decisions, in focus." }),
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: "Decisions", exact: true }),
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: "Operations", exact: true }),
  ).toHaveCount(0);
  await choose(page, "Program Owner");
  await expect(
    page.getByRole("heading", { name: "Protect delivery. Choose the path." }),
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: "Knowledge & Evidence" }),
  ).toHaveCount(0);
  await choose(page, "Program operator");
  await expect(
    page.getByRole("heading", { name: "Move every program forward." }),
  ).toBeVisible();
  await expect(nav.getByRole("link")).toHaveCount(7);
});
test("Connected pages remain usable at the three supported desktop sizes", async ({
  page,
}) => {
  test.setTimeout(180000);
  await page.addInitScript(() =>
    sessionStorage.setItem("stratos:demo-restart-operator", "1"),
  );
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await mkdir(shots, { recursive: true });
  await ready(page);
  await choose(page, "Program operator");
  for (const [width, height] of [
    [1920, 1080],
    [1440, 900],
    [1280, 800],
  ]) {
    await page.setViewportSize({ width, height });
    for (const [name, path] of [
      ["overview", "/control/overview"],
      ["programs", "/control/programs"],
      ["helios", "/control/programs/PRG-A17"],
      ["cr017", "/control/programs/PRG-A17/cases/CR-017"],
      ["cr019", "/control/programs/PRG-A17/cases/CR-019"],
      ["qe004", "/control/programs/PRG-A17/cases/QE-004"],
      ["dr009", "/control/programs/PRG-A17/cases/DR-009"],
      ["decisions", "/control/decisions"],
      ["scenarios", "/control/scenarios"],
      ["knowledge", "/control/knowledge"],
      ["workflows", "/control/workflows"],
      ["operations", "/control/operations"],
    ]) {
      await ready(page, path);
      await expect(
        page.getByText("This workspace could not load", { exact: true }),
      ).toHaveCount(0);
      await expect
        .poll(
          () =>
            page.evaluate(
              () => document.documentElement.scrollWidth <= innerWidth + 1,
            ),
          { message: `${name} at ${width}px should fit` },
        )
        .toBe(true);
      await page.screenshot({ path: `${shots}/${name}-${width}.png` });
      if (name !== "overview")
        await expect(page.locator(".aw-workspace")).toHaveCount(0);
      if (name === "cr019") {
        await expect(page.getByText("18/18", { exact: true })).toHaveCount(0);
      }
    }
  }
  expect(errors).toEqual([]);
});
