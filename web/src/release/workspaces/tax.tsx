"use client";

import { useState } from "react";

import { get, post, today, type Row } from "../client";
import { usePostingContext } from "../context";
import { useLoad, useRows } from "../hooks";
import { optionsOf, useGl } from "../refs";
import { ActionButton, Amount, Badge, Card, Form, Grid, Table, Tabs, Workspace, useActionLog } from "../ui";

const TABS = [
  { id: "returns", label: "Returns & remittance" },
  { id: "liabilities", label: "Liabilities" },
  { id: "rules", label: "Jurisdictions & rules" },
  { id: "authorities", label: "Authorities" },
  { id: "calculate", label: "Calculator" },
];

export function TaxWorkspace() {
  const [tab, setTab] = useState("returns");
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const key = String(version);
  const gl = useGl(key);
  const jurisdictions = useRows("jurisdictions", key);
  const authorities = useLoad(() => get<Row[]>("/api/v4b/authorities"), `auth:${key}`);
  const authorityName = (id: unknown) => {
    const a = (authorities.data ?? []).find((x) => x.id === id);
    return a ? `${a.code} ${a.name}` : String(id ?? "");
  };
  const shared = { gl, jurisdictions, authorities, authorityName, version, refresh };
  return (
    <Workspace title="Taxes" description="Jurisdictions and versioned rules, calculation, liabilities from payroll, returns, approval, remittance and reconciliation." accent="#ea580c">
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "returns" ? <Returns {...shared} /> : null}
      {tab === "liabilities" ? <Liabilities {...shared} /> : null}
      {tab === "rules" ? <Rules {...shared} /> : null}
      {tab === "authorities" ? <Authorities {...shared} /> : null}
      {tab === "calculate" ? <Calculator {...shared} /> : null}
    </Workspace>
  );
}

type Shared = {
  gl: ReturnType<typeof useGl>;
  jurisdictions: ReturnType<typeof useRows>;
  authorities: ReturnType<typeof useLoad<Row[]>>;
  authorityName: (id: unknown) => string;
  version: number;
  refresh: () => void;
};

function Rules({ jurisdictions, version, refresh }: Shared) {
  const rules = useRows("tax-rules", String(version));
  const juris = (id: unknown) => String((jurisdictions.data ?? []).find((j) => j.id === id)?.code ?? "");
  return (
    <Grid>
      <Card title="Jurisdictions and rules">
        <Table
          testId="rules-table"
          rows={rules.data}
          loading={rules.loading}
          error={rules.error}
          empty="No tax rules yet."
          columns={[
            { key: "code", label: "Rule" },
            { key: "version", label: "Ver" },
            { key: "jurisdiction_id", label: "Jurisdiction", render: (r) => juris(r.jurisdiction_id) },
            { key: "responsibility", label: "Paid by" },
            { key: "rate", label: "Rate" },
            { key: "effective_from", label: "From" },
            { key: "effective_to", label: "To" },
          ]}
        />
        <Table
          testId="jurisdictions-table"
          rows={jurisdictions.data}
          loading={jurisdictions.loading}
          columns={[
            { key: "code", label: "Code" },
            { key: "name", label: "Jurisdiction" },
            { key: "level", label: "Level" },
            { key: "active", label: "Active", render: (r) => <Badge value={String(r.active)} /> },
          ]}
        />
      </Card>
      <div className="rwStack">
        <Form
          title="New tax rule"
          testId="rule-form"
          permission="tax.setup"
          submitLabel="Create rule"
          fields={[
            { name: "jurisdiction_id", label: "Jurisdiction", type: "select", options: optionsOf(jurisdictions.data, (j) => `${j.code} ${j.name}`), required: true },
            { name: "code", label: "Code", required: true },
            { name: "version", label: "Version", type: "number", step: "1", initial: "1", required: true },
            { name: "responsibility", label: "Paid by", type: "select", required: true, options: ["employee", "employer", "both"].map((x) => ({ value: x, label: x })) },
            { name: "rate", label: "Rate (decimal)", type: "number", step: "0.0001", required: true },
            { name: "annual_wage_base", label: "Annual wage base (optional)", type: "number" },
            { name: "effective_from", label: "Effective from", type: "date", required: true },
            { name: "effective_to", label: "Effective to (optional)", type: "date" },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v4b/tax-rules", {
              ...v,
              version: Number(v.version),
              annual_wage_base: v.annual_wage_base || null,
              effective_to: v.effective_to || null,
            });
            return `Rule ${v.code} v${v.version} created.`;
          }}
        />
        <Form
          title="New jurisdiction"
          testId="jurisdiction-form"
          permission="tax.setup"
          submitLabel="Create jurisdiction"
          fields={[
            { name: "code", label: "Code", required: true },
            { name: "name", label: "Name", required: true },
            { name: "level", label: "Level", type: "select", required: true, options: ["federal", "state", "local", "territory"].map((x) => ({ value: x, label: x })) },
            { name: "country_code", label: "Country", initial: "US", required: true },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v4b/jurisdictions", v);
            return `Jurisdiction ${v.code} created.`;
          }}
        />
      </div>
    </Grid>
  );
}

