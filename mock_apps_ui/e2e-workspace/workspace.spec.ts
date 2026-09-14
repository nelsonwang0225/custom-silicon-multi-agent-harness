// Explicitly synthetic display fixtures over isolated deterministic HTTP runs.
// Captures demonstrate UI behavior, not fresh paid model execution.
import { test, expect, type Page, type Route } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
const shots =
  process.env.STRATOS_SCREENSHOT_DIR ||
  "../docs/screenshots/phase10-2/fixtures";
let idle: any, recorded: any, cr017: any, cr019: any;
const headers = {
  Origin: "http://127.0.0.1:5204",
  "X-Stratos-Action": "1",
  "X-Stratos-Demo-Profile": "automation",
};
const clone = (v: any) => structuredClone(v);
const node = (page: Page, id: string) =>
  page.locator(`[data-agent-id="${id}"]`);
const workspace = (page: Page) => page.locator(".aw-workspace");
async function ready(page: Page) {
  await page.goto("/control/overview");
  await expect(workspace(page)).toBeVisible();
  await expect(
    page.getByRole("combobox", { name: "Agent work scope" }),
  ).toBeEnabled();
}
async function choose(page: Page, role = "Program operator") {
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
    .getByRole("button", { name: new RegExp("^" + role) })
    .click();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
}
async function fixture(
  page: Page,
  value: any,
  options: { count?: () => void } = {},
) {
  await page.route("**/control-api/agent-workspace*", async (route) => {
    options.count?.();
    const v = clone(value);
    v.read_at = new Date().toISOString();
    const selection = new URL(route.request().url()).searchParams.get("run_id");
    if (selection) v.selected_run_id = selection === "all" ? null : selection;
    if (route.request().headers()["x-stratos-demo-profile"] !== "automation")
      for (const r of v.runs)
        r.links = r.links.filter((l: any) => l.label !== "View run");
    await route.fulfill({ json: v });
  });
}
function parallel() {
  const v = clone(recorded),
    r = clone(cr017);
  v.runs = [r];
  v.selected_run_id = r.run_id;
  v.active_run_count = 1;
  v.total_permitted_runs = 1;
  r.status = "running";
  r.completed_at = null;
  r.telemetry = "current";
  r.observed_at = new Date().toISOString();
  r.handoff = null;
  for (const a of r.agents) {
    if (
      ["coordinator", "validation_evidence", "program_commercial"].includes(
        a.id,
      )
    ) {
      a.state = a.id === "coordinator" ? "delegated" : "working";
      a.label = a.id === "coordinator" ? "With specialists" : "Investigating";
      a.tasks = [
        {
          invocation_id: a.id + "_fixture",
          state: a.state,
          label: a.label,
          observed_at: r.observed_at,
          finding: null,
          evidence: [],
          dependencies: [],
          error: null,
        },
      ];
    }
  }
  return v;
}
async function capture(page: Page, name: string) {
  await page.screenshot({ path: `${shots}/${name}.png` });
}
async function fits(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
}
test.beforeAll(async ({ request }) => {
  await mkdir(shots, { recursive: true });
  idle = await (await request.get("/control-api/agent-workspace")).json();
  const initial = clone(idle);
  idle.runs = [];
  idle.total_permitted_runs = 0;
  idle.active_run_count = 0;
  idle.selected_run_id = null;
  for (const id of ["CR-017", "CR-019"]) {
    if (
      initial.runs.some(
        (r: any) =>
          r.case_id === id &&
          r.handoff?.label.includes(
            id === "CR-017" ? "Awaiting Engineering" : "Handoff verified",
          ),
      )
    )
      continue;
    const r = await request.post(`/control-api/cases/${id}/investigations`, {
      headers,
      data: {
        invocation_id: "ui_workspace_" + randomUUID().replaceAll("-", ""),
        change_id: id,
        workflow_id: "requirement_change_analysis",
      },
    });
    expect(r.status(), await r.text()).toBe(202);
    await expect
      .poll(
        async () => {
          recorded = await (
            await request.get("/control-api/agent-workspace", { headers })
          ).json();
          return recorded.runs.find((r: any) => r.case_id === id)?.handoff
            ?.label;
        },
        { timeout: 45000 },
      )
      .toContain(id === "CR-017" ? "Awaiting Engineering" : "Handoff verified");
  }
  recorded = await (
    await request.get("/control-api/agent-workspace", { headers })
  ).json();
  recorded.runs = recorded.runs.filter((r: any) =>
    ["human", "external"].includes(r.handoff?.kind),
  );
  recorded.selected_run_id = recorded.runs.find(
    (r: any) => r.case_id === "CR-019",
  ).run_id;
  cr017 = recorded.runs.find((r: any) => r.case_id === "CR-017");
  cr019 = recorded.runs.find((r: any) => r.case_id === "CR-019");
  await writeFile(
    "../.cache/phase10-2/browser-fixture-provenance.json",
    JSON.stringify(
      {
        description:
          "Isolated HTTP investigations using existing deterministic SDK doubles. Running/error/stale/multirun are browser response fixtures. No paid model or speech.",
        idle,
        recorded,
      },
      null,
      2,
    ),
  );
});
test.beforeEach(async ({ context }) => {
  // These response fixtures exercise roster/telemetry states without starting
  // an opening. The autonomous suite covers the enabled entry lifecycle.
  await context.route('**/control-api/demo', route => route.fulfill({json:{enabled:false}}));
  await context.addInitScript(() => {
    class NoSpeech {
      start() {
        throw Error("Real speech prohibited");
      }
      stop() {}
      abort() {}
    }
    Object.assign(window, {
      SpeechRecognition: NoSpeech,
      webkitSpeechRecognition: NoSpeech,
    });
  });
});
test("known idle keeps the muted roster, health separation and 1440 layout", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const writes: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST") writes.push(r.url());
  });
  await fixture(page, idle);
  await ready(page);
  await expect(workspace(page)).toContainText("No active investigation");
  await expect(workspace(page).locator('[data-display-state="idle"]')).toHaveCount(5);
  await expect(workspace(page).locator(".aw-flowing, .aw-relationship-lines circle")).toHaveCount(0);
  const a = await workspace(page).boundingBox(),
    b = await page
      .locator(".cp-overview-work > .cp-section")
      .nth(1)
      .boundingBox();
  expect(a!.x).toBeLessThan(b!.x);
  expect(a!.width).toBeGreaterThan(b!.width);
  await capture(page, "idle-1440x900");
  await fits(page);
  await page
    .getByRole("button", { name: "Workspace telemetry details" })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "Deterministic test runtime",
  );
  await expect(page.getByRole("dialog")).toContainText("Not checked");
  await expect(
    page.getByRole("dialog").getByRole("link", { name: "Open Operations" }),
  ).toHaveCount(0);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
