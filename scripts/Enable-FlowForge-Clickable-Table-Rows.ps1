$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$TablePath = Join-Path $Web "src\components\data-table.tsx"
$CssPath = Join-Path $Web "src\app\globals.css"

foreach ($Path in @($TablePath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Table = @'
"use client";

import { useMemo, useState } from "react";
import type { TableColumn } from "@/lib/types";

export function DataTable({ columns, rows }: { columns: TableColumn[]; rows: Record<string, string>[] }) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Record<string, string> | null>(null);

  const filtered = useMemo(
    () => rows.filter((row) => Object.values(row).join(" ").toLowerCase().includes(query.toLowerCase())),
    [query, rows],
  );

  const title = selected?.id ?? selected?.name ?? "Record";

  return (
    <>
      <div className="panel">
        <div className="toolbar">
          <input className="field" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter records..." />
          <button type="button" className="btn" onClick={() => setQuery("")}>Clear</button>
          <button type="button" className="btn" onClick={() => window.print()}>Export</button>
        </div>
        <div className="tablewrap">
          <table className="data">
            <thead><tr>{columns.map((column) => <th className={column.align === "right" ? "right" : ""} key={column.key}>{column.label}</th>)}</tr></thead>
            <tbody>
              {filtered.map((row, index) => (
                <tr
                  className="clickable-row"
                  key={row.id ?? index}
                  tabIndex={0}
                  role="button"
                  aria-label={`Open ${row.id ?? row.name ?? "record"}`}
                  onClick={() => setSelected(row)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setSelected(row);
                    }
                  }}
                >
                  {columns.map((column) => (
                    <td className={column.align === "right" ? "right" : ""} key={column.key}>
                      {column.key === "status" ? <span className="status">{row[column.key]}</span> : row[column.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {!filtered.length && <div className="empty">No matching records</div>}
        </div>
      </div>

      {selected && (
        <div className="record-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}>
          <section className="record-drawer" role="dialog" aria-modal="true" aria-label={`${title} details`}>
            <header className="record-head">
              <div><small>Record details</small><h2>{title}</h2></div>
              <button type="button" className="iconbtn" onClick={() => setSelected(null)} aria-label="Close record">X</button>
            </header>
            <div className="record-body">
              <div className="record-grid">
                {columns.map((column) => (
                  <div className="record-field" key={column.key}>
                    <span>{column.label}</span>
                    <strong>{selected[column.key] || "-"}</strong>
                  </div>
                ))}
              </div>
              <div className="record-section">
                <h3>Activity</h3>
                <div className="record-event"><span className="dot"/><div><strong>Record opened</strong><p>Viewing local demonstration details.</p></div></div>
                <div className="record-event"><span className="dot"/><div><strong>Last synchronized</strong><p>Demo data refreshed 18 minutes ago.</p></div></div>
              </div>
              <div className="record-note">Production editing, approvals, fulfillment, and posting remain disabled until this workspace is connected to its backend API.</div>
            </div>
            <footer className="record-actions">
              <button type="button" className="btn" onClick={() => setSelected(null)}>Close</button>
              <button type="button" className="btn primary" onClick={() => alert(`${title} edit workflow opened in demo mode`)}>Edit demo record</button>
            </footer>
          </section>
        </div>
      )}
    </>
  );
}
'@

[System.IO.File]::WriteAllText($TablePath, $Table, [System.Text.UTF8Encoding]::new($false))

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.record-backdrop') {
$Css += @'

.clickable-row{cursor:pointer;outline:none}.clickable-row:hover td,.clickable-row:focus td{background:#eef2ff!important}.clickable-row:focus{box-shadow:inset 3px 0 0 var(--primary)}
.record-backdrop{position:fixed;inset:0;z-index:100;background:#10182b70;display:flex;justify-content:flex-end;backdrop-filter:blur(2px)}
.record-drawer{width:min(520px,100%);height:100%;background:#fff;box-shadow:-20px 0 60px #10182b33;display:flex;flex-direction:column}
.record-head{display:flex;align-items:center;justify-content:space-between;padding:20px 22px;border-bottom:1px solid var(--line)}.record-head small{color:var(--primary);text-transform:uppercase;letter-spacing:.11em;font-weight:800}.record-head h2{margin:5px 0 0;font-size:23px}
.record-body{padding:22px;overflow:auto;flex:1}.record-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.record-field{display:grid;gap:5px;padding:13px;border:1px solid var(--line);border-radius:10px;background:#fafbfe}.record-field span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}.record-field strong{font-size:13px}
.record-section{margin-top:22px}.record-section h3{font-size:13px}.record-event{display:flex;gap:11px;padding:11px 0;border-bottom:1px solid var(--line)}.record-event strong{font-size:12px}.record-event p{font-size:10px;color:var(--muted);margin:3px 0}.record-note{margin-top:20px;padding:13px;border-radius:10px;background:#fff8e8;color:#8b5a10;font-size:11px;line-height:1.5}.record-actions{display:flex;justify-content:flex-end;gap:9px;padding:15px 20px;border-top:1px solid var(--line)}
@media(max-width:680px){.record-drawer{width:100%}.record-grid{grid-template-columns:1fr}}
'@
}
[System.IO.File]::WriteAllText($CssPath, $Css, [System.Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Clickable table TypeScript validation failed." }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Clickable table tests failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Clickable table production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE CLICKABLE TABLE ROWS PASSED" -ForegroundColor Green
