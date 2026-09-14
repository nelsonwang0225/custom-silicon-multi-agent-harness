import { test, expect, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import {
  healthMix,
  overviewSummary,
  searchIndex,
  matchSearch,
  sourceAlerts,
} from "../src/control/presentation-model";
import type { Snapshot } from "../src/control/data";
const home = "/control/overview";
const sourceHeaders = {
  Authorization: "Bearer demo-portfolio-reader-local-only",
};
async function ready(page: Page, path = home) {
  await page.goto(path);
  await expect(page.locator(".cp-connection")).toContainText("Current read");
}
async function search(page: Page, q: string) {
  await page.getByLabel("Search Stratos", { exact: true }).fill(q);
  return page.getByRole("dialog", { name: "Search results" });
}
async function capture(page: Page, name: string) {
  mkdirSync("../docs/phase08/workflows/regression-08-2-1/regression-shell", {
    recursive: true,
  });
  await page.screenshot({
    path: `../docs/phase08/workflows/regression-08-2-1/regression-shell/${name}.png`,
  });
}

test("Overview aliases, explicit scope and short tiles replace filters and metric strip", async ({
  page,
}) => {
  for (const path of [
    "/overview",
    "/portfolio",
    "/control/portfolio",
    "/control",
  ]) {
    await ready(page, path);
    await expect(page).toHaveURL(home);
    await expect(page).toHaveTitle("Overview · Stratos Silicon");
  }
  await ready(page, home + "?q=nonexistent&scope=all&stage=closed");
  await expect(
    page.getByRole("heading", { name: "Overview", exact: true }),
  ).toBeVisible();
  await expect(
    page.locator("main input, main select, .cp-metrics"),
  ).toHaveCount(0);
  await expect(page.locator(".cp-program-row")).toHaveCount(3);
  await expect(
    page.locator(".cp-program-row p,.cp-role-tiles small"),
  ).toHaveCount(0);
  await expect(page.locator('[data-metric="Programs"] strong')).toHaveText("3");
  await expect(page.locator('[data-metric="At risk"] strong')).toHaveText("1");
  await expect(
    page.getByRole("img", { name: /on track or completed/ }),
  ).toHaveAccessibleName(
    /2 on track or completed, 1 at risk, 0 unknown; 3 programs/,
  );
  await page.getByRole("link", { name: "View programs", exact: true }).click();
  await expect(page.getByLabel("Lifecycle filter")).toBeVisible();
  await expect(page.locator(".cp-program-row")).toHaveCount(11);
});

test("search groups metadata, matches IDs and titles, opens scoped evidence and agent dialogs", async ({
  page,
}) => {
  await ready(page);
  let panel = await search(page, "hELios");
  await expect(
    panel.getByRole("heading", { name: "Programs & customers", exact: true }),
  ).toBeVisible();
  await expect(
    panel.getByRole("heading", { name: "Cases", exact: true }),
  ).toBeVisible();
  await expect(panel).toContainText("Ask Stratos Concierge about");
  await search(page, "res-short-b");
  await panel.getByRole("button", { name: /^RES-SHORT-B/ }).click();
  await expect(page.getByRole("dialog")).toHaveAccessibleName("RES-SHORT-B");
  await expect(page.getByRole("dialog")).toContainText(
    "Applicability to CR-017",
  );
  await page.keyboard.press("Escape");
  // Closing evidence updates the route; wait before entering a new search.
  await expect(page.getByRole("dialog", { name: "RES-SHORT-B" })).toHaveCount(
    0,
  );
  await expect(page).toHaveURL(/\?tab=evidence$/);
  await search(page, "manufacturing specialist");
  await panel
    .getByRole("button", { name: /^Manufacturing Specialist/ })
    .click();
  await expect(page.getByRole("dialog")).toHaveAccessibleName(
    "Manufacturing Specialist",
  );
  await expect(page.getByRole("dialog")).toContainText("Definition only");
  await page.keyboard.press("Escape");
  await search(page, "requirement change");
  await expect(
    panel.getByRole("button", { name: /Requirement Change Analysis/ }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByLabel("Search Stratos", { exact: true }),
  ).toBeFocused();
  await expect(panel).toHaveCount(0);
  await page.keyboard.press("Control+k");
  await expect(panel).toBeVisible();
  await page.keyboard.press("ArrowDown");
  await expect(
    panel.getByRole("button", { name: "Close search" }),
  ).toBeFocused();
  await page.keyboard.press("ArrowDown");
  await expect(
    panel.getByRole("button", { name: /Requirement Change Analysis/ }),
  ).toBeFocused();
});

test("Ask Concierge is always available and appends queries without sending or replacing drafts", async ({
  page,
}) => {
  const writes: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/api/") && r.method() !== "GET") writes.push(r.url());
  });
  await ready(page);
  await page.getByLabel("Search Stratos", { exact: true }).focus();
  await page
    .getByRole("dialog", { name: "Search results" })
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await page.getByLabel("Your draft").fill("Preserve my existing draft");
  for (const q of ["Helios", "no-matching-record-xyz"]) {
    const panel = await search(page, q);
    if (q.startsWith("no-"))
      await expect(panel).toContainText("No matches in the available metadata");
    await panel
      .getByRole("button", { name: `Ask Stratos Concierge about “${q}”` })
      .click();
    await expect(page.getByLabel("Your draft")).toHaveValue(
      new RegExp(`Preserve my existing draft[\\s\\S]*${q}`),
    );
    await expect(page.locator(".cp-chat-context")).toContainText(
      "Added from global search · Overview",
    );
  }
  await expect(
    page.getByRole("button", { name: "Send message unavailable" }),
  ).toBeDisabled();
  expect(writes).toEqual([]);
});

test("demo selection clears context without changing read-only HTTP authority", async ({
  page,
}) => {
  const roles: string[] = [],
    writes: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/api/")) {
      roles.push(r.headers().authorization);
      if (r.method() !== "GET") writes.push(r.method());
    }
  });
  await ready(page);
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await page.getByLabel("Your draft").fill("Old identity draft");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  const modal = page.getByRole("dialog", { name: "Demo access" });
  await expect(modal).toContainText("not production authentication");
  await expect(
    page.getByRole("complementary", { name: "Stratos Concierge" }),
  ).toBeHidden();
  await modal.getByRole("button", { name: /Engineering approver/ }).click();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  await expect(page.getByLabel("Search Stratos", { exact: true })).toHaveValue(
    "",
  );
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await expect(page.getByLabel("Your draft")).toHaveValue("");
  await page.getByRole("button", { name: "Demo profile", exact: true }).click();
  const profile = page.getByRole("dialog", { name: "Demo profile" });
  await expect(profile).toContainText("Demo identity · engineer role");
  await expect(profile).toContainText(
    "Customer acceptance and held-material release remain separate.",
  );
  await profile.getByRole("button", { name: "Switch profile" }).click();
  await page
    .getByRole("dialog", { name: "Demo access" })
    .getByRole("button", { name: /Read-only viewer/ })
    .click();
  await page.getByRole("button", { name: "Demo profile", exact: true }).click();
  await page.getByRole("button", { name: "Exit demo", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Log in", exact: true }),
  ).toBeVisible();
  expect(new Set(roles)).toEqual(
    new Set(["Bearer demo-portfolio-reader-local-only"]),
  );
  expect(writes).toEqual([]);
});

test("source alerts deduplicate and marking read cannot mutate business work", async ({
  page,
  request,
}) => {
  const before = await (
    await request.get("http://127.0.0.1:18000/api/v1/portfolio", {
      headers: sourceHeaders,
    })
  ).json();
  await ready(page);
  await page.getByRole("button", { name: /^Alerts, / }).click();
  const panel = page.getByRole("dialog", { name: "Source alerts" });
  const initial = await panel.locator("article").count();
  expect(initial).toBeGreaterThan(0);
  const keys = await panel
    .locator("article")
    .evaluateAll((els) => els.map((el) => el.getAttribute("data-alert-id")));
  expect(new Set(keys).size).toBe(initial);
  await expect(panel).toContainText("Source updated");
  await expect(panel).toContainText("Source plan awaiting review");
  await expect(panel).toContainText("Scheduled · Planner link missing");
  await panel
    .getByRole("button", { name: "Mark read", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("button", {
      name: `Alerts, ${initial - 1} unread`,
      exact: true,
    }),
  ).toBeVisible();
  await panel
    .getByRole("button", { name: "Mark all read", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Alerts, 0 unread", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Alerts, 0 unread", exact: true }),
  ).toBeFocused();
  const after = await (
    await request.get("http://127.0.0.1:18000/api/v1/portfolio", {
      headers: sourceHeaders,
    })
  ).json();
  expect(after).toEqual(before);
});

test("unavailable sources show limited search coverage and no invented alerts", async ({
  page,
}) => {
  await page.route("**/api/v1/**", (route) => route.abort());
  await page.goto(home);
  await expect(
    page.getByRole("button", { name: "Refresh source records" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Alerts unavailable" }).click();
  await expect(
    page.getByRole("dialog", { name: "Source alerts" }),
  ).toContainText("Alerts unavailable");
  const panel = await search(page, "RES-SHORT-B");
  await expect(panel).toContainText("Definitions only");
  await expect(panel).toContainText("No matches in the available metadata");
  await expect(
    panel.getByRole("button", { name: /Ask Stratos Concierge about/ }),
  ).toBeVisible();
});

test("adapters enforce scope, unknown health, current reviews and closed-alert exclusion", () => {
  const programs = [
    {
      id: "PRG-A17",
      customer_id: "A",
      name: "Helios Atlas Inference",
      customer_name: "Helios AI",
      health: "on_track",
    },
    {
      id: "PRG-P01",
      customer_id: "B",
      name: "Northstar",
      health: "future_state",
    },
    { id: "PRG-P02", customer_id: "C", name: "Vela", health: "at_risk" },
  ];
  const c = {
    change: {
      id: "CR-017",
      program_id: "PRG-A17",
      customer_id: "A",
      content_version: 2,
      title: "Evidence change",
      workflow_state: "pending_impact_assessment",
      current_plan_id: "PLAN",
      updated_at: "2026-11-16T09:00:00Z",
      plans: [
        {
          id: "PLAN",
          program_id: "PRG-A17",
          customer_id: "A",
          state: "draft",
          content_version: 1,
        },
      ],
    },
    coverage: { coverage_satisfied: false, items: [] },
  };
  const data = {
    programs,
    cases: [
      c,
      {
        ...c,
        change: { ...c.change, id: "PRIVATE", customer_id: "elsewhere" },
      },
    ],
    documents: [],
    milestones: [],
  } as unknown as Snapshot;
  const summary = overviewSummary(data);
  expect(summary.programs).toHaveLength(3);
  expect(summary.cases).toHaveLength(1);
  expect(summary.mix).toEqual({ onTrack: 1, atRisk: 1, unknown: 1 });
  expect(summary.metrics.find((m) => m.label === "At risk")?.value).toBeNull();
  expect(summary.metrics.find((m) => m.label === "Needs review")?.value).toBe(
    1,
  );
  const index = searchIndex(data);
  expect(
    matchSearch(index, "helios ai").some((i) => i.group === "Cases"),
  ).toBeTruthy();
  expect(matchSearch(index, "PRIVATE")).toHaveLength(0);
  expect(
    matchSearch(index, "PLAN").some((i) => i.title === "PLAN"),
  ).toBeTruthy();
  expect(sourceAlerts(data)).toHaveLength(1);
  expect(healthMix([])).toEqual({ onTrack: 0, atRisk: 0, unknown: 0 });
  data.cases[0].change.workflow_state = "closed";
  expect(sourceAlerts(data)).toHaveLength(0);
  expect(
    overviewSummary(data).metrics.find((m) => m.label === "Needs review")
      ?.value,
  ).toBe(0);
});

test("gradient Overview, utilities and concierge fit desktop and narrow layouts", async ({
  page,
}) => {
  for (const [width, height] of [
    [1440, 900],
    [1280, 800],
    [375, 812],
  ]) {
    await page.setViewportSize({ width, height });
    await ready(page);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await capture(page, `overview-${width}`);
    await search(page, "Helios");
    await expect(
      page.getByRole("button", { name: /Ask Stratos Concierge about/ }),
    ).toBeInViewport();
    await capture(page, `search-${width}`);
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: /^Alerts, / }).click();
    await capture(page, `alerts-${width}`);
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: "Log in", exact: true }).click();
    await expect(
      page.getByRole("dialog", { name: "Demo access" }),
    ).toBeVisible();
    await capture(page, `demo-access-${width}`);
    await page.keyboard.press("Escape");
    await page
      .getByRole("button", { name: "Open Stratos Concierge", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Minimize Stratos Concierge" }),
    ).toBeInViewport();
    await expect(page.getByLabel("Your draft")).toBeInViewport();
    await capture(page, `concierge-${width}`);
  }
});
