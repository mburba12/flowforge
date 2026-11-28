import { expect, test } from "@playwright/test";

import { signIn } from "./auth";
import { submitOk } from "./ledger";

// Approving your own work (owners always; designated people by a switch in Settings),
// the full audit export, and record drop-downs in the More tools forms.

const tag = Date.now().toString(36);

test.describe.serial("Approvals, audit export and record pickers", () => {
  test("owner designates a person who may approve their own work", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/settings");
    const uf = page.getByTestId("user-form");
    const email = `clerk-${tag}@example.com`;
    await uf.locator("#user-form-display_name").fill(`Clerk ${tag}`);
    await uf.locator("#user-form-email").fill(email);
    await uf.locator("#user-form-password").fill(`Clerk-${tag}-pass!`);
    await uf.locator("#user-form-role").selectOption("Clerk");
    await submitOk(uf, "Create user", "created with role Clerk");

    const users = page.getByTestId("users-table");
    const row = users.locator("tr", { hasText: email });
    await expect(row).toContainText("No");
    await row.click();
    await page.getByTestId("self-approve-on").click();
    await expect(row).toContainText("Yes");
    await page.getByTestId("self-approve-off").click();
    await expect(row).toContainText("No");

    // The owner row says owners always may.
    await users.locator("tr", { hasText: "Owner" }).first().click();
    await expect(page.getByTestId("self-approve")).toContainText("Owners can always approve");
  });

  test("audit shows the latest 100 and exports every change", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/audit");
    const card = page.getByTestId("audit-card");
    await expect(card).toContainText("Latest 100 changes");
    await expect(page.getByTestId("audit-table")).toContainText("Who");
    const rows = await page.getByTestId("audit-table").locator("tbody tr").count();
    expect(rows).toBeLessThanOrEqual(100);
    const [download] = await Promise.all([page.waitForEvent("download"), page.getByTestId("audit-export").click()]);
    expect(download.suggestedFilename()).toMatch(/^flowforge-audit-\d{4}-\d{2}-\d{2}\.csv$/);
    const path = await download.path();
    const text = (await import("node:fs")).readFileSync(path, "utf-8");
    expect(text).toContain("occurred_at,user,action,record_type,record_id,details");
    expect(text.trim().split("\n").length - 1).toBeGreaterThanOrEqual(rows);
  });

  test("More tools forms choose records from a drop-down", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/finance-advanced");
    await page.getByRole("searchbox", { name: "Filter operations" }).fill("budgets");
    await page.locator('[data-testid^="op-"][title="/api/v2/finance/advanced/budgets/{version_id}/lines"]').click();
    const form = page.getByTestId("op-form");
    const picker = form.locator('select[data-ref="accounts"]');
    await expect(picker).toBeVisible();
    // Accounts are offered by their code and name, not an id.
    await expect.poll(async () => picker.locator("option").count()).toBeGreaterThan(1);
    const label = await picker.locator("option").nth(1).textContent();
    expect(label ?? "").not.toMatch(/^[0-9a-f]{8}-/);
    // A typed id is still possible.
    await form.getByRole("button", { name: "Enter an id" }).first().click();
    await expect(form.getByPlaceholder("Record id").first()).toBeVisible();
  });
});
