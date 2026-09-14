import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-knowledge",
  workers: 1,
  retries: 0,
  timeout: 90000,
  use: {
    baseURL: "http://127.0.0.1:5210",
    viewport: { width: 1440, height: 900 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_knowledge_integration.serve --root .cache/phase09-3/phase10-knowledge/${Date.now()} --port 18411 --source-port 18412 --mcp-port 19412 --ui-origin http://127.0.0.1:5210`,
      url: "http://127.0.0.1:18411/control-api/health",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18412 CONTROL_HOST_URL=http://127.0.0.1:18411 npm run dev -- --port 5210",
      url: "http://127.0.0.1:5210",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
