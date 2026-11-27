"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type RecordValue = Record<string, unknown>;

type PageResult = {
  items: RecordValue[];
  total: number;
};

type ServiceWorkspaceProps = {
  title: string;
  resources: string[];
  actions?: string[];
};

export function ServiceWorkspace({
  title,
  resources,
  actions = [],
}: ServiceWorkspaceProps) {
  const [resource, setResource] = useState(resources[0] ?? "");
  const [items, setItems] = useState<RecordValue[]>([]);
  const [selected, setSelected] = useState<RecordValue | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!resource) {
      setItems([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `/api/flowforge/api/v1/platform/${resource}`,
        { cache: "no-store" },
      );

      if (!response.ok) {
        throw new Error(`Request failed (${response.status})`);
      }

      const page = (await response.json()) as PageResult;
      setItems(page.items ?? []);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : String(cause),
      );
    } finally {
      setLoading(false);
    }
  }, [resource]);

  useEffect(() => {
    const controller = new AbortController();

    void fetch(
      `/api/flowforge/api/v1/platform/${resource}`,
      {
        cache: "no-store",
        signal: controller.signal,
      },
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Request failed (${response.status})`,
          );
        }

        return response.json() as Promise<PageResult>;
      })
      .then((page) => {
        setItems(page.items ?? []);
      })
      .catch((cause) => {
        if (
          !(cause instanceof DOMException) ||
          cause.name !== "AbortError"
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : String(cause),
          );
        }
      });

    return () => controller.abort();
  }, [resource]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    if (!normalized) {
      return items;
    }

    return items.filter((item) =>
      JSON.stringify(item).toLowerCase().includes(normalized),
    );
  }, [items, query]);

  const columns = Object.keys(filtered[0] ?? {}).slice(0, 8);

  async function runAction(action: string) {
    if (!selected?.id) {
      setError("Select a record before running an action.");
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `/api/flowforge/api/v1/platform/${resource}/${String(
          selected.id,
        )}/${action}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: "{}",
        },
      );

      if (!response.ok) {
        throw new Error(
          `${action} failed (${response.status})`,
        );
      }

      await load();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : String(cause),
      );
    }
  }

  return (
    <main>
      <div className="pagehead">
        <div>
          <div className="eyebrow">Connected platform service</div>
          <h1>{title}</h1>
        </div>

        <button
          className="btn"
          type="button"
          onClick={() => void load()}
        >
          Refresh
        </button>
      </div>

      <div className="toolbar panel">
        <select
          className="field"
          aria-label="Resource"
          value={resource}
          onChange={(event) => {
            setResource(event.target.value);
            setSelected(null);
          }}
        >
          {resources.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <input
          className="field"
          aria-label="Search loaded records"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search loaded records"
        />
      </div>

      {loading && <p role="status">Loading...</p>}
      {error && <p role="alert">{error}</p>}

      <section className="panel">
        <div className="panelbody">
          {!loading && filtered.length === 0 ? (
            <p>No records found.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    {columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {filtered.map((row, index) => (
                    <tr
                      key={String(row.id ?? index)}
                      onClick={() => setSelected(row)}
                    >
                      {columns.map((column) => {
                        const value = row[column];

                        return (
                          <td key={column}>
                            {typeof value === "object"
                              ? JSON.stringify(value)
                              : String(value ?? "")}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {selected && (
            <aside>
              <h2>Selected record</h2>
              <pre>{JSON.stringify(selected, null, 2)}</pre>

              <div>
                {actions.map((action) => (
                  <button
                    className="btn"
                    type="button"
                    key={action}
                    onClick={() => void runAction(action)}
                  >
                    {action}
                  </button>
                ))}
              </div>
            </aside>
          )}
        </div>
      </section>
    </main>
  );
}