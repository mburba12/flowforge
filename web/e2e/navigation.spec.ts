import { expect, test } from "@playwright/test";

import { expectSignedInShell, signIn } from "./auth";

const workspaces = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/approvals", label: "Approvals" },
  { path: "/work-queue", label: "Work queue" },
  { path: "/ap", label: "Accounts payable" },
  { path: "/ar", label: "Accounts receivable" },
  { path: "/finance", label: "Finance" },
  { path: "/banking", label: "Banking" },
  { path: "/tax", label: "Tax" },
  { path: "/orders", label: "Orders" },
  { path: "/inventory", label: "Inventory" },
  { path: "/shipping", label: "Shipping" },
  { path: "/payroll", label: "Payroll" },
  { path: "/workforce", label: "Workforce" },
  { path: "/documents", label: "Documents" },
  { path: "/reconciliation", label: "Reconciliation" },
  { path: "/entities", label: "Entities" },
  { path: "/reports", label: "Reports" },
  { path: "/audit", label: "Audit" },
  { path: "/integrations", label: "Integrations" },
  { path: "/billing", label: "Billing" },
  { path: "/settings", label: "Settings" },
  { path: "/support", label: "Support" },
] as const;

test.describe("FlowForge workspace navigation (signed in)", () => {
  test.beforeEach(async ({ page }) => {
    await signIn(page);
  });

  for (const workspace of workspaces) {
    test(`${workspace.label} loads inside the signed-in shell`, async ({ page }) => {
      const response = await page.goto(workspace.path, { waitUntil: "domcontentloaded" });
      expect(response?.status(), `${workspace.path} returned an HTTP error`).toBeLessThan(400);
      await expect(page).toHaveURL(new RegExp(`${workspace.path.replaceAll("/", "\\/")}\\/?$`));
      await expectSignedInShell(page);

      const content = page.locator(".shell .main");
      await expect(content).toBeVisible();
      const text = (await content.innerText()).trim();
      expect(text.length, `${workspace.path} rendered too little content`).toBeGreaterThan(20);
      await expect(page.getByText("This page could not be found")).toHaveCount(0);
      await expect(page.getByText("Application error")).toHaveCount(0);
    });
  }

  test("sidebar navigation opens the Documents workspace", async ({ page }) => {
    await page.getByRole("link", { name: "Documents", exact: true }).click();
    await expect(page).toHaveURL(/\/modules\/documents\/?$/);
    await expect(page.getByRole("heading", { name: "Documents", level: 1 })).toBeVisible();
    await expectSignedInShell(page);
  });

  test("accounts payable workspace reads live data without errors", async ({ page }) => {
    await page.goto("/modules/ap");
    await expect(page.getByRole("heading", { name: "Accounts payable", level: 1 })).toBeVisible();
    await page.locator(".commandbar select").selectOption("purchase-orders");
    await expect(page.locator(".dataCard .cardTitle span")).toHaveText(/\d+ records/);
    await expect(page.locator(".notice")).toHaveCount(0);
  });

  test("log out returns to sign-in and protects workspaces", async ({ page }) => {
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login\/?$/);
    await page.goto("/modules/ap");
    await expect(page).toHaveURL(/\/login\/?$/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });
});
