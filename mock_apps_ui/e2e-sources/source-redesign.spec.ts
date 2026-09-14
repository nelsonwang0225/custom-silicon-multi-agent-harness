import {
  test,
  expect,
  type APIRequestContext,
  type Page,
  type TestInfo,
} from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import type { Schema } from "../src/api";
import type { HostSchema } from "../src/control/host";

const screenshots = fileURLToPath(
  new URL(
    "../../docs/screenshots/source-redesign/responsive/",
    import.meta.url,
  ),
);
const headers = { Authorization: "Bearer demo-portfolio-reader-local-only" };
const diagnostics = new WeakMap<
  Page,
  { pageErrors: string[]; consoleErrors: string[]; writes: string[] }
>();
const apps = {
  engineering: "Stratos PLM",
  validation: "Stratos TestOps",
  manufacturing: "Stratos MES",
  erp: "Stratos ERP",
  programs: "Stratos ProgramOps",
} as const;

async function source<T>(request: APIRequestContext, path: string): Promise<T> {
  const response = await request.get("/api/v1" + path, { headers });
  expect(
    response.ok(),
    `Source read failed: ${path} (${response.status()})`,
  ).toBeTruthy();
  return response.json();
}
async function ready(page: Page) {
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText(/Last API refresh/)).toBeVisible();
  await expect(
    page.getByText("Refreshing from APIs…", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page
      .locator("main .empty")
      .filter({ hasText: /^(Loading|Reading|Retrieving)/ }),
  ).toHaveCount(0);
}
async function layout(page: Page) {
  await expect
    .poll(() =>
      page.evaluate(() => ({
        document: document.documentElement.scrollWidth <= window.innerWidth + 1,
        body: document.body.scrollWidth <= window.innerWidth + 1,
      })),
    )
    .toEqual({ document: true, body: true });
  await expect(page.locator("main .page-heading h1")).toHaveCount(1);
}
async function capture(page: Page, info: TestInfo, route: string) {
  await layout(page);
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  const file = `${
    route
      .replace(/^\//, "")
      .replace(/[^a-z0-9]+/gi, "-")
      .toLowerCase() || "launcher"
  }-${page.viewportSize()!.width}.png`;
  await page.screenshot({
    path: `${screenshots}/${file}`,
    animations: "disabled",
  });
  await info.attach(file, {
    path: `${screenshots}/${file}`,
    contentType: "image/png",
  });
}
async function visit(
  page: Page,
  info: TestInfo,
  route: string,
  heading: string | RegExp,
  app: keyof typeof apps,
) {
  await page.goto(route);
  await ready(page);
  await expect(
    page.locator("main").getByRole("heading", {
      name: heading,
      exact: typeof heading === "string",
      level: 1,
    }),
  ).toBeVisible();
  await expect(page.locator(".topbar .app-title")).toContainText(apps[app]);
  await expect(page).toHaveTitle(new RegExp(apps[app]));
  await expect(page.getByLabel("App switcher")).toHaveValue(app);
  await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
  await capture(page, info, route);
}

test.beforeEach(async ({ context, page }) => {
  await mkdir(screenshots, { recursive: true });
  await context.addInitScript(() => {
    class NoSpeech {
      start() {
        throw new Error("Real speech is disabled in source UI tests");
      }
      stop() {}
      abort() {}
    }
    Object.assign(window, {
      SpeechRecognition: NoSpeech,
      webkitSpeechRecognition: NoSpeech,
    });
  });
  const observed = {
    pageErrors: [] as string[],
    consoleErrors: [] as string[],
    writes: [] as string[],
  };
  diagnostics.set(page, observed);
  page.on("pageerror", (error) => observed.pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    // Missing QE-011 and an unpublished lab completion are explicit source states.
    const expectedMissing =
      /\/quality-exceptions\/QE-011\/(context|records)|\/validation\/jobs\/[^/]+\/completion/.test(
        message.location().url,
      ) && /404/.test(message.text());
    if (!expectedMissing) observed.consoleErrors.push(message.text());
  });
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (
      (path.startsWith("/api/v1/") || path.startsWith("/control-api/")) &&
      !["GET", "HEAD", "OPTIONS"].includes(request.method())
    ) {
      observed.writes.push(`${request.method()} ${path}`);
    }
  });
});

