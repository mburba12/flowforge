import { expect, test } from "@playwright/test";

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

test.describe("FlowForge workspace navigation", () => {
  for (const workspace of workspaces) {
    test(`${workspace.label} is reachable`, async ({ page }) => {
      const response = await page.goto(workspace.path, {
        waitUntil: "domcontentloaded",
      });

      expect(
        response,
        `${workspace.path} did not return a response`,
      ).not.toBeNull();

      expect(
        response?.status(),
        `${workspace.path} returned an HTTP error`,
      ).toBeLessThan(400);

      await expect(page).toHaveURL(
        new RegExp(
          `${workspace.path.replaceAll("/", "\\/")}\\/?$`,
        ),
      );

      const applicationMain = page.locator(
        "body > div > main, body > main, .app-shell > main",
      ).first();

      await expect(
        applicationMain,
        `${workspace.path} has no visible application content`,
      ).toBeVisible();

      await expect(
        applicationMain,
        `${workspace.path} rendered no meaningful content`,
      ).not.toBeEmpty();

      const visibleText = (
        await applicationMain.innerText()
      ).trim();

      expect(
        visibleText.length,
        `${workspace.path} contains too little visible content`,
      ).toBeGreaterThan(20);

      await expect(
        page.getByText("This page could not be found", {
          exact: false,
        }),
      ).toHaveCount(0);

      await expect(
        page.getByText("Application error", {
          exact: false,
        }),
      ).toHaveCount(0);
    });
  }

  test("sidebar navigation opens Documents", async ({ page }) => {
    await page.goto("/dashboard", {
      waitUntil: "domcontentloaded",
    });

    const documentsLink = page.getByRole("link", {
      name: "Documents",
      exact: true,
    });

    await expect(documentsLink).toBeVisible();
    await documentsLink.click();

    await expect(page).toHaveURL(/\/documents\/?$/);

    await expect(
      page.locator(
        "body > div > main, body > main, .app-shell > main",
      ).first(),
    ).toBeVisible();
  });
});