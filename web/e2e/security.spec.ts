import { createHmac } from "node:crypto";

import { expect, test, type Page } from "@playwright/test";

import { signIn } from "./auth";

// Account security in the browser: setting up two-step sign-in, signing in with the code,
// recovery codes, forgot / reset password pages, and sign-out ending the session.

const api = (process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8001").replace(/\/$/, "");
const tag = Date.now().toString(36);
const email = `mfa-${tag}@example.com`;
const password = `Mfa-${tag}-pass-123`;

function base32(secret: string): Buffer {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  let bits = "";
  for (const ch of secret.replace(/\s|=/g, "").toUpperCase()) bits += alphabet.indexOf(ch).toString(2).padStart(5, "0");
  const bytes: number[] = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) bytes.push(parseInt(bits.slice(i, i + 8), 2));
  return Buffer.from(bytes);
}

function totp(secret: string, offsetSteps = 0): string {
  const step = Math.floor(Date.now() / 1000 / 30) + offsetSteps;
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(step));
  const digest = createHmac("sha1", base32(secret)).update(counter).digest();
  const offset = digest[digest.length - 1] & 0x0f;
  return String((digest.readUInt32BE(offset) & 0x7fffffff) % 1_000_000).padStart(6, "0");
}

async function signInAs(page: Page, who: string, pw: string) {
  await page.goto("/login");
  await page.locator("#email").fill(who);
  await page.locator("#password").fill(pw);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
}

test.describe.serial("Account security in the browser", () => {
  let secret = "";
  let recovery: string[] = [];

  test("a person sets up two-step sign-in from Settings", async ({ page, request }) => {
    // A dedicated person, so the shared test owner keeps signing in without a code.
    const owner = await request.post(`${api}/api/v1/auth/login`, { data: { email: process.env.E2E_EMAIL, password: process.env.E2E_PASSWORD } });
    const token = (await owner.json()).access_token as string;
    const made = await request.post(`${api}/api/v1/users`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { email, display_name: "Two Step", password, roles: ["Manager"] },
    });
    expect(made.status()).toBe(201);

    await signInAs(page, email, password);
    await expect(page).toHaveURL(/\/modules\/dashboard/);
    await page.goto("/modules/settings");
    const card = page.getByTestId("security-card");
    await expect(card).toContainText("Off");
    await card.getByTestId("mfa-open-setup").click();
    await card.getByTestId("mfa-start").click();
    secret = ((await card.getByTestId("mfa-secret").textContent()) ?? "").replace(/\s/g, "");
    expect(secret.length).toBeGreaterThan(20);
    await card.getByTestId("mfa-code").fill("000000");
    await card.getByTestId("mfa-confirm").click();
    await expect(card.locator(".rwNotice.error")).toBeVisible();
    await card.getByTestId("mfa-code").fill(totp(secret));
    await card.getByTestId("mfa-confirm").click();
    const codes = card.getByTestId("mfa-recovery");
    await expect(codes).toContainText("Save these recovery codes");
    recovery = (await codes.locator("code").allTextContents()).map((c) => c.trim());
    expect(recovery).toHaveLength(10);
    await codes.getByTestId("mfa-done").click();
    await expect(card.getByTestId("mfa-status")).toContainText("On. 10 recovery codes left");
    // This session continues (its token was renewed as a two-step sign-in).
    await page.goto("/modules/dashboard");
    await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
    await page.getByRole("button", { name: "Log out" }).click();
  });

  test("signing in asks for the code; a recovery code works once", async ({ page }) => {
    await signInAs(page, email, password);
    const form = page.getByTestId("mfa-form");
    await expect(form).toBeVisible();
    await form.locator("#code").fill("123456");
    await form.getByRole("button", { name: "Continue" }).click();
    await expect(page.locator(".loginError")).toContainText("not right");
    await form.locator("#code").fill(totp(secret, 1));
    await form.getByRole("button", { name: "Continue" }).click();
    await expect(page).toHaveURL(/\/modules\/dashboard/);
    await page.getByRole("button", { name: "Log out" }).click();

    await signInAs(page, email, password);
    await page.getByTestId("mfa-form").locator("#code").fill(recovery[0]);
    await page.getByTestId("mfa-form").getByRole("button", { name: "Continue" }).click();
    await expect(page).toHaveURL(/\/modules\/dashboard/);
    await page.goto("/modules/settings");
    await expect(page.getByTestId("mfa-status")).toContainText("9 recovery codes left");
  });

  test("forgot and reset password pages", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("link", { name: "Forgot your password?" }).click();
    await page.locator("#email").fill("someone@example.com");
    await page.getByRole("button", { name: "Send reset link" }).click();
    await expect(page.getByTestId("forgot-sent")).toContainText("If that email has an account");
    await page.goto("/reset-password");
    await expect(page.locator(".loginCard")).toContainText("needs the link from your email");
    await page.goto("/reset-password#token=not-a-real-token-123456789012345");
    await expect.poll(() => new URL(page.url()).hash).toBe(""); // the token leaves the address bar
    await page.locator("#password").fill("Brand-new-pass-123");
    await page.locator("#confirm").fill("Brand-new-pass-123");
    await page.getByRole("button", { name: "Change password" }).click();
    await expect(page.locator(".loginError")).toContainText("no longer valid");
  });

  test("log out ends the session on the server", async ({ page }) => {
    await signIn(page);
    const token = await page.evaluate(() => sessionStorage.getItem("flowforge.accessToken"));
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login/);
    const after = await page.request.get(`${api}/api/v1/me`, { headers: { Authorization: `Bearer ${token}` } });
    expect(after.status()).toBe(401);
  });

  test("pages are sent with security headers", async ({ page }) => {
    const response = await page.goto("/login");
    const headers = response?.headers() ?? {};
    expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
    expect(headers["x-frame-options"]).toBe("DENY");
  });
});
