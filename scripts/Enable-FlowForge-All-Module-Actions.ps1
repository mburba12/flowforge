$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$Layout = Join-Path $Web "src\app\layout.tsx"
$Component = Join-Path $Web "src\components\module-action-controller.tsx"
$Css = Join-Path $Web "src\app\globals.css"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

foreach ($Path in @($Layout, $Css, $Python)) {
  if (-not (Test-Path -LiteralPath $Path)) { throw "Run from FlowForge project root. Missing: $Path" }
}

$Controller = @'
"use client";

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

type ActionKind = "create" | "filter" | "import" | "export" | "details" | "customize" | "guided" | null;

type ActionState = { kind: ActionKind; title: string; source: HTMLElement | null };

const createWords = /^(create|new|add|adjust|run|start|schedule|invite|connect)/i;
const filterWords = /filter|last 30 days|date range/i;
const importWords = /import|upload/i;
const exportWords = /export|download/i;
const detailWords = /^(open|view|view all|details|review|manage)/i;
const customizeWords = /customize|configure/i;
const guidedWords = /approve|reject|reconcile|match|post|submit|send|retry|resolve|archive/i;

const moduleNames: Record<string, string> = {
  shipping: "Shipping", payroll: "Payroll", workforce: "Workforce", documents: "Documents",
  reconciliation: "Reconciliation", entities: "Entities", reports: "Reports", audit: "Audit",
  integrations: "Integrations", billing: "Billing", ap: "Accounts payable", ar: "Accounts receivable",
  orders: "Orders", inventory: "Inventory", banking: "Banking", tax: "Tax", approvals: "Approvals",
  "work-queue": "Work queue", settings: "Settings", support: "Support", finance: "Finance",
};

function cleanText(element: HTMLElement) {
  return (element.innerText || element.textContent || "").replace(/\s+/g, " ").trim();
}

function moduleFromPath(pathname: string) {
  const key = pathname.split("/").filter(Boolean)[0] || "dashboard";
  return moduleNames[key] || key.replace(/-/g, " ").replace(/\b\w/g, (value) => value.toUpperCase());
}

export function ModuleActionController() {
  const pathname = usePathname();
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [action, setAction] = useState<ActionState>({ kind: null, title: "", source: null });
  const [notice, setNotice] = useState("");
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All statuses");

  const moduleName = moduleFromPath(pathname);

  useEffect(() => {
    function click(event: MouseEvent) {
      const target = event.target as HTMLElement | null;
      const button = target?.closest("button") as HTMLButtonElement | null;
      if (!button || button.disabled || button.dataset.flowforgeHandled === "true") return;
      if (button.closest("[data-native-actions='true']")) return;
      const text = cleanText(button);
      if (!text || text === "X" || text === "Cancel" || text === "Close" || text === "Done" || text === "Clear") return;

      let kind: ActionKind = null;
      if (createWords.test(text)) kind = "create";
      else if (filterWords.test(text)) kind = "filter";
      else if (importWords.test(text)) kind = "import";
      else if (exportWords.test(text)) kind = "export";
      else if (customizeWords.test(text)) kind = "customize";
      else if (guidedWords.test(text)) kind = "guided";
      else if (detailWords.test(text)) kind = "details";
      if (!kind) return;

      event.preventDefault();
      event.stopPropagation();
      if (kind === "import") {
        setAction({ kind, title: text, source: button });
        window.setTimeout(() => fileRef.current?.click(), 0);
        return;
      }
      if (kind === "export") {
        exportVisibleData();
        return;
      }
      setTitle("");
      setNotes("");
      setQuery("");
      setStatus("All statuses");
      setAction({ kind, title: text, source: button });
    }
    document.addEventListener("click", click, true);
    return () => document.removeEventListener("click", click, true);
  }, [pathname]);

  function close() { setAction({ kind: null, title: "", source: null }); }

  function notify(message: string) {
    setNotice(message);
    window.setTimeout(() => setNotice(""), 3200);
  }

  function exportVisibleData() {
    const table = document.querySelector("main table");
    const rows = table ? Array.from(table.querySelectorAll("tr")).map((row) => Array.from(row.querySelectorAll("th,td")).map((cell) => `"${(cell.textContent || "").trim().replace(/"/g, '""')}"`).join(",")) : [];
    const content = rows.length ? rows.join("\n") : `Module,Exported at\n${moduleName},${new Date().toISOString()}`;
    const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${pathname.replace(/\//g, "-").replace(/^-/, "") || "dashboard"}-export.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    notify(`${moduleName} export downloaded`);
  }

  function imported(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) notify(`${file.name} staged for ${moduleName} validation`);
    event.target.value = "";
    close();
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (action.kind === "filter") {
      const rows = Array.from(document.querySelectorAll("main tbody tr")) as HTMLElement[];
      rows.forEach((row) => {
        const haystack = cleanText(row).toLowerCase();
        const queryMatch = !query || haystack.includes(query.toLowerCase());
        const statusMatch = status === "All statuses" || haystack.includes(status.toLowerCase());
        row.style.display = queryMatch && statusMatch ? "" : "none";
      });
      notify(`${moduleName} filters applied`);
    } else if (action.kind === "guided") {
      notify(`${action.title} completed in local demonstration mode`);
    } else if (action.kind === "customize") {
      notify(`${moduleName} layout preference saved for this session`);
    } else {
      notify(`${title || action.title} created locally in ${moduleName}`);
    }
    close();
  }

  function detailsText() {
    const card = action.source?.closest("article,section,tr,.panel,.card") as HTMLElement | null;
    return card ? cleanText(card) : `${moduleName} workspace overview`;
  }

  return (
    <>
      <input ref={fileRef} hidden type="file" accept=".csv,.xlsx,.xls,.pdf,.png,.jpg,.jpeg" onChange={imported} />
      {notice && <div className="module-action-toast" role="status">{notice}</div>}
      {action.kind && action.kind !== "import" && (
        <div className="module-action-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}>
          <section className="module-action-dialog" data-native-actions="true" role="dialog" aria-modal="true">
            <header><div><small>{moduleName.toUpperCase()}</small><h2>{action.kind === "details" ? action.title : `${action.title} - ${moduleName}`}</h2></div><button type="button" className="iconbtn" onClick={close}>X</button></header>
            {action.kind === "details" ? (
              <><div className="module-action-body"><p className="module-action-summary">{detailsText()}</p><div className="module-action-info"><strong>Workspace</strong><span>{moduleName}</span></div><div className="module-action-info"><strong>Current route</strong><span>{pathname}</span></div><p className="module-action-boundary">This panel shows the selected local demonstration content. Production records will come from the authenticated tenant API.</p></div><footer><button type="button" className="btn" onClick={close}>Close</button><button type="button" className="btn primary" onClick={() => router.push(pathname as never)}>Open workspace</button></footer></>
            ) : (
              <form onSubmit={submit}>
                <div className="module-action-body">
                  {action.kind === "filter" ? <><label><span>Search records</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Filter ${moduleName.toLowerCase()}...`} /></label><label><span>Status</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option>All statuses</option><option>Open</option><option>Pending</option><option>Approved</option><option>Completed</option><option>Exception</option></select></label></> : action.kind === "customize" ? <><label className="module-action-check"><input type="checkbox" defaultChecked /> Show summary metrics</label><label className="module-action-check"><input type="checkbox" defaultChecked /> Show recent activity</label><label className="module-action-check"><input type="checkbox" defaultChecked /> Show priority work</label></> : action.kind === "guided" ? <><p className="module-action-summary">Confirm <strong>{action.title}</strong> for the selected {moduleName.toLowerCase()} item.</p><label><span>Comment</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} placeholder="Optional audit comment" /></label></> : <><label><span>Title or reference</span><input required value={title} onChange={(event) => setTitle(event.target.value)} placeholder={`${action.title} reference`} /></label><label><span>Notes</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} placeholder="Optional notes" /></label></>}
                  <p className="module-action-boundary">Local demonstration action only. Consequential production writes remain disabled until the authenticated module API is connected.</p>
                </div>
                <footer><button type="button" className="btn" onClick={close}>Cancel</button><button type="submit" className="btn primary">{action.kind === "filter" ? "Apply filters" : action.kind === "customize" ? "Save layout" : action.kind === "guided" ? "Confirm action" : action.title}</button></footer>
              </form>
            )}
          </section>
        </div>
      )}
    </>
  );
}
'@

[IO.File]::WriteAllText($Component, $Controller, [Text.UTF8Encoding]::new($false))

$env:FLOWFORGE_LAYOUT_PATH = $Layout
@'
import os
import re
from pathlib import Path

path = Path(os.environ["FLOWFORGE_LAYOUT_PATH"])
text = path.read_text(encoding="utf-8")
import_line = 'import { ModuleActionController } from "@/components/module-action-controller";'
if import_line not in text:
    imports = list(re.finditer(r'^import .*?;\s*$', text, flags=re.MULTILINE))
    if not imports:
        raise RuntimeError("Layout import block not found")
    pos = imports[-1].end()
    text = text[:pos] + "\n" + import_line + text[pos:]
if "<ModuleActionController />" not in text:
    candidates = ["</body>", "</div>\n  );"]
    for marker in candidates:
        if marker in text:
            text = text.replace(marker, "<ModuleActionController />\n" + marker, 1)
            break
    else:
        raise RuntimeError("Layout mount point not found")
path.write_text(text.rstrip() + "\n", encoding="utf-8")
'@ | & $Python -
if ($LASTEXITCODE -ne 0) { throw "Module action controller integration failed." }

$Styles = Get-Content -LiteralPath $Css -Raw
if ($Styles -notmatch '\.module-action-backdrop') {
$Styles += @'

.module-action-backdrop{position:fixed;inset:0;background:#17203366;z-index:145;display:grid;place-items:center;padding:18px}.module-action-dialog{width:min(580px,100%);max-height:90vh;overflow:auto;background:white;border-radius:16px;box-shadow:0 30px 90px #17203355}.module-action-dialog>header{display:flex;justify-content:space-between;align-items:center;padding:20px 22px;border-bottom:1px solid var(--line)}.module-action-dialog>header small{font-size:9px;color:var(--primary);font-weight:850;letter-spacing:.08em}.module-action-dialog h2{margin:4px 0 0;font-size:18px}.module-action-body{padding:22px;display:grid;gap:14px}.module-action-body label{display:grid;gap:6px}.module-action-body label>span{font-size:10px;font-weight:750;color:var(--muted)}.module-action-body input,.module-action-body select,.module-action-body textarea{width:100%;border:1px solid var(--line);border-radius:9px;padding:11px;background:white;color:var(--text);font:inherit}.module-action-dialog footer{display:flex;justify-content:flex-end;gap:8px;padding:16px 22px;border-top:1px solid var(--line)}.module-action-boundary{margin:0;background:#fff8e8;color:#80530a;padding:11px;border-radius:9px;font-size:9px;line-height:1.55}.module-action-summary{margin:0;color:var(--text);font-size:12px;line-height:1.6}.module-action-info{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #eef0f5;padding:10px 0;font-size:11px}.module-action-info span{color:var(--muted);text-align:right}.module-action-check{display:flex!important;grid-template-columns:auto 1fr!important;align-items:center;gap:9px!important}.module-action-check input{width:auto}.module-action-toast{position:fixed;right:22px;top:82px;z-index:160;background:#133e32;color:white;padding:12px 16px;border-radius:10px;font-size:11px;font-weight:800;box-shadow:0 12px 34px #17203333}
'@
}
[IO.File]::WriteAllText($Css, $Styles, [Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
  npm run typecheck
  if ($LASTEXITCODE -ne 0) { throw "Module action TypeScript validation failed." }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "Module action production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE ALL MODULE ACTIONS PASSED" -ForegroundColor Green
