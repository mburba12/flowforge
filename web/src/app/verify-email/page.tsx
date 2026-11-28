"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { clearFragment, fragmentValues, messageFrom, postJson, readJson } from "@/lib/signin";

/** Confirms the email address from the emailed link (#token=...). */
export default function VerifyEmailPage() {
  const [message, setMessage] = useState("Confirming your email...");
  const [ok, setOk] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const token = fragmentValues().get("token") ?? "";
    clearFragment();
    (async () => {
      const response = await postJson("/api/v1/auth/email/verify", { token });
      const payload = await readJson(response);
      if (!response.ok) throw new Error(messageFrom(payload, "This link is no longer valid."));
      setOk(true);
      setMessage("Your email is confirmed. Thank you!");
    })().catch((e: unknown) => setMessage(e instanceof Error ? e.message : "This link is no longer valid."));
  }, []);

  return (
    <main className="loginPage">
      <section className="loginCard" aria-labelledby="verify-title">
        <div className="loginBrand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/krov-workagent-logo.svg" alt="Krov WorkAgent" width={230} height={40} />
        </div>
        <h1 id="verify-title">Confirm your email</h1>
        <p data-testid="verify-status">{message}</p>
        <p className="loginAlt">
          <Link href={(ok ? "/modules/dashboard" : "/login") as never}>{ok ? "Open Krov WorkAgent" : "Back to sign in"}</Link>
        </p>
      </section>
    </main>
  );
}
