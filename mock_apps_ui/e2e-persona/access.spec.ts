import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { randomUUID } from "node:crypto";
const root = "/control/programs/PRG-A17/cases/";
const names = {
  automation: "Program operator",
  engineer: "Engineering approver",
  program_owner: "Program Owner",
  reader: "Read-only viewer",
};
const matrix = {
  automation: [
    "Overview",
    "Programs",
    "Workflows & Automations",
    "Decisions",
    "Scenarios",
    "Knowledge & Evidence",
    "Operations",
  ],
  engineer: [
    "Overview",
    "Programs",
    "Decisions",
    "Scenarios",
    "Knowledge & Evidence",
  ],
  program_owner: ["Overview", "Programs", "Decisions", "Scenarios"],
  reader: ["Overview", "Programs", "Knowledge & Evidence"],
};
const shots =
  process.env.STRATOS_SCREENSHOT_DIR || "../docs/screenshots/phase10-1";
async function choose(page: Page, role: keyof typeof names) {
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
    .getByRole("dialog", { name: "Demo access" })
    .getByRole("button", { name: new RegExp("^" + names[role]) })
    .click();
  await expect(
    page
      .getByRole("navigation", { name: "Control plane navigation" })
      .getByRole("link"),
  ).toHaveText(matrix[role]);
  await expect(page.locator(".cp-connection")).toContainText("Current read");
}
async function ready(page: Page, path: string) {
  await page.goto(path);
  await expect(
    page
      .getByRole("navigation", { name: "Control plane navigation" })
      .getByRole("link"),
  ).toHaveCount(3);
  await expect(page.locator("main h1")).toBeVisible();
}
async function capture(page: Page, name: string) {
  await page.screenshot({ path: `${shots}/${name}.png` });
}
test.beforeAll(async ({ request }) => {
  await mkdir(shots, { recursive: true });
  for (const [id, w] of [
    ["CR-017", "requirement_change_analysis"],
    ["CR-019", "requirement_change_analysis"],
    ["QE-004", "yield_exception_recovery"],
    ["DR-009", "delivery_readiness"],
  ]) {
    const r = await request.post(`/control-api/cases/${id}/investigations`, {
      headers: {
        Origin: "http://127.0.0.1:5202",
        "X-Stratos-Action": "1",
        "X-Stratos-Demo-Profile": "automation",
      },
      data: {
        invocation_id: "ui_persona_" + randomUUID().replaceAll("-", ""),
        change_id: id,
        workflow_id: w,
      },
    });
    expect(r.status()).toBe(202);
    await expect
      .poll(
        async () => {
          const h = await (
            await request.get("/control-api/cases/CR-017")
          ).json();
          const c = h.case_summaries.find((c: any) => c.change_id === id);
          return (
            c.state !== "investigating" &&
            c.state !== "new" &&
            (id !== "CR-017" || h.proposals.length > 0)
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
        throw Error("No real microphone in automated tests");
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
for (const role of Object.keys(names) as (keyof typeof names)[]) {
  test(`${role}: navigation, search, queues, scoped actions and screenshot`, async ({
    page,
    request,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await ready(page, "/control/overview");
    await choose(page, role);
    await expect(
      page.locator('[data-metric="Needs review"] strong'),
    ).toHaveText(
      role === "engineer" ? "1" : role === "program_owner" ? "2" : "0",
    );
    await capture(page, `overview-${role}-1440`);
    for (const width of [1440, 1280]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 800 });
      for (const name of matrix[role]) {
        await page
          .getByRole("navigation", { name: "Control plane navigation" })
          .getByRole("link", { name, exact: true })
          .click();
        await expect(page.locator("main h1")).toBeVisible();
        await expect(
          page
            .getByRole("navigation", { name: "Control plane navigation" })
            .getByRole("link", { name, exact: true }),
        ).toHaveAttribute("aria-current", "page");
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth + 1,
          ),
        ).toBe(true);
        if (name === "Decisions") {
          const cards = page.locator(".cp-decision-row");
          await expect(cards).toHaveCount(
            role === "engineer" ? 1 : role === "program_owner" ? 2 : 3,
          );
        }
        if (name === "Scenarios")
          await expect(page.locator(".cp-catalog > a")).toHaveCount(
            role === "automation" ? 4 : 2,
          );
      }
    }
    await page.setViewportSize({ width: 1440, height: 900 });
    for (const caseId of ["CR-017", "CR-019", "QE-004", "DR-009"]) {
      await page
        .getByRole("navigation", { name: "Control plane navigation" })
        .getByRole("link", { name: "Programs", exact: true })
        .click();
      await page
        .getByRole("link", { name: /Helios Atlas Inference/ })
        .first()
        .click();
      await page
        .locator(`.cp-connected-cards [data-case-id="${caseId}"]`)
        .click();
      const canInvestigate =
        role !== "reader" && (role !== "program_owner" || caseId !== "CR-019");
      await expect(
        page.getByRole("button", {
          name: /^(Reassess CR-017|Run investigation|Run investigation again|Start connected investigation|Run connected investigation|Run connected delivery analysis)$/,
        }),
      ).toHaveCount(canInvestigate ? 1 : 0);
      await expect(page.getByRole("button", { name: /^Approve/ })).toHaveCount(
        role === "program_owner" && !caseId.startsWith("CR") ? 1 : 0,
      );
      if (role === "reader")
        await expect(
          page.getByRole("button", {
            name: /^(Execute|Reconcile|Retry failed|Prepare)/,
          }),
        ).toHaveCount(0);
      if (role === "program_owner" && caseId === "DR-009") {
        await page.locator("#decision").scrollIntoViewIfNeeded();
        await page
          .getByRole("button", {
            name: "Approve exact commitment",
            exact: true,
          })
          .scrollIntoViewIfNeeded();
        await capture(page, "delivery-decision-program-owner-1440");
      }
    }
    if (role === "engineer" || role === "automation") {
      const h = await (await request.get("/control-api/cases/CR-017")).json();
      const p = h.proposals[0].proposal;
      // Client navigation preserves the selected identity.
      await page
        .getByRole("navigation", { name: "Control plane navigation" })
        .getByRole("link", { name: "Decisions", exact: true })
        .click();
      await page.locator('.cp-decision-row[data-case-id="CR-017"]').click();
      await expect(
        page.getByRole("button", {
          name: "Approve this proposal",
          exact: true,
        }),
      ).toHaveCount(role === "engineer" ? 1 : 0);
      await expect(
        page.getByRole("button", {
          name: "Execute approved proposal",
          exact: true,
        }),
      ).toBeDisabled();
      if (role === "engineer") {
        await page
          .getByRole("heading", { name: "Human decision", exact: true })
          .scrollIntoViewIfNeeded();
        await page
          .getByRole("heading", { name: "Human decision", exact: true })
          .evaluate((el) => el.scrollIntoView({ block: "start" }));
        await capture(page, "engineering-decision-1440");
      }
    }
    await page
      .getByRole("textbox", { name: "Search Stratos", exact: true })
      .fill("Operations");
    if (role !== "automation")
      await expect(
        page.getByRole("option", { name: /Operations/ }),
      ).toHaveCount(0);
    await page.keyboard.press("Escape");
    expect(errors).toEqual([]);
  });
}
test("persona switching removes forbidden route, private draft and late responses", async ({
  page,
}) => {
  await ready(page, "/control/overview");
  await choose(page, "automation");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Workflows & Automations" })
    .click();
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await page.getByLabel("Your draft").fill("Private operator draft");
  await page
    .getByRole("button", { name: "Minimize Stratos Concierge" })
    .click();
  await choose(page, "reader");
  await expect(page).toHaveURL(/\/control\/overview$/);
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await expect(page.getByLabel("Your draft")).toHaveValue("");
  await expect(
    page.getByRole("button", {
      name: /Submit approval|Save configuration|Start investigation/,
    }),
  ).toHaveCount(0);
});
test("anonymous deep links fail closed and keyboard navigation remains usable", async ({
  page,
  request,
}) => {
  for (const path of [
    "workflows",
    "decisions",
    "operations",
    "scenarios",
    "runs/run_guessed",
    "automations/guess",
  ]) {
    await ready(page, "/control/" + path);
    await expect(page).toHaveURL(/\/control\/overview$/);
  }
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Overview", exact: true })
    .focus();
  await page.keyboard.press("Tab");
  await expect(
    page
      .getByRole("navigation", { name: "Control plane navigation" })
      .getByRole("link", { name: "Programs", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/control\/programs$/);
  for (const path of [
    "operations",
    "operations/runs/run_guessed",
    "operations/sessions/chat_guessed",
    "decisions",
    "workflows",
    "automations",
  ])
    expect((await request.get("/control-api/" + path)).status()).toBe(403);
});

test("late operator read cannot repopulate a viewer after identity switch", async ({
  page,
  request,
}) => {
  await ready(page, "/control/overview");
  await choose(page, "automation");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Programs", exact: true })
    .click();
  await page
    .getByRole("link", { name: /Helios Atlas Inference/ })
    .first()
    .click();
  await page.locator('.cp-connected-cards [data-case-id="CR-017"]').click();
  const old = await (
    await request.get("/control-api/cases/CR-017", {
      headers: { "X-Stratos-Demo-Profile": "automation" },
    })
  ).json();
  old.case_summaries.find((c: any) => c.change_id === "CR-017").detail =
    "LATE_OPERATOR_CONTENT";
  let release!: () => void, observed!: () => void;
  const waiting = new Promise<void>((r) => (observed = r)),
    gate = new Promise<void>((r) => (release = r));
  await page.route("**/control-api/cases/CR-017", async (route) => {
    if (route.request().headers()["x-stratos-demo-profile"] === "automation") {
      observed();
      await gate;
      await route.fulfill({ json: old });
    } else await route.continue();
  });
  await page
    .getByRole("button", { name: "Refresh workflow", exact: true })
    .click();
  await waiting;
  await choose(page, "reader");
  const late = page.waitForResponse(
    (r) =>
      r.url().endsWith("/control-api/cases/CR-017") &&
      r.request().headers()["x-stratos-demo-profile"] === "automation",
  );
  release();
  await (await late).finished();
  await expect(
    page.getByLabel("CR-017 current case state").first(),
  ).not.toContainText("LATE_OPERATOR_CONTENT");
  await expect(
    page.getByRole("button", {
      name: /Reassess CR-017|Run investigation|Approve|Execute/,
    }),
  ).toHaveCount(0);
  await page
    .getByRole("textbox", { name: "Search Stratos", exact: true })
    .fill("LATE_OPERATOR_CONTENT");
  await expect(page.getByRole("option")).toHaveCount(0);
});

test("persona change aborts mocked dictation and ignores its late transcript", async ({
  page,
}) => {
  await ready(page, "/control/overview");
  await choose(page, "automation");
  await page.evaluate(() => {
    const state = {
      calls: [] as string[],
      last: null as any,
      late: null as any,
    };
    (window as any).__personaSpeech = state;
    class Recognition {
      onstart: any;
      onresult: any;
      start() {
        state.calls.push("start");
        state.last = this;
        state.late = this.onresult;
      }
      stop() {
        state.calls.push("stop");
      }
      abort() {
        state.calls.push("abort");
      }
    }
    Object.assign(window, {
      SpeechRecognition: Recognition,
      webkitSpeechRecognition: Recognition,
    });
  });
  const posts: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST") posts.push(r.url());
  });
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Dictate to Stratos Concierge", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Before using dictation" }),
  ).toContainText("may send audio to its speech provider");
  await page
    .getByRole("button", { name: "Start dictation", exact: true })
    .click();
  await page.evaluate(() => {
    const r = (window as any).__personaSpeech.last;
    r.onstart?.();
    r.onaudiostart?.();
  });
  await expect(page.locator(".cp-voice-status")).toContainText("Listening");
  await choose(page, "reader");
  expect(
    await page.evaluate(() => (window as any).__personaSpeech.calls),
  ).toEqual(["start", "abort"]);
  await page.evaluate(() =>
    (window as any).__personaSpeech.late?.({
      results: [{ 0: { transcript: "OLD_PRIVATE_DRAFT" }, isFinal: true }],
    }),
  );
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
  await expect(page.getByLabel("Your draft")).toHaveValue("");
  expect(posts).toEqual([]);
});

