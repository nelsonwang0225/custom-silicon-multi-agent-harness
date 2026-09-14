import { test, expect, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";

const API = "http://127.0.0.1:18000/api/v1";
const headers = { Authorization: "Bearer demo-reader-local-only" };
async function ready(page: Page) {
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText(/Last API refresh/)).toBeVisible();
}
async function persona(page: Page, role: string) {
  await page.getByLabel("Simulated persona").selectOption(role);
  await ready(page);
}
async function screenshot(page: Page, name: string) {
  mkdirSync("../docs/phase08/workflows/regression-08-2-1/regression-source", { recursive: true });
  for (const [width, height] of [
    [1440, 900],
    [1280, 800],
  ]) {
    await page.setViewportSize({ width, height });
    await page.evaluate(() => window.scrollTo(0, 0));
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `../docs/phase08/workflows/regression-08-2-1/regression-source/followup-${name}-${width}.png`,
      fullPage: true,
    });
  }
}

test("case orientation, multiple citations and immutable revision require fresh approval", async ({
  page,
  request,
}) => {
  console.log(
    "SCRIPTED UI/API INTEGRATION CHECK — NO AI; ALL PERSONAS ARE SIMULATED.",
  );
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await ready(page);
  await expect(
    page.getByText("Assess the customer change", { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("list", { name: "Case stages" })).toBeVisible();
  await screenshot(page, "launcher-clean");
  await page.getByRole("link", { name: "Open next step" }).click();
  await persona(page, "automation");
  await page
    .getByLabel("Validation option")
    .selectOption("SLOT-STANDARD|SAMPLE-B-017");
  await page
    .getByRole("textbox", { name: "Assessment fact", exact: true })
    .fill(
      "The customer requests expanded context coverage on the same configuration.",
    );
  await page
    .getByLabel("Supporting source", { exact: true })
    .selectOption("engineering.change|CR-017");
  await page.getByRole("button", { name: "Add citation to fact 1" }).click();
  await page
    .getByLabel("Supporting source 1.2", { exact: true })
    .selectOption("engineering.document|DOC-REQUEST-01");
  const sourceResponse = page.waitForResponse(
    (r) =>
      r.url().endsWith("/engineering/documents/DOC-REQUEST-01") &&
      r.request().method() === "GET",
  );
  await page.getByText("Preview DOC-REQUEST-01", { exact: true }).click();
  expect((await sourceResponse).status()).toBe(200);
  await expect(page.locator(".source-markdown")).toContainText("480");
  await page.getByRole("button", { name: "Add fact", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Create immutable draft" }),
  ).toBeDisabled();
  await page
    .getByRole("textbox", { name: "Assessment fact 2", exact: true })
    .fill("The requested revision requires the target workload profile.");
  await page
    .getByLabel("Supporting source 2.1")
    .selectOption("engineering.requirement|REQ-042-V2");
  await page
    .getByLabel("Evidence gap", { exact: true })
    .fill("No full applicable run is recorded.");
  await page.getByRole("button", { name: "Add evidence gap" }).click();
  await page
    .getByLabel("Evidence gap 2", { exact: true })
    .fill("Engineering review remains pending.");
  await page
    .getByLabel("Unresolved question", { exact: true })
    .fill("Will the longer workload meet unchanged criteria?");
  await screenshot(page, "assessment");
  await page.reload();
  await ready(page);
  await expect(
    page.getByRole("textbox", { name: "Assessment fact 2", exact: true }),
  ).toHaveValue("The requested revision requires the target workload profile.");
  await page.getByRole("button", { name: "Create immutable draft" }).click();
  await expect(page).toHaveURL(/\/engineering\/plans\/plan-/);
  const originalId = page.url().split("/").pop()!;
  const original = await (
    await request.get(API + "/engineering/plans/" + originalId, { headers })
  ).json();
  expect(original.assessment.facts).toHaveLength(2);
  expect(original.assessment.facts[0].source_refs).toHaveLength(2);
  expect(original.assessment.evidence_gaps).toHaveLength(2);
  await page
    .locator(".assessment-sources")
    .getByText("Preview DOC-REQUEST-01", { exact: true })
    .click();
  await expect(
    page.locator(".assessment-sources .source-preview"),
  ).toContainText("Captured with this immutable plan");
  await expect(
    page.getByRole("button", { name: "Record approval" }),
  ).toBeDisabled();
  await persona(page, "engineer");
  await page
    .getByLabel("Decision reason")
    .fill(
      "Simulated engineer approves the exact initial scope, including its late forecast.",
    );
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Record approval" }).click();
  await expect(
    page.getByText("Saved and verified from the API."),
  ).toBeVisible();
  const approved = await (
    await request.get(API + "/engineering/plans/" + originalId, { headers })
  ).json();
  await page
    .getByRole("link", { name: "Create revised plan", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Create revised plan", exact: true }),
  ).toBeVisible();
  await persona(page, "automation");
  await expect(page.getByLabel("Validation option")).toHaveValue("");
  await expect(
    page.getByRole("textbox", { name: "Assessment fact 2", exact: true }),
  ).toHaveValue(original.assessment.facts[1].text);
  await page
    .getByLabel("Validation option")
    .selectOption("SLOT-PRIORITY|SAMPLE-B-017");
  await page
    .getByRole("textbox", { name: "Assessment fact", exact: true })
    .fill(
      "Revised assessment: the earlier slot leaves time for engineering review before the baseline deadline.",
    );
  await page.getByRole("button", { name: "Create immutable revision" }).click();
  await expect(page).toHaveURL(/\/engineering\/plans\/plan-/);
  const revisionId = page.url().split("/").pop()!;
  expect(revisionId).not.toBe(originalId);
  const revision = await (
    await request.get(API + "/engineering/plans/" + revisionId, { headers })
  ).json();
  expect(revision.supersedes_plan_id).toBe(originalId);
  expect(revision.state).toBe("draft");
  expect(revision.decision_id).toBeNull();
  await expect(
    page.getByRole("heading", { name: "Changes from the preceding plan" }),
  ).toBeVisible();
  const changes = page
    .locator("section")
    .filter({
      has: page.getByRole("heading", {
        name: "Changes from the preceding plan",
      }),
    });
  await expect(changes).toContainText("SLOT-STANDARD");
  await expect(changes).toContainText("SLOT-PRIORITY");
  await screenshot(page, "revision");
  const denied = await request.post(API + "/validation/jobs", {
    headers: {
      Authorization: "Bearer demo-automation-local-only",
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: { plan_id: revisionId, approval_id: approved.decision_id },
  });
  expect(denied.status()).toBe(403);
  await page.goto("/");
  await ready(page);
  await expect(
    page.getByText("Review the exact draft plan", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Open next step" }).click();
  await persona(page, "engineer");
  await page
    .getByLabel("Decision reason")
    .fill(
      "Simulated fresh approval for the revised exact scope and $1,800 charge.",
    );
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Record approval" }).click();
  await expect(
    page.getByText("Saved and verified from the API."),
  ).toBeVisible();
  const latest = await (
    await request.get(API + "/engineering/plans/" + revisionId, { headers })
  ).json();
  expect(latest.decision_id).not.toBe(approved.decision_id);
  const originalAfter = await (
    await request.get(API + "/engineering/plans/" + originalId, { headers })
  ).json();
  expect(originalAfter).toEqual(approved);
  await page.locator(".audit-details summary").first().click();
  await expect(page.locator(".audit-details[open]")).toContainText(
    "Request ID",
  );
  await expect(page.locator(".audit-details[open]")).toContainText(
    "Correlation ID",
  );
  await expect(
    page
      .locator(".audit-details[open]")
      .getByRole("link", { name: /Open decision/ }),
  ).toHaveAttribute("href", new RegExp("#decision-" + latest.decision_id));
  await screenshot(page, "activity");
  await page.goto("/engineering/changes/CR-017/draft?supersedes=unknown");
  await ready(page);
  await expect(page.getByText(/Preceding plan not found/)).toBeVisible();
  expect(errors).toEqual([]);
});

test("source preview failures show errors and richer ERP / hold context comes from HTTP", async ({
  page,
  request,
}) => {
  await page.goto("/manufacturing/lots/LOT-4492");
  await ready(page);
  const lot = await (
    await request.get(API + "/manufacturing/lots/LOT-4492", { headers })
  ).json();
  await expect(
    page.getByText(lot.hold_details[0].rationale, { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(lot.hold_details[0].responsible_team, { exact: true }),
  ).toBeVisible();
  await screenshot(page, "hold");
  await page.goto("/erp/rates");
  await ready(page);
  const rates = await (
    await request.get(API + "/erp/cost-rates?program_id=PRG-A17", { headers })
  ).json();
  await expect(
    page.getByText(rates.items[0].service_description, { exact: true }),
  ).toBeVisible();
  await screenshot(page, "rates");
  await page.goto("/engineering/changes/CR-017/draft");
  await persona(page, "automation");
  await page
    .getByLabel("Validation option")
    .selectOption("SLOT-PRIORITY|SAMPLE-B-017");
  await page
    .getByLabel("Supporting source", { exact: true })
    .selectOption("engineering.document|DOC-REQUEST-01");
  await page.route("**/api/v1/engineering/documents/DOC-REQUEST-01", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "SERVICE_UNAVAILABLE",
          message: "Test-only source preview outage.",
        },
      }),
    }),
  );
  await page.getByText("Preview DOC-REQUEST-01", { exact: true }).click();
  await expect(
    page.locator(".source-preview").getByRole("alert"),
  ).toContainText("SERVICE_UNAVAILABLE");
  await expect(page.locator(".source-markdown")).toHaveCount(0);
});
