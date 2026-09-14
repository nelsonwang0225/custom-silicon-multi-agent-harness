import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-reset",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 180000,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report-reset" }],
  ],
  outputDir: "test-results-reset",
  use: {
    baseURL: "http://127.0.0.1:5191",
    viewport: { width: 1440, height: 1000 },
    actionTimeout: 15000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    },
  },
  webServer: [
    {
      command:
        "MOCK_API_URL=http://127.0.0.1:18192 CONTROL_HOST_URL=http://127.0.0.1:18191 npm run dev -- --port 5191",
      url: "http://127.0.0.1:5191",
      reuseExistingServer: false,
      timeout: 30000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
    },
  ],
});
