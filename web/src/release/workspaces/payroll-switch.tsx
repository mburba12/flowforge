"use client";

import { useRef, useState } from "react";

import { errorText, get, money, post, upload } from "../client";
import { useLoad, usePermissions } from "../hooks";
import { Card, Notice, Table } from "../ui";

type Provider = { code: string; name: string; export_steps: string; direct_connection: boolean };
type Catalog = { providers: Provider[]; template_columns: string[]; gusto_configured: boolean };
type PreviewRow = {
  row: number;
  external_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  hire_date: string | null;
  status: string;
  pay_type: string | null;
  pay_rate: string | null;
  pay_frequency: string;
  state: string | null;
  ytd: Record<string, string>;
  warnings: string[];
};
type Preview = { employees: PreviewRow[]; count: number; errors: string[]; columns_recognised: Record<string, string> };
type Migration = {
  id: string;
  provider_name: string;
  method: string;
  status: string;
  company_name: string | null;
  filename: string | null;
  summary: Record<string, number>;
  errors: string[];
  created_at: string | null;
};

const STEPS = ["Choose your provider", "Upload your export", "Check and import"];

/** Switch payroll to Krov WorkAgent: bring employees, pay rates and year-to-date totals over. */
export function PayrollSwitch() {
  const { can } = usePermissions();
  const catalog = useLoad(() => get<Catalog>("/api/v1/payroll-migration/providers"), "payroll-providers");
  const history = useLoad(() => get<Migration[]>("/api/v1/payroll-migration/imports"), "payroll-imports");
  const [provider, setProvider] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const chosen = catalog.data?.providers.find((p) => p.code === provider);
  const step = !provider ? 0 : !preview ? 1 : 2;
  const allowed = can("payroll.migrate");

  async function check(selected: File) {
    setBusy("preview");
    setMessage(null);
    const form = new FormData();
    form.append("file", selected);
    form.append("provider", provider);
    try {
      setFile(selected);
      setPreview(await upload<Preview>("/api/v1/payroll-migration/preview", form));
    } catch (error) {
      setPreview(null);
      setMessage({ ok: false, text: errorText(error) });
    } finally {
      setBusy("");
    }
  }

  async function runImport() {
    if (!file) return;
    setBusy("import");
    const form = new FormData();
    form.append("file", file);
    form.append("provider", provider);
    try {
      const m = await upload<Migration>("/api/v1/payroll-migration/file", form);
      setMessage({
        ok: true,
        text: `Done: ${m.summary.employees_created ?? 0} employees added, ${m.summary.employees_updated ?? 0} updated, ${m.summary.pay_rates_set ?? 0} pay rates set, ${m.summary.ytd_balances ?? 0} year-to-date balances carried over. Your next payroll can run in Krov WorkAgent.`,
      });
      setPreview(null);
      setFile(null);
      setProvider("");
      history.reload();
    } catch (error) {
      setMessage({ ok: false, text: errorText(error) });
    } finally {
      setBusy("");
    }
  }

  async function connectGusto() {
    setBusy("gusto");
    try {
      const r = await post<{ authorize_url: string }>("/api/v1/payroll-migration/gusto/start");
      window.location.assign(r.authorize_url);
    } catch (error) {
      setMessage({ ok: false, text: errorText(error) });
      setBusy("");
    }
  }

  function downloadTemplate() {
    const header = (catalog.data?.template_columns ?? []).join(",");
    const sample = "E-001,Jordan,Smith,jordan@example.com,2024-03-01,Active,Employee,Hourly,28.50,Biweekly,TX,Single,0,12400.00,980.00,768.80,179.80,0,0,10471.40";
    const url = URL.createObjectURL(new Blob([`${header}\n${sample}\n`], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "krov-workagent-payroll-import-template.csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 30_000);
  }

  return (
    <div className="rwStack" data-testid="payroll-switch">
      <Card title="Move your payroll to Krov WorkAgent">
        <p className="rwMuted">
          Bring your employees, pay rates, tax settings and this year&apos;s totals over from your current provider. Nothing changes at your old
          provider — cancel it after your first Krov WorkAgent payroll.
        </p>
        <ol className="stepper">
          {STEPS.map((s, i) => (
            <li key={s} className={i < step ? "done" : i === step ? "now" : ""}>
              <span>{i + 1}</span>
              {s}
            </li>
          ))}
        </ol>
        {!allowed ? <Notice kind="info">Switching payroll needs the permission payroll.migrate (owners and managers have it).</Notice> : null}
        {message ? <Notice kind={message.ok ? "ok" : "error"}>{message.text}</Notice> : null}

        {allowed && step === 0 ? (
          <div className="providerGrid" role="radiogroup" aria-label="Current payroll provider">
            {(catalog.data?.providers ?? []).map((p) => (
              <button key={p.code} type="button" role="radio" aria-checked={false} className="providerTile" onClick={() => setProvider(p.code)}>
                {p.name}
              </button>
            ))}
          </div>
        ) : null}

        {allowed && step === 1 && chosen ? (
          <div className="rwStack">
            <div className="rwActions">
              <b>{chosen.name}</b>
              <button type="button" className="linkish" onClick={() => setProvider("")}>
                change
              </button>
            </div>
            {chosen.code === "gusto" ? (
              <div className="choice">
                <b>Connect Gusto directly</b>
                <span className="rwMuted">Sign in to Gusto and Krov WorkAgent copies everything over for you.</span>
                <button type="button" className="rwBtn primary" disabled={!chosen.direct_connection || !!busy} onClick={connectGusto}>
                  {busy === "gusto" ? "Opening Gusto…" : "Sign in to Gusto"}
                </button>
                {!chosen.direct_connection ? (
                  <span className="rwMuted small">The direct Gusto connection isn&apos;t switched on for this server yet — upload a Gusto export below instead.</span>
                ) : null}
              </div>
            ) : null}
            <div className="choice">
              <b>Upload your {chosen.name} export</b>
              <span className="rwMuted">Where to find it: {chosen.export_steps}</span>
              <span className="rwMuted small">
                Combine employees and year-to-date totals in one CSV, or upload the employee list first and the totals report after.{" "}
                <button type="button" className="linkish" onClick={downloadTemplate}>
                  Download the Krov WorkAgent template
                </button>
              </span>
              <input ref={input} type="file" accept=".csv,.txt" hidden data-testid="payroll-file" onChange={(e) => e.target.files?.[0] && void check(e.target.files[0])} />
              <button type="button" className="rwBtn primary" disabled={!!busy} onClick={() => input.current?.click()}>
                {busy === "preview" ? "Reading the file…" : "Choose the CSV file"}
              </button>
            </div>
          </div>
        ) : null}

        {allowed && step === 2 && preview ? (
          <div className="rwStack">
            <p>
              Found <b>{preview.count}</b> employee{preview.count === 1 ? "" : "s"} in <b>{file?.name}</b>.{" "}
              {preview.errors.length ? <span className="warnText">{preview.errors.length} row(s) can&apos;t be imported (listed below).</span> : "Everything looks good."}
            </p>
            <Table
              testId="payroll-preview"
              rows={preview.employees as unknown as Record<string, unknown>[]}
              columns={[
                { key: "name", label: "Employee", render: (r) => `${String(r.first_name)} ${String(r.last_name)}` },
                { key: "hire_date", label: "Hired" },
                { key: "status", label: "Status" },
                {
                  key: "pay",
                  label: "Pay",
                  render: (r) => (r.pay_rate ? (r.pay_type === "hourly" ? `${money(r.pay_rate)}/hr` : `${money(r.pay_rate)}/yr`) : "—"),
                },
                { key: "pay_frequency", label: "Paid" },
                { key: "ytd", label: "YTD gross", align: "right", render: (r) => ((r.ytd as Record<string, string>).gross_pay ? money((r.ytd as Record<string, string>).gross_pay) : "") },
                { key: "warnings", label: "", render: (r) => <span className="rwMuted small">{(r.warnings as string[]).join("; ")}</span> },
              ]}
            />
            {preview.errors.length ? <Notice kind="error">{preview.errors.slice(0, 20).join(" · ")}</Notice> : null}
            <div className="rwActions">
              <button type="button" className="rwBtn primary" disabled={!!busy || preview.count === 0} onClick={runImport} data-testid="payroll-import">
                {busy === "import" ? "Importing…" : `Import ${preview.count} employee${preview.count === 1 ? "" : "s"}`}
              </button>
              <button type="button" className="rwBtn" onClick={() => { setPreview(null); setFile(null); }}>
                Choose another file
              </button>
            </div>
          </div>
        ) : null}
      </Card>

      <Card title="Earlier imports">
        <Table
          rows={(history.data ?? []) as unknown as Record<string, unknown>[]}
          loading={history.loading}
          error={history.error}
          empty="Nothing imported yet."
          columns={[
            { key: "created_at", label: "When", render: (r) => (r.created_at ? new Date(String(r.created_at)).toLocaleString() : "") },
            { key: "provider_name", label: "From" },
            { key: "source", label: "Source", render: (r) => String(r.company_name ?? r.filename ?? "") },
            { key: "status", label: "Status" },
            {
              key: "summary",
              label: "Result",
              render: (r) => {
                const s = r.summary as Record<string, number>;
                return `${s.employees_created ?? 0} added · ${s.employees_updated ?? 0} updated · ${s.ytd_balances ?? 0} YTD`;
              },
            },
          ]}
        />
      </Card>
    </div>
  );
}
