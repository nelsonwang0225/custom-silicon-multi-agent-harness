import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-workspace",
  workers: 1,
  retries: 0,
  timeout: 90000,
  reporter: [
    ["list"],
    ["json", { outputFile: "../.cache/phase10-2/browser-results.json" }],
  ],
  outputDir: "../.cache/phase10-2/browser-results",
  use: {
    browserName: process.env.STRATOS_TEST_BROWSER === "webkit" ? "webkit" : "chromium",
    baseURL: "http://127.0.0.1:5204",
    viewport: { width: 1440, height: 900 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.STRATOS_TEST_BROWSER === "webkit" ? undefined : process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve --root .cache/phase09-3/phase10-2/${Date.now()} --port 18331 --source-port 18332 --mcp-port 19332 --ui-origin http://127.0.0.1:5204`,
      url: "http://127.0.0.1:18331/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18332 CONTROL_HOST_URL=http://127.0.0.1:18331 npm run dev -- --port 5204",
      url: "http://127.0.0.1:5204",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
