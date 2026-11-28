import { expect, test } from "@playwright/test";

import { signIn } from "./auth";
import { act, createLedger, selectContaining, setContext, submitOk, type Ledger } from "./ledger";

let ledger: Ledger;
const vendor = `Acme ${Date.now().toString(36)}`;

test.describe.serial("Accounts payable in the browser", () => {
  test.beforeAll(async () => {
    ledger = await createLedger("AP");
  });

  test("owner creates a vendor and a purchase order, then submits it", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/ap");
    await page.getByRole("tab", { name: "Vendors" }).click();
    const vf = page.getByTestId("vendor-form");
    await vf.locator("#vendor-form-legal_name").fill(vendor);
    await vf.locator("#vendor-form-ap_account_id").selectOption({ label: ledger.account("ap") });
    await submitOk(vf, "Create vendor", "created");
    await expect(page.getByTestId("vendors-table")).toContainText(vendor);

    await page.getByRole("tab", { name: "Purchase orders" }).click();
    const po = page.getByTestId("po-form");
    await selectContaining(po.locator("#po-form-vendor_id"), vendor);
    await po.locator("#po-form-l0-description").fill("Widgets");
    await po.locator("#po-form-l0-quantity").fill("10");
    await po.locator("#po-form-l0-unit_price").fill("30.00");
    await po.locator("#po-form-l0-expense_account_id").selectOption({ label: ledger.account("expense") });
    await submitOk(po, "Create purchase order", "created as draft");

    await page.getByTestId("po-table").getByText(vendor).first().click();
    await act(page, "po-submit", "Submit");
    // The approver approves next (owners may approve their own work; the two-person rule
    // for other creators is covered in finance.spec.ts and the backend workflow tests).
  });

  test("approver approves the purchase order", async ({ page }) => {
    await signIn(page, "approver");
    await page.goto("/modules/ap");
    await page.getByTestId("po-table").getByText(vendor).first().click();
    await act(page, "po-approve", "Approve");
    await expect(page.getByTestId("po-table")).toContainText("approved");
  });

  test("owner receives, invoices, matches, posts, pays and reconciles", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/ap");
    await page.getByTestId("po-table").getByText(vendor).first().click();
    await act(page, "po-receive", "Receive remaining");
    const inv = page.getByTestId("po-invoice-form");
    await inv.locator("#po-invoice-form-invoice_number").fill(`INV-${ledger.code}`);
    await inv.locator("#po-invoice-form-due_date").fill("2030-12-31");
    await submitOk(inv, "Record vendor invoice", "Invoice recorded");

    await page.getByRole("tab", { name: "Invoices" }).click();
    await setContext(page, ledger, { "AP control account": "ap", "Cash account": "cash" });
    await page.getByTestId("invoice-table").getByText(`INV-${ledger.code}`).click();
    await act(page, "invoice-match", "Match to PO and receipt");
    await act(page, "invoice-post", "Post to ledger");
    await expect(page.getByTestId("invoice-table")).toContainText("posted");

    await page.getByRole("tab", { name: "Open items & payments" }).click();
    await setContext(page, ledger, { "AP control account": "ap", "Cash account": "cash" });
    const row = page.getByTestId("ap-open-table").locator("tr", { hasText: vendor });
    await expect(row).toContainText("300.00");
    await row.click();
    const pay = page.getByTestId("ap-pay-form");
    await pay.locator("#ap-pay-form-amount").fill("300.00");
    await submitOk(pay, "Record payment", "recorded and posted");
    await expect(page.getByTestId("ap-open-table").locator("tr", { hasText: vendor })).toHaveCount(0);
    await page.getByTestId("ap-reconcile").click();
    await expect(page.getByTestId("ap-recon-result")).toContainText("reconciled");
  });
});
