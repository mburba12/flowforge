"use client";

import { type FormEvent, useState } from "react";

import { del, errorText, get, post } from "../client";
import { useLoad, usePermissions } from "../hooks";
import { ActionButton, Badge, Card, Grid, Notice, RequiresPermission, Table, Workspace, useActionLog } from "../ui";

type Line = { code: string; description: string; quantity: string; unit: string; unit_price: string; amount: string };
type Quote = { lines: Line[]; total: string; currency: string };
type Invoice = {
  id: string;
  number: string;
  period_start: string;
  period_end: string;
  total: string;
  status: string;
  charge_on: string;
  emailed_to: string | null;
  emailed_at: string | null;
  last_error: string | null;
  lines: Line[];
} & Record<string, unknown>;
type Summary = {
  exempt: boolean;
  rates: { storage_gb_month: string; per_1k_requests: string; payment_processing: string; margin: string };
  card: { brand: string; last4: string; exp_month: number; exp_year: number } | null;
  month: { start: string; end: string; today: string };
  so_far: { storage_gb: string; requests: number };
  estimate: Quote;
  invoices: Invoice[];
  payments_ready: boolean;
  email_ready: boolean;
  charge_after_business_days: number;
};

const usd = (value: string | number) => Number(value).toLocaleString("en-US", { style: "currency", currency: "USD" });
const longDate = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });

function QuoteTable({ quote, testId }: { quote: Quote; testId?: string }) {
  return (
    <Table
      testId={testId}
      rows={[...quote.lines.map((l) => ({ ...l })), { code: "total", description: "Total", quantity: "", unit: "", unit_price: "", amount: quote.total }]}
      columns={[
        { key: "description", label: "What", render: (r) => (r.code === "total" ? <b>Total</b> : String(r.description)) },
        { key: "quantity", label: "Used", render: (r) => (r.code === "total" ? "" : `${Number(r.quantity).toLocaleString("en-US", { maximumFractionDigits: 3 })} ${r.unit}`) },
        { key: "unit_price", label: "Price each", align: "right", render: (r) => (r.unit_price ? `$${Number(r.unit_price).toFixed(4).replace(/0{1,2}$/, "")}` : "") },
        { key: "amount", label: "Amount", align: "right", render: (r) => (r.code === "total" ? <b>{usd(String(r.amount))}</b> : usd(String(r.amount))) },
      ]}
    />
  );
}

export function PlanWorkspace() {
  return (
    <Workspace title="Billing & usage" description="Every feature is included. You pay only for the storage and activity you use; moving data in and keeping it in sync are free." accent="#8b7cff">
      <RequiresPermission permission="account.billing.read" area="Billing & usage">
        <PlanContent />
      </RequiresPermission>
    </Workspace>
  );
}

function PlanContent() {
  const [version, setVersion] = useState(0);
  const summary = useLoad(() => get<Summary>("/api/v1/account-billing/summary"), `billing:${version}`);
  const refresh = () => setVersion((v) => v + 1);
  const s = summary.data;
  if (summary.error) return <Notice kind="error">{summary.error}</Notice>;
  if (!s) return <p className="rwMuted">Loading…</p>;
  return (
    <>
      {s.exempt ? <Notice kind="info">This is your own business workspace: it is never billed. The figures below show what it would cost a customer.</Notice> : null}
      <Grid>
        <Card title={`This month so far (${longDate(s.month.start)} – today)`} testId="billing-estimate">
          <p className="rwMuted small">
            Storage averages {Number(s.so_far.storage_gb).toLocaleString("en-US", { maximumFractionDigits: 3 })} GB; {s.so_far.requests.toLocaleString("en-US")} actions so far. Estimated bill for the whole month:
          </p>
          <QuoteTable quote={s.estimate} testId="billing-estimate-table" />
          <p className="rwMuted small">
            Your invoice is emailed on the 1st of next month. The card on file is charged automatically {s.charge_after_business_days} business days later.
          </p>
        </Card>
        <CardOnFile summary={s} onChange={refresh} />
      </Grid>
      <Calculator rates={s.rates} />
      <Invoices invoices={s.invoices} onChange={refresh} />
    </>
  );
}

