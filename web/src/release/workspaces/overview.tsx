"use client";

import Link from "next/link";

import { get, type Row } from "../client";
import { useLoad, usePermissions } from "../hooks";
import { Amount, Badge, Card, Grid, RequiresPermission, Table, Workspace } from "../ui";

type Aging = { total_open: string; buckets: Record<string, string> };

/** Dashboard: live figures from the release APIs, each shown only with the read permission. */
export function DashboardWorkspace() {
  const { can, loaded } = usePermissions();
  const ar = useLoad(async () => (can("ar.read") ? get<Aging>("/api/v3b/aging") : null), `ar:${loaded}`);
  const ap = useLoad(async () => (can("ap.read") ? get<Aging>("/api/v3/aging") : null), `ap:${loaded}`);
  const periods = useLoad(async () => (can("gl.read") ? get<Row[]>("/api/v2/accounting-periods") : null), `per:${loaded}`);
  const journals = useLoad(async () => (can("business.read") ? (await get<{ items: Row[] }>("/api/v1/business/journals", { limit: 200 })).items : null), `jr:${loaded}`);
  const runs = useLoad(async () => (can("business.read") ? (await get<{ items: Row[] }>("/api/v1/business/payroll-runs", { limit: 200 })).items : null), `pr:${loaded}`);
  const orders = useLoad(async () => (can("ar.read") ? get<Row[]>("/api/v3b/orders", { limit: 10 }) : null), `or:${loaded}`);
  const awaiting = (journals.data ?? []).filter((j) => j.status === "draft" || j.status === "approved").length;
  const runsAwaiting = (runs.data ?? []).filter((r) => r.status === "calculated" || r.status === "approved").length;
  const open = (periods.data ?? []).filter((p) => p.status === "open").map((p) => String(p.period_code));
  const tiles: [string, React.ReactNode, string][] = [];
  if (ar.data) tiles.push(["Receivables open", <Amount key="ar" value={ar.data.total_open} />, "/modules/ar"]);
  if (ap.data) tiles.push(["Payables open", <Amount key="ap" value={ap.data.total_open} />, "/modules/ap"]);
  if (journals.data) tiles.push(["Journals awaiting approval/posting", String(awaiting), "/modules/finance"]);
  if (runs.data) tiles.push(["Payroll runs awaiting action", String(runsAwaiting), "/modules/payroll"]);
  if (periods.data) tiles.push(["Open accounting periods", open.join(", ") || "none", "/modules/finance"]);
  return (
    <Workspace title="Dashboard" description="Live figures from your ledger, payables, receivables and payroll." accent="#2563eb">
      <div className="rwKpis" data-testid="dashboard-kpis">
        {loaded && tiles.length === 0 ? <p className="rwMuted">Your role does not include any dashboard figures.</p> : null}
        {tiles.map(([label, value, href]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
            <Link href={href as never}>Open</Link>
          </article>
        ))}
      </div>
      {orders.data ? (
        <Grid>
          <Card title="Latest orders">
            <Table
              rows={orders.data}
              columns={[
                { key: "order_number", label: "Order" },
                { key: "order_date", label: "Date" },
                { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
                { key: "total", label: "Total", align: "right", render: (r) => <Amount value={r.total} /> },
              ]}
              empty="No orders yet."
            />
          </Card>
          <span />
        </Grid>
      ) : null}
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
  return (
    <>
      <Card title="Latest 100 audit entries">
        <Table
          testId="audit-table"
          rows={audit.data}
          loading={audit.loading}
          error={audit.error}
          columns={[
            { key: "action", label: "Action", render: (r) => <Badge value={r.action} /> },
            { key: "resource_type", label: "Record type" },
            { key: "resource_id", label: "Record" },
          ]}
        />
      </Card>
    </>
  );
}
