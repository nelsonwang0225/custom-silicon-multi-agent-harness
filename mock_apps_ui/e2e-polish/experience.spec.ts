import { test, expect, type Page } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import {
  lifecycle,
  caseFact,
  nextBusinessStep,
} from "../src/control/experience-model";
import type { HostCase } from "../src/control/host";
const program = "/control/programs/PRG-A17",
  root = program + "/cases/",
  shots = "../docs/screenshots/phase09-3";
const read = async (request: any) =>
  (await request.get("/control-api/cases/CR-017")).json();
test.beforeAll(async ({ request }) => {
  for (const id of ["CR-019", "QE-004", "DR-009", "CR-017"]) {
    const response = await request.post(
      `/control-api/cases/${id}/investigations`,
      {
        data: {
          invocation_id: "ui_polish_" + randomUUID().replaceAll("-", ""),
          change_id: id,
          workflow_id:
            id === "QE-004"
              ? "yield_exception_recovery"
              : id === "DR-009"
                ? "delivery_readiness"
                : "requirement_change_analysis",
        },
        headers: {
          Origin: "http://127.0.0.1:5194",
          "X-Stratos-Action": "1",
          "X-Stratos-Demo-Profile": "automation",
        },
      },
    );
    expect(response.status()).toBe(202);
    const run = (await response.json()).run_id;
    await expect
      .poll(
        async () => {
          const data = await read(request),
            summary = data.case_summaries.find((s: any) => s.change_id === id);
          return (
            summary.run_id === run &&
            summary.state !== "investigating" &&
            (id !== "CR-017" || data.proposals.length > 0)
          );
        },
        { timeout: 45000 },
      )
      .toBe(true);
  }
});
test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    class MockSpeech {
      start() {
        throw Error("No real microphone or external speech in polish tests");
      }
      stop() {}
      abort() {}
    }
    Object.assign(window, {
      SpeechRecognition: MockSpeech,
      webkitSpeechRecognition: MockSpeech,
    });
  });
});
async function ready(page: Page, path: string) {
  await page.goto(path);
  await expect(page.locator("main h1")).toBeVisible();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  await expect
    .poll(async () => page.locator("body").innerText())
    .not.toContain("Reading current workflow state…");
  await page.waitForLoadState("networkidle");
}
async function capture(page: Page, name: string) {
  await mkdir(shots, { recursive: true });
  await page.screenshot({ path: `${shots}/${name}.png` });
}
async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth + 1,
    ),
  ).toBe(true);
}

test("current-source visuals preserve scope, uncertainty, stale approval and partial readback", async ({
  request,
}) => {
  const h: HostCase = await read(request);
  const dr = h.case_summaries!.find((s) => s.change_id === "DR-009")!;
  expect(caseFact(h, dr)).toBe("600 / 800 eligible · 200 gap");
  expect(nextBusinessStep(h, dr)).toBe("Program Owner decision required");
  expect(
    lifecycle(h, "CR-017").find((s) => s.label === "Lab result")?.state,
  ).toBe("pending");
  expect(lifecycle(h, "CR-019").find((s) => s.label === "Intake")?.state).toBe(
    "done",
  );
  expect(
    lifecycle(h, "CR-019").find((s) => s.label === "Lab authority"),
  ).toBeUndefined();
  expect(
    lifecycle(h, "QE-004").find((s) => s.label === "Quality disposition"),
  ).toBeUndefined();
  const stale = structuredClone(h);
  stale.case_summaries!.find((s) => s.change_id === "DR-009")!.state = "stale";
  expect(lifecycle(stale, "DR-009").some((s) => s.state === "done")).toBe(
    false,
  );
  const partial = structuredClone(h);
  partial.case_summaries!.find((s) => s.change_id === "DR-009")!.state =
    "partial_failure";
  expect(
    lifecycle(partial, "DR-009").find((s) => s.label === "ERP + Planner"),
  ).toMatchObject({ state: "failed", detail: "Partial execution · Reconcile" });
});

