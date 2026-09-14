import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir:"./e2e-product",workers:1,retries:0,timeout:180000,
  reporter:[["list"],["html",{open:"never",outputFolder:"playwright-report-product"}]],outputDir:"test-results-product",
  use:{baseURL:"http://127.0.0.1:5192",viewport:{width:1440,height:1000},actionTimeout:15000,trace:"retain-on-failure",screenshot:"only-on-failure",launchOptions:{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}},
  webServer:[
    {command:`cd .. && PYTHONPATH=src:. coordinator/.venv/bin/python -m coordinator.evals.phase09_1.serve --root .cache/phase09-2/browser/${Date.now()} --port 18201 --source-port 18202 --mcp-port 19202 --ui-origin http://127.0.0.1:5192`,url:"http://127.0.0.1:18201/control-api/health",reuseExistingServer:false,timeout:30000,gracefulShutdown:{signal:"SIGTERM",timeout:10000}},
    {command:"MOCK_API_URL=http://127.0.0.1:18202 CONTROL_HOST_URL=http://127.0.0.1:18201 npm run dev -- --port 5192",url:"http://127.0.0.1:5192",reuseExistingServer:false,timeout:30000,gracefulShutdown:{signal:"SIGTERM",timeout:10000}},
  ],
});
