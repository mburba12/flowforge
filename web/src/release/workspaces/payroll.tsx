"use client";

import { useState } from "react";

import { get, post, today, type Row } from "../client";
import { usePostingContext } from "../context";
import { useLoad, usePartyNames, useRows } from "../hooks";
import { optionsOf, useGl } from "../refs";
import { ActionButton, Amount, Badge, Card, Details, Form, Grid, Notice, Table, Tabs, Workspace, useActionLog } from "../ui";
import { PayrollSwitch } from "./payroll-switch";

const TABS = [
  { id: "runs", label: "Payroll runs" },
  { id: "workers", label: "Workers" },
  { id: "setup", label: "Pay groups & periods" },
  { id: "switch", label: "Move from another provider" },
];

type RunSummary = {
  id: string;
  run_number: string;
  status: string;
  workers: number;
  totals: Record<string, string>;
  liabilities: { type: string; amount: string; open: string }[];
  paid: string;
};

export function PayrollWorkspace({ initialTab = "runs" }: { initialTab?: string }) {
  const [tab, setTab] = useState(initialTab);
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const key = String(version);
  const gl = useGl(key);
  const names = usePartyNames(key);
  const workers = useRows("workers", key);
  const workerName = (id: unknown) => {
    const w = (workers.data ?? []).find((x) => x.id === id);
    return w ? `${names.get(String(w.party_id)) ?? w.worker_number} (${String(w.worker_number)})` : String(id ?? "");
  };
  const shared = { gl, workers, workerName, version, refresh, names };
  return (
    <Workspace
      title={initialTab === "workers" ? "Employees" : "Payroll"}
      description={initialTab === "workers" ? "Everyone you pay: details, pay rates, tax settings and bank accounts." : "Run payroll from gross to net, approve it, pay your people and keep the books right."}
      accent="#dc2626"
    >
      {workers.data && workers.data.length === 0 && tab !== "switch" ? (
        <Notice kind="info">
          No employees yet. Coming from ADP, Gusto, Paychex, QuickBooks or another provider?{" "}
          <button type="button" className="linkish" onClick={() => setTab("switch")}>
            Move your payroll to Krov WorkAgent
          </button>
        </Notice>
      ) : null}
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "runs" ? <Runs {...shared} /> : null}
      {tab === "workers" ? <Workers {...shared} /> : null}
      {tab === "setup" ? <Setup {...shared} /> : null}
      {tab === "switch" ? <PayrollSwitch /> : null}
    </Workspace>
  );
}

type Shared = {
  gl: ReturnType<typeof useGl>;
  workers: ReturnType<typeof useRows>;
  workerName: (id: unknown) => string;
  version: number;
  refresh: () => void;
  names: Map<string, string>;
};

function Workers({ workers, names, refresh }: Shared) {
  return (
    <Grid>
      <Card title="Workers">
        <Table
          testId="workers-table"
          rows={workers.data}
          loading={workers.loading}
          error={workers.error}
          columns={[
            { key: "worker_number", label: "Number" },
            { key: "party_id", label: "Name", render: (r) => names.get(String(r.party_id)) ?? "" },
            { key: "worker_type", label: "Type" },
            { key: "employment_status", label: "Status", render: (r) => <Badge value={r.employment_status} /> },
            { key: "pay_frequency", label: "Pay frequency" },
            { key: "hire_date", label: "Hired" },
          ]}
        />
      </Card>
      <Form
        title="New worker"
        testId="worker-form"
        permission="workforce.write"
        submitLabel="Add worker"
        fields={[
          { name: "given_name", label: "First name", required: true },
          { name: "family_name", label: "Last name", required: true },
          { name: "hire_date", label: "Hire date", type: "date", initial: today(), required: true },
          {
            name: "pay_frequency",
            label: "Pay frequency",
            type: "select",
            initial: "semimonthly",
            required: true,
            options: ["weekly", "biweekly", "semimonthly", "monthly"].map((f) => ({ value: f, label: f })),
          },
          { name: "hourly_rate", label: "Hourly rate", type: "number", required: true },
          { name: "currency", label: "Currency", initial: "USD", required: true },
        ]}
        onSaved={refresh}
        onSubmit={async (v) => {
          const person = await post<{ id: string }>("/api/v2/people", { given_name: v.given_name, family_name: v.family_name });
          const worker = await post<{ id: string; worker_number: string }>("/api/v4a/workers", {
            party_id: person.id,
            worker_type: "employee",
            hire_date: v.hire_date,
            default_currency: v.currency,
            pay_frequency: v.pay_frequency,
          });
          await post(`/api/v4a/workers/${worker.id}/compensation`, {
            compensation_type: "hourly",
            amount: v.hourly_rate,
            currency_code: v.currency,
            effective_from: v.hire_date,
          });
          return `Worker ${worker.worker_number} added at ${v.hourly_rate}/hour.`;
        }}
      />
    </Grid>
  );
}

function Setup({ version, refresh }: Shared) {
  const groups = useRows("pay-groups", String(version));
  const periods = useRows("pay-periods", String(version));
  const groupName = (id: unknown) => String((groups.data ?? []).find((g) => g.id === id)?.code ?? id ?? "");
  return (
    <Grid>
      <Card title="Pay groups and pay periods">
        <Table testId="pay-groups-table" rows={groups.data} loading={groups.loading} error={groups.error} columns={[{ key: "code", label: "Group" }, { key: "name", label: "Name" }, { key: "pay_frequency", label: "Frequency" }]} />
        <Table
          testId="pay-periods-table"
          rows={periods.data}
          loading={periods.loading}
          columns={[
            { key: "period_code", label: "Period" },
            { key: "pay_group_id", label: "Group", render: (r) => groupName(r.pay_group_id) },
            { key: "start_date", label: "Start" },
            { key: "end_date", label: "End" },
            { key: "pay_date", label: "Pay date" },
          ]}
        />
      </Card>
      <div className="rwStack">
        <Form
          title="New pay group"
          testId="pay-group-form"
          permission="payroll.setup"
          submitLabel="Create pay group"
          fields={[
            { name: "code", label: "Code", required: true },
            { name: "name", label: "Name", required: true },
            { name: "pay_frequency", label: "Frequency", type: "select", initial: "semimonthly", required: true, options: ["weekly", "biweekly", "semimonthly", "monthly"].map((f) => ({ value: f, label: f })) },
            { name: "currency_code", label: "Currency", initial: "USD", required: true },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v4a/pay-groups", v);
            return `Pay group ${v.code} created.`;
          }}
        />
        <Form
          title="New pay period"
          testId="pay-period-form"
          permission="payroll.setup"
          submitLabel="Create pay period"
          fields={[
            { name: "pay_group_id", label: "Pay group", type: "select", options: optionsOf(groups.data, (g) => `${g.code} ${g.name}`), required: true },
            { name: "period_code", label: "Code", required: true },
            { name: "start_date", label: "Start", type: "date", required: true },
            { name: "end_date", label: "End", type: "date", required: true },
            { name: "pay_date", label: "Pay date", type: "date", required: true },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v4a/pay-periods", v);
            return `Pay period ${v.period_code} created.`;
          }}
        />
      </div>
    </Grid>
  );
}