function CardOnFile({ summary, onChange }: { summary: Summary; onChange: () => void }) {
  const { can, loaded } = usePermissions();
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [log, onDone] = useActionLog();
  const card = summary.card;
  const manage = loaded && can("account.billing.manage");

  async function startCardSetup() {
    setBusy(true);
    setError("");
    try {
      const { url } = await post<{ url: string }>("/api/v1/account-billing/card", { authorize_automatic_charges: agree });
      window.location.assign(url); // Stripe's secure page; the card number never touches Krov WorkAgent
    } catch (e) {
      setError(errorText(e));
      setBusy(false);
    }
  }

  return (
    <Card title="Card on file" testId="billing-card">
      {card ? (
        <p data-testid="card-on-file">
          <b>{card.brand.charAt(0).toUpperCase() + card.brand.slice(1)}</b> ending in <b>{card.last4}</b>, expires {String(card.exp_month).padStart(2, "0")}/{card.exp_year}
        </p>
      ) : (
        <p className="rwMuted">No card on file yet. Add one so invoices are paid automatically.</p>
      )}
      {!summary.payments_ready ? <Notice kind="info">Card payments are not switched on for this server yet (the Stripe key is missing).</Notice> : null}
      {manage ? (
        <>
          <label className="rwCheck">
            <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} data-testid="billing-authorize" />
            <span>
              I authorize Krov WorkAgent to charge this card automatically for each monthly invoice, {summary.charge_after_business_days} business days after the invoice is emailed.
            </span>
          </label>
          <div className="rwActions">
            <button type="button" className="rwBtn primary" disabled={!agree || busy || !summary.payments_ready} onClick={startCardSetup} data-testid="billing-add-card">
              {busy ? "Opening secure card page…" : card ? "Replace card" : "Add a card"}
            </button>
            {card ? (
              <ActionButton
                label="Remove card"
                permission="account.billing.manage"
                testId="billing-remove-card"
                onDone={(m, ok) => {
                  onDone(m, ok);
                  onChange();
                }}
                run={() => del("/api/v1/account-billing/card")}
              />
            ) : null}
          </div>
          {error ? <Notice kind="error">{error}</Notice> : null}
          {log}
        </>
      ) : (
        <p className="rwMuted small">Only the workspace owner can change the card.</p>
      )}
    </Card>
  );
}

function Calculator({ rates }: { rates: Summary["rates"] }) {
  const [storage, setStorage] = useState("1");
  const [actions, setActions] = useState("50000");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [error, setError] = useState("");
  async function run(event?: FormEvent) {
    event?.preventDefault();
    setError("");
    try {
      setQuote(await post<Quote>("/api/v1/account-billing/calculator", { storage_gb: storage || "0", requests: Math.round(Number(actions || 0)) }));
    } catch (e) {
      setError(errorText(e));
    }
  }
  return (
    <Card title="Cost calculator" testId="billing-calculator">
      <p className="rwMuted small">
        Prices: storage {usd(rates.storage_gb_month)} per GB per month · activity {usd(rates.per_1k_requests)} per 1,000 actions · card processing {usd(rates.payment_processing)} per monthly payment. Every feature is
        included; moving your data in and syncing banks, payroll and carriers are free.
      </p>
      <form className="rwForm rwInlineForm" onSubmit={run}>
        <label>
          <span>Storage (GB)</span>
          <input type="number" min="0" step="0.1" value={storage} onChange={(e) => setStorage(e.target.value)} data-testid="calc-storage" />
        </label>
        <label>
          <span>Actions per month</span>
          <input type="number" min="0" step="1000" value={actions} onChange={(e) => setActions(e.target.value)} data-testid="calc-actions" />
        </label>
        <button type="submit" className="rwBtn primary" data-testid="calc-run">
          Calculate
        </button>
      </form>
      {error ? <Notice kind="error">{error}</Notice> : null}
      {quote ? (
        <>
          <p data-testid="calc-total" className="rwBig">
            {usd(quote.total)} <span className="rwMuted small">per month</span>
          </p>
          <QuoteTable quote={quote} />
        </>
      ) : null}
    </Card>
  );
}

function Invoices({ invoices, onChange }: { invoices: Invoice[]; onChange: () => void }) {
  const [log, onDone] = useActionLog();
  return (
    <Card title="Invoices" testId="billing-invoices">
      <Table<Invoice>
        rows={invoices}
        empty="No invoices yet. Your first one arrives on the 1st of next month."
        columns={[
          { key: "number", label: "Invoice" },
          { key: "period_start", label: "Month", render: (i) => new Date(`${i.period_start}T12:00:00`).toLocaleDateString("en-US", { month: "long", year: "numeric" }) },
          { key: "total", label: "Total", align: "right", render: (i) => usd(i.total) },
          { key: "status", label: "Status", render: (i) => <Badge value={i.status === "open" ? "scheduled" : i.status} /> },
          { key: "charge_on", label: "Card charged on", render: (i) => (i.status === "paid" ? "Paid" : longDate(i.charge_on)) },
          { key: "emailed_to", label: "Emailed to", render: (i) => i.emailed_to || "—" },
          {
            key: "id",
            label: "",
            render: (i) =>
              i.status === "failed" || i.status === "uncollected" ? (
                <ActionButton
                  label="Pay now"
                  permission="account.billing.manage"
                  onDone={(m, ok) => {
                    onDone(m, ok);
                    onChange();
                  }}
                  run={() => post(`/api/v1/account-billing/invoices/${i.id}/pay`)}
                />
              ) : i.last_error ? (
                <span className="rwMuted small">{i.last_error}</span>
              ) : null,
          },
        ]}
      />
      {log}
    </Card>
  );
}
