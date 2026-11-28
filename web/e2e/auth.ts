import { expect, type Page } from "@playwright/test";

/** Sign in through the real form with the tenant created by global setup. */
export async function signIn(page: Page, as: "owner" | "approver" = "owner"): Promise<void> {
  const tenant = process.env.E2E_TENANT;
  const email = as === "owner" ? process.env.E2E_EMAIL : process.env.E2E_APPROVER_EMAIL;
  const password = process.env.E2E_PASSWORD;
  if (!tenant || !email || !password) {
    throw new Error("Browser acceptance credentials are missing; global setup did not run.");
  }

  await page.goto("/login");
  await page.locator("#tenant").fill(tenant);
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/modules\/dashboard\/?$/);
  await expectSignedInShell(page);
}

/** The signed-in application chrome is present and the sign-in form is not. */
export async function expectSignedInShell(page: Page): Promise<void> {
  await expect(page.locator(".shell aside nav")).toBeVisible();
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sign in" })).toHaveCount(0);
}

/** Log out through the shell button and wait for the sign-in page. */
export async function signOut(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login\/?$/);
}