$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$PagePath = Join-Path $Web "src\components\workspace-page.tsx"
$CssPath = Join-Path $Web "src\app\globals.css"

foreach ($Path in @($PagePath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Page = @'
"use client";

import { FormEvent, useState } from "react";
import { DataTable } from "./data-table";
import { MetricCard } from "./metric-card";
import type { WorkspaceConfig } from "@/lib/types";

type Dialog = "create" | "import" | null;

export function WorkspacePage({ config }: { config: WorkspaceConfig }) {
  const [dialog, setDialog] = useState<Dialog>(null);
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [fileName, setFileName] = useState("");
  const [notice, setNotice] = useState("");

  function finish(message: string) {
    setNotice(message);
    setDialog(null);
    window.setTimeout(() => setNotice(""), 3500);
  }

  function createRecord(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;
    finish(`${title.trim()} created in ${config.title} demo mode`);
    setTitle("");
    setAmount("");
  }

  function stageImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!fileName) return;
    finish(`${fileName} staged for ${config.title} validation`);
    setFileName("");
  }

  return (
    <>
      <div className="pagehead">
        <div>
          <div className="eyebrow">{config.eyebrow}</div>
          <h1>{config.title}</h1>
          <p>{config.description}</p>
        </div>
        <div className="actions">
          <button type="button" className="btn" onClick={() => setDialog("import")}>Import</button>
          <button type="button" className="btn primary" onClick={() => setDialog("create")}>+ {config.primaryAction}</button>
        </div>
      </div>

      {notice && <div className="workspace-toast" role="status">{notice}</div>}

      <div className="metrics">
        {config.metrics.map((metric) => <MetricCard metric={metric} key={metric.label} />)}
      </div>

      <DataTable columns={config.columns} rows={config.rows} />

      {dialog && (
        <div className="workspace-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialog(null); }}>
          <section className="workspace-modal" role="dialog" aria-modal="true" aria-label={dialog === "create" ? config.primaryAction : `Import ${config.title}`}>
            <header className="workspace-modal-head">
              <div><small>{config.eyebrow}</small><h2>{dialog === "create" ? config.primaryAction : `Import ${config.title}`}</h2></div>
              <button type="button" className="iconbtn" onClick={() => setDialog(null)} aria-label="Close">X</button>
            </header>

            {dialog === "create" ? (
              <form className="workspace-modal-body" onSubmit={createRecord}>
                <p className="workspace-help">Create a local demonstration record. Production submission remains disabled until the {config.title} API workflow is connected.</p>
                <label className="workspace-field">Title or reference
                  <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={`New ${config.title.toLowerCase()} record`} autoFocus />
                </label>
                <label className="workspace-field">Amount or quantity
                  <input value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="Optional" />
                </label>
                <label className="workspace-field">Notes<textarea placeholder="Add context, owner, or supporting details" /></label>
                <div className="workspace-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="submit" className="btn primary" disabled={!title.trim()}>Create demo record</button>
                </div>
              </form>
            ) : (
              <form className="workspace-modal-body" onSubmit={stageImport}>
                <p className="workspace-help">Select a local file for validation. No file is sent to an external service in demo mode.</p>
                <label className="workspace-upload">Select CSV, Excel, PDF, or image
                  <input type="file" accept=".csv,.xlsx,.xls,.pdf,.png,.jpg,.jpeg" onChange={(event) => setFileName(event.target.files?.[0]?.name ?? "")} />
                </label>
                {fileName && <div className="workspace-file">Selected: {fileName}</div>}
                <div className="workspace-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="submit" className="btn primary" disabled={!fileName}>Stage import</button>
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

[System.IO.File]::WriteAllText($PagePath, $Page, [System.Text.UTF8Encoding]::new($false))

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.workspace-modal-backdrop') {
$Css += @'

.workspace-modal-backdrop{position:fixed;inset:0;z-index:100;background:#10182b80;display:grid;place-items:center;padding:18px;backdrop-filter:blur(3px)}
.workspace-modal{width:min(540px,100%);background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 28px 80px #10182b4d;overflow:hidden}
.workspace-modal-head{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--line)}
.workspace-modal-head small{color:var(--primary);text-transform:uppercase;letter-spacing:.11em;font-weight:800}.workspace-modal-head h2{margin:4px 0 0;font-size:21px}
.workspace-modal-body{padding:20px}.workspace-help{color:var(--muted);font-size:12px;line-height:1.55;margin-top:0}
.workspace-field{display:grid;gap:7px;margin:14px 0;font-size:12px;font-weight:750}.workspace-field input,.workspace-field textarea{border:1px solid var(--line);border-radius:9px;padding:10px 11px;background:white;color:var(--text);outline:none}.workspace-field textarea{min-height:82px;resize:vertical}
.workspace-upload{display:grid;gap:12px;place-items:center;text-align:center;border:2px dashed #cfd7ea;background:#f8faff;border-radius:12px;padding:28px;color:var(--primary);font-size:12px;font-weight:750;cursor:pointer}.workspace-upload input{max-width:100%}.workspace-file{margin-top:12px;padding:10px;border-radius:8px;background:#eef2ff;color:#344ca8;font-size:11px}
.workspace-modal-actions{display:flex;justify-content:flex-end;gap:9px;margin-top:20px}.workspace-modal-actions .btn:disabled{opacity:.45;cursor:not-allowed}
.workspace-toast{position:fixed;right:22px;top:82px;z-index:110;background:#133e32;color:white;padding:12px 16px;border-radius:10px;box-shadow:0 12px 36px #133e3240;font-size:12px;font-weight:750}
@media(max-width:680px){.workspace-modal-backdrop{align-items:end;padding:7px}.workspace-modal{border-radius:16px 16px 10px 10px}.workspace-toast{left:14px;right:14px;top:76px}}
'@
}
[System.IO.File]::WriteAllText($CssPath, $Css, [System.Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Workspace button TypeScript validation failed." }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Workspace button unit tests failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Workspace button production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE WORKSPACE BUTTONS PASSED" -ForegroundColor Green
