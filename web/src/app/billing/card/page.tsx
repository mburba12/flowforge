"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { errorText, post } from "@/release/client";

/** Stripe sends the customer back here after they saved a card on Stripe's page. */
export default function CardSavedPage() {
  const router = useRouter();
  const [message, setMessage] = useState("Saving your card…");
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const sessionId = new URLSearchParams(window.location.search).get("session_id") ?? "";
    post("/api/v1/account-billing/card/complete", { session_id: sessionId })
      .then(() => router.replace("/modules/plan" as never))
      .catch((e: unknown) => setMessage(`The card was not saved: ${errorText(e)}`));
  }, [router]);

  return (
    <div className="rwWorkspace">
      <p data-testid="card-saved-status">{message}</p>
    </div>
  );
}
