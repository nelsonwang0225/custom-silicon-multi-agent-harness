import { test as base, expect, type Page } from "@playwright/test";
import { spawn, type ChildProcess } from "node:child_process";
import { mkdir } from "node:fs/promises";
import path from "node:path";
const root = path.resolve(".."),
  origin = "http://127.0.0.1:5175";
const basePath = "/control/programs/PRG-A17/cases/CR-017";
const shots = path.join(
  root,
  "docs/phase08/workflows/regression-08-2-1/regression-connected",
);
const test = base.extend<{ fault: string; isolated: void }>({
  fault: ["none", { option: true }],
  isolated: [
    async ({ request, fault }, use) => {
      let proc: ChildProcess | undefined;
      if (!process.env.PHASE08_REUSE_PREVIEW) {
        proc = spawn(
          path.join(root, "coordinator/.venv/bin/python"),
          [
            "-m",
            "coordinator.evals.phase08_2.serve",
            "--fault",
            fault,
            "--delay",
            "1.5",
          ],
          {
            cwd: root,
            env: { ...process.env, PYTHONPATH: "src:." },
            stdio: "pipe",
          },
        );
        let logs = "";
        proc.stdout?.on("data", (x) => (logs += x));
        proc.stderr?.on("data", (x) => (logs += x));
        await expect
          .poll(
            async () => {
              if (proc?.exitCode !== null) throw new Error(logs);
              return (
                await request
                  .get("http://127.0.0.1:18083/control-api/health")
                  .catch(() => null)
              )?.status();
            },
            { timeout: 20000 },
          )
          .toBe(200);
      }
      await mkdir(shots, { recursive: true });
      await use();
      if (proc) {
        proc.kill("SIGTERM");
        await new Promise<void>((resolve) =>
          proc!.once("exit", () => resolve()),
        );
      }
    },
    { auto: true },
  ],
});
async function profile(page: Page, name: string) {
  await expect(
    page.getByRole("button", { name: /^(Log in|Demo profile)$/ }),
  ).toBeVisible();
  if (await page.getByRole("button", { name: "Log in", exact: true }).count())
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
    .getByRole("dialog", { name: "Demo access", exact: true })
    .getByRole("button", { name: new RegExp(name) })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Demo access", exact: true }),
  ).toHaveCount(0);
}
async function shot(page: Page, name: string) {
  if (/^(06|07|08)/.test(name)) {
    const reduce = page.getByRole("button", {
      name: "Reduce Stratos Concierge",
      exact: true,
    });
    if (await reduce.count()) await reduce.click();
    await page
      .locator(".cp-section")
      .filter({
        has: page.getByRole("heading", {
          name: "Execution & independent verification",
          exact: true,
        }),
      })
      .screenshot({ path: path.join(shots, name + "-readback.png") });
  }
  await page.screenshot({
    path: path.join(shots, name + ".png"),
    fullPage: true,
  });
  await page.screenshot({ path: path.join(shots, name + "-viewport.png") });
}
async function run(page: Page) {
  await page.goto(basePath);
  await profile(page, "Program operator");
  await expect(
    page.getByRole("button", { name: "Run investigation", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Run investigation", exact: true })
    .click();
  await expect(
    page.getByText("Investigation running", { exact: true }),
  ).toBeVisible();
}
async function review(page: Page) {
  await expect(
    page.getByRole("link", { name: /(Review|View) exact proposal · v1/ }),
  ).toBeVisible({ timeout: 30000 });
  await page
    .getByRole("link", { name: /(Review|View) exact proposal · v1/ })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review validation plan", exact: true }),
  ).toBeVisible();
}
async function approve(page: Page) {
  const url = page.url();
  await profile(page, "Engineering approver");
  expect(page.url()).toBe(url);
  await page
    .getByLabel("Review comment")
    .fill(
      "Scripted integration test of exact proposal. Simulated engineering reviewer.",
    );
  await page
    .getByRole("button", { name: "Approve this proposal", exact: true })
    .click();
  await expect(
    page.getByText("Approval recorded for this exact proposal.", {
      exact: true,
    }),
  ).toBeVisible();
}
async function hostPost(
  page: Page,
  route: string,
  body: unknown,
  role = "automation",
) {
  return page.request.post(origin + "/control-api/" + route, {
    data: body,
    headers: {
      Origin: origin,
      "X-Stratos-Action": "1",
      "X-Stratos-Demo-Profile": role,
    },
  });
}

test("connected CR-017: exact review, governed execution and pending physical results", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const sourceWrites: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST" && r.url().includes("/api/v1/"))
      sourceWrites.push(r.url());
  });
  await page.goto(basePath);
  await expect(
    page.getByRole("heading", { name: "Not investigated", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Long-context workload acceptance evidence",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      /Assess whether current validation evidence covers Helios’s expanded long-context workload/,
    ),
  ).toBeVisible();
  const originalRequest = page.getByText(
    /Our updated long-context inference release uses workload manifest WF-LC-V2/,
  );
  await expect(originalRequest).toBeHidden();
  await page.getByText("View original request", { exact: true }).click();
  await expect(originalRequest).toBeVisible();
  await expect(
    page.getByText(
      "Run an investigation to assess evidence coverage and prepare validation options.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    page.getByText("Evidence applicability not assessed", { exact: true }),
  ).toBeVisible();
  const initialEvidence = page.getByRole("table", {
    name: /These source observations are available for review/,
  });
  await expect(initialEvidence).toContainText("Not assessed");
  await expect(initialEvidence).not.toContainText("Insufficient");
  await expect(initialEvidence).not.toContainText(
    "Test duration is shorter than required",
  );
  await page
    .getByRole("button", { name: "Options & decisions", exact: true })
    .click();
  await expect(
    page.getByText("Run the investigation to calculate validation options.", {
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Summary", exact: true }).click();
  await shot(page, "01-before-investigation-test-double");
  await profile(page, "Program operator");
  await page
    .getByRole("button", { name: "Run investigation", exact: true })
    .dblclick();
  await expect(
    page.getByText("Investigation running", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Evidence applicability assessment in progress", {
      exact: true,
    }),
  ).toBeVisible();
  await shot(page, "02-investigation-recorded-test-double");
  await expect(
    page.getByRole("link", { name: /(Review|View) exact proposal · v1/ }),
  ).toBeVisible({ timeout: 30000 });
  const state = await (
    await page.request.get("/control-api/cases/CR-017")
  ).json();
  expect(state.runs).toHaveLength(1);
  expect(state.runs[0].specialists).toHaveLength(4);
  const replay = await hostPost(page, "cases/CR-017/investigations", {
    invocation_id: state.runs[0].invocation_id,
  });
  expect(replay.status()).toBe(202);
  expect((await replay.json()).replayed).toBe(true);
  const invalid = await hostPost(page, "cases/CR-017/investigations", {
    invocation_id: "ui_bad_workflow",
    workflow_id: "delivery_readiness",
  });
  expect(invalid.status()).toBe(422);
  const ref = state.proposals[0].execution.reference;
  expect(
    (await hostPost(page, "proposals/execute", { reference: ref })).status(),
  ).toBe(409);
  expect(
    (
      await hostPost(
        page,
        "proposals/review",
        { reference: ref, decision: "approve" },
        "reader",
      )
    ).status(),
  ).toBe(403);
  await page.getByRole("button", { name: "Summary", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Recommendation & options" }),
  ).toBeVisible();
  await expect(
    page.getByText("Overall findings and next steps", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(
      /Current evidence covers 60 of the requested 480 test minutes/,
    ),
  ).toBeVisible();
  const completedEvidence = page.getByRole("table", {
    name: /The completed investigation compared each result/,
  });
  await expect(completedEvidence).toContainText("Insufficient");
  await expect(completedEvidence).toContainText(
    "Test duration is shorter than required",
  );
  await expect(
    page.getByText("Full applicable evidence still required", { exact: true }),
  ).toBeVisible();
  await shot(page, "03-completed-findings-test-double");
  await review(page);
  await expect(
    page.getByText("Responsible role: Engineering approver.", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Approve this proposal", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", {
      name: "Execute approved proposal",
      exact: true,
    }),
  ).toBeDisabled();
  await shot(page, "04-exact-decision-review-test-double");
  await approve(page);
  await shot(page, "05-approved-proposal-test-double");
  const altered = await hostPost(page, "proposals/execute", {
    reference: ref,
    arguments: { configuration_id: "CFG-WRONG" },
  });
  expect(altered.status()).toBe(422);
  await page
    .getByRole("button", { name: "Execute approved proposal", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Recheck source readback", exact: true }),
  ).toBeEnabled({ timeout: 30000 });
  await expect(
    page.getByText("Execution verified", { exact: true }).first(),
  ).toBeVisible();
  await shot(page, "06-verified-execution-test-double");
  await page.getByRole("link", { name: /Return to CR-017 workbench/ }).click();
  await expect(
    page.getByRole("heading", { name: "Physical validation", exact: true }),
  ).toBeVisible();
  await expect(
    page.locator(".cp-section").filter({
      has: page.getByRole("heading", {
        name: "Physical validation",
        exact: true,
      }),
    }),
  ).toContainText("Pending");
  const after = await (
    await page.request.get("/control-api/cases/CR-017")
  ).json();
  expect(after.proposals[0].execution.customer_acceptance).toBe("pending");
  expect(after.proposals[0].execution.hardware_adequacy).toBe("unvalidated");
  expect(after.proposals[0].verification).toHaveLength(2);
  expect(sourceWrites).toEqual([]);
  expect(errors).toEqual([]);
  await page.goto("/control/overview");
  // This older fixture initializes only CR-017. Its completed review must not
  // imply a known zero across the three unavailable later workflow sources.
  expect(
    after.decision_summaries.filter((d: any) => d.requires_human),
  ).toHaveLength(0);
  expect(after.case_summaries.some((c: any) => !c.source_available)).toBe(true);
  await expect(page.locator('[data-metric="Needs review"] strong')).toHaveText(
    "—",
  );
  await expect(page.getByRole("region", { name: "Agent workspace" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Agent workspace" })).not.toContainText(
    "Scripted demo",
  );
  await profile(page, "Program operator");
  await page.getByLabel("Search Stratos", { exact: true }).fill("CR-017");
  await expect(
    page
      .getByRole("dialog", { name: "Search results" })
      .getByRole("button", { name: /CR-017/ })
      .first(),
  ).toBeVisible();
});

test.describe("partial write fixture", () => {
  test.use({ fault: "planner_rejected" });
  test("retains verified Validation action and displays Planner failure", async ({
    page,
  }) => {
    await run(page);
    await review(page);
    await approve(page);
    await page
      .getByRole("button", { name: "Execute approved proposal", exact: true })
      .click();
    await expect(
      page.getByText("Partially executed", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      page.getByText(/RESOURCE|Resource conflict/).first(),
    ).toBeVisible();
    await shot(page, "07-partial-execution-test-double");
    const state = await (
      await page.request.get("/control-api/cases/CR-017")
    ).json();
    expect(state.proposals[0].execution.steps[0].verification).toBe("matched");
    expect(state.proposals[0].execution.steps[1].status).toBe("failed");
    await expect(
      page.getByText("Execution verified", { exact: true }),
    ).toHaveCount(0);
  });
});
test.describe("readback mismatch fixture", () => {
  test.use({ fault: "readback_mismatch" });
  test("successful POST with mismatched readback stays unverified", async ({
    page,
  }) => {
    await run(page);
    await review(page);
    await approve(page);
    await page
      .getByRole("button", { name: "Execute approved proposal", exact: true })
      .click();
    await expect(
      page.getByText("Verification failed", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      page.getByText("Execution verified", { exact: true }),
    ).toHaveCount(0);
    await shot(page, "08-readback-mismatch-test-double");
    const state = await (
      await page.request.get("/control-api/cases/CR-017")
    ).json();
    expect(state.proposals[0].attempts[0].outcome).toBe("succeeded");
    expect(state.proposals[0].verification[0].outcome).toBe("mismatch");
  });
});
