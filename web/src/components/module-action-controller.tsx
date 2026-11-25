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