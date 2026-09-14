import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e-harness", workers: 1, fullyParallel: false, retries: 0,
  timeout: 240000, reporter: [["list"]], outputDir: "test-results-harness",
  use: { baseURL: "http://127.0.0.1:5196", viewport: { width: 1440, height: 900 },
    screenshot: "only-on-failure", trace: "retain-on-failure",
    launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } },
});
