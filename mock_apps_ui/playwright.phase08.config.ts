import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-connected",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 90000,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-connected" }],
  ],
  outputDir: "test-results-connected",
  use: {
    baseURL: "http://127.0.0.1:5175",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: {
    command:
      "MOCK_API_URL=http://127.0.0.1:18020 CONTROL_HOST_URL=http://127.0.0.1:18083 npm run dev -- --port 5175",
    url: "http://127.0.0.1:5175",
    reuseExistingServer: !!process.env.PHASE08_REUSE_PREVIEW,
    gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
  },
});
