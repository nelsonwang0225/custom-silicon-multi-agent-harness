import { defineConfig } from "@playwright/test";
export default defineConfig({
  outputDir: "../.cache/phase10-autonomous/browser-results",
  reporter: [["list"], ["json", {outputFile: "../.cache/phase10-autonomous/browser-results.json"}]],
  testDir: "./e2e-autonomous", workers: 1, retries: 0, timeout: 210000,
  use: { baseURL: "http://127.0.0.1:5231", viewport: {width:1440,height:900},
    trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: [
    { command: `cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase10_knowledge_integration.serve --root .cache/phase09-3/phase10-autonomous/${Date.now()} --port 18531 --source-port 18532 --mcp-port 19532 --ui-origin http://127.0.0.1:5231 --cr-delay 2`,
      url: "http://127.0.0.1:18531/control-api/health", reuseExistingServer: false, timeout: 30000,
      gracefulShutdown: {signal:"SIGTERM",timeout:10000}},
    { command: "MOCK_API_URL=http://127.0.0.1:18532 CONTROL_HOST_URL=http://127.0.0.1:18531 npm run dev -- --port 5231 --strictPort",
      url: "http://127.0.0.1:5231", reuseExistingServer: false, timeout:30000,
      gracefulShutdown: {signal:"SIGTERM",timeout:10000}},
  ],
});
