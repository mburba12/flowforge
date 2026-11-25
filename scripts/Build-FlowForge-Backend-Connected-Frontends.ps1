$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Payroll = Join-Path $Web "src\app\payroll\page.tsx"
$Catalog = Join-Path $Web "src\lib\generated-api-catalog.ts"
$Workspace = Join-Path $Web "src\components\backend-feature-workspace.tsx"
$CoveragePage = Join-Path $Web "src\app\feature-coverage\page.tsx"
$ProxyDirectory = Join-Path $Web "src\app\api\flowforge\[...path]"
$Proxy = Join-Path $ProxyDirectory "route.ts"
$Sidebar = Join-Path $Web "src\components\sidebar.tsx"
$Css = Join-Path $Web "src\app\globals.css"
$Report = Join-Path $Root "var\frontend_api_gap_report.json"

foreach ($Path in @($Python, $Payroll, $Sidebar, $Css)) {
  if (-not (Test-Path -LiteralPath $Path)) { throw "Run from FlowForge project root. Missing: $Path" }
}
New-Item -ItemType Directory -Force -Path (Split-Path $Catalog), (Split-Path $Workspace), (Split-Path $CoveragePage), $ProxyDirectory, (Split-Path $Report) | Out-Null

# Stop the global action controller from hijacking Payroll's direct React controls.
$PayrollText = Get-Content -LiteralPath $Payroll -Raw
$PayrollText = $PayrollText.Replace('<main className="page payroll-page">', '<main className="page payroll-page" data-native-actions="true">')
[IO.File]::WriteAllText($Payroll, $PayrollText, [Text.UTF8Encoding]::new($false))

$env:FLOWFORGE_ROOT = $Root
$env:FLOWFORGE_CATALOG = $Catalog
$env:FLOWFORGE_REPORT = $Report
@'
import json
import os
import re
from pathlib import Path

root = Path(os.environ["FLOWFORGE_ROOT"])
catalog_path = Path(os.environ["FLOWFORGE_CATALOG"])
report_path = Path(os.environ["FLOWFORGE_REPORT"])

from flowforge.main import app

schema = app.openapi()
operations = []
for path, path_item in sorted(schema.get("paths", {}).items()):
    if path in {"/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}:
        continue
    for method, operation in path_item.items():
        if method.lower() not in {"get", "post", "put", "patch", "delete"}:
            continue
        tags = operation.get("tags") or [path.strip("/").split("/")[0] or "general"]
        request_body = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
        parameters = []
        for parameter in operation.get("parameters", []):
            parameters.append({
                "name": parameter.get("name"),
                "location": parameter.get("in"),
                "required": bool(parameter.get("required")),
                "schema": parameter.get("schema", {}),
            })
        operations.append({
            "method": method.upper(),
            "path": path,
            "operationId": operation.get("operationId") or f"{method}_{path}",
            "summary": operation.get("summary") or operation.get("operationId") or path,
            "description": operation.get("description") or "",
            "tags": tags,
            "parameters": parameters,
            "requestSchema": request_body,
        })

# Determine whether the exact API path or operation ID is already referenced by frontend source.
frontend_text = "\n".join(
    p.read_text(encoding="utf-8", errors="ignore")
    for p in (root / "web" / "src").rglob("*")
    if p.suffix in {".ts", ".tsx"} and p != catalog_path
)
for item in operations:
    normalized = re.sub(r"\{[^}]+\}", "", item["path"]).rstrip("/")
    item["frontendReferenced"] = (
        item["path"] in frontend_text
        or (normalized and normalized in frontend_text)
        or item["operationId"] in frontend_text
    )

by_tag = {}
for item in operations:
    for tag in item["tags"]:
        by_tag.setdefault(tag, []).append(item)

report = {
    "totalOperations": len(operations),
    "frontendReferenced": sum(1 for item in operations if item["frontendReferenced"]),
    "missingFrontendReferences": sum(1 for item in operations if not item["frontendReferenced"]),
    "tags": {
        tag: {
            "total": len(items),
            "referenced": sum(1 for item in items if item["frontendReferenced"]),
            "missing": sum(1 for item in items if not item["frontendReferenced"]),
            "operations": items,
        }
        for tag, items in sorted(by_tag.items())
    },
}
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

catalog = "export type ApiParameter = { name: string; location: string; required: boolean; schema: Record<string, unknown> };\n"
catalog += "export type ApiOperation = { method: string; path: string; operationId: string; summary: string; description: string; tags: string[]; parameters: ApiParameter[]; requestSchema: unknown; frontendReferenced: boolean };\n\n"
catalog += "export const apiOperations: ApiOperation[] = " + json.dumps(operations, indent=2) + ";\n"
catalog += "export const apiTags = [...new Set(apiOperations.flatMap((item) => item.tags))].sort();\n"
catalog_path.write_text(catalog, encoding="utf-8")

print(f"TOTAL BACKEND OPERATIONS: {report['totalOperations']}")
print(f"ALREADY REFERENCED BY FRONTEND: {report['frontendReferenced']}")
print(f"MISSING FRONTEND REFERENCES: {report['missingFrontendReferences']}")
print(f"REPORT: {report_path}")
'@ | & $Python -
if ($LASTEXITCODE -ne 0) { throw "Backend/frontend coverage generation failed." }

$WorkspaceText = @'
"use client";

import { FormEvent, useMemo, useState } from "react";
import { apiOperations, apiTags, type ApiOperation } from "@/lib/generated-api-catalog";

function concretePath(operation: ApiOperation, values: Record<string, string>) {
  let path = operation.path;
  operation.parameters.filter((parameter) => parameter.location === "path").forEach((parameter) => {
    path = path.replace(`{${parameter.name}}`, encodeURIComponent(values[parameter.name] || ""));
  });
  const query = operation.parameters.filter((parameter) => parameter.location === "query" && values[parameter.name]).map((parameter) => `${encodeURIComponent(parameter.name)}=${encodeURIComponent(values[parameter.name])}`).join("&");
  return query ? `${path}?${query}` : path;
}

export function BackendFeatureWorkspace() {
  const [tag, setTag] = useState(apiTags[0] ?? "");
  const [showMissingOnly, setShowMissingOnly] = useState(true);
  const [selected, setSelected] = useState<ApiOperation | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [body, setBody] = useState("{}");
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);

  const visible = useMemo(() => apiOperations.filter((operation) => operation.tags.includes(tag) && (!showMissingOnly || !operation.frontendReferenced)), [tag, showMissingOnly]);
  const missing = apiOperations.filter((operation) => !operation.frontendReferenced).length;

  async function execute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    setBusy(true);
    setResult("");
    try {
      const target = `/api/flowforge${concretePath(selected, values)}`;
      const response = await fetch(target, {
        method: selected.method,
        headers: selected.method === "GET" || selected.method === "DELETE" ? undefined : { "Content-Type": "application/json" },
        body: selected.method === "GET" || selected.method === "DELETE" ? undefined : body,
      });
      const text = await response.text();
      let formatted = text;
      try { formatted = JSON.stringify(JSON.parse(text), null, 2); } catch { /* retain text */ }
      setResult(`${response.status} ${response.statusText}\n${formatted}`);
    } catch (reason) {
      setResult(reason instanceof Error ? reason.message : "Request failed");
    } finally { setBusy(false); }
  }

  return (
    <main className="page api-coverage-page" data-native-actions="true">
      <header className="pagehead"><div><small>PLATFORM ADMINISTRATION</small><h1>Backend feature coverage</h1><p>Generated from the current FastAPI OpenAPI contract. Every unrepresented backend operation receives an executable frontend here.</p></div></header>
      <section className="api-coverage-summary"><article><span>Backend operations</span><strong>{apiOperations.length}</strong></article><article><span>Frontend references</span><strong>{apiOperations.length - missing}</strong></article><article><span>Generated workspaces</span><strong>{missing}</strong></article><article><span>API groups</span><strong>{apiTags.length}</strong></article></section>
      <div className="api-coverage-layout">
        <aside className="panel api-tag-list"><div className="api-tag-head"><strong>Feature groups</strong><label><input type="checkbox" checked={showMissingOnly} onChange={(event) => setShowMissingOnly(event.target.checked)} /> Missing only</label></div>{apiTags.map((item) => { const count = apiOperations.filter((operation) => operation.tags.includes(item) && !operation.frontendReferenced).length; return <button type="button" className={item === tag ? "active" : ""} key={item} onClick={() => setTag(item)}><span>{item}</span><b>{count}</b></button>; })}</aside>
        <section className="panel api-operation-list"><div className="panelhead"><div><h2>{tag}</h2><p>{visible.length} operations shown</p></div></div>{visible.length ? visible.map((operation) => <button type="button" className="api-operation" key={`${operation.method}-${operation.path}`} onClick={() => { setSelected(operation); setValues({}); setBody("{}"); setResult(""); }}><span className={`api-method ${operation.method.toLowerCase()}`}>{operation.method}</span><div><strong>{operation.summary}</strong><code>{operation.path}</code></div><span className={`api-coverage-state ${operation.frontendReferenced ? "covered" : "generated"}`}>{operation.frontendReferenced ? "Existing UI" : "Generated UI"}</span></button>) : <div className="empty">No matching operations</div>}</section>
      </div>
      {selected && <div className="api-request-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}><section className="api-request-drawer"><header><div><small>{selected.tags.join(" / ")}</small><h2>{selected.summary}</h2><code>{selected.method} {selected.path}</code></div><button type="button" className="iconbtn" onClick={() => setSelected(null)}>X</button></header><form onSubmit={execute}><div className="api-request-body">{selected.description && <p>{selected.description}</p>}{selected.parameters.map((parameter) => <label key={`${parameter.location}-${parameter.name}`}><span>{parameter.name} <small>{parameter.location}{parameter.required ? " · required" : ""}</small></span><input required={parameter.required} value={values[parameter.name] || ""} onChange={(event) => setValues((current) => ({ ...current, [parameter.name]: event.target.value }))} /></label>)}{!["GET", "DELETE"].includes(selected.method) && <label><span>JSON request body</span><textarea rows={10} value={body} onChange={(event) => setBody(event.target.value)} spellCheck={false} /></label>}<div className="api-safety-note">Requests use the local FlowForge API proxy. Tenant context and authorization remain backend-enforced. Destructive production actions should remain disabled until authentication and approval gates are active.</div>{result && <pre className="api-result">{result}</pre>}</div><footer><button type="button" className="btn" onClick={() => setSelected(null)}>Close</button><button type="submit" className="btn primary" disabled={busy}>{busy ? "Running..." : "Run request"}</button></footer></form></section></div>}
    </main>
  );
}
'@
[IO.File]::WriteAllText($Workspace, $WorkspaceText, [Text.UTF8Encoding]::new($false))
$CoveragePageText = @'
import { BackendFeatureWorkspace } from "@/components/backend-feature-workspace";

