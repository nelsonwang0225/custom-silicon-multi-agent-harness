import { test, expect, type Page } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
const variant = process.env.OPERATIONS_VARIANT || "base";
const root = "/control/programs/PRG-A17/cases/";
const session = "chat_" + randomUUID().replaceAll("-", "");
async function post(
  page: Page,
  path: string,
  body: unknown,
  role = "automation",
) {
  return page.request.post("/control-api/" + path, {
    data: body,
    headers: {
      Origin: "http://127.0.0.1:5180",
      "X-Stratos-Action": "1",
      "X-Stratos-Demo-Profile": role,
    },
  });
}
async function ask(page: Page, text: string, caseId?: string) {
  const body = {
    session_id: session,
    message_id: "msg_" + randomUUID().replaceAll("-", ""),
    context: caseId ? root + caseId : "/control/overview",
    text,
  };
  expect((await post(page, "concierge/messages", body)).status()).toBe(202);
  let turn: any;
  await expect
    .poll(
      async () => {
        turn = await (
          await page.request.get(
            "/control-api/concierge/" + session + "/" + body.message_id,
          )
        ).json();
        return turn.status === "running"
          ? "running"
          : turn.status === "completed"
            ? "completed"
            : JSON.stringify(turn);
      },
      { timeout: 30000 },
    )
    .toBe("completed");
  return { turn, body };
}
async function invoke(page: Page, caseId: string) {
  const { turn } = await ask(page, "Investigate " + caseId, caseId);
  const id = turn.cards[0].run_id;
  await expect
    .poll(
      async () => {
        const rows = await (
          await page.request.get("/control-api/operations/runs")
        ).json();
        return rows.find((r: any) => r.run_id === id)?.runtime_state;
      },
      { timeout: 60000 },
    )
    .toBe("completed");
  if (caseId === "CR-017")
    await expect
      .poll(async () => {
        const c = await (
          await page.request.get("/control-api/cases/CR-017")
        ).json();
        return c.proposals.some((p: any) => p.proposal.origin.run_id === id);
      })
      .toBe(true);
  return id;
}
async function action(page: Page, text: string) {
  const { turn, body } = await ask(page, text, "DR-009");
  return post(
    page,
    "concierge/" + session + "/actions/" + turn.cards[0].action_id,
    { context: body.context, confirmed: true },
    "program_owner",
  );
}
async function capture(page: Page, name: string) {
  await expect(page.locator(".cp-connection")).not.toContainText("Reading…");
  await page.evaluate(() => window.scrollTo(0, 0));
  await mkdir("../docs/screenshots/phase08-6", { recursive: true });
  await page.screenshot({
    path: "../docs/screenshots/phase08-6/" + name + ".png",
    fullPage: true,
  });
}

test("Operations connects all business workflows, Concierge and historical reliability", async ({
  page,
}) => {
  test.skip(variant !== "base");
  const runs: Record<string, string> = {};
  for (const c of ["CR-017", "CR-019", "QE-004", "DR-009"])
    runs[c] = await invoke(page, c);
  expect((await action(page, "Approve it")).status()).toBe(200);
  expect((await action(page, "Execute approved plan")).status()).toBe(200);
  const auto = await ask(page, "Check DR-009 every weekday at 7 AM CT");
  expect(
    (
      await post(
        page,
        "concierge/" + session + "/actions/" + auto.turn.cards[0].action_id,
        { context: auto.body.context, confirmed: true },
      )
    ).status(),
  ).toBe(200);
  await page.goto("/control/operations");
  await expect(
    page.getByRole("heading", { name: "Operations", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Unknown / not checked", { exact: true }),
  ).toHaveCount(5);
  await page.getByRole("button", { name: "Check source reads" }).click();
  await expect(page.getByText("Available", { exact: true })).toHaveCount(5);
  await expect(page.getByRole("table").first()).toContainText("Concierge");
  await capture(page, "operations");
  await page.getByLabel("Case", { exact: true }).selectOption("CR-017");
  await expect(
    page.getByRole("link", { name: "CR-019 · View run" }),
  ).toHaveCount(0);
  const selectedRow = page.getByRole("row", { name: /^Open run CR-017 / });
  await selectedRow.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", {
      name: "Waiting for human review",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "What each agent did", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Change Impact", exact: true }),
  ).toBeVisible();
  await page.locator("summary").filter({ hasText: "Source reads and service calls" }).click();
  await expect(
    page.getByRole("heading", { name: "Source reads and service calls", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("table").filter({ hasText: "get_change_request" }).first(),
  ).toBeVisible();
  await capture(page, "cr017-run");
  await page
    .getByRole("link", { name: "Open CR-017", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(new RegExp("/cases/CR-017"));
  await expect(page.locator("main")).toContainText(/Customer acceptance/i);
  await page
    .getByRole("link", { name: "View run details", exact: true })
    .click();
  await expect(page).toHaveURL(new RegExp(runs["CR-017"]));
  for (const c of ["CR-019", "QE-004", "DR-009"]) {
    await page.goto("/control/runs/" + runs[c]);
    await expect(
      page.getByRole("heading", { name: "Workflow run", exact: true }),
    ).toBeVisible();
    if (c === "CR-019")
      await expect(
        page.getByRole("heading", {
          name: "Handoff verified · Lab authorization pending",
          exact: true,
        }),
      ).toBeVisible();
    if (c === "QE-004")
      await expect(page.locator("main")).toContainText(/hold/i);
    if (c === "DR-009") {
      await expect(page.locator("main")).toContainText("600");
      await expect(page.locator("main")).toContainText("800");
      await expect(
        page.getByRole("heading", { name: "Execution verified", exact: true }),
      ).toBeVisible();
      await capture(page, "delivery-run");
    }
    await page
      .getByRole("link", { name: "Open " + c, exact: true })
      .first()
      .click();
    await expect(page).toHaveURL(new RegExp("/cases/" + c));
    if (c === "DR-009") {
      await expect(page.locator("main")).toContainText("600");
      await expect(page.locator("main")).toContainText("800");
    }
  }
  await page.goto("/control/decisions");
  await expect(page.locator("main")).toContainText("CR-017");
  await expect(
    page.locator('.cp-decision-row[data-case-id="DR-009"]'),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Executed / Completed", exact: true })
    .click();
  await expect(
    page.locator('.cp-decision-row[data-case-id="DR-009"]'),
  ).toHaveCount(1);
  await page.goto("/control/operations/evals");
  await expect(
    page.getByRole("heading", { name: "Historical full smoke", exact: true }),
  ).toBeVisible();
  await expect(
    page.locator("article").filter({
      has: page.getByRole("heading", {
        name: "Historical full smoke",
        exact: true,
      }),
    }),
  ).toContainText("4/6 — FAIL");
  await expect(
    page.getByRole("heading", {
      name: "Later targeted validation · cr017_covered",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Later targeted validation · cr017_scheduled",
      exact: true,
    }),
  ).toBeVisible();
  await capture(page, "reliability");
  const search = page.getByRole("textbox", { name: "Search Stratos" });
  await search.fill(runs["DR-009"]);
  await page
    .getByRole("button", { name: new RegExp("DR-009 · " + runs["DR-009"]) })
    .click();
  await expect(page).toHaveURL(new RegExp(runs["DR-009"]));
  await page
    .getByRole("link", { name: "Open Concierge session", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Concierge session", exact: true }),
  ).toBeVisible();
  await expect(page.locator("main")).toContainText(/Delivery execute/i);
  await page
    .getByRole("link", { name: "Open saved configuration", exact: true })
    .click();
  await expect(page.locator("main")).toContainText(/not enabled|not active/i);
  await page.goto("/control/overview");
  await expect(page.locator("main")).not.toContainText("Input tokens");
  await expect(page.locator("main")).not.toContainText("Trace ID");
  await page.getByRole("button", { name: /Notifications|alerts/i }).click();
  await expect(
    page
      .getByRole("dialog", { name: "Source alerts" })
      .or(page.getByLabel("Source alerts")),
  ).toContainText("Hard gate failed");
  await page.keyboard.press("Escape");
  await page.goto("/control/programs");
  await expect(page.getByRole("heading").first()).toBeVisible();
  await page.goto("/control/operations");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Operations", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth + 1,
    ),
  ).toBeTruthy();
  await capture(page, "mobile");
});

test("Partial writes and verification mismatches remain distinct", async ({
  page,
}) => {
  test.skip(variant === "base");
  const run = await invoke(page, "DR-009");
  expect((await action(page, "Approve it")).status()).toBe(200);
  await action(page, "Execute approved plan");
  await page.goto("/control/runs/" + run);
  if (variant === "partial") {
    await expect(
      page.getByRole("heading", { name: "Partial execution", exact: true }),
    ).toBeVisible();
    await expect(
      page.locator("article").filter({
        has: page.getByRole("heading", {
          name: "ERP commitment",
          exact: true,
        }),
      }),
    ).toContainText("Verified");
    await expect(
      page.locator("article").filter({
        has: page.getByRole("heading", {
          name: "Planner update",
          exact: true,
        }),
      }),
    ).toContainText("Failed");
  } else {
    await expect(
      page.getByRole("heading", {
        name: "Not verified · Readback mismatch",
        exact: true,
      }),
    ).toBeVisible();
    const erp = page.locator("article").filter({
      has: page.getByRole("heading", { name: "ERP commitment", exact: true }),
    });
    await expect(erp).toContainText("Succeeded");
    await expect(erp).toContainText("Mismatch");
  }
  await capture(page, variant);
  await page.goto("/control/operations");
  await expect(
    page.getByRole("heading", { name: "Run outcomes to review", exact: true }),
  ).toBeVisible();
  await expect(page.locator("main")).toContainText(
    variant === "partial" ? "Partial execution" : "Readback mismatch",
  );
});
