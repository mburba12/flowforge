"use client";

import { get, type Row } from "./client";
import { useLoad, useRows } from "./hooks";
import type { Option } from "./ui";

export type Period = { id: string; calendar_id: string; period_code: string; start_date: string; end_date: string; status: string };

/** General-ledger reference data shared by every workspace (ledgers, periods, accounts). */
export function useGl(key = "") {
  const ledgers = useRows("ledgers", key);
  const accounts = useRows("accounts", key);
  const calendars = useRows("fiscal-calendars", key);
  const periods = useLoad(() => get<Period[]>("/api/v2/accounting-periods"), `periods:${key}`);

  const ledgerOptions: Option[] = (ledgers.data ?? []).map((l) => ({ value: String(l.id), label: `${l.code} — ${l.name}` }));
  const openPeriodOptions: Option[] = (periods.data ?? [])
    .filter((p) => p.status === "open")
    .map((p) => ({ value: p.id, label: `${p.period_code} (${p.start_date} to ${p.end_date})` }));
  const calendarOptions: Option[] = (calendars.data ?? []).map((c) => ({ value: String(c.id), label: String(c.name) }));
  const accountOptions = (type?: string): Option[] =>
    (accounts.data ?? [])
      .filter((a) => !type || a.account_type === type)
      .sort((a, b) => String(a.account_code).localeCompare(String(b.account_code)))
      .map((a) => ({ value: String(a.id), label: `${a.account_code} ${a.name}` }));
  const accountName = (id: unknown): string => {
    const a = (accounts.data ?? []).find((x) => x.id === id);
    return a ? `${a.account_code} ${a.name}` : String(id ?? "");
  };
  const reload = () => {
    ledgers.reload();
    accounts.reload();
    calendars.reload();
    periods.reload();
  };
  return { ledgers, accounts, calendars, periods, ledgerOptions, openPeriodOptions, calendarOptions, accountOptions, accountName, reload };
}

export function optionsOf(rows: Row[] | null, label: (r: Row) => string): Option[] {
  return (rows ?? []).map((r) => ({ value: String(r.id), label: label(r) }));
}

export function shortId(value: unknown): string {
  return String(value ?? "").slice(0, 8);
}