test.afterEach(async ({ page }) => {
  const observed = diagnostics.get(page)!;
  expect(observed.pageErrors, "Uncaught browser errors").toEqual([]);
  expect(observed.consoleErrors, "Unexpected console errors").toEqual([]);
  expect(
    observed.writes,
    "Source inspection must not mutate business or host state",
  ).toEqual([]);
});

test("PLM exposes controlled changes, exact configuration and document navigation", async ({
  page,
  request,
}, info) => {
  const portfolio = await source<Schema["Portfolio"]>(request, "/portfolio");
  const cr = portfolio.cases.find((c) => c.change.id === "CR-017")!;
  const standard = portfolio.cases.find((c) => c.change.id === "CR-019")!;
  expect(cr).toBeDefined();
  expect(standard).toBeDefined();
  await visit(page, info, "/engineering", "Change requests", "engineering");
  await expect(
    page.getByRole("complementary", { name: "Product structure", exact: true }),
  ).toContainText("CFG-B-01");
  await page.getByLabel("Search changes").fill("CR-017");
  await expect(
    page.locator(".plm-worklist").getByRole("link", { name: /CR-017/ }),
  ).toHaveCount(1);
  await page
    .locator(".plm-worklist")
    .getByRole("link", { name: /CR-017/ })
    .click();
  await ready(page);
  await expect(page).toHaveURL(/\/engineering\/changes\/CR-017$/);
  await visit(
    page,
    info,
    "/engineering/changes/CR-017",
    cr.change.title,
    "engineering",
  );
  await expect(
    page.getByLabel("Engineering record relationships"),
  ).toContainText("CR-017");
  await expect(
    page.getByLabel("Engineering record relationships"),
  ).toContainText("CFG-B-01");
  await expect(page.locator("#plm-requirements")).toContainText(cr.baseline.id);
  await expect(page.locator("#plm-requirements")).toContainText(cr.target.id);
  await page
    .getByRole("navigation", { name: "Engineering object sections" })
    .getByRole("link", { name: "Configuration", exact: true })
    .click();
  await expect(page).toHaveURL(/#plm-configuration$/);
  await expect(page.locator("#plm-configuration")).toBeInViewport();
  await visit(
    page,
    info,
    "/engineering/changes/CR-019",
    standard.change.title,
    "engineering",
  );
  await expect(page.locator("#plm-configuration")).toContainText(
    standard.config.id,
  );
  await expect(page.locator("#plm-requirements")).toContainText(
    standard.target.workload_profile_id,
  );
  await visit(
    page,
    info,
    "/engineering/documents",
    "Controlled documents",
    "engineering",
  );
  const document =
    portfolio.documents.find((d) => d.id === "DOC-STD-PROC-01") ||
    portfolio.documents[0];
  expect(document).toBeDefined();
  await page.getByLabel("Search documents").fill(document.id);
  await page.getByRole("link", { name: document.id, exact: true }).click();
  await ready(page);
  await expect(
    page.getByRole("heading", { name: document.id, exact: true, level: 1 }),
  ).toBeVisible();
  await expect(page.locator(".markdown")).not.toBeEmpty();
  await capture(page, info, `/engineering/documents/${document.id}`);
});

test("TestOps preserves scheduling, execution, results and intake distinctions", async ({
  page,
  request,
}, info) => {
  const portfolio = await source<Schema["Portfolio"]>(request, "/portfolio");
  const jobs = portfolio.cases.flatMap((c) => c.jobs);
  const pending = jobs.filter((j) => !j.completion);
  const completed = new Set([
    ...portfolio.history.map((j) => j.id),
    ...jobs.filter((j) => j.completion).map((j) => j.id),
  ]).size;
  await visit(page, info, "/validation", "Lab overview", "validation");
  const summary = page.getByLabel("Lab operational summary");
  await expect(
    summary.getByRole("link", { name: /^Scheduled / }).locator("strong"),
  ).toHaveText(String(pending.length));
  await expect(
    summary
      .getByRole("link", { name: /^Completed executions / })
      .locator("strong"),
  ).toHaveText(String(completed));
  await expect(
    page.getByRole("heading", { name: "Evidence & coverage", exact: true }),
  ).toBeVisible();
  for (const [route, heading] of [
    ["/validation/jobs", "Jobs queue"],
    ["/validation/samples", "Sample inventory"],
    ["/validation/schedule", "Lab schedule"],
    ["/validation/history", "Lab execution history"],
  ]) {
    await visit(page, info, route, heading, "validation");
  }
  const job = jobs[0];
  if (job) {
    await visit(
      page,
      info,
      `/validation/jobs/${job.id}`,
      "Validation job",
      "validation",
    );
    await expect(page.getByLabel("Validation lifecycle")).toContainText(
      "Reservation confirmed",
    );
    await expect(page.getByLabel("Validation lifecycle")).toContainText(
      "Customer acceptance",
    );
    await expect(page.locator(".testops-object-summary")).toContainText(
      job.sample_id,
    );
    await expect(page.locator(".testops-object-summary")).toContainText(
      job.procedure_id,
    );
    if (!job.completion)
      await expect(page.getByLabel("Validation lifecycle")).toContainText(
        "Not available",
      );
  } else {
    info.annotations.push({
      type: "coverage",
      description:
        "No scheduled JobView exists in this source session; inspected immutable execution history without creating business state.",
    });
    const historical = portfolio.history[0];
    expect(
      historical,
      "A source execution record is required for the history detail check",
    ).toBeDefined();
    await visit(
      page,
      info,
      `/validation/history/${historical.id}`,
      historical.id,
      "validation",
    );
    await expect(page.getByLabel("Validation lifecycle")).toContainText(
      "Completed",
    );
    await expect(page.locator("main")).toContainText(historical.sample_id);
  }
  const coverage = await source<Schema["Coverage"]>(
    request,
    "/validation/coverage?change_id=CR-017",
  );
  const evidence = coverage.items.find((i) => i.result.id === "RES-SHORT-B")!;
  expect(evidence).toBeDefined();
  expect(evidence.satisfies).toBe(false);
  await visit(
    page,
    info,
    `/validation/results/${evidence.result.id}`,
    evidence.result.id,
    "validation",
  );
  await expect(page.locator("main")).toContainText(
    "does not satisfy the requested evidence obligation",
  );
  await expect(page.locator(".testops-object-summary")).toContainText(
    `${evidence.result.actual_suite_minutes} min`,
  );
  await expect(page.locator("main")).toContainText(
    "Historical criteria evaluation",
  );
  await visit(
    page,
    info,
    "/validation/intakes",
    "Validation Operations intake",
    "validation",
  );
  const intakes = await source<Schema["IntakeList"]>(
    request,
    "/validation/changes/CR-019/intakes",
  );
  if (intakes.items.length) {
    const intake = intakes.items[0];
    await page.getByRole("link", { name: intake.id, exact: true }).click();
    await ready(page);
    await expect(page.locator("main")).toContainText(
      intake.downstream_queue_id,
    );
    await expect(page.locator("main")).toContainText(
      "No lab job or reservation created",
    );
    await page.getByText("Exact received package", { exact: true }).click();
    await expect(page.locator("main pre")).toContainText(
      intake.package.package_id,
    );
    await capture(page, info, `/validation/intakes/${intake.id}`);
  } else {
    await expect(
      page.getByText("No standard packages received.", { exact: true }),
    ).toBeVisible();
  }
});

test("MES keeps lot holds and yield facts distinct from quality hypotheses", async ({
  page,
  request,
}, info) => {
  await visit(page, info, "/manufacturing", "Unit inventory", "manufacturing");
  await visit(
    page,
    info,
    "/manufacturing/lots",
    "Source lots",
    "manufacturing",
  );
  await visit(
    page,
    info,
    "/manufacturing/lots/LOT-B-204",
    "LOT-B-204",
    "manufacturing",
  );
  await visit(
    page,
    info,
    "/manufacturing/quality/QE-004",
    "QE-004 · Source records",
    "manufacturing",
  );
  const quality = page.getByLabel("Quality exception and affected lot");
  await expect(quality).toContainText("LOT-B-204");
  await expect(quality.getByText("HOLD", { exact: true })).toBeVisible();
  const yields = page.getByLabel("First-pass yield comparison");
  await expect(yields.getByText("80%", { exact: true })).toBeVisible();
  await expect(yields.getByText("96%", { exact: true })).toBeVisible();
  await expect(yields).toContainText("-16");
  await expect(
    page.getByRole("heading", { name: "Signals & hypotheses", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".mes-root-cause")).toContainText(
    "Site-level counts do not establish a physical cause.",
  );
  const event = await request.get(
    "/api/v1/manufacturing/quality-exceptions/QE-011/context",
    { headers },
  );
  expect(
    [200, 404],
    "QE-011 must be present or explicitly unavailable",
  ).toContain(event.status());
  // Same-component navigation checks that QE-004 observations never leak into QE-011.
  await page
    .locator(".sidebar nav")
    .getByRole("link", { name: "QE-011 source event", exact: true })
    .click();
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "QE-011 · Source records", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".quality-source-page")).not.toContainText(
    "LOT-B-204",
  );
  if (event.ok()) {
    const actual = (await event.json()) as HostSchema["QualityContext"];
    expect(actual.exception_id).toBe("QE-011");
    await expect(
      page.getByLabel("Quality exception and affected lot"),
    ).toContainText(actual.exception.lot_id);
    await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
  } else {
    await expect(page.getByRole("alert")).toHaveText(
      "Current quality source unavailable.",
    );
    await expect(
      page.getByLabel("Quality exception and affected lot"),
    ).toHaveCount(0);
  }
  await capture(page, info, "/manufacturing/quality/QE-011");
  await visit(
    page,
    info,
    "/manufacturing/delivery/DR-009",
    "DR-009 · Source records",
    "manufacturing",
  );
  await expect(page.locator("main")).toContainText("LOT-B-204");
});

