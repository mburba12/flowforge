"use client";

import { useState } from "react";

import { OperationsConsole, RecordsBrowser, useOperations } from "../operations";
import { Notice, Tabs, Workspace } from "../ui";
import { EXTENDED_WORKSPACES } from "../slugs";

/** Workspace for an extended domain: every operation as a form, plus its records. */
export function ExtendedWorkspace({ slug }: { slug: string }) {
  const meta = EXTENDED_WORKSPACES[slug];
  const catalog = useOperations(slug);
  const [tab, setTab] = useState("operations");
  const tables = catalog.data?.tables ?? [];
  return (
    <Workspace title={meta.title} description={meta.description} accent={meta.accent}>
      <Tabs
        tabs={[
          { id: "operations", label: `Operations${catalog.data ? ` (${catalog.data.operations.length})` : ""}` },
          { id: "records", label: `Records${catalog.data ? ` (${tables.length})` : ""}` },
        ]}
        active={tab}
        onChange={setTab}
      />
      {catalog.error ? <Notice kind="error">{catalog.error}</Notice> : null}
      {tab === "operations" ? (
        <OperationsConsole workspace={slug} operations={catalog.data?.operations} />
      ) : (
        <RecordsBrowser tables={tables} />
      )}
    </Workspace>
  );
}

/** Every operation of a release or browser workspace, below its purpose-built screens. */
export function OperationsSection({ slug }: { slug: string }) {
  const catalog = useOperations(slug);
  const count = catalog.data?.operations.length ?? 0;
  if (!catalog.data || count === 0) return null;
  return (
    <section className="rw rwAllOps" data-testid="all-operations">
      <details>
        <summary>Advanced: every action in this section ({count})</summary>
        <OperationsConsole workspace={slug} operations={catalog.data.operations} />
      </details>
    </section>
  );
}
