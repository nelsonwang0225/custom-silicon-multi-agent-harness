import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-persona",
  workers: 1,
  retries: 0,
  timeout: 90000,
  reporter: [
    ["list"],
    ["json", { outputFile: "../.cache/phase10-1/browser-results.json" }],
  ],
  outputDir: "../.cache/phase10-1/browser-results",
  use: {
    baseURL: "http://127.0.0.1:5202",
    viewport: { width: 1440, height: 900 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve --root .cache/phase09-3/phase10-1/${Date.now()} --port 18311 --source-port 18312 --mcp-port 19312 --ui-origin http://127.0.0.1:5202`,
      url: "http://127.0.0.1:18311/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18312 CONTROL_HOST_URL=http://127.0.0.1:18311 npm run dev -- --port 5202",
      url: "http://127.0.0.1:5202",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
