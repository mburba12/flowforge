import { expect, type Locator, type Page } from "@playwright/test";

/**
 * Per-spec ledger, chart of accounts and open period, created through the API with
 * the owner's credentials so domain specs can focus on their own workflows.
 * Every name carries the spec's code, so parallel specs never pick each other's accounts.
 */
export type Ledger = {
  code: string;
  ledgerLabel: string;
  periodLabel: string;
  account: (key: AccountKey) => string;
};

const ACCOUNTS = {
  cash: ["1000", "Cash", "asset", "debit"],
  ar: ["1100", "Receivables", "asset", "debit"],
  inventory: ["1200", "Inventory", "asset", "debit"],
  ap: ["2000", "Payables", "liability", "credit"],
  eeTax: ["2100", "Employee tax payable", "liability", "credit"],
  erTax: ["2110", "Employer tax payable", "liability", "credit"],
  deductions: ["2120", "Deductions payable", "liability", "credit"],
  netPay: ["2130", "Net pay payable", "liability", "credit"],
  equity: ["3000", "Owner equity", "equity", "credit"],
  revenue: ["4000", "Sales", "revenue", "credit"],
  cogs: ["5000", "Cost of goods sold", "expense", "debit"],
  expense: ["6000", "Supplies expense", "expense", "debit"],
  wages: ["6100", "Wages", "expense", "debit"],
  erTaxExpense: ["6110", "Employer tax expense", "expense", "debit"],
} as const;
export type AccountKey = keyof typeof ACCOUNTS;

async function call(method: string, path: string, token: string, body?: unknown): Promise<Record<string, unknown>> {
  const api = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8001";
  const response = await fetch(`${api}${path}`, {
    method,
    headers: { "content-type": "application/json", authorization: `Bearer ${token}` },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`${method} ${path} -> ${response.status} ${await response.text()}`);
  return (await response.json()) as Record<string, unknown>;
}

export async function ownerToken(): Promise<string> {
  const api = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8001";
  const response = await fetch(`${api}/api/v1/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: process.env.E2E_EMAIL, password: process.env.E2E_PASSWORD, tenant_slug: process.env.E2E_TENANT }),
  });
  if (!response.ok) throw new Error(`owner login failed: ${response.status}`);
  return ((await response.json()) as { access_token: string }).access_token;
}

export async function createLedger(prefix: string): Promise<Ledger> {
  const token = await ownerToken();
  const code = `${prefix}${Date.now().toString(36).slice(-4).toUpperCase()}`;
  const now = new Date();
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString().slice(0, 10);
  const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 0)).toISOString().slice(0, 10);
  await call("POST", "/api/v2/currencies", token, { code: "USD", name: "US Dollar" }).catch(() => undefined);
  const calendar = await call("POST", "/api/v2/fiscal-calendars", token, { name: `FY ${code}`, start_month: 1 });
  const ledger = await call("POST", "/api/v2/ledgers", token, { code, name: `${code} Ledger`, base_currency: "USD" });
  for (const [num, name, type, normal] of Object.values(ACCOUNTS)) {
    await call("POST", "/api/v2/accounts", token, {
      ledger_id: ledger.id,
      account_code: num,
      name: `${name} ${code}`,
      account_type: type,
      normal_balance: normal,
      posting_allowed: true,
    });
  }
  await call("POST", "/api/v2/accounting-periods", token, { calendar_id: calendar.id, period_code: `${code}-P`, start_date: start, end_date: end });
  return {
    code,
    ledgerLabel: `${code} — ${code} Ledger`,
    periodLabel: `${code}-P (${start} to ${end})`,
    account: (key) => `${code} · ${ACCOUNTS[key][0]} ${ACCOUNTS[key][1]} ${code}`,
  };
}

/** Fill the posting context bar (ledger, period, then named accounts by label). */
export async function setContext(page: Page, ledger: Ledger, accounts: Record<string, AccountKey>): Promise<void> {
  const bar = page.getByRole("region", { name: "Posting context" });
  await bar.getByLabel("Ledger", { exact: true }).selectOption({ label: ledger.ledgerLabel });
  await bar.getByLabel("Period", { exact: true }).selectOption({ label: ledger.periodLabel });
  for (const [label, key] of Object.entries(accounts)) {
    await bar.getByLabel(label, { exact: true }).selectOption({ label: ledger.account(key).split(" · ")[1] }); // the bar lists only this ledger
  }
}

/** Submit a form and assert its success message. */
export async function submitOk(form: Locator, button: string, expected: string | RegExp): Promise<void> {
  await form.getByRole("button", { name: button }).click();
  await expect(form.getByRole("status")).toContainText(expected);
}

/** Click an action button and assert the action log reports success. */
export async function act(page: Page, testId: string, label: string): Promise<void> {
  await page.getByTestId(testId).click();
  await expect(page.getByRole("status").filter({ hasText: `${label}:` })).toContainText("done");
}

/** Select the option whose label contains `text` (names appear inside longer labels). */
export async function selectContaining(select: Locator, text: string): Promise<void> {
  const value = await select.locator("option", { hasText: text }).first().getAttribute("value");
  if (!value) throw new Error(`No option containing "${text}"`);
  await select.selectOption(value);
}
