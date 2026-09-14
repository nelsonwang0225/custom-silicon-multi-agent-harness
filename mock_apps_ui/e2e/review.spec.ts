import { test, expect, type Page } from "@playwright/test";

async function draftForm(page: Page) {
  await page.goto("/engineering/changes/CR-017/draft");
  await page.getByLabel("Simulated persona").selectOption("automation");
  await expect(page.getByLabel("Validation option")).toBeEnabled();
  await page
    .getByLabel("Validation option")
    .selectOption("SLOT-PRIORITY|SAMPLE-B-017");
  await page
    .getByRole("textbox", { name: "Assessment fact", exact: true })
    .fill(
      "Independent review: the customer requests additional evidence on the existing configuration.",
    );
  await page
    .getByLabel("Supporting source")
    .selectOption("engineering.change|CR-017");
}

test("a committed draft with denied read-back retains its original request across reload", async ({
  page,
  request,
}) => {
  const headers = { Authorization: "Bearer demo-reader-local-only" };
  const change = "http://127.0.0.1:18000/api/v1/engineering/changes/CR-017";
  const before = (await (await request.get(change, { headers })).json()).plans
    .length;
  await draftForm(page);
  const keys: string[] = [];
  const ids: string[] = [];
  page.on("response", async (response) => {
    if (
      response.request().method() === "POST" &&
      response.url().endsWith("/plans")
    ) {
      keys.push(response.request().headers()["idempotency-key"]);
      ids.push((await response.json()).id);
    }
  });
  await page.route("**/api/v1/engineering/plans/*", (route) =>
    route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "FORBIDDEN_ROLE",
          message: "Test-only denial of canonical read-back.",
        },
      }),
    }),
  );
  await page.getByRole("button", { name: "Create immutable draft" }).click();
  await expect(page.getByRole("alert")).toContainText("FORBIDDEN_ROLE");
  await expect(
    page.getByRole("button", { name: "Revise request after denial" }),
  ).toHaveCount(0);
  await expect(page.getByText("Saved and verified from the API.")).toHaveCount(
    0,
  );
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Retry same request" }),
  ).toBeEnabled();
  await page.getByLabel("Simulated persona").selectOption("engineer");
  await expect(
    page.getByRole("button", { name: "Retry same request" }),
  ).toBeDisabled();
  await page.getByLabel("Simulated persona").selectOption("automation");
  await page.unroute("**/api/v1/engineering/plans/*");
  await page.getByRole("button", { name: "Retry same request" }).click();
  await expect(page).toHaveURL(/\/engineering\/plans\/plan-/);
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
  expect(ids[0]).toBe(ids[1]);
  const after = await (await request.get(change, { headers })).json();
  expect(after.plans).toHaveLength(before + 1);
});

test("options distinguish actual sample configuration, policy blocks and late timing", async ({
  page,
}) => {
  await page.goto("/validation/options");
  const card = page
    .locator("section")
    .filter({
      has: page.getByRole("heading", { name: "SLOT-PRIORITY", exact: true }),
    })
    .filter({ hasText: "SAMPLE-A-010" });
  await expect(
    card.getByText("SAMPLE-A-010 / CFG-A-01", { exact: true }),
  ).toBeVisible();
  await expect(card.getByText("CFG-B-01", { exact: true })).toBeVisible();
  await expect(card.getByText("Approval unavailable")).toHaveClass(/warning/);
  await page.getByLabel("Option eligibility").selectOption("eligible");
  await expect(page.getByText("28 hours after baseline")).toHaveClass(
    /warning/,
  );
  await expect(page.getByText("22 hours before baseline")).toHaveClass(/good/);
  await page
    .getByRole("link", { name: "Draft assessment", exact: true })
    .click();
  await expect(page.getByLabel("Validation option")).toHaveValue("");
});

test("unknown domain pages and milestones never silently display another record", async ({
  page,
}) => {
  for (const path of [
    "/validation/unknown",
    "/manufacturing/unknown",
    "/erp/unknown",
    "/engineering/changes/CR-017/unknown",
    "/programs/PRG-A17/milestones/unknown",
  ]) {
    await page.goto(path);
    await expect(page.getByText(/not found/i)).toBeVisible();
  }
});