test("navigation icons, keyboard behavior and requested Overview hierarchy", async ({
  page,
}) => {
  await ready(page, "/control/overview");
  await choose(page, "automation");
  const nav = page.getByRole("navigation", {
    name: "Control plane navigation",
  });
  const links = nav.getByRole("link");
  await expect(links).toHaveText(matrix.automation);
  await expect(nav.locator("svg[aria-hidden=true]")).toHaveCount(7);
  for (const link of await links.all()) {
    expect(await link.getAttribute("aria-label")).toBeNull();
    const dimensions = await link
      .locator("svg")
      .evaluate((el) => ({
        width: el.getBoundingClientRect().width,
        height: el.getBoundingClientRect().height,
        stroke: el.getAttribute("stroke-width"),
        color: getComputedStyle(el).color,
        labelColor: getComputedStyle(el.parentElement!).color,
      }));
    expect(dimensions.width).toBe(17);
    expect(dimensions.height).toBe(17);
    expect(dimensions.stroke).toBe("1.75");
    expect(dimensions.color).toBe(dimensions.labelColor);
  }
  await links.first().focus();
  await page.keyboard.press("Tab");
  await expect(
    nav.getByRole("link", { name: "Programs", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/control\/programs$/);
  await nav.getByRole("link", { name: "Overview", exact: true }).click();
  for (const width of [1440, 1280]) {
    await page.setViewportSize({ width, height: width === 1440 ? 900 : 800 });
    await page.evaluate(() => window.scrollTo(0, 0));
    const hero = await page
      .getByRole("region", { name: "Overview summary" })
      .boundingBox();
    const programs = await page.locator(".cp-overview-section").boundingBox();
    // Read both boxes in one layout snapshot; polling can update the agent card between awaits.
    const [work, attention] = await page.locator(".cp-overview-work").evaluate((el) =>
      [".aw-workspace", ".cp-attention-section"].map(selector =>
        el.querySelector(selector)!.getBoundingClientRect().toJSON()));
    expect(programs!.y).toBeGreaterThanOrEqual(hero!.y + hero!.height);
    expect(work!.y).toBeGreaterThan(programs!.y + programs!.height);
    expect(attention!.y).toBe(work!.y);
    expect(attention!.height).toBeCloseTo(work!.height, 0);
    const surfaces = await page
      .locator(".cp-overview-work > .cp-section")
      .evaluateAll((elements) =>
        elements.map((el) => ({
          background: getComputedStyle(el).backgroundColor,
          border: getComputedStyle(el).borderTopColor,
          radius: getComputedStyle(el).borderRadius,
        })),
      );
    expect(surfaces[0]).toEqual(surfaces[1]);
    expect((await nav.boundingBox())!.height).toBeLessThanOrEqual(54);
    await capture(page, `icons-overview-${width}`);
    await page.screenshot({
      path: `${shots}/overview-${width}-full.png`,
      fullPage: true,
    });
    await page
      .locator(".cp-overview-work")
      .evaluate((el) => el.scrollIntoView({ block: "center" }));
    await capture(page, `matching-panels-${width}`);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(links).toHaveCount(7);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await capture(page, "icons-narrow-390");
});
