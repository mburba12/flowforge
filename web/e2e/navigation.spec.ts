import { expect, test } from "@playwright/test";

import { expectSignedInShell, signIn } from "./auth";

const workspaces = [
  { path: "/dashboard", label: "Home" },
  { path: "/approvals", label: "Approvals" },
  { path: "/work-queue", label: "Work queue" },
  { path: "/ap", label: "Bills to pay" },
  { path: "/ar", label: "Invoices & payments" },
  { path: "/finance", label: "Accounting" },
  { path: "/banking", label: "Bank accounts" },
  { path: "/tax", label: "Taxes" },
  { path: "/orders", label: "Orders" },
  { path: "/inventory", label: "Inventory" },
  { path: "/shipping", label: "Shipments" },
  { path: "/payroll", label: "Payroll" },
  { path: "/workforce", label: "Employees" },
  { path: "/documents", label: "Files" },
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
      // Legacy top-level routes redirect to their connected /modules workspace.
      const moved: Record<string, string> = {};
      const expected = moved[workspace.path] ?? `/modules${workspace.path}`;
      await expect(page).toHaveURL(new RegExp(`${expected.replaceAll("/", "\\/")}\\/?$`));
      await expectSignedInShell(page);

      const content = page.locator(".shell .main");
      await expect(content).toBeVisible();
      const text = (await content.innerText()).trim();
      expect(text.length, `${workspace.path} rendered too little content`).toBeGreaterThan(20);
      await expect(page.getByText("This page could not be found")).toHaveCount(0);
      await expect(page.getByText("Application error")).toHaveCount(0);
    });
  }

  test("sidebar navigation opens Files", async ({ page }) => {
    await page.locator(".side").getByRole("link", { name: "Files", exact: true }).click();
    await expect(page).toHaveURL(/\/modules\/documents\/?$/);
    await expect(page.getByRole("heading", { name: "Files", level: 1 })).toBeVisible();
    await expectSignedInShell(page);
  });

  test("the sidebar is grouped and specialist tools are folded under More tools", async ({ page }) => {
    const side = page.locator(".side");
    for (const group of ["Money", "Sales", "Products", "People"]) await expect(side.getByText(group, { exact: true })).toBeVisible();
    const more = side.locator(".navMore");
    await expect(more.getByRole("link", { name: "Audit trail" })).toBeHidden();
    await more.locator("summary").click();
    await more.getByRole("link", { name: "Audit trail" }).click();
    await expect(page).toHaveURL(/\/modules\/audit\/?$/);
    await expect(page.getByRole("heading", { name: "Audit trail", level: 1 })).toBeVisible();
    // The group stays open while one of its pages is shown.
    await expect(page.locator(".side .navMore")).toHaveAttribute("open", "");
  });

  test("accounts payable workspace reads live data without errors", async ({ page }) => {
    await page.goto("/modules/ap");
    await expect(page.getByRole("heading", { name: "Bills to pay", level: 1 })).toBeVisible();
    await expect(page.getByTestId("po-form")).toBeVisible();
    await page.getByRole("tab", { name: "Vendors" }).click();
    await expect(page.getByTestId("vendor-form")).toBeVisible();
    await expect(page.locator(".rwNotice.error")).toHaveCount(0);
  });

  test("log out returns to sign-in and protects workspaces", async ({ page }) => {
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login\/?$/);
    await page.goto("/modules/ap");
    await expect(page).toHaveURL(/\/login\/?$/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });
});