test("fresh visits with API failures show no frontend business fixtures in any app", async ({
  page,
}) => {
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "SERVICE_UNAVAILABLE",
          message: "Test-only API outage.",
        },
      }),
    }),
  );
  for (const app of [
    "engineering",
    "validation",
    "manufacturing",
    "erp",
    "programs",
  ]) {
    await page.goto("/" + app);
    await expect(page.getByRole("alert")).toContainText("SERVICE_UNAVAILABLE");
    await expect(
      page.getByText("Business data is unavailable.", { exact: false }),
    ).toBeVisible();
    await expect(
      page.getByText(
        /CR-017|ACCELERATOR-X|ORD-1204|LOT-4491|HELIOS AI/,
      ),
    ).toHaveCount(0);
    await expect(
      page.getByText("Saved and verified from the API."),
    ).toHaveCount(0);
  }
});

test("a real stale-source denial preserves the assessment for explicit revision", async ({
  page,
  request,
}) => {
  const url = "http://127.0.0.1:18000/api/v1/engineering/changes/CR-017";
  const headers = { Authorization: "Bearer demo-reader-local-only" };
  const before = (await (await request.get(url, { headers })).json()).plans
    .length;
  await draftForm(page);
  await page.route(
    "**/api/v1/engineering/changes/CR-017/plans",
    async (route) => {
      const body = route.request().postDataJSON();
      body.expected_source_versions.records[0].content_version += 1;
      await route.continue({ postData: JSON.stringify(body) });
    },
  );
  await page.getByRole("button", { name: "Create immutable draft" }).click();
  await expect(page.getByRole("alert")).toContainText("STALE_SOURCE");
  expect(
    (await (await request.get(url, { headers })).json()).plans,
  ).toHaveLength(before);
  await expect(
    page.getByRole("textbox", { name: "Assessment fact", exact: true }),
  ).toHaveValue(/Independent review/);
  await page.unroute("**/api/v1/engineering/changes/CR-017/plans");
  await page
    .getByRole("button", { name: "Revise request after denial" })
    .click();
  await expect(
    page.getByRole("textbox", { name: "Assessment fact", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("textbox", { name: "Assessment fact", exact: true })
    .fill("Reassessed after refreshing the stale source versions.");
  await page.getByRole("button", { name: "Create immutable draft" }).click();
  await expect(page).toHaveURL(/\/engineering\/plans\/plan-/);
  expect(
    (await (await request.get(url, { headers })).json()).plans,
  ).toHaveLength(before + 1);
});

test("unknown server errors retain the request instead of enabling a second draft", async ({
  page,
}) => {
  await draftForm(page);
  await page.route("**/api/v1/engineering/changes/CR-017/plans", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "UPSTREAM_FAILURE",
          message: "Test-only server failure.",
        },
      }),
    }),
  );
  await page.getByRole("button", { name: "Create immutable draft" }).click();
  await expect(page.getByRole("alert")).toContainText("UPSTREAM_FAILURE");
  await expect(
    page.getByRole("button", { name: "Revise request after denial" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Retry same request" }),
  ).toBeEnabled();
  await expect(page.getByText("Saved and verified from the API.")).toHaveCount(
    0,
  );
});

test("a newer focus refresh completes a pending write without false success or false failure", async ({
  page,
}) => {
  await draftForm(page);
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  let started!: () => void;
  const arrived = new Promise<void>((resolve) => {
    started = resolve;
  });
  let calls = 0;
  await page.route("**/api/v1/programs", async (route) => {
    calls++;
    if (calls === 1) {
      started();
      await held;
    }
    await route.continue();
  });
  await page.getByRole("button", { name: "Create immutable draft" }).click();
  await arrived;
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect.poll(() => calls).toBeGreaterThan(1);
  release();
  await expect(page).toHaveURL(/\/engineering\/plans\/plan-/);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test('option comparison and draft forms fit both requested desktop viewports', async ({page}) => {
  for (const [width, height] of [[1440, 900], [1280, 800]]) {
    await page.setViewportSize({width, height});
    await page.goto('/validation/options');
    await expect(page.getByLabel('Option eligibility')).toBeVisible();
    await page.getByLabel('Option eligibility').selectOption('eligible');
    await expect(page.getByText('22 hours before baseline')).toBeVisible();
    await page.screenshot({path: `../docs/phase08/workflows/regression-08-2-1/regression-source/options-${width}.png`, fullPage: true});
    await draftForm(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await page.screenshot({path: `../docs/phase08/workflows/regression-08-2-1/regression-source/draft-${width}.png`, fullPage: true});
  }
});
