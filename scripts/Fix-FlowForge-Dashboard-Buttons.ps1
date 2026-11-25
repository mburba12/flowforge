$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$Page = Join-Path $Web "src\app\dashboard\page.tsx"
$Component = Join-Path $Web "src\components\dashboard-actions.tsx"
$Css = Join-Path $Web "src\app\globals.css"

foreach ($Path in @($Page, $Css)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$ComponentText = @'
"use client";

import { FormEvent, useState } from "react";

type Dialog = "customize" | "create" | null;

export function DashboardActions() {
  const [dialog, setDialog] = useState<Dialog>(null);
  const [title, setTitle] = useState("");
  const [module, setModule] = useState("Accounts payable");
  const [view, setView] = useState("Executive overview");
  const [showCash, setShowCash] = useState(true);
  const [showWork, setShowWork] = useState(true);
  const [showActivity, setShowActivity] = useState(true);
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
      <div className="actions">
        <button type="button" className="btn" onClick={() => setDialog("customize")}>Customize</button>
        <button type="button" className="btn primary" onClick={() => setDialog("create")}>+ Create</button>
      </div>

      {notice && <div className="dashboard-toast" role="status">{notice}</div>}

      {dialog && (
        <div className="dashboard-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialog(null); }}>
          <section className="dashboard-modal" role="dialog" aria-modal="true" aria-label={dialog === "customize" ? "Customize dashboard" : "Create record"}>
            <header className="dashboard-modal-head">
              <div><small>Dashboard</small><h2>{dialog === "customize" ? "Customize dashboard" : "Create a record"}</h2></div>
              <button type="button" className="iconbtn" onClick={() => setDialog(null)} aria-label="Close dialog">X</button>
            </header>

            {dialog === "customize" ? (
              <div className="dashboard-modal-body">
                <label className="dashboard-field">Dashboard view
                  <select value={view} onChange={(event) => setView(event.target.value)}>
                    <option>Executive overview</option><option>Finance focus</option><option>Operations focus</option><option>My work</option>
                  </select>
                </label>
                <label className="dashboard-check"><input type="checkbox" checked={showCash} onChange={(event) => setShowCash(event.target.checked)} /> Cash-flow outlook</label>
                <label className="dashboard-check"><input type="checkbox" checked={showWork} onChange={(event) => setShowWork(event.target.checked)} /> Priority work</label>
                <label className="dashboard-check"><input type="checkbox" checked={showActivity} onChange={(event) => setShowActivity(event.target.checked)} /> Recent activity</label>
                <div className="dashboard-modal-actions"><button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button><button type="button" className="btn primary" onClick={() => finish(`${view} layout saved locally`)}>Save layout</button></div>
              </div>
            ) : (
              <form className="dashboard-modal-body" onSubmit={create}>
                <p className="dashboard-help">Creates a local demonstration record. No production data is written until the module API is connected.</p>
                <label className="dashboard-field">Module
                  <select value={module} onChange={(event) => setModule(event.target.value)}>
                    <option>Accounts payable</option><option>Accounts receivable</option><option>Orders</option><option>Inventory</option><option>Payroll</option><option>Tax</option><option>Work queue</option>
                  </select>
                </label>
                <label className="dashboard-field">Title or reference
                  <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Enter a record name" autoFocus />
                </label>
                <label className="dashboard-field">Notes<textarea placeholder="Optional details" /></label>
                <div className="dashboard-modal-actions"><button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button><button type="submit" className="btn primary" disabled={!title.trim()}>Create demo record</button></div>
              </form>
            )}
          </section>
        </div>
      )}
    </>
  );
}
'@
[IO.File]::WriteAllText($Component, $ComponentText, [Text.UTF8Encoding]::new($false))

$env:FLOWFORGE_DASHBOARD_PAGE = $Page
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { throw "Project Python not found: $Python" }

@'
import os
import re
from pathlib import Path

path = Path(os.environ["FLOWFORGE_DASHBOARD_PAGE"])
text = path.read_text(encoding="utf-8")

import_line = 'import { DashboardActions } from "@/components/dashboard-actions";'
if import_line not in text:
    lines = text.splitlines()
    indexes = [i for i, line in enumerate(lines) if line.startswith("import ")]
    if not indexes:
        raise RuntimeError("Dashboard import block was not found")
    lines.insert(indexes[-1] + 1, import_line)
    text = "\n".join(lines)

pattern = re.compile(
    r'<div className="actions">\s*<StatusBanner\s*/>\s*<button className="btn">Customize</button>\s*<button className="btn primary">[^<]*Create</button>\s*</div>'
)
replacement = '<div className="actions"><StatusBanner/><DashboardActions/></div>'
text, count = pattern.subn(replacement, text, count=1)

if count != 1 and "<DashboardActions" not in text:
    raise RuntimeError("Dashboard Customize/Create button block was not found")

path.write_text(text.rstrip() + "\n", encoding="utf-8")
print("PATCHED: dashboard/page.tsx")
'@ | & $Python -

if ($LASTEXITCODE -ne 0) { throw "Dashboard page patch failed." }

$CssText = Get-Content -LiteralPath $Css -Raw
if ($CssText -notmatch '\.dashboard-modal-backdrop') {
$CssText += @'

.dashboard-modal-backdrop{position:fixed;inset:0;z-index:100;background:#10182b80;display:grid;place-items:center;padding:18px;backdrop-filter:blur(3px)}
.dashboard-modal{width:min(540px,100%);background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 28px 80px #10182b4d;overflow:hidden}
.dashboard-modal-head{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--line)}
.dashboard-modal-head small{color:var(--primary);text-transform:uppercase;letter-spacing:.11em;font-weight:800}.dashboard-modal-head h2{margin:4px 0 0;font-size:21px}
.dashboard-modal-body{padding:20px}.dashboard-help{color:var(--muted);font-size:12px;line-height:1.55;margin-top:0}
.dashboard-field{display:grid;gap:7px;margin:14px 0;font-size:12px;font-weight:750}.dashboard-field input,.dashboard-field select,.dashboard-field textarea{border:1px solid var(--line);border-radius:9px;padding:10px 11px;background:white;color:var(--text);outline:none}.dashboard-field textarea{min-height:80px;resize:vertical}
.dashboard-check{display:flex;gap:9px;align-items:center;padding:8px 0;font-size:12px}.dashboard-check input{accent-color:var(--primary)}
.dashboard-modal-actions{display:flex;justify-content:flex-end;gap:9px;margin-top:20px}.dashboard-modal-actions .btn:disabled{opacity:.45;cursor:not-allowed}
.dashboard-toast{position:fixed;right:22px;top:82px;z-index:110;background:#133e32;color:white;padding:12px 16px;border-radius:10px;box-shadow:0 12px 36px #133e3240;font-size:12px;font-weight:750}
@media(max-width:680px){.dashboard-modal-backdrop{align-items:end;padding:7px}.dashboard-modal{border-radius:16px 16px 10px 10px}.dashboard-toast{left:14px;right:14px;top:76px}}
'@
}
[IO.File]::WriteAllText($Css, $CssText, [Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Dashboard action TypeScript validation failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Dashboard action production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE DASHBOARD BUTTONS PASSED" -ForegroundColor Green