test("ERP preserves the order object and reconciled delivery supply accounting", async ({
  page,
  request,
}, info) => {
  const order = await source<Schema["Order"]>(request, "/erp/orders/ORD-1204");
  await visit(page, info, "/erp", "Customer orders", "erp");
  await visit(page, info, "/erp/orders/ORD-1204", "ORD-1204", "erp");
  await expect(page.getByLabel("Customer order header")).toContainText(
    order.quantity.toLocaleString(),
  );
  await expect(
    page.getByRole("heading", { name: "Line items", exact: true }),
  ).toBeVisible();
  await visit(
    page,
    info,
    "/erp/delivery/DR-009",
    "DR-009 · Source records",
    "erp",
  );
  const accounting = page.getByLabel("Supply and demand accounting");
  for (const [label, amount] of [
    ["Physical", "1,000"],
    ["Held", "250"],
    ["Allocated", "150"],
    ["Eligible", "600"],
    ["Demand", "800"],
    ["Gap", "200"],
  ]) {
    const fact = accounting
      .locator("div")
      .filter({
        has: page.locator("span").filter({ hasText: new RegExp(`^${label}$`) }),
      })
      .filter({
        has: page
          .locator("strong")
          .filter({ hasText: new RegExp(`^${amount}$`) }),
      });
    await expect(fact.last()).toBeVisible();
  }
  await page
    .getByRole("navigation", { name: "Delivery order sections" })
    .getByRole("link", { name: "Supply", exact: true })
    .click();
  await expect(page).toHaveURL(/#delivery-supply$/);
  await expect(page.locator("#delivery-supply")).toBeInViewport();
  await visit(
    page,
    info,
    "/erp/rates",
    "Approved validation cost rates",
    "erp",
  );
});

test("ProgramOps preserves milestone baselines, forecasts and dependency navigation", async ({
  page,
  request,
}, info) => {
  const portfolio = await source<Schema["Portfolio"]>(request, "/portfolio");
  const milestone = portfolio.milestones.find((m) => m.id === "MS-ACCEPT-01")!;
  expect(milestone).toBeDefined();
  await visit(page, info, "/programs", "Program workspaces", "programs");
  await page.getByLabel("Search programs").fill("PRG-A17");
  await expect(
    page.getByRole("link", { name: "Open program", exact: true }),
  ).toHaveCount(1);
  await page.getByRole("link", { name: "Open program", exact: true }).click();
  await ready(page);
  await expect(page).toHaveURL(/\/programs\/PRG-A17$/);
  await visit(
    page,
    info,
    "/programs/PRG-A17",
    "ACCELERATOR-X program",
    "programs",
  );
  await expect(
    page.getByRole("heading", { name: "Milestone register", exact: true }),
  ).toBeVisible();
  await expect(
    page
      .locator("#program-milestones")
      .getByRole("columnheader", { name: "Baseline", exact: true }),
  ).toBeVisible();
  await expect(
    page
      .locator("#program-milestones")
      .getByRole("columnheader", { name: "Internal forecast", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Program sections" })
    .getByRole("link", { name: "Dependencies & actions", exact: true })
    .click();
  await expect(page).toHaveURL(/#program-dependencies$/);
  await expect(page.locator("#program-dependencies")).toBeInViewport();
  await visit(
    page,
    info,
    `/programs/PRG-A17/milestones/${milestone.id}`,
    "ACCELERATOR-X program",
    "programs",
  );
  await expect(page.locator("#program-milestones")).toContainText(milestone.id);
  await visit(
    page,
    info,
    "/programs/quality/QE-004",
    "QE-004 · Source records",
    "programs",
  );
  await expect(
    page.getByRole("heading", {
      name: "QE-004 recovery task record",
      exact: true,
    }),
  ).toBeVisible();
  await visit(
    page,
    info,
    "/programs/delivery/DR-009",
    "DR-009 · Source records",
    "programs",
  );
});

test("source navigation, refresh and unavailable records remain accessible and read-only", async ({
  page,
}, info) => {
  await page.goto("/");
  await ready(page);
  await expect(
    page.getByRole("link", { name: "Open application", exact: true }),
  ).toHaveCount(5);
  for (const [app, name] of Object.entries(apps)) {
    await expect(
      page.getByRole("heading", { name, exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: `Open ${name} in new tab`, exact: true }),
    ).toHaveAttribute("target", "_blank");
    await expect(
      page.getByLabel("App switcher").locator(`option[value="${app}"]`),
    ).toHaveText(name);
  }
  await page.getByLabel("App switcher").selectOption("validation");
  await ready(page);
  await expect(page).toHaveURL(/\/validation$/);
  await page
    .locator(".sidebar nav")
    .getByRole("link", { name: "Sample inventory", exact: true })
    .click();
  await ready(page);
  await expect(
    page.getByRole("heading", {
      name: "Sample inventory",
      level: 1,
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page
      .locator(".sidebar nav")
      .getByRole("link", { name: "Sample inventory", exact: true }),
  ).toHaveAttribute("aria-current", "page");
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await ready(page);
  await page.reload();
  await ready(page);
  await expect(page.getByLabel("Simulated persona")).toHaveValue("reader");
  // A deterministic failed source read verifies recovery without touching the server.
  await page.route("**/api/v1/erp/delivery-requests/DR-009/context", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: "null",
    }),
  );
  await page.goto("/erp/delivery/DR-009");
  await ready(page);
  await expect(page.getByRole("alert")).toHaveText(
    "Current delivery source unavailable.",
  );
  await expect(
    page.getByRole("button", { name: "Refresh source records", exact: true }),
  ).toBeEnabled();
  await capture(page, info, "/erp/delivery/DR-009-unavailable");
  await page.unroute("**/api/v1/erp/delivery-requests/DR-009/context");
  await page
    .getByRole("button", { name: "Refresh source records", exact: true })
    .click();
  await expect(page.getByLabel("Supply and demand accounting")).toBeVisible();
  await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
  await layout(page);
});
