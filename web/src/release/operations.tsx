"use client";

import { type FormEvent, useMemo, useState } from "react";

import { errorText, get, request, type Params, type Row } from "./client";
import { useLoad, usePermissions, useRows } from "./hooks";
import { Card, Notice, Table } from "./ui";

/**
 * Operations console: every API operation of a workspace, described by the server
 * (/api/v1/operations), with a typed form generated from its input schema. Buttons
 * follow the signed-in user's permissions; the server enforces them regardless.
 */

export type Schema = {
  type?: string;
  format?: string;
  enum?: unknown[];
  anyOf?: Schema[];
  oneOf?: Schema[];
  allOf?: Schema[];
  properties?: Record<string, Schema>;
  required?: string[];
  items?: Schema;
  title?: string;
  default?: unknown;
  pattern?: string;
  description?: string;
  minimum?: number;
  maximum?: number;
  /** Table whose records this id field refers to (added by the server's operation catalog). */
  "x-ref"?: string;
};
export type Parameter = { name: string; in: "path" | "query"; required: boolean; schema: Schema; ref?: string };
export type Operation = {
  id: string;
  method: string;
  path: string;
  summary: string;
  group: string;
  workspace: string;
  permission: string;
  decision_permission: string;
  parameters: Parameter[];
  body: Schema | null;
};
export type Catalog = { workspace: string | null; operations: Operation[]; tables: string[] };

export function useOperations(workspace: string) {
  return useLoad(() => get<Catalog>("/api/v1/operations", { workspace }), workspace);
}

// ------------------------------------------------------------------ schema -> fields
type Kind = "text" | "number" | "integer" | "checkbox" | "select" | "date" | "datetime" | "json" | "ref";
type Field = { name: string; label: string; kind: Kind; required: boolean; options: string[]; hint: string; schema: Schema; ref?: string };

function plain(schema: Schema): Schema {
  const options = schema.anyOf ?? schema.oneOf;
  if (options) {
    const real = options.filter((s) => s.type !== "null");
    return real.length === 1 ? { ...real[0], description: schema.description ?? real[0].description } : schema;
  }
  if (schema.allOf?.length === 1) return schema.allOf[0];
  return schema;
}

function choices(schema: Schema): string[] {
  if (schema.enum) return schema.enum.map(String);
  const m = schema.pattern?.match(/^\^\(([\w|-]+)\)\$$/);
  return m ? m[1].split("|") : [];
}

function kindOf(schema: Schema): Kind {
  if (choices(schema).length) return "select";
  switch (schema.type) {
    case "boolean":
      return "checkbox";
    case "integer":
      return "integer";
    case "number":
      return "number";
    case "string":
      if (schema.format === "date") return "date";
      if (schema.format === "date-time") return "datetime";
      return "text";
    default:
      return "json";
  }
}

