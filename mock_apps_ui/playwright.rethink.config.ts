import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-rethink",
  workers: 1,
  retries: 0,
  timeout: 60000,
  reporter: [
    ["list"],
    [
      "json",
      { outputFile: "../.cache/rethink-implementation/browser-results.json" },
    ],
  ],
  outputDir: "../.cache/rethink-implementation/browser-output",
  use: {
    baseURL: "http://127.0.0.1:5221",
    viewport: { width: 1440, height: 900 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve --root .cache/phase09-3/rethink/${Date.now()} --port 18521 --source-port 18522 --mcp-port 19522 --ui-origin http://127.0.0.1:5221`,
      url: "http://127.0.0.1:18521/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18522 CONTROL_HOST_URL=http://127.0.0.1:18521 npm run dev -- --port 5221",
      url: "http://127.0.0.1:5221",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
