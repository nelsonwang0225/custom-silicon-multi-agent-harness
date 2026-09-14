import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-polish",
  workers: 1,
  retries: 0,
  timeout: 180000,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-polish" }],
  ],
  outputDir: "test-results-polish",
  use: {
    baseURL: "http://127.0.0.1:5194",
    viewport: { width: 1440, height: 900 },
    actionTimeout: 15000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve --root .cache/phase09-3/browser/${Date.now()} --port 18221 --source-port 18222 --mcp-port 19222 --ui-origin http://127.0.0.1:5194`,
      url: "http://127.0.0.1:18221/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18222 CONTROL_HOST_URL=http://127.0.0.1:18221 npm run dev -- --port 5194",
      url: "http://127.0.0.1:5194",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