function label(name: string): string {
  const text = name.replace(/_id$/, "").replace(/^id$/, "record").replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function fieldFor(name: string, raw: Schema, required: boolean, ref?: string): Field {
  const schema = plain(raw);
  const target = ref ?? raw["x-ref"] ?? schema["x-ref"];
  if (target && kindOf(schema) === "text") return { name, label: label(name), kind: "ref", required, options: [], hint: "", schema, ref: target };
  const kind = kindOf(schema);
  const hints: string[] = [];
  if (schema.format === "uuid" || /_id$/.test(name)) hints.push("record id");
  if (kind === "json") hints.push(schema.type === "array" ? "JSON list" : "JSON");
  if (schema.format === "decimal" || (schema.type === "string" && /amount|price|rate|qty|quantity|total|cost/.test(name))) hints.push("decimal");
  return { name, label: label(name), kind, required, options: choices(schema), hint: hints.join(", "), schema };
}

function bodyFields(body: Schema | null): Field[] | null {
  if (!body) return [];
  const schema = plain(body);
  if (!schema.properties) return null; // not an object: edit the whole body as JSON
  const required = new Set(schema.required ?? []);
  return Object.entries(schema.properties).map(([name, s]) => fieldFor(name, s, required.has(name)));
}

function example(schema: Schema, depth = 0): unknown {
  const s = plain(schema);
  if (depth > 4) return null;
  if (s.default !== undefined && s.default !== null) return s.default;
  if (choices(s).length) return choices(s)[0];
  if (s.properties) return Object.fromEntries(Object.entries(s.properties).map(([k, v]) => [k, example(v, depth + 1)]));
  if (s.type === "array") return s.items ? [example(s.items, depth + 1)] : [];
  if (s.type === "integer" || s.type === "number") return 0;
  if (s.type === "boolean") return false;
  if (s.type === "object") return {};
  return "";
}

function convert(field: Field, value: string): unknown {
  switch (field.kind) {
    case "checkbox":
      return value === "true";
    case "integer": {
      const n = Number.parseInt(value, 10);
      if (Number.isNaN(n)) throw new Error(`${field.label}: enter a whole number`);
      return n;
    }
    case "number": {
      const n = Number(value);
      if (Number.isNaN(n)) throw new Error(`${field.label}: enter a number`);
      return n;
    }
    case "datetime":
      return new Date(value).toISOString();
    case "json":
      try {
        return JSON.parse(value);
      } catch {
        throw new Error(`${field.label}: enter valid JSON`);
      }
    default:
      return value;
  }
}

function initial(field: Field): string {
  const d = field.schema.default;
  if (field.kind === "checkbox") return d === true ? "true" : "false";
  if (field.kind === "json") return d !== undefined && d !== null ? JSON.stringify(d) : field.required ? JSON.stringify(example(field.schema)) : "";
  return d !== undefined && d !== null ? String(d) : "";
}

const LABEL_KEYS = ["display_name", "name", "legal_name", "title", "full_name", "email", "number", "document_number", "reference", "code", "period_code", "description", "status"];

/** Human label for a record: its code and name where it has them, else a short id and date. */
export function recordLabel(row: Row): string {
  const value = (k: string) => {
    const v = row[k];
    return v === null || v === undefined || typeof v === "object" ? "" : String(v).trim();
  };
  const given = [value("given_name"), value("family_name")].filter(Boolean).join(" ");
  const main = LABEL_KEYS.map(value).find(Boolean) || given;
  const code = value("code") || value("account_code") || value("number");
  const parts = [code && code !== main ? code : "", main].filter(Boolean);
  const text = parts.join(" — ");
  const date = value("created_at").slice(0, 10);
  const short = String(row.id ?? "").slice(0, 8);
  return text ? (text.length > 80 ? `${text.slice(0, 77)}…` : text) : `${short}${date ? ` (created ${date})` : ""}`;
}

function RefInput(props: { field: Field; id: string; value: string; onChange: (v: string) => void }) {
  const rows = useRows(props.field.ref ?? "", props.field.ref ?? "");
  const [manual, setManual] = useState(false);
  const options = (rows.data ?? [])
    .filter((r) => r.id !== undefined && r.id !== null)
    .map((r) => ({ value: String(r.id), label: recordLabel(r) }))
    .sort((a, b) => a.label.localeCompare(b.label));
  const known = !props.value || options.some((o) => o.value === props.value);
  if (manual || rows.error || (!known && !rows.loading))
    return (
      <span className="rwRef">
        <input id={props.id} type="text" value={props.value} required={props.field.required} placeholder="Record id" onChange={(e) => props.onChange(e.target.value)} />
        {rows.data && options.length ? (
          <button type="button" className="rwLink" onClick={() => setManual(false)}>
            Choose from list
          </button>
        ) : null}
      </span>
    );
  return (
    <span className="rwRef">
      <select id={props.id} value={props.value} required={props.field.required} onChange={(e) => props.onChange(e.target.value)} data-ref={props.field.ref}>
        <option value="">{rows.loading ? "Loading…" : options.length ? "Choose…" : "No records yet"}</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <button type="button" className="rwLink" onClick={() => setManual(true)}>
        Enter an id
      </button>
    </span>
  );
}

function FieldInput(props: { field: Field; id: string; value: string; onChange: (v: string) => void }) {
  const { field } = props;
  if (field.kind === "ref") return <RefInput {...props} />;
  if (field.kind === "select")
    return (
      <select id={props.id} value={props.value} required={field.required} onChange={(e) => props.onChange(e.target.value)}>
        <option value="">Select…</option>
        {field.options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    );
  if (field.kind === "checkbox")
    return <input id={props.id} type="checkbox" checked={props.value === "true"} onChange={(e) => props.onChange(String(e.target.checked))} />;
  if (field.kind === "json")
    return <textarea id={props.id} rows={3} value={props.value} required={field.required} onChange={(e) => props.onChange(e.target.value)} spellCheck={false} />;
  const type = { text: "text", number: "number", integer: "number", date: "date", datetime: "datetime-local" }[field.kind] ?? "text";
  return (
    <input
      id={props.id}
      type={type}
      step={field.kind === "number" ? "any" : field.kind === "integer" ? "1" : undefined}
      value={props.value}
      required={field.required}
      onChange={(e) => props.onChange(e.target.value)}
    />
  );
}

function Fields(props: { title?: string; fields: Field[]; values: Record<string, string>; prefix: string; onChange: (name: string, v: string) => void }) {
  if (!props.fields.length) return null;
  return (
    <div className="rwOpFields">
      {props.title ? <span className="rwLinesTitle">{props.title}</span> : null}
      <div className="rwFields">
        {props.fields.map((f) => (
          <label key={f.name} htmlFor={`${props.prefix}-${f.name}`} className={f.kind === "json" ? "wide" : ""}>
            <span>
              {f.label}
              {f.required ? " *" : ""}
              {f.hint ? <em> ({f.hint})</em> : null}
            </span>
            <FieldInput field={f} id={`${props.prefix}-${f.name}`} value={props.values[f.name] ?? ""} onChange={(v) => props.onChange(f.name, v)} />
          </label>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ one operation
export function OperationForm(props: { operation: Operation; onDone?: () => void }) {
  const op = props.operation;
  const { can, loaded } = usePermissions();
  const pathFields = useMemo(() => op.parameters.filter((p) => p.in === "path").map((p) => fieldFor(p.name, p.schema, true, p.ref)), [op]);
  const queryFields = useMemo(() => op.parameters.filter((p) => p.in === "query").map((p) => fieldFor(p.name, p.schema, p.required, p.ref)), [op]);
  const fields = useMemo(() => bodyFields(op.body), [op]);
  const all = [...pathFields, ...queryFields, ...(fields ?? [])];
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(all.map((f) => [f.name, initial(f)])));
  const [rawBody, setRawBody] = useState(() => (op.body && !fields ? JSON.stringify(example(op.body), null, 2) : ""));
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string; data?: unknown } | null>(null);
  const allowed = !op.permission || (loaded && can(op.permission));
  const prefix = `op-${op.id}`;
  const set = (name: string, v: string) => setValues((s) => ({ ...s, [name]: v }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setResult(null);
    try {
      let path = op.path;
      for (const f of pathFields) path = path.replace(`{${f.name}}`, encodeURIComponent(values[f.name] ?? ""));
      const params: Params = {};
      for (const f of queryFields) if ((values[f.name] ?? "") !== "") params[f.name] = String(convert(f, values[f.name]));
      let body: unknown = undefined;
      if (op.body) {
        if (fields) {
          const out: Record<string, unknown> = {};
          for (const f of fields) {
            const v = values[f.name] ?? "";
            if (v === "" && f.kind !== "checkbox") continue;
            out[f.name] = convert(f, v);
          }
          body = out;
        } else {
          body = rawBody.trim() ? JSON.parse(rawBody) : undefined;
        }
      }
      const data = await request<unknown>(op.method, path, body, params);
      setResult({ ok: true, text: `${op.method} ${op.path}: done`, data });
      props.onDone?.();
    } catch (error) {
      setResult({ ok: false, text: errorText(error) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="rwForm rwOpForm" onSubmit={submit} data-testid="op-form" aria-label={op.summary || op.path}>
      <h3>
        <span className={`rwMethod ${op.method.toLowerCase()}`}>{op.method}</span> {op.summary || op.path}
      </h3>
      <p className="rwMuted rwPath">{op.path}</p>
      <p className="rwMuted">
        {op.permission ? `Requires ${op.permission}` : "Available to every signed-in user"}
        {op.decision_permission ? `; decisions (approve, post, close…) require ${op.decision_permission}` : ""}.
      </p>
      <fieldset disabled={!allowed || busy}>
        <Fields title="Identify" fields={pathFields} values={values} prefix={prefix} onChange={set} />
        <Fields title="Options" fields={queryFields} values={values} prefix={prefix} onChange={set} />
        {fields ? (
          <Fields title={fields.length ? "Details" : undefined} fields={fields} values={values} prefix={prefix} onChange={set} />
        ) : (
          <label htmlFor={`${prefix}-body`} className="wide">
            <span>Request (JSON)</span>
            <textarea id={`${prefix}-body`} rows={8} value={rawBody} onChange={(e) => setRawBody(e.target.value)} spellCheck={false} />
          </label>
        )}
        <button type="submit" className="rwBtn primary" data-testid="op-run">
          {busy ? "Working…" : op.method === "GET" ? "Load" : "Run"}
        </button>
      </fieldset>
      {!allowed && loaded ? <p className="rwMuted">You do not have permission {op.permission}.</p> : null}
      {result ? <Notice kind={result.ok ? "ok" : "error"}>{result.text}</Notice> : null}
      {result?.ok && result.data !== undefined && result.data !== null ? (
        <pre className="rwJson" data-testid="op-result">
          {JSON.stringify(result.data, null, 2).slice(0, 20000)}
        </pre>
      ) : null}
    </form>
  );
}

// ------------------------------------------------------------------ console
export function OperationsConsole(props: { workspace: string; operations?: Operation[] }) {
  const loaded = useOperations(props.workspace);
  const operations = props.operations ?? loaded.data?.operations ?? [];
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<string>("");
  const { can, loaded: permsLoaded } = usePermissions();
  const shown = operations.filter((o) => `${o.summary} ${o.path} ${o.group}`.toLowerCase().includes(filter.toLowerCase()));
  const groups = new Map<string, Operation[]>();
  for (const o of shown) groups.set(o.group, [...(groups.get(o.group) ?? []), o]);
  const current = operations.find((o) => o.id === selected) ?? null;

  if (loaded.error && !props.operations) return <Notice kind="error">{loaded.error}</Notice>;
  if (loaded.loading && !operations.length) return <p className="rwMuted">Loading operations…</p>;
  return (
    <div className="rwOps" data-testid="ops-console">
      <aside className="rwOpList">
        <input
          type="search"
          placeholder={`Filter ${operations.length} operations`}
          aria-label="Filter operations"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        {[...groups.entries()].map(([group, ops]) => (
          <div key={group} className="rwOpGroup">
            <span>{label(group.replace(/-/g, " "))}</span>
            {ops.map((o) => (
              <button
                key={o.id}
                type="button"
                className={`rwOpItem${o.id === selected ? " on" : ""}${permsLoaded && o.permission && !can(o.permission) ? " locked" : ""}`}
                data-testid={`op-${o.id}`}
                title={o.path}
                onClick={() => setSelected(o.id)}
              >
                <span className={`rwMethod ${o.method.toLowerCase()}`}>{o.method}</span>
                {o.summary || o.path}
              </button>
            ))}
          </div>
        ))}
      </aside>
      <div className="rwOpMain">
        {current ? (
          <OperationForm key={current.id} operation={current} />
        ) : (
          <p className="rwMuted">Choose an operation to see its form. Operations you are not permitted to run are dimmed.</p>
        )}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ records
export function RecordsBrowser(props: { tables: string[] }) {
  const [table, setTable] = useState("");
  const active = table || props.tables[0] || "";
  const rows = useRows(active, active);
  const columns = Object.keys(rows.data?.[0] ?? {})
    .filter((c) => c !== "tenant_id")
    .slice(0, 9)
    .map((key) => ({
      key,
      label: label(key),
      render: (row: Record<string, unknown>) => {
        const v = row[key];
        const text = v !== null && typeof v === "object" ? JSON.stringify(v) : String(v ?? "");
        return text.length > 60 ? `${text.slice(0, 57)}…` : text;
      },
    }));
  if (!props.tables.length) return <p className="rwMuted">This workspace has no record tables of its own.</p>;
  return (
    <Card
      title="Records"
      testId="records-browser"
      aside={
        <select aria-label="Record type" value={active} onChange={(e) => setTable(e.target.value)}>
          {props.tables.map((t) => (
            <option key={t} value={t}>
              {label(t)}
            </option>
          ))}
        </select>
      }
    >
      <Table rows={rows.data} columns={columns} loading={rows.loading} error={rows.error} empty="No records of this type yet." />
    </Card>
  );
}
