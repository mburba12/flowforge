"use client";

import { useState } from "react";

import { get, post, today, type Row } from "../client";
import { usePostingContext } from "../context";
import { useLoad, usePartyNames, useRows } from "../hooks";
import { optionsOf, useGl } from "../refs";
import { ActionButton, Amount, Badge, Card, Form, Grid, Notice, Table, Tabs, Workspace, useActionLog } from "../ui";

const TABS = [
  { id: "orders", label: "Purchase orders" },
  { id: "invoices", label: "Invoices" },
  { id: "open", label: "Open items & payments" },
  { id: "aging", label: "Aging" },
  { id: "vendors", label: "Vendors" },
];

export function PayablesWorkspace() {
  const [tab, setTab] = useState("orders");
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const gl = useGl(String(version));
  const ctx = usePostingContext(gl, [
    { key: "ap_account_id", label: "AP control account", type: "liability" },
    { key: "cash_account_id", label: "Cash account", type: "asset" },
  ]);
  const names = usePartyNames(String(version));
  const vendors = useRows("vendors", String(version));
  const vendorName = (id: unknown) => {
    const v = (vendors.data ?? []).find((x) => x.id === id);
    return v ? `${names.get(String(v.party_id)) ?? v.vendor_number} (${String(v.vendor_number)})` : String(id ?? "");
  };
  const shared = { gl, ctx, vendors, vendorName, version, refresh };
  return (
    <Workspace title="Accounts payable" description="Vendors, purchase orders, receiving, three-way match, posting, payments and aging." accent="#7c3aed">
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "invoices" || tab === "open" ? ctx.node : null}
      {tab === "orders" ? <Orders {...shared} /> : null}
      {tab === "invoices" ? <Invoices {...shared} /> : null}
      {tab === "open" ? <OpenItems {...shared} /> : null}
      {tab === "aging" ? <Aging vendorName={vendorName} version={version} /> : null}
      {tab === "vendors" ? <Vendors {...shared} names={names} /> : null}
    </Workspace>
  );
}

type Shared = {
  gl: ReturnType<typeof useGl>;
  ctx: ReturnType<typeof usePostingContext>;
  vendors: ReturnType<typeof useRows>;
  vendorName: (id: unknown) => string;
  version: number;
  refresh: () => void;
};

function Vendors({ gl, vendors, refresh, names }: Shared & { names: Map<string, string> }) {
  return (
    <Grid>
      <Card title="Vendors">
        <Table
          testId="vendors-table"
          rows={vendors.data}
          loading={vendors.loading}
          error={vendors.error}
          columns={[
            { key: "vendor_number", label: "Number" },
            { key: "party_id", label: "Name", render: (r) => names.get(String(r.party_id)) ?? "" },
            { key: "default_currency", label: "Currency" },
            { key: "ap_account_id", label: "AP account", render: (r) => gl.accountName(r.ap_account_id) },
            { key: "active", label: "Active", render: (r) => <Badge value={String(r.active)} /> },
          ]}
        />
      </Card>
      <Form
        title="New vendor"
        testId="vendor-form"
        permission="ap.vendor.write"
        submitLabel="Create vendor"
        fields={[
          { name: "legal_name", label: "Legal name", required: true },
          { name: "default_currency", label: "Currency", initial: "USD", required: true },
          { name: "ap_account_id", label: "AP account", type: "select", options: gl.accountOptions("liability"), required: true },
        ]}
        onSaved={refresh}
        onSubmit={async (v) => {
          const party = await post<{ id: string }>("/api/v2/organizations", { legal_name: v.legal_name });
          const vendor = await post<{ vendor_number: string }>("/api/v3/vendors", {
            party_id: party.id,
            default_currency: v.default_currency,
            ap_account_id: v.ap_account_id,
          });
          return `Vendor ${vendor.vendor_number} created.`;
        }}
      />
    </Grid>
  );
}