function Runs({ gl, workers, workerName, version, refresh }: Shared) {
  const runs = useRows("payroll-runs", String(version));
  const groups = useRows("pay-groups", String(version));
  const periods = useRows("pay-periods", String(version));
  const [selectedId, setSelectedId] = useState("");
  const summary = useLoad(async () => (selectedId ? get<RunSummary>(`/api/v4a/payroll/runs/${selectedId}`) : null), `run:${selectedId}:${version}`);
  const ctx = usePostingContext(gl, [
    { key: "wage_expense_account_id", label: "Wage expense", type: "expense" },
    { key: "employer_tax_expense_account_id", label: "Employer tax expense", type: "expense" },
    { key: "employee_tax_payable_account_id", label: "Employee tax payable", type: "liability" },
    { key: "employer_tax_payable_account_id", label: "Employer tax payable", type: "liability" },
    { key: "deductions_payable_account_id", label: "Deductions payable", type: "liability" },
    { key: "net_pay_payable_account_id", label: "Net pay payable", type: "liability" },
    { key: "cash_account_id", label: "Cash", type: "asset" },
  ]);
  const [log, onDone] = useActionLog();
  const [recon, setRecon] = useState("");
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  const s = summary.data;
  const periodLabel = (id: unknown) => String((periods.data ?? []).find((p) => p.id === id)?.period_code ?? "");
  return (
    <>
      {ctx.node}
      <Grid>
        <Card title="Payroll runs">
          <Table
            testId="runs-table"
            rows={runs.data}
            loading={runs.loading}
            error={runs.error}
            selectedId={selectedId}
            onSelect={(r: Row) => setSelectedId(String(r.id))}
            columns={[
              { key: "run_number", label: "Run" },
              { key: "pay_period_id", label: "Pay period", render: (r) => periodLabel(r.pay_period_id) },
              { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
            ]}
          />
          {s ? (
            <div className="rwSelected" data-testid="run-detail">
              <h3>
                {s.run_number} <Badge value={s.status} />
              </h3>
              <Details
                items={[
                  ["Workers", String(s.workers)],
                  ["Gross", <Amount key="g" value={s.totals.gross} />],
                  ["Employee taxes", <Amount key="e" value={s.totals.employee_taxes} />],
                  ["Employer taxes", <Amount key="r" value={s.totals.employer_taxes} />],
                  ["Deductions", <Amount key="d" value={s.totals.deductions} />],
                  ["Net pay", <Amount key="n" value={s.totals.net} />],
                  ["Paid", <Amount key="p" value={s.paid} />],
                ]}
              />
              <div className="rwActions">
                <ActionButton label="Approve" permission="payroll.run.approve" testId="run-approve" onDone={done} run={() => post(`/api/v4a/payroll/runs/${s.id}/approve`)} />
                <ActionButton
                  label="Post to ledger"
                  permission="payroll.run.post"
                  testId="run-post"
                  primary
                  disabled={!ctx.ready}
                  onDone={done}
                  run={() =>
                    post(`/api/v4a/payroll/runs/${s.id}/post`, {
                      wage_expense_account_id: ctx.values.wage_expense_account_id,
                      employer_tax_expense_account_id: ctx.values.employer_tax_expense_account_id,
                      employee_tax_payable_account_id: ctx.values.employee_tax_payable_account_id,
                      employer_tax_payable_account_id: ctx.values.employer_tax_payable_account_id,
                      deductions_payable_account_id: ctx.values.deductions_payable_account_id,
                      net_pay_payable_account_id: ctx.values.net_pay_payable_account_id,
                      currency_code: "USD",
                    })
                  }
                />
                <ActionButton
                  label="Reconcile"
                  permission="payroll.reconcile"
                  testId="run-reconcile"
                  onDone={onDone}
                  run={async () => {
                    const r = await post<{ status: string; subledger_total: string; gl_total: string }>(`/api/v4a/payroll/runs/${s.id}/reconcile`);
                    setRecon(`${r.status}: payroll ${r.subledger_total} vs ledger ${r.gl_total}`);
                  }}
                />
              </div>
              {recon ? <p data-testid="run-recon">{recon}</p> : null}
              {!ctx.ready ? <Notice kind="info">Choose the ledger, period and payroll accounts above to post and pay.</Notice> : null}
              {log}
              <Form
                title="Calculate gross to net"
                testId="run-calc-form"
                permission="payroll.run.write"
                submitLabel="Calculate"
                fields={[]}
                lines={{
                  name: "workers",
                  label: "Worker inputs (tax rates as decimals, e.g. 0.10)",
                  columns: [
                    { name: "worker_id", label: "Worker", type: "select", options: optionsOf(workers.data, (w) => workerName(w.id)), required: true },
                    { name: "regular_hours", label: "Regular hrs", type: "number", initial: "80" },
                    { name: "overtime_hours", label: "Overtime hrs", type: "number", initial: "0" },
                    { name: "bonus", label: "Bonus", type: "number", initial: "0" },
                    { name: "pretax_deductions", label: "Pre-tax ded.", type: "number", initial: "0" },
                    { name: "posttax_deductions", label: "Post-tax ded.", type: "number", initial: "0" },
                    { name: "employee_tax_rate", label: "Employee tax", type: "number", step: "0.0001", initial: "0.10" },
                    { name: "employer_tax_rate", label: "Employer tax", type: "number", step: "0.0001", initial: "0.0765" },
                  ],
                }}
                onSaved={refresh}
                onSubmit={async (_, rows) => {
                  await post(`/api/v4a/payroll/runs/${s.id}/calculate`, { workers: rows });
                  return "Calculated. Another user approves the run before posting.";
                }}
              />
              <Form
                title="Pay a worker"
                testId="run-pay-form"
                permission="payroll.pay"
                submitLabel="Record payment"
                fields={[
                  { name: "worker_id", label: "Worker", type: "select", options: optionsOf(workers.data, (w) => workerName(w.id)), required: true },
                  { name: "amount", label: "Net amount", type: "number", required: true },
                ]}
                onSaved={refresh}
                onSubmit={async (v) => {
                  if (!ctx.values.cash_account_id || !ctx.values.net_pay_payable_account_id) throw new Error("Choose the cash and net pay payable accounts above.");
                  await post(`/api/v4a/payroll/runs/${s.id}/payments`, {
                    worker_id: v.worker_id,
                    amount: v.amount,
                    cash_account_id: ctx.values.cash_account_id,
                    net_pay_payable_account_id: ctx.values.net_pay_payable_account_id,
                    currency_code: "USD",
                  });
                  return `Paid ${v.amount}.`;
                }}
              />
            </div>
          ) : (
            <p className="rwMuted">Select a run to calculate, approve, post, pay and reconcile it.</p>
          )}
        </Card>
        <Form
          title="New payroll run"
          testId="run-form"
          permission="payroll.run.write"
          submitLabel="Create run"
          fields={[
            { name: "pay_group_id", label: "Pay group", type: "select", options: optionsOf(groups.data, (g) => `${g.code} ${g.name}`), required: true },
            { name: "pay_period_id", label: "Pay period", type: "select", options: optionsOf(periods.data, (p) => `${p.period_code} (pay ${p.pay_date})`), required: true },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            if (!ctx.values.ledger_id || !ctx.values.period_id) throw new Error("Choose the ledger and accounting period above first.");
            const run = await post<{ id: string; run_number: string }>("/api/v4a/payroll/runs", {
              ...v,
              ledger_id: ctx.values.ledger_id,
              accounting_period_id: ctx.values.period_id,
            });
            setSelectedId(run.id);
            return `Run ${run.run_number} created as draft.`;
          }}
        />
      </Grid>
    </>
  );
}
