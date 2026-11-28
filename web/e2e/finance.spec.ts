import { expect, test, type Page } from "@playwright/test";

import { signIn, signOut } from "./auth";

// One ledger per run so parallel spec files never collide inside the shared tenant.
const code = `L${Date.now().toString(36).slice(-5).toUpperCase()}`;
const now = new Date();
const y = now.getUTCFullYear();
const m = now.getUTCMonth();
const periodStart = new Date(Date.UTC(y, m, 1)).toISOString().slice(0, 10);
const periodEnd = new Date(Date.UTC(y, m + 1, 0)).toISOString().slice(0, 10);
const ledgerLabel = `${code} — ${code} Ledger`;
const periodCode = `${code}-P`;

async function openTab(page: Page, name: string) {
  await page.goto("/modules/finance");
  await page.getByRole("tab", { name }).click();
}

test.describe.serial("General ledger in the browser", () => {
  test("owner sets up a ledger, accounts and an open period", async ({ page }) => {
    await signIn(page);
    await openTab(page, "Ledgers & accounts");

    const calendar = page.getByTestId("calendar-form");
    await calendar.locator("#calendar-form-name").fill(`FY ${code}`);
    await calendar.getByRole("button", { name: "Add calendar" }).click();
    await expect(calendar.getByRole("status")).toContainText("added");

    const ledger = page.getByTestId("ledger-form");
    await ledger.locator("#ledger-form-code").fill(code);
    await ledger.locator("#ledger-form-name").fill(`${code} Ledger`);
    await ledger.getByRole("button", { name: "Add ledger" }).click();
    await expect(ledger.getByRole("status")).toContainText("added");

    const account = page.getByTestId("account-form");
    for (const [num, name, type, normal] of [
      ["1000", "Cash", "asset", "debit"],
      ["3000", "Owner equity", "equity", "credit"],
    ]) {
      await account.locator("#account-form-ledger_id").selectOption({ label: ledgerLabel });
      await account.locator("#account-form-account_code").fill(num);
      await account.locator("#account-form-name").fill(name);
      await account.locator("#account-form-account_type").selectOption(type);
      await account.locator("#account-form-normal_balance").selectOption(normal);
      await account.getByRole("button", { name: "Add account" }).click();
      await expect(account.getByRole("status")).toContainText(`Account ${num} added`);
    }
    await expect(page.getByTestId("accounts-table")).toContainText("Owner equity");

    await page.getByRole("tab", { name: "Periods" }).click();
    const period = page.getByTestId("period-form");
    await period.locator("#period-form-calendar_id").selectOption({ label: `FY ${code}` });
    await period.locator("#period-form-period_code").fill(periodCode);
    await period.locator("#period-form-start_date").fill(periodStart);
    await period.locator("#period-form-end_date").fill(periodEnd);
    await period.getByRole("button", { name: "Create period" }).click();
    await expect(period.getByRole("status")).toContainText("created");
    await expect(page.getByTestId("periods-table")).toContainText(periodCode);
  });

  test("owner records a balanced journal; an unbalanced one is refused", async ({ page }) => {
    await signIn(page);
    await openTab(page, "Journals");
    const form = page.getByTestId("journal-form");
    await form.locator("#journal-form-ledger_id").selectOption({ label: ledgerLabel });
    await form.locator("#journal-form-period_id").selectOption({ label: `${periodCode} (${periodStart} to ${periodEnd})` });
    await form.locator("#journal-form-description").fill(`Capital ${code}`);
    await form.locator("#journal-form-l0-account_id").selectOption({ label: "1000 Cash" });
    await form.locator("#journal-form-l0-debit").fill("100.00");
    await form.locator("#journal-form-l1-account_id").selectOption({ label: "3000 Owner equity" });
    await form.locator("#journal-form-l1-credit").fill("90.00");
    await form.getByRole("button", { name: "Create journal" }).click();
    await expect(form.getByRole("alert")).toBeVisible();

    await form.locator("#journal-form-l1-credit").fill("100.00");
    await form.getByRole("button", { name: "Create journal" }).click();
    await expect(form.getByRole("status")).toContainText("Journal created");

    // Segregation of duties: the creator cannot approve their own journal.
    await page.getByTestId("journals-table").getByText(`Capital ${code}`).click();
    await page.getByTestId("journal-approve").click();
    await expect(page.getByRole("alert").filter({ hasText: "Approve" })).toContainText(/cannot approve/i);
  });

  test("approver approves and posts; the trial balance balances", async ({ page }) => {
    await signIn(page, "approver");
    await openTab(page, "Journals");
    await page.getByTestId("journals-table").getByText(`Capital ${code}`).click();
    await page.getByTestId("journal-approve").click();
    await expect(page.getByRole("status").filter({ hasText: "Approve" })).toContainText("done");
    await page.getByTestId("journal-post").click();
    await expect(page.getByRole("status").filter({ hasText: "Post" })).toContainText("done");
    await expect(page.getByTestId("journals-table")).toContainText("posted");

    await page.getByRole("tab", { name: "Trial balance" }).click();
    await page.getByLabel("Ledger").selectOption({ label: ledgerLabel });
    await page.getByLabel("Period").selectOption({ label: `${periodCode} (open)` });
    await expect(page.getByTestId("tb-totals")).toContainText("100.00");
    await expect(page.getByTestId("tb-totals")).toContainText("balanced");
    await signOut(page);
  });
});