test("a new standard investigation keeps the prior handoff explicitly historical", async ({ page, request }) => {
  const h = await read(request);
  const prior = h.standard.handoffs[0];
  expect(prior.status).toBe("handoff_verified");
  h.standard.runs.unshift({ ...h.standard.runs[0], run_id: "run_current_pending", status: "running", recommendation: null, specialists: [], completed_at: null });
  h.standard.status = "Assessing applicability";
  Object.assign(h.case_summaries.find((s: any) => s.change_id === "CR-019"), {
    state: "investigating", state_label: "Investigating", run_id: "run_current_pending",
    detail: "Agent investigation is running; no new business outcome is implied.",
  });
  await page.route("**/control-api/cases/CR-017", route => route.fulfill({ json: h }));
  await ready(page, root + "CR-019");
  await expect(page.getByLabel("CR-019 current case state")).toContainText("Investigating");
  await expect(page.getByLabel("Standard policy and handoff")).toContainText("Package pending");
  await expect(page.getByLabel("Standard policy and handoff")).toContainText("Not assessed");
  await expect(page.getByLabel("Standard policy and handoff")).toContainText("0 reusable records");
  await expect(page.getByLabel("Standard policy and handoff")).toContainText("Historical evidence not assessed");
  await expect(page.getByLabel("Standard policy and handoff")).not.toContainText("18 / 18 checks match");
  await expect(page.getByLabel("Standard policy and handoff")).not.toContainText("Approved profile and procedure");
  await expect(page.getByRole("link", { name: "Inspect policy checks" })).toHaveCount(0);
  await expect(page.getByLabel("CR-019 lifecycle")).toContainText("Not verified");
  await expect(page.getByRole("heading", { name: "Handoff package", exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Inspect the previous run’s handoff result" })).toHaveAttribute("href", `${root}CR-019?tab=activity&run=${prior.run_id}`);
  await expect(page.getByLabel("Standard policy and handoff")).not.toContainText("Workflow complete");
  await expect(page.getByText("The Coordinator is checking the request. Recorded activity updates automatically.")).toBeVisible();
});

test("another case running does not relabel the verified standard case", async ({ page, request }) => {
  const h = await read(request);
  h.runs[0].status = "running";
  await page.route("**/control-api/cases/CR-017", route => route.fulfill({ json: h }));
  await ready(page, root + "CR-019");
  await expect(page.getByLabel("CR-019 current case state")).toContainText("Workflow complete");
  await expect(page.getByLabel("CR-019 current case state")).toContainText("Lab authorization owned by Validation Operations");
  await expect(page.getByLabel("Standard policy and handoff")).toContainText("Handoff verified");
  await expect(page.getByRole("button", { name: "Investigating…", exact: true })).toHaveCount(0);
});

test("business hierarchy and source-backed case visuals across three desktop sizes", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const h = await read(request),
    a = h.delivery.context.analysis;
  const observations = [];
  for (const [width, height] of [
    [1440, 900],
    [1920, 1080],
    [1280, 800],
  ]) {
    await page.setViewportSize({ width, height });
    for (const [route, name] of [
      ["/control/overview", "overview"],
      [program, "program"],
      ...["CR-017", "CR-019", "QE-004", "DR-009"].map((id) => [
        root + id,
        id.toLowerCase(),
      ]),
      ["/control/decisions", "decisions"],
      ["/control/workflows", "workflows"],
      ["/control/operations", "operations"],
    ]) {
      await ready(page, route);
      await noOverflow(page);
      if (name === "program") {
        const cards = page
          .getByLabel("Connected workflow cases")
          .locator("[data-case-id]");
        await expect(cards).toHaveCount(4);
        if (width >= 1440)
          for (const card of await cards.all())
            await expect(card).toBeInViewport({ ratio: 0.99 });
      }
      if (name === "dr-009") {
        const visual = page.getByLabel("Delivery inventory reconciliation");
        await expect(visual).toContainText(
          `${a.physical_total.toLocaleString()} units`,
        );
        await expect(visual).toContainText(
          `${a.eligible_quantity} / ${a.requested_quantity}`,
        );
        await expect(visual).toContainText(`${a.gap_quantity} unit gap`);
        await expect(visual.getByRole("img")).toHaveAccessibleName(
          "600 eligible, 250 held, 150 allocated",
        );
      }
      if (name === "cr-017") {
        await expect(
          page.getByLabel("Requirement and evidence comparison"),
        ).toContainText("60 / 480");
        await expect(page.getByLabel("CR-017 lifecycle")).toContainText(
          "Customer acceptance pending",
        );
      }
      if (name === "cr-019")
        await expect(
          page.getByLabel("Standard policy and handoff"),
        ).toContainText("Handoff verified");
      await capture(page, `${name}-${width}`);
      observations.push({ name, width, height, url: page.url() });
    }
  }
  expect(errors).toEqual([]);
  await writeFile(
    `${shots}/capture-index.json`,
    JSON.stringify(observations, null, 2),
  );
});

test("exact decision navigation, actionable identity switch and evidence focus recovery", async ({
  page,
  request,
}) => {
  const before = await read(request);
  await ready(page, "/control/decisions");
  await page.locator('.cp-decision-row[data-case-id="DR-009"]').click();
  await expect(page).toHaveURL(/\/cases\/DR-009\?plan=.+#decision$/);
  await expect(page.locator("#decision")).toBeFocused();
  await expect(
    page.getByRole("heading", { name: "Human commitment decision" }),
  ).toBeInViewport();
  await expect(
    page.getByRole("button", { name: "Approve exact commitment", exact: true }),
  ).toBeDisabled();
  const exact = page.url();
  await page
    .locator(".cp-section")
    .filter({
      has: page.getByRole("heading", { name: "Human commitment decision" }),
    })
    .getByRole("button", { name: "Switch identity", exact: false })
    .first()
    .click();
  const dialog = page.getByRole("dialog", { name: "Demo access" });
  await expect(dialog).toContainText("Cannot release held material");
  await expect(dialog.getByRole("button")).toHaveCount(6);
  await capture(page, "persona-selector-1440");
  await dialog.getByRole("button", { name: /^Program Owner/ }).click();
  await expect(page).toHaveURL(exact);
  await expect(
    page.getByRole("button", { name: "Demo profile", exact: true }),
  ).toContainText("Program Owner");
  await expect(
    page.getByRole("button", { name: "Approve exact commitment", exact: true }),
  ).toBeEnabled();
  const after = await read(request);
  expect(after.delivery.records.decisions).toEqual(
    before.delivery.records.decisions,
  );
  expect(after.delivery.records.commitments).toEqual(
    before.delivery.records.commitments,
  );
  await ready(page, root + "CR-017");
  const link = page.getByRole("link", {
    name: "Inspect RES-SHORT-B",
    exact: true,
  });
  await link.click();
  await expect(page.getByRole("dialog")).toContainText(
    "60 minutes observed; 480 minutes requested",
  );
  await capture(page, "evidence-1440");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(link).toBeFocused();
});

test("Concierge stays floating, context accurate, structured reply bounded and keyboard/zoom usable", async ({
  page,
}) => {
  await ready(page, program);
  await expect(page.locator(".cp-concierge-dock")).toHaveClass(
    /cp-dock-minimal/,
  );
  const launch = page.getByRole("button", { name: "Open Stratos Concierge" });
  await launch.click();
  const chat = page.getByRole("complementary", { name: "Stratos Concierge" });
  await expect(chat).toContainText(
    "4 connected cases · 3 decisions need review",
  );
  await expect(chat).not.toContainText("CR-017 · No connected run");
  await page.getByLabel("Your draft").fill("What is the status of DR-009?");
  await page.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(chat.locator(".cp-chat-card").first()).toBeVisible({
    timeout: 20000,
  });
  await capture(page, "concierge-1440");
  await page.keyboard.press("Escape");
  await expect(launch).toBeFocused();
  for (const [width, height] of [
    [1920, 1080],
    [1280, 800],
  ]) {
    await page.setViewportSize({ width, height });
    await launch.click();
    await expect(page.getByLabel("Your draft")).toBeInViewport({ ratio: 1 });
    await noOverflow(page);
    await capture(page, `concierge-${width}`);
    await page.keyboard.press("Escape");
  }
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  await launch.click();
  await expect(page.getByLabel("Your draft")).toBeInViewport({ ratio: 1 });
  await expect(
    page.getByRole("button", { name: "Minimize Stratos Concierge" }),
  ).toBeInViewport();
  await noOverflow(page);
  await capture(page, "concierge-200-percent-zoom");
});

test("source outages keep actions unavailable and remove current lifecycle claims", async ({
  page,
}) => {
  await ready(page, root + "CR-017");
  await page.route("**/control-api/cases/CR-017", (route) =>
    route.abort("failed"),
  );
  await page
    .getByRole("button", { name: "Refresh workflow", exact: false })
    .click();
  const outcome = page.getByLabel("CR-017 current case state");
  await expect(outcome).toContainText("Stale read · Refresh required");
  await expect(page.getByLabel("CR-017 lifecycle")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Reassess CR-017", exact: true }),
  ).toBeDisabled();
  await expect(page.locator(".cp-action-access").first()).toContainText(
    "Source connection unavailable",
  );
  await capture(page, "source-unavailable-1440");
});
