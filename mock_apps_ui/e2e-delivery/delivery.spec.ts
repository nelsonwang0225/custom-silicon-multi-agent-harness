import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const path = "/control/programs/PRG-A17/cases/DR-009",
  variant = process.env.DELIVERY_VARIANT || "base";
const artifactDir =
  process.env.SOURCE_BROWSER_ARTIFACT_DIR || "../docs/screenshots/phase08-4c";
async function login(page: any, role: string) {
  await page
    .locator('button[aria-label="Log in"], button[aria-label="Demo profile"]')
    .waitFor({ state: "visible" });
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
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: role, exact: false })
    .click();
}
test(`DR-009 connected delivery · ${variant}`, async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const read = async () =>
    (await request.get("/control-api/cases/DR-009")).json();
  await page.goto("/control/overview");
  await page.getByRole("link", { name: "Inspect case DR-009" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Plan Helios’s 800-unit delivery release",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      /Determine how much of Helios’s 800-unit request can be committed/,
    ),
  ).toBeVisible();
  await expect(
    page.getByText("View original request", { exact: true }),
  ).toBeVisible();
  const before = await read();
  await login(page, "Program operator");
  await page
    .getByRole("button", {
      name: "Assess delivery readiness",
      exact: true,
    })
    .click();
  await expect
    .poll(
      async () => {
        const v = await read();
        return v.runs[0]?.status;
      },
      { timeout: 45000 },
    )
    .toBe("completed");
  await page.reload();
  await login(page, "Program operator");
  await expect(
    page.getByRole("heading", { name: "Agent findings", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/units are eligible for the Helios delivery/),
  ).toBeVisible();
  const state = await read(),
    a = state.context.analysis;
  expect(a.physical_total).toBe(1000);
  expect(a.held_quantity).toBe(250);
  expect(a.allocated_quantity).toBe(150);
  expect(a.eligible_quantity).toBe(variant === "wrong_configuration" ? 0 : 600);
  expect(a.gap_quantity).toBe(variant === "wrong_configuration" ? 800 : 200);
  await page
    .locator("summary")
    .filter({ hasText: "Inventory & supportable quantity" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Inventory & supportable quantity" }),
  ).toBeVisible();
  if (["technical_blocked", "wrong_configuration"].includes(variant)) {
    expect(state.status).toBe("readiness_blocked");
    expect(state.records.plans).toHaveLength(0);
    await expect(
      page.getByRole("button", { name: "Approve exact commitment" }),
    ).toHaveCount(0);
    if (variant === "technical_blocked") {
      expect(a.technical_readiness).toBe("BLOCKED");
      expect(a.customer_ready_quantity).toBe(0);
      await expect(
        page.getByRole("link", { name: "Inspect CR-017 technical dependency" }),
      ).toBeVisible();
    }
  } else {
    const p = state.progress[0],
      ref = {
        run_id: p.run_id,
        plan_id: p.plan_id,
        plan_version: p.plan_version,
        plan_digest: p.plan_digest,
      };
    await expect(
      page.getByRole("button", { name: "Approve exact commitment" }),
    ).toHaveCount(0);
    await expect(
      page.getByText("Responsible role: Program Owner.", { exact: true }),
    ).toBeVisible();
    const wrong = await request.post(
      "/control-api/delivery-commitment/review",
      {
        data: { ...ref, decision: "approve" },
        headers: {
          Origin: "http://127.0.0.1:5178",
          "X-Stratos-Action": "1",
          "X-Stratos-Demo-Profile": "automation",
        },
      },
    );
    expect(wrong.status()).toBe(403);
    if (variant === "stale_proposal") {
      expect(state.status).toBe("stale");
      await login(page, "Program Owner");
      await expect(
        page.getByRole("button", { name: "Approve exact commitment" }),
      ).toBeDisabled();
      const stale = await request.post(
        "/control-api/delivery-commitment/review",
        {
          data: { ...ref, decision: "approve" },
          headers: {
            Origin: "http://127.0.0.1:5178",
            "X-Stratos-Action": "1",
            "X-Stratos-Demo-Profile": "program_owner",
          },
        },
      );
      expect(stale.status()).toBe(409);
      expect((await read()).records.commitments).toHaveLength(0);
    } else {
      expect(state.status).toBe("awaiting_review");
      if (variant === "future_conditional") {
        await page
          .locator("summary")
          .filter({ hasText: "Timing & existing allocations" })
          .click();
        expect(a.future_expected_quantity).toBe(300);
        expect(
          a.options.find((o: any) => o.id === "future_supply").executable,
        ).toBe(false);
        await expect(
          page.getByText(/FUT-HEL-300 · 300 expected/),
        ).toBeVisible();
      }
      await login(page, "Program Owner");
      await page
        .getByRole("textbox", { name: "Review comment" })
        .fill(
          "Authorize exactly 600 units; preserve the remaining gap and customer agreement state.",
        );
      await page
        .getByRole("button", { name: "Approve exact commitment" })
        .click();
      await expect(
        page.getByRole("button", {
          name: "Execute approved ERP and Planner updates",
        }),
      ).toBeEnabled();
      await page
        .getByRole("button", {
          name: "Execute approved ERP and Planner updates",
        })
        .click();
      if (variant === "partial_failure") {
        await expect
          .poll(async () => (await read()).status)
          .toBe("partial_completion");
        const partial = await read();
        expect(partial.records.commitments).toHaveLength(1);
        expect(partial.records.links).toHaveLength(0);
        expect(partial.progress[0].steps.erp.status).toBe("verified");
        await page.reload();
        await login(page, "Program operator");
        await expect(
          page.getByText(/Partial completion — ERP update verified/),
        ).toBeVisible();
        await expect(page.locator(".cp-connection")).toContainText(
          "Current read",
        );
        await mkdir(artifactDir, { recursive: true });
        await page.screenshot({
          path: `${artifactDir}/partial-reconciliation.png`,
          fullPage: true,
        });
        await page
          .getByRole("button", { name: "Reconcile and retry approved updates" })
          .click();
      }
      await expect.poll(async () => (await read()).status).toBe("verified");
      const final = await read();
      expect(final.records.commitments).toHaveLength(1);
      expect(final.records.links).toHaveLength(1);
      expect(final.context.input_digest).toBe(before.context.input_digest);
      expect(final.context.material).toEqual(before.context.material);
      expect(final.context.allocations).toEqual(before.context.allocations);
      expect(final.context.technical_dependency).toEqual(
        before.context.technical_dependency,
      );
      const commitment = final.context.commitment;
      expect(commitment.quantity).toBe(600);
      expect(commitment.remaining_uncommitted_quantity).toBe(200);
      expect(commitment.customer_agreement).toBe("pending");
      expect(commitment.delivered_quantity).toBe(0);
      expect(commitment.allocation_changed).toBe(false);
      expect(final.records.links[0].quantity).toBe(commitment.quantity);
      expect(final.records.links[0].committed_at).toBe(commitment.committed_at);
      const release = await request.post(
        "/api/v1/manufacturing/lots/LOT-B-204/release",
        {
          data: {},
          headers: {
            Authorization: "Bearer demo-automation-local-only",
            "Idempotency-Key": "delivery-browser-release-denied",
          },
        },
      );
      expect([404, 405]).toContain(release.status());
      if (variant === "base") {
        await page.goto("/control/decisions");
        await login(page, "Program Owner");
        await page
          .getByRole("link", { name: "Decisions", exact: true })
          .click();
        await page
          .getByRole("combobox", { name: "Decision status", exact: true })
          .selectOption("Needs review");
        await expect(
          page.locator('.cp-decision-row[data-case-id="DR-009"]'),
        ).toHaveCount(0);
        await page
          .getByRole("combobox", { name: "Decision status", exact: true })
          .selectOption("Executed / Completed");
        await expect(
          page.locator('.cp-decision-row[data-case-id="DR-009"]'),
        ).toHaveCount(1);
        await page.goto("/control/workflows/delivery_readiness");
        await login(page, "Program operator");
        await page
          .getByRole("link", { name: "Workflows & Automations", exact: true })
          .click();
        await page
          .locator('a[href="/control/workflows/delivery_readiness"]')
          .first()
          .click();
        await expect(
          page.getByText("Connected", { exact: true }).first(),
        ).toBeVisible();
        await expect(
          page.getByText(/Schedule configured · runner inactive/),
        ).toBeVisible();
        const runLink = page.locator(`a[href="/control/runs/${p.run_id}"]`);
        await expect(runLink).toBeVisible();
        await runLink.click();
        await expect(page).toHaveURL(new RegExp(`/control/runs/${p.run_id}$`));
        await page.goBack();
        await expect(
          page.getByRole("heading", { name: "Run history", exact: true }),
        ).toBeVisible();
        await page.getByLabel("Search Stratos", { exact: true }).fill("DR-009");
        await page
          .getByRole("dialog", { name: "Search results" })
          .getByRole("button", { name: /DR-009 · Delivery/ })
          .first()
          .click();
        await expect(page).toHaveURL(new RegExp(`${path}$`));
        for (const [system, heading] of [
          ["erp", "Delivery request & commercial commitment"],
          ["programs", "Delivery milestone & commitment links"],
          ["manufacturing", "Shared material & disposition"],
          ["engineering", "Configuration & Engineering clearance"],
          ["validation", "Applicable evidence & technical dependency"],
        ]) {
          await page.goto(`/${system}/delivery/DR-009`);
          await expect(
            page.getByRole("heading", { name: heading, exact: true }),
          ).toBeVisible();
        }
      }
    }
  }
  await page.goto(path);
  await expect(
    page.getByRole("heading", {
      name: "Plan Helios’s 800-unit delivery release",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  await mkdir(artifactDir, { recursive: true });
  await page.screenshot({
    path: `${artifactDir}/${variant}.png`,
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: `${artifactDir}/${variant}-mobile.png`,
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