function Authorities({ jurisdictions, authorities, refresh }: Shared) {
  return (
    <Grid>
      <Card title="Tax authorities">
        <Table
          testId="authorities-table"
          rows={authorities.data}
          loading={authorities.loading}
          error={authorities.error}
          columns={[
            { key: "code", label: "Code" },
            { key: "name", label: "Authority" },
            { key: "jurisdiction_id", label: "Jurisdiction", render: (r) => String((jurisdictions.data ?? []).find((j) => j.id === r.jurisdiction_id)?.code ?? "") },
          ]}
        />
      </Card>
      <Form
        title="New authority"
        testId="authority-form"
        permission="tax.setup"
        submitLabel="Create authority"
        fields={[
          { name: "jurisdiction_id", label: "Jurisdiction", type: "select", options: optionsOf(jurisdictions.data, (j) => `${j.code} ${j.name}`), required: true },
          { name: "code", label: "Code", required: true },
          { name: "name", label: "Name", required: true },
        ]}
        onSaved={() => {
          refresh();
          authorities.reload();
        }}
        onSubmit={async (v) => {
          await post("/api/v4b/authorities", v);
          return `Authority ${v.code} created.`;
        }}
      />
    </Grid>
  );
}

function Liabilities({ authorities, authorityName, version, refresh }: Shared) {
  const liabilities = useLoad(() => get<Row[]>("/api/v4b/liabilities"), `liab:${version}`);
  const runs = useRows("payroll-runs", String(version));
  return (
    <Grid>
      <Card title="Tax liabilities">
        <Table
          testId="liabilities-table"
          rows={liabilities.data}
          loading={liabilities.loading}
          error={liabilities.error}
          empty="No liabilities. Create them from a posted payroll run."
          columns={[
            { key: "authority_id", label: "Authority", render: (r) => authorityName(r.authority_id) },
            { key: "liability_type", label: "Type" },
            { key: "due_date", label: "Due" },
            { key: "amount", label: "Amount", align: "right", render: (r) => <Amount value={r.amount} /> },
            { key: "open_amount", label: "Open", align: "right", render: (r) => <Amount value={r.open_amount} /> },
            { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
          ]}
        />
      </Card>
      <Form
        title="Create liabilities from a posted payroll run"
        testId="liability-form"
        permission="tax.liability.write"
        submitLabel="Create liabilities"
        fields={[
          { name: "payroll_run_id", label: "Posted payroll run", type: "select", options: optionsOf((runs.data ?? []).filter((r) => ["posted", "funded", "paid"].includes(String(r.status))), (r) => String(r.run_number)), required: true },
          { name: "authority_id", label: "Authority", type: "select", options: optionsOf(authorities.data, (a) => `${a.code} ${a.name}`), required: true },
          { name: "due_date", label: "Due date", type: "date", required: true },
        ]}
        onSaved={() => {
          refresh();
          liabilities.reload();
        }}
        onSubmit={async (v) => {
          const created = await post<{ liability_type: string; amount: string }[]>("/api/v4b/liabilities/from-payroll", v);
          return `Created ${created.map((c) => `${c.liability_type} ${c.amount}`).join(", ")}.`;
        }}
      />
    </Grid>
  );
}

function Returns({ gl, authorities, authorityName, version, refresh }: Shared) {
  const returns = useLoad(() => get<Row[]>("/api/v4b/returns"), `ret:${version}`);
  const liabilities = useLoad(() => get<Row[]>("/api/v4b/liabilities"), `liab2:${version}`);
  const [selected, setSelected] = useState<Row | null>(null);
  const ctx = usePostingContext(gl, [
    { key: "tax_payable_account_id", label: "Tax payable account", type: "liability" },
    { key: "cash_account_id", label: "Cash account", type: "asset" },
  ]);
  const [log, onDone] = useActionLog();
  const [recon, setRecon] = useState("");
  const [authority, setAuthority] = useState("");
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  const current = selected ? (returns.data ?? []).find((r) => r.id === selected.id) ?? selected : null;
  return (
    <>
      {ctx.node}
      <Grid>
        <Card title="Tax returns">
          <Table
            testId="returns-table"
            rows={returns.data}
            loading={returns.loading}
            error={returns.error}
            selectedId={current ? String(current.id) : undefined}
            onSelect={setSelected}
            columns={[
              { key: "period_code", label: "Period" },
              { key: "authority_id", label: "Authority", render: (r) => authorityName(r.authority_id) },
              { key: "due_date", label: "Due" },
              { key: "total_tax", label: "Tax", align: "right", render: (r) => <Amount value={r.total_tax} /> },
              { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
            ]}
          />
          {current ? (
            <div className="rwSelected">
              <h3>
                {String(current.period_code)} <Badge value={current.status} />
              </h3>
              <div className="rwActions">
                <ActionButton label="Approve" permission="tax.return.approve" testId="return-approve" onDone={done} run={() => post(`/api/v4b/returns/${String(current.id)}/approve`)} />
              </div>
              {log}
              <Form
                title="Remit payment"
                testId="remit-form"
                permission="tax.remit"
                submitLabel="Remit and post"
                fields={[
                  {
                    name: "liability_id",
                    label: "Liability",
                    type: "select",
                    options: optionsOf((liabilities.data ?? []).filter((l) => Number(l.open_amount) > 0), (l) => `${String(l.liability_type)} open ${String(l.open_amount)}`),
                    required: true,
                  },
                  { name: "amount", label: "Amount", type: "number", required: true },
                  { name: "payment_date", label: "Payment date", type: "date", initial: today(), required: true },
                ]}
                onSaved={() => {
                  refresh();
                  liabilities.reload();
                }}
                onSubmit={async (v) => {
                  if (!ctx.ready) throw new Error(`Choose the posting context first (${ctx.missing.join(", ")}).`);
                  await post(`/api/v4b/returns/${String(current.id)}/remit`, {
                    ...v,
                    ledger_id: ctx.values.ledger_id,
                    accounting_period_id: ctx.values.period_id,
                    tax_payable_account_id: ctx.values.tax_payable_account_id,
                    cash_account_id: ctx.values.cash_account_id,
                    currency_code: "USD",
                  });
                  return `Remitted ${v.amount}.`;
                }}
              />
            </div>
          ) : (
            <p className="rwMuted">Select a return to approve and remit it.</p>
          )}
          <div className="rwFilters">
            <label>
              <span>Reconcile authority</span>
              <select aria-label="Reconcile authority" value={authority} onChange={(e) => setAuthority(e.target.value)}>
                <option value="">Select…</option>
                {(authorities.data ?? []).map((a) => (
                  <option key={String(a.id)} value={String(a.id)}>
                    {authorityName(a.id)}
                  </option>
                ))}
              </select>
            </label>
            <ActionButton
              label="Reconcile to ledger"
              permission="tax.reconcile"
              testId="tax-reconcile"
              disabled={!authority || !ctx.values.tax_payable_account_id}
              onDone={onDone}
              run={async () => {
                const r = await post<{ status: string; subledger_total: string; gl_total: string }>("/api/v4b/reconcile", undefined, {
                  authority_id: authority,
                  tax_payable_account_id: ctx.values.tax_payable_account_id,
                });
                setRecon(`${r.status}: liabilities ${r.subledger_total} vs ledger ${r.gl_total}`);
              }}
            />
          </div>
          {recon ? <p data-testid="tax-recon">{recon}</p> : null}
        </Card>
        <Form
          title="New tax return"
          testId="return-form"
          permission="tax.return.write"
          submitLabel="Create return"
          fields={[
            { name: "authority_id", label: "Authority", type: "select", options: optionsOf(authorities.data, (a) => `${a.code} ${a.name}`), required: true },
            { name: "period_code", label: "Period code", required: true },
            { name: "period_start", label: "Period start", type: "date", required: true },
            { name: "period_end", label: "Period end", type: "date", required: true },
            { name: "due_date", label: "Due date", type: "date", required: true },
            { name: "tax_code", label: "Tax code", required: true },
            { name: "taxable_wages", label: "Taxable wages", type: "number", required: true },
            { name: "tax_amount", label: "Tax amount", type: "number", required: true },
          ]}
          onSaved={() => {
            refresh();
            returns.reload();
          }}
          onSubmit={async (v) => {
            await post("/api/v4b/returns", v);
            return `Return ${v.period_code} created as draft. Another user approves it.`;
          }}
        />
      </Grid>
    </>
  );
}

function Calculator({ version }: Shared) {
  const rules = useRows("tax-rules", String(version));
  const workers = useRows("payroll-run-workers", String(version));
  const [result, setResult] = useState("");
  return (
    <Grid>
      <Form
        title="Calculate tax for a payroll worker"
        testId="calc-form"
        permission="tax.calculate"
        submitLabel="Calculate"
        fields={[
          { name: "tax_rule_id", label: "Rule", type: "select", options: optionsOf(rules.data, (r) => `${r.code} v${r.version} (${r.effective_from}${r.effective_to ? ` to ${r.effective_to}` : ""})`), required: true },
          { name: "payroll_worker_id", label: "Payroll run worker", type: "select", options: optionsOf(workers.data, (w) => `gross ${String(w.gross_pay)} · net ${String(w.net_pay)}`), required: true },
          { name: "taxable_wages", label: "Taxable wages", type: "number", required: true },
          { name: "as_of", label: "Pay date", type: "date", initial: today(), required: true },
          { name: "additional_withholding", label: "Additional withholding", type: "number", initial: "0" },
          { name: "exempt", label: "Exempt", type: "checkbox" },
        ]}
        onSubmit={async (v) => {
          const r = await post<{ employee_amount: string; employer_amount: string; explanation: string }>("/api/v4b/calculate", {
            ...v,
            additional_withholding: v.additional_withholding || "0",
            exempt: v.exempt === "true",
          });
          setResult(`Employee ${r.employee_amount} · Employer ${r.employer_amount} (${r.explanation})`);
          return "Calculated.";
        }}
      />
      <Card title="Result">{result ? <p data-testid="calc-result">{result}</p> : <p className="rwMuted">Run a calculation.</p>}</Card>
    </Grid>
  );
}
