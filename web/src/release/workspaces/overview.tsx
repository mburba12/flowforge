"use client";

import Link from "next/link";

import { AppIcon, type IconName } from "@/components/app-icon";

import { get, money, openFile, type Row } from "../client";
import { useLoad, usePermissions } from "../hooks";
import { ActionButton, Card, Grid, RequiresPermission, Table, Workspace, Badge, useActionLog } from "../ui";

type Aging = { total_open: string; buckets: Record<string, string> };
type Status = { banks: number; carriers: number; shipments: number; payroll_imports: number; files: number };
type BankOverview = { accounts: unknown[]; totals: { currency: string; cash: string; owed: string }[] };
type Txn = Row & { date: string; description: string; money_in: string | null; money_out: string | null; account: string };
type Shipment = Row & { id: string; status: string; reference: string | null; tracking_number: string; carrier_name: string; estimated_delivery: string | null; status_detail: string | null };

const QUICK: { label: string; href: string; icon: IconName; permission: string }[] = [
  { label: "Upload a bill", href: "/modules/ap", icon: "ap", permission: "documents.upload" },
  { label: "New sales order", href: "/modules/orders", icon: "orders", permission: "ar.order.write" },
  { label: "Record a payment", href: "/modules/ar", icon: "ar", permission: "ar.receipt.write" },
  { label: "Run payroll", href: "/modules/payroll", icon: "payroll", permission: "payroll.run.write" },
  { label: "Track a package", href: "/modules/shipping", icon: "shipping", permission: "shipping.track" },
  { label: "Import a bank statement", href: "/modules/banking", icon: "banking", permission: "banking.import" },
];

function greeting(): string {
  const hour = new Date().getHours();
  return hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
}

