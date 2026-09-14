import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-concierge",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 120000,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-concierge" }],
  ],
  outputDir: "test-results-concierge",
  use: {
    actionTimeout: 15000,
    baseURL: "http://127.0.0.1:5179",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase08_5.serve`,
      url: "http://127.0.0.1:18088/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18043 CONTROL_HOST_URL=http://127.0.0.1:18088 npm run dev -- --port 5179",
      url: "http://127.0.0.1:5179",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
