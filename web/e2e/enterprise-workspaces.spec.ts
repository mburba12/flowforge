import { expect, test } from "@playwright/test";

import { expectSignedInShell, signIn } from "./auth";

const routes = [
  "platform",
  "master-data",
  "finance",
  "crm",
  "commerce",
  "workforce",
  "payroll-tax",
  "billing",
  "projects",
  "assets",
  "manufacturing",
  "quality",
  "reporting",
  "copilot",
  "integrations",
  "operations",
];

test.describe("Enterprise workspaces (signed in)", () => {
  test.beforeEach(async ({ page }) => {
    await signIn(page);
  });

  for (const route of routes) {
    test(`enterprise ${route}`, async ({ page }) => {
      await page.goto(`/enterprise/${route}`);
      await expectSignedInShell(page);
      await expect(page.locator(".shell .main h1").first()).toBeVisible();
      await expect(page.getByText("Application error")).toHaveCount(0);
    });
  }
});
