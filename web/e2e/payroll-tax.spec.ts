import { expect, test } from "@playwright/test";

import { signIn, signOut } from "./auth";
import { act, createLedger, selectContaining, setContext, submitOk, type Ledger } from "./ledger";

let ledger: Ledger;
const tag = Date.now().toString(36).toUpperCase();
const lastName = `Rivera${tag}`;
const group = `SM${tag}`;
const payPeriod = `PP${tag}`;
const payrollAccounts = {
  "Wage expense": "wages",
  "Employer tax expense": "erTaxExpense",
  "Employee tax payable": "eeTax",
  "Employer tax payable": "erTax",
  "Deductions payable": "deductions",
  "Net pay payable": "netPay",
  Cash: "cash",
} as const;

test.describe.serial("Payroll and tax in the browser", () => {
  test.beforeAll(async () => {
    ledger = await createLedger("PY");
  });

  test("owner adds a worker, pay group and pay period", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/workforce");
    const wf = page.getByTestId("worker-form");
    await wf.locator("#worker-form-given_name").fill("Dana");
    await wf.locator("#worker-form-family_name").fill(lastName);
    await wf.locator("#worker-form-hourly_rate").fill("30.00");
    await submitOk(wf, "Add worker", "30.00/hour");
    await expect(page.getByTestId("workers-table")).toContainText(lastName);

    await page.getByRole("tab", { name: "Pay groups & periods" }).click();
    const gf = page.getByTestId("pay-group-form");
    await gf.locator("#pay-group-form-code").fill(group);
    await gf.locator("#pay-group-form-name").fill("Semimonthly");
    await submitOk(gf, "Create pay group", "created");
    const now = new Date();
    const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString().slice(0, 10);
    const mid = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 15)).toISOString().slice(0, 10);
    const pay = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 20)).toISOString().slice(0, 10);
    const pf = page.getByTestId("pay-period-form");
    await selectContaining(pf.locator("#pay-period-form-pay_group_id"), group);
    await pf.locator("#pay-period-form-period_code").fill(payPeriod);
    await pf.locator("#pay-period-form-start_date").fill(start);
    await pf.locator("#pay-period-form-end_date").fill(mid);
    await pf.locator("#pay-period-form-pay_date").fill(pay);
    await submitOk(pf, "Create pay period", "created");
  });

  test("owner creates and calculates a run (gross 2680.00, net 2347.00)", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/payroll");
    await setContext(page, ledger, payrollAccounts);
    const rf = page.getByTestId("run-form");
    await selectContaining(rf.locator("#run-form-pay_group_id"), group);
    await selectContaining(rf.locator("#run-form-pay_period_id"), payPeriod);
    await submitOk(rf, "Create run", "created as draft");
    const calc = page.getByTestId("run-calc-form");
    await selectContaining(calc.locator("#run-calc-form-l0-worker_id"), lastName);
    await calc.locator("#run-calc-form-l0-overtime_hours").fill("4");
    await calc.locator("#run-calc-form-l0-bonus").fill("100");
    await calc.locator("#run-calc-form-l0-pretax_deductions").fill("50");
    await calc.locator("#run-calc-form-l0-posttax_deductions").fill("20");
    await submitOk(calc, "Calculate", "Calculated");
    const detail = page.getByTestId("run-detail");
    await expect(detail).toContainText("2,680.00");
    await expect(detail).toContainText("2,347.00");
    await page.getByTestId("run-approve").click();
    await expect(page.getByRole("alert").filter({ hasText: "Approve:" })).toContainText(/cannot approve/i);
  });

  test("approver approves; owner posts, pays, reconciles", async ({ page }) => {
    await signIn(page, "approver");
    await page.goto("/modules/payroll");
    await page.getByTestId("runs-table").locator("tr", { hasText: "calculated" }).first().click();
    await act(page, "run-approve", "Approve");
    await signOut(page);

    await signIn(page);
    await page.goto("/modules/payroll");
    await setContext(page, ledger, payrollAccounts);
    await page.getByTestId("runs-table").locator("tr", { hasText: "approved" }).first().click();
    await act(page, "run-post", "Post to ledger");
    const pay = page.getByTestId("run-pay-form");
    await selectContaining(pay.locator("#run-pay-form-worker_id"), lastName);
    await pay.locator("#run-pay-form-amount").fill("2347.01");
    await pay.getByRole("button", { name: "Record payment" }).click();
    await expect(pay.getByRole("alert")).toContainText(/exceeds/i);
    await pay.locator("#run-pay-form-amount").fill("2347.00");
    await submitOk(pay, "Record payment", "Paid 2347.00");
    await page.getByTestId("run-reconcile").click();
    await expect(page.getByTestId("run-recon")).toContainText("reconciled");
  });

  test("tax: authority, liabilities from payroll, return, approval, remittance, reconciliation", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/tax");
    await page.getByRole("tab", { name: "Jurisdictions & rules" }).click();
    const jf = page.getByTestId("jurisdiction-form");
    await jf.locator("#jurisdiction-form-code").fill(`US-${tag}`);
    await jf.locator("#jurisdiction-form-name").fill(`Federal ${tag}`);
    await jf.locator("#jurisdiction-form-level").selectOption("federal");
    await submitOk(jf, "Create jurisdiction", "created");

    await page.getByRole("tab", { name: "Authorities" }).click();
    const af = page.getByTestId("authority-form");
    await selectContaining(af.locator("#authority-form-jurisdiction_id"), `US-${tag}`);
    await af.locator("#authority-form-code").fill(`IRS${tag}`);
    await af.locator("#authority-form-name").fill("Internal Revenue");
    await submitOk(af, "Create authority", "created");

    await page.getByRole("tab", { name: "Liabilities" }).click();
    const lf = page.getByTestId("liability-form");
    await lf.locator("#liability-form-payroll_run_id").selectOption({ index: 1 });
    await selectContaining(lf.locator("#liability-form-authority_id"), `IRS${tag}`);
    await lf.locator("#liability-form-due_date").fill("2030-12-31");
    await submitOk(lf, "Create liabilities", "employee_tax 263");

    await page.getByRole("tab", { name: "Returns & remittance" }).click();
    const ret = page.getByTestId("return-form");
    await selectContaining(ret.locator("#return-form-authority_id"), `IRS${tag}`);
    await ret.locator("#return-form-period_code").fill(`Q${tag}`);
    await ret.locator("#return-form-period_start").fill("2030-01-01");
    await ret.locator("#return-form-period_end").fill("2030-03-31");
    await ret.locator("#return-form-due_date").fill("2030-04-30");
    await ret.locator("#return-form-tax_code").fill("OASDI");
    await ret.locator("#return-form-taxable_wages").fill("2630.00");
    await ret.locator("#return-form-tax_amount").fill("263.00");
    await submitOk(ret, "Create return", "created as draft");
  });

  test("approver approves the return; owner remits and reconciles", async ({ page }) => {
    await signIn(page, "approver");
    await page.goto("/modules/tax");
    await page.getByTestId("returns-table").locator("tr", { hasText: `Q${tag}` }).click();
    await act(page, "return-approve", "Approve");
    await signOut(page);

    await signIn(page);
    await page.goto("/modules/tax");
    await setContext(page, ledger, { "Tax payable account": "eeTax", "Cash account": "cash" });
    await page.getByTestId("returns-table").locator("tr", { hasText: `Q${tag}` }).click();
    const rm = page.getByTestId("remit-form");
    await selectContaining(rm.locator("#remit-form-liability_id"), "employee_tax open 263");
    await rm.locator("#remit-form-amount").fill("263.00");
    await submitOk(rm, "Remit and post", "Remitted 263.00");
    // Employee tax is now paid; the employer-tax liability (201.20) remains, booked to the
    // employer tax payable account, so reconcile the authority against that account.
    await page
      .getByRole("region", { name: "Posting context" })
      .getByLabel("Tax payable account", { exact: true })
      .selectOption({ label: ledger.account("erTax").split(" · ")[1] });
    await selectContaining(page.getByLabel("Reconcile authority"), `IRS${tag}`);
    await page.getByTestId("tax-reconcile").click();
    await expect(page.getByTestId("tax-recon")).toContainText("reconciled");
  });
});
