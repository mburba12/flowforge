"use client";

import { useState } from "react";

import { get, money, post, today, type Row } from "../client";
import { useLoad, useRows } from "../hooks";
import { useGl, type Period } from "../refs";
import { ActionButton, Amount, Badge, Card, Form, Grid, Table, Tabs, Workspace, useActionLog } from "../ui";

const TABS = [
  { id: "journals", label: "Journals" },
  { id: "periods", label: "Periods" },
  { id: "trial", label: "Trial balance" },
  { id: "setup", label: "Ledgers & accounts" },
];

export function FinanceWorkspace() {
  const [tab, setTab] = useState("journals");
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const gl = useGl(String(version));
  return (
    <Workspace title="Accounting" description="Your books: journal entries, approvals, accounting periods, trial balance and chart of accounts." accent="#4f46e5">
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "journals" ? <Journals gl={gl} version={version} refresh={refresh} /> : null}
      {tab === "periods" ? <Periods gl={gl} refresh={refresh} /> : null}
      {tab === "trial" ? <TrialBalance gl={gl} version={version} /> : null}
      {tab === "setup" ? <Setup gl={gl} refresh={refresh} /> : null}
    </Workspace>
  );
}

type Gl = ReturnType<typeof useGl>;

function Journals({ gl, version, refresh }: { gl: Gl; version: number; refresh: () => void }) {
  const journals = useRows("journals", String(version));
  const [selected, setSelected] = useState<Row | null>(null);
  const lines = useLoad(
    async () => (selected ? (await get<{ items: Row[] }>("/api/v1/business/journal-lines", { field: "journal_id", value: String(selected.id), limit: 200 })).items : []),
    `lines:${String(selected?.id)}:${version}`,
  );
  const [log, onDone] = useActionLog();
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  const accounts = gl.accountOptions();
  return (
    <Grid>
      <Card title="Journals" aside={<span className="rwMuted">{journals.data?.length ?? 0} journals</span>}>
        <Table
          testId="journals-table"
          rows={journals.data}
          loading={journals.loading}
          error={journals.error}
          selectedId={selected ? String(selected.id) : undefined}
          onSelect={setSelected}
          columns={[
            { key: "journal_number", label: "Number" },
            { key: "journal_date", label: "Date" },
            { key: "description", label: "Description" },
            { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
          ]}
        />
        {selected ? (
          <div className="rwSelected">
            <h3>
              {String(selected.journal_number)} <Badge value={selected.status} />
            </h3>
            <Table
              rows={lines.data}
              loading={lines.loading}
              columns={[
                { key: "account_id", label: "Account", render: (r) => gl.accountName(r.account_id) },
                { key: "debit", label: "Debit", align: "right", render: (r) => <Amount value={r.debit} /> },
                { key: "credit", label: "Credit", align: "right", render: (r) => <Amount value={r.credit} /> },
              ]}
            />
            <div className="rwActions">
              <ActionButton label="Approve" permission="gl.journal.approve" testId="journal-approve" onDone={done} run={() => post(`/api/v2/journals/${String(selected.id)}/approve`)} />
              <ActionButton label="Post" permission="gl.journal.post" testId="journal-post" primary onDone={done} run={() => post(`/api/v2/journals/${String(selected.id)}/post`)} />
            </div>
            {log}
          </div>
        ) : null}
      </Card>
      <Card title="New journal">
        <Form
          title="Create journal"
          testId="journal-form"
          permission="gl.journal.write"
          submitLabel="Create journal"
          fields={[
            { name: "ledger_id", label: "Ledger", type: "select", options: gl.ledgerOptions, required: true },
            { name: "period_id", label: "Period", type: "select", options: gl.openPeriodOptions, required: true },
            { name: "journal_date", label: "Date", type: "date", initial: today(), required: true },
            { name: "description", label: "Description", required: true },
            { name: "currency_code", label: "Currency", initial: "USD", required: true },
          ]}
          lines={{
            name: "lines",
            label: "Lines (debits must equal credits)",
            minRows: 2,
            columns: [
              { name: "account_id", label: "Account", type: "select", options: accounts, required: true },
              { name: "debit", label: "Debit", type: "number" },
              { name: "credit", label: "Credit", type: "number" },
            ],
          }}
          onSaved={refresh}
          onSubmit={async (v, rows) => {
            const created = await post<{ id: string }>("/api/v2/journals", {
              ledger_id: v.ledger_id,
              period_id: v.period_id,
              journal_date: v.journal_date,
              description: v.description,
              lines: rows.map((r) => ({ account_id: r.account_id, debit: r.debit || "0", credit: r.credit || "0", currency_code: v.currency_code })),
            });
            return `Journal created (${created.id.slice(0, 8)}). It needs approval by another user before posting.`;
          }}
        />
      </Card>
    </Grid>
  );
}

function Periods({ gl, refresh }: { gl: Gl; refresh: () => void }) {
  const [log, onDone] = useActionLog();
  const [reason, setReason] = useState("");
  const done = (m: string, ok: boolean) => {
    onDone(m, ok);
    refresh();
  };
  return (
    <Grid>
      <Card title="Accounting periods">
        <Table<Period & Record<string, unknown>>
          testId="periods-table"
          rows={gl.periods.data as (Period & Record<string, unknown>)[] | null}
          loading={gl.periods.loading}
          error={gl.periods.error}
          columns={[
            { key: "period_code", label: "Period" },
            { key: "start_date", label: "Start" },
            { key: "end_date", label: "End" },
            { key: "status", label: "Status", render: (r) => <Badge value={r.status} /> },
            {
              key: "act",
              label: "",
              render: (r) =>
                r.status === "open" ? (
                  <ActionButton label="Close" permission="gl.period.manage" testId={`close-${r.period_code}`} onDone={done} run={() => post(`/api/v2/accounting-periods/${r.id}/close`)} />
                ) : (
                  <ActionButton
                    label="Reopen"
                    permission="gl.period.manage"
                    testId={`reopen-${r.period_code}`}
                    disabled={reason.trim().length < 5}
                    onDone={done}
                    run={() => post(`/api/v2/accounting-periods/${r.id}/reopen`, { reason })}
                  />
                ),
            },
          ]}
        />
        <label className="rwInline">
          <span>Reason for reopening</span>
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="At least 5 characters" />
        </label>
        {log}
      </Card>
      <Card title="New period">
        <Form
          title="Create period"
          testId="period-form"
          permission="gl.period.manage"
          submitLabel="Create period"
          fields={[
            { name: "calendar_id", label: "Fiscal calendar", type: "select", options: gl.calendarOptions, required: true },
            { name: "period_code", label: "Code (e.g. 2026-12)", required: true },
            { name: "start_date", label: "Start", type: "date", required: true },
            { name: "end_date", label: "End", type: "date", required: true },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v2/accounting-periods", v);
            return `Period ${v.period_code} created (open).`;
          }}
        />
      </Card>
    </Grid>
  );
}

function TrialBalance({ gl, version }: { gl: Gl; version: number }) {
  const [ledger, setLedger] = useState("");
  const [period, setPeriod] = useState("");
  const totals = useLoad(
    async () => (ledger && period ? get<{ debit: string; credit: string }>("/api/v2/trial-balance", { ledger_id: ledger, period_id: period }) : null),
    `tb:${ledger}:${period}:${version}`,
  );
  const balances = useLoad(
    async () => (ledger && period ? (await get<{ items: Row[] }>("/api/v1/business/account-balances", { field: "period_id", value: period, limit: 200 })).items : []),
    `bal:${ledger}:${period}:${version}`,
  );
  const allPeriods = (gl.periods.data ?? []).map((p) => ({ value: p.id, label: `${p.period_code} (${p.status})` }));
  const rows = (balances.data ?? []).filter((b) => b.ledger_id === ledger);
  return (
    <Card title="Trial balance">
      <div className="rwFilters">
        <label>
          <span>Ledger</span>
          <select aria-label="Ledger" value={ledger} onChange={(e) => setLedger(e.target.value)}>
            <option value="">Select…</option>
            {gl.ledgerOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Period</span>
          <select aria-label="Period" value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="">Select…</option>
            {allPeriods.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {totals.error ? <p className="rwNotice error">{totals.error}</p> : null}
      {totals.data ? (
        <p data-testid="tb-totals" className="rwTotals">
          Debits <strong>{money(totals.data.debit)}</strong> · Credits <strong>{money(totals.data.credit)}</strong> ·{" "}
          {totals.data.debit === totals.data.credit ? <Badge value="balanced" /> : <Badge value="out of balance" />}
        </p>
      ) : (
        <p className="rwMuted">Choose a ledger and period.</p>
      )}
      <Table
        rows={rows}
        columns={[
          { key: "account_id", label: "Account", render: (r) => gl.accountName(r.account_id) },
          { key: "debit_total", label: "Debits", align: "right", render: (r) => <Amount value={r.debit_total} /> },
          { key: "credit_total", label: "Credits", align: "right", render: (r) => <Amount value={r.credit_total} /> },
          { key: "net", label: "Net", align: "right", render: (r) => <Amount value={Number(r.debit_total) - Number(r.credit_total)} /> },
        ]}
        empty="No postings in this period."
      />
    </Card>
  );
}

function Setup({ gl, refresh }: { gl: Gl; refresh: () => void }) {
  return (
    <Grid>
      <Card title="Chart of accounts" aside={<span className="rwMuted">{gl.accounts.data?.length ?? 0} accounts</span>}>
        <Table
          testId="accounts-table"
          rows={gl.accounts.data}
          loading={gl.accounts.loading}
          error={gl.accounts.error}
          columns={[
            { key: "account_code", label: "Code" },
            { key: "name", label: "Name" },
            { key: "account_type", label: "Type" },
            { key: "normal_balance", label: "Normal" },
            { key: "posting_allowed", label: "Posting", render: (r) => <Badge value={String(r.posting_allowed)} /> },
          ]}
        />
      </Card>
      <div className="rwStack">
        <Form
          title="Add account"
          testId="account-form"
          permission="gl.setup"
          submitLabel="Add account"
          fields={[
            { name: "ledger_id", label: "Ledger", type: "select", options: gl.ledgerOptions, required: true },
            { name: "account_code", label: "Code", required: true },
            { name: "name", label: "Name", required: true },
            {
              name: "account_type",
              label: "Type",
              type: "select",
              required: true,
              options: ["asset", "liability", "equity", "revenue", "expense"].map((t) => ({ value: t, label: t })),
            },
            { name: "normal_balance", label: "Normal balance", type: "select", required: true, options: [{ value: "debit", label: "debit" }, { value: "credit", label: "credit" }] },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v2/accounts", { ...v, posting_allowed: true });
            return `Account ${v.account_code} added.`;
          }}
        />
        <Form
          title="Add ledger"
          testId="ledger-form"
          permission="gl.setup"
          submitLabel="Add ledger"
          fields={[
            { name: "code", label: "Code", required: true },
            { name: "name", label: "Name", required: true },
            { name: "base_currency", label: "Base currency", initial: "USD", required: true },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v2/currencies", { code: v.base_currency, name: v.base_currency }).catch(() => undefined);
            await post("/api/v2/ledgers", v);
            return `Ledger ${v.code} added.`;
          }}
        />
        <Form
          title="Add fiscal calendar"
          testId="calendar-form"
          permission="gl.setup"
          submitLabel="Add calendar"
          fields={[
            { name: "name", label: "Name", required: true },
            { name: "start_month", label: "Start month (1-12)", type: "number", step: "1", initial: "1", required: true },
          ]}
          onSaved={refresh}
          onSubmit={async (v) => {
            await post("/api/v2/fiscal-calendars", { name: v.name, start_month: Number(v.start_month) });
            return `Calendar ${v.name} added.`;
          }}
        />
      </div>
    </Grid>
  );
}
