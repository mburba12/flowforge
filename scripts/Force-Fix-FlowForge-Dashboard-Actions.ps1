$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$PagePath = Join-Path $Web "src\app\dashboard\page.tsx"
$ActionsPath = Join-Path $Web "src\components\dashboard-actions.tsx"
$CssPath = Join-Path $Web "src\app\globals.css"

foreach ($Path in @($PagePath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Actions = @'
"use client";

import { FormEvent, useState } from "react";

type Dialog = "customize" | "create" | null;

export function DashboardActions() {
  const [dialog, setDialog] = useState<Dialog>(null);
  const [title, setTitle] = useState("");
  const [module, setModule] = useState("Accounts payable");
  const [view, setView] = useState("Executive overview");
  const [notice, setNotice] = useState("");

  function finish(message: string) {
    setNotice(message);
    setDialog(null);
    window.setTimeout(() => setNotice(""), 3500);
  }

  function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;
    finish(`${title.trim()} created in ${module} demo mode`);
    setTitle("");
  }

  return (
    <>
      <div className="actions dashboard-actions">
        <button type="button" className="btn" onClick={() => setDialog("customize")}>Customize</button>
        <button type="button" className="btn primary" onClick={() => setDialog("create")}>+ Create</button>
      </div>

      {notice && <div className="dashboard-toast" role="status">{notice}</div>}

      {dialog && (
        <div className="dashboard-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialog(null); }}>
          <section className="dashboard-modal" role="dialog" aria-modal="true">
            <header className="dashboard-modal-head">
              <div><small>Dashboard</small><h2>{dialog === "customize" ? "Customize dashboard" : "Create a record"}</h2></div>
              <button type="button" className="iconbtn" onClick={() => setDialog(null)} aria-label="Close">X</button>
            </header>

            {dialog === "customize" ? (
              <div className="dashboard-modal-body">
                <label className="dashboard-field">Dashboard view
                  <select value={view} onChange={(event) => setView(event.target.value)}>
                    <option>Executive overview</option>
                    <option>Finance focus</option>
                    <option>Operations focus</option>
                    <option>My work</option>
                  </select>
                </label>
                <label className="dashboard-check"><input type="checkbox" defaultChecked /> Cash-flow outlook</label>
                <label className="dashboard-check"><input type="checkbox" defaultChecked /> Priority work</label>
                <label className="dashboard-check"><input type="checkbox" defaultChecked /> Recent activity</label>
                <div className="dashboard-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="button" className="btn primary" onClick={() => finish(`${view} layout saved locally`)}>Save layout</button>
                </div>
              </div>
            ) : (
              <form className="dashboard-modal-body" onSubmit={create}>
                <p className="dashboard-help">Creates a local demonstration record. Production writes remain disabled until the module API is connected.</p>
                <label className="dashboard-field">Module
                  <select value={module} onChange={(event) => setModule(event.target.value)}>
                    <option>Accounts payable</option><option>Accounts receivable</option><option>Orders</option><option>Inventory</option><option>Payroll</option><option>Tax</option><option>Work queue</option>
                  </select>
                </label>
                <label className="dashboard-field">Title or reference
                  <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Enter a record name" autoFocus />
                </label>
                <label className="dashboard-field">Notes<textarea placeholder="Optional details" /></label>
                <div className="dashboard-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="submit" className="btn primary" disabled={!title.trim()}>Create demo record</button>
                </div>
              </form>
            )}
          </section>
        </div>
      )}
    </>
  );
}
'@
[IO.File]::WriteAllText($ActionsPath, $Actions, [Text.UTF8Encoding]::new($false))

$Page = @'
"use client";

import { DashboardActions } from "@/components/dashboard-actions";
import { MetricCard } from "@/components/metric-card";
import { StatusBanner } from "@/components/status-banner";
import { activities, workItems } from "@/lib/demo-data";

const metrics = [
  { label: "Available cash", value: "$1.27M", delta: "+4.8% this month", trend: "up" as const, tone: "positive" as const },
  { label: "Receivables", value: "$412.9k", delta: "$74.3k overdue", trend: "down" as const, tone: "warning" as const },
  { label: "Payables", value: "$184.3k", delta: "$62.4k due this week", trend: "up" as const, tone: "neutral" as const },
  { label: "Open work", value: "22", delta: "3 critical", trend: "up" as const, tone: "danger" as const },
];

export default function Dashboard() {
  return (
    <>
      <div className="pagehead">
        <div>
          <div className="eyebrow">Tuesday, November 24</div>
          <h1>Good evening, Mack</h1>
          <p>Here is what needs attention across Apex Manufacturing.</p>
        </div>
        <div className="actions dashboard-head-actions">
          <StatusBanner />
          <DashboardActions />
        </div>
      </div>

      <div className="metrics">{metrics.map((metric) => <MetricCard metric={metric} key={metric.label} />)}</div>

      <div className="grid">
        <section className="panel">
          <div className="panelhead"><h2>Cash flow outlook</h2><button className="btn" type="button">Last 30 days</button></div>
          <div className="panelbody"><div className="chart">{[42,55,47,63,58,71,68,76,61,83,78,88].map((height,index) => <div className="bar" style={{ height: `${height}%` }} key={index} />)}</div></div>
        </section>
        <section className="panel">
          <div className="panelhead"><h2>Recent activity</h2><button className="btn" type="button">View all</button></div>
          <div className="panelbody">{activities.map((activity) => <div className="activity" key={activity.id}><span className="dot"/><div><strong>{activity.title}</strong><p>{activity.detail}</p><p>{activity.module} - {activity.timestamp}</p></div></div>)}</div>
        </section>
      </div>

      <div style={{ height: 18 }} />
      <div className="split">
        <section className="panel">
          <div className="panelhead"><h2>Priority work</h2><button className="btn" type="button">Open work queue</button></div>
          <div className="panelbody">{workItems.map((item) => <div className="workitem" key={item.id}><div className="worktop"><h3><span className={`severity ${item.severity}`}/>{item.title}</h3><span className="status">{item.status}</span></div><div className="workmeta">{item.module} - {item.owner} - Due {item.due}</div></div>)}</div>
        </section>
        <section className="panel">
          <div className="panelhead"><h2>Business health</h2></div>
          <div className="panelbody">
            <div className="featurecard"><h3>Order fulfillment</h3><p><strong className="positive">96.2%</strong> on time, up 1.4% from last month.</p></div>
            <div style={{ height: 9 }} /><div className="featurecard"><h3>Reconciliation</h3><p><strong className="warning">5 exceptions</strong> across cash, payroll, and inventory.</p></div>
            <div style={{ height: 9 }} /><div className="featurecard"><h3>Data freshness</h3><p>All critical sources synced within the last 18 minutes.</p></div>
          </div>
        </section>
      </div>
    </>
  );
}
'@
[IO.File]::WriteAllText($PagePath, $Page, [Text.UTF8Encoding]::new($false))

$CssText = Get-Content -LiteralPath $CssPath -Raw
if ($CssText -notmatch '\.dashboard-modal-backdrop') {
$CssText += @'

.dashboard-head-actions{align-items:center}.dashboard-head-actions>.dashboard-actions{display:flex}.dashboard-modal-backdrop{position:fixed;inset:0;z-index:100;background:#10182b80;display:grid;place-items:center;padding:18px;backdrop-filter:blur(3px)}.dashboard-modal{width:min(540px,100%);background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 28px 80px #10182b4d;overflow:hidden}.dashboard-modal-head{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--line)}.dashboard-modal-head small{color:var(--primary);text-transform:uppercase;letter-spacing:.11em;font-weight:800}.dashboard-modal-head h2{margin:4px 0 0;font-size:21px}.dashboard-modal-body{padding:20px}.dashboard-help{color:var(--muted);font-size:12px;line-height:1.55}.dashboard-field{display:grid;gap:7px;margin:14px 0;font-size:12px;font-weight:750}.dashboard-field input,.dashboard-field select,.dashboard-field textarea{border:1px solid var(--line);border-radius:9px;padding:10px 11px;background:white;color:var(--text)}.dashboard-field textarea{min-height:80px}.dashboard-check{display:flex;gap:9px;padding:8px 0;font-size:12px}.dashboard-modal-actions{display:flex;justify-content:flex-end;gap:9px;margin-top:20px}.dashboard-modal-actions .btn:disabled{opacity:.45}.dashboard-toast{position:fixed;right:22px;top:82px;z-index:110;background:#133e32;color:white;padding:12px 16px;border-radius:10px;font-size:12px;font-weight:750}@media(max-width:680px){.dashboard-modal-backdrop{align-items:end;padding:7px}.dashboard-toast{left:14px;right:14px}}
'@
}
[IO.File]::WriteAllText($CssPath, $CssText, [Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Dashboard TypeScript validation failed." }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Dashboard unit tests failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE DASHBOARD DIRECT ACTIONS PASSED" -ForegroundColor Green
