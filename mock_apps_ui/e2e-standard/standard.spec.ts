import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const path = "/control/programs/PRG-A17/cases/CR-019";
const variant = process.env.STANDARD_VARIANT || "success";
const screenshots = "../docs/screenshots/source-redesign/standard";
async function login(page: any) {
  await page.getByRole("button", { name: /^(Log in|Demo profile)$/ }).click();
  await page
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: /Program operator/ })
    .click();
}
test("Overview keeps CR-019 discoverable and shows Northstar on track", async ({
  page,
  request,
}) => {
  await page.goto("/control/overview");
  await expect(
    page.locator('.cp-attention [data-case-id="CR-019"]'),
  ).toHaveCount(1);
  await expect(
    page.locator(".cp-program-row").filter({ hasText: "Northstar Boreal" }),
  ).toContainText("On track");
  await expect(
    page.locator('.cp-attention [data-case-id="CR-019"]'),
  ).toContainText("New");
  await page.goto(path);
  await expect(
    page.getByRole("heading", {
      name: "Why this handoff can proceed automatically",
    }),
  ).toHaveCount(0);
  await expect(page.getByText(/checks matched/)).toHaveCount(0);
  const initial = await (await request.get("/control-api/cases/CR-019")).json();
  expect(initial.eligibility).toBeNull();
});
test("connected standard request reaches the policy-bound handoff or review stop", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/control/programs/PRG-A17");
  await page
    .getByLabel("Connected workflow cases")
    .locator('[data-case-id="CR-019"]')
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Add approved WF-LC-V1 profile to the Helios acceptance package",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(/Confirm whether this already-approved workload profile/),
  ).toBeVisible();
  await expect(
    page.getByText("View original request", { exact: true }),
  ).toBeVisible();
  await login(page);
  await expect(
    page.getByRole("button", { name: "Run investigation", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Run investigation", exact: true })
    .click();
  await expect
    .poll(
      async () => {
        const r = await request.get("/control-api/cases/CR-019");
        return r.ok() ? (await r.json()).runs[0]?.status : "";
      },
      { timeout: 45000 },
    )
    .toBe("completed");
  await page.reload();
  if (variant === "success") {
    await expect(
      page.getByRole("heading", { name: "Agent findings", exact: true }),
    ).toBeVisible();
    await expect(page.getByText(/approved-scope checks matched/)).toBeVisible();
    await expect(page.getByLabel("CR-019 current case state")).toContainText(
      "Validation Operations received and verified the handoff package",
    );
    await page
      .getByText("Handoff package & remaining standard work", { exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Handoff package", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Bounded pre-authorized handoff · No new human approval", {
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByText("Pending · Separate authority", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", {
        name: /Approve proposal|Record engineering approval/,
      }),
    ).toHaveCount(0);
    const first = await (await request.get("/control-api/cases/CR-019")).json();
    expect(first.handoffs[0].intake.physical_testing).toBe("not_started");
    expect(first.handoffs[0].intake.customer_acceptance).toBe("pending");
    await mkdir(screenshots, { recursive: true });
    await page.screenshot({
      path: `${screenshots}/standard-handoff.png`,
      fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `${screenshots}/standard-mobile.png`,
      fullPage: true,
    });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
    await page
      .getByRole("button", { name: "Run investigation again", exact: true })
      .click();
    await expect
      .poll(
        async () => {
          const s = await (
            await request.get("/control-api/cases/CR-019")
          ).json();
          return s.handoffs.length;
        },
        { timeout: 45000 },
      )
      .toBe(2);
    const next = await (await request.get("/control-api/cases/CR-019")).json();
    expect(next.handoffs[0].intake.id).toBe(first.handoffs[0].intake.id);
    await page
      .getByRole("navigation", { name: "Control plane navigation" })
      .getByRole("link", { name: "Workflows & Automations", exact: true })
      .click();
    await page
      .getByRole("link", { name: /Standard Change/ })
      .first()
      .click();
    await expect(
      page.getByRole("heading", { name: "Run history", exact: true }),
    ).toBeVisible();
    await expect(
      page
        .getByText("No human approval · Bounded pre-authorized handoff")
        .first(),
    ).toBeVisible();
    await page.screenshot({
      path: `${screenshots}/workflow-history.png`,
      fullPage: true,
    });
    const search = page.getByPlaceholder("Search Stratos...");
    await search.fill(first.handoffs[0].package.package_id);
    await expect(
      page
        .getByRole("button", {
          name: new RegExp(first.handoffs[0].package.package_id),
        })
        .first(),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await search.fill(first.handoffs[0].intake.id);
    await expect(
      page
        .getByRole("button", { name: new RegExp(first.handoffs[0].intake.id) })
        .first(),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await page
      .getByRole("region", { name: "Run history table" })
      .getByRole("link", { name: "CR-019 · Investigation" })
      .first()
      .click();
    await page
      .getByText("Handoff package & remaining standard work", { exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Handoff package", exact: true }),
    ).toBeVisible();
    await page.goto(`/validation/intakes/${first.handoffs[0].intake.id}`);
    await expect(
      page.getByRole("heading", {
        name: "Validation Operations intake",
        exact: true,
      }),
    ).toBeVisible();
    await expect(page.getByText("Not started", { exact: true })).toBeVisible();
    await page.screenshot({
      path: `${screenshots}/validation-intake.png`,
      fullPage: true,
    });
    await page.goto("/control/overview");
    const attention = page.locator(".cp-attention");
    await expect(attention.locator('[data-case-id="CR-019"]')).toHaveCount(0);
  } else {
    await expect(
      page.getByText("Standard change requires review", { exact: true }),
    ).toBeVisible();
    const state = await (await request.get("/control-api/cases/CR-019")).json();
    expect(state.handoffs[0].package).toBeNull();
    expect(state.handoffs[0].action_status).toBe("not_attempted");
    const source = await request.get(
      "/api/v1/validation/changes/CR-019/intakes",
      { headers: { Authorization: "Bearer demo-reader-local-only" } },
    );
    expect((await source.json()).items).toHaveLength(0);
    await mkdir(screenshots, { recursive: true });
    await page.screenshot({
      path: `${screenshots}/standard-${variant}-blocked.png`,
      fullPage: true,
    });
  }
  expect(errors).toEqual([]);
});
