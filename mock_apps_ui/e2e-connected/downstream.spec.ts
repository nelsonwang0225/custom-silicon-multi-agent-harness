import { test as base, expect, type Page } from "@playwright/test";
import { spawn, type ChildProcess } from "node:child_process";
import { mkdir } from "node:fs/promises";
import path from "node:path";
const root = path.resolve(".."),
  origin = "http://127.0.0.1:5175";
const basePath = "/control/programs/PRG-A17/cases/CR-017";
const shots = path.join(
  root,
  "docs/phase08/workflows/regression-08-2-1/screenshots",
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
async function scheduled(page: Page) {
  await page.goto(basePath);
  await profile(page, "Program operator");
  await page
    .getByRole("button", { name: "Run investigation", exact: true })
    .click();
  await page
    .getByRole("link", { name: /Review exact proposal · v1/ })
    .click({ timeout: 30000 });
  await profile(page, "Engineering approver");
  await page
    .getByLabel("Review comment", { exact: true })
    .fill("Scripted test of the original scheduling approval.");
  await page
    .getByRole("button", { name: "Approve this proposal", exact: true })
    .click();
  await expect(
    page.getByText("Approval recorded for this exact proposal.", {
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Execute approved proposal", exact: true })
    .click();
  await expect
    .poll(
      async () => {
        const state = await (
          await page.request.get("/control-api/cases/CR-017")
        ).json();
        return state.proposals[0]?.execution.status;
      },
      { timeout: 30000 },
    )
    .toBe("completed_execution");
  await page.goto(basePath);
  const panel = page.locator(".cp-section").filter({
    has: page.getByRole("heading", {
      name: "Physical validation",
      exact: true,
    }),
  });
  await expect(panel).toContainText("Physical validation pending");
  return panel;
}
async function publish(page: Page) {
  await page
    .getByRole("link", { name: "Open Validation Lab", exact: true })
    .click();
  const lab = page;
  await expect(
    lab.getByRole("heading", { name: "Final check before publishing" }),
  ).toBeVisible();
  await lab
    .getByLabel("Demo identity · Lab operator for this synthetic event")
    .check();
  await lab
    .getByRole("button", { name: "Publish synthetic result", exact: true })
    .click();
  await expect(
    lab.getByRole("link", { name: "View validation result", exact: true }),
  ).toBeVisible();
  await lab.screenshot({
    path: path.join(shots, "02-lab-result.png"),
    fullPage: true,
  });
  await lab
    .getByRole("link", { name: "Return to CR-017", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Refresh workflow", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Assess validation result", exact: true }),
  ).toBeVisible();
}
async function assess(page: Page) {
  await profile(page, "Program operator");
  await page
    .getByRole("button", { name: "Assess validation result", exact: true })
    .click();
  await expect
    .poll(
      async () => {
        const state = await (
          await page.request.get("/control-api/cases/CR-017")
        ).json();
        return !!state.downstream?.assessment;
      },
      { timeout: 35000 },
    )
    .toBe(true);
  await page
    .getByRole("button", { name: "Refresh workflow", exact: true })
    .click();
}
test("downstream lab event, reassessment and distinct engineering review", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await scheduled(page);
  await page.screenshot({
    path: path.join(shots, "01-physical-pending.png"),
    fullPage: true,
  });
  await publish(page);
  await assess(page);
  await expect(
    page.getByRole("link", { name: "Review validation evidence", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: path.join(shots, "03-evidence-reassessed.png"),
    fullPage: true,
  });
  await page
    .getByRole("link", { name: "View validation result", exact: true })
    .click();
  const modal = page.getByRole("dialog");
  await expect(modal).toContainText("Explicit synthetic demo lab action");
  await expect(modal).toContainText("Engineering review");
  await modal.screenshot({
    path: path.join(shots, "03-result-evidence-modal.png"),
  });
  await page.keyboard.press("Escape");
  await page.goto("/control/decisions");
  await profile(page, "Program operator");
  await page
    .getByRole("link", {
      name: "CR-017 · Engineering evidence review",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Approve validation evidence",
      exact: true,
    }),
  ).toBeDisabled();
  await expect(
    page.getByText("Demo identity · Program operator", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Refresh source records", exact: true }),
  ).toBeEnabled();
  await expect(page.locator(".cp-concierge-dock")).toHaveClass(
    /cp-dock-minimal/,
  );
  await page.screenshot({
    path: path.join(shots, "04-operator-cannot-approve.png"),
    fullPage: true,
  });
  await profile(page, "Engineering approver");
  await page
    .getByLabel("Engineering evidence review comment")
    .fill(
      "Scripted engineering review: exact result applies to REQ-042-V2. Customer acceptance remains pending.",
    );
  await page
    .getByRole("button", { name: "Approve validation evidence", exact: true })
    .click();
  await expect(page.getByText("Approved", { exact: true })).toBeVisible();
  await page.screenshot({
    path: path.join(shots, "05-engineering-approved.png"),
    fullPage: true,
  });
  await page.goto(basePath);
  const panel = page.locator(".cp-section").filter({
    has: page.getByRole("heading", {
      name: "Physical validation",
      exact: true,
    }),
  });
  await expect(panel).toContainText(
    "Validation complete · Customer acceptance pending",
  );
  await panel.screenshot({
    path: path.join(shots, "06-validation-complete.png"),
  });
  await page.goto("/control/overview");
  await expect(
    page.locator('.cp-attention [data-case-id="CR-017"]'),
  ).toHaveCount(0);
  const state = await (
    await page.request.get("/control-api/cases/CR-017")
  ).json();
  expect(state.proposals).toHaveLength(1);
  expect(state.runs).toHaveLength(2);
  expect(state.downstream.physical.reviews).toHaveLength(1);
  expect(state.downstream.physical.customer_acceptance).toBe("pending");
  await page.goto("/engineering/changes/CR-017");
  const sourceEvidence=page.locator(".panel").filter({has:page.getByRole("heading",{name:"Current validation evidence",exact:true})});
  await expect(sourceEvidence).toContainText("Validation complete");
  await expect(sourceEvidence).toContainText("Approved");
  await expect(sourceEvidence).toContainText(state.downstream.physical.current_review.id);
  await expect(sourceEvidence).toContainText("Pending");
  await expect(page.getByText("Scheduling record:",{exact:false})).toBeVisible();

  expect(errors).toEqual([]);
});
test.describe("failed criteria fixture", () => {
  test.use({ fault: "lab_failed" });
  test("failure remains open after reassessment", async ({ page }) => {
    await scheduled(page);
    await publish(page);
    await assess(page);
    const panel = page.locator(".cp-section").filter({
      has: page.getByRole("heading", {
        name: "Physical validation",
        exact: true,
      }),
    });
    await expect(panel).toContainText("Validation evidence gap remains");
    await expect(panel).toContainText("Criteria not passed");
    await expect(
      page.getByRole("link", {
        name: "Review validation evidence",
        exact: true,
      }),
    ).toHaveCount(0);
    await panel.screenshot({
      path: path.join(shots, "07-failed-criteria.png"),
    });
    const state = await (
      await page.request.get("/control-api/cases/CR-017")
    ).json();
    expect(state.downstream.review_ready).toBe(false);
    expect(state.downstream.physical.reviews).toHaveLength(0);
    expect(state.proposals).toHaveLength(1);
    await page.getByRole("button", { name: "Retry evidence reassessment", exact: true }).click();
    await expect.poll(async () => {
      const after = await (await page.request.get("/control-api/cases/CR-017")).json();
      return after.downstream.assessment?.run_id;
    }).not.toBe(state.downstream.assessment.run_id);
    await page.getByRole("button", { name: "Refresh workflow", exact: true }).click();
    await expect(panel).toContainText("Validation evidence gap remains");
    await expect(page.getByRole("link", { name: "Review validation evidence", exact: true })).toHaveCount(0);
  });
});
