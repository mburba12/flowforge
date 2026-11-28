"use client";

import { useRef, useState } from "react";

import { del, errorText, get, money, post, upload } from "../client";
import { useLoad, usePermissions } from "../hooks";
import { Badge, Card, Notice, Table, Workspace } from "../ui";

type Account = {
  id: string;
  name: string;
  mask: string | null;
  type: string;
  subtype: string | null;
  currency: string;
  current_balance: string | null;
  available_balance: string | null;
  owed: boolean;
  connection_id: string;
  institution: string | null;
  provider: string;
  status: string;
  last_synced_at: string | null;
  transactions: number;
};
type Overview = { accounts: Account[]; totals: { currency: string; cash: string; owed: string }[]; live_connections_available: boolean };
type Txn = Record<string, unknown> & { id: string; account: string; date: string; description: string; money_in: string | null; money_out: string | null; currency: string; pending: boolean };

type PlaidHandler = { open: () => void };
type PlaidGlobal = { create: (config: Record<string, unknown>) => PlaidHandler };

function loadPlaid(): Promise<PlaidGlobal> {
  const w = window as unknown as { Plaid?: PlaidGlobal };
  if (w.Plaid) return Promise.resolve(w.Plaid);
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.plaid.com/link/v2/stable/link-initialize.js";
    script.onload = () => (w.Plaid ? resolve(w.Plaid) : reject(new Error("Plaid did not load")));
    script.onerror = () => reject(new Error("Could not load the secure bank sign-in window"));
    document.head.appendChild(script);
  });
}