function Orders({ gl, vendors, vendorName, version, refresh }: Shared) {
  const orders = useRows("purchase-orders", String(version));
  const [selected, setSelected] = useState<Row | null>(null);
  const lines = useLoad(
    async () => (selected ? (await get<{ items: Row[] }>("/api/v1/business/purchase-order-lines", { field: "purchase_order_id", value: String(selected.id), limit: 200 })).items : []),
    `pol:${String(selected?.id)}:${version}`,
  );
  const [log, onDone] = useActionLog();
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  const current = selected ? (orders.data ?? []).find((o) => o.id === selected.id) ?? selected : null;
  const remaining = (lines.data ?? [])
    .map((l) => ({ po_line_id: String(l.id), quantity: Number(l.quantity) - Number(l.received_quantity) }))
    .filter((l) => l.quantity > 0);
  return (
    <Grid>
      <Card title="Purchase orders">
        <Table
          testId="po-table"
          rows={orders.data}
          loading={orders.loading}
          error={orders.error}
          selectedId={current ? String(current.id) : undefined}
          onSelect={setSelected}
          columns={[
            { key: "po_number", label: "PO" },
            { key: "vendor_id", label: "Vendor", render: (r) => vendorName(r.vendor_id) },
            { key: "order_date", label: "Date" },
            { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
            { key: "total_amount", label: "Total", align: "right", render: (r) => <Amount value={r.total_amount} /> },
          ]}
        />
        {current ? (
          <div className="rwSelected">
            <h3>
              {String(current.po_number)} <Badge value={current.status} />
            </h3>
            <Table
              rows={lines.data}
              loading={lines.loading}
              columns={[
                { key: "description", label: "Item" },
                { key: "quantity", label: "Ordered", align: "right" },
                { key: "received_quantity", label: "Received", align: "right" },
                { key: "unit_price", label: "Price", align: "right", render: (r) => <Amount value={r.unit_price} /> },
              ]}
            />
            <div className="rwActions">
              <ActionButton label="Submit" permission="ap.po.write" testId="po-submit" onDone={done} run={() => post(`/api/v3/purchase-orders/${String(current.id)}/submit`)} />
              <ActionButton label="Approve" permission="ap.po.approve" testId="po-approve" onDone={done} run={() => post(`/api/v3/purchase-orders/${String(current.id)}/approve`)} />
              <ActionButton
                label="Receive remaining"
                permission="ap.receive"
                testId="po-receive"
                disabled={remaining.length === 0}
                onDone={done}
                run={() => post("/api/v3/goods-receipts", { purchase_order_id: current.id, receipt_date: today(), lines: remaining })}
              />
            </div>
            {log}
            <Form
              title="Invoice this PO"
              testId="po-invoice-form"
              permission="ap.invoice.write"
              submitLabel="Record vendor invoice"
              fields={[
                { name: "invoice_number", label: "Vendor invoice number", required: true },
                { name: "invoice_date", label: "Invoice date", type: "date", initial: today(), required: true },
                { name: "due_date", label: "Due date", type: "date", required: true },
              ]}
              onSaved={refresh}
              onSubmit={async (v) => {
                const invoice = await post<{ id: string; total_amount: string }>("/api/v3/vendor-invoices", {
                  vendor_id: current.vendor_id,
                  purchase_order_id: current.id,
                  invoice_number: v.invoice_number,
                  invoice_date: v.invoice_date,
                  due_date: v.due_date,
                  currency_code: current.currency_code,
                  lines: (lines.data ?? []).map((l) => ({
                    po_line_id: l.id,
                    description: l.description,
                    quantity: l.quantity,
                    unit_price: l.unit_price,
                    account_id: l.expense_account_id,
                  })),
                });
                return `Invoice recorded (${invoice.total_amount}). Match and post it on the Invoices tab.`;
              }}
            />
          </div>
        ) : (
          <p className="rwMuted">Select a purchase order to submit, approve, receive or invoice it.</p>
        )}
      </Card>
      <Form
        title="New purchase order"
        testId="po-form"
        permission="ap.po.write"
        submitLabel="Create purchase order"
        fields={[
          { name: "vendor_id", label: "Vendor", type: "select", options: optionsOf(vendors.data, (r) => vendorName(r.id)), required: true },
          { name: "currency_code", label: "Currency", initial: "USD", required: true },
          { name: "order_date", label: "Order date", type: "date", initial: today(), required: true },
        ]}
        lines={{
          name: "lines",
          label: "Lines",
          columns: [
            { name: "description", label: "Item", required: true },
            { name: "quantity", label: "Qty", type: "number", required: true },
            { name: "unit_price", label: "Unit price", type: "number", required: true },
            { name: "expense_account_id", label: "Expense account", type: "select", options: gl.accountOptions("expense"), required: true },
          ],
        }}
        onSaved={refresh}
        onSubmit={async (v, rows) => {
          const po = await post<{ po_number: string }>("/api/v3/purchase-orders", { ...v, lines: rows });
          return `Purchase order ${po.po_number} created as draft. Submit it, then another user approves it.`;
        }}
      />
    </Grid>
  );
}

function Invoices({ ctx, vendorName, version, refresh }: Shared) {
  const invoices = useRows("vendor-invoices", String(version));
  const [selected, setSelected] = useState<Row | null>(null);
  const [log, onDone] = useActionLog();
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  const current = selected ? (invoices.data ?? []).find((o) => o.id === selected.id) ?? selected : null;
  return (
    <Card title="Vendor invoices">
      <Table
        testId="invoice-table"
        rows={invoices.data}
        loading={invoices.loading}
        error={invoices.error}
        selectedId={current ? String(current.id) : undefined}
        onSelect={setSelected}
        columns={[
          { key: "invoice_number", label: "Invoice" },
          { key: "vendor_id", label: "Vendor", render: (r) => vendorName(r.vendor_id) },
          { key: "invoice_date", label: "Date" },
          { key: "due_date", label: "Due" },
          { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
          { key: "total_amount", label: "Total", align: "right", render: (r) => <Amount value={r.total_amount} /> },
        ]}
      />
      {current ? (
        <div className="rwSelected">
          <h3>
            {String(current.invoice_number)} <Badge value={current.status} />
          </h3>
          {!ctx.ready ? <Notice kind="info">Choose the ledger, open period and AP account above to post.</Notice> : null}
          <div className="rwActions">
            <ActionButton
              label="Match to PO and receipt"
              permission="ap.invoice.write"
              testId="invoice-match"
              onDone={done}
              run={async () => {
                const r = await post<{ status: string; details: string }>(`/api/v3/vendor-invoices/${String(current.id)}/match`);
                if (r.status !== "matched") throw new Error(`exception: ${r.details}`);
              }}
            />
            <ActionButton
              label="Post to ledger"
              permission="ap.invoice.post"
              testId="invoice-post"
              primary
              disabled={!ctx.values.ledger_id || !ctx.values.period_id || !ctx.values.ap_account_id}
              onDone={done}
              run={() =>
                post(`/api/v3/vendor-invoices/${String(current.id)}/post`, undefined, {
                  ledger_id: ctx.values.ledger_id,
                  period_id: ctx.values.period_id,
                  ap_account_id: ctx.values.ap_account_id,
                })
              }
            />
          </div>
          {log}
        </div>
      ) : (
        <p className="rwMuted">Select an invoice to match or post it. Invoices are created from a purchase order.</p>
      )}
    </Card>
  );
}

function OpenItems({ ctx, vendorName, version, refresh }: Shared) {
  const items = useLoad(() => get<Row[]>("/api/v3/open-items"), `apopen:${version}`);
  const [selected, setSelected] = useState<Row | null>(null);
  const [log, onDone] = useActionLog();
  const [recon, setRecon] = useState("");
  return (
    <Grid>
      <Card title="Open payables">
        <Table
          testId="ap-open-table"
          rows={items.data}
          loading={items.loading}
          error={items.error}
          selectedId={selected ? String(selected.id) : undefined}
          onSelect={setSelected}
          empty="Nothing owed. Posted invoices appear here."
          columns={[
            { key: "vendor_id", label: "Vendor", render: (r) => vendorName(r.vendor_id) },
            { key: "due_date", label: "Due" },
            { key: "original_amount", label: "Original", align: "right", render: (r) => <Amount value={r.original_amount} /> },
            { key: "open_amount", label: "Open", align: "right", render: (r) => <Amount value={r.open_amount} /> },
            { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
          ]}
        />
        <div className="rwActions">
          <ActionButton
            label="Reconcile AP to ledger"
            permission="ap.reconcile"
            testId="ap-reconcile"
            disabled={!ctx.values.ledger_id || !ctx.values.period_id || !ctx.values.ap_account_id}
            onDone={onDone}
            run={async () => {
              const r = await post<{ status: string; subledger_total: string; gl_total: string }>("/api/v3/ap/reconcile", undefined, {
                ledger_id: ctx.values.ledger_id,
                period_id: ctx.values.period_id,
                ap_account_id: ctx.values.ap_account_id,
              });
              setRecon(`${r.status}: open items ${r.subledger_total} vs ledger ${r.gl_total}`);
            }}
          />
        </div>
        {recon ? <p data-testid="ap-recon-result">{recon}</p> : null}
        {log}
      </Card>
      <Form
        title={selected ? `Pay ${vendorName(selected.vendor_id)}` : "Pay an open item"}
        testId="ap-pay-form"
        permission="ap.pay"
        submitLabel="Record payment"
        fields={[
          { name: "amount", label: "Amount", type: "number", required: true },
          { name: "payment_date", label: "Payment date", type: "date", initial: today(), required: true },
        ]}
        onSaved={() => {
          refresh();
          items.reload();
        }}
        onSubmit={async (v) => {
          if (!selected) throw new Error("Select an open item first.");
          if (!ctx.ready) throw new Error(`Choose the posting context first (${ctx.missing.join(", ")}).`);
          await post(`/api/v3/ap/open-items/${String(selected.id)}/pay`, undefined, {
            amount: v.amount,
            payment_date: v.payment_date,
            ledger_id: ctx.values.ledger_id,
            period_id: ctx.values.period_id,
            ap_account_id: ctx.values.ap_account_id,
            cash_account_id: ctx.values.cash_account_id,
            currency_code: "USD",
          });
          return `Payment of ${v.amount} recorded and posted.`;
        }}
      />
    </Grid>
  );
}

export function AgingTable({ path, partyLabel, partyKey, version, testId }: { path: string; partyLabel: (id: unknown) => string; partyKey: string; version: number; testId: string }) {
  const [asOf, setAsOf] = useState(today());
  const aging = useLoad(() => get<{ buckets: Record<string, string>; total_open: string; by_party: Row[] }>(path, { as_of: asOf }), `${path}:${asOf}:${version}`);
  const buckets = ["current", "1-30", "31-60", "61-90", "90+"];
  return (
    <Card title="Aging" aside={<label className="rwInline"><span>As of</span><input type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} /></label>}>
      {aging.error ? <Notice kind="error">{aging.error}</Notice> : null}
      {aging.data ? (
        <>
          <div className="rwKpis" data-testid={testId}>
            {buckets.map((b) => (
              <article key={b}>
                <span>{b === "current" ? "Not yet due" : `${b} days`}</span>
                <strong>
                  <Amount value={aging.data?.buckets[b]} />
                </strong>
              </article>
            ))}
            <article>
              <span>Total open</span>
              <strong>
                <Amount value={aging.data.total_open} />
              </strong>
            </article>
          </div>
          <Table
            rows={aging.data.by_party}
            columns={[
              { key: partyKey, label: "Party", render: (r) => partyLabel(r[partyKey]) },
              ...buckets.map((b) => ({ key: b, label: b, align: "right" as const, render: (r: Row) => <Amount value={r[b]} /> })),
            ]}
            empty="No open items."
          />
        </>
      ) : null}
    </Card>
  );
}

function Aging({ vendorName, version }: { vendorName: (id: unknown) => string; version: number }) {
  return <AgingTable path="/api/v3/aging" partyLabel={vendorName} partyKey="vendor_id" version={version} testId="ap-aging" />;
}
