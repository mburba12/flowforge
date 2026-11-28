import { expect, test } from "@playwright/test";

import { expectSignedInShell } from "./auth";

// The website's Log in and Sign up buttons open these pages with details in the address
// fragment (#email=…); the password is only ever typed here, in the app.

const tag = Date.now().toString(36);

test.describe.serial("Sign in and sign up from the website", () => {
  test("Log in from the website: email filled in, password typed in the app", async ({ page }) => {
    const email = process.env.E2E_EMAIL ?? "";
    await page.goto(`/login#email=${encodeURIComponent(email)}`);
    await expect(page.locator("#email")).toHaveValue(email);
    await expect(page.locator("#tenant")).toHaveCount(0); // no workspace box
    expect(new URL(page.url()).hash).toBe(""); // the email does not stay in the address
    await page.locator("#password").fill("definitely-not-the-password");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.locator(".loginError")).toContainText("email or password is not right");
    await page.locator("#password").fill(process.env.E2E_PASSWORD ?? "");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(/\/modules\/dashboard\/?$/);
    await expectSignedInShell(page);
  });

  test("Sign up from the website creates a workspace and opens it", async ({ page }) => {
    const company = `Signup Test ${tag}`;
    const email = `founder-${tag}@example.com`;
    await page.goto(`/signup#plan=business&company=${encodeURIComponent(company)}&email=${encodeURIComponent(email)}`);
    const form = page.getByTestId("signup-form");
    await expect(page.locator(".loginCard")).toContainText("pay only for the storage and activity you use");
    await expect(form.locator("#organization")).toHaveValue(company);
    await expect(form.locator("#email")).toHaveValue(email);
    await form.locator("#name").fill("Pat Founder");
    await form.locator("#password").fill(`Founder-${tag}-pass!`);
    await form.locator("#confirm").fill(`Founder-${tag}-other`);
    await form.getByRole("button", { name: "Create account" }).click();
    await expect(page.locator(".loginError")).toContainText("different");
    await form.locator("#confirm").fill(`Founder-${tag}-pass!`);
    await form.getByRole("button", { name: "Create account" }).click();
    await expect(page).toHaveURL(/\/modules\/dashboard\/?$/);
    await expectSignedInShell(page);
    // The founder administers the new workspace.
    await page.goto("/modules/settings");
    await expect(page.getByTestId("users-table")).toContainText(email);
    await page.getByRole("button", { name: "Log out" }).click();

    // Signing up again with the same email is refused with a clear message.
    await page.goto(`/signup#email=${encodeURIComponent(email)}&company=Again`);
    const again = page.getByTestId("signup-form");
    await again.locator("#name").fill("Pat");
    await again.locator("#password").fill(`Founder-${tag}-pass!`);
    await again.locator("#confirm").fill(`Founder-${tag}-pass!`);
    await again.getByRole("button", { name: "Create account" }).click();
    await expect(page.locator(".loginError")).toContainText("already exists");

    // And the new account signs in with just email and password.
    await page.getByRole("link", { name: "Sign in" }).click();
    await page.locator("#email").fill(email);
    await page.locator("#password").fill(`Founder-${tag}-pass!`);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(/\/modules\/dashboard\/?$/);
  });
});
