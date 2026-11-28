"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { readSession } from "@/lib/session";
import { clearFragment, finishSignIn, fragmentValues, messageFrom, postJson, readJson } from "@/lib/signin";

type Workspace = { slug: string; name: string };

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspace, setWorkspace] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (readSession()?.accessToken) {
      router.replace("/modules/dashboard" as never);
      return;
    }
    // From the website's Log in page: the email arrives in the address fragment.
    // The address fragment exists only in the browser (after hydration), so it is read here.
    /* eslint-disable react-hooks/set-state-in-effect */
    const given = fragmentValues().get("email");
    clearFragment();
    if (given) {
      setEmail(given);
      passwordRef.current?.focus();
    } else {
      emailRef.current?.focus();
    }
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await postJson("/api/v1/auth/login", {
        email: email.trim().toLowerCase(),
        password,
        ...(workspace ? { tenant_slug: workspace } : {}),
      });
      const payload = await readJson(response);
      const detail = payload.detail as { code?: string; workspaces?: Workspace[] } | undefined;
      if (response.status === 409 && detail?.code === "workspace_required") {
        setWorkspaces(detail.workspaces ?? []);
        setWorkspace(detail.workspaces?.[0]?.slug ?? "");
        throw new Error("This email opens more than one workspace. Choose one and sign in again.");
      }
      if (response.status === 401) throw new Error("The email or password is not right.");
      if (!response.ok) throw new Error(messageFrom(payload, `Sign-in failed (${response.status}).`));
      await finishSignIn(payload);
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
        <div className="loginBrand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/krov-workagent-logo.svg" alt="Krov WorkAgent" width={230} height={40} />
        </div>
        <span className="loginTag">One platform. Every business operation.</span>
        <h1 id="login-title">Sign in</h1>
        <p>Sign in to your Krov WorkAgent workspace.</p>
        <form onSubmit={submit} noValidate>
          <label htmlFor="email">Email</label>
          <input ref={emailRef} id="email" type="email" value={email} onChange={(e) => { setEmail(e.target.value); setWorkspaces([]); setWorkspace(""); }} autoComplete="username" required disabled={busy} />

          <label htmlFor="password">Password</label>
          <div style={{ display: "flex", gap: 8 }}>
            <input ref={passwordRef} id="password" style={{ flex: 1 }} type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required disabled={busy} />
            <button type="button" onClick={() => setShowPassword((value) => !value)} disabled={busy} aria-label={showPassword ? "Hide password" : "Show password"}>
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>

          {workspaces.length > 1 ? (
            <>
              <label htmlFor="workspace">Workspace</label>
              <select id="workspace" value={workspace} onChange={(e) => setWorkspace(e.target.value)} disabled={busy}>
                {workspaces.map((w) => (
                  <option key={w.slug} value={w.slug}>
                    {w.name}
                  </option>
                ))}
              </select>
            </>
          ) : null}

          {error ? <div className="loginError" role="alert" aria-live="assertive">{error}</div> : null}
          <button type="submit" disabled={busy}>
            {busy ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <p className="loginAlt">
          New to Krov WorkAgent? <Link href={"/signup" as never}>Create an account</Link>
        </p>
      </section>
    </main>
  );
}
