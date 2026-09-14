import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-delivery",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 90000,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-delivery" }],
  ],
  outputDir: "test-results-delivery",
  use: {
    baseURL: "http://127.0.0.1:5178",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase08_4c.serve --variant ${process.env.DELIVERY_VARIANT || "base"}`,
      url: "http://127.0.0.1:18087/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18042 CONTROL_HOST_URL=http://127.0.0.1:18087 npm run dev -- --port 5178",
      url: "http://127.0.0.1:5178",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
