"use client";

import { type FormEvent, type ReactNode, useEffect, useState, useSyncExternalStore } from "react";

import { replaceAccessToken } from "@/lib/session";

import { errorText, get, post } from "./client";
import { Card, Notice } from "./ui";

export type SecurityStatus = {
  email: string | null;
  email_verified: boolean;
  email_verification_required: boolean;
  mfa_enabled: boolean;
  mfa_required: boolean;
  recovery_codes_left: number;
};

// ------------------------------------------------------------------ shared status
let status: SecurityStatus | null = null;
let pending: Promise<void> | null = null;
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

/** Forget the signed-in person's status (at sign-out). */
export function resetSecurity(): void {
  status = null;
  pending = null;
}

export function reloadSecurity(): void {
  pending = get<SecurityStatus>("/api/v1/me/security")
    .then((s) => {
      status = s;
    })
    .catch(() => {
      status = null;
    })
    .finally(() => {
      pending = null;
      notify();
    });
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (!status && !pending) reloadSecurity();
  return () => listeners.delete(listener);
}

export function useSecurity(): SecurityStatus | null {
  return useSyncExternalStore(subscribe, () => status, () => null);
}

// ------------------------------------------------------------------ two-step setup
/** Set up the authenticator app; shows the recovery codes once when done. */
export function MfaSetup({ onDone }: { onDone?: () => void }) {
  const [secret, setSecret] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [codes, setCodes] = useState<string[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function start() {
    setBusy(true);
    setError("");
    try {
      setSecret(await post("/api/v1/me/mfa/setup"));
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  async function confirm(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await post<{ recovery_codes: string[]; access_token: string }>("/api/v1/me/mfa/enable", { code: code.trim() });
      replaceAccessToken(result.access_token); // this sign-in now counts as two-step
      setCodes(result.recovery_codes);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  if (codes) {
    return (
      <div data-testid="mfa-recovery">
        <Notice kind="ok">Two-step sign-in is on.</Notice>
        <p>
          <b>Save these recovery codes now</b> (print them or keep them in a password manager). Each one works once if you lose your phone. They will not be shown again.
        </p>
        <ul className="recoveryCodes">
          {codes.map((c) => (
            <li key={c}>
              <code>{c}</code>
            </li>
          ))}
        </ul>
        <button
          type="button"
          className="rwBtn primary"
          data-testid="mfa-done"
          onClick={() => {
            reloadSecurity();
            onDone?.();
          }}
        >
          I saved them
        </button>
      </div>
    );
  }

  if (!secret) {
    return (
      <div>
        <p>
          You will need an authenticator app on your phone (Google Authenticator, Microsoft Authenticator, 1Password, Authy...). Each sign-in then asks for the 6-digit code it shows, so a stolen password is not enough to get in.
        </p>
        {error ? <Notice kind="error">{error}</Notice> : null}
        <button type="button" className="rwBtn primary" disabled={busy} onClick={start} data-testid="mfa-start">
          Set up two-step sign-in
        </button>
      </div>
    );
  }

  const grouped = secret.secret.match(/.{1,4}/g)?.join(" ") ?? secret.secret;
  return (
    <form onSubmit={confirm} className="rwForm" data-testid="mfa-setup">
      <ol className="mfaSteps">
        <li>
          In your authenticator app, choose <b>Add account</b> → <b>Enter a setup key</b> (or open{" "}
          <a href={secret.otpauth_uri}>this link</a> on your phone).
        </li>
        <li>
          Account name: <b>Krov WorkAgent</b>. Key: <code data-testid="mfa-secret">{grouped}</code> (time-based).
        </li>
        <li>Type the 6-digit code the app shows:</li>
      </ol>
      <label>
        <span>Code</span>
        <input inputMode="numeric" autoComplete="one-time-code" value={code} onChange={(e) => setCode(e.target.value)} data-testid="mfa-code" />
      </label>
      {error ? <Notice kind="error">{error}</Notice> : null}
      <button type="submit" className="rwBtn primary" disabled={busy || code.trim().length < 6} data-testid="mfa-confirm">
        Turn on
      </button>
    </form>
  );
}

// ------------------------------------------------------------------ Settings card
export function SecurityCard() {
  const security = useSecurity();
  const [setup, setSetup] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [offCode, setOffCode] = useState("");

  async function changePassword(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    if (next.length < 12) return setMessage({ ok: false, text: "Use at least 12 characters." });
    try {
      const result = await post<{ access_token: string }>("/api/v1/me/password", { current_password: current, new_password: next });
      replaceAccessToken(result.access_token);
      setCurrent("");
      setNext("");
      setMessage({ ok: true, text: "Password changed. Every other sign-in has ended." });
    } catch (e) {
      setMessage({ ok: false, text: errorText(e) });
    }
  }

  async function turnOff() {
    setMessage(null);
    try {
      await post("/api/v1/me/mfa/disable", { code: offCode.trim() });
      setOffCode("");
      reloadSecurity();
    } catch (e) {
      setMessage({ ok: false, text: errorText(e) });
    }
  }

  return (
    <Card title="Your sign-in security" testId="security-card">
      {!security ? (
        <p className="rwMuted">Loading…</p>
      ) : (
        <>
          <h3>Two-step sign-in</h3>
          {security.mfa_enabled ? (
            <>
              <p data-testid="mfa-status">
                On. {security.recovery_codes_left} recovery codes left.
              </p>
              {security.mfa_required ? (
                <p className="rwMuted small">Your role requires it, so it stays on.</p>
              ) : (
                <div className="rwActions">
                  <input placeholder="Code to turn off" value={offCode} onChange={(e) => setOffCode(e.target.value)} aria-label="Code to turn off" />
                  <button type="button" className="rwBtn" onClick={turnOff} disabled={offCode.trim().length < 6}>
                    Turn off
                  </button>
                </div>
              )}
            </>
          ) : setup ? (
            <MfaSetup onDone={() => setSetup(false)} />
          ) : (
            <div className="rwActions">
              <p className="rwMuted">Off. Turn it on so a stolen password is not enough to get in.</p>
              <button type="button" className="rwBtn primary" onClick={() => setSetup(true)} data-testid="mfa-open-setup">
                Set up
              </button>
            </div>
          )}

          <h3>Email</h3>
          <p>
            {security.email} — {security.email_verified ? "confirmed" : "not confirmed yet"}
          </p>
          {!security.email_verified ? <ResendVerification /> : null}

          <h3>Change password</h3>
          <form onSubmit={changePassword} className="rwForm rwInlineForm">
            <label>
              <span>Current password</span>
              <input type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} />
            </label>
            <label>
              <span>New password (12+ characters)</span>
              <input type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} />
            </label>
            <button type="submit" className="rwBtn" disabled={!current || !next}>
              Change password
            </button>
          </form>
          {message ? <Notice kind={message.ok ? "ok" : "error"}>{message.text}</Notice> : null}
        </>
      )}
    </Card>
  );
}

function ResendVerification() {
  const [text, setText] = useState("");
  return (
    <div className="rwActions">
      <button
        type="button"
        className="rwBtn"
        data-testid="verify-resend"
        onClick={() =>
          post<{ status: string }>("/api/v1/me/email/resend")
            .then((r) => setText(r.status))
            .catch((e: unknown) => setText(errorText(e)))
        }
      >
        Send the confirmation email again
      </button>
      {text ? <span className="rwMuted small">{text}</span> : null}
    </div>
  );
}

// ------------------------------------------------------------------ app gate
/** Owners who still need two-step sign-in set it up first; unconfirmed emails get a banner. */
export function AccountGate({ children }: { children: ReactNode }) {
  const security = useSecurity();
  const [dismissed, setDismissed] = useState(false);
  useEffect(() => {
    if (!security) reloadSecurity();
  }, [security]);
  if (security?.mfa_required && !security.mfa_enabled) {
    return (
      <div className="rwWorkspace" data-testid="mfa-gate">
        <Card title="Protect your account first">
          <p>
            You manage people or billing, so Krov WorkAgent requires <b>two-step sign-in</b> for your account. It takes about a minute.
          </p>
          <MfaSetup />
        </Card>
      </div>
    );
  }
  return (
    <>
      {security && !security.email_verified && security.email_verification_required && !dismissed ? (
        <div className="verifyBanner" data-testid="verify-banner">
          <span>
            Please confirm your email (<b>{security.email}</b>). We sent you a link. Adding a card, connecting a bank and inviting people unlock after that.
          </span>
          <ResendVerification />
          <button type="button" className="rwLink" onClick={() => setDismissed(true)}>
            Hide
          </button>
        </div>
      ) : null}
      {children}
    </>
  );
}
