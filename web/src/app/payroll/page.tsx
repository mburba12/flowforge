"use client";

import { FormEvent, useMemo, useState } from "react";

type Run = { id: string; period: string; payDate: string; employees: number; gross: number; taxes: number; net: number; status: string; exceptions: number };
type Connection = { provider: string; state: "Not connected" | "Learning" | "Validated"; lastSync?: string; coverage?: number };

const initialRuns: Run[] = [
  { id: "PR-2026-24", period: "Nov 9 - Nov 22", payDate: "Nov 27, 2026", employees: 148, gross: 486240, taxes: 104870, net: 326510, status: "Needs approval", exceptions: 3 },
  { id: "PR-2026-23", period: "Oct 26 - Nov 8", payDate: "Nov 13, 2026", employees: 146, gross: 472810, taxes: 101320, net: 318940, status: "Completed", exceptions: 0 },
  { id: "PR-2026-22", period: "Oct 12 - Oct 25", payDate: "Oct 30, 2026", employees: 145, gross: 468420, taxes: 100540, net: 315790, status: "Completed", exceptions: 0 },
];

const providers = ["ADP Workforce Now", "Paychex Flex", "Gusto", "QuickBooks Payroll", "UKG Pro", "Workday Payroll", "Paylocity", "Other payroll system"];
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export default function PayrollPage() {
  const [runs, setRuns] = useState(initialRuns);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Run | null>(null);
  const [dialog, setDialog] = useState<"new" | "connect" | "connection" | null>(null);
  const [connection, setConnection] = useState<Connection>({ provider: "", state: "Not connected" });
  const [provider, setProvider] = useState(providers[0]);
  const [lookback, setLookback] = useState("24");
  const [notice, setNotice] = useState("");

  const filtered = useMemo(() => runs.filter((run) => `${run.id} ${run.period} ${run.status}`.toLowerCase().includes(query.toLowerCase())), [runs, query]);
  const latest = runs[0];

  function notify(message: string) { setNotice(message); window.setTimeout(() => setNotice(""), 3200); }
  function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setConnection({ provider, state: "Learning", lastSync: "Just now", coverage: Number(lookback) });
    setDialog(null);
    notify(`${provider} connected in read-only learning mode`);
  }
  function createRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next: Run = { id: `PR-2026-${25 + runs.length}`, period: "Nov 23 - Dec 6", payDate: "Dec 11, 2026", employees: 148, gross: 0, taxes: 0, net: 0, status: "Draft", exceptions: 0 };
    setRuns((current) => [next, ...current]);
    setDialog(null);
    notify(`${next.id} created as a draft`);
  }

  return (
    <main className="page payroll-page" data-native-actions="true">
      <header className="pagehead"><div><small>PEOPLE</small><h1>Payroll</h1><p>Prepare, validate, approve, synchronize, and reconcile payroll without enabling money movement prematurely.</p></div><div className="page-actions"><button type="button" className="btn" onClick={() => setDialog("connect")}>{connection.state === "Not connected" ? "Connect payroll system" : "Manage connection"}</button><button type="button" className="btn primary" onClick={() => setDialog("new")}>New payroll run</button></div></header>

      <section className="payroll-connection-banner">
        <div className={`payroll-provider-mark ${connection.state === "Not connected" ? "offline" : ""}`}>PS</div>
        <div><small>PAYROLL SYSTEM CONNECTION</small><h2>{connection.state === "Not connected" ? "Connect your current payroll provider" : connection.provider}</h2><p>{connection.state === "Not connected" ? "FlowForge can securely import payroll history, learn your earnings, deductions, taxes, approvals, and reconciliation patterns, then help you migrate when the results are validated." : `Read-only learning is active. ${connection.coverage} months of history selected; production submission and money movement remain disabled.`}</p></div>
        <div className="payroll-connection-actions"><span className={`payroll-connection-status ${connection.state.toLowerCase().replace(" ", "-")}`}>{connection.state}</span><button type="button" className="btn" onClick={() => setDialog(connection.state === "Not connected" ? "connect" : "connection")}>{connection.state === "Not connected" ? "Connect account" : "View learning status"}</button></div>
      </section>

      <section className="payroll-summary-grid">
        <article className="payroll-summary-card">
          <span>Current gross payroll</span>
          <strong>{money.format(latest.gross)}</strong>
          <small>{latest.period}</small>
        </article>
        <article className="payroll-summary-card">
          <span>Net payroll</span>
          <strong>{money.format(latest.net)}</strong>
          <small>{latest.employees} workers</small>
        </article>
        <article className="payroll-summary-card">
          <span>Payroll taxes</span>
          <strong>{money.format(latest.taxes)}</strong>
          <small>Employee and employer</small>
        </article>
        <article className="payroll-summary-card">
          <span>Open exceptions</span>
          <strong>{latest.exceptions}</strong>
          <small>Review before approval</small>
        </article>
      </section>

      <div className="payroll-grid">
        <section className="panel payroll-runs"><div className="panelhead"><div><h2>Payroll runs</h2><p>Draft, validate, approve, and reconcile each payroll cycle.</p></div><input className="field" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search payroll runs" /></div><div className="tablewrap"><table className="data"><thead><tr><th>Run</th><th>Pay period</th><th>Pay date</th><th className="right">Employees</th><th className="right">Gross</th><th className="right">Net</th><th>Status</th></tr></thead><tbody>{filtered.map((run) => <tr key={run.id} className="clickable-row" role="button" tabIndex={0} onClick={() => setSelected(run)} onKeyDown={(event) => { if (event.key === "Enter") setSelected(run); }}><td><strong>{run.id}</strong></td><td>{run.period}</td><td>{run.payDate}</td><td className="right">{run.employees}</td><td className="right">{money.format(run.gross)}</td><td className="right">{money.format(run.net)}</td><td><span className="status">{run.status}</span></td></tr>)}</tbody></table></div></section>
        <aside className="panel payroll-readiness"><div className="panelhead"><div><h2>Run readiness</h2><p>{latest.id}</p></div></div><div className="payroll-checklist"><div className="complete"><span>1</span><div><strong>Worker and time data</strong><small>148 workers included</small></div></div><div className="complete"><span>2</span><div><strong>Earnings and deductions</strong><small>Gross-to-net inputs loaded</small></div></div><div className="warning"><span>3</span><div><strong>Exception review</strong><small>3 issues require resolution</small></div></div><div><span>4</span><div><strong>Approval</strong><small>Creator/approver separation required</small></div></div><div><span>5</span><div><strong>Provider submission</strong><small>Disabled in local mode</small></div></div><div><span>6</span><div><strong>Bank and GL reconciliation</strong><small>Runs after provider confirmation</small></div></div></div><button type="button" className="btn full" onClick={() => setSelected(latest)}>Review payroll run</button></aside>
      </div>

      <section className="panel payroll-learning"><div className="panelhead"><div><small>MIGRATION PATH</small><h2>Learn before replacing your existing payroll system</h2><p>FlowForge uses a controlled, read-only migration process. No payroll is submitted during learning.</p></div></div><div className="payroll-learning-steps"><article className={connection.state !== "Not connected" ? "active" : ""}><span>1</span><h3>Connect read-only</h3><p>Authorize historical payroll, worker, earning, deduction, tax, and journal data.</p></article><article className={connection.state === "Learning" ? "active" : ""}><span>2</span><h3>Learn and map</h3><p>Map provider codes to FlowForge and identify recurring payroll rules and exceptions.</p></article><article><span>3</span><h3>Parallel validation</h3><p>Calculate comparison runs and reconcile every material variance with the provider.</p></article><article><span>4</span><h3>Controlled cutover</h3><p>Replace the provider only after approval, employee validation, tax validation, and rollback testing.</p></article></div></section>

      {notice && <div className="payroll-toast" role="status">{notice}</div>}

      {dialog && <div className="payroll-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialog(null); }}><section className="payroll-dialog" role="dialog" aria-modal="true"><header><div><small>PAYROLL</small><h2>{dialog === "new" ? "Create payroll run" : dialog === "connect" ? "Connect current payroll system" : "Payroll connection status"}</h2></div><button type="button" className="iconbtn" onClick={() => setDialog(null)}>X</button></header>{dialog === "connect" ? <form onSubmit={connect}><div className="payroll-dialog-body"><label><span>Current payroll provider</span><select value={provider} onChange={(event) => setProvider(event.target.value)}>{providers.map((item) => <option key={item}>{item}</option>)}</select></label><label><span>History to import</span><select value={lookback} onChange={(event) => setLookback(event.target.value)}><option value="12">12 months</option><option value="24">24 months</option><option value="36">36 months</option><option value="60">5 years</option></select></label><div className="payroll-scope"><strong>Read-only learning scope</strong><label><input type="checkbox" defaultChecked /> Payroll registers and pay statements</label><label><input type="checkbox" defaultChecked /> Earnings, deductions, and taxes</label><label><input type="checkbox" defaultChecked /> Employee and contractor history</label><label><input type="checkbox" defaultChecked /> General-ledger and bank reconciliation</label></div><div className="payroll-boundary">Connecting does not authorize FlowForge to submit payroll, debit bank accounts, file taxes, or change records in the provider.</div></div><footer><button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button><button type="submit" className="btn primary">Continue to provider authorization</button></footer></form> : dialog === "new" ? <form onSubmit={createRun}><div className="payroll-dialog-body"><label><span>Payroll group</span><select><option>US biweekly payroll</option><option>US weekly hourly</option><option>Contractors</option></select></label><div className="payroll-form-grid"><label><span>Pay-period start</span><input type="date" required /></label><label><span>Pay-period end</span><input type="date" required /></label></div><label><span>Payment date</span><input type="date" required /></label><div className="payroll-boundary">This creates a draft only. Payment submission requires validation, approval, MFA, and an enabled production provider connection.</div></div><footer><button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button><button type="submit" className="btn primary">Create draft run</button></footer></form> : <><div className="payroll-dialog-body"><div className="payroll-connection-summary"><div><span>Provider</span><strong>{connection.provider}</strong></div><div><span>Connection mode</span><strong>Read-only learning</strong></div><div><span>Last sync</span><strong>{connection.lastSync}</strong></div><div><span>History coverage</span><strong>{connection.coverage} months</strong></div></div><div className="payroll-sync-list"><div><span>Workers and employment history</span><b>Mapped</b></div><div><span>Earnings and deduction codes</span><b>Learning</b></div><div><span>Tax jurisdictions and deposits</span><b>Learning</b></div><div><span>Payroll journals and bank activity</span><b>Queued</b></div></div><div className="payroll-boundary">Provider write-back, direct deposit, tax filing, and production payroll execution remain disabled.</div></div><footer><button type="button" className="btn" onClick={() => setDialog(null)}>Close</button><button type="button" className="btn primary" onClick={() => notify("Read-only synchronization requested")}>Sync now</button></footer></>}</section></div>}

      {selected && <div className="payroll-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}><section className="payroll-drawer"><header><div><small>PAYROLL RUN</small><h2>{selected.id}</h2><p>{selected.period} Ã‚Â· Pay date {selected.payDate}</p></div><button type="button" className="iconbtn" onClick={() => setSelected(null)}>X</button></header><div className="payroll-dialog-body"><div className="payroll-run-summary"><article><span>Workers</span><strong>{selected.employees}</strong></article><article><span>Gross pay</span><strong>{money.format(selected.gross)}</strong></article><article><span>Payroll taxes</span><strong>{money.format(selected.taxes)}</strong></article><article><span>Net pay</span><strong>{money.format(selected.net)}</strong></article></div><h3>Exceptions</h3>{selected.exceptions ? <div className="payroll-exceptions"><div><strong>2 missing time approvals</strong><span>Hourly workforce Ã‚Â· Operations</span><button type="button" className="btn small">Review</button></div><div><strong>1 net-pay variance above threshold</strong><span>Variance is 18.4% from prior cycle</span><button type="button" className="btn small">Review</button></div></div> : <div className="empty">No open exceptions</div>}<div className="payroll-boundary">This run cannot be submitted until all exceptions are resolved and an independent approver authorizes release.</div></div><footer><button type="button" className="btn" onClick={() => setSelected(null)}>Close</button><button type="button" className="btn" onClick={() => notify(`${selected.id} validation started`)}>Validate</button><button type="button" className="btn primary" disabled={selected.exceptions > 0} onClick={() => notify(`${selected.id} sent for approval`)}>Send for approval</button></footer></section></div>}
    </main>
  );
}
