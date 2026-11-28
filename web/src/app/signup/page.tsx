"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { readSession } from "@/lib/session";
import { clearFragment, finishSignIn, fragmentValues, messageFrom, postJson, readJson } from "@/lib/signin";

const PLANS = [
  { value: "starter", label: "Starter · $199/month" },
  { value: "business", label: "Business · $499/month" },
];

/** Public sign-up: a new workspace with this person as its owner, then straight in. */
export default function SignupPage() {
  const router = useRouter();
  const [plan, setPlan] = useState("starter");
  const [organization, setOrganization] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (readSession()?.accessToken) {
      router.replace("/modules/dashboard" as never);
      return;
    }
    // From the website's Sign up page (address fragment, never sent to a server).
    // The address fragment exists only in the browser (after hydration), so it is read here.
    /* eslint-disable react-hooks/set-state-in-effect */
    const given = fragmentValues();
    clearFragment();
    const wanted = given.get("plan");
    if (wanted && PLANS.some((p) => p.value === wanted)) setPlan(wanted);
    if (given.get("company")) setOrganization(given.get("company") ?? "");
    if (given.get("email")) setEmail(given.get("email") ?? "");
    if (given.get("name")) setName(given.get("name") ?? "");
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError("");
    if (!organization.trim() || !name.trim() || !email.trim()) return setError("Fill in every field.");
    if (password.length < 12) return setError("Use a password of at least 12 characters.");
    if (password !== confirm) return setError("The two passwords are different.");
    setBusy(true);
    try {
      const response = await postJson("/api/v1/auth/signup", {
        organization: organization.trim(),
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
        plan,
      });
      const payload = await readJson(response);
      if (!response.ok) throw new Error(messageFrom(payload, `Sign-up failed (${response.status}).`));
      await finishSignIn(payload);
      router.replace("/modules/dashboard" as never);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to create the account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="loginPage">
      <section className="loginCard" aria-labelledby="signup-title">
        <div className="loginBrand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/krov-workagent-logo.svg" alt="Krov WorkAgent" width={230} height={40} />
        </div>
        <h1 id="signup-title">Create your account</h1>
        <p>Your own Krov WorkAgent workspace. You are its administrator.</p>
        <form onSubmit={submit} noValidate data-testid="signup-form">
          <label htmlFor="plan">Plan</label>
          <select id="plan" value={plan} onChange={(e) => setPlan(e.target.value)} disabled={busy}>
            {PLANS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>

          <label htmlFor="organization">Business name</label>
          <input id="organization" value={organization} onChange={(e) => setOrganization(e.target.value)} autoComplete="organization" required disabled={busy} />

          <label htmlFor="name">Your name</label>
          <input id="name" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" required disabled={busy} />

          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required disabled={busy} />

          <label htmlFor="password">Password (at least 12 characters)</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required minLength={12} disabled={busy} />

          <label htmlFor="confirm">Repeat password</label>
          <input id="confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required disabled={busy} />

          {error ? <div className="loginError" role="alert" aria-live="assertive">{error}</div> : null}
          <button type="submit" disabled={busy}>
            {busy ? "Creating your workspace..." : "Create account"}
          </button>
        </form>
        <p className="loginAlt">
          Already have an account? <Link href={"/login" as never}>Sign in</Link>
        </p>
      </section>
    </main>
  );
}
