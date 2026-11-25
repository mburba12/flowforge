$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$WebSrc = Join-Path $Root "web\src"
$Components = Join-Path $WebSrc "components"
$LayoutPath = Join-Path $WebSrc "app\layout.tsx"
$CssPath = Join-Path $WebSrc "app\globals.css"

foreach ($Path in @($WebSrc, $Components, $LayoutPath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$ActionsPath = Join-Path $Components "website-actions.tsx"
$Actions = @'
"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";

type ActionKind = "create" | "customize" | "filter" | "export" | "import" | "open" | "generic";

type ActionRequest = {
  kind: ActionKind;
  label: string;
};

const interceptedLabels = new Set([
  "Customize",
  "+ Create",
  "Create",
  "Import",
  "Filters",
  "Export",
  "Open",
  "View all",
  "Last 30 days",
  "Open work queue",
  "New transfer",
  "New bill",
  "New invoice",
  "New order",
  "Adjust inventory",
  "New payroll run",
  "Run reconciliation",
  "Export calendar",
  "+ Create obligation",
  "View evidence",
  "Open case",
]);

function classify(label: string): ActionKind {
  const value = label.toLowerCase();
  if (value.includes("customize")) return "customize";
  if (value.includes("filter") || value.includes("last 30")) return "filter";
  if (value.includes("export") || value.includes("evidence")) return "export";
  if (value.includes("import")) return "import";
  if (value === "open" || value.includes("view all") || value.includes("open work")) return "open";
  if (value.includes("create") || value.includes("new ") || value.includes("adjust") || value.includes("run reconciliation")) return "create";
  return "generic";
}

function titleFromPath(pathname: string) {
  const segment = pathname.split("/").filter(Boolean).at(-1) ?? "dashboard";
  return segment.replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function WebsiteActions() {
  const pathname = usePathname();
  const moduleName = useMemo(() => titleFromPath(pathname), [pathname]);
  const [request, setRequest] = useState<ActionRequest | null>(null);
  const [notice, setNotice] = useState("");
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [view, setView] = useState("Executive overview");
  const [range, setRange] = useState("Last 30 days");

  useEffect(() => {
    function handleClick(event: MouseEvent) {
      const target = event.target as HTMLElement | null;
      const button = target?.closest("button") as HTMLButtonElement | null;
      if (!button || button.disabled) return;
      if (button.closest(".ai-window") || button.classList.contains("ai-launcher")) return;
      if (button.type === "submit") return;
      if (button.dataset.flowforgeAction === "ignore") return;

      const label = (button.textContent ?? "").replace(/\s+/g, " ").trim();
      if (!interceptedLabels.has(label)) return;

      event.preventDefault();
      setRequest({ kind: classify(label), label });
    }

    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  function close() {
    setRequest(null);
    setName("");
    setAmount("");
  }

  function complete(message: string) {
    setNotice(message);
    close();
    window.setTimeout(() => setNotice(""), 3500);
  }

  return (
    <>
      {notice && <div className="action-toast" role="status">✓ {notice}</div>}
      {request && (
        <div className="action-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}>
          <section className="action-dialog" role="dialog" aria-modal="true" aria-label={`${request.label} ${moduleName}`}>
            <div className="action-dialog-head">
              <div><small>{moduleName}</small><h2>{request.label}</h2></div>
              <button type="button" className="iconbtn" onClick={close} aria-label="Close">×</button>
            </div>

            {request.kind === "customize" && (
              <div className="action-dialog-body">
                <label className="action-label">Dashboard view<select value={view} onChange={(event) => setView(event.target.value)}><option>Executive overview</option><option>Finance focus</option><option>Operations focus</option><option>My work</option></select></label>
                <label className="action-check"><input type="checkbox" defaultChecked /> Show cash-flow outlook</label>
                <label className="action-check"><input type="checkbox" defaultChecked /> Show priority work</label>
                <label className="action-check"><input type="checkbox" defaultChecked /> Show recent activity</label>
                <label className="action-check"><input type="checkbox" /> Compact metric cards</label>
                <div className="action-dialog-actions"><button type="button" className="btn" onClick={close}>Cancel</button><button type="button" className="btn primary" onClick={() => complete(`Dashboard saved as ${view}`)}>Save layout</button></div>
              </div>
            )}

            {request.kind === "create" && (
              <div className="action-dialog-body">
                <p className="action-help">Create a local demonstration record in {moduleName}. Production submission remains disabled until the corresponding API workflow is connected.</p>
                <label className="action-label">Title or reference<input value={name} onChange={(event) => setName(event.target.value)} placeholder={`${moduleName} record`} autoFocus /></label>
                <label className="action-label">Amount or quantity<input value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="Optional" /></label>
                <label className="action-label">Notes<textarea placeholder="Add context, owner, or supporting details" /></label>
                <div className="action-dialog-actions"><button type="button" className="btn" onClick={close}>Cancel</button><button type="button" className="btn primary" disabled={!name.trim()} onClick={() => complete(`${name} added to the ${moduleName} demo workspace`)}>Create demo record</button></div>
              </div>
            )}

            {request.kind === "filter" && (
              <div className="action-dialog-body">
                <label className="action-label">Date range<select value={range} onChange={(event) => setRange(event.target.value)}><option>Today</option><option>Last 7 days</option><option>Last 30 days</option><option>This quarter</option><option>This year</option></select></label>
                <label className="action-label">Status<select><option>All statuses</option><option>Needs attention</option><option>Pending</option><option>Completed</option></select></label>
                <div className="action-dialog-actions"><button type="button" className="btn" onClick={() => complete("Filters cleared")}>Clear</button><button type="button" className="btn primary" onClick={() => complete(`${range} filter applied`)}>Apply filters</button></div>
              </div>
            )}

            {request.kind === "export" && (
              <div className="action-dialog-body">
                <p className="action-help">Prepare the currently visible {moduleName} demonstration data for export.</p>
                <label className="action-label">Format<select><option>CSV</option><option>Microsoft Excel</option><option>PDF</option><option>Audit package</option></select></label>
                <label className="action-check"><input type="checkbox" defaultChecked /> Include active filters</label>
                <div className="action-dialog-actions"><button type="button" className="btn" onClick={close}>Cancel</button><button type="button" className="btn primary" onClick={() => complete(`${moduleName} export prepared in demo mode`)}>Prepare export</button></div>
              </div>
            )}

            {request.kind === "import" && (
              <div className="action-dialog-body">
                <p className="action-help">Choose a local file for validation. No file is uploaded to an external service in demo mode.</p>
                <label className="action-drop"><input type="file" />Select CSV, Excel, PDF, or image</label>
                <div className="action-dialog-actions"><button type="button" className="btn" onClick={close}>Cancel</button><button type="button" className="btn primary" onClick={() => complete(`${moduleName} import staged for validation`)}>Stage import</button></div>
              </div>
            )}

            {(request.kind === "open" || request.kind === "generic") && (
              <div className="action-dialog-body">
                <p className="action-help">The {request.label.toLowerCase()} workspace is available in demonstration mode. Live records will appear after the module API is connected.</p>
                <div className="action-summary"><strong>{moduleName}</strong><span>Local demonstration data</span><span>Read-only production boundary</span></div>
                <div className="action-dialog-actions"><button type="button" className="btn primary" onClick={() => complete(`${moduleName} workspace opened`)}>Continue</button></div>
              </div>
            )}
          </section>
        </div>
      )}
    </>
  );
}
'@

[System.IO.File]::WriteAllText($ActionsPath, $Actions, [System.Text.UTF8Encoding]::new($false))

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Project Python was not found: $Python"
}

$env:FLOWFORGE_LAYOUT_PATH = $LayoutPath
@'
import os
from pathlib import Path

path = Path(os.environ["FLOWFORGE_LAYOUT_PATH"])
text = path.read_text(encoding="utf-8")

import_line = 'import { WebsiteActions } from "@/components/website-actions";'
compact_import = 'import {WebsiteActions} from "@/components/website-actions";'

if import_line not in text and compact_import not in text:
    lines = text.splitlines()
    import_indexes = [
        index
        for index, line in enumerate(lines)
        if line.startswith("import ")
    ]
    if not import_indexes:
        raise RuntimeError("No import block was found in layout.tsx")
    lines.insert(import_indexes[-1] + 1, import_line)
    text = "\n".join(lines)

if "<WebsiteActions" not in text:
    if "</body>" not in text:
        raise RuntimeError("Closing body tag was not found in layout.tsx")
    text = text.replace("</body>", "<WebsiteActions />\n</body>", 1)

path.write_text(text.rstrip() + "\n", encoding="utf-8")
print("PATCHED: layout.tsx")
'@ | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Could not integrate WebsiteActions into layout.tsx."
}

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.action-backdrop') {
$Css += @'

.action-backdrop{position:fixed;inset:0;z-index:80;background:#10182b80;display:grid;place-items:center;padding:18px;backdrop-filter:blur(3px)}
.action-dialog{width:min(540px,100%);max-height:calc(100vh - 40px);overflow:auto;background:white;border:1px solid var(--line);border-radius:16px;box-shadow:0 28px 80px #10182b4d}
.action-dialog-head{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--line)}
.action-dialog-head small{color:var(--primary);text-transform:uppercase;letter-spacing:.11em;font-weight:800}.action-dialog-head h2{margin:4px 0 0;font-size:21px}
.action-dialog-body{padding:20px}.action-help{color:var(--muted);font-size:12px;line-height:1.55;margin-top:0}
.action-label{display:grid;gap:7px;margin:14px 0;color:var(--text);font-size:12px;font-weight:750}.action-label input,.action-label select,.action-label textarea{border:1px solid var(--line);border-radius:9px;padding:10px 11px;background:white;color:var(--text);outline:none}.action-label textarea{min-height:84px;resize:vertical}
.action-check{display:flex;gap:9px;align-items:center;padding:8px 0;font-size:12px;color:var(--text)}.action-check input{accent-color:var(--primary)}
.action-dialog-actions{display:flex;justify-content:flex-end;gap:9px;margin-top:20px}.action-dialog-actions .btn:disabled{opacity:.45;cursor:not-allowed}
.action-toast{position:fixed;right:22px;top:82px;z-index:90;background:#133e32;color:white;padding:12px 16px;border-radius:10px;box-shadow:0 12px 36px #133e3240;font-size:12px;font-weight:750}
.action-drop{display:grid;place-items:center;text-align:center;border:2px dashed #cfd7ea;background:#f8faff;border-radius:12px;padding:28px;color:var(--primary);font-size:12px;font-weight:750;cursor:pointer}.action-drop input{max-width:100%}
.action-summary{display:grid;gap:8px;border:1px solid var(--line);background:#f8f9fc;padding:14px;border-radius:10px;font-size:12px}.action-summary span{color:var(--muted)}
@media(max-width:680px){.action-backdrop{align-items:end;padding:7px}.action-dialog{border-radius:16px 16px 10px 10px}.action-toast{left:14px;right:14px;top:76px}}
'@
}
[System.IO.File]::WriteAllText($CssPath, $Css, [System.Text.UTF8Encoding]::new($false))

Push-Location (Join-Path $Root "web")
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Website action TypeScript validation failed." }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Website action unit tests failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Website action production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE WEBSITE ACTIONS PASSED" -ForegroundColor Green