/** Home: what needs doing, the numbers that matter, and one-click shortcuts. */
export function DashboardWorkspace() {
  const { can, loaded } = usePermissions();
  const status = useLoad(() => get<Status>("/api/v1/connections/status"), "conn-status");
  const bank = useLoad(async () => (can("banking.read") ? get<BankOverview>("/api/v1/banking/overview") : null), `bank:${loaded}`);
  const txns = useLoad(async () => (can("banking.read") ? get<Txn[]>("/api/v1/banking/transactions", { limit: 6 }) : null), `tx:${loaded}`);
  const ar = useLoad(async () => (can("ar.read") ? get<Aging>("/api/v3b/aging") : null), `ar:${loaded}`);
  const ap = useLoad(async () => (can("ap.read") ? get<Aging>("/api/v3/aging") : null), `ap:${loaded}`);
  const ships = useLoad(
    async () => (can("shipping.read") ? get<{ shipments: Shipment[]; counts: Record<string, number> }>("/api/v1/shipping/shipments", { status: "active", limit: 6 }) : null),
    `sh:${loaded}`,
  );
  const runs = useLoad(async () => (can("business.read") ? (await get<{ items: Row[] }>("/api/v1/business/payroll-runs", { limit: 200 })).items : null), `pr:${loaded}`);
  const journals = useLoad(async () => (can("business.read") ? (await get<{ items: Row[] }>("/api/v1/business/journals", { limit: 200 })).items : null), `jr:${loaded}`);

  const s = status.data;
  const checklist = [
    { done: (s?.banks ?? 0) > 0, label: "Connect your bank", detail: "See balances and transactions without logging in to the bank.", href: "/modules/banking", permission: "banking.connect" },
    { done: (s?.payroll_imports ?? 0) > 0, label: "Move your payroll to Krov WorkAgent", detail: "Bring employees, pay rates and this year's totals from ADP, Gusto, Paychex and others.", href: "/modules/payroll", permission: "payroll.migrate" },
    { done: (s?.carriers ?? 0) > 0, label: "Connect FedEx, UPS, USPS or DHL", detail: "Track every package in one list.", href: "/modules/shipping", permission: "shipping.connect" },
    { done: (s?.files ?? 0) > 0, label: "Upload your first invoice or receipt", detail: "Every section has an Upload button; everything also lands in Files.", href: "/modules/documents", permission: "documents.upload" },
  ].filter((item) => can(item.permission));
  const remaining = checklist.filter((c) => !c.done);

  const cash = bank.data?.totals.find((t) => t.currency === "USD") ?? bank.data?.totals[0];
  const waitingRuns = (runs.data ?? []).filter((r) => r.status === "calculated" || r.status === "approved").length;
  const waitingJournals = (journals.data ?? []).filter((j) => j.status === "draft" || j.status === "approved").length;
  const counts = ships.data?.counts ?? {};
  const tiles: { label: string; value: string; href: string; hint?: string }[] = [];
  if (bank.data) tiles.push({ label: "Cash in the bank", value: cash ? money(cash.cash) : "—", href: "/modules/banking", hint: cash ? undefined : "Connect a bank" });
  if (ar.data) tiles.push({ label: "Customers owe you", value: money(ar.data.total_open), href: "/modules/ar" });
  if (ap.data) tiles.push({ label: "Bills to pay", value: money(ap.data.total_open), href: "/modules/ap" });
  if (ships.data) tiles.push({ label: "Packages on the way", value: String((counts.in_transit ?? 0) + (counts.out_for_delivery ?? 0) + (counts.label_created ?? 0)), href: "/modules/shipping", hint: counts.exception ? `${counts.exception} need attention` : undefined });
  if (runs.data) tiles.push({ label: "Payroll waiting on you", value: String(waitingRuns), href: "/modules/payroll" });
  if (journals.data) tiles.push({ label: "Journals to approve or post", value: String(waitingJournals), href: "/modules/finance" });

  return (
    <Workspace title={`${greeting()}`} description="Here's what's happening in your business today." accent="#57d3ff">
      {remaining.length ? (
        <Card title={`Finish setting up (${checklist.length - remaining.length} of ${checklist.length} done)`} testId="setup-checklist">
          <ul className="checklist">
            {checklist.map((item) => (
              <li key={item.label} className={item.done ? "done" : ""}>
                <span className="tick" aria-hidden="true">{item.done ? "✓" : ""}</span>
                <span>
                  <b>{item.label}</b>
                  <span className="rwMuted small">{item.detail}</span>
                </span>
                {item.done ? <span className="rwMuted small">Done</span> : (
                  <Link className="rwBtn" href={item.href as never}>
                    Start
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      <nav className="quickActions" aria-label="Quick actions">
        {QUICK.filter((q) => can(q.permission)).map((q) => (
          <Link key={q.label} href={q.href as never}>
            <AppIcon name={q.icon} />
            {q.label}
          </Link>
        ))}
      </nav>

      <div className="rwKpis" data-testid="dashboard-kpis">
        {loaded && tiles.length === 0 ? <p className="rwMuted">Your role does not include any dashboard figures.</p> : null}
        {tiles.map((t) => (
          <article key={t.label}>
            <span>{t.label}</span>
            <strong>{t.value}</strong>
            {t.hint ? <small className="rwMuted">{t.hint}</small> : null}
            <Link href={t.href as never}>Open</Link>
          </article>
        ))}
      </div>

      <Grid>
        {txns.data ? (
          <Card title="Latest bank activity" aside={<Link href={"/modules/banking" as never}>All transactions</Link>}>
            <Table
              rows={txns.data}
              empty="No bank transactions yet."
              columns={[
                { key: "date", label: "Date" },
                { key: "description", label: "Description" },
                {
                  key: "amount",
                  label: "Amount",
                  align: "right",
                  render: (t) => (t.money_in ? <span className="pos">+{money(t.money_in)}</span> : <span>−{money(t.money_out)}</span>),
                },
              ]}
            />
          </Card>
        ) : <span />}
        {ships.data ? (
          <Card title="Shipments on the way" aside={<Link href={"/modules/shipping" as never}>All shipments</Link>}>
            <Table
              rows={ships.data.shipments}
              empty="Nothing on the way."
              columns={[
                { key: "reference", label: "Shipment", render: (r) => r.reference || r.tracking_number },
                { key: "carrier_name", label: "Carrier" },
                { key: "status", label: "Status", render: (r) => <Badge value={String(r.status).replace(/_/g, " ")} /> },
                { key: "estimated_delivery", label: "Arrives" },
              ]}
            />
          </Card>
        ) : <span />}
      </Grid>
    </Workspace>
  );
}

/** Audit trail (latest 100 entries). */
export function AuditWorkspace() {
  return (
    <Workspace title="Audit trail" description="Every consequential change, with the acting user, newest first." accent="#64748b">
      <RequiresPermission permission="audit.read" area="The audit trail">
        <AuditEntries />
      </RequiresPermission>
    </Workspace>
  );
}

function AuditEntries() {
  const audit = useLoad(() => get<Row[]>("/api/v1/audit"), "audit");
  const [log, onDone] = useActionLog();
  return (
    <Card
      title="Latest 100 changes"
      testId="audit-card"
      aside={
        <ActionButton
          label="Export all changes"
          permission="audit.read"
          testId="audit-export"
          onDone={onDone}
          run={() => openFile("/api/v1/audit/export", `krov-workagent-audit-${new Date().toISOString().slice(0, 10)}.csv`, false)}
        />
      }
    >
      <p className="rwMuted small">Only the latest 100 are shown here. Export all changes downloads every change ever recorded as a spreadsheet (CSV).</p>
      {log}
      <Table
        testId="audit-table"
        rows={audit.data}
        loading={audit.loading}
        error={audit.error}
        columns={[
          { key: "occurred_at", label: "When", render: (r) => (r.occurred_at ? new Date(String(r.occurred_at)).toLocaleString() : "") },
          { key: "user", label: "Who", render: (r) => String(r.user || "system") },
          { key: "action", label: "Action", render: (r) => <Badge value={r.action} /> },
          { key: "resource_type", label: "Record type" },
          { key: "resource_id", label: "Record" },
        ]}
      />
    </Card>
  );
}