function ago(value: string | null): string {
  if (!value) return "never";
  const minutes = Math.round((Date.now() - new Date(value).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 60 * 24) return `${Math.round(minutes / 60)} h ago`;
  return new Date(value).toLocaleDateString();
}

const SOURCE: Record<string, string> = { plaid: "Live feed", demo: "Demo data", statement: "Statements" };

export function BankingWorkspace() {
  const { can } = usePermissions();
  const overview = useLoad(() => get<Overview>("/api/v1/banking/overview"), "bank-overview");
  const [account, setAccount] = useState("");
  const [search, setSearch] = useState("");
  const txns = useLoad(
    () => get<Txn[]>("/api/v1/banking/transactions", { account_id: account || undefined, search: search || undefined, limit: 300 }),
    `txns:${account}:${search}:${overview.data ? overview.data.accounts.length : 0}`,
  );
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState("");
  const [importing, setImporting] = useState(false);
  const accounts = overview.data?.accounts ?? [];

  function refreshAll() {
    overview.reload();
    txns.reload();
  }

  async function act(label: string, run: () => Promise<string>) {
    setBusy(label);
    setMessage(null);
    try {
      setMessage({ ok: true, text: await run() });
      refreshAll();
    } catch (error) {
      setMessage({ ok: false, text: errorText(error) });
    } finally {
      setBusy("");
    }
  }

  async function connectLive() {
    await act("connect", async () => {
      const { link_token } = await post<{ link_token: string }>("/api/v1/banking/link", { provider: "plaid" });
      const plaid = await loadPlaid();
      return new Promise<string>((resolve, reject) => {
        plaid
          .create({
            token: link_token,
            onSuccess: async (publicToken: string, metadata: { institution?: { institution_id?: string; name?: string } }) => {
              try {
                const result = await post<{ accounts: number; transactions_added: number }>("/api/v1/banking/connections", {
                  provider: "plaid",
                  public_token: publicToken,
                  institution_id: metadata.institution?.institution_id,
                  institution_name: metadata.institution?.name,
                });
                resolve(`Connected ${result.accounts} account(s) and imported ${result.transactions_added} transactions.`);
              } catch (error) {
                reject(error);
              }
            },
            onExit: (error: { display_message?: string } | null) =>
              error ? reject(new Error(error.display_message || "The bank sign-in was not completed")) : resolve("Bank connection cancelled."),
          })
          .open();
      });
    });
  }

  const totals = overview.data?.totals ?? [];
  return (
    <Workspace title="Bank accounts" description="Balances and transactions from your banks, always up to date." accent="#57d3ff">
      <div className="heroActions">
        {can("banking.connect") ? (
          <button type="button" className="rwBtn primary" disabled={!!busy} onClick={connectLive} data-testid="connect-bank">
            {busy === "connect" ? "Connecting…" : "Connect a bank"}
          </button>
        ) : null}
        {can("banking.import") ? (
          <button type="button" className="rwBtn" onClick={() => setImporting((v) => !v)} data-testid="import-statement">
            Import a statement
          </button>
        ) : null}
        {can("banking.connect") && accounts.length === 0 ? (
          <button
            type="button"
            className="rwBtn"
            disabled={!!busy}
            data-testid="demo-bank"
            onClick={() =>
              act("demo", async () => {
                const r = await post<{ accounts: number }>("/api/v1/banking/connections", { provider: "demo", public_token: "demo-link" });
                return `Added ${r.accounts} demo accounts with sample transactions. Disconnect them any time.`;
              })
            }
          >
            Try with demo data
          </button>
        ) : null}
      </div>
      {overview.data && !overview.data.live_connections_available && can("banking.connect") ? (
        <Notice kind="info">
          Live bank feeds are switched off on this server, so “Connect a bank” will explain how to turn them on. Until then, import statements
          (CSV, OFX or QFX from your bank&apos;s website) — they work with every bank.
        </Notice>
      ) : null}
      {message ? <Notice kind={message.ok ? "ok" : "error"}>{message.text}</Notice> : null}
      {importing ? (
        <StatementImport
          accounts={accounts}
          onDone={(text) => {
            setImporting(false);
            setMessage({ ok: true, text });
            refreshAll();
          }}
        />
      ) : null}

      <div className="rwKpis" data-testid="bank-totals">
        {totals.length === 0 ? (
          <article>
            <span>Cash in the bank</span>
            <strong>—</strong>
            <small className="rwMuted">Connect a bank or import a statement to see it.</small>
          </article>
        ) : (
          totals.map((t) => (
            <article key={t.currency}>
              <span>Cash in the bank ({t.currency})</span>
              <strong>{money(t.cash)}</strong>
              {Number(t.owed) ? <small className="rwMuted">Owed on cards and loans: {money(t.owed)}</small> : null}
            </article>
          ))
        )}
        <article>
          <span>Accounts</span>
          <strong>{accounts.length}</strong>
        </article>
      </div>

      {overview.error ? <Notice kind="error">{overview.error}</Notice> : null}
      <div className="accountGrid" data-testid="bank-accounts">
        {accounts.map((a) => (
          <article key={a.id} className={`accountCard${account === a.id ? " on" : ""}`}>
            <button type="button" className="accountMain" onClick={() => setAccount(account === a.id ? "" : a.id)}>
              <span className="rwMuted">
                {a.institution}
                {a.mask ? ` ••${a.mask}` : ""}
              </span>
              <b>{a.name}</b>
              <strong className={a.owed ? "neg" : ""}>
                {a.owed ? "Owed " : ""}
                {money(a.current_balance)} <small>{a.currency}</small>
              </strong>
              <span className="rwMuted small">
                {SOURCE[a.provider] ?? a.provider} · updated {ago(a.last_synced_at)} · {a.transactions} transactions
              </span>
            </button>
            <div className="rwActions">
              {a.status !== "connected" ? <Badge value={a.status === "reauth_required" ? "sign in again" : a.status} /> : null}
              {a.provider !== "statement" && can("banking.import") ? (
                <button
                  type="button"
                  className="rwBtn"
                  disabled={!!busy}
                  onClick={() =>
                    act(`sync-${a.connection_id}`, async () => {
                      const r = await post<{ transactions_added: number }>(`/api/v1/banking/connections/${a.connection_id}/sync`);
                      return `${a.institution}: ${r.transactions_added} new transactions.`;
                    })
                  }
                >
                  {busy === `sync-${a.connection_id}` ? "Refreshing…" : "Refresh"}
                </button>
              ) : null}
              {can("banking.connect") ? (
                <button
                  type="button"
                  className="rwBtn"
                  disabled={!!busy}
                  onClick={() => {
                    if (!window.confirm(`Disconnect ${a.institution}? Its transactions stay in Krov WorkAgent.`)) return;
                    void act("disconnect", async () => {
                      await del(`/api/v1/banking/connections/${a.connection_id}`);
                      return `${a.institution} disconnected.`;
                    });
                  }}
                >
                  Disconnect
                </button>
              ) : null}
            </div>
          </article>
        ))}
      </div>

      <Card
        title={account ? `Transactions — ${accounts.find((a) => a.id === account)?.name ?? ""}` : "Recent transactions"}
        aside={
          <input type="search" placeholder="Search transactions" aria-label="Search transactions" value={search} onChange={(e) => setSearch(e.target.value)} />
        }
      >
        <Table
          testId="bank-transactions"
          rows={txns.data}
          loading={txns.loading}
          error={txns.error}
          empty="No transactions yet."
          columns={[
            { key: "date", label: "Date" },
            { key: "description", label: "Description", render: (t) => (<>{t.description}{t.pending ? <span className="rwMuted small"> · pending</span> : null}</>) },
            { key: "account", label: "Account" },
            { key: "money_in", label: "Money in", align: "right", render: (t) => (t.money_in ? <span className="pos">{money(t.money_in)}</span> : "") },
            { key: "money_out", label: "Money out", align: "right", render: (t) => (t.money_out ? money(t.money_out) : "") },
          ]}
        />
      </Card>
    </Workspace>
  );
}

function StatementImport(props: { accounts: Account[]; onDone: (message: string) => void }) {
  const file = useRef<HTMLInputElement>(null);
  const [target, setTarget] = useState(props.accounts[0]?.id ?? "new");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <form
      className="rwForm"
      aria-label="Import a bank statement"
      onSubmit={async (event) => {
        event.preventDefault();
        const chosen = file.current?.files?.[0];
        if (!chosen) return setError("Choose the statement file");
        const form = new FormData();
        form.append("file", chosen);
        if (target === "new") form.append("account_name", name);
        else form.append("account_id", target);
        setBusy(true);
        setError("");
        try {
          const r = await upload<{ transactions_added: number; transactions_already_imported: number }>("/api/v1/banking/statements", form);
          props.onDone(
            `Imported ${r.transactions_added} transactions${r.transactions_already_imported ? ` (${r.transactions_already_imported} were already there)` : ""}.`,
          );
        } catch (e) {
          setError(errorText(e));
        } finally {
          setBusy(false);
        }
      }}
    >
      <h3>Import a bank statement</h3>
      <p className="rwMuted">
        On your bank&apos;s website, download the account activity as CSV, OFX or QFX (often under “Download” or “Export”). Importing the same
        statement twice never creates duplicates.
      </p>
      <div className="rwFields">
        <label>
          <span>Statement file</span>
          <input ref={file} type="file" accept=".csv,.ofx,.qfx,.txt" data-testid="statement-file" required />
        </label>
        <label>
          <span>Account</span>
          <select value={target} onChange={(e) => setTarget(e.target.value)} data-testid="statement-account">
            {props.accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
                {a.mask ? ` ••${a.mask}` : ""}
              </option>
            ))}
            <option value="new">A new account…</option>
          </select>
        </label>
        {target === "new" ? (
          <label>
            <span>Account name</span>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Operating account at Chase" required data-testid="statement-account-name" />
          </label>
        ) : null}
      </div>
      <button type="submit" className="rwBtn primary" disabled={busy}>
        {busy ? "Importing…" : "Import"}
      </button>
      {error ? <Notice kind="error">{error}</Notice> : null}
    </form>
  );
}
