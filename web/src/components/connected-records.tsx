"use client";

import { useEffect, useMemo, useState } from "react";

type TableInfo = { name: string; columns: string[] };
type Page = { table: string; total: number; items: Record<string, unknown>[] };

const groups: Record<string, string[]> = {
  "Accounts payable": ["vendors", "purchase_orders", "vendor_invoices", "vendor_payments"],
  "Accounts receivable": ["customers", "sales_orders", "customer_invoices", "customer_receipts"],
  Orders: ["sales_orders", "sales_order_lines", "shipments"],
  "Inventory and purchasing": ["products", "warehouses", "warehouse_locations", "inventory_balances", "purchase_orders"],
  Banking: ["connected_bank_accounts", "bank_transactions", "processor_payments", "processor_payouts"],
  "Finance and ledger": ["ledgers", "accounts", "journals", "journal_lines"],
  Payroll: ["payroll_runs", "payroll_lines", "workforce_payroll_runs"],
  Workforce: ["workers", "worker_profiles", "time_entries", "work_schedules"],
  Tax: ["tax_liabilities", "tax_returns", "tax_remittances", "tax_notices"],
  Reconciliation: ["reconciliation_runs", "reconciliation_items", "reconciliation_exceptions"],
  Integrations: ["integrations", "provider_registrations", "webhook_endpoints", "webhook_deliveries"],
  Entities: ["entities", "parties", "organizations"],
  Documents: ["documents"],
  "Audit and platform": ["audit_events", "work_queue_items", "workflow_tasks"],
  Dashboard: ["work_queue_items", "audit_events"],
  Approvals: ["approval_requests", "workflow_tasks"],
  "Work queue": ["work_queue_items", "workflow_tasks"],
};

export function ConnectedRecords({ title }: { title: string }) {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selected, setSelected] = useState("");
  const [pages, setPages] = useState<Record<string, Page>>({});
  const [error, setError] = useState("");

  const choices = useMemo(() => {
    const wanted = groups[title] ?? [];
    const exact = tables.filter((table) => wanted.includes(table.name));
    return exact.length
      ? exact
      : tables.filter((table) =>
          wanted.some((name) => table.name.includes(name.replace(/s$/, ""))),
        );
  }, [tables, title]);
  const active = selected || choices[0]?.name || "";
  const page = pages[active] ?? null;

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/flowforge/api/v1/catalog/tables", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Catalog ${response.status}`);
        return response.json() as Promise<TableInfo[]>;
      })
      .then(setTables)
      .catch((cause: unknown) => {
        if (!(cause instanceof DOMException && cause.name === "AbortError")) setError(String(cause));
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!active || pages[active]) return;
    const controller = new AbortController();
    fetch(`/api/flowforge/api/v1/catalog/tables/${active}/records`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Records ${response.status}`);
        return response.json() as Promise<Page>;
      })
      .then((value) => setPages((current) => ({ ...current, [active]: value })))
      .catch((cause: unknown) => {
        if (!(cause instanceof DOMException && cause.name === "AbortError")) setError(String(cause));
      });
    return () => controller.abort();
  }, [active, pages]);

  const columns = Object.keys(page?.items[0] ?? {});
  return (
    <section className="panel">
      <div className="panelbody">
        <h2>Connected records</h2>
        {error && <p role="alert">{error}</p>}
        <label>
          Resource
          <select className="field" value={active} onChange={(event) => setSelected(event.target.value)}>
            {choices.map((table) => <option key={table.name}>{table.name}</option>)}
          </select>
        </label>
        {page && (
          <>
            <p>{page.total} persisted records</p>
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
                <tbody>{page.items.map((row, index) => (
                  <tr key={String(row.id ?? index)}>{columns.map((column) => {
                    const value = row[column];
                    return <td key={column}>{typeof value === "object" ? JSON.stringify(value) : String(value ?? "")}</td>;
                  })}</tr>
                ))}</tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
