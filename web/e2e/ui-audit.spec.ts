import { expect, type Page, test } from "@playwright/test";

import { signIn, signOut } from "./auth";
import { ownerToken } from "./ledger";

// UI audit: every sidebar workspace for owner, approver and a viewer, and every
// operation form opened in the browser. Any page crash, console error or error
// notice fails the audit with the list of places it happened.

type Finding = { role: string; where: string; what: string };

const API = () => process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8001";

async function workspaceSlugs(page: Page): Promise<string[]> {
  const hrefs = await page.locator(".shell aside nav a").evaluateAll((links) => links.map((a) => a.getAttribute("href") ?? ""));
  return hrefs.map((h) => h.replace(/^\/modules\//, "")).filter(Boolean);
}

function watch(page: Page, findings: Finding[], role: string, where: () => string): void {
  page.on("pageerror", (e) => findings.push({ role, where: where(), what: `page error: ${e.message}` }));
  page.on("console", (m) => {
    if (m.type() === "error" && !/favicon|Failed to load resource: the server responded with a status of 40[34]/.test(m.text())) {
      findings.push({ role, where: where(), what: `console: ${m.text().slice(0, 200)}` });
    }
  });
}

async function auditWorkspaces(page: Page, role: string, findings: Finding[], openForms: boolean): Promise<number> {
  let current = "";
  watch(page, findings, role, () => current);
  const slugs = await workspaceSlugs(page);
  let forms = 0;
  for (const slug of slugs) {
    current = `/modules/${slug}`;
    await page.goto(current);
    await page.locator(".shell .main h1").first().waitFor();
    await page.waitForLoadState("networkidle");
    if (await page.getByText("Application error").count()) findings.push({ role, where: current, what: "application error" });
    for (const text of await page.locator(".rwNotice.error").allInnerTexts()) {
      findings.push({ role, where: current, what: `error notice: ${text.slice(0, 160)}` });
    }
    if (!openForms) continue;
    const all = page.getByTestId("all-operations");
    if (await all.count()) await all.locator("summary").click();
    const buttons = page.locator('[data-testid^="op-"][title]');
    const count = await buttons.count();
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const label = `${current} ${await button.getAttribute("title")}`;
      await button.click();
      const form = page.getByTestId("op-form");
      if (!(await form.isVisible())) findings.push({ role, where: label, what: "form did not open" });
      forms++;
    }
  }
  return forms;
}

async function createViewer(): Promise<{ email: string; password: string }> {
  const token = await ownerToken();
  const email = `viewer-${Date.now()}@example.com`;
  const password = `View-${Math.random().toString(36).slice(2)}-${Date.now()}`;
  const response = await fetch(`${API()}/api/v1/users`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${token}` },
    body: JSON.stringify({ email, display_name: "Audit Viewer", password, roles: ["Viewer"] }),
  });
  if (!response.ok) throw new Error(`viewer creation failed: ${response.status}`);
  return { email, password };
}

test.describe("UI audit", () => {
  test.setTimeout(600_000);

  test("owner: every workspace loads and every operation form opens", async ({ page }) => {
    const findings: Finding[] = [];
    await signIn(page);
    const forms = await auditWorkspaces(page, "owner", findings, true);
    console.log(`owner: opened ${forms} operation forms`);
    expect(forms).toBeGreaterThan(300);
    expect(findings, JSON.stringify(findings, null, 2)).toEqual([]);
  });

  test("approver: every workspace loads without errors", async ({ page }) => {
    const findings: Finding[] = [];
    await signIn(page, "approver");
    await auditWorkspaces(page, "approver", findings, false);
    expect(findings, JSON.stringify(findings, null, 2)).toEqual([]);
  });

  test("viewer: every workspace loads; write operations are locked", async ({ page }) => {
    const findings: Finding[] = [];
    const viewer = await createViewer();
    await page.goto("/login");
    await page.locator("#tenant").fill(process.env.E2E_TENANT ?? "");
    await page.locator("#email").fill(viewer.email);
    await page.locator("#password").fill(viewer.password);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(/\/modules\/dashboard\/?$/);
    await auditWorkspaces(page, "viewer", findings, false);
    await page.goto("/modules/crm");
    await page.getByRole("searchbox", { name: "Filter operations" }).fill("leads");
    await page.locator('[data-testid^="op-"][title="/api/v2/crm/leads"]').filter({ hasText: "POST" }).click();
    await expect(page.getByTestId("op-run")).toBeDisabled();
    expect(findings, JSON.stringify(findings, null, 2)).toEqual([]);
    await signOut(page);
  });
});
