import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-standard",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 90000,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-standard" }],
  ],
  outputDir: "test-results-standard",
  use: {
    baseURL: "http://127.0.0.1:5176",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase08_4a.serve --variant ${process.env.STANDARD_VARIANT || "success"}`,
      url: "http://127.0.0.1:18085/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18040 CONTROL_HOST_URL=http://127.0.0.1:18085 npm run dev -- --port 5176",
      url: "http://127.0.0.1:5176",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
