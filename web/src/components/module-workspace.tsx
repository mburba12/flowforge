"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/auth";
import { modules, tagMap } from "@/lib/modules";

type Parameter = {
  in?: string;
  name?: string;
  required?: boolean;
};

type Operation = {
  path: string;
  method: string;
  summary: string;
  tags: string[];
  schema?: Record<string, unknown>;
  parameters?: Parameter[];
};

type OpenApiOperation = {
  summary?: string;
  operationId?: string;
  tags?: string[];
  parameters?: Parameter[];
  requestBody?: {
    content?: {
      "application/json"?: {
        schema?: Record<string, unknown>;
      };
    };
  };
};

type OpenApiDocument = {
  paths?: Record<string, Record<string, OpenApiOperation>>;
};

function defaultPayload(schema?: Record<string, unknown>) {
  if (!schema || "$ref" in schema) return {};

  const properties = (schema.properties ?? {}) as Record<
    string,
    Record<string, unknown>
  >;
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(properties)) {
    if (value.default !== undefined) result[key] = value.default;
    else if (value.type === "boolean") result[key] = false;
    else if (value.type === "array") result[key] = [];
    else if (value.type === "object") result[key] = {};
    else result[key] = "";
  }

  return result;
}

export function ModuleWorkspace({ slug }: { slug: string }) {
  const title = modules.find(([key]) => key === slug)?.[1] ?? slug;
  const [operations, setOperations] = useState<Operation[]>([]);
  const [selected, setSelected] = useState<Operation | null>(null);
  const [payload, setPayload] = useState("{}");
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    void fetch("/api/flowforge/openapi.json", {
      cache: "no-store",
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`OpenAPI request failed (${response.status})`);
        }
        return response.json() as Promise<OpenApiDocument>;
      })
      .then((specification) => {
        const rows: Operation[] = [];

        for (const [path, pathItem] of Object.entries(
          specification.paths ?? {},
        )) {
          for (const method of ["get", "post", "put", "patch", "delete"]) {
            const operation = pathItem[method];
            if (!operation) continue;

            rows.push({
              path,
              method,
              summary: operation.summary ?? operation.operationId ?? path,
              tags: operation.tags ?? [],
              schema:
                operation.requestBody?.content?.["application/json"]?.schema,
              parameters: operation.parameters ?? [],
            });
          }
        }

        const moduleTags = tagMap[slug] ?? [];
        setOperations(
          rows.filter((operation) =>
            operation.tags.some((tag) => moduleTags.includes(tag)),
          ),
        );
      })
      .catch((cause: unknown) => {
        if (!(cause instanceof DOMException && cause.name === "AbortError")) {
          setResult(cause instanceof Error ? cause.message : String(cause));
        }
      });

    return () => controller.abort();
  }, [slug]);

  const shown = useMemo(() => {
    const normalized = filter.toLowerCase();
    return operations.filter((operation) =>
      `${operation.summary} ${operation.path}`
        .toLowerCase()
        .includes(normalized),
    );
  }, [filter, operations]);

  function choose(operation: Operation) {
    setSelected(operation);
    setPayload(JSON.stringify(defaultPayload(operation.schema), null, 2));
    setResult("");
  }

  async function run() {
    if (!selected) return;

    setBusy(true);
    try {
      let requestPath = selected.path;
      const body = JSON.parse(payload || "{}") as Record<string, unknown>;

      for (const parameter of selected.parameters ?? []) {
        if (parameter.in !== "path" || !parameter.name) continue;
        const parameterValue = window.prompt(parameter.name);
        if (!parameterValue) {
          throw new Error(`${parameter.name} is required`);
        }
        requestPath = requestPath.replace(
          `{${parameter.name}}`,
          encodeURIComponent(parameterValue),
        );
      }

      const data = await api(requestPath, {
        method: selected.method.toUpperCase(),
        body: ["get", "delete"].includes(selected.method)
          ? undefined
          : JSON.stringify(body),
      });
      setResult(JSON.stringify(data, null, 2));
    } catch (cause) {
      setResult(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <div className="pageTitle">
        <div>
          <small>Connected module</small>
          <h1>{title}</h1>
          <p>{operations.length} live backend operations available.</p>
        </div>
      </div>

      <div className="workspace">
        <section className="panel operations">
          <input
            aria-label="Search operations"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Search operations"
          />

          {shown.map((operation) => (
            <button
              type="button"
              className={selected === operation ? "selected" : ""}
              key={`${operation.method}:${operation.path}`}
              onClick={() => choose(operation)}
            >
              <span className={`method ${operation.method}`}>
                {operation.method}
              </span>
              <b>{operation.summary}</b>
              <small>{operation.path}</small>
            </button>
          ))}
        </section>

        <section className="panel editor">
          {selected ? (
            <>
              <div className="ophead">
                <span className={`method ${selected.method}`}>
                  {selected.method}
                </span>
                <h2>{selected.summary}</h2>
              </div>
              <code>{selected.path}</code>

              {!['get', 'delete'].includes(selected.method) && (
                <>
                  <label htmlFor="request-payload">Request data</label>
                  <textarea
                    id="request-payload"
                    value={payload}
                    onChange={(event) => setPayload(event.target.value)}
                  />
                </>
              )}

              <button
                type="button"
                className="primary"
                disabled={busy}
                onClick={() => void run()}
              >
                {busy ? "Running..." : "Run operation"}
              </button>

              <label>Response</label>
              <pre>{result || "No response yet."}</pre>
            </>
          ) : (
            <div className="empty">
              <h2>Select an operation</h2>
              <p>
                Choose an action from the left to view its request and run it
                against FlowForge.
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
