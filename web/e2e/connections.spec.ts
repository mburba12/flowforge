import { expect, test } from "@playwright/test";

import { signIn } from "./auth";

// The connections release in the browser: Upload in every section, the Files hub, bank
// accounts (demo bank + statement import), shipment tracking (demo carrier) and moving
// payroll from another provider with an export file.

const PDF = Buffer.from("%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF");

test.describe.serial("Connections and uploads in the browser", () => {
  test("home shows the setup checklist and quick actions", async ({ page }) => {
    await signIn(page);
    const checklist = page.getByTestId("setup-checklist");
    await expect(checklist).toContainText("Connect your bank");
    await expect(checklist).toContainText("Move your payroll to FlowForge");
    await expect(checklist).toContainText("Connect FedEx, UPS, USPS or DHL");
    await expect(page.getByRole("navigation", { name: "Quick actions" }).getByRole("link", { name: "Track a package" })).toBeVisible();
  });

  test("every section has Upload; files land in that section and in Files", async ({ page }) => {
    await signIn(page);
    for (const [slug, title] of [["ap", "Bills to pay"], ["workforce", "Employees"], ["crm", "CRM & sales"], ["reports", "Reports"]] as const) {
      await page.goto(`/modules/${slug}`);
      await expect(page.locator(".main > header")).toContainText(slug === "crm" ? "Customers & deals" : title);
      await expect(page.getByTestId("section-upload")).toBeVisible();
    }
    await page.goto("/modules/ap");
    await page.getByTestId("section-upload").click();
    const drawer = page.getByTestId("files-drawer");
    await expect(drawer).toContainText("Files in Bills to pay");
    await drawer.getByTestId("upload-input").setInputFiles([
      { name: "acme-invoice-778.pdf", mimeType: "application/pdf", buffer: PDF },
      { name: "receipt.png", mimeType: "image/png", buffer: Buffer.from("\x89PNG\r\n\x1a\n0000", "binary") },
    ]);
    await expect(drawer.locator(".rwNotice.ok")).toContainText("Uploaded 2 files");
    await expect(drawer.getByTestId("file-table")).toContainText("acme-invoice-778.pdf");
    // Active content is refused with a clear reason.
    await drawer.getByTestId("upload-input").setInputFiles({ name: "x.html", mimeType: "text/html", buffer: Buffer.from("<script>") });
    await expect(drawer.locator(".rwNotice.error")).toContainText("not accepted");
    await drawer.getByRole("button", { name: "Close files" }).click();
    await expect(page.getByTestId("section-files-button")).toContainText("2");

    await page.locator(".side").getByRole("link", { name: "Files", exact: true }).click();
    const all = page.getByTestId("file-table");
    await expect(all).toContainText("acme-invoice-778.pdf");
    await expect(all).toContainText("Bills to pay");
    // A non-viewable file downloads with its own name.
    await page.goto("/modules/workforce");
    await page.getByTestId("section-upload").click();
    await page.getByTestId("upload-input").setInputFiles({ name: "w4-forms.csv", mimeType: "text/csv", buffer: Buffer.from("name,status\nRiley,single\n") });
    await expect(page.getByTestId("files-drawer").locator(".rwNotice.ok")).toContainText("Uploaded 1 file");
    const download = page.waitForEvent("download");
    await page.getByTestId("files-drawer").getByRole("button", { name: "Download" }).click();
    expect((await download).suggestedFilename()).toBe("w4-forms.csv");
  });

  test("bank accounts: demo bank, then a statement from any bank", async ({ page }) => {
    await signIn(page);
    await page.locator(".side").getByRole("link", { name: "Bank accounts" }).click();
    await page.getByTestId("demo-bank").click();
    await expect(page.getByTestId("bank-accounts")).toContainText("Business Checking (demo)");
    await expect(page.getByTestId("bank-totals")).toContainText("173,250.17");
    await expect(page.getByTestId("bank-transactions")).toContainText("Customer payment — Acme Corp");

    await page.getByTestId("import-statement").click();
    await page.getByTestId("statement-account").selectOption("new");
    await page.getByTestId("statement-account-name").fill("Operating at Second Bank");
    await page.getByTestId("statement-file").setInputFiles({
      name: "activity.csv",
      mimeType: "text/csv",
      buffer: Buffer.from("Date,Description,Amount,Balance\n2026-11-20,Client payment Initech,1500.00,9500.00\n2026-11-21,Office supplies,-82.15,9417.85\n"),
    });
    await page.getByRole("button", { name: "Import", exact: true }).click();
    await expect(page.locator(".rwNotice.ok")).toContainText("Imported 2 transactions");
    await expect(page.getByTestId("bank-accounts")).toContainText("Operating at Second Bank");
    await page.getByRole("searchbox", { name: "Search transactions" }).fill("Office supplies");
    await expect(page.getByTestId("bank-transactions")).toContainText("82.15");
  });

  test("shipments: track a package and see it on the way", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/shipping");
    await page.getByTestId("tracking-number").fill(`DEMO-${Date.now()}`);
    await page.getByLabel("Reference (optional)").fill("SO-1042");
    await page.getByTestId("track-button").click();
    await expect(page.locator(".rwNotice.ok")).toContainText("Tracking Demo carrier");
    const list = page.getByTestId("shipments");
    await expect(list).toContainText("SO-1042");
    await list.getByRole("button", { name: /SO-1042/ }).click();
    await expect(list.locator(".timeline")).toContainText("Label created");
    await page.getByTestId("connect-carrier").click();
    await expect(page.getByRole("radio", { name: "FedEx" })).toBeVisible();
    await page.getByRole("radio", { name: "UPS" }).click();
    await expect(page.getByLabel("Client secret")).toHaveAttribute("type", "password");
  });

  test("payroll: move employees and year-to-date totals from another provider", async ({ page }) => {
    await signIn(page);
    await page.goto("/modules/payroll");
    await page.getByRole("tab", { name: "Move from another provider" }).click();
    const wizard = page.getByTestId("payroll-switch");
    await wizard.getByRole("radio", { name: "Paychex Flex" }).click();
    const tag = Date.now().toString(36);
    await wizard.getByTestId("payroll-file").setInputFiles({
      name: "paychex-census.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(
        "Employee ID,First Name,Last Name,Hire Date,Pay Type,Pay Rate,Pay Frequency,Work State,YTD Gross Pay\n" +
          `P-${tag}-1,Riley,Nguyen,2022-04-11,Hourly,27.25,Biweekly,OH,41200.00\n` +
          `P-${tag}-2,Sam,Patel,2020-09-01,Salary,91000,Biweekly,Ohio,83420.00\n`,
      ),
    });
    const preview = page.getByTestId("payroll-preview");
    await expect(preview).toContainText("Riley Nguyen");
    await expect(preview).toContainText("91,000.00/yr");
    await page.getByTestId("payroll-import").click();
    await expect(wizard.locator(".rwNotice.ok")).toContainText("2 employees added");
    await expect(wizard).toContainText("Paychex Flex");
  });
});
