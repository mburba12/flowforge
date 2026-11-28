"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { errorText, post } from "@/release/client";

type Migration = { id: string; company_name: string | null; summary: Record<string, number> };

/** Gusto sends the user back here after they approve access; finish the connection and import. */
export default function PayrollCallbackPage() {
  const [state, setState] = useState<{ done: boolean; text: string; ok: boolean }>({ done: false, ok: true, text: "Connecting to Gusto…" });
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const oauthState = params.get("state");
    const denied = params.get("error");
    void (async () => {
      if (denied || !code || !oauthState) {
        setState({ done: true, ok: false, text: "Gusto access was not granted, so nothing was imported." });
        return;
      }
      try {
        const connected = await post<Migration>("/api/v1/payroll-migration/gusto/complete", { code, state: oauthState });
        setState({ done: false, ok: true, text: `Connected to ${connected.company_name ?? "Gusto"}. Copying employees and this year's payrolls…` });
        const result = await post<Migration>(`/api/v1/payroll-migration/imports/${connected.id}/sync`, {});
        const s = result.summary;
        setState({
          done: true,
          ok: true,
          text: `Imported from ${result.company_name ?? "Gusto"}: ${s.employees_created ?? 0} employees added, ${s.employees_updated ?? 0} updated, ${s.ytd_balances ?? 0} year-to-date balances.`,
        });
      } catch (error) {
        setState({ done: true, ok: false, text: errorText(error) });
      }
    })();
  }, []);

  return (
    <main className="callbackPage">
      <section className="rwCard">
        <div className="rwCardBody">
          <h1>Move payroll from Gusto</h1>
          <div className={`rwNotice ${state.done ? (state.ok ? "ok" : "error") : "info"}`} role="status">
            {state.text}
          </div>
          {state.done ? (
            <Link className="rwBtn primary" href={"/modules/payroll" as never}>
              Back to Payroll
            </Link>
          ) : null}
        </div>
      </section>
    </main>
  );
}
