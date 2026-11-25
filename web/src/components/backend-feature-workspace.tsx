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
      {selected && <div className="api-request-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}><section className="api-request-drawer"><header><div><small>{selected.tags.join(" / ")}</small><h2>{selected.summary}</h2><code>{selected.method} {selected.path}</code></div><button type="button" className="iconbtn" onClick={() => setSelected(null)}>X</button></header><form onSubmit={execute}><div className="api-request-body">{selected.description && <p>{selected.description}</p>}{selected.parameters.map((parameter) => <label key={`${parameter.location}-${parameter.name}`}><span>{parameter.name} <small>{parameter.location}{parameter.required ? " Â· required" : ""}</small></span><input required={parameter.required} value={values[parameter.name] || ""} onChange={(event) => setValues((current) => ({ ...current, [parameter.name]: event.target.value }))} /></label>)}{!["GET", "DELETE"].includes(selected.method) && <label><span>JSON request body</span><textarea rows={10} value={body} onChange={(event) => setBody(event.target.value)} spellCheck={false} /></label>}<div className="api-safety-note">Requests use the local FlowForge API proxy. Tenant context and authorization remain backend-enforced. Destructive production actions should remain disabled until authentication and approval gates are active.</div>{result && <pre className="api-result">{result}</pre>}</div><footer><button type="button" className="btn" onClick={() => setSelected(null)}>Close</button><button type="submit" className="btn primary" disabled={busy}>{busy ? "Running..." : "Run request"}</button></footer></form></section></div>}
    </main>
  );
}