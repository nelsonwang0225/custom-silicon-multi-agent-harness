import { test, expect, type Page } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
const root = "/control",
  program = `${root}/programs/PRG-A17`,
  cr = `${program}/cases/CR-017`;
async function ready(page: Page) {
  await expect(
    page.getByRole("button", { name: "Refresh source records" }),
  ).toBeEnabled();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
}
async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
}
async function capture(page: Page, name: string, fullPage = false) {
  mkdirSync("../docs/phase08/workflows/regression-08-2-1/regression-shell", { recursive: true });
  await page.screenshot({
    path: `../docs/phase08/workflows/regression-08-2-1/regression-shell/${name}.png`,
    fullPage,
  });
}

test("control journey, evidence provenance, URL state and GET-only source access", async ({
  page,
  request,
}) => {
  const writes: string[] = [],
    errors: string[] = [],
    methods: { method: string; path: string }[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (r.url().includes("/api/")) {
      methods.push({ method: r.method(), path: new URL(r.url()).pathname });
      if (r.method() !== "GET") writes.push(r.url());
    }
  });
  const headers = { Authorization: "Bearer demo-portfolio-reader-local-only" };
  const before = await (
    await request.get("http://127.0.0.1:18000/api/v1/portfolio", { headers })
  ).json();
  await page.goto(root);
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "Overview", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".cp-program-row")).toHaveCount(3);
  await expect(page.locator('[data-metric="Programs"] strong')).toHaveText("3");
  await page.goto("/control/programs?scope=focus");
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "Agent workspace", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Needs attention", exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Search programs").fill("Helios");
  await expect(page.locator(".cp-program-row")).toHaveCount(1);
  await page.reload();
  await ready(page);
  await expect(page.getByLabel("Search programs")).toHaveValue("Helios");
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByLabel("Program scope").selectOption("focus");
  await page.getByLabel("Lifecycle filter").selectOption("qualification");
  await expect(page.locator(".cp-program-row")).toHaveCount(1);
  await expect(page.locator(".cp-program-row")).toContainText("Northstar");
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page
    .locator(".cp-program-row")
    .filter({ hasText: "Helios Atlas Inference" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Helios Atlas Inference", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Agent workspace", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Needs attention", exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Case filter").selectOption("connected");
  await expect(page.locator(".cp-case-list > a")).toHaveCount(0);
  await page.getByLabel("Case filter").selectOption("source");
  await page
    .locator(".cp-case-list")
    .getByRole("link", { name: /CR-017/ })
    .click();
  await expect(page).toHaveURL(cr);
  await expect(
    page.getByRole("heading", { name: "Long-context evidence change" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Evidence", exact: true }).click();
  const evidenceLink = page.getByRole("link", {
    name: "Inspect evidence RES-SHORT-B",
  });
  await evidenceLink.click();
  await expect(page.getByRole("dialog")).toContainText(
    "60 minutes observed; 480 minutes requested",
  );
  await expect(page.getByRole("dialog")).toContainText("Content version");
  await expect(page.getByRole("dialog")).toContainText("Applicability gap");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(evidenceLink).toBeFocused();
  await evidenceLink.click();
  await page.reload();
  await ready(page);
  await expect(page.getByRole("dialog")).toContainText("RES-SHORT-B");
  await page.getByRole("button", { name: "Close evidence" }).click();
  await page.getByRole("button", { name: "Options & decisions" }).click();
  await expect(page.getByText("$1,800").first()).toBeVisible();
  await expect(
    page.getByText("Eligible · meets deadline").first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Activity", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Case activity" }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("button", { name: "Options & decisions" }),
  ).toHaveAttribute("aria-current", "page");
  await page.goto(`${program}/cases/preview-DR-009`);
  await ready(page);
  await expect(page.getByText(/DR-009 source context is not available/)).toBeVisible();
  const after = await (
    await request.get("http://127.0.0.1:18000/api/v1/portfolio", { headers })
  ).json();
  expect(after).toEqual(before);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
  mkdirSync("../.cache/phase08-4c", { recursive: true });
  writeFileSync(
    "../.cache/phase08-4c/browser-read-receipt.json",
    JSON.stringify(
      {
        label: "SCRIPTED HTTP/BROWSER INTEGRATION TEST; NO AI",
        sourcePortfolioUnchanged: true,
        writes,
        errors,
        methods,
      },
      null,
      2,
    ),
  );
});

test("secondary programs, capability previews and controlled document drawer", async ({
  page,
}) => {
  await page.goto(root);
  await ready(page);
  await page
    .locator(".cp-program-row")
    .filter({ hasText: "Northstar Boreal" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Northstar Boreal", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Programs", exact: true })
    .click();
  await expect(page.locator(".cp-program-row")).toHaveCount(11);
  await page
    .locator(".cp-program-row")
    .filter({ hasText: "Vela Stream" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Vela Stream", exact: true }),
  ).toBeVisible();
  for (const [route, title] of [
    ["workflows", "Workflows & Automations"],
    ["decisions", "Decisions"],
    ["scenarios", "Scenarios"],
    ["knowledge", "Knowledge & Evidence"],
    ["operations", "Operations"],
  ]) {
    await page.goto(`${root}/${route}`);
    await ready(page);
    await expect(
      page.getByRole("heading", { name: title, exact: true }),
    ).toBeVisible();
    await expect(page.locator("main")).not.toContainText("coming soon");
  }
  await page.goto(`${root}/workflows/tapeout_readiness`);
  await ready(page);
  await expect(
    page.getByText("This workflow is not connected yet.", { exact: true }),
  ).toBeVisible();
  await page.goto(`${root}/knowledge?q=DOC-POLICY-01`);
  await ready(page);
  await page.locator(".cp-case-list a").click();
  await expect(page.getByRole("dialog")).toContainText("200,000 USD cents");
  await expect(page.getByRole("dialog")).toContainText("Document version");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("floating assistant preserves drafts, context, layout and focus; invalid scope never substitutes data", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/api/"))
      requests.push(`${r.method()} ${new URL(r.url()).pathname}`);
  });
  await page.goto(cr);
  await ready(page);
  const before = await page.locator("main").boundingBox();
  const sourceReads = [...requests];
  const launcher = page.getByRole("button", { name: "Open Stratos Concierge" });
  await expect(launcher).toHaveCount(1);
  await launcher.click();
  const chat = page.getByRole("complementary", { name: "Stratos Concierge" });
  await expect(page.getByLabel("Your draft")).toBeFocused();
  await expect(chat).toContainText("Helios Atlas Inference · CR-017");
  expect(await page.locator("main").boundingBox()).toEqual(before);
  expect((await chat.boundingBox())!.width).toBeGreaterThanOrEqual(380);
  await expect(
    page.getByRole("button", { name: "Send message unavailable" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Explain this case." }).click();
  await expect(page.getByLabel("Your draft")).toHaveValue("Explain this case.");
  await page.getByLabel("Your draft").fill("Check the CR-017 evidence scope");
  await page.keyboard.press("Enter");
  await page.keyboard.press("Escape");
  await expect(launcher).toBeFocused();
  await expect(chat).toHaveCount(0);
  await launcher.click();
  await expect(page.getByLabel("Your draft")).toHaveValue(
    "Check the CR-017 evidence scope\n",
  );
  // Nonmodal: moving focus to the main navigation is allowed.
  const portfolioLink = page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Overview", exact: true });
  await portfolioLink.focus();
  await expect(portfolioLink).toBeFocused();
  await portfolioLink.click();
  await expect(chat).toContainText("Overview");
  await expect(page.getByLabel("Your draft")).toHaveValue("");
  await expect(
    page.getByRole("button", { name: "Explain this case." }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "What needs attention?", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Minimize Stratos Concierge" })
    .click();
  await expect(launcher).toBeFocused();
  await page.getByRole("link", { name: "Inspect case CR-017" }).click();
  await launcher.click();
  await expect(page.getByLabel("Your draft")).toHaveValue(
    "Check the CR-017 evidence scope\n",
  );
  expect(requests).toEqual(sourceReads); // Drafts, navigation and suggestions start nothing.
  await page.keyboard.press("Escape");
  await noOverflow(page);
  await page.goto("/control/programs/PRG-P01/cases/CR-017");
  await ready(page);
  await expect(page.getByText("Case not found in this program.")).toBeVisible();
  await page.goto(`${cr}?tab=evidence&evidence=RES-NOT-IN-CASE`);
  await ready(page);
  await expect(page.getByRole("dialog")).toContainText(
    "not in the current case",
  );
});

test("source outage remains unavailable or stale, never simulation success", async ({
  page,
}) => {
  await page.route("**/api/v1/**", (route) => route.abort());
  await page.goto(root);
  await expect(page.getByRole("alert")).toContainText(
    "No source records were retrieved",
  );
  await expect(page.locator(".cp-program-row")).toHaveCount(0);
  await page.unroute("**/api/v1/**");
  await page.getByRole("button", { name: "Refresh source records" }).click();
  await ready(page);
  await page.route("**/api/v1/**", (route) => route.abort());
  await page.getByRole("button", { name: "Refresh source records" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Stale last-read records",
  );
  await expect(page.locator(".cp-program-row")).toHaveCount(3);
  await expect(page.locator(".cp-connection")).toContainText("Stale");
  await expect(page.locator("main")).not.toContainText("Current read");
});

test("responsive screenshot review set and keyboard reflow", async ({
  page,
}) => {
  for (const [width, height] of [
    [1440, 900],
    [1280, 800],
  ]) {
    await page.setViewportSize({ width, height });
    for (const [path, name] of [
      [root, "portfolio"],
      [program, "program"],
      [cr, "case"],
      [`${cr}?tab=evidence&evidence=RES-SHORT-B`, "evidence"],
      [`${program}/cases/preview-DR-009`, "delivery"],
    ]) {
      await page.goto(path);
      await ready(page);
      if (name === "evidence")
        await expect(page.getByRole("dialog")).toBeVisible();
      await noOverflow(page);
      if (name === "portfolio") {
        await expect(
          page.getByRole("heading", { name: "Agent workspace", exact: true }),
        ).toBeVisible();
        await expect(
          page.locator(".cp-agent-panel [data-agent-role]"),
        ).toHaveCount(5);
      }
      await capture(page, `${name}-${width}`);
      if (name === "portfolio") {
        await page.locator(".cp-agent-panel").scrollIntoViewIfNeeded();
        await capture(page, `agent-workspace-${width}`);
      }
    }
    await page.goto(root);
    await ready(page);
    await page.getByRole("button", { name: "Open Stratos Concierge" }).click();
    await noOverflow(page);
    await capture(page, `assistant-${width}`);
  }
  for (const [width, height] of [
    [1920, 1080],
    [1024, 900],
    [640, 900],
    [375, 812],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto(root);
    await ready(page);
    await noOverflow(page);
    await capture(page, `portfolio-${width}`, width === 1024);
    await page.getByRole("button", { name: "Open Stratos Concierge" }).click();
    await expect(
      page.getByRole("button", { name: "Minimize Stratos Concierge" }),
    ).toBeInViewport();
    await noOverflow(page);
    await capture(page, `assistant-${width}`);
  }
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(`${cr}?tab=evidence&evidence=RES-SHORT-B`);
  await ready(page);
  const modal = page.getByRole("dialog");
  await expect(modal).toBeVisible();
  await expect(
    modal.getByRole("button", { name: "Done", exact: true }),
  ).toBeInViewport();
  expect(
    await modal.evaluate((el) => el.scrollWidth <= el.clientWidth + 1),
  ).toBeTruthy();
  await capture(page, "evidence-375");
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(cr);
  await ready(page);
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  await noOverflow(page);
  await capture(page, "case-200-percent-zoom");
  await page.getByRole("button", { name: "Open Stratos Concierge" }).click();
  await expect(page.getByLabel("Your draft")).toBeInViewport({ ratio: 1 });
  await expect(
    page.getByRole("button", { name: "Minimize Stratos Concierge" }),
  ).toBeInViewport({ ratio: 1 });
  await noOverflow(page);
  await capture(page, "assistant-200-percent-zoom");
  await page.emulateMedia({ reducedMotion: "reduce" });
  expect(
    await page
      .locator(".cp-connection svg")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("none");
});

test("control CSS stays isolated after navigating into all five source apps", async ({
  page,
}) => {
  const styles = async () =>
    page.locator(".sidebar").evaluate((el) => ({
      background: getComputedStyle(el).backgroundColor,
      color: getComputedStyle(el).color,
      width: getComputedStyle(el).width,
    }));
  await page.goto("/engineering");
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
  const before = await styles();
  await page.goto("/control");
  await ready(page);
  await page.getByRole("link", { name: "Source apps", exact: true }).click();
  await expect(page.getByLabel("App switcher")).toBeVisible();
  for (const value of [
    "engineering",
    "validation",
    "manufacturing",
    "erp",
    "programs",
  ]) {
    await page.getByLabel("App switcher").selectOption(value);
    await expect(
      page.getByRole("button", { name: "Refresh", exact: true }),
    ).toBeEnabled();
    await expect(page.getByText(/Last API refresh/)).toBeVisible();
    await expect(page.locator(".cp-root")).toHaveCount(0);
    expect(await styles()).toEqual(before);
    await noOverflow(page);
  }
});

test("metrics use scoped current source records; agent availability stays separate from source events", async ({
  page,
  request,
}) => {
  const headers = { Authorization: "Bearer demo-portfolio-reader-local-only" };
  const portfolio = await (
    await request.get("http://127.0.0.1:18000/api/v1/portfolio", { headers })
  ).json();
  const { items: sourcePrograms } = await (
    await request.get("http://127.0.0.1:18000/api/v1/programs", { headers })
  ).json();
  const risk = new Set([
    "validation_risk",
    "at_risk",
    "manufacturing_constraint",
    "recovery_active",
    "blocked",
    "waiting_on_customer",
  ]);
  await page.goto("/control/programs");
  await ready(page);
  await expect(page.getByRole("button", { name: "Clear filters" })).toHaveCount(
    0,
  );
  for (const filter of ["focus", "all", "Vela", "none-matches"]) {
    await page
      .getByLabel("Program scope")
      .selectOption(filter === "focus" ? "focus" : "all");
    await page
      .getByLabel("Search programs")
      .fill(["focus", "all"].includes(filter) ? "" : filter);
    const programs = sourcePrograms.filter(
      (p: {
        id: string;
        name: string;
        customer_name: string;
        owner: string;
      }) =>
        filter === "focus"
          ? ["PRG-A17", "PRG-P01", "PRG-P02"].includes(p.id)
          : filter === "all" ||
            `${p.name} ${p.customer_name} ${p.id} ${p.owner}`
              .toLowerCase()
              .includes(filter.toLowerCase()),
    );
    const ids = new Set(programs.map((p: { id: string }) => p.id));
    const cases = portfolio.cases.filter(
      (c: { change: { program_id: string } }) => ids.has(c.change.program_id),
    );
    const drafts = cases.filter(
      (c: {
        change: {
          workflow_state: string;
          current_plan_id: string;
          plans: { id: string; state: string }[];
        };
      }) =>
        !["closed", "superseded"].includes(c.change.workflow_state) &&
        c.change.plans.some(
          (p) => p.id === c.change.current_plan_id && p.state === "draft",
        ),
    );
    for (const [label, value] of [
      ["Programs", programs.length],
      ["Source plan drafts", drafts.length],
      [
        "At risk",
        programs.filter((p: { health: string }) => risk.has(p.health)).length,
      ],
    ]) {
      await expect(page.locator(`[data-metric="${label}"] strong`)).toHaveText(
        String(value),
      );
    }
    await expect(page.locator(".cp-program-row")).toHaveCount(programs.length);
  }
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByText("Metric definitions", { exact: true }).click();
  await expect(page.locator(".cp-metric-definitions")).toContainText(
    "A source plan does not establish a reviewable host proposal",
  );
  await expect(page.locator(".cp-metric-definitions")).toContainText(
    "Illustrative entries are excluded",
  );
  await page.getByText("Metric definitions", { exact: true }).click();
  const activity = page.locator(".cp-agent-panel");
  await expect(activity).toContainText("Live activity isn’t connected");
  await expect(activity).not.toContainText(
    /Running|No investigations running|Recorded result|Succeeded/,
  );
  await expect(activity).toContainText("Agent roles · Preview");
  await expect(activity.locator("[data-agent-role]")).toHaveCount(5);
  expect(
    await activity
      .locator("[data-agent-role]")
      .evaluateAll((els) => els.map((e) => e.getAttribute("data-agent-role"))),
  ).toEqual([
    "coordinator",
    "change_impact",
    "validation_evidence",
    "program_commercial",
    "manufacturing",
  ]);
  await activity
    .getByRole("button", {
      name: "View Validation & Evidence Specialist details",
    })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "No task or result is implied",
  );
  await page.getByRole("button", { name: "Close agent details" }).click();
  await page.getByText("Recent source activity", { exact: true }).click();
  await expect(
    page
      .locator(".cp-secondary-content")
      .filter({ hasText: "Recent source activity" }),
  ).toContainText("Recorded source events");
  await expect(activity.locator(".cp-activity")).toHaveCount(0);
  await page
    .locator(".cp-program-row")
    .filter({ hasText: "Helios Atlas Inference" })
    .click();
  await expect(activity).toContainText(
    "Live activity isn’t connected for Helios Atlas Inference",
  );
  await activity.scrollIntoViewIfNeeded();
  await expect(activity).toBeInViewport();
});

test("floating chat yields to page focus and evidence, reflows with a short mobile viewport", async ({
  page,
}) => {
  await page.goto(`${cr}?tab=evidence`);
  await ready(page);
  const launcher = page.getByRole("button", { name: "Open Stratos Concierge" });
  const chat = page.getByRole("complementary", { name: "Stratos Concierge" });
  await launcher.click();
  // Focus a real source control behind the floating window. Chat yields without stealing focus.
  const evidence = page.getByRole("link", {
    name: "Inspect evidence RES-SHORT-B",
  });
  await evidence.scrollIntoViewIfNeeded();
  await evidence.focus();
  await expect(evidence).toBeFocused();
  await expect(chat).toHaveCount(0);
  await launcher.click();
  // An active evidence dialog owns the native top layer, including direct-linked dialogs.
  await page.evaluate((path) => {
    window.history.pushState({}, "", path);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, `${cr}?tab=evidence&evidence=RES-SHORT-B`);
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(chat).toBeHidden();
  await expect(
    page.getByRole("button", { name: "Close evidence" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(chat).toBeVisible();
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(root);
  await ready(page);
  await launcher.click();
  await page
    .getByLabel("Your draft")
    .fill("Draft survives a keyboard-sized viewport");
  await page.setViewportSize({ width: 375, height: 380 });
  await expect(page.getByLabel("Your draft")).toBeInViewport({ ratio: 1 });
  await expect(
    page.getByRole("button", { name: "Minimize Stratos Concierge" }),
  ).toBeInViewport({ ratio: 1 });
  await expect(
    page.getByRole("button", { name: "Send message unavailable" }),
  ).toBeInViewport({ ratio: 1 });
  await noOverflow(page);
  await capture(page, "assistant-short-375");
  await page.setViewportSize({ width: 375, height: 812 });
  await expect(page.getByLabel("Your draft")).toHaveValue(
    "Draft survives a keyboard-sized viewport",
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  expect(
    await chat.evaluate((el) => getComputedStyle(el).transitionDuration),
  ).toBe("0s");
  await page.keyboard.press("Escape");
  await expect(launcher).toBeFocused();
});

test("launcher makes room for a keyboard-focused page control", async ({
  page,
}) => {
  await page.goto(root);
  await ready(page);
  const launcher = page.getByRole("button", { name: "Open Stratos Concierge" });
  const control = page.getByRole("link", {
    name: "View programs",
    exact: true,
  });
  // Position the real navigation link at the collision boundary without changing its behavior.
  await control.evaluate((el) => {
    Object.assign((el as HTMLElement).style, {
      position: "fixed",
      right: "30px",
      bottom: "30px",
      zIndex: "1",
    });
  });
  await control.focus();
  await expect(control).toBeFocused();
  await expect
    .poll(async () => {
      const a = await page.locator(".cp-concierge-dock").boundingBox(),
        b = await control.boundingBox();
      return a!.y + a!.height < b!.y;
    })
    .toBeTruthy();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(`${root}/programs`);
});
