"use client";

import { type DragEvent, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { labelOf, modules } from "@/lib/modules";

import { del, errorText, get, openFile, upload } from "./client";
import { useLoad, usePermissions } from "./hooks";
import { Card, Notice, Workspace } from "./ui";

export type StoredFile = {
  id: string;
  section: string;
  record_type: string | null;
  record_id: string | null;
  filename: string;
  content_type: string;
  size_bytes: number;
  note: string | null;
  created_at: string | null;
};

const ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.gif,.webp,.heic,.tif,.tiff,.csv,.txt,.ofx,.qfx,.xml,.json,.xls,.xlsx,.doc,.docx,.eml,.zip";

/** What people usually upload in each section (shown in the drop zone). */
const HINTS: Record<string, string> = {
  ap: "vendor invoices and bills",
  ar: "customer invoices, remittances and checks",
  banking: "bank statements and deposit slips",
  payroll: "pay stubs, payroll reports and tax forms",
  workforce: "offer letters, I-9s, W-4s and contracts",
  tax: "tax notices, returns and payment confirmations",
  orders: "purchase orders and packing slips",
  shipping: "labels, bills of lading and proof of delivery",
  inventory: "count sheets and supplier spec sheets",
  commerce: "quotes, purchase orders and receiving documents",
  finance: "receipts, journals backup and statements",
  crm: "contracts, proposals and signed quotes",
};

function size(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function when(value: string | null): string {
  return value
    ? new Date(value).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "";
}

/** Drop zone + button; uploads every chosen file to `section`. */
export function Uploader(props: {
  section: string;
  recordType?: string;
  recordId?: string;
  onUploaded: () => void;
  compact?: boolean;
}) {
  const { can, loaded } = usePermissions();
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [over, setOver] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null,
  );
  const allowed = loaded && can("documents.upload");

  async function send(files: FileList | File[]) {
    const list = Array.from(files);
    if (!list.length) return;
    setBusy(true);
    setMessage(null);
    const failed: string[] = [];
    for (const file of list) {
      const form = new FormData();
      form.append("file", file);
      form.append("section", props.section);
      if (props.recordType) form.append("record_type", props.recordType);
      if (props.recordId) form.append("record_id", props.recordId);
      try {
        await upload("/api/v1/files", form);
      } catch (error) {
        failed.push(`${file.name}: ${errorText(error)}`);
      }
    }
    setBusy(false);
    if (input.current) input.current.value = "";
    const done = list.length - failed.length;
    setMessage(
      failed.length
        ? { ok: false, text: failed.join(" · ") }
        : { ok: true, text: `Uploaded ${done} file${done === 1 ? "" : "s"}.` },
    );
    if (done) props.onUploaded();
  }

  function drop(event: DragEvent) {
    event.preventDefault();
    setOver(false);
    if (allowed && !busy) void send(event.dataTransfer.files);
  }

  return (
    <div
      className={`dropZone${over ? " over" : ""}${props.compact ? " compact" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        if (allowed) setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={drop}
      data-testid="drop-zone"
    >
      <input
        ref={input}
        type="file"
        multiple
        accept={ACCEPT}
        hidden
        data-testid="upload-input"
        onChange={(e) => e.target.files && void send(e.target.files)}
      />
      <button
        type="button"
        className="rwBtn primary"
        disabled={!allowed || busy}
        onClick={() => input.current?.click()}
        data-testid="upload-button"
      >
        {busy ? "Uploading…" : "Upload files"}
      </button>
      <span className="rwMuted">
        {allowed || !loaded
          ? `or drag files here${HINTS[props.section] ? ` — ${HINTS[props.section]}` : ""}. PDF, images, spreadsheets, documents; up to 20 MB each.`
          : "Your role can view files but not upload them."}
      </span>
      {message ? (
        <Notice kind={message.ok ? "ok" : "error"}>{message.text}</Notice>
      ) : null}
    </div>
  );
}

export function FileTable(props: {
  files: StoredFile[] | null;
  loading: boolean;
  error: string;
  showSection?: boolean;
  onChanged: () => void;
  empty: string;
}) {
  const { can } = usePermissions();
  const [problem, setProblem] = useState("");
  if (props.error) return <Notice kind="error">{props.error}</Notice>;
  if (props.loading && !props.files) return <p className="rwMuted">Loading…</p>;
  if (!props.files?.length) return <p className="rwMuted">{props.empty}</p>;
  return (
    <div className="rwTable" data-testid="file-table">
      {problem ? <Notice kind="error">{problem}</Notice> : null}
      <table>
        <thead>
          <tr>
            <th>File</th>
            {props.showSection ? <th>Section</th> : null}
            <th>Added</th>
            <th className="r">Size</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {props.files.map((f) => {
            const viewable = /pdf|png|jpeg/.test(f.content_type);
            return (
              <tr key={f.id}>
                <td>
                  <b>{f.filename}</b>
                  {f.note ? (
                    <div className="rwMuted small">{f.note}</div>
                  ) : null}
                </td>
                {props.showSection ? <td>{labelOf(f.section)}</td> : null}
                <td>{when(f.created_at)}</td>
                <td className="r">{size(f.size_bytes)}</td>
                <td className="r rowActions">
                  <button
                    type="button"
                    className="rwBtn"
                    onClick={() =>
                      openFile(
                        `/api/v1/files/${f.id}/content`,
                        f.filename,
                        viewable,
                      ).catch((e) => setProblem(errorText(e)))
                    }
                  >
                    {viewable ? "Open" : "Download"}
                  </button>
                  {can("documents.manage") ? (
                    <button
                      type="button"
                      className="rwBtn"
                      aria-label={`Delete ${f.filename}`}
                      onClick={async () => {
                        if (!window.confirm(`Delete ${f.filename}?`)) return;
                        try {
                          await del(`/api/v1/files/${f.id}`);
                          props.onChanged();
                        } catch (e) {
                          setProblem(errorText(e));
                        }
                      }}
                    >
                      Delete
                    </button>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** The files strip shown at the top of every section: count, upload, and the list on demand. */
export function SectionFiles({ section }: { section: string }) {
  const { can, loaded } = usePermissions();
  const readable = loaded && can("documents.read");
  const files = useLoad(
    async () =>
      readable ? get<StoredFile[]>("/api/v1/files", { section }) : [],
    `${section}:${readable}`,
  );
  const [open, setOpen] = useState(false);
  if (
    !section ||
    section === "documents" ||
    section === "dashboard" ||
    !loaded ||
    !readable
  )
    return null;
  const count = files.data?.length ?? 0;
  return (
    <div className="sectionFiles" data-testid="section-files">
      <button
        type="button"
        className="filesButton"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        data-testid="section-files-button"
      >
        📎 Files <span className="pill">{count}</span>
      </button>
      <button
        type="button"
        className="rwBtn primary"
        onClick={() => setOpen(true)}
        data-testid="section-upload"
      >
        Upload
      </button>
      {open && typeof document !== "undefined"
        ? createPortal(
            <>
              <div className="drawerScrim" onClick={() => setOpen(false)} />
              <aside
                className="drawer"
                role="dialog"
                aria-label={`Files in ${labelOf(section)}`}
                data-testid="files-drawer"
              >
                <div className="drawerHead">
                  <h2>Files in {labelOf(section)}</h2>
                  <button
                    type="button"
                    className="rwBtn"
                    onClick={() => setOpen(false)}
                    aria-label="Close files"
                  >
                    Close
                  </button>
                </div>
                <Uploader section={section} onUploaded={files.reload} />
                <FileTable
                  files={files.data}
                  loading={files.loading}
                  error={files.error}
                  onChanged={files.reload}
                  empty="No files here yet."
                />
              </aside>
            </>,
            document.body,
          )
        : null}
    </div>
  );
}

/** Files: everything uploaded anywhere, with a filter by section. */
export function FilesWorkspace() {
  const [section, setSection] = useState("");
  const files = useLoad(
    () =>
      get<StoredFile[]>("/api/v1/files", {
        section: section || undefined,
        limit: 500,
      }),
    `files:${section}`,
  );
  return (
    <Workspace
      title="Files"
      description="Every invoice, receipt, statement and document uploaded anywhere in FlowForge."
      accent="#57d3ff"
    >
      <Card title="Upload">
        <Uploader section="documents" onUploaded={files.reload} />
      </Card>
      <Card
        title="All files"
        aside={
          <select
            aria-label="Show files from"
            value={section}
            onChange={(e) => setSection(e.target.value)}
          >
            <option value="">All sections</option>
            {modules.map(([s]) => (
              <option key={s} value={s}>
                {labelOf(s)}
              </option>
            ))}
          </select>
        }
      >
        <FileTable
          files={files.data}
          loading={files.loading}
          error={files.error}
          onChanged={files.reload}
          showSection
          empty="Nothing uploaded yet. Upload a file above, or from any section."
        />
      </Card>
    </Workspace>
  );
}
