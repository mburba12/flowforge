"use client";

import { FormEvent, useState } from "react";

type Dialog = "customize" | "create" | null;

export function DashboardActions() {
  const [dialog, setDialog] = useState<Dialog>(null);
  const [title, setTitle] = useState("");
  const [module, setModule] = useState("Accounts payable");
  const [view, setView] = useState("Executive overview");
  const [notice, setNotice] = useState("");

  function finish(message: string) {
    setNotice(message);
    setDialog(null);
    window.setTimeout(() => setNotice(""), 3500);
  }

  function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;
    finish(`${title.trim()} created in ${module} demo mode`);
    setTitle("");
  }

  return (
    <>
      <div className="actions dashboard-actions">
        <button type="button" className="btn" onClick={() => setDialog("customize")}>Customize</button>
        <button type="button" className="btn primary" onClick={() => setDialog("create")}>+ Create</button>
      </div>

      {notice && <div className="dashboard-toast" role="status">{notice}</div>}

      {dialog && (
        <div className="dashboard-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialog(null); }}>
          <section className="dashboard-modal" role="dialog" aria-modal="true">
            <header className="dashboard-modal-head">
              <div><small>Dashboard</small><h2>{dialog === "customize" ? "Customize dashboard" : "Create a record"}</h2></div>
              <button type="button" className="iconbtn" onClick={() => setDialog(null)} aria-label="Close">X</button>
            </header>

            {dialog === "customize" ? (
              <div className="dashboard-modal-body">
                <label className="dashboard-field">Dashboard view
                  <select value={view} onChange={(event) => setView(event.target.value)}>
                    <option>Executive overview</option>
                    <option>Finance focus</option>
                    <option>Operations focus</option>
                    <option>My work</option>
                  </select>
                </label>
                <label className="dashboard-check"><input type="checkbox" defaultChecked /> Cash-flow outlook</label>
                <label className="dashboard-check"><input type="checkbox" defaultChecked /> Priority work</label>
                <label className="dashboard-check"><input type="checkbox" defaultChecked /> Recent activity</label>
                <div className="dashboard-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="button" className="btn primary" onClick={() => finish(`${view} layout saved locally`)}>Save layout</button>
                </div>
              </div>
            ) : (
              <form className="dashboard-modal-body" onSubmit={create}>
                <p className="dashboard-help">Creates a local demonstration record. Production writes remain disabled until the module API is connected.</p>
                <label className="dashboard-field">Module
                  <select value={module} onChange={(event) => setModule(event.target.value)}>
                    <option>Accounts payable</option><option>Accounts receivable</option><option>Orders</option><option>Inventory</option><option>Payroll</option><option>Tax</option><option>Work queue</option>
                  </select>
                </label>
                <label className="dashboard-field">Title or reference
                  <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Enter a record name" autoFocus />
                </label>
                <label className="dashboard-field">Notes<textarea placeholder="Optional details" /></label>
                <div className="dashboard-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="submit" className="btn primary" disabled={!title.trim()}>Create demo record</button>
                </div>
              </form>
            )}
          </section>
        </div>
      )}
    </>
  );
}
