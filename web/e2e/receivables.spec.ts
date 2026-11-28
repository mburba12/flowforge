import { expect, test } from "@playwright/test";

import { signIn } from "./auth";
import { act, createLedger, selectContaining, setContext, submitOk, type Ledger } from "./ledger";

let ledger: Ledger;
const tag = Date.now().toString(36).toUpperCase();
const customer = `Globex ${tag}`;
const tightCustomer = `Tight ${tag}`;
const sku = `SKU-${tag}`;

test.describe.serial("Inventory and order-to-cash in the browser", () => {
  test.beforeAll(async () => {
    ledger = await createLedger("AR");
  });

  test("owner sets up a warehouse, product and posted opening stock", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/inventory");
    await page.getByRole("tab", { name: "Warehouses & locations" }).click();
    const wh = page.getByTestId("warehouse-form");
    await wh.locator("#warehouse-form-code").fill(`WH${tag}`);
    await wh.locator("#warehouse-form-name").fill("Main");
    await submitOk(wh, "Create warehouse", "created");
    const loc = page.getByTestId("location-form");
    await selectContaining(loc.locator("#location-form-warehouse_id"), `WH${tag}`);
    await loc.locator("#location-form-code").fill(`A${tag}`);
    await submitOk(loc, "Create location", "created");

    await page.getByRole("tab", { name: "Products" }).click();
    const pf = page.getByTestId("product-form");
    await pf.locator("#product-form-sku").fill(sku);
    await pf.locator("#product-form-name").fill("Gadget");
    await pf.locator("#product-form-sales_price").fill("10.00");
    await pf.locator("#product-form-standard_cost").fill("6.00");
    await pf.locator("#product-form-inventory_account_id").selectOption({ label: ledger.account("inventory") });
    await pf.locator("#product-form-cogs_account_id").selectOption({ label: ledger.account("cogs") });
    await submitOk(pf, "Create product", "created");

    await page.getByRole("tab", { name: "Stock" }).click();
    await setContext(page, ledger, { "Adjustment offset account": "equity" });
    const adj = page.getByTestId("adjust-form");
    await selectContaining(adj.locator("#adjust-form-product_id"), sku);
    await selectContaining(adj.locator("#adjust-form-warehouse_id"), `WH${tag}`);
    await selectContaining(adj.locator("#adjust-form-location_id"), `A${tag}`);
    await adj.locator("#adjust-form-quantity").fill("50");
    await adj.locator("#adjust-form-unit_cost").fill("6.00");
    await submitOk(adj, "Record adjustment", "On hand is now 50");
  });

  test("customers: an order within credit is approved; one over the limit is held", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/orders");
    await page.getByRole("tab", { name: "Customers" }).click();
    for (const [name, limit] of [
      [customer, "10000"],
      [tightCustomer, "10"],
    ]) {
      const cf = page.getByTestId("customer-form");
      await cf.locator("#customer-form-legal_name").fill(name);
      await cf.locator("#customer-form-credit_limit").fill(limit);
      await cf.locator("#customer-form-ar_account_id").selectOption({ label: ledger.account("ar") });
      await cf.locator("#customer-form-revenue_account_id").selectOption({ label: ledger.account("revenue") });
      await submitOk(cf, "Create customer", "created");
    }

    await page.getByRole("tab", { name: "Orders" }).click();
    await setContext(page, ledger, { "AR control account": "ar", "Cash account": "cash" });
    for (const [name, expected] of [
      [customer, "approved"],
      [tightCustomer, "credit hold"],
    ]) {
      const of = page.getByTestId("order-form");
      await selectContaining(of.locator("#order-form-customer_id"), name);
      await selectContaining(of.locator("#order-form-l0-product_id"), sku);
      await of.locator("#order-form-l0-quantity").fill("20");
      await of.locator("#order-form-l0-unit_price").fill("10.00");
      await submitOk(of, "Create order", expected);
    }
  });

  test("reserve, ship and invoice with visible status history, then receive payment", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/orders");
    await setContext(page, ledger, { "AR control account": "ar", "Cash account": "cash" });
    await page.getByTestId("orders-table").locator("tr", { hasText: customer }).first().click();
    await act(page, "order-reserve", "Reserve stock");
    await page.getByLabel("Payment due").fill("2030-12-31");
    await act(page, "order-ship", "Ship and invoice");
    const detail = page.getByTestId("order-detail");
    await expect(detail).toContainText("invoiced");
    await expect(detail).toContainText(/approved.*→.*reserved.*→.*invoiced/);

    await page.getByRole("tab", { name: "Open items & receipts" }).click();
    await setContext(page, ledger, { "AR control account": "ar", "Cash account": "cash" });
    const row = page.getByTestId("ar-open-table").locator("tr", { hasText: customer });
    await expect(row).toContainText("200.00");
    await row.click();
    const rf = page.getByTestId("ar-receipt-form");
    await rf.locator("#ar-receipt-form-amount").fill("200.01");
    await rf.getByRole("button", { name: "Record receipt" }).click();
    await expect(rf.getByRole("alert")).toBeVisible();
    await rf.locator("#ar-receipt-form-amount").fill("200.00");
    await submitOk(rf, "Record receipt", "recorded and posted");
    await expect(page.getByTestId("ar-open-table").locator("tr", { hasText: customer })).toHaveCount(0);

    await page.getByRole("tab", { name: "Aging" }).click();
    await expect(page.getByTestId("ar-aging")).toBeVisible();
  });
});
