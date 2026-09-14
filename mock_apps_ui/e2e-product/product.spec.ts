import { test, expect, type Page } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
const program = "/control/programs/PRG-A17",
  root = program + "/cases/";
async function post(
  page: Page,
  path: string,
  body: unknown,
  role = "automation",
) {
  return page.request.post("/control-api/" + path, {
    data: body,
    headers: {
      Origin: "http://127.0.0.1:5192",
      "X-Stratos-Action": "1",
      "X-Stratos-Demo-Profile": role,
    },
  });
}
async function snapshot(page: Page) {
  return (await page.request.get("/control-api/cases/CR-017")).json();
}
async function gotoAsOperator(page: Page, path: string) {
  const login = page.getByRole("button", { name: "Log in", exact: true });
  if (await login.isVisible()) {
    await login.click();
    await page
      .getByRole("dialog", { name: "Demo access", exact: true })
      .getByRole("button", { name: /^Program operator/ })
      .click();
  }
  await page.evaluate((target) => {
    history.pushState(null, "", target);
    dispatchEvent(new PopStateEvent("popstate"));
  }, path);
  await expect(page).toHaveURL(path);
  await expect(page.locator("main h1")).toBeVisible();
}
async function start(page: Page, id: string) {
  const r = await post(page, `cases/${id}/investigations`, {
    invocation_id: "ui_product_" + randomUUID().replaceAll("-", ""),
    change_id: id,
    workflow_id:
      id === "QE-004"
        ? "yield_exception_recovery"
        : id === "DR-009"
          ? "delivery_readiness"
          : "requirement_change_analysis",
  });
  expect(r.status()).toBe(202);
  const run = (await r.json()).run_id;
  await expect
    .poll(
      async () => {
        const v = await snapshot(page),
          s = v.case_summaries.find((c: any) => c.change_id === id);
        return (
          s.run_id === run &&
          s.state !== "investigating" &&
          (id !== "CR-017" || v.proposals.length > 0)
        );
      },
      { timeout: 45000 },
    )
    .toBe(true);
  return run;
}
async function openDemoControls(page: Page) {
  if (page.url() === "about:blank") await page.goto("/control/operations/demo");
  const login = page.getByRole("button", { name: "Log in", exact: true });
  await expect(login).toBeVisible();
  await login.click();
  await page
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: /^Program operator/ })
    .click();
  const review = page.getByRole("button", { name: "Review reset…" });
  if (await review.isVisible()) return;
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Operations", exact: true })
    .click();
  await page.getByRole("link", { name: "Demo controls" }).click();
  await expect(review).toBeVisible();
}
async function reset(page: Page) {
  await openDemoControls(page);
  await page.getByRole("button", { name: "Review reset…" }).click();
  await page.getByLabel("Type RESET to confirm").fill("RESET");
  await page.getByRole("button", { name: "Confirm demo reset" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await openDemoControls(page);
  await page.getByRole("button", { name: "Verify baseline" }).click();
  await expect(
    page.getByRole("heading", { name: "Baseline valid · full" }),
  ).toBeVisible();
}
async function shot(page: Page, name: string) {
  await expect(page.locator("main h1")).toBeVisible();
  await mkdir("../docs/screenshots/phase09-2", { recursive: true });
  await page.screenshot({
    path: `../docs/screenshots/phase09-2/${name}.png`,
    fullPage: true,
  });
}
async function ask(page: Page, context: string) {
  const body = {
    session_id: "chat_" + randomUUID().replaceAll("-", ""),
    message_id: "msg_" + randomUUID().replaceAll("-", ""),
    context,
    text: "What is the status of DR-009?",
  };
  expect((await post(page, "concierge/messages", body)).status()).toBe(202);
  let turn: any;
  await expect
    .poll(async () => {
      turn = await (
        await page.request.get(
          `/control-api/concierge/${body.session_id}/${body.message_id}`,
          { headers: { "X-Stratos-Demo-Profile": "automation" } },
        )
      ).json();
      return turn.status;
    })
    .toBe("completed");
  return turn.cards
    .flatMap((c: any) => c.facts)
    .find((f: any) => f[0] === "Current source")?.[1];
}

test("four workflows share decisions, attention, search, context, source links and reset state", async ({
  page,
  context,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await context.addInitScript(() => {
    class Speech {
      start() {
        throw Error("No real microphone in product tests");
      }
      stop() {}
      abort() {}
    }
    Object.assign(window, {
      SpeechRecognition: Speech,
      webkitSpeechRecognition: Speech,
    });
  });
  await reset(page);
  await gotoAsOperator(page, program);
  const connected = page.getByLabel("Connected workflow cases");
  await expect(connected.locator("[data-case-id]")).toHaveCount(4);
  for (const id of ["CR-017", "CR-019", "QE-004", "DR-009"])
    await expect(connected.locator(`[data-case-id="${id}"]`)).toHaveCount(1);
  await expect(page.locator("main")).toContainText(
    "Approved baseline → DR-009",
  );
  await expect(page.locator("main")).toContainText(
    "CR-017 requested V2 evidence is a separate obligation",
  );
  await expect(
    page.getByRole("region", { name: "Agent workspace" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Needs attention", exact: true }),
  ).toHaveCount(0);
  await shot(page, "program-baseline");
  await start(page, "CR-019");
  await gotoAsOperator(page, "/control/overview");
  await expect(
    page.getByRole("region", { name: "Agent workspace" }),
  ).toContainText("CR-019");
  await expect(
    page.getByRole("link", { name: "Inspect CR-019" }),
  ).toHaveAttribute("href", root + "CR-019");
  await start(page, "QE-004");
  await start(page, "DR-009");
  const materialRun = await start(page, "CR-017");
  await gotoAsOperator(page, "/control/overview");
  await expect(page.locator('[data-metric="Needs review"] strong')).toHaveText(
    "0",
  );
  const attention = page.locator(".cp-attention");
  for (const id of ["CR-017", "QE-004", "DR-009"])
    await expect(attention.locator(`[data-case-id="${id}"]`)).toHaveCount(1);
  await expect(attention.locator('[data-case-id="CR-019"]')).toHaveCount(0);
  await shot(page, "overview-review");
  await gotoAsOperator(page, "/control/decisions");
  await expect(page.locator(".cp-decision-row")).toHaveCount(3);
  await expect(
    page.locator('.cp-decision-row[data-case-id="CR-019"]'),
  ).toHaveCount(0);
  await shot(page, "decisions");
  const before = await snapshot(page);
  const dr = before.delivery.progress[0];
  const exact = {
    run_id: dr.run_id,
    plan_id: dr.plan_id,
    plan_version: dr.plan_version,
    plan_digest: dr.plan_digest,
  };
  expect(
    (
      await post(
        page,
        "delivery-commitment/review",
        {
          ...exact,
          decision: "approve",
          comment: "Scripted exact demo decision",
        },
        "program_owner",
      )
    ).status(),
  ).toBe(200);
  expect(
    (
      await post(page, "delivery-commitment/execute", exact, "program_owner")
    ).status(),
  ).toBe(200);
  const current = (await snapshot(page)).case_summaries.find(
    (c: any) => c.change_id === "DR-009",
  ).detail;
  for (const route of [
    "/control/overview",
    program,
    root + "DR-009",
    "/control/decisions",
    "/control/workflows/delivery_readiness",
    "/control/operations",
  ])
    expect(await ask(page, route)).toBe(current);
  await gotoAsOperator(
    page,
    "/control/decisions?filter=Executed%20%2F%20Completed",
  );
  await page.getByRole("button", { name: "Refresh workflow" }).click();
  const decision = page.locator('.cp-decision-row[data-case-id="DR-009"]');
  await expect(decision).toHaveCount(1);
  await expect(decision).toContainText("demo-program-owner");
  await decision.click();
  await expect(page).toHaveURL(new RegExp("plan=" + dr.plan_id));
  await expect(page.getByLabel("DR-009 current case state")).toContainText(
    "200 gap remains",
  );
  await gotoAsOperator(page, program);
  const search = page.getByRole("textbox", { name: "Search Stratos" });
  for (const id of ["CR-017", "CR-019", "QE-004", "DR-009"]) {
    await search.fill(id);
    // First business result is the one canonical case, before runs and technical records.
    await expect(
      page.locator(".cp-search-results button").first(),
    ).toContainText(id);
  }
  await search.fill("MAT-B-202");
  const material = page.getByRole("button", { name: /MAT-B-202 · LOT-B-202/ });
  await expect(material).toBeVisible();
  await material.click();
  await expect(page).toHaveURL(/\/manufacturing\/lots\/LOT-B-202/);
  await expect(page.locator("main")).toContainText("LOT-B-202");
  await gotoAsOperator(page, program);
  await page.getByRole("button", { name: /Notifications|alerts/i }).click();
  const alerts = page.getByLabel("Source alerts");
  await expect(alerts.locator('a[href$="/cases/CR-019"]')).toHaveCount(0);
  for (const id of ["CR-017", "QE-004", "DR-009"])
    await expect(alerts.locator(`a[href$="/cases/${id}"]`)).toHaveCount(1);
  await page.keyboard.press("Escape");
  const stale = await context.newPage();
  await stale.goto(root + "CR-017");
  await expect(stale.getByLabel("CR-017 current case state")).toContainText(
    "Needs review",
  );
  await stale.evaluate(() => {
    sessionStorage.setItem("stratos-cr017-invocation", "ui_old");
    sessionStorage.setItem("stratos.quality.invocation", "ui_old");
    sessionStorage.setItem("stratos.delivery.invocation", "ui_old");
  });
  await reset(page);
  await expect(stale.getByLabel("CR-017 current case state")).toHaveAttribute(
    "data-case-state",
    "new",
    { timeout: 15000 },
  );
  await expect(
    stale.getByRole("link", { name: /Review exact proposal/ }),
  ).toHaveCount(0);
  expect(
    await stale.evaluate(() =>
      [
        "stratos-cr017-invocation",
        "stratos.quality.invocation",
        "stratos.delivery.invocation",
      ].some((k) => sessionStorage.getItem(k)),
    ),
  ).toBe(false);
  await gotoAsOperator(page, program);
  await expect(
    page
      .getByLabel("Connected workflow cases")
      .locator('[data-case-state="new"]'),
  ).toHaveCount(4);
  await gotoAsOperator(page, "/control/decisions");
  await expect(page.locator(".cp-decision-row")).toHaveCount(0);
  const cleared = await snapshot(page);
  expect(cleared.runs).toHaveLength(0);
  expect(cleared.standard.runs).toHaveLength(0);
  await gotoAsOperator(page, "/control/operations");
  await expect(
    page.getByRole("link", { name: /CR-019 · View run/ }),
  ).toHaveCount(0);
  expect(
    (
      await (
        await page.request.get("/control-api/operations", {
          headers: { "X-Stratos-Demo-Profile": "automation" },
        })
      ).json()
    ).runs.filter((run: any) => run.case_id !== "QE-011"),
  ).toHaveLength(0);
  await gotoAsOperator(page, program);
  await expect(
    page
      .getByLabel("Connected workflow cases")
      .locator('[data-case-state="new"]'),
  ).toHaveCount(4);
  await shot(page, "reset-baseline");
  await stale.close();
  expect(errors).toEqual([]);
});
