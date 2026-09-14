import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
const shots = "../docs/screenshots/phase10-knowledge";
async function choose(page: Page, role: string) {
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  if (
    await page.getByRole("button", { name: "Log in", exact: true }).isVisible()
  )
    await page.getByRole("button", { name: "Log in", exact: true }).click();
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
test.beforeAll(async () => {
  await mkdir(shots, { recursive: true });
});
test.beforeEach(async ({ context }) => {
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
test("read-only search, explicit index sync, exact passage modal and layouts", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/control/knowledge");
  await expect(
    page.getByText("Index: Not indexed", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Reindex knowledge corpus" }),
  ).toHaveCount(0);
  await choose(page, "Program operator");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  const librarySearch = await page
    .getByRole("textbox", { name: "Search evidence documents" })
    .boundingBox();
  expect(librarySearch?.width).toBeGreaterThan(600);
  await expect(page.locator(".kn-library-header")).toContainText("Version");
  await expect(page.locator(".kn-library-header")).not.toContainText(
    "Source state",
  );
  await expect(page.locator(".kn-library-header")).not.toContainText("Program");
  await page
    .getByText("Knowledge index administration", { exact: true })
    .click();
  await page.getByRole("button", { name: "Reindex knowledge corpus" }).click();
  await page.getByRole("button", { name: "Confirm reindex" }).click();
  await expect(page.locator(".kn-provider")).toContainText("Index: Current");
  await page
    .getByRole("textbox", { name: "Search knowledge", exact: true })
    .fill("supplemental validation approval");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.locator(".kn-result").first()).toBeVisible();
  await expect(page.locator(".kn-result").first()).toContainText(
    "Open exact document and passage",
  );
  await expect(page.locator(".cp-connection")).toContainText("Current read");
  await page
    .getByRole("heading", { name: "Knowledge & Evidence", exact: true })
    .click();
  await page.mouse.move(1430, 1);
  await page.screenshot({ path: shots + "/search-1440.png", fullPage: true });
  await page.locator(".kn-result").first().click();
  await expect(page.getByRole("dialog")).toContainText(
    "Document matches the current source version",
  );
  await expect(page.getByRole("dialog")).toContainText(
    "This passage is supporting material",
  );
  await page.screenshot({ path: shots + "/passage-1440.png" });
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.screenshot({ path: shots + "/passage-1280.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: shots + "/passage-390.png" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 1440, height: 900 });
  await choose(page, "Read-only viewer");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Reindex knowledge corpus" }),
  ).toHaveCount(0);
  await page
    .getByRole("textbox", { name: "Search knowledge", exact: true })
    .fill("xyzzymissingterm");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(
    page.getByText("No eligible evidence found.", { exact: false }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("source failure and persona changes clear retrieved content", async ({
  page,
}) => {
  await page.goto("/control/knowledge");
  await choose(page, "Program operator");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  await expect(page.locator(".kn-provider")).toContainText("Index: Current");
  await page
    .getByRole("textbox", { name: "Search knowledge", exact: true })
    .fill("supplemental validation");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.locator(".kn-result").first()).toBeVisible();
  await choose(page, "Program Owner");
  await expect(page.locator(".kn-result")).toHaveCount(0);
  await choose(page, "Read-only viewer");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  await page.route("**/control-api/knowledge/search", (r) =>
    r.fulfill({ status: 503, json: { error: { code: "SOURCE_READ_FAILED" } } }),
  );
  await page
    .getByRole("textbox", { name: "Search knowledge", exact: true })
    .fill("validation");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Source unavailable");
  await expect(page.locator(".kn-result")).toHaveCount(0);
});

test("recorded specialist knowledge is discoverable from library, case and Operations", async ({
  page,
}) => {
  await page.goto("/control/knowledge");
  await choose(page, "Program operator");
  const started = await page.request.post(
    "http://127.0.0.1:18411/control-api/cases/CR-017/investigations",
    {
      headers: {
        Origin: "http://127.0.0.1:5210",
        "X-Stratos-Action": "1",
        "X-Stratos-Demo-Profile": "automation",
      },
      data: { invocation_id: "ui_knowledge_browser_run" },
    },
  );
  expect(started.status(), await started.text()).toBe(202);
  const runId = (await started.json()).run_id;
  await expect
    .poll(
      async () => {
        const r = await page.request.get(
          "http://127.0.0.1:18411/control-api/cases/CR-017",
        );
        return (await r.json()).runs.find(
          (r: { run_id: string }) => r.run_id === runId,
        )?.status;
      },
      { timeout: 30000 },
    )
    .toBe("completed");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Refresh knowledge activity", exact: true })
    .click();
  await page
    .getByRole("checkbox", { name: "Used in agent runs", exact: true })
    .check();
  await expect(page.locator(".kn-library-row").first()).toContainText(
    "Used by recent agent runs",
  );
  await expect(page.locator(".kn-run-passage").first()).toContainText(
    "Checked against the source document",
  );
  await page
    .getByRole("heading", { name: "Knowledge & Evidence", exact: true })
    .click();
  await page.mouse.move(1430, 1);
  await page.screenshot({
    path: shots + "/used-in-runs-1440.png",
    fullPage: true,
  });
  await page.locator(".kn-run-passage a").first().click();
  await expect(page.getByRole("dialog")).toContainText(
    "Document matches the current source version",
  );
  await page.keyboard.press("Escape");
  await page.getByRole("link", { name: "Open recorded run →" }).first().click();
  await expect(
    page.getByRole("heading", {
      name: "Documents the agents searched",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".kn-run-event").first()).toContainText(
    "What the agent looked for",
  );
  await page.screenshot({
    path: shots + "/run-provenance-1440.png",
    fullPage: true,
  });
});

test("quality corpus lifecycle, historical verification and QE-004 run provenance", async ({
  page,
}) => {
  await page.goto("/control/knowledge");
  await choose(page, "Program operator");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  const history = page
    .locator(".kn-library-row")
    .filter({ hasText: "DOC-QA-HIST-01" });
  await expect(history).toContainText("Historical · Non-normative");
  await expect(history).not.toContainText("Approved");
  await expect(
    page.locator(".kn-library-row").filter({ hasText: "DOC-QA-HOLD-01" }),
  ).toContainText("Approved");
  await expect(
    page.locator(".kn-library-row").filter({ hasText: "DOC-QA-EXCURSION-01" }),
  ).toContainText("Approved");
  await page
    .getByRole("combobox", { name: "Retrieval profile" })
    .selectOption("MANUFACTURING_QUALITY");
  await page
    .getByRole("textbox", { name: "Search knowledge", exact: true })
    .fill(
      "What does prior experience say about failures concentrated at one test site?",
    );
  await page
    .getByRole("checkbox", { name: "Include historical reports", exact: true })
    .check();
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.locator(".kn-result").first()).toContainText(
    "DOC-QA-HIST-01",
  );
  await page.locator(".kn-result").first().click();
  await expect(page.getByRole("dialog")).toContainText(
    "Document matches the current source version",
  );
  await expect(page.getByRole("dialog")).toContainText(
    "Historical context; not a current approval rule",
  );
  await page.screenshot({ path: shots + "/quality-historical-1440.png" });
  await page.keyboard.press("Escape");
  const started = await page.request.post(
    "http://127.0.0.1:18411/control-api/cases/QE-004/investigations",
    {
      headers: {
        Origin: "http://127.0.0.1:5210",
        "X-Stratos-Action": "1",
        "X-Stratos-Demo-Profile": "automation",
      },
      data: {
        invocation_id: "ui_quality_corpus_run",
        change_id: "QE-004",
        workflow_id: "yield_exception_recovery",
      },
    },
  );
  expect(started.status(), await started.text()).toBe(202);
  const runId = (await started.json()).run_id;
  await expect
    .poll(
      async () => {
        const r = await page.request.get(
          "http://127.0.0.1:18411/control-api/cases/QE-004",
        );
        return (await r.json()).runs.find(
          (r: { run_id: string }) => r.run_id === runId,
        )?.status;
      },
      { timeout: 30000 },
    )
    .toBe("completed");
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Refresh knowledge activity", exact: true })
    .click();
  await expect(
    page
      .locator(".kn-run-event")
      .filter({ hasText: "Explain the current hold/disposition rule." }),
  ).toContainText("Checked against the source document");
  const event = page
    .locator(".kn-run-event")
    .filter({
      hasText: "Historical context only; do not infer current root cause.",
    });
  await expect(event).toContainText("Historical context");
  await expect(event).toContainText("Used in the agent’s finding");
  await expect(event).toContainText("MANUFACTURING_QUALITY");
  await event.getByRole("link", { name: "Open recorded run →" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Documents the agents searched",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".kn-run-event")).toHaveCount(3);
  await page.screenshot({
    path: shots + "/quality-operations-1440.png",
    fullPage: true,
  });
  await page
    .getByRole("navigation", { name: "Control plane navigation" })
    .getByRole("link", { name: "Knowledge & Evidence", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Search evidence documents", exact: true })
    .fill("DOC-QA");
  await expect(page.locator(".kn-library-row")).toHaveCount(3);
  await expect(page.locator(".kn-provider")).toContainText("Index: Current");
  await page
    .getByRole("heading", { name: "Document library", exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({ path: shots + "/quality-library-1440.png" });
  for (const width of [1920, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await page
      .getByRole("heading", { name: "Document library", exact: true })
      .scrollIntoViewIfNeeded();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    await page.screenshot({ path: shots + `/quality-library-${width}.png` });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole("heading", { name: "Document library", exact: true })
    .scrollIntoViewIfNeeded();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await page.screenshot({ path: shots + "/quality-library-390.png" });
});
