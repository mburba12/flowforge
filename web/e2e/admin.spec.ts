import { expect, test } from "@playwright/test";

import { signIn } from "./auth";
import { submitOk } from "./ledger";

const tag = Date.now().toString(36);
const viewerEmail = `viewer-${tag}@example.com`;
const viewerPassword = `Viewer-${tag}-pass!`;

test.describe.serial("Administration and permissions in the browser", () => {
  test("owner invites a Viewer", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/settings");
    const uf = page.getByTestId("user-form");
    await uf.locator("#user-form-display_name").fill(`Viewer ${tag}`);
    await uf.locator("#user-form-email").fill(viewerEmail);
    await uf.locator("#user-form-password").fill(viewerPassword);
    await uf.locator("#user-form-role").selectOption("Viewer");
    await submitOk(uf, "Create user", "created with role Viewer");
    await expect(page.getByTestId("users-table")).toContainText(viewerEmail);
    await page.getByRole("tab", { name: "Roles & permissions" }).click();
    await expect(page.getByTestId("roles-table")).toContainText("Approver");
  });

  test("a Viewer can read but every write action is disabled", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#tenant").fill(process.env.E2E_TENANT ?? "");
    await page.locator("#email").fill(viewerEmail);
    await page.locator("#password").fill(viewerPassword);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(/\/modules\/dashboard\/?$/);
    await page.goto("/modules/ap");
    const form = page.getByTestId("po-form");
    await expect(form).toContainText("Requires permission ap.po.write");
    await expect(form.getByRole("button", { name: "Create purchase order" })).toBeDisabled();
    await page.goto("/modules/settings");
    await expect(page.locator(".rwNotice.error").first()).toContainText(/permission/i);
  });

  test("owner deactivates the Viewer, whose session then ends", async ({ browser, page }) => {
    const viewer = await browser.newPage();
    await viewer.goto("/login");
    await viewer.locator("#tenant").fill(process.env.E2E_TENANT ?? "");
    await viewer.locator("#email").fill(viewerEmail);
    await viewer.locator("#password").fill(viewerPassword);
    await viewer.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(viewer).toHaveURL(/\/modules\/dashboard\/?$/);

    await signIn(page);
    await page.goto("/modules/settings");
    await page.getByTestId("users-table").getByText(viewerEmail).click();
    await page.getByTestId("user-deactivate").click();
    await expect(page.getByRole("status").filter({ hasText: "Deactivate:" })).toContainText("done");

    await viewer.goto("/modules/finance");
    await expect(viewer).toHaveURL(/\/login\/?$/);
    await viewer.close();
  });
});
