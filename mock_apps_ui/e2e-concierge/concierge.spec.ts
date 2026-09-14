import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const root = "/control/programs/PRG-A17/cases/";
async function login(page: Page, role: string) {
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
async function open(page: Page) {
  if (!(await page.locator("#cp-concierge").isVisible()))
    await page
      .getByRole("button", { name: "Open Stratos Concierge", exact: true })
      .click();
}
async function ask(page: Page, text: string) {
  await open(page);
  await page.getByLabel("Your draft").fill(text);
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  const turn = page.locator(".cp-chat-turn").last();
  await expect(turn.locator(".cp-chat-user")).toHaveText(text);
  await expect(turn).not.toContainText("Reading your request", {
    timeout: 20000,
  });
  await expect(turn.locator(".cp-error")).toHaveCount(0);
  return turn;
}
async function capture(page: Page, name: string) {
  await mkdir("../docs/screenshots/phase08-5", { recursive: true });
  await page.screenshot({ path: `../docs/screenshots/phase08-5/${name}.png` });
}
test("connected Concierge operator journey with all four workflows", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/control/overview");
  await login(page, "Program operator");
  const overview = await ask(page, "What needs my attention?");
  await expect(overview).toContainText("do not add the case gaps");
  await expect(overview).toContainText("DR-009");
  await capture(page, "overview");
  await overview
    .getByRole("link", { name: "Open CR-017", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(new RegExp("cases/CR-017"));
  const evidence = await ask(page, "Why is CR-017 still open?");
  await expect(evidence).toContainText("RES-");
  const run = await ask(page, "Reassess CR-017.");
  await expect(run.getByRole("link", { name: "Open run" })).toBeVisible();
  await expect
    .poll(
      async () =>
        (await request.get("/control-api/cases/CR-017"))
          .json()
          .then((s) => s.runs[0]?.status),
      { timeout: 45000 },
    )
    .toBe("completed");
  await run.getByRole("link", { name: "Open run", exact: true }).click();
  await expect(page.locator(".cp-chat-context")).toContainText("CR-017 · Run");
  await page.goto(root + "QE-004");
  const supply = await ask(page, "How much supply is affected?");
  await expect(supply).toContainText("600");
  await expect(supply).toContainText("200");
  const cause = await ask(page, "What caused QE-004?");
  await expect(cause).toContainText("Unresolved");
  await capture(page, "quality");
  await page.goto(root + "DR-009");
  await login(page, "Program operator");
  const readiness = await ask(page, "Can we commit 800 units?");
  for (const value of ["600", "800", "200"])
    await expect(readiness).toContainText(value);
  await ask(page, "Run delivery readiness for DR-009.");
  await expect
    .poll(
      async () =>
        (await request.get("/control-api/cases/DR-009"))
          .json()
          .then((s) => s.runs[0]?.status),
      { timeout: 45000 },
    )
    .toBe("completed");
  let decision = await ask(page, "Commit the 600-unit option.");
  await expect(decision).toContainText(
    "This demo identity cannot perform that action",
  );
  expect(
    (await (await request.get("/control-api/cases/DR-009")).json()).records
      .commitments,
  ).toHaveLength(0);
  // Phase 10.1 removes unauthorized confirmations; the source remains unchanged.
  await expect(
    decision.getByRole("button", { name: "Submit approval" }),
  ).toHaveCount(0);
  await capture(page, "wrong-role");
  await login(page, "Program Owner");
  await open(page);
  decision = await ask(page, "Approve this proposal.");
  await expect(decision).toContainText("Exact source proposal");
  await decision.getByRole("button", { name: "Submit approval" }).click();
  await expect(decision).toContainText("Host action returned");
  expect(
    (await (await request.get("/control-api/cases/DR-009")).json()).records
      .commitments,
  ).toHaveLength(0);
  const execution = await ask(page, "Execute approved plan.");
  await capture(page, "execution-preview");
  await execution
    .getByRole("button", { name: "Execute approved plan" })
    .click();
  await expect(execution).toContainText("Governed action · verified");
  const after = await (await request.get("/control-api/cases/DR-009")).json();
  expect(after.records.commitments[0].quantity).toBe(600);
  expect(after.records.commitments[0].customer_agreement).toBe("pending");
  await page.goto(root + "CR-019");
  await login(page, "Program operator");
  await ask(page, "Process CR-019.");
  await expect
    .poll(
      async () =>
        (await request.get("/control-api/cases/CR-019"))
          .json()
          .then((s) => s.handoffs[0]?.status),
      { timeout: 45000 },
    )
    .toBe("handoff_verified");
  const policy = await ask(page, "Why was this touchless?");
  await expect(policy).toContainText(
    "Intake is separate from lab authorization",
  );
  await capture(page, "standard-handoff");
  await page.goto(root + "DR-009");
  await login(page, "Program operator");
  const automation = await ask(
    page,
    "Check delivery readiness every weekday at 7 AM CT.",
  );
  await expect(automation).toContainText("America/Chicago");
  await automation.getByRole("button", { name: "Save configuration" }).click();
  await expect(automation).toContainText("Background execution is not enabled");
  await capture(page, "automation-saved");
  expect(errors).toEqual([]);
});

test("search, scoped drafts, nonmodal layout and voice never autosend", async ({
  page,
}) => {
  await page.addInitScript(() => {
    class Recognition {
      lang = "";
      continuous = false;
      interimResults = false;
      onstart: any;
      onend: any;
      onresult: any;
      onerror: any;
      start() {
        (window as any).__recognition = this;
        this.onstart?.();
      }
      stop() {
        this.onend?.();
      }
      abort() {
        this.onend?.();
      }
    }
    (window as any).SpeechRecognition = Recognition;
  });
  let sends = 0;
  page.on("request", (r) => {
    if (
      r.url().endsWith("/control-api/concierge/messages") &&
      r.method() === "POST"
    )
      sends++;
  });
  await page.goto(root + "CR-017");
  await open(page);
  await page.getByLabel("Your draft").fill("Approve this");
  await page
    .getByRole("button", { name: "Dictate to Stratos Concierge", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start dictation", exact: true })
    .click();
  await page.evaluate(() => {
    const r = (window as any).__recognition;
    const result = Object.assign([{ transcript: "approve this" }], {
      isFinal: true,
    });
    r.onresult?.({ resultIndex: 0, results: [result] });
  });
  await page
    .getByRole("button", { name: "Stop dictation", exact: true })
    .click();
  await expect(page.getByLabel("Your draft")).toContainText("approve this");
  expect(sends).toBe(0);
  await page
    .getByRole("button", { name: "Minimize Stratos Concierge" })
    .click();
  await page
    .getByRole("link", { name: "Overview", exact: true })
    .first()
    .click();
  await open(page);
  await expect(page.locator(".cp-chat-context")).toContainText("Scope changed");
  await expect(page.getByLabel("Your draft")).toHaveValue("");
  await page
    .getByRole("button", { name: "Minimize Stratos Concierge" })
    .click();
  await page
    .getByRole("textbox", { name: "Search Stratos", exact: true })
    .fill("why is QE-004 blocked");
  const dialog = page.getByRole("dialog", { name: "Search results" });
  await dialog.getByRole("button", { name: /Ask Stratos Concierge/ }).click();
  await expect(page.getByLabel("Your draft")).toHaveValue(
    "why is QE-004 blocked",
  );
  expect(sends).toBe(0);
  await expect(
    page.getByRole("button", { name: "Send message", exact: true }),
  ).toBeEnabled();
  await page.setViewportSize({ width: 390, height: 844 });
  await capture(page, "mobile-draft");
  const box = await page.locator("#cp-concierge").boundingBox();
  expect(box!.width).toBeLessThanOrEqual(390);
  expect(box!.x).toBeGreaterThanOrEqual(0);
});
