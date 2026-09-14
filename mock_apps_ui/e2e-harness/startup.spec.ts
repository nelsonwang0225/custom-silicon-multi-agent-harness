import { test, expect } from "@playwright/test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
const exec = promisify(execFile);
const id = randomUUID();
const state = `.demo/phase09-4-e2e-${id}`;
const logs = `.cache/phase09-4/cold-start-${id}`;
const shots = "../docs/screenshots/phase09-4";
let sequence = 0;
async function demo(command: string[], allowed = [0]) {
  try {
    const r = await exec("./scripts/demo", ["--state-dir", state, ...command], { cwd: "..", timeout: 150000 });
    await writeFile(`../${logs}/${sequence++}-${command.at(-1)}.log`, r.stdout + r.stderr);
    expect(allowed).toContain(0);
    return r.stdout;
  } catch (e: any) {
    await writeFile(`../${logs}/${sequence++}-failed.log`, (e.stdout || "") + (e.stderr || ""));
    expect(allowed, e.stderr).toContain(e.code);
    return e.stdout;
  }
}
test.afterAll(async () => { await demo(["stop"]); });

test("cold start, real HTTP preflight, static routes, persistence, full reset and owned shutdown without model calls", async ({ page, request, browser }) => {
  await mkdir(`../${logs}`, { recursive: true }); await mkdir(shots, { recursive: true });
  await demo(["--source-port", "18241", "--mcp-port", "19241", "--host-port", "18240", "--ui-port", "5196", "init", "--yes"]);
  await demo(["start"]);
  const owner = JSON.parse(await readFile(`../${state}/processes.json`, "utf8"));
  expect(owner.children).toHaveLength(4);
  expect(await demo(["start"])).toContain("already_running");
  expect(JSON.parse(await readFile(`../${state}/processes.json`, "utf8")).pid).toBe(owner.pid);
  await demo(["status"]);
  await demo(["prepare", "--yes"], [0, 1]); // Missing credentials must fail preflight, never fake configured status.
  const initial = JSON.parse(await demo(["--json", "check"], [0, 1]));
  expect(initial.checks.baseline_valid).toBe(true);
  for (const [key, valid] of Object.entries(initial.checks)) if (key !== "model_configured") expect(valid, key).toBe(true);
  expect(initial.result).toBe(initial.checks.model_configured ? "Demo ready" : "Not ready");
  expect(initial.model_configuration.connectivity).toBe("not_checked");
  const errors: string[] = [], failed: string[] = [], responses: number[] = [];
  page.on("pageerror", e => errors.push(e.message));
  page.on("console", m => { if (["error", "warning"].includes(m.type())) errors.push(m.text() + " " + m.location().url); });
  page.on("requestfailed", r => failed.push(r.url()));
  page.on("response", r => { if (r.status() >= 400) responses.push(r.status()); });
  await page.addInitScript(() => {
    class MockSpeech { start() { throw Error("No real microphone allowed"); } stop() {} abort() {} }
    Object.assign(window, { SpeechRecognition: MockSpeech, webkitSpeechRecognition: MockSpeech });
  });
  const routes = ["/control/overview", "/control/programs/PRG-A17", ...["CR-017", "CR-019", "QE-004", "DR-009"].map(c => `/control/programs/PRG-A17/cases/${c}`),
    "/control/workflows", "/control/decisions", "/control/operations", "/engineering", "/validation", "/manufacturing", "/erp", "/programs"];
  const measurements = [];
  for (const route of routes) {
    const started = Date.now(); await page.goto(route); await page.locator("main h1").first().waitFor(); await page.waitForLoadState("networkidle");
    expect(await page.locator("body").innerText()).not.toContain("Host and source connections point to different");
    measurements.push({ route, settled_ms: Date.now() - started });
    if (["/control/overview", "/control/programs/PRG-A17", "/control/operations"].includes(route))
      await page.screenshot({ path: `${shots}/${route.split("/").at(-1)}-1440.png` });
  }
  expect(errors).toEqual([]); expect(failed).toEqual([]); expect(responses).toEqual([]);
  const normalRouteAudit = { console_errors: [...errors], failed_requests: [...failed], failed_http_statuses: [...responses] };
  await page.goto("/control/overview"); await page.waitForLoadState("networkidle");
  const overviewResources = await page.evaluate(() => performance.getEntriesByType("resource").map(x => x.name));
  expect(overviewResources.some(x => /\/assets\/source-app-/.test(x))).toBe(false);
  expect(overviewResources.some(x => /\/assets\/operations-/.test(x))).toBe(false);
  expect(overviewResources.some(x => /\/control-api\/operations(?:$|\?)/.test(x))).toBe(false);
  // An actual isolated metadata mutation must survive restart, then be removed by existing reset.
  const created = await request.post("/control-api/automations", { headers: { Origin: "http://127.0.0.1:5196", "X-Stratos-Action": "1", "X-Stratos-Demo-Profile": "automation" },
    data: { request_id: "harness_" + id.replaceAll("-", ""), configuration: { name: "Harness persistence check", workflow_id: "requirement_change_analysis", case_scope: "CR-017", trigger: { type: "schedule", cadence: "daily", time: "07:00", timezone: "America/Chicago" }, authority: "read_only" } } });
  expect(created.ok(), await created.text()).toBe(true);
  const mutation = await created.json();
  expect(mutation.automation_id).toMatch(/^automation_/);
  const sourceHeaders = { Authorization: "Bearer demo-automation-local-only" };
  const options = await (await request.get("/api/v1/validation/options?change_id=CR-017", { headers: sourceHeaders })).json();
  const option = options.items.find((o: any) => o.resource_eligible && o.meets_deadline);
  expect(option).toBeTruthy();
  const planBody = { expected_change_content_version: 1, target_requirement_revision_id: "REQ-042-V2",
    configuration_id: option.configuration_id, procedure_id: option.procedure_id, sample_id: option.sample.id,
    slot_id: option.slot.id, milestone_id: option.milestone_id, expected_source_versions: option.expected_source_versions,
    assessment: { facts: [{ text: "Scripted startup persistence check: additional evidence requested.", source_refs: [{ resource_type: "engineering.change", resource_id: "CR-017" }] }],
      evidence_gaps: ["Complete applicable evidence is absent."], unresolved_questions: ["The future test outcome is unknown."] } };
  const planRequest = { headers: { ...sourceHeaders, "Idempotency-Key": "harness-plan-" + id }, data: planBody };
  const sourcePlan = await request.post("/api/v1/engineering/changes/CR-017/plans", planRequest);
  expect(sourcePlan.status(), await sourcePlan.text()).toBe(201);
  const plan = await sourcePlan.json();
  expect(JSON.parse(await demo(["--json", "check"], [1])).checks.baseline_valid).toBe(false);
  await demo(["stop"]);
  for (const url of Object.values(initial.urls) as string[]) expect(await fetch(url).then(() => true, () => false)).toBe(false);
  await demo(["start"]);
  const list = await (await request.get("/control-api/automations")).json();
  expect(list.some((x: any) => x.automation_id === mutation.automation_id && x.name === "Harness persistence check")).toBe(true);
  const persisted = await (await request.get("/api/v1/engineering/plans/" + plan.id, { headers: sourceHeaders })).json();
  expect(persisted.plan_digest).toBe(plan.plan_digest);
  const replay = await request.post("/api/v1/engineering/changes/CR-017/plans", planRequest);
  expect(replay.headers()["idempotency-replayed"]).toBe("true");
  expect((await replay.json()).id).toBe(plan.id);
  const changed = JSON.parse(await demo(["--json", "check"], [1]));
  expect(changed.checks.baseline_valid).toBe(false);
  expect(changed.baseline.source_digest).not.toBe(initial.baseline.source_digest);
  await demo(["prepare", "--yes"], [0, 1]);
  const reset = JSON.parse(await demo(["--json", "check"], [0, 1]));
  expect(reset.checks.baseline_valid).toBe(true);
  expect(reset.baseline.source_digest).toBe(initial.baseline.source_digest);
  expect((await request.get("/api/v1/engineering/plans/" + plan.id, { headers: sourceHeaders })).status()).toBe(404);
  expect((await (await request.get("/control-api/operations/runs")).json())).toEqual([]);
  const ready = await (await request.get("/control-api/readiness")).json();
  expect(ready.mode).toBe("live_model"); expect(ready.active_workflows).toEqual([]);
  expect(ready.model_configuration.paid_call_made).toBe(false);
  // A failed lazy asset is readable and recoverable; it is not suppressed as success.
  const separate = await browser.newPage();
  await separate.route("**/assets/operations-*.js", r => r.abort());
  await separate.goto("http://127.0.0.1:5196/control/operations");
  await expect(separate.getByRole("alert")).toContainText("This workspace could not load");
  await separate.screenshot({ path: `${shots}/workspace-load-failure-1440.png` });
  await separate.unroute("**/assets/operations-*.js");
  await separate.getByRole("button", { name: "Reload workspace" }).click();
  await expect(separate.getByRole("heading", { name: "Operations", exact: true })).toBeVisible();
  await separate.close();
  await demo(["stop"]);
  await demo(["start"]);
  expect(JSON.parse(await demo(["--json", "check"], [0, 1])).checks.baseline_valid).toBe(true);
  await demo(["stop"]);
  const result = { method: "Scripted integration testing, live adapter configured but never invoked; no paid model, no real microphone", state, logs, initial, reset, route_measurements: measurements, ...normalRouteAudit,
    intentional_restart_observations: { note: "The open page can observe refused connections or reset admission conflicts while the test deliberately stops/restarts/resets services. These legitimate errors are retained separately from the normal 14-route audit.", console_errors: errors, failed_requests: failed, failed_http_statuses: responses },
    cold_start: "passed", persistence: "Source plan, plan digest, idempotency receipt and saved configuration retained across restart", baseline_restoration: "passed", baseline_restart: "passed", ownership_stop: "passed" };
  await writeFile("../docs/PHASE09_4_COLD_START.json", JSON.stringify(result, null, 2));
});
