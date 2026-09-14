import {
  test,
  expect,
  type Page,
  type APIRequestContext,
} from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import type { components } from "../src/schema";
type S = components["schemas"];
const API = "http://127.0.0.1:18000/api/v1";
const auth = (role = "reader") => ({
  Authorization: `Bearer demo-${role}-local-only`,
});
async function get<T>(request: APIRequestContext, path: string): Promise<T> {
  const r = await request.get(API + path, { headers: auth() });
  expect(r.ok(), await r.text()).toBeTruthy();
  return r.json();
}
async function post(
  request: APIRequestContext,
  path: string,
  body: unknown,
  role = "automation",
  key = crypto.randomUUID(),
) {
  return request.post(API + path, {
    headers: { ...auth(role), "Idempotency-Key": key },
    data: body,
  });
}
async function ready(page: Page) {
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText(/Last API refresh/)).toBeVisible();
}
async function persona(page: Page, value: string) {
  await page.getByLabel("Simulated persona").selectOption(value);
  await ready(page);
}
async function draftBody(request: APIRequestContext): Promise<S["PlanInput"]> {
  const c = await get<S["ChangeView"]>(request, "/engineering/changes/CR-017");
  const opts = await get<S["Options"]>(
    request,
    "/validation/options?change_id=CR-017",
  );
  const o = opts.items.find((o) => o.resource_eligible && o.meets_deadline)!;
  return {
    expected_change_content_version: c.content_version,
    target_requirement_revision_id: c.proposed_requirement_revision_id,
    configuration_id: o.configuration_id,
    procedure_id: o.procedure_id,
    sample_id: o.sample.id,
    slot_id: o.slot.id,
    milestone_id: o.milestone_id,
    expected_source_versions: o.expected_source_versions,
    assessment: {
      facts: [
        {
          text: "Scripted API check: customer requested additional workload evidence.",
          source_refs: [
            { resource_type: "engineering.change", resource_id: c.id },
          ],
        },
      ],
      evidence_gaps: ["Complete applicable evidence is absent."],
      unresolved_questions: ["The future test outcome is unknown."],
    },
  };
}
const errors: string[] = [];
const network: {
  method: string;
  path: string;
  status: number;
  replay: boolean;
}[] = [];
function trackNetwork(page: Page) {
  page.on("response", (response) => {
    const url = new URL(response.url());
    if (!url.pathname.startsWith("/api/v1/")) return;
    network.push({
      method: response.request().method(),
      path: url.pathname + url.search,
      status: response.status(),
      replay: response.headers()["idempotency-replayed"] === "true",
    });
  });
}
test.afterAll(() => {
  mkdirSync("../.cache", { recursive: true });
  writeFileSync(
    "../.cache/ui-review-network.json",
    JSON.stringify(network, null, 2),
  );
});
let externalPlan: S["PlanView"],
  uiPlan: S["PlanView"],
  uiJob: S["JobView"],
  originalOrder: S["Order"],
  originalUnits: unknown,
  originalLots: unknown,
  originalEvidence: unknown;
let browserWriter: Page, engineer: Page, observer: Page;

test.describe.configure({ mode: "serial" });
test.beforeEach(async ({ page }) => {
  page.on("pageerror", (e) => errors.push(e.message));
  trackNetwork(page);
});

