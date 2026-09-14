import { defineConfig } from "@playwright/test";

// SOURCE_UI_URL targets an explicitly selected, already-running isolated session.
// Without it, Playwright owns a new deterministic fixture and never resets data.
const suppliedURL = process.env.SOURCE_UI_URL;
if (suppliedURL && !/^http:\/\/127\.0\.0\.1:\d+\/?$/.test(suppliedURL)) {
  throw new Error("SOURCE_UI_URL must be an explicit loopback HTTP origin");
}
const baseURL = suppliedURL?.replace(/\/$/, "") || "http://127.0.0.1:5251";
const run = `${Date.now()}-${process.pid}`;

export default defineConfig({
  testDir: "./e2e-sources",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120000,
  expect: { timeout: 15000 },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-sources" }],
  ],
  outputDir: "test-results-sources",
  use: {
    baseURL,
    actionTimeout: 15000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  projects: [
    { name: "desktop-1440", use: { viewport: { width: 1440, height: 900 } } },
    { name: "desktop-1920", use: { viewport: { width: 1920, height: 1080 } } },
    { name: "desktop-1280", use: { viewport: { width: 1280, height: 800 } } },
  ],
  webServer: suppliedURL
    ? []
    : [
        {
          command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve --root .cache/phase09-3/source-redesign/${run} --port 18651 --source-port 18652 --mcp-port 19652 --ui-origin http://127.0.0.1:5251`,
          url: "http://127.0.0.1:18651/control-api/health",
          reuseExistingServer: false,
          timeout: 45000,
          gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
        },
        {
          command:
            "MOCK_API_URL=http://127.0.0.1:18652 CONTROL_HOST_URL=http://127.0.0.1:18651 npm run dev -- --port 5251",
          url: baseURL,
          reuseExistingServer: false,
          timeout: 30000,
          gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
        },
      ],
});
