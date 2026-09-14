import { test, expect, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
const cr = "/control/programs/PRG-A17/cases/CR-017";
async function mockSpeech(page: Page, prefix = false) {
  await page.addInitScript(
    ({ prefix }) => {
      const root = window as any;
      const state = {
        calls: [] as string[],
        instances: [] as any[],
        lateResult: null as any,
      };
      class Recognition {
        continuous = false;
        interimResults = false;
        lang = "";
        maxAlternatives = 1;
        onstart: any;
        onaudiostart: any;
        onaudioend: any;
        onresult: any;
        onerror: any;
        onend: any;
        onnomatch: any;
        constructor() {
          state.instances.push(this);
        }
        start() {
          state.calls.push("start");
          state.lateResult = this.onresult;
        }
        stop() {
          state.calls.push("stop");
        }
        abort() {
          state.calls.push("abort");
        }
      }
      Object.defineProperty(root, "SpeechRecognition", {
        configurable: true,
        value: prefix ? undefined : Recognition,
      });
      Object.defineProperty(root, "webkitSpeechRecognition", {
        configurable: true,
        value: prefix ? Recognition : undefined,
      });
      root.__speech = state;
    },
    { prefix },
  );
}
async function event(page: Page, name: string, value?: unknown) {
  await page.evaluate(
    ({ name, value }) => {
      const s = (window as any).__speech;
      const r = s.instances.at(-1);
      r?.[`on${name}`]?.(value);
    },
    { name, value },
  );
}
async function results(page: Page, values: [string, boolean][]) {
  await event(page, "result", {
    results: values.map(([transcript, isFinal]) => ({
      0: { transcript },
      isFinal,
    })),
  });
}
async function ready(page: Page, path = cr) {
  await page.goto(path);
  await expect(
    page.getByRole("button", { name: "Refresh source records" }),
  ).toBeEnabled();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
}
async function open(page: Page) {
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .click();
}
async function start(page: Page) {
  await page
    .getByRole("button", { name: "Dictate to Stratos Concierge" })
    .click();
  if (
    await page
      .getByRole("button", { name: "Start dictation", exact: true })
      .count()
  )
    await page
      .getByRole("button", { name: "Start dictation", exact: true })
      .click();
}
async function calls(page: Page) {
  return page.evaluate(() => (window as any).__speech.calls as string[]);
}

test("explicit consent, actual active events, interim/final deduplication and no voice submission", async ({
  page,
}) => {
  await mockSpeech(page);
  const requests: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/api/")) requests.push(`${r.method()} ${r.url()}`);
  });
  await ready(page);
  await open(page);
  expect(await calls(page)).toEqual([]);
  const initial = [...requests];
  await page.getByLabel("Your draft").fill("Please inspect:");
  await page
    .getByRole("button", { name: "Dictate to Stratos Concierge" })
    .click();
  await expect(
    page.getByRole("region", { name: "Before using dictation" }),
  ).toContainText("may send audio to its speech provider");
  expect(await calls(page)).toEqual([]);
  await page
    .getByRole("button", { name: "Start dictation", exact: true })
    .click();
  expect(await calls(page)).toEqual(["start"]);
  await expect(page.locator(".cp-voice-status")).toContainText(
    "Requesting microphone permission",
  );
  await expect(page.locator(".cp-voice-status")).not.toContainText("Listening");
  await event(page, "start");
  await event(page, "audiostart");
  await expect(page.locator(".cp-voice-status")).toContainText("Listening");
  await results(page, [["approve the", false]]);
  await expect(page.locator(".cp-voice-interim")).toContainText("approve the");
  await expect(page.getByLabel("Your draft")).toHaveValue("Please inspect:");
  await results(page, [
    ["approve the plan", true],
    ["after review", false],
  ]);
  await results(page, [
    ["approve the plan", true],
    ["after review", true],
  ]);
  await results(page, [
    ["approve the plan", true],
    ["after review", true],
  ]);
  await expect(page.getByLabel("Your draft")).toHaveValue(
    "Please inspect: approve the plan after review",
  );
  await expect(
    page.getByRole("button", { name: "Send message unavailable" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Stop dictation", exact: true })
    .click();
  expect(await calls(page)).toContain("stop");
  await event(page, "audioend");
  await event(page, "end");
  await expect(page.locator(".cp-voice-status")).toContainText(
    "Dictation added",
  );
  await page
    .getByLabel("Your draft")
    .fill("Edited transcript; no approval granted");
  expect(requests).toEqual(initial);
  await expect(page.getByRole("button", { name: /^Approve/ })).toHaveCount(0);
});

test("cancel restores original draft, typing stops recognition and stale callbacks cannot overwrite it", async ({
  page,
}) => {
  await mockSpeech(page, true);
  await ready(page);
  await open(page);
  await page.getByLabel("Your draft").fill("Original draft");
  await start(page);
  await event(page, "audiostart");
  await results(page, [["dictated text", true]]);
  await page.getByRole("button", { name: "Cancel dictation" }).click();
  await expect(page.getByLabel("Your draft")).toHaveValue("Original draft");
  expect(await calls(page)).toContain("abort");
  await start(page);
  await event(page, "audiostart");
  await results(page, [["new text", true]]);
  await page.getByLabel("Your draft").fill("Manual edit wins");
  await page.evaluate(() =>
    (window as any).__speech.lateResult({
      results: [{ 0: { transcript: "late unwanted text" }, isFinal: true }],
    }),
  );
  await expect(page.getByLabel("Your draft")).toHaveValue("Manual edit wins");
  await expect(
    page.getByRole("button", { name: "Stop dictation" }),
  ).toHaveCount(0);
});

for (const [code, expected] of [
  ["not-allowed", "permission denied"],
  ["service-not-allowed", "permission denied"],
  ["audio-capture", "No microphone"],
  ["no-speech", "No speech detected"],
  ["network", "network error"],
  ["aborted", "interrupted"],
  ["language-not-supported", "language is unavailable"],
]) {
  test(`speech error ${code} keeps typed input and stops capture`, async ({
    page,
  }) => {
    await mockSpeech(page);
    await ready(page);
    await open(page);
    await page.getByLabel("Your draft").fill("Keep this text");
    await start(page);
    await event(page, "error", { error: code });
    await expect(page.locator(".cp-voice-status")).toContainText(expected);
    await expect(page.getByLabel("Your draft")).toHaveValue("Keep this text");
    await expect(
      page.getByRole("button", { name: "Stop dictation" }),
    ).toHaveCount(0);
    expect(await calls(page)).toEqual(["start", "abort"]);
    await page.getByLabel("Your draft").fill("Typing remains usable");
  });
}

test("60-second hard limit, service stop timeout and silence do not restart", async ({
  page,
}) => {
  await mockSpeech(page);
  await page.clock.install();
  await ready(page);
  await open(page);
  await start(page);
  await event(page, "audiostart");
  await page.clock.runFor(60001);
  await expect(page.locator(".cp-voice-status")).toContainText(
    "60-second limit reached",
  );
  expect(await calls(page)).toEqual(["start", "abort"]);
  await page.clock.runFor(60000);
  expect(await calls(page)).toEqual(["start", "abort"]);
  await start(page);
  await page.getByRole("button", { name: "Stop dictation" }).click();
  await page.clock.runFor(3001);
  await expect(page.locator(".cp-voice-status")).toContainText(
    "Speech service interrupted",
  );
  await start(page);
  await event(page, "end");
  await expect(page.locator(".cp-voice-status")).toContainText(
    "No speech recognized",
  );
});

test("cleanup on minimize, Escape, modal, context change, page hide and unmount", async ({
  page,
}) => {
  await mockSpeech(page);
  await ready(page);
  await open(page);
  await start(page);
  await event(page, "audiostart");
  await results(page, [["CR-017 scoped draft", true]]);
  await page
    .getByRole("button", { name: "Minimize Stratos Concierge" })
    .click();
  expect((await calls(page)).at(-1)).toBe("abort");
  await open(page);
  await expect(page.getByLabel("Your draft")).toHaveValue(
    "CR-017 scoped draft",
  );
  await start(page);
  await page.keyboard.press("Escape");
  expect((await calls(page)).at(-1)).toBe("abort");
  await open(page);
  await start(page);
  // Exercise a modal opened while dictation is active without focusing the page first.
  await page.evaluate(() => {
    const link = Array.from(document.querySelectorAll("a")).find((a) =>
      a.getAttribute("href")?.includes("evidence=RES-SHORT-B"),
    );
    link?.click();
  });
  await expect(page.getByRole("dialog")).toBeVisible();
  expect((await calls(page)).at(-1)).toBe("abort");
  await expect(
    page.getByRole("complementary", { name: "Stratos Concierge" }),
  ).toBeHidden();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("complementary", { name: "Stratos Concierge" }),
  ).toBeVisible();
  await start(page);
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Overview", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Overview", exact: true }),
  ).toBeVisible();
  await expect.poll(async () => (await calls(page)).at(-1)).toBe("abort");
  await expect(page.getByLabel("Your draft")).toHaveValue("");
  await start(page);
  await page.evaluate(() =>
    window.dispatchEvent(new PageTransitionEvent("pagehide")),
  );
  expect((await calls(page)).at(-1)).toBe("abort");
  await start(page);
  await page.getByRole("link", { name: "Source apps", exact: true }).click();
  await expect.poll(async () => (await calls(page)).at(-1)).toBe("abort");
});

test("unsupported browser and failed constructor retain typing; opening alone never captures", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "SpeechRecognition", {
      configurable: true,
      value: undefined,
    });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      configurable: true,
      value: undefined,
    });
  });
  await ready(page, "/control");
  await expect(
    page.getByRole("button", { name: "Dictation unavailable", exact: true }),
  ).toBeDisabled();
  await page.getByLabel("Search Stratos", { exact: true }).focus();
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .first()
    .click();
  await expect(page.getByLabel("Your draft")).toBeFocused();
  await expect(
    page.getByRole("button", { name: "Dictate to Stratos Concierge" }),
  ).toBeDisabled();
  await expect(page.locator(".cp-voice-status")).toContainText(
    "Dictation unavailable",
  );
  await page.getByLabel("Your draft").fill("Typed input works");
  await page.evaluate(() =>
    Object.defineProperty(window, "SpeechRecognition", {
      configurable: true,
      value: class {
        constructor() {
          throw Error("unsupported service");
        }
      },
    }),
  );
  await page
    .getByLabel("Your draft")
    .fill("Feature detection is not service verification");
  await start(page);
  await expect(page.locator(".cp-voice-status")).toContainText(
    "Speech service unavailable",
  );
});

test("reference hierarchy, plain statuses, scoped modal focus and state restoration", async ({
  page,
}) => {
  await mockSpeech(page);
  await ready(page, "/control/programs?q=Helios");
  expect(
    await page.locator("h1").evaluate((el) => getComputedStyle(el).fontSize),
  ).toBe("40px");
  expect(
    await page
      .locator(".cp-program-row p")
      .evaluate((el) => getComputedStyle(el).fontSize),
  ).toBe("16px");
  expect(
    await page
      .locator(".cp-card-title strong")
      .evaluate((el) => getComputedStyle(el).fontSize),
  ).toBe("20px");
  expect(
    await page
      .locator(".cp-header")
      .evaluate((el) => getComputedStyle(el).backgroundImage),
  ).toContain("linear-gradient");
  const status = page.locator(".cp-card-status .cp-status");
  expect(
    await status.evaluate((el) => ({
      background: getComputedStyle(el).backgroundColor,
      padding: getComputedStyle(el).padding,
      border: getComputedStyle(el).borderWidth,
    })),
  ).toEqual({ background: "rgba(0, 0, 0, 0)", padding: "0px", border: "0px" });
  await expect(status).toHaveText("Validation risk");
  await expect(
    page.locator('[data-metric="Active investigations"]'),
  ).toHaveCount(0);
  const tile = page.getByRole("button", {
    name: "View Manufacturing Specialist details",
  });
  await tile.scrollIntoViewIfNeeded();
  await tile.focus();
  const before = await page.evaluate(() => ({
    y: scrollY,
    url: location.href,
  }));
  await tile.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toHaveAccessibleName("Manufacturing Specialist");
  await expect(dialog).toContainText("Helios Atlas Inference");
  await expect(dialog).toContainText("cannot release holds");
  await page.getByLabel("Search programs").evaluate((el: any) => el.focus());
  expect(
    await dialog.evaluate((el) => el.contains(document.activeElement)),
  ).toBeTruthy();
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press("Tab");
    expect(
      await dialog.evaluate((el) => el.contains(document.activeElement)),
    ).toBeTruthy();
  }
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press("Shift+Tab");
    expect(
      await dialog.evaluate((el) => el.contains(document.activeElement)),
    ).toBeTruthy();
  }
  await page.keyboard.press("Escape");
  await expect(tile).toBeFocused();
  expect(
    await page.evaluate(() => ({ y: scrollY, url: location.href })),
  ).toEqual(before);
  await page.locator(".cp-program-row").click();
  await page.locator(".cp-case-list a").filter({ hasText: "CR-017" }).click();
  const view = page.getByRole("link", {
    name: "Inspect RES-SHORT-B",
    exact: true,
  });
  await view.click();
  await expect(dialog).toContainText("Source record");
  await expect(dialog).toContainText("RES-SHORT-B");
  await expect(dialog).toContainText(
    "60 minutes observed; 480 minutes requested",
  );
  await expect(dialog).toContainText("Applicability gap");
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(view).toBeFocused();
});

