"use client";

import { useState } from "react";

import type { useGl } from "./refs";
import type { Option } from "./ui";

export type AccountRole = { key: string; label: string; type?: string };

/**
 * Posting context bar: ledger, open period and named accounts used by subledger
 * actions (post invoice, pay, receipts, payroll posting). Values persist per tab.
 */
export function usePostingContext(gl: ReturnType<typeof useGl>, roles: AccountRole[]) {
  const [values, setValues] = useState<Record<string, string>>({});
  const ledgerAccounts = (type?: string): Option[] =>
    (gl.accounts.data ?? [])
      .filter((a) => (!values.ledger_id || a.ledger_id === values.ledger_id) && (!type || a.account_type === type))
      .map((a) => ({ value: String(a.id), label: `${a.account_code} ${a.name}` }));
  const set = (key: string, value: string) => setValues((v) => ({ ...v, [key]: value }));
  const select = (key: string, label: string, options: Option[]) => (
    <label key={key}>
      <span>{label}</span>
      <select aria-label={label} value={values[key] ?? ""} onChange={(e) => set(key, e.target.value)}>
        <option value="">Select…</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
  const node = (
    <section className="rwContext" aria-label="Posting context">
      <strong>Posting to</strong>
      {select("ledger_id", "Ledger", gl.ledgerOptions)}
      {select("period_id", "Period", gl.openPeriodOptions)}
      {roles.map((r) => select(r.key, r.label, ledgerAccounts(r.type)))}
    </section>
  );
  const missing = ["ledger_id", "period_id", ...roles.map((r) => r.key)].filter((k) => !values[k]);
  return { node, values, ready: missing.length === 0, missing };
}
