import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-quality",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 90000,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-quality" }],
  ],
  outputDir: "test-results-quality",
  use: {
    baseURL: "http://127.0.0.1:5177",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase08_4b.serve --variant ${process.env.QUALITY_VARIANT || "comparable"}`,
      url: "http://127.0.0.1:18086/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18041 CONTROL_HOST_URL=http://127.0.0.1:18086 npm run dev -- --port 5177",
      url: "http://127.0.0.1:5177",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
