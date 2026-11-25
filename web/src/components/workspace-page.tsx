"use client";

import { FormEvent, useState } from "react";
import { DataTable } from "./data-table";
import { MetricCard } from "./metric-card";
import type { WorkspaceConfig } from "@/lib/types";

type Dialog = "create" | "import" | null;

export function WorkspacePage({ config }: { config: WorkspaceConfig }) {
  const [dialog, setDialog] = useState<Dialog>(null);
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [fileName, setFileName] = useState("");
  const [notice, setNotice] = useState("");

  function finish(message: string) {
    setNotice(message);
    setDialog(null);
    window.setTimeout(() => setNotice(""), 3500);
  }

  function createRecord(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;
    finish(`${title.trim()} created in ${config.title} demo mode`);
    setTitle("");
    setAmount("");
  }

  function stageImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!fileName) return;
    finish(`${fileName} staged for ${config.title} validation`);
    setFileName("");
  }

  return (
    <>
      <div className="pagehead">
        <div>
          <div className="eyebrow">{config.eyebrow}</div>
          <h1>{config.title}</h1>
          <p>{config.description}</p>
        </div>
        <div className="actions">
          <button type="button" className="btn" onClick={() => setDialog("import")}>Import</button>
          <button type="button" className="btn primary" onClick={() => setDialog("create")}>+ {config.primaryAction}</button>
        </div>
      </div>

      {notice && <div className="workspace-toast" role="status">{notice}</div>}

      <div className="metrics">
        {config.metrics.map((metric) => <MetricCard metric={metric} key={metric.label} />)}
      </div>

      <DataTable columns={config.columns} rows={config.rows} />

      {dialog && (
        <div className="workspace-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialog(null); }}>
          <section className="workspace-modal" role="dialog" aria-modal="true" aria-label={dialog === "create" ? config.primaryAction : `Import ${config.title}`}>
            <header className="workspace-modal-head">
              <div><small>{config.eyebrow}</small><h2>{dialog === "create" ? config.primaryAction : `Import ${config.title}`}</h2></div>
              <button type="button" className="iconbtn" onClick={() => setDialog(null)} aria-label="Close">X</button>
            </header>

            {dialog === "create" ? (
              <form className="workspace-modal-body" onSubmit={createRecord}>
                <p className="workspace-help">Create a local demonstration record. Production submission remains disabled until the {config.title} API workflow is connected.</p>
                <label className="workspace-field">Title or reference
                  <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={`New ${config.title.toLowerCase()} record`} autoFocus />
                </label>
                <label className="workspace-field">Amount or quantity
                  <input value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="Optional" />
                </label>
                <label className="workspace-field">Notes<textarea placeholder="Add context, owner, or supporting details" /></label>
                <div className="workspace-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="submit" className="btn primary" disabled={!title.trim()}>Create demo record</button>
                </div>
              </form>
            ) : (
              <form className="workspace-modal-body" onSubmit={stageImport}>
                <p className="workspace-help">Select a local file for validation. No file is sent to an external service in demo mode.</p>
                <label className="workspace-upload">Select CSV, Excel, PDF, or image
                  <input type="file" accept=".csv,.xlsx,.xls,.pdf,.png,.jpg,.jpeg" onChange={(event) => setFileName(event.target.files?.[0]?.name ?? "")} />
                </label>
                {fileName && <div className="workspace-file">Selected: {fileName}</div>}
                <div className="workspace-modal-actions">
                  <button type="button" className="btn" onClick={() => setDialog(null)}>Cancel</button>
                  <button type="submit" className="btn primary" disabled={!fileName}>Stage import</button>
                </div>
              </form>
            )}
          </section>
        </div>
      )}
    </>
  );
}