"use client";

import { useState } from "react";

import { get, post, today, type Row } from "../client";
import { usePostingContext } from "../context";
import { useLoad, usePartyNames, useRows } from "../hooks";
import { optionsOf, useGl } from "../refs";
import { ActionButton, Amount, Badge, Card, Details, Form, Grid, Notice, Table, Tabs, Workspace, useActionLog } from "../ui";
import { AgingTable } from "./payables";

const TABS = [
  { id: "orders", label: "Orders" },
  { id: "open", label: "Open items & receipts" },
  { id: "aging", label: "Aging" },
  { id: "customers", label: "Customers" },
];

type OrderDetail = {
  id: string;
  order_number: string;
  status: string;
  total: string;
  order_date: string;
  lines: Row[];
  status_history: { status: string; at: string; note: string | null }[];
  shipments: Row[];
  invoices: Row[];
};

export function ReceivablesWorkspace({ initialTab = "orders" }: { initialTab?: string }) {
  const [tab, setTab] = useState(initialTab);
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const gl = useGl(String(version));
  const ctx = usePostingContext(gl, [
    { key: "ar_account_id", label: "AR control account", type: "asset" },
    { key: "cash_account_id", label: "Cash account", type: "asset" },
  ]);
  const names = usePartyNames(String(version));
  const customers = useRows("customers", String(version));
  const customerName = (id: unknown) => {
    const c = (customers.data ?? []).find((x) => x.id === id);
    return c ? `${names.get(String(c.party_id)) ?? c.customer_number} (${String(c.customer_number)})` : String(id ?? "");
  };
  const shared = { gl, ctx, customers, customerName, names, version, refresh };
  return (
    <Workspace title={initialTab === "orders" ? "Orders" : "Invoices & payments"} description={initialTab === "orders" ? "Sales orders from entry to shipping and invoicing, with their status." : "Customers, invoices, payments received and who owes you by age."} accent="#0891b2">
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "orders" || tab === "open" ? ctx.node : null}
      {tab === "orders" ? <Orders {...shared} /> : null}
      {tab === "open" ? <OpenItems {...shared} /> : null}
      {tab === "aging" ? <AgingTable path="/api/v3b/aging" partyLabel={customerName} partyKey="customer_id" version={version} testId="ar-aging" /> : null}
      {tab === "customers" ? <Customers {...shared} /> : null}
    </Workspace>
  );
}

type Shared = {
  gl: ReturnType<typeof useGl>;
  ctx: ReturnType<typeof usePostingContext>;
  customers: ReturnType<typeof useRows>;
  customerName: (id: unknown) => string;
  names: Map<string, string>;
  version: number;
  refresh: () => void;
};

function Customers({ gl, customers, names, refresh }: Shared) {
  return (
    <Grid>
      <Card title="Customers">
        <Table
          testId="customers-table"
          rows={customers.data}
          loading={customers.loading}
          error={customers.error}
          columns={[
            { key: "customer_number", label: "Number" },
            { key: "party_id", label: "Name", render: (r) => names.get(String(r.party_id)) ?? "" },
            { key: "credit_limit", label: "Credit limit", align: "right", render: (r) => <Amount value={r.credit_limit} /> },
            { key: "credit_status", label: "Credit", render: (r) => <Badge value={r.credit_status} /> },
          ]}
        />
      </Card>
      <Form
        title="New customer"
        testId="customer-form"
        permission="ar.customer.write"
        submitLabel="Create customer"
        fields={[
          { name: "legal_name", label: "Legal name", required: true },
          { name: "credit_limit", label: "Credit limit", type: "number", initial: "10000", required: true },
          { name: "default_currency", label: "Currency", initial: "USD", required: true },
          { name: "ar_account_id", label: "AR account", type: "select", options: gl.accountOptions("asset"), required: true },
          { name: "revenue_account_id", label: "Revenue account", type: "select", options: gl.accountOptions("revenue"), required: true },
        ]}
        onSaved={refresh}
        onSubmit={async (v) => {
          const party = await post<{ id: string }>("/api/v2/organizations", { legal_name: v.legal_name });
          const customer = await post<{ customer_number: string }>("/api/v3b/customers", {
            party_id: party.id,
            default_currency: v.default_currency,
            ar_account_id: v.ar_account_id,
            revenue_account_id: v.revenue_account_id,
            credit_limit: v.credit_limit,
          });
          return `Customer ${customer.customer_number} created.`;
        }}
      />
    </Grid>
  );
}

