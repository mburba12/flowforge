"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { BotCheck } from "@/components/bot-check";
import { messageFrom, postJson, readJson } from "@/lib/signin";

/** Ask for a password reset link (the answer never reveals whether an email has an account). */
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [bot, setBot] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await postJson("/api/v1/auth/password/forgot", { email: email.trim().toLowerCase(), turnstile_token: bot || null });
      const payload = await readJson(response);
      if (!response.ok) throw new Error(messageFrom(payload, "Could not send the link. Try again in a few minutes."));
      setSent(String(payload.status ?? "If that email has an account, a reset link is on its way."));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not send the link.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="loginPage">
      <section className="loginCard" aria-labelledby="forgot-title">
        <div className="loginBrand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/krov-workagent-logo.svg" alt="Krov WorkAgent" width={230} height={40} />
        </div>
        <h1 id="forgot-title">Reset your password</h1>
        {sent ? (
          <p data-testid="forgot-sent">{sent} Check your email; the link works for 30 minutes.</p>
        ) : (
          <form onSubmit={submit} noValidate>
            <p>Enter your email and we will send you a link to choose a new password.</p>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required disabled={busy} autoFocus />
            <BotCheck onToken={setBot} />
            {error ? <div className="loginError" role="alert">{error}</div> : null}
            <button type="submit" disabled={busy || !email.includes("@")}>
              {busy ? "Sending..." : "Send reset link"}
            </button>
          </form>
        )}
        <p className="loginAlt">
          <Link href={"/login" as never}>Back to sign in</Link>
        </p>
      </section>
    </main>
  );
}
