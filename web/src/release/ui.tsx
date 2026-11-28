"use client";

import { type FormEvent, type ReactNode, useState } from "react";

import { errorText, money } from "./client";
import { usePermissions } from "./hooks";

// ------------------------------------------------------------------ layout
export function Workspace(props: { title: string; description: string; accent?: string; children: ReactNode }) {
  return (
    <main className="rw">
      <header className="rwHead" style={{ borderLeftColor: props.accent ?? "#2563eb" }}>
        <h1>{props.title}</h1>
        <p>{props.description}</p>
      </header>
      {props.children}
    </main>
  );
}

export function Tabs(props: { tabs: { id: string; label: string }[]; active: string; onChange: (id: string) => void }) {
  return (
    <nav className="rwTabs" role="tablist">
      {props.tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={props.active === tab.id}
          className={props.active === tab.id ? "on" : ""}
          onClick={() => props.onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}

export function Card(props: { title: string; aside?: ReactNode; children: ReactNode; testId?: string }) {
  return (
    <section className="rwCard" data-testid={props.testId}>
      <div className="rwCardHead">
        <h2>{props.title}</h2>
        {props.aside}
      </div>
      <div className="rwCardBody">{props.children}</div>
    </section>
  );
}

export function Grid(props: { children: ReactNode }) {
  return <div className="rwGrid">{props.children}</div>;
}

export function Notice(props: { kind: "error" | "ok" | "info"; children: ReactNode }) {
  if (!props.children) return null;
  return (
    <div className={`rwNotice ${props.kind}`} role={props.kind === "error" ? "alert" : "status"}>
      {props.children}
    </div>
  );
}

export function Badge(props: { value: unknown }) {
  const text = String(props.value ?? "");
  const tone = /posted|paid|approved|reconciled|active|open|invoiced|filed|matched|true/.test(text)
    ? "good"
    : /hold|exception|rejected|closed|false|draft/.test(text)
      ? "warn"
      : "neutral";
  return <span className={`rwBadge ${tone}`}>{text}</span>;
}

export function Amount(props: { value: unknown }) {
  return <span className="rwAmount">{money(props.value)}</span>;
}

/** Renders children only for users holding `permission`; otherwise explains the access. */
export function RequiresPermission(props: { permission: string; area: string; children: ReactNode }) {
  const { can, loaded } = usePermissions();
  if (!loaded) return <p className="rwMuted">Loading…</p>;
  if (!can(props.permission)) {
    return (
      <Notice kind="info">
        {props.area} needs the permission {props.permission}. Ask an owner or manager to grant it to your role.
      </Notice>
    );
  }
  return <>{props.children}</>;
}

// ------------------------------------------------------------------ table
export type Column<T> = { key: string; label: string; render?: (row: T) => ReactNode; align?: "right" };

export function Table<T extends Record<string, unknown>>(props: {
  rows: T[] | null;
  columns: Column<T>[];
  loading?: boolean;
  error?: string;
  empty?: string;
  selectedId?: string;
  onSelect?: (row: T) => void;
  testId?: string;
}) {
  if (props.error) return <Notice kind="error">{props.error}</Notice>;
  if (props.loading && !props.rows) return <p className="rwMuted">Loading…</p>;
  if (!props.rows || props.rows.length === 0) return <p className="rwMuted">{props.empty ?? "No records yet."}</p>;
  return (
    <div className="rwTable" data-testid={props.testId}>
      <table>
        <thead>
          <tr>
            {props.columns.map((c) => (
              <th key={c.key} className={c.align === "right" ? "r" : ""}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {props.rows.map((row, index) => {
            const id = String(row.id ?? index);
            return (
              <tr
                key={id}
                className={props.selectedId === id ? "sel" : props.onSelect ? "click" : ""}
                onClick={props.onSelect ? () => props.onSelect?.(row) : undefined}
              >
                {props.columns.map((c) => (
                  <td key={c.key} className={c.align === "right" ? "r" : ""}>
                    {c.render ? c.render(row) : String(row[c.key] ?? "")}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ------------------------------------------------------------------ actions
export function ActionButton(props: {
  label: string;
  permission: string;
  run: () => Promise<unknown>;
  onDone: (message: string, ok: boolean) => void;
  primary?: boolean;
  disabled?: boolean;
  testId?: string;
}) {
  const { can, loaded } = usePermissions();
  const [busy, setBusy] = useState(false);
  const allowed = loaded && can(props.permission);
  return (
    <button
      type="button"
      className={props.primary ? "rwBtn primary" : "rwBtn"}
      data-testid={props.testId}
      disabled={busy || !allowed || props.disabled}
      title={loaded && !allowed ? `Requires permission ${props.permission}` : undefined}
      onClick={async () => {
        setBusy(true);
        try {
          await props.run();
          props.onDone(`${props.label}: done`, true);
        } catch (error) {
          props.onDone(`${props.label}: ${errorText(error)}`, false);
        } finally {
          setBusy(false);
        }
      }}
    >
      {busy ? "Working…" : props.label}
    </button>
  );
}

// ------------------------------------------------------------------ forms
export type Option = { value: string; label: string };
export type FieldSpec = {
  name: string;
  label: string;
  type?: "text" | "number" | "date" | "select" | "checkbox" | "email" | "password";
  options?: Option[];
  required?: boolean;
  initial?: string;
  step?: string;
};
export type LineSpec = { name: string; label: string; columns: FieldSpec[]; minRows?: number };
export type Values = Record<string, string>;
export type FormValues = Values & { __lines?: unknown };

function blank(fields: FieldSpec[]): Values {
  const values: Values = {};
  for (const f of fields) values[f.name] = f.initial ?? (f.type === "checkbox" ? "false" : "");
  return values;
}

function Input(props: { spec: FieldSpec; value: string; onChange: (v: string) => void; idPrefix: string }) {
  const { spec } = props;
  const id = `${props.idPrefix}-${spec.name}`;
  if (spec.type === "select") {
    return (
      <select id={id} name={spec.name} value={props.value} required={spec.required} onChange={(e) => props.onChange(e.target.value)}>
        <option value="">Select…</option>
        {(spec.options ?? []).map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    );
  }
  if (spec.type === "checkbox") {
    return <input id={id} name={spec.name} type="checkbox" checked={props.value === "true"} onChange={(e) => props.onChange(String(e.target.checked))} />;
  }
  return (
    <input
      id={id}
      name={spec.name}
      type={spec.type ?? "text"}
      step={spec.step ?? (spec.type === "number" ? "0.01" : undefined)}
      value={props.value}
      required={spec.required}
      onChange={(e) => props.onChange(e.target.value)}
    />
  );
}

/**
 * Declarative form: fields (+ optional line items). onSubmit receives string values
 * and line rows; it returns a success message. Disabled without the permission.
 */
export function Form(props: {
  title: string;
  permission: string;
  fields: FieldSpec[];
  lines?: LineSpec;
  submitLabel: string;
  onSubmit: (values: Values, lines: Values[]) => Promise<string>;
  onSaved?: () => void;
  testId?: string;
}) {
  const { can, loaded } = usePermissions();
  const [values, setValues] = useState<Values>(() => blank(props.fields));
  const [rows, setRows] = useState<Values[]>(() =>
    props.lines ? Array.from({ length: props.lines.minRows ?? 1 }, () => blank(props.lines?.columns ?? [])) : [],
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const allowed = loaded && can(props.permission);
  const prefix = props.testId ?? props.title.toLowerCase().replace(/[^a-z0-9]+/g, "-");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const text = await props.onSubmit(values, rows);
      setMessage({ ok: true, text });
      setValues(blank(props.fields));
      if (props.lines) setRows(Array.from({ length: props.lines.minRows ?? 1 }, () => blank(props.lines?.columns ?? [])));
      props.onSaved?.();
    } catch (error) {
      setMessage({ ok: false, text: errorText(error) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="rwForm" onSubmit={submit} data-testid={props.testId} aria-label={props.title}>
      <h3>{props.title}</h3>
      {!allowed && loaded ? <p className="rwMuted">Requires permission {props.permission}.</p> : null}
      <fieldset disabled={!allowed || busy}>
        <div className="rwFields">
          {props.fields.map((f) => (
            <label key={f.name} htmlFor={`${prefix}-${f.name}`}>
              <span>{f.label}</span>
              <Input spec={f} idPrefix={prefix} value={values[f.name] ?? ""} onChange={(v) => setValues((s) => ({ ...s, [f.name]: v }))} />
            </label>
          ))}
        </div>
        {props.lines ? (
          <div className="rwLines">
            <span className="rwLinesTitle">{props.lines.label}</span>
            {rows.map((row, index) => (
              <div className="rwLine" key={index}>
                {props.lines?.columns.map((c) => (
                  <label key={c.name} htmlFor={`${prefix}-l${index}-${c.name}`}>
                    <span>{c.label}</span>
                    <Input
                      spec={c}
                      idPrefix={`${prefix}-l${index}`}
                      value={row[c.name] ?? ""}
                      onChange={(v) => setRows((all) => all.map((r, i) => (i === index ? { ...r, [c.name]: v } : r)))}
                    />
                  </label>
                ))}
                {rows.length > (props.lines?.minRows ?? 1) ? (
                  <button type="button" className="rwBtn" onClick={() => setRows((all) => all.filter((_, i) => i !== index))}>
                    Remove
                  </button>
                ) : null}
              </div>
            ))}
            <button type="button" className="rwBtn" onClick={() => setRows((all) => [...all, blank(props.lines?.columns ?? [])])}>
              Add line
            </button>
          </div>
        ) : null}
        <button type="submit" className="rwBtn primary">
          {busy ? "Saving…" : props.submitLabel}
        </button>
      </fieldset>
      {message ? <Notice kind={message.ok ? "ok" : "error"}>{message.text}</Notice> : null}
    </form>
  );
}

/** Detail list of key/value pairs. */
export function Details(props: { items: [string, ReactNode][] }) {
  return (
    <dl className="rwDetails">
      {props.items.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Status line for row actions: last result message. */
export function useActionLog(): [ReactNode, (message: string, ok: boolean) => void] {
  const [last, setLast] = useState<{ text: string; ok: boolean } | null>(null);
  const node = last ? <Notice kind={last.ok ? "ok" : "error"}>{last.text}</Notice> : null;
  return [node, (text, ok) => setLast({ text, ok })];
}