test("two observed parallel tasks, completed peer, static participation, 1280 layout", async ({
  page,
}) => {
  await fixture(page, parallel());
  await ready(page);
  await expect(workspace(page).locator('[data-state="working"]')).toHaveCount(
    2,
  );
  await expect(node(page, "coordinator")).toHaveAttribute(
    "data-state",
    "delegated",
  );
  await expect(node(page, "change_impact")).toHaveAttribute(
    "data-state",
    "completed",
  );
  await expect(workspace(page)).toContainText("CR-017");
  expect(
    await node(page, "validation_evidence")
      .locator(".aw-ring")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("aw-observed");
  await expect(workspace(page).locator(".aw-flowing")).toHaveCount(2);
  expect(await workspace(page).locator(".aw-flowing circle").first().evaluate(el => getComputedStyle(el).animationName)).toBe("aw-delegation");
  await capture(page, "parallel-1440x900");
  await page.setViewportSize({ width: 1280, height: 800 });
  // The explicit follow-up moves Programs above this row; inspect its local viewport.
  await workspace(page).evaluate((el) =>
    el.scrollIntoView({ block: "center" }),
  );
  await capture(page, "parallel-1280x800");
  await fits(page);
  const footer = await page.locator(".aw-handoff").boundingBox();
  expect(footer!.y + footer!.height).toBeLessThanOrEqual(800);
});
test("completed human handoff and exact actor-specific review", async ({
  page,
}) => {
  const v = clone(recorded);
  v.selected_run_id = cr017.run_id;
  await fixture(page, v);
  await ready(page);
  await expect(workspace(page)).toContainText("Awaiting Engineering review");
  await expect(workspace(page).locator('[data-state="working"]')).toHaveCount(
    0,
  );
  await capture(page, "human-handoff-1440x900");
  await choose(page, "Engineering approver");
  await expect(workspace(page)).toContainText("Awaiting your review");
  await expect(
    page.getByRole("link", { name: "Inspect your exact decision" }),
  ).toBeVisible();
  await node(page, "validation_evidence").click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Sources consulted");
  await expect(dialog).toContainText("content v");
  await expect(
    dialog.getByRole("link", { name: "View run", exact: true }),
  ).toHaveCount(0);
  await capture(page, "business-inspector-1440x900");
});
test("exact proposal mismatch cannot claim awaiting your review", async ({
  page,
}) => {
  const v = clone(recorded);
  v.selected_run_id = cr017.run_id;
  v.runs.find((r: any) => r.run_id === cr017.run_id).handoff.digest =
    "superseded-fixture";
  await fixture(page, v);
  await ready(page);
  await choose(page, "Engineering approver");
  await expect(workspace(page)).toContainText("Awaiting Engineering review");
  await expect(
    page.getByRole("link", { name: "Inspect your exact decision" }),
  ).toHaveCount(0);
});
test("failed invocation preserves another specialist finding", async ({
  page,
}) => {
  const v = parallel(),
    r = v.runs[0];
  r.status = "failed";
  r.telemetry = "recorded";
  r.handoff = {
    kind: "attention",
    label: "Investigation incomplete · Inspect findings",
  };
  const failure = r.agents.find((a: any) => a.id === "validation_evidence");
  failure.state = "failed";
  failure.label = "Task failed";
  failure.tasks[0].state = "failed";
  failure.tasks[0].label = "Task failed";
  failure.tasks[0].error = "Specialist invocation failed";
  for (const a of r.agents.filter((a: any) =>
    ["coordinator", "program_commercial"].includes(a.id),
  )) {
    a.state = "unknown";
    a.label = "No current observation";
  }
  await fixture(page, v);
  await ready(page);
  await expect(node(page, "validation_evidence")).toHaveAttribute(
    "data-state",
    "failed",
  );
  await capture(page, "failed-specialist-1440x900");
  await node(page, "change_impact").click();
  await expect(page.getByRole("dialog")).toContainText(
    cr017.agents.find((a: any) => a.id === "change_impact").tasks[0].finding,
  );
});
test("stale and missing telemetry never animate or imply idle", async ({
  page,
}) => {
  const v = parallel();
  v.runs[0].telemetry = "stale";
  for (const a of v.runs[0].agents.filter((a: any) =>
    ["working", "delegated"].includes(a.state),
  )) {
    a.state = "unknown";
    a.label = "Observation stale";
  }
  await fixture(page, v);
  await ready(page);
  await expect(workspace(page).locator(".aw-processing")).toHaveCount(0);
  await expect(workspace(page).locator(".aw-flowing")).toHaveCount(0);
  await capture(page, "stale-1440x900");
  await page.unroute("**/control-api/agent-workspace*");
  await page.route("**/control-api/agent-workspace*", (r) =>
    r.fulfill({ status: 503, json: { detail: "Telemetry unavailable" } }),
  );
  await page.getByRole("button", { name: "Refresh agent activity" }).click();
  await expect(workspace(page).locator('[data-state="unknown"]')).toHaveCount(
    5,
  );
  await expect(workspace(page)).toContainText("Current activity unavailable");
  await capture(page, "unavailable-1440x900");
});
test("concurrent run selection does not blend findings or silently switch", async ({
  page,
}) => {
  const v = parallel(),
    second = clone(v.runs[0]);
  second.run_id = cr019.run_id;
  second.case_id = "CR-019";
  second.links = cr019.links;
  second.agents.find((a: any) => a.id === "change_impact").tasks[0].finding =
    "SECOND RUN ONLY — illustrative fixture";
  v.runs.push(second);
  v.active_run_count = 2;
  v.total_permitted_runs = 2;
  await fixture(page, v);
  await ready(page);
  await expect(workspace(page)).toContainText("2 Active runs");
  await expect(page.getByRole("combobox", { name: "Agent work scope" }).locator('option[value="all"]')).toHaveCount(0);
  await expect(node(page, "validation_evidence")).toContainText("1 active task");
  await node(page, "change_impact").click();
  await expect(page.getByRole("dialog")).not.toContainText("SECOND RUN ONLY");
  await page.keyboard.press("Escape");
  await page.getByRole("combobox", {name: "Agent work scope"}).selectOption(second.run_id);
  await node(page, "change_impact").click();
  await expect(page.getByRole("dialog")).toContainText("SECOND RUN ONLY");
  await page.keyboard.press("Escape");
  await page.getByRole("combobox", {name: "Agent work scope"}).selectOption(cr017.run_id);
  await expect(workspace(page)).toHaveAttribute("data-selection", cr017.run_id);
  await node(page, "change_impact").click();
  await expect(page.getByRole("dialog")).not.toContainText("SECOND RUN ONLY");
  await expect(workspace(page)).toHaveAttribute("data-selection", cr017.run_id);
  await page.keyboard.press("Escape");
  v.runs[0].status = "completed";
  v.runs[0].telemetry = "recorded";
  v.selected_run_id = second.run_id;
  v.active_run_count = 1;
  await page.getByRole("button", {name: "Refresh agent activity"}).click();
  await expect(workspace(page)).toHaveAttribute("data-selection", cr017.run_id);
  await page.getByRole("button", {name: "Back to live activity", exact: true}).click();
  await expect(workspace(page)).toHaveAttribute("data-selection", second.run_id);
});
test("CR-019 verified handoff keeps lab pending for reader", async ({
  page,
}) => {
  await fixture(page, recorded);
  await ready(page);
  await expect(workspace(page)).toContainText(
    "Handoff verified · Lab authorization pending",
  );
  await expect(workspace(page).locator('[data-state="working"]')).toHaveCount(
    0,
  );
  await capture(page, "standard-handoff-1440x900");
  await node(page, "coordinator").click();
  const d = page.getByRole("dialog");
  await expect(
    d.getByRole("link", { name: "Open case", exact: true }),
  ).toBeVisible();
  await expect(
    d.getByRole("link", { name: "View run", exact: true }),
  ).toHaveCount(0);
  await expect(
    d.getByRole("button", { name: /Approve|Execute|Start agent/ }),
  ).toHaveCount(0);
});
test("Explain opens one editable contextual draft, does not send or replay on return", async ({
  page,
}) => {
  await fixture(page, recorded);
  await ready(page);
  await choose(page);
  const writes: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST") writes.push(r.url());
  });
  await node(page, "coordinator").click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("link", { name: "View run", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Explain in Concierge", exact: true })
    .click();
  const draft = page.locator(".cp-chat-window textarea");
  await expect(draft).toHaveValue(new RegExp(cr019.run_id));
  const value = await draft.inputValue();
  await draft.fill(value + "\nEditable local addition");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Overview", exact: true })
    .click();
  await page.goBack();
  await expect(draft).toHaveValue(value + "\nEditable local addition");
  expect(writes).toEqual([]);
});
test("poll only active selection, pause hidden, expire read and retain recorded result", async ({
  page,
}) => {
  let count = 0;
  await fixture(page, parallel(), { count: () => count++ });
  await ready(page);
  await page.clock.install();
  let before = count;
  await page.clock.runFor(6500);
  await expect.poll(() => count).toBeGreaterThan(before);
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(workspace(page).locator(".aw-processing")).toHaveCount(0);
  before = count;
  await page.clock.runFor(9500);
  expect(count).toBe(before);
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect.poll(() => count).toBeGreaterThan(before);
  await page.unroute("**/control-api/agent-workspace*");
  await fixture(page, recorded, { count: () => count++ });
  await page.getByRole("button", { name: "Refresh agent activity" }).click();
  await expect(workspace(page).locator(".aw-processing")).toHaveCount(0);
  await expect(node(page, "coordinator")).toHaveAttribute("data-state", "completed");
  before = count;
  await page.clock.runFor(6500);
  expect(count).toBe(before);
  await page.clock.runFor(31000);
  await expect(workspace(page)).toContainText("Read out of date");
  await expect(node(page, "coordinator")).toHaveAttribute(
    "data-state",
    "completed",
  );
});
test("persona switch and reset clear inspector, old selection and delayed response", async ({
  page,
}) => {
  await fixture(page, recorded);
  await ready(page);
  await choose(page);
  await node(page, "coordinator").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.evaluate(() =>
    window.dispatchEvent(new Event("stratos:demo-reset")),
  );
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("combobox", { name: "Agent work scope" }),
  ).toBeEnabled();
  await choose(page); // Existing reset boundary also clears the selected demo persona.
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let pending = false;
  await page.route("**/control-api/agent-workspace*", async (route: Route) => {
    if (route.request().headers()["x-stratos-demo-profile"] === "automation") {
      pending = true;
      await gate;
      const v = clone(recorded);
      v.runs[0].agents[0].tasks[0].finding = "OLD PRIVATE RESPONSE";
      await route.fulfill({ json: v });
    } else await route.fallback();
  });
  await page.getByRole("button", { name: "Refresh agent activity" }).click();
  await expect.poll(() => pending).toBe(true);
  await choose(page, "Read-only viewer");
  release();
  await expect(
    page.getByRole("combobox", { name: "Agent work scope" }),
  ).toBeEnabled();
  await node(page, "coordinator").click();
  await expect(page.getByRole("dialog")).not.toContainText(
    "OLD PRIVATE RESPONSE",
  );
  await expect(
    page
      .getByRole("dialog")
      .getByRole("link", { name: "View run", exact: true }),
  ).toHaveCount(0);
});
test("narrow, enlarged text and reduced motion remain readable", async ({
  page,
}) => {
  await fixture(page, parallel());
  await ready(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  expect(
    await node(page, "validation_evidence")
      .locator(".aw-ring")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("none");
  expect(await workspace(page).locator(".aw-flowing circle").first().evaluate(el => getComputedStyle(el).animationName)).toBe("none");
  await capture(page, "reduced-motion-1440x900");
  await page.setViewportSize({ width: 390, height: 844 });
  await workspace(page).evaluate((el) =>
    el.scrollIntoView({ block: "center" }),
  );
  await capture(page, "narrow-390x844");
  await fits(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.addStyleTag({
    content:
      ".cp-root .aw-agent-copy strong{font-size:22px}.cp-root .aw-agent-copy>span{font-size:20px}.cp-root .aw-heading h2{font-size:30px}.cp-root .aw-scope select,.cp-root .aw-handoff{font-size:20px}",
  });
  await capture(page, "enlarged-text-1440x900");
  await fits(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await workspace(page).evaluate((el) =>
    el.scrollIntoView({ block: "center" }),
  );
  await capture(page, "narrow-enlarged-text-390x844");
  await fits(page);
  for (const id of [
    "coordinator",
    "change_impact",
    "validation_evidence",
    "program_commercial",
    "manufacturing",
  ])
    await expect(node(page, id)).toBeVisible();
  await node(page, "validation_evidence").click();
  await capture(page, "narrow-inspector-390x844");
  await fits(page);
});


test("compact monitor uses scoped counts and checkpoint observations", async ({ page }) => {
  const v = parallel();
  await fixture(page, v);
  await ready(page);
  const metrics = workspace(page).locator(".aw-metrics");
  await expect(metrics.locator("strong")).toHaveText(["1", "2", "0"]);
  await expect(workspace(page).locator(".aw-count-scope")).toContainText("CR-017 · Selected run");
  await expect(workspace(page).locator(".aw-observation")).toHaveCount(5);
  await expect(workspace(page).locator(".aw-observation").first()).toHaveAttribute("title", /Latest checkpoint observation/);
  await expect(workspace(page).locator(".aw-observation time").first()).toHaveAttribute("datetime", v.runs[0].observed_at);
  const boxes = await workspace(page).locator(".aw-agent").evaluateAll((elements) => elements.map((el) => ({ y: el.getBoundingClientRect().y, width: el.getBoundingClientRect().width })));
  expect(boxes[0].y).toBeLessThan(boxes[1].y);
  expect(new Set(boxes.slice(1).map((box) => Math.round(box.y))).size).toBe(1);
  await expect(workspace(page).locator("[data-connection]")).toHaveCount(4);
  expect(Math.max(...boxes.slice(1).map((b) => b.width)) - Math.min(...boxes.slice(1).map((b) => b.width))).toBeLessThan(1);
  await workspace(page).locator(".aw-observation").first().focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(workspace(page).locator(".aw-observation").first()).toBeFocused();
  for (const [width, height] of [[1440,900], [1920,1080], [1280,800], [390,844]]) {
    await page.setViewportSize({width, height});
    await workspace(page).evaluate((el) => el.scrollIntoView({block:"center"}));
    await fits(page);
    await capture(page, `monitor-${width}x${height}`);
  }
  await page.unroute("**/control-api/agent-workspace*");
  v.runs[0].telemetry = "stale";
  for (const agent of v.runs[0].agents) { agent.state = "unknown"; agent.label = "Observation stale"; }
  await fixture(page, v);
  await page.getByRole("button", {name: "Refresh agent activity"}).click();
  await expect(metrics.locator("strong")).toHaveText(["—", "—", "—"]);
  await expect(workspace(page).locator(".aw-processing")).toHaveCount(0);
  await expect(workspace(page).locator(".aw-count-scope")).toContainText("Counts unavailable");
});


test("only active colored branches move; completed and idle observations stop", async ({ page }) => {
  const active = parallel();
  for (const agent of active.runs[0].agents) { agent.state = "working"; for (const task of agent.tasks) task.state = "working"; }
  await fixture(page, active);
  await ready(page);
  await expect(workspace(page).locator(".aw-flowing")).toHaveCount(4);
  await expect(workspace(page).locator("[data-peer], .aw-peer-key, .aw-motion-note")).toHaveCount(0);
  const dots = workspace(page).locator(".aw-flowing circle");
  expect(new Set(await dots.evaluateAll(nodes => nodes.map(el => getComputedStyle(el).fill))).size).toBe(4);
  const before = await dots.evaluateAll(nodes => nodes.map(el => getComputedStyle(el).offsetDistance));
  await expect.poll(async () => (await dots.evaluateAll(nodes => nodes.map(el => getComputedStyle(el).offsetDistance))).every((v,i) => v !== before[i])).toBe(true);
  await page.emulateMedia({reducedMotion:"reduce"});
  expect(await dots.evaluateAll(nodes => nodes.map(el => getComputedStyle(el).animationName))).toEqual(["none", "none", "none", "none"]);
  await page.unroute("**/control-api/agent-workspace*");
  await fixture(page, recorded);
  await page.getByRole("button", { name: "Refresh agent activity" }).click();
  await expect(workspace(page).locator(".aw-flowing")).toHaveCount(0);
  await page.unroute("**/control-api/agent-workspace*");
  await fixture(page, idle);
  await page.getByRole("button", { name: "Refresh agent activity" }).click();
  await expect(workspace(page)).toContainText("No active investigation");
  await expect(workspace(page).locator(".aw-flowing")).toHaveCount(0);
});

// Current visual contract: the roster is stable; light and motion mean processing.
test("processing light and dots follow each task through completion and idle", async ({ page }) => {
  const v = parallel();
  const run = v.runs[0];
  const unused = run.agents.find((a: any) => a.id === "manufacturing");
  unused.state = "not_invoked"; unused.tasks = [];
  await fixture(page, v);
  await ready(page);
  await expect(workspace(page).locator(".aw-agent")).toHaveCount(5);
  await expect(workspace(page).locator('[data-display-state="processing"]')).toHaveCount(2);
  await expect(node(page, "validation_evidence")).toContainText("Processing");
  await expect(node(page, "manufacturing")).toHaveAttribute("data-display-state", "idle");
  await expect(node(page, "manufacturing")).toContainText("Not used in this run");
  await expect(node(page, "change_impact")).toContainText("Completed");
  await expect(node(page, "change_impact")).toContainText("Task complete");
  await expect(node(page, "change_impact").locator("small")).toHaveCSS("color", "rgb(23, 107, 69)");
  const workingColor = await node(page, "validation_evidence").locator(".aw-ring").evaluate(el => getComputedStyle(el).backgroundColor);
  expect(workingColor).not.toBe(await node(page, "manufacturing").locator(".aw-ring").evaluate(el => getComputedStyle(el).backgroundColor));
  await expect(node(page, "coordinator")).not.toHaveAttribute("data-display-state", "processing");
  await expect(workspace(page).locator(".aw-relationship-lines circle")).toHaveCount(2);
  const dot = workspace(page).locator('[data-connection="validation_evidence"] circle');
  const origin = await dot.boundingBox();
  await expect.poll(async () => {
    const box = await dot.boundingBox();
    return Math.hypot(box!.x-origin!.x, box!.y-origin!.y);
  }).toBeGreaterThan(2);
  await workspace(page).scrollIntoViewIfNeeded();
  await capture(page, "processing-1440x900");

  const validation = run.agents.find((a: any) => a.id === "validation_evidence");
  validation.state = "completed";
  for (const task of validation.tasks) task.state = "completed";
  await page.getByRole("button", {name:"Refresh agent activity"}).click();
  await expect(node(page, "validation_evidence")).toHaveAttribute("data-display-state", "completed");
  await expect(node(page, "validation_evidence")).toContainText("Completed");
  await expect(workspace(page).locator('[data-connection="validation_evidence"] circle')).toHaveCount(0);
  await expect(workspace(page).locator(".aw-flowing")).toHaveCount(1);

  const coordinator = run.agents.find((a: any) => a.id === "coordinator");
  coordinator.state = "working";
  for (const task of coordinator.tasks) task.state = "working";
  await page.getByRole("button", {name:"Refresh agent activity"}).click();
  await expect(node(page, "coordinator")).toHaveAttribute("data-display-state", "processing");
  await expect(node(page, "coordinator")).toContainText("Processing");

  run.status = "completed"; run.telemetry = "recorded";
  for (const agent of run.agents.filter((a: any) => a.tasks.length)) {
    agent.state = "completed";
    for (const task of agent.tasks) task.state = "completed";
  }
  await page.getByRole("button", {name:"Refresh agent activity"}).click();
  await expect(workspace(page).locator('[data-display-state="completed"]')).toHaveCount(4);
  await expect(workspace(page).locator('[data-display-state="idle"]')).toHaveCount(1);
  await expect(workspace(page).locator(".aw-processing, .aw-relationship-lines circle")).toHaveCount(0);
  await capture(page, "completed-idle-1440x900");
});
