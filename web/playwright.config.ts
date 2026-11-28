import { defineConfig } from "@playwright/test";

// Browser acceptance runs against an ISOLATED stack by default:
//   web  : a fresh `next start` on E2E_PORT (default 3100), never an existing server
//   api  : E2E_API_BASE_URL (default the isolated acceptance API on :8001)
// Global setup bootstraps a throwaway tenant on that API, so pointing it at the
// live API (:8000) is refused unless E2E_ALLOW_LIVE=1 is set deliberately.
// Run `npm run build` first; the web server serves the production build.
const port = Number(process.env.E2E_PORT ?? 3100);
const apiBase = (process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8001").replace(/\/$/, "");

if (/:8000$/.test(apiBase) && process.env.E2E_ALLOW_LIVE !== "1") {
  throw new Error(
    `Refusing to run browser acceptance against ${apiBase}: it would create a test tenant ` +
      "in the live database. Use the isolated API or set E2E_ALLOW_LIVE=1 deliberately.",
  );
}
process.env.E2E_API_BASE_URL = apiBase;

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: { baseURL: `http://127.0.0.1:${port}`, trace: "retain-on-failure" },
  webServer: {
    command: `npx next start -p ${port}`,
    url: `http://127.0.0.1:${port}/login`,
    reuseExistingServer: false,
    timeout: 120_000,
    env: { FLOWFORGE_API_BASE_URL: apiBase },
  },
});