test("controlled listening screenshot is explicitly mocked, never a live speech check", async ({
  page,
}) => {
  await mockSpeech(page);
  await ready(page, "/control");
  await open(page);
  await start(page);
  await event(page, "start");
  await event(page, "audiostart");
  await results(page, [["What needs attention", false]]);
  await expect(page.locator(".cp-voice-status")).toContainText("Listening");
  mkdirSync("../docs/phase08/workflows/regression-08-2-1/regression-shell", {
    recursive: true,
  });
  await page.screenshot({
    path: "../docs/phase08/workflows/regression-08-2-1/regression-shell/MOCKED-listening-1440.png",
  });
  await page.getByRole("button", { name: "Cancel dictation" }).click();
});

test("search and demo access stop actual mocked capture before changing presentation context", async ({
  page,
}) => {
  await mockSpeech(page);
  await ready(page, "/control/overview");
  await open(page);
  await start(page);
  await event(page, "audiostart");
  await page.getByLabel("Search Stratos", { exact: true }).fill("Helios");
  expect((await calls(page)).at(-1)).toBe("abort");
  await page.keyboard.press("Escape");
  await page
    .getByRole("button", { name: "Open Stratos Concierge", exact: true })
    .count()
    .then(async (n) => {
      if (n) await open(page);
    });
  await start(page);
  await event(page, "audiostart");
  await results(page, [["Old demo draft", true]]);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Demo access" })).toBeVisible();
  expect((await calls(page)).at(-1)).toBe("abort");
  await page
    .getByRole("dialog", { name: "Demo access" })
    .getByRole("button", { name: /Program operator/ })
    .click();
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  await open(page);
  await expect(page.getByLabel("Your draft")).toHaveValue("");
  expect((await calls(page)).filter((x) => x === "start")).toHaveLength(2);
});
