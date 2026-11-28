"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { readSession, tokenFromResponse, writeSession } from "@/lib/session";

type JsonObject = Record<string, unknown>;

const DEFAULT_TENANT = "flowforge-production";

function messageFrom(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.trim()) return value;
  if (Array.isArray(value)) {
    const messages = value
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) return String((item as { msg: unknown }).msg);
        return "";
      })
      .filter(Boolean);
    if (messages.length) return messages.join(" ");
  }
  if (value && typeof value === "object") {
    if ("detail" in value) return messageFrom((value as { detail: unknown }).detail, fallback);
    if ("message" in value) return messageFrom((value as { message: unknown }).message, fallback);
  }
  return fallback;
}

async function readJson(response: Response): Promise<JsonObject> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as JsonObject;
  } catch {
    throw new Error(`FlowForge returned an invalid response (${response.status}).`);
  }
}

export default function LoginPage() {
  const router = useRouter();
  const [tenantSlug, setTenantSlug] = useState(DEFAULT_TENANT);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (readSession()?.accessToken) router.replace("/modules/dashboard" as never);
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");

    try {
      const response = await fetch("/api/flowforge/api/v1/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
          tenant_slug: tenantSlug.trim().toLowerCase(),
        }),
      });

      const payload = await readJson(response);
      if (!response.ok) throw new Error(messageFrom(payload, `Sign-in failed (${response.status}).`));

      const accessToken = tokenFromResponse(payload);
      const tokenType = typeof payload.token_type === "string" ? payload.token_type : "bearer";

      const me = await fetch("/api/flowforge/api/v1/me", {
        headers: { authorization: `Bearer ${accessToken}`, accept: "application/json" },
      });
      if (!me.ok) {
        const detail = await readJson(me);
        throw new Error(messageFrom(detail, "The account signed in, but identity verification failed."));
      }

      const user: JsonObject = await readJson(me);
      const candidate = user.tenant_id ?? user.tenantId ?? user.organization_id ?? user.organizationId;
      const tenantId = typeof candidate === "string" ? candidate : undefined;

      writeSession({ accessToken, tokenType, tenantId, user });
      router.replace("/modules/dashboard" as never);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="loginPage">
      <section className="loginCard" aria-labelledby="login-title">
        <div className="loginBrand">FlowForge</div>
        <span className="loginTag">One platform. Every business operation.</span>
        <h1 id="login-title">Sign in</h1>
        <p>Access the FlowForge Production workspace.</p>
        <form onSubmit={submit} noValidate>
          <label htmlFor="tenant">Workspace</label>
          <input id="tenant" value={tenantSlug} onChange={(e) => setTenantSlug(e.target.value)} autoComplete="organization" required disabled={busy} />

          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required disabled={busy} />

          <label htmlFor="password">Password</label>
          <div style={{ display: "flex", gap: 8 }}>
            <input id="password" style={{ flex: 1 }} type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required disabled={busy} autoFocus />
            <button type="button" onClick={() => setShowPassword((value) => !value)} disabled={busy} aria-label={showPassword ? "Hide password" : "Show password"}>
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>

          {error ? <div className="loginError" role="alert" aria-live="assertive">{error}</div> : null}
          <button type="submit" onClick={() => setError("")} disabled={busy}>
            {busy ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}