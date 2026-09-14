import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import { mkdir } from "node:fs/promises";
import type { Schema } from "../src/api";

// Scripted source HTTP/browser integration, with simulated identities and an
// isolated database owned by playwright.config.ts. No AI or physical test run.
const api = "/api/v1";
const auth = (role = "reader") => ({
  Authorization: `Bearer demo-portfolio-${role}-local-only`,
});

async function read<T>(request: APIRequestContext, path: string): Promise<T> {
  const response = await request.get(api + path, { headers: auth() });
  expect(response.ok(), await response.text()).toBeTruthy();
  return response.json();
}

async function write<T>(
  request: APIRequestContext,
  path: string,
  body: unknown,
  role = "automation",
): Promise<T> {
  const response = await request.post(api + path, {
    headers: { ...auth(role), "Idempotency-Key": crypto.randomUUID() },
    data: body,
  });
  expect(response.status(), await response.text()).toBe(201);
  return response.json();
}

async function schedule(request: APIRequestContext, changeId: string) {
  const change = await read<Schema["ChangeView"]>(
    request,
    `/engineering/changes/${changeId}`,
  );
  const options = await read<Schema["Options"]>(
    request,
    `/validation/options?change_id=${changeId}`,
  );
  const option = options.items.find(
    (o) => o.resource_eligible && o.meets_deadline,
  );
  expect(
    option,
    "Fixture needs an eligible on-time source option",
  ).toBeDefined();
  const body: Schema["PlanInput"] = {
    expected_change_content_version: change.content_version,
    target_requirement_revision_id: change.proposed_requirement_revision_id,
    configuration_id: option!.configuration_id,
    procedure_id: option!.procedure_id,
    sample_id: option!.sample.id,
    slot_id: option!.slot.id,
    milestone_id: option!.milestone_id,
    expected_source_versions: option!.expected_source_versions,
    assessment: {
      facts: [
        {
          text: "Scripted source UI verification: inspect the approved workload before publishing a synthetic result.",
          source_refs: [
            { resource_type: "engineering.change", resource_id: change.id },
          ],
        },
      ],
      evidence_gaps: ["No applicable result has been published for this job."],
      unresolved_questions: ["The test result remains unknown until recorded."],
    },
  };
  const plan = await write<Schema["PlanView"]>(
    request,
    `/engineering/changes/${changeId}/plans`,
    body,
  );
  const decision = await write<Schema["Decision"]>(
    request,
    `/engineering/plans/${plan.id}/decisions`,
    {
      decision: "approve",
      expected_plan_version: plan.plan_version,
      expected_plan_digest: plan.plan_digest,
      reason:
        "Simulated engineer approval for isolated source UI verification.",
    },
    "engineer",
  );
  return write<Schema["JobView"]>(request, "/validation/jobs", {
    plan_id: plan.id,
    approval_id: decision.id,
  });
}

async function ready(page: Page) {
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
  await expect(page.getByText(/Last API refresh/)).toBeVisible();
  await expect(
    page.getByText("Refreshing from APIs…", { exact: true }),
  ).toHaveCount(0);
}

async function navigateJob(page: Page, jobId: string) {
  // Exercise same-component route changes, including late read cleanup, without
  // reloading the document and accidentally masking retained local state.
  await page.evaluate((id) => {
    history.pushState({}, "", `/validation/jobs/${id}`);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, jobId);
  await ready(page);
  await expect(page.locator("main .page-heading")).toContainText(jobId);
}

test("CR-017 final check is an interactive source preview until explicit lab publication", async ({
  page,
  request,
}, info) => {
  test.setTimeout(120000);
  await page.addInitScript(() => {
    class NoSpeech {
      start() {
        throw new Error("Real speech is disabled in source UI tests");
      }
      stop() {}
      abort() {}
    }
    Object.assign(window, {
      SpeechRecognition: NoSpeech,
      webkitSpeechRecognition: NoSpeech,
    });
  });
  const job = await schedule(request, "CR-017");
  const otherJob = await schedule(request, "CR-105");
  const portfolio = await read<Schema["Portfolio"]>(request, "/portfolio");
  const scope = portfolio.cases.find((c) => c.change.id === "CR-017")!;
  const errors: string[] = [];
  const writes: {
    path: string;
    body: unknown;
    authorization: string | undefined;
  }[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (
      (path.startsWith("/api/v1/") || path.startsWith("/control-api/")) &&
      !["GET", "HEAD", "OPTIONS"].includes(request.method())
    ) {
      writes.push({
        path,
        body: request.postDataJSON(),
        authorization: request.headers().authorization,
      });
    }
  });
  await page.goto(`/validation/jobs/${job.id}`);
  await ready(page);
  const finalCheck = page.locator("section.lab-completion").filter({
    has: page.getByRole("heading", {
      name: "Final check before publishing",
      exact: true,
    }),
  });
  await expect(finalCheck).toBeVisible();
  await expect(finalCheck).toContainText("Passing result preview");
  await expect(finalCheck).toContainText("Not yet published");
  await expect(finalCheck).toContainText(scope.config.id);
  await expect(finalCheck).toContainText(scope.baseline.id);
  await expect(finalCheck).toContainText(scope.target.id);
  await expect(finalCheck).toContainText(
    scope.baselineWorkload.context_bins
      .map((bin) => bin.toLocaleString("en-US"))
      .join(" / "),
  );
  await expect(finalCheck).toContainText(
    scope.targetWorkload.context_bins
      .map((bin) => bin.toLocaleString("en-US"))
      .join(" / "),
  );
  await expect(finalCheck).toContainText(
    String(scope.targetWorkload.total_suite_minutes),
  );
  const publish = page.getByRole("button", {
    name: "Publish synthetic result",
    exact: true,
  });
  const identity = page.getByRole("checkbox", {
    name: "Demo identity · Lab operator for this synthetic event",
  });
  await expect(publish).toBeDisabled();
  const before = await read<Schema["JobView"]>(
    request,
    `/validation/jobs/${job.id}`,
  );
  expect(before.completion).toBeNull();
  const completionBefore = await request.get(
    `${api}/validation/jobs/${job.id}/completion`,
    { headers: auth() },
  );
  expect(completionBefore.status()).toBe(404);

  // A newer source version must remove the passing preview until its exact
  // approved binding is restored. The intercepted response never changes data.
  const workloadRoute = `**/api/v1/engineering/workloads/${scope.targetWorkload.id}`;
  await page.route(workloadRoute, async (route) => {
    const response = await route.fetch();
    const workload = (await response.json()) as Schema["Workload"];
    await route.fulfill({
      response,
      json: { ...workload, content_version: workload.content_version + 1 },
    });
  });
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await ready(page);
  await expect(finalCheck).toContainText(
    "The final-check summary needs current records for this approved job.",
  );
  await expect(
    finalCheck.getByText("Passing result preview", { exact: true }),
  ).toHaveCount(0);
  await page.unroute(workloadRoute);
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await ready(page);
  await expect(
    finalCheck.getByText("Passing result preview", { exact: true }),
  ).toBeVisible();
  expect(
    await read<Schema["Workload"]>(
      request,
      `/engineering/workloads/${scope.targetWorkload.id}`,
    ),
  ).toEqual(scope.targetWorkload);

  for (const mode of ["Original", "Updated", "Changes"]) {
    await finalCheck.getByRole("button", { name: mode, exact: true }).click();
    await expect(
      finalCheck.getByRole("button", { name: mode, exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
  }
  for (const region of ["Context & memory", "Compute", "I/O & scheduling"]) {
    await finalCheck
      .getByRole("button", { name: new RegExp(region + "$"), exact: false })
      .click();
  }
  await expect(finalCheck).toContainText(scope.config.firmware);
  await expect(finalCheck).toContainText(scope.config.runtime);
  await finalCheck
    .getByRole("button", { name: "Switch to top view", exact: true })
    .click();
  const hotspotCanvas = finalCheck.locator("canvas");
  const hotspotBounds = await hotspotCanvas.boundingBox();
  expect(hotspotBounds).not.toBeNull();
  await hotspotCanvas.click({
    position: { x: hotspotBounds!.width / 2, y: hotspotBounds!.height / 2 },
  });
  await expect(
    finalCheck.getByRole("heading", { name: "Compute array", exact: true }),
  ).toBeVisible();
  await finalCheck.getByRole("button", { name: /I\/O & scheduling$/ }).click();
  await finalCheck
    .getByRole("button", { name: "Switch to oblique view", exact: true })
    .click();
  for (const control of [
    "Rotate left",
    "Rotate right",
    "Switch to top view",
    "Switch to oblique view",
    "Zoom out",
    "Zoom in",
  ]) {
    await finalCheck
      .getByRole("button", { name: control, exact: true })
      .click();
  }
  const canvas = finalCheck.locator("canvas");
  await expect(canvas).toBeVisible();
  const box = await canvas.boundingBox();
  expect(box).not.toBeNull();
  const beforeDrag = await canvas.evaluate((element) =>
    (element as HTMLCanvasElement).toDataURL(),
  );
  await page.mouse.move(box!.x + box!.width * 0.4, box!.y + box!.height * 0.4);
  await page.mouse.down();
  await page.mouse.move(
    box!.x + box!.width * 0.6,
    box!.y + box!.height * 0.55,
    { steps: 8 },
  );
  await page.mouse.up();
  expect(
    await canvas.evaluate((element) =>
      (element as HTMLCanvasElement).toDataURL(),
    ),
    "Drag must change the visible camera",
  ).not.toBe(beforeDrag);
  expect(
    writes,
    "Visual exploration must never mutate source or host state",
  ).toEqual([]);
  expect(
    await read<Schema["JobView"]>(request, `/validation/jobs/${job.id}`),
  ).toEqual(before);
  await expect(publish).toBeDisabled();

  await mkdir("../docs/screenshots/cr017-final-check", { recursive: true });
  for (const [width, height] of [
    [1440, 900],
    [1920, 1080],
    [1280, 800],
  ]) {
    await page.setViewportSize({ width, height });
    await finalCheck.scrollIntoViewIfNeeded();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    const path = `../docs/screenshots/cr017-final-check/preview-${width}.png`;
    await page.screenshot({ path, animations: "disabled" });
    await info.attach(`preview-${width}`, { path, contentType: "image/png" });
  }

  await identity.check();
  await expect(publish).toBeEnabled();
  await navigateJob(page, otherJob.id);
  await expect(finalCheck).toHaveCount(0);
  await expect(publish).toHaveCount(0);
  await navigateJob(page, job.id);
  await expect(finalCheck).toBeVisible();
  await expect(identity).not.toBeChecked();
  await expect(publish).toBeDisabled();
  await identity.check();
  const published = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url().endsWith(`/validation/jobs/${job.id}/synthetic-result`),
  );
  await publish.click();
  const response = await published;
  expect(response.status()).toBe(201);
  const receipt = (await response.json()) as Schema["LabCompletion"];
  await expect(
    page.getByRole("link", { name: "View validation result", exact: true }),
  ).toBeVisible();
  await expect(finalCheck).toHaveCount(0);
  expect(writes).toEqual([
    {
      path: `/api/v1/validation/jobs/${job.id}/synthetic-result`,
      body: { expected_plan_digest: job.plan_digest },
      authorization: "Bearer demo-lab-local-only",
    },
  ]);
  const after = await read<Schema["JobView"]>(
    request,
    `/validation/jobs/${job.id}`,
  );
  const readback = await read<Schema["LabCompletion"]>(
    request,
    `/validation/jobs/${job.id}/completion`,
  );
  expect(readback).toEqual(receipt);
  expect(after.completion).toEqual(receipt);
  expect({ ...after, completion: null }).toEqual(before);
  expect(receipt.recorded_by).toBe("demo-lab");
  const result = await read<Schema["Result"]>(
    request,
    `/validation/results/${receipt.result_id}`,
  );
  expect(result.criteria_passed).toBe(true);
  expect(result.configuration_snapshot).toEqual(scope.config);
  expect(result.workload_snapshot).toEqual(scope.targetWorkload);
  expect(result.actual_suite_minutes).toBe(
    scope.targetWorkload.total_suite_minutes,
  );
  await page.reload();
  await ready(page);
  await expect(finalCheck).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "View validation result", exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
