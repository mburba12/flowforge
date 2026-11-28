import { expect, test } from "@playwright/test";

import { signIn } from "./auth";

// Billing & usage (estimate, calculator, card on file, invoices) and hiding / showing
// parts of the screen (Settings -> Customize your screen).

test.describe.serial("Billing & usage and screen customization", () => {
  test("owner sees this month's estimate and prices a month with the calculator", async ({ page }) => {
    await signIn(page);
    await page.locator(".side").getByRole("link", { name: "Billing & usage" }).click();
    await expect(page.getByRole("heading", { name: "Billing & usage", level: 1 })).toBeVisible();
    await expect(page.getByTestId("billing-estimate-table")).toContainText("Storage");
    await expect(page.getByTestId("billing-estimate-table")).toContainText("Card payment processing");
    await expect(page.getByTestId("billing-invoices")).toContainText("No invoices yet");

    const calc = page.getByTestId("billing-calculator");
    await calc.getByTestId("calc-storage").fill("0.3");
    await calc.getByTestId("calc-actions").fill("40000");
    await calc.getByTestId("calc-run").click();
    await expect(calc.getByTestId("calc-total")).toContainText("$6.94");

    // Saving a card needs the owner's agreement to automatic charges (and Stripe on the server).
    const card = page.getByTestId("billing-card");
    await expect(card).toContainText("No card on file");
    await expect(card.getByTestId("billing-add-card")).toBeDisabled();
    await card.getByTestId("billing-authorize").check();
    await expect(card).toContainText("Stripe key is missing");
  });

  test("a manager can see billing but not change the card", async ({ page }) => {
    await signIn(page, "approver");
    await page.goto("/modules/plan");
    await expect(page.getByTestId("billing-card")).toContainText("Only the workspace owner can change the card");
  });

  test("each person can hide and show sidebar sections and home parts", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/settings");
    const custom = page.getByTestId("customize");
    await expect(custom.getByTestId("show-nav:settings")).toBeDisabled(); // Settings always stays
    await custom.getByTestId("show-nav:crm").uncheck();
    await custom.getByTestId("show-home:quick").uncheck();
    await expect(custom.getByTestId("customize-status")).toHaveText("All changes saved.");
    await expect(page.locator(".side")).not.toContainText("Customers & deals");

    await page.locator(".side").getByRole("link", { name: "Home" }).click();
    await expect(page.getByRole("navigation", { name: "Quick actions" })).toHaveCount(0);
    // It is remembered on the server: still hidden after signing in again.
    await page.getByRole("button", { name: "Log out" }).click();
    await signIn(page);
    await expect(page.locator(".side")).not.toContainText("Customers & deals");
    await expect(page.getByRole("navigation", { name: "Quick actions" })).toHaveCount(0);
    // The other user's screen is not affected.
    await page.getByRole("button", { name: "Log out" }).click();
    await signIn(page, "approver");
    await expect(page.locator(".side")).toContainText("Customers & deals");
    await page.getByRole("button", { name: "Log out" }).click();

    await signIn(page);
    await page.goto("/modules/settings");
    await page.getByTestId("customize").getByRole("button", { name: "Show everything" }).click();
    await expect(page.locator(".side")).toContainText("Customers & deals");
    await page.locator(".side").getByRole("link", { name: "Home" }).click();
    await expect(page.getByRole("navigation", { name: "Quick actions" })).toBeVisible();
  });
});