function Orders({ ctx, customers, customerName, version, refresh }: Shared) {
  const orders = useLoad(() => get<Row[]>("/api/v3b/orders"), `orders:${version}`);
  const products = useRows("products", String(version));
  const [selectedId, setSelectedId] = useState<string>("");
  const detail = useLoad(async () => (selectedId ? get<OrderDetail>(`/api/v3b/orders/${selectedId}`) : null), `order:${selectedId}:${version}`);
  const [log, onDone] = useActionLog();
  const [due, setDue] = useState("");
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  const productName = (id: unknown) => {
    const p = (products.data ?? []).find((x) => x.id === id);
    return p ? `${p.sku} ${p.name}` : String(id ?? "");
  };
  const d = detail.data;
  return (
    <Grid>
      <Card title="Sales orders">
        <Table
          testId="orders-table"
          rows={orders.data}
          loading={orders.loading}
          error={orders.error}
          selectedId={selectedId}
          onSelect={(r) => setSelectedId(String(r.id))}
          columns={[
            { key: "order_number", label: "Order" },
            { key: "customer_id", label: "Customer", render: (r) => customerName(r.customer_id) },
            { key: "order_date", label: "Date" },
            { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
            { key: "total", label: "Total", align: "right", render: (r) => <Amount value={r.total} /> },
          ]}
        />
        {d ? (
          <div className="rwSelected" data-testid="order-detail">
            <h3>
              {d.order_number} <Badge value={d.status} />
            </h3>
            <Details
              items={[
                ["Total", <Amount key="t" value={d.total} />],
                ["Status history", d.status_history.map((e) => `${e.status} (${e.at.slice(0, 16).replace("T", " ")})`).join(" → ")],
                ["Shipments", d.shipments.map((s) => String(s.shipment_number)).join(", ") || "none"],
                ["Invoices", d.invoices.map((i) => `${String(i.invoice_number)} ${String(i.total)}`).join(", ") || "none"],
              ]}
            />
            <Table
              rows={d.lines}
              columns={[
                { key: "product_id", label: "Product", render: (r) => productName(r.product_id) },
                { key: "quantity", label: "Qty", align: "right" },
                { key: "reserved", label: "Reserved", align: "right" },
                { key: "shipped", label: "Shipped", align: "right" },
              ]}
            />
            {d.status === "credit_hold" ? <Notice kind="info">This order exceeds the customer&apos;s credit limit and is on hold.</Notice> : null}
            <div className="rwActions">
              <ActionButton label="Reserve stock" permission="ar.order.fulfill" testId="order-reserve" onDone={done} run={() => post(`/api/v3b/orders/${d.id}/reserve`)} />
              <label className="rwInline">
                <span>Payment due</span>
                <input type="date" aria-label="Payment due" value={due} onChange={(e) => setDue(e.target.value)} />
              </label>
              <ActionButton
                label="Ship and invoice"
                permission="ar.order.fulfill"
                testId="order-ship"
                primary
                disabled={!due}
                onDone={done}
                run={() => post(`/api/v3b/orders/${d.id}/ship-invoice`, undefined, { ship_date: today(), due_date: due })}
              />
            </div>
            {log}
          </div>
        ) : (
          <p className="rwMuted">Select an order to see its status history, reserve stock, or ship and invoice it.</p>
        )}
      </Card>
      <Form
        title="New sales order"
        testId="order-form"
        permission="ar.order.write"
        submitLabel="Create order"
        fields={[
          { name: "customer_id", label: "Customer", type: "select", options: optionsOf(customers.data, (r) => customerName(r.id)), required: true },
          { name: "order_date", label: "Order date", type: "date", initial: today(), required: true },
        ]}
        lines={{
          name: "lines",
          label: "Lines",
          columns: [
            { name: "product_id", label: "Product", type: "select", options: optionsOf(products.data, (r) => `${r.sku} ${r.name}`), required: true },
            { name: "quantity", label: "Qty", type: "number", required: true },
            { name: "unit_price", label: "Unit price", type: "number", required: true },
          ],
        }}
        onSaved={refresh}
        onSubmit={async (v, rows) => {
          if (!ctx.values.ledger_id || !ctx.values.period_id) throw new Error("Choose the ledger and open period above first.");
          const order = await post<{ status: string; total: string }>("/api/v3b/orders", {
            customer_id: v.customer_id,
            order_date: v.order_date,
            ledger_id: ctx.values.ledger_id,
            period_id: ctx.values.period_id,
            lines: rows,
          });
          return order.status === "credit_hold" ? `Order created on credit hold (total ${order.total}).` : `Order created and approved (total ${order.total}).`;
        }}
      />
    </Grid>
  );
}

function OpenItems({ ctx, customerName, version, refresh }: Shared) {
  const items = useLoad(() => get<Row[]>("/api/v3b/open-items"), `aropen:${version}`);
  const [selected, setSelected] = useState<Row | null>(null);
  return (
    <Grid>
      <Card title="Open receivables">
        <Table
          testId="ar-open-table"
          rows={items.data}
          loading={items.loading}
          error={items.error}
          selectedId={selected ? String(selected.id) : undefined}
          onSelect={setSelected}
          empty="Nothing outstanding. Invoiced orders appear here."
          columns={[
            { key: "customer_id", label: "Customer", render: (r) => customerName(r.customer_id) },
            { key: "due_date", label: "Due" },
            { key: "original_amount", label: "Original", align: "right", render: (r) => <Amount value={r.original_amount} /> },
            { key: "open_amount", label: "Open", align: "right", render: (r) => <Amount value={r.open_amount} /> },
            { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
          ]}
        />
      </Card>
      <Form
        title={selected ? `Receive from ${customerName(selected.customer_id)}` : "Record a receipt"}
        testId="ar-receipt-form"
        permission="ar.receipt.write"
        submitLabel="Record receipt"
        fields={[
          { name: "amount", label: "Amount", type: "number", required: true },
          { name: "receipt_date", label: "Receipt date", type: "date", initial: today(), required: true },
        ]}
        onSaved={() => {
          refresh();
          items.reload();
        }}
        onSubmit={async (v) => {
          if (!selected) throw new Error("Select an open item first.");
          if (!ctx.ready) throw new Error(`Choose the posting context first (${ctx.missing.join(", ")}).`);
          await post("/api/v3b/receipts", {
            open_item_id: selected.id,
            amount: v.amount,
            receipt_date: v.receipt_date,
            cash_account_id: ctx.values.cash_account_id,
            ar_account_id: ctx.values.ar_account_id,
            ledger_id: ctx.values.ledger_id,
            period_id: ctx.values.period_id,
            currency_code: "USD",
          });
          return `Receipt of ${v.amount} recorded and posted.`;
        }}
      />
    </Grid>
  );
}
