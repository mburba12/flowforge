$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$TablePath = Join-Path $Web "src\components\data-table.tsx"
$CssPath = Join-Path $Web "src\app\globals.css"

if (-not (Test-Path -LiteralPath $TablePath)) { throw "Run from the FlowForge project root." }

$Table = @'
"use client";

import { FormEvent, useMemo, useState } from "react";
import type { TableColumn } from "@/lib/types";

export function DataTable({ columns, rows }: { columns: TableColumn[]; rows: Record<string, string>[] }) {
  const [query, setQuery] = useState("");
  const [data, setData] = useState(rows);
  const [selected, setSelected] = useState<Record<string, string> | null>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("");

  const filtered = useMemo(
    () => data.filter((row) => Object.values(row).join(" ").toLowerCase().includes(query.toLowerCase())),
    [data, query],
  );

  function open(row: Record<string, string>) {
    setSelected(row);
    setDraft({ ...row });
    setEditing(false);
  }

  function close() {
    setSelected(null);
    setEditing(false);
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const rowId = selected?.id;
    setData((current) => current.map((row) => (row.id === rowId ? { ...row, ...draft } : row)));
    setSelected({ ...draft });
    setEditing(false);
    setNotice(`${draft.id || draft.name || "Record"} updated locally`);
    window.setTimeout(() => setNotice(""), 3000);
  }

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
            <tbody>{filtered.map((row, index) => (
              <tr className="clickable-row" key={row.id ?? index} tabIndex={0} role="button" onClick={() => open(row)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(row); } }}>
                {columns.map((column) => <td className={column.align === "right" ? "right" : ""} key={column.key}>{column.key === "status" ? <span className="status">{row[column.key]}</span> : row[column.key]}</td>)}
              </tr>
            ))}</tbody>
          </table>
          {!filtered.length && <div className="empty">No matching records</div>}
        </div>
      </div>

      {notice && <div className="record-toast" role="status">{notice}</div>}

      {selected && (
        <div className="record-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}>
          <section className="record-drawer" role="dialog" aria-modal="true">
            <header className="record-head"><div><small>{editing ? "Edit record" : "Record details"}</small><h2>{selected.id ?? selected.name ?? "Record"}</h2></div><button type="button" className="iconbtn" onClick={close}>X</button></header>
            {editing ? (
              <form className="record-body" onSubmit={save}>
                <div className="record-grid">{columns.map((column) => (
                  <label className="record-edit-field" key={column.key}><span>{column.label}</span><input value={draft[column.key] ?? ""} onChange={(event) => setDraft((current) => ({ ...current, [column.key]: event.target.value }))} /></label>
                ))}</div>
                <div className="record-note">Changes are stored only in this browser session until the workspace API is connected.</div>
                <div className="record-actions inline"><button type="button" className="btn" onClick={() => { setDraft({ ...selected }); setEditing(false); }}>Cancel</button><button type="submit" className="btn primary">Save changes</button></div>
              </form>
            ) : (
              <><div className="record-body"><div className="record-grid">{columns.map((column) => <div className="record-field" key={column.key}><span>{column.label}</span><strong>{selected[column.key] || "-"}</strong></div>)}</div><div className="record-section"><h3>Activity</h3><div className="record-event"><span className="dot"/><div><strong>Record opened</strong><p>Viewing local demonstration details.</p></div></div><div className="record-event"><span className="dot"/><div><strong>Last synchronized</strong><p>Demo data refreshed 18 minutes ago.</p></div></div></div><div className="record-note">Production actions remain disabled until this workspace is connected to its backend API.</div></div><footer className="record-actions"><button type="button" className="btn" onClick={close}>Close</button><button type="button" className="btn primary" onClick={() => setEditing(true)}>Edit record</button></footer></>
            )}
          </section>
        </div>
      )}
    </>
  );
}
'@

[IO.File]::WriteAllText($TablePath, $Table, [Text.UTF8Encoding]::new($false))

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.record-edit-field') {
$Css += @'

.record-edit-field{display:grid;gap:6px}.record-edit-field span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}.record-edit-field input{border:1px solid var(--line);border-radius:8px;padding:10px;background:white;color:var(--text);font-weight:650}.record-actions.inline{padding:20px 0 0;border:0}.record-toast{position:fixed;right:22px;top:82px;z-index:120;background:#133e32;color:white;padding:12px 16px;border-radius:10px;font-size:12px;font-weight:750}
'@
}
[IO.File]::WriteAllText($CssPath, $Css, [Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
  npm run typecheck
  if ($LASTEXITCODE -ne 0) { throw "Record editor TypeScript validation failed." }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "Record editor build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE INLINE RECORD EDITOR PASSED" -ForegroundColor Green