test("five source-system apps, direct links, filters and developer screenshots", async ({
  page,
  request,
}) => {
  originalOrder = await get(request, "/erp/orders/ORD-1204");
  originalUnits = await get(request, "/manufacturing/units");
  originalLots = await get(request, "/manufacturing/lots");
  originalEvidence = await get(
    request,
    "/validation/coverage?change_id=CR-017",
  );
  mkdirSync("../docs/screenshots/source-redesign/source-regression", {
    recursive: true,
  });
  await page.goto("/");
  await ready(page);
  await expect(
    page.getByRole("link", { name: "Open application", exact: true }),
  ).toHaveCount(5);
  const popupPromise = page.waitForEvent("popup");
  await page
    .getByRole("link", { name: "Open Stratos PLM in new tab", exact: true })
    .click();
  const popup = await popupPromise;
  await ready(popup);
  await expect(popup).toHaveTitle(/Stratos PLM/);
  await expect(popup.getByLabel("Simulated persona")).toHaveValue("reader");
  await popup.close();
  await page.getByLabel("App switcher").selectOption("erp");
  await expect(page).toHaveURL("/erp");
  expect(
    (await request.get("http://127.0.0.1:5174/e2e/workflow.spec.ts")).status(),
  ).toBe(403);
  for (const path of [
    "/validation/samples",
    "/validation/schedule",
    "/validation/jobs",
    "/validation/results/RES-SHORT-B",
    "/manufacturing/lots",
    "/programs/PRG-A17/milestones/MS-ACCEPT-01",
  ]) {
    await page.goto(path);
    await ready(page);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  }

  const views = [
    [
      "engineering",
      "/engineering/changes/CR-017",
      "Long-context workload acceptance evidence",
    ],
    ["validation", "/validation", "Evidence & coverage"],
    ["manufacturing", "/manufacturing", "Unit inventory"],
    ["erp", "/erp/orders/ORD-1204", "ORD-1204"],
    ["programs", "/programs/PRG-A17", "ACCELERATOR-X program"],
  ];
  for (const [name, path, title] of views) {
    await page.goto(path);
    await ready(page);
    await expect(
      page.getByRole("heading", { name: title, exact: true }),
    ).toBeVisible();
    await expect(page).toHaveTitle(
      new RegExp(
        name === "erp"
          ? "Stratos ERP"
          : name === "programs"
            ? "Stratos ProgramOps"
            : name === "engineering"
              ? "Stratos PLM"
              : name === "manufacturing"
                ? "Stratos MES"
                : "Stratos TestOps",
      ),
    );
    for (const [width, height] of [
      [1440, 900],
      [1280, 800],
    ]) {
      await page.setViewportSize({ width, height });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBeTruthy();
      await page.screenshot({
        path: `../docs/screenshots/source-redesign/source-regression/${name}-${width}-viewport.png`,
      });
      await page.screenshot({
        path: `../docs/screenshots/source-redesign/source-regression/${name}-${width}.png`,
        fullPage: true,
      });
    }
    await page.getByRole("button", { name: "Refresh", exact: true }).click();
    await ready(page);
    await page.reload();
    await ready(page);
  }
  await page.goto("/engineering");
  await ready(page);
  await page.getByLabel("Search changes").fill("nothing");
  await expect(page.getByText("No changes match these filters.")).toBeVisible();
  await page.getByLabel("Search changes").fill("CR-017");
  await expect(
    page.locator(".plm-worklist").getByRole("link", { name: /CR-017/ }),
  ).toBeVisible();
  await page.goto("/validation/options");
  await ready(page);
  await page.getByLabel("Option eligibility").selectOption("eligible");
  await expect(
    page.getByRole("heading", { name: "SLOT-PRIORITY", exact: true }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("heading", { name: "SLOT-UNQUALIFIED", exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Search options").fill("STANDARD");
  await expect(
    page.getByRole("heading", { name: "SLOT-STANDARD", exact: true }),
  ).toHaveCount(1);
  await page.goto("/manufacturing");
  await ready(page);
  await page.getByLabel("Restriction filter").selectOption("held");
  await expect(
    page.getByRole("link", { name: "UNIT-B-018", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "UNIT-B-017", exact: true }),
  ).toHaveCount(0);
  await page.goto("/manufacturing/units/UNIT-B-018");
  await ready(page);
  await expect(
    page.getByText("Engineering hold", { exact: true }).first(),
  ).toBeVisible();
  await page.goto("/engineering/documents/DOC-PROC-01");
  await ready(page);
  await expect(
    page.getByRole("heading", { name: /PROC-LC-02 — supplemental/ }),
  ).toBeVisible();
  await page.goto("/erp");
  await ready(page);
  await page.getByLabel("Search orders").fill("absent");
  await expect(page.getByText("No orders match this search.")).toBeVisible();
  await page.goto("/erp/rates");
  await ready(page);
  await expect(page.getByText("180,000 cents · USD")).toBeVisible();
  await page.goto("/programs");
  await ready(page);
  await page.getByLabel("Search programs").fill("absent");
  await expect(
    page.getByText("No programs match these filters."),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("scripted direct API draft appears on UI refresh; API authority and retry checks", async ({
  page,
  request,
}) => {
  console.log(
    "SCRIPTED API CHECK — no agent run; engineer identity is simulated.",
  );
  await page.goto("/engineering/changes/CR-017");
  await ready(page);
  const body = await draftBody(request);
  const key = crypto.randomUUID();
  const denied = await post(
    request,
    "/engineering/changes/CR-017/plans",
    body,
    "reader",
  );
  expect(denied.status()).toBe(403);
  const made = await post(
    request,
    "/engineering/changes/CR-017/plans",
    body,
    "automation",
    key,
  );
  expect(made.status()).toBe(201);
  externalPlan = await made.json();
  const replay = await post(
    request,
    "/engineering/changes/CR-017/plans",
    body,
    "automation",
    key,
  );
  expect(replay.headers()["idempotency-replayed"]).toBe("true");
  expect(await replay.json()).toEqual(externalPlan);
  const changed = await post(
    request,
    "/engineering/changes/CR-017/plans",
    {
      ...body,
      assessment: {
        ...body.assessment,
        unresolved_questions: ["Revised question."],
      },
    },
    "automation",
    key,
  );
  expect(changed.status()).toBe(409);
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await ready(page);
  await expect(
    page.getByRole("link", { name: externalPlan.id, exact: true }).first(),
  ).toBeVisible();
  const decision = {
    decision: "approve",
    expected_plan_version: externalPlan.plan_version,
    expected_plan_digest: externalPlan.plan_digest,
    reason: "Scripted authority probe.",
  };
  expect(
    (
      await post(
        request,
        `/engineering/plans/${externalPlan.id}/decisions`,
        decision,
      )
    ).status(),
  ).toBe(403);
  expect(
    (
      await post(request, "/validation/jobs", {
        plan_id: externalPlan.id,
        approval_id: "invented",
      })
    ).status(),
  ).toBe(404);
  const rejected = await post(
    request,
    `/engineering/plans/${externalPlan.id}/decisions`,
    { ...decision, decision: "reject" },
    "engineer",
  );
  expect(rejected.status()).toBe(201);
  expect(
    (
      await post(request, "/validation/jobs", {
        plan_id: externalPlan.id,
        approval_id: (await rejected.json()).id,
      })
    ).status(),
  ).toBe(403);
  await page.goto("/engineering/plans/" + externalPlan.id);
  await ready(page);
  await expect(
    page.getByText(
      "Scripted API check: customer requested additional workload evidence.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    page.getByText("Scripted authority probe.", { exact: true }),
  ).toBeVisible();
  writeFileSync(
    "../.cache/ui-review-scripted-api.json",
    JSON.stringify(
      {
        label:
          "SCRIPTED API INTEGRATION CHECK — NO AI; ENGINEER IDENTITY IS SIMULATED",
        plan_id: externalPlan.id,
        create_status: made.status(),
        replay_status: replay.status(),
        replayed: replay.headers()["idempotency-replayed"],
        changed_body_status: changed.status(),
        reader_write_status: denied.status(),
        authored_text_verified_in_browser: body.assessment.facts[0].text,
      },
      null,
      2,
    ),
  );
});

test("operator drafts; different explicitly selected engineer inspects and approves", async ({
  browser,
  request,
}) => {
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:5174",
    viewport: { width: 1440, height: 900 },
  });
  browserWriter = await context.newPage();
  engineer = await context.newPage();
  observer = await context.newPage();
  for (const p of [browserWriter, engineer, observer]) {
    p.on("pageerror", (e) => errors.push(e.message));
    trackNetwork(p);
  }
  await browserWriter.goto("/engineering/changes/CR-017/draft");
  await ready(browserWriter);
  await expect(
    browserWriter.getByRole("button", { name: "Create immutable draft" }),
  ).toBeDisabled();
  await persona(browserWriter, "automation");
  await expect(browserWriter.getByLabel("Validation option")).toHaveValue("");
  await browserWriter
    .getByLabel("Validation option")
    .selectOption("SLOT-PRIORITY|SAMPLE-B-017");
  await browserWriter
    .getByLabel("Assessment fact", { exact: true })
    .fill(
      "Customer requests additional evidence on the unchanged REV-B configuration. <script>window.bad=true</script>",
    );
  await browserWriter
    .getByLabel("Supporting source")
    .selectOption("engineering.change|CR-017");
  await browserWriter
    .getByLabel("Evidence gap", { exact: true })
    .fill("Existing results do not complete the target workload evidence.");
  await browserWriter
    .getByLabel("Unresolved question")
    .fill("Will the full workload satisfy unchanged acceptance criteria?");
  await browserWriter
    .getByRole("button", { name: "Create immutable draft" })
    .click();
  await expect(browserWriter).toHaveURL(/\/engineering\/plans\/plan-/);
  await ready(browserWriter);
  const id = browserWriter.url().split("/").pop()!;
  uiPlan = await get(request, "/engineering/plans/" + id);
  await expect(
    browserWriter.getByRole("button", { name: "Record approval" }),
  ).toBeDisabled();
  expect(await browserWriter.evaluate(() => "bad" in window)).toBeFalsy();
  await engineer.goto("/engineering/plans/" + id);
  await ready(engineer);
  await expect(engineer.getByLabel("Simulated persona")).toHaveValue("reader");
  await persona(engineer, "engineer");
  await expect(
    engineer.locator("#plm-scope").getByText("$1,800.00", { exact: true }),
  ).toBeVisible();
  await engineer
    .getByLabel("Decision reason")
    .fill(
      "Simulated engineer review: exact resources, scope, evidence gap and incremental spend inspected.",
    );
  await engineer.getByLabel(/I reviewed this immutable plan/).check();
  await engineer.getByRole("button", { name: "Record approval" }).click();
  await expect(
    engineer.getByText("Saved and verified from the API."),
  ).toBeVisible();
  await browserWriter.bringToFront();
  await ready(browserWriter);
  await expect(browserWriter.getByLabel("Simulated persona")).toHaveValue(
    "automation",
  );
  await expect(
    browserWriter.getByText("demo-portfolio-engineer", { exact: true }),
  ).toBeVisible();
  uiPlan = await get(request, "/engineering/plans/" + id);
  expect(uiPlan.state).toBe("approved");
  await observer.goto("/programs/PRG-A17");
  await ready(observer);
});

test("lost booking response recovers through retained key after reload; cross-tab state", async ({
  request,
}) => {
  await browserWriter.goto("/validation/jobs");
  await ready(browserWriter);
  await browserWriter
    .getByLabel("Approved plan", { exact: true })
    .selectOption(uiPlan.id);
  let dropped = false;
  const keys: string[] = [];
  await browserWriter.route("**/api/v1/validation/jobs", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    keys.push(route.request().headers()["idempotency-key"]);
    if (!dropped) {
      dropped = true;
      const actual = await route.fetch();
      expect(actual.status()).toBe(201);
      uiJob = await actual.json();
      await route.abort("connectionreset");
    } else await route.continue();
  });
  await browserWriter
    .getByRole("button", { name: "Schedule exact validation job" })
    .dblclick();
  await expect(browserWriter.getByText(/CONNECTION_INTERRUPTED/)).toBeVisible();
  expect(keys).toHaveLength(1); // The second physical click cannot issue another booking.
  await browserWriter.reload();
  await ready(browserWriter);
  await expect(
    browserWriter.getByRole("button", { name: "Retry same request" }),
  ).toBeEnabled();
  await browserWriter
    .getByRole("button", { name: "Retry same request" })
    .click();
  await expect(browserWriter).toHaveURL("/validation/jobs/" + uiJob.id);
  await ready(browserWriter);
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
  await browserWriter.unroute("**/api/v1/validation/jobs");
  const jobs = await get<{ items: S["JobView"][] }>(
    request,
    "/validation/jobs?change_id=CR-017",
  );
  expect(jobs.items).toHaveLength(1);
  expect(jobs.items[0].id).toBe(uiJob.id);
  await observer.bringToFront();
  await ready(observer);
  await expect(
    observer.getByText(/1 lab job is scheduled with no planner link/),
  ).toBeVisible();
  await expect(observer.getByLabel("Simulated persona")).toHaveValue("reader");
  await browserWriter.goto("/validation/schedule");
  await ready(browserWriter);
  await expect(
    browserWriter
      .getByRole("row")
      .filter({ hasText: uiJob.slot_id })
      .getByText("Reserved", { exact: true }),
  ).toBeVisible();
  await browserWriter.screenshot({
    path: "../docs/screenshots/source-redesign/source-regression/validation-reservation.png",
    fullPage: true,
  });
  expect(
    (await get<S["ChangeView"]>(request, "/engineering/changes/CR-017"))
      .execution_state,
  ).toBe("lab_scheduled_pending_planner");
  await browserWriter.goto("/");
  await ready(browserWriter);
  await expect(
    browserWriter.getByText("Update Planner for the scheduled job", {
      exact: true,
    }),
  ).toBeVisible();
  await browserWriter.goto("/engineering/changes/CR-017");
  await ready(browserWriter);
  await expect(browserWriter.locator(".page-heading")).toContainText(
    "Lab scheduled pending planner",
  );
  await expect(browserWriter.locator(".page-heading")).not.toContainText(
    "Approved awaiting scheduling",
  );
});

test("operator links exact scheduled job; protected state and evidence remain unchanged", async ({
  request,
}) => {
  const stale = await post(request, "/programs/PRG-A17/implementation-links", {
    plan_id: uiPlan.id,
    approval_id: uiPlan.decision_id,
    job_id: uiJob.id,
    expected_milestone_record_version: 999,
  });
  expect(stale.status()).toBe(409);
  expect((await stale.json()).error.code).toBe("STALE_MILESTONE");
  await browserWriter.goto("/programs/PRG-A17");
  await ready(browserWriter);
  await browserWriter
    .getByLabel("Approved scheduled job")
    .selectOption(uiJob.id);
  // Test-only transport fault before Planner receives the write. Validation
  // already committed; no successful business response is fabricated.
  const plannerKeys: string[] = [];
  await browserWriter.route(
    "**/api/v1/programs/PRG-A17/implementation-links",
    async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      plannerKeys.push(route.request().headers()["idempotency-key"]);
      if (plannerKeys.length === 1)
        return route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "SERVICE_UNAVAILABLE",
              message: "Test-only Planner outage.",
            },
          }),
        });
      await route.continue();
    },
  );
  await browserWriter
    .getByRole("button", { name: "Link job to program plan" })
    .click();
  await expect(browserWriter.getByRole("alert")).toContainText(
    "SERVICE_UNAVAILABLE",
  );
  await expect(
    browserWriter.getByText("Saved and verified from the API."),
  ).toHaveCount(0);
  expect(
    (
      await get<{ items: S["JobView"][] }>(
        request,
        "/validation/jobs?change_id=CR-017",
      )
    ).items,
  ).toHaveLength(1);
  expect(
    (
      await get<{ items: S["LinkView"][] }>(
        request,
        "/programs/PRG-A17/implementation-links?change_id=CR-017",
      )
    ).items,
  ).toHaveLength(0);
  await browserWriter.reload();
  await ready(browserWriter);
  await expect(
    browserWriter.getByText(/1 lab job is scheduled with no planner link/),
  ).toBeVisible();
  await browserWriter
    .getByRole("button", { name: "Retry same request" })
    .click();
  await expect(
    browserWriter.getByText("Saved and verified from the API."),
  ).toBeVisible();
  expect(plannerKeys).toHaveLength(2);
  expect(plannerKeys[0]).toBe(plannerKeys[1]);
  await browserWriter.unroute(
    "**/api/v1/programs/PRG-A17/implementation-links",
  );
  await expect(
    browserWriter.getByText("Saved and verified from the API."),
  ).toBeVisible();
  await browserWriter.reload();
  await ready(browserWriter);
  await expect(
    browserWriter.getByText("Supplemental validation and engineering review", {
      exact: true,
    }),
  ).toBeVisible();
  await browserWriter.screenshot({
    path: "../docs/screenshots/source-redesign/source-regression/programs-linked.png",
    fullPage: true,
  });
  await engineer.bringToFront();
  await ready(engineer);
  await expect(
    engineer.getByText("Scheduled awaiting execution", { exact: true }).first(),
  ).toBeVisible();
  await engineer.screenshot({
    path: "../docs/screenshots/source-redesign/source-regression/engineering-approved.png",
    fullPage: true,
  });
  const links = await get<{ items: S["LinkView"][] }>(
    request,
    "/programs/PRG-A17/implementation-links?change_id=CR-017",
  );
  expect(links.items).toHaveLength(1);
  expect(links.items[0].task.status).toBe("scheduled");
  expect(
    (await get<S["ChangeView"]>(request, "/engineering/changes/CR-017"))
      .execution_state,
  ).toBe("scheduled_awaiting_execution");
  for (const [path, name] of [
    ["/", "launcher-scheduled"],
    ["/engineering/changes/CR-017", "change-scheduled"],
    ["/validation/options", "options-scheduled"],
  ]) {
    await browserWriter.goto(path);
    await ready(browserWriter);
    await expect(
      browserWriter.getByText("Work already scheduled", { exact: true }),
    ).toBeVisible();
    if (path === "/")
      await expect(
        browserWriter.getByText("Await test execution and engineering review", {
          exact: true,
        }),
      ).toBeVisible();
    if (path.includes("/changes/")) {
      await expect(browserWriter.locator(".page-heading")).toContainText(
        "Scheduled awaiting execution",
      );
      await expect(browserWriter.locator(".page-heading")).not.toContainText(
        "Approved awaiting scheduling",
      );
    }
    if (path === "/validation/options") {
      await expect(
        browserWriter.getByRole("link", {
          name: "Draft assessment",
          exact: true,
        }),
      ).toHaveCount(0);
      await expect(
        browserWriter.getByRole("link", {
          name: "Open scheduled job " + uiJob.id,
          exact: true,
        }),
      ).toBeVisible();
    }
    for (const [width, height] of [
      [1440, 900],
      [1280, 800],
    ]) {
      await browserWriter.setViewportSize({ width, height });
      expect(
        await browserWriter.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBeTruthy();
      await browserWriter.screenshot({
        path: `../docs/screenshots/source-redesign/source-regression/followup-${name}-${width}.png`,
      });
    }
  }
  await browserWriter.goto("/programs/PRG-A17");
  await ready(browserWriter);
  const linkedEvent = browserWriter
    .locator(".event")
    .filter({ hasText: "Link program plan" })
    .filter({ has: browserWriter.locator(".badge.good") })
    .first();
  await linkedEvent.locator("summary").click();
  const recordLink = linkedEvent.getByRole("link", {
    name: /Open Planner record/,
  });
  await expect(recordLink).toHaveAttribute(
    "href",
    "/programs/PRG-A17#link-" + links.items[0].id,
  );
  await expect(
    linkedEvent.getByRole("link", { name: /Open job/ }),
  ).toHaveAttribute("href", "/validation/jobs/" + uiJob.id);
  await recordLink.click();
  await expect(
    browserWriter.locator("#link-" + links.items[0].id),
  ).toBeInViewport();

  const milestone = await get<S["Milestone"]>(
    request,
    "/programs/PRG-A17/milestones/MS-ACCEPT-01",
  );
  expect(milestone.baseline_at).toBe("2026-11-19T18:00:00Z");
  expect(milestone.current_forecast_at).toBe("2026-11-18T20:00:00Z");
  expect(milestone.forecast_status).toBe("conditional_on_test_and_review");
  expect(await get(request, "/erp/orders/ORD-1204")).toEqual(originalOrder);
  expect(await get(request, "/manufacturing/units")).toEqual(originalUnits);
  expect(await get(request, "/manufacturing/lots")).toEqual(originalLots);
  expect(await get(request, "/validation/coverage?change_id=CR-017")).toEqual(
    originalEvidence,
  );
  expect(
    (
      await get<S["Requirement"]>(
        request,
        "/engineering/requirements/REQ-042-V1",
      )
    ).status,
  ).toBe("approved");
  expect(
    (
      await get<S["Requirement"]>(
        request,
        "/engineering/requirements/REQ-042-V2",
      )
    ).status,
  ).toBe("requested");
  const duplicate = await post(request, "/validation/jobs", {
    plan_id: uiPlan.id,
    approval_id: uiPlan.decision_id,
  });
  expect(duplicate.status()).toBe(409);
  expect((await duplicate.json()).error.details.existing_resource_id).toBe(
    uiJob.id,
  );
  for (const path of [
    "/erp/orders/ORD-1204",
    "/manufacturing/lots/LOT-4492",
    "/validation/results/RES-SHORT-B",
  ])
    expect((await post(request, path, {})).status()).toBe(405);
  expect(errors).toEqual([]);
});

test("API outage shows failure and disables writes without fabricated success", async ({
  page,
}) => {
  await page.goto("/engineering/changes/CR-017/draft");
  await ready(page);
  await persona(page, "automation");
  await page.route("**/api/v1/**", (r) => r.abort("connectionrefused"));
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("CONNECTION_INTERRUPTED");
  await expect(
    page.getByRole("button", { name: "Create immutable draft" }),
  ).toBeDisabled();
  await expect(page.getByText("Saved and verified from the API.")).toHaveCount(
    0,
  );
  await page.unroute("**/api/v1/**");
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await ready(page);
  await expect(page.getByRole("alert")).toHaveCount(0);
});
