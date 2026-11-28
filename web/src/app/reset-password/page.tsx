"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { clearFragment, fragmentValues, messageFrom, postJson, readJson } from "@/lib/signin";

/** Choose a new password from the emailed link (#token=...). */
export default function ResetPasswordPage() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // The link's token is in the address fragment, which only the browser can read; it is
    // removed from the address bar right away. Also handles a link opened in this same tab.
    const read = () => {
      const given = fragmentValues().get("token");
      if (given) setToken(given);
      clearFragment();
    };
    read();
    window.addEventListener("hashchange", read);
    return () => window.removeEventListener("hashchange", read);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError("");
    if (password.length < 12) return setError("Use at least 12 characters.");
    if (password !== confirm) return setError("The two passwords are different.");
    setBusy(true);
    try {
      const response = await postJson("/api/v1/auth/password/reset", { token, password });
      const payload = await readJson(response);
      if (!response.ok) throw new Error(messageFrom(payload, "This link is no longer valid. Please ask for a new one."));
      setDone(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not change the password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="loginPage">
      <section className="loginCard" aria-labelledby="reset-title">
        <div className="loginBrand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/krov-workagent-logo.svg" alt="Krov WorkAgent" width={230} height={40} />
        </div>
        <h1 id="reset-title">Choose a new password</h1>
        {done ? (
          <p data-testid="reset-done">
            Your password is changed and every other sign-in has ended. <Link href={"/login" as never}>Sign in</Link>
          </p>
        ) : !token ? (
          <p>
            This page needs the link from your email. <Link href={"/forgot-password" as never}>Ask for a new link</Link>
          </p>
        ) : (
          <form onSubmit={submit} noValidate>
            <label htmlFor="password">New password (at least 12 characters)</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required disabled={busy} autoFocus />
            <label htmlFor="confirm">Repeat new password</label>
            <input id="confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required disabled={busy} />
            {error ? <div className="loginError" role="alert">{error}</div> : null}
            <button type="submit" disabled={busy}>
              {busy ? "Saving..." : "Change password"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