export default function FeatureCoveragePage() {
  return <BackendFeatureWorkspace />;
}
'@
[IO.File]::WriteAllText($CoveragePage, $CoveragePageText, [Text.UTF8Encoding]::new($false))

$ProxyText = @'
import { NextRequest, NextResponse } from "next/server";

const backend = process.env.FLOWFORGE_API_URL || "http://127.0.0.1:8000";

async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = new URL(`${backend}/${path.join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.append(key, value));
  const headers = new Headers();
  const authorization = request.headers.get("authorization");
  if (authorization) headers.set("authorization", authorization);
  const tenant = request.headers.get("x-tenant-id");
  if (tenant) headers.set("x-tenant-id", tenant);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();
  const response = await fetch(target, { method: request.method, headers, body, cache: "no-store" });
  return new NextResponse(await response.text(), { status: response.status, headers: { "content-type": response.headers.get("content-type") || "text/plain" } });
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
'@
[IO.File]::WriteAllText($Proxy, $ProxyText, [Text.UTF8Encoding]::new($false))

# Add one internal platform navigation entry if absent.
$SidebarText = Get-Content -LiteralPath $Sidebar -Raw
if ($SidebarText -notmatch 'feature-coverage') {
  $SidebarText = $SidebarText.Replace('{label:"Settings",href:"/settings",icon:"settings"}', '{label:"Settings",href:"/settings",icon:"settings"},{label:"Feature coverage",href:"/feature-coverage",icon:"reports"}')
  $SidebarText = $SidebarText.Replace('{ label: "Settings", href: "/settings", icon: "settings" }', '{ label: "Settings", href: "/settings", icon: "settings" }, { label: "Feature coverage", href: "/feature-coverage", icon: "reports" }')
}
[IO.File]::WriteAllText($Sidebar, $SidebarText, [Text.UTF8Encoding]::new($false))

$Styles = Get-Content -LiteralPath $Css -Raw
if ($Styles -notmatch '\.api-coverage-layout') {
$Styles += @'

.api-coverage-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}.api-coverage-summary article{background:white;border:1px solid var(--line);border-radius:14px;padding:16px}.api-coverage-summary span,.api-coverage-summary strong{display:block}.api-coverage-summary span{font-size:9px;color:var(--muted);font-weight:750}.api-coverage-summary strong{font-size:23px;margin-top:7px}.api-coverage-layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:16px}.api-tag-list{padding:8px}.api-tag-head{display:flex;justify-content:space-between;padding:10px}.api-tag-head label{font-size:9px}.api-tag-list>button{width:100%;display:flex;justify-content:space-between;border:0;background:white;padding:10px;border-radius:8px;text-align:left;cursor:pointer}.api-tag-list>button.active{background:#eef2ff;color:#3157d5}.api-tag-list b{font-size:9px}.api-operation-list .panelhead{padding:18px;border-bottom:1px solid var(--line)}.api-operation{width:100%;display:grid;grid-template-columns:58px 1fr auto;gap:12px;align-items:center;border:0;border-bottom:1px solid #eef0f5;background:white;padding:13px 18px;text-align:left;cursor:pointer}.api-operation:hover{background:#f7f8fc}.api-operation strong,.api-operation code{display:block}.api-operation strong{font-size:11px}.api-operation code{font-size:9px;color:var(--muted);margin-top:4px}.api-method{border-radius:6px;padding:5px;text-align:center;font-size:9px;font-weight:900;background:#edf0f7}.api-method.get{background:#e8f7ef;color:#197346}.api-method.post{background:#eef2ff;color:#3157d5}.api-method.delete{background:#fff0f2;color:#b42336}.api-coverage-state{font-size:8px;font-weight:800}.api-coverage-state.generated{color:#a66a00}.api-coverage-state.covered{color:#197346}.api-request-backdrop{position:fixed;inset:0;background:#17203366;z-index:170;display:flex;justify-content:flex-end}.api-request-drawer{width:min(760px,96vw);height:100%;overflow:auto;background:white}.api-request-drawer>header{display:flex;justify-content:space-between;padding:20px;border-bottom:1px solid var(--line)}.api-request-drawer h2{margin:5px 0}.api-request-drawer header small{color:var(--primary);font-size:8px;font-weight:850}.api-request-drawer header code{font-size:10px}.api-request-body{padding:20px;display:grid;gap:14px}.api-request-body label{display:grid;gap:6px}.api-request-body label>span{font-size:10px;font-weight:750}.api-request-body label small{color:var(--muted)}.api-request-body input,.api-request-body textarea{border:1px solid var(--line);border-radius:8px;padding:10px;font:inherit}.api-request-drawer footer{display:flex;justify-content:flex-end;gap:8px;padding:16px 20px;border-top:1px solid var(--line)}.api-safety-note{background:#fff8e8;color:#80530a;padding:11px;border-radius:8px;font-size:9px;line-height:1.55}.api-result{white-space:pre-wrap;overflow:auto;background:#111827;color:#dbe5f5;border-radius:9px;padding:14px;font-size:10px;max-height:300px}@media(max-width:850px){.api-coverage-summary{grid-template-columns:1fr 1fr}.api-coverage-layout{grid-template-columns:1fr}.api-tag-list{max-height:240px;overflow:auto}}@media(max-width:520px){.api-coverage-summary{grid-template-columns:1fr}.api-operation{grid-template-columns:52px 1fr}.api-coverage-state{display:none}}
'@
}
[IO.File]::WriteAllText($Css, $Styles, [Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
  npm run typecheck
  if ($LASTEXITCODE -ne 0) { throw "Backend feature frontend TypeScript validation failed." }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "Backend feature frontend production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE BACKEND-CONNECTED FRONTENDS PASSED" -ForegroundColor Green
Write-Host "Coverage report: $Report"
