import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
const target = process.env.MOCK_API_URL || "http://127.0.0.1:8000";
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(target))
  throw new Error("MOCK_API_URL must use loopback HTTP");
const hostTarget = process.env.CONTROL_HOST_URL || "http://127.0.0.1:18082";
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(hostTarget))
  throw new Error("CONTROL_HOST_URL must use loopback HTTP");
export default defineConfig({
  plugins: [react()],
  define: { __STRATOS_SOURCE_URL__: JSON.stringify(target) },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    fs: {
      allow: [import.meta.dirname],
      deny: [
        ".env",
        ".env.*",
        "*.{crt,pem}",
        "**/.git/**",
        "**/e2e/**",
        "**/e2e-connected/**",
        "**/test-results-connected/**",
        "**/playwright-report-connected/**",
        "**/playwright.phase08.config.ts",
        "**/test-results/**",
        "**/playwright-report/**",
        "**/playwright.config.ts",
      ],
    },
    proxy: { "/control-api": { target: hostTarget }, "/api": { target } },
  },
  preview: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { "/control-api": { target: hostTarget }, "/api": { target } },
  },
});
