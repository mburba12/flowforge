"use client";

import { useMemo, useState } from "react";

type TaxRecord = {
  id: string;
  jurisdiction: string;
  taxType: string;
  period: string;
  dueDate: string;
  amount: number;
  status: "Due soon" | "Scheduled" | "Filed" | "Review" | "Overdue";
  owner: string;
};

const initialRecords: TaxRecord[] = [
  { id: "TAX-1042", jurisdiction: "United States Â- Federal", taxType: "Form 941 payroll tax", period: "Q4 2026", dueDate: "Jan 31, 2027", amount: 68420, status: "Scheduled", owner: "Payroll" },
  { id: "TAX-1041", jurisdiction: "Michigan", taxType: "Sales and use tax", period: "November 2026", dueDate: "Dec 20, 2026", amount: 18470, status: "Due soon", owner: "Tax" },
  { id: "TAX-1040", jurisdiction: "Michigan", taxType: "Withholding tax", period: "November 2026", dueDate: "Dec 20, 2026", amount: 31980, status: "Review", owner: "Payroll" },
  { id: "TAX-1039", jurisdiction: "Genesee County, MI", taxType: "Personal property tax", period: "2026 annual", dueDate: "Feb 20, 2027", amount: 12640, status: "Scheduled", owner: "Controller" },
  { id: "TAX-1038", jurisdiction: "Ohio", taxType: "Commercial activity tax", period: "Q3 2026", dueDate: "Nov 10, 2026", amount: 7840, status: "Filed", owner: "Tax" },
  { id: "TAX-1037", jurisdiction: "Indiana", taxType: "Sales tax", period: "October 2026", dueDate: "Nov 20, 2026", amount: 4260, status: "Overdue", owner: "Tax" },
];

const notices = [
  { agency: "Michigan Department of Treasury", reference: "MI-NTC-88214", received: "Nov 21, 2026", responseDue: "Dec 12, 2026", issue: "Sales tax payment variance", severity: "High" },
  { agency: "Internal Revenue Service", reference: "CP-21090", received: "Nov 14, 2026", responseDue: "Dec 30, 2026", issue: "Form 941 deposit reconciliation", severity: "Medium" },
  { agency: "Ohio Department of Taxation", reference: "OH-CAT-1594", received: "Oct 28, 2026", responseDue: "Complete", issue: "Registration confirmation", severity: "Low" },
];

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export default function TaxPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All statuses");
  const [activeTab, setActiveTab] = useState<"obligations" | "notices">("obligations");
  const [records, setRecords] = useState(initialRecords);

  const filtered = useMemo(() => records.filter((record) => {
    const text = `${record.id} ${record.jurisdiction} ${record.taxType} ${record.period}`.toLowerCase();
    return text.includes(query.toLowerCase()) && (status === "All statuses" || record.status === status);
  }), [query, records, status]);

  const due = records.filter((record) => record.status === "Due soon" || record.status === "Review" || record.status === "Overdue");
  const dueAmount = due.reduce((sum, record) => sum + record.amount, 0);
  const filed = records.filter((record) => record.status === "Filed").length;

  function markFiled(id: string) {
    setRecords((current) => current.map((record) => record.id === id ? { ...record, status: "Filed" } : record));
  }

  return (
    <>
      <div className="pagehead">
        <div>
          <div className="eyebrow">Finance Â- Tax</div>
          <h1>Tax &amp; compliance</h1>
          <p>Track obligations, filings, notices, jurisdictions, payments, and supporting evidence.</p>
        </div>
        <div className="actions">
          <button className="btn">Export calendar</button>
          <button className="btn primary" onClick={() => alert("New tax obligation workflow opened")}>ï¼‹ Create obligation</button>
        </div>
      </div>

      <div className="metrics">
        <article className="metric"><div className="metriclabel">Due in 30 days</div><div className="metricvalue">{money(dueAmount)}</div><div className="delta warning">{due.length} obligations need attention</div></article>
        <article className="metric"><div className="metriclabel">Open notices</div><div className="metricvalue">2</div><div className="delta danger">1 high-priority response</div></article>
        <article className="metric"><div className="metriclabel">Filed this quarter</div><div className="metricvalue">{18 + filed}</div><div className="delta positive">100% filed on time</div></article>
        <article className="metric"><div className="metriclabel">Active jurisdictions</div><div className="metricvalue">12</div><div className="delta neutral">Federal + 7 states + 4 local</div></article>
      </div>

      <div className="cards" style={{ marginBottom: 18 }}>
        <article className="featurecard"><h3>Next filing</h3><p><strong>Michigan sales and use tax</strong><br />Due December 20, 2026 Â- {money(18470)}</p><span className="status">Due in 26 days</span></article>
        <article className="featurecard"><h3>Payment readiness</h3><p><strong>{money(118850)}</strong> is scheduled or awaiting final review across federal and state obligations.</p><span className="status">Funding confirmed</span></article>
        <article className="featurecard"><h3>Compliance health</h3><p>No missed federal filings. One overdue Indiana sales-tax payment requires resolution.</p><span className="status">92% healthy</span></article>
      </div>

      <div className="toolbar panel">
        <button className={`btn ${activeTab === "obligations" ? "primary" : ""}`} onClick={() => setActiveTab("obligations")}>Obligations</button>
        <button className={`btn ${activeTab === "notices" ? "primary" : ""}`} onClick={() => setActiveTab("notices")}>Notices</button>
        <input className="field" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search tax recordsâ€¦" />
        <select className="field" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option>All statuses</option><option>Due soon</option><option>Scheduled</option><option>Review</option><option>Filed</option><option>Overdue</option>
        </select>
      </div>

      <div style={{ height: 12 }} />

      {activeTab === "obligations" ? (
        <section className="panel">
          <div className="panelhead"><h2>Tax obligations and filings</h2><span className="status">Example data</span></div>
          <div className="tablewrap">
            <table className="data">
              <thead><tr><th>Reference</th><th>Jurisdiction</th><th>Tax type</th><th>Period</th><th>Due date</th><th className="right">Amount</th><th>Status</th><th>Action</th></tr></thead>
              <tbody>{filtered.map((record) => (
                <tr key={record.id}>
                  <td><strong>{record.id}</strong></td><td>{record.jurisdiction}</td><td>{record.taxType}</td><td>{record.period}</td><td>{record.dueDate}</td><td className="right">{money(record.amount)}</td><td><span className="status">{record.status}</span></td><td>{record.status !== "Filed" ? <button className="btn" onClick={() => markFiled(record.id)}>Mark filed</button> : <button className="btn">View evidence</button>}</td>
                </tr>
              ))}</tbody>
            </table>
            {!filtered.length && <div className="empty">No matching tax obligations</div>}
          </div>
        </section>
      ) : (
        <section className="panel">
          <div className="panelhead"><h2>Agency notices</h2><span className="status">3 notices</span></div>
          <div className="tablewrap"><table className="data"><thead><tr><th>Agency</th><th>Reference</th><th>Issue</th><th>Received</th><th>Response due</th><th>Priority</th><th>Action</th></tr></thead><tbody>{notices.map((notice) => <tr key={notice.reference}><td>{notice.agency}</td><td><strong>{notice.reference}</strong></td><td>{notice.issue}</td><td>{notice.received}</td><td>{notice.responseDue}</td><td><span className="status">{notice.severity}</span></td><td><button className="btn">Open case</button></td></tr>)}</tbody></table></div>
        </section>
      )}
    </>
  );
}