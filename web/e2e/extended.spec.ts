import { expect, type Page, test } from "@playwright/test";

import { expectSignedInShell, signIn } from "./auth";

// Extended domains: generated from the server's operation catalog. Every workspace must
// list its operations; a create-then-read round trip proves the generated forms work.
const workspaces: [slug: string, title: string][] = [
  ["crm", "CRM & sales"],
  ["commerce", "Procurement & logistics"],
  ["finance-advanced", "Close, budgets & assets"],
  ["payroll-tax", "Payroll & tax operations"],
  ["talent", "HR & talent"],
  ["master-data", "Master data"],
  ["billing", "Subscriptions & projects"],
  ["manufacturing", "Manufacturing & quality"],
  ["copilot", "Knowledge & copilot"],
  ["operations", "Operations runs"],
  ["governance", "Governance & controls"],
  ["integrations", "Integrations"],
  ["entities", "Entities"],
];

function operation(page: Page, method: string, path: string) {
  return page.locator(`[data-testid^="op-"][title="${path}"]`).filter({ hasText: method });
}

test.describe("Extended workspaces (signed in)", () => {
  test.beforeEach(async ({ page }) => {
    await signIn(page);
  });

  for (const [slug, title] of workspaces) {
    test(`${title} lists its operations`, async ({ page }) => {
      await page.goto(`/modules/${slug}`);
      await expectSignedInShell(page);
      await expect(page.getByRole("heading", { name: title, level: 1 })).toBeVisible();
      const console = page.getByTestId("ops-console");
      await expect(console).toBeVisible();
      expect(await console.locator('[data-testid^="op-"]').count()).toBeGreaterThan(0);
      await expect(page.locator(".rwNotice.error")).toHaveCount(0);
      await page.getByRole("tab", { name: /Records/ }).click();
      await expect(page.getByText("Application error")).toHaveCount(0);
    });
  }

  test("CRM lead: create through the generated form, then read it back", async ({ page }) => {
    const number = `L-${Date.now()}`;
    await page.goto("/modules/crm");
    await page.getByRole("searchbox", { name: "Filter operations" }).fill("leads");
    await operation(page, "POST", "/api/v2/crm/leads").click();
    const form = page.getByTestId("op-form");
    await form.getByLabel(/^Lead number/).fill(number);
    await form.getByLabel(/^Contact name/).fill("Pat Example");
    await form.getByLabel(/^Company name/).fill("Example Supplies");
    await form.getByTestId("op-run").click();
    await expect(form.locator(".rwNotice.ok")).toBeVisible();
    await expect(form.getByTestId("op-result")).toContainText(number);

    await operation(page, "GET", "/api/v2/crm/final/leads").click();
    await page.getByTestId("op-form").getByTestId("op-run").click();
    await expect(page.getByTestId("op-result")).toContainText(number);
  });

  test("validation errors from the server are shown on the form", async ({ page }) => {
    await page.goto("/modules/crm");
    await operation(page, "POST", "/api/v2/crm/leads").click();
    const form = page.getByTestId("op-form");
    await form.getByLabel(/^Contact name/).fill("No number");
    await form.getByLabel(/^Lead number/).fill("x");
    await form.getByLabel(/^Lead number/).fill("");
    // Required in the browser too; remove the attribute to prove the server validates.
    await form.getByLabel(/^Lead number/).evaluate((el) => el.removeAttribute("required"));
    await form.getByTestId("op-run").click();
    await expect(form.locator(".rwNotice.error")).toContainText(/lead_number/i);
  });

  test("release workspaces expose all their operations", async ({ page }) => {
    await page.goto("/modules/ap");
    const all = page.getByTestId("all-operations");
    await expect(all).toBeVisible();
    await all.locator("summary").click();
    expect(await all.locator('[data-testid^="op-"]').count()).toBeGreaterThan(5);
  });

  test("legacy enterprise routes open the connected workspaces", async ({ page }) => {
    await page.goto("/enterprise/crm");
    await expect(page).toHaveURL(/\/modules\/crm\/?$/);
    await expect(page.getByTestId("ops-console")).toBeVisible();
  });
});
