"use client";

import { useEffect, useRef } from "react";

type Turnstile = { render: (el: HTMLElement, options: Record<string, unknown>) => string; remove: (id: string) => void };
declare global {
  interface Window {
    turnstile?: Turnstile;
  }
}

/**
 * Cloudflare Turnstile ("are you a person?") when the server has a site key; renders
 * nothing otherwise. Calls onToken with the check's answer (or "" when it expires).
 */
export function BotCheck({ onToken }: { onToken: (token: string) => void }) {
  const box = useRef<HTMLDivElement>(null);
  const callback = useRef(onToken);
  useEffect(() => {
    callback.current = onToken;
  }, [onToken]);

  useEffect(() => {
    let widget = "";
    let cancelled = false;
    (async () => {
      const response = await fetch("/api/flowforge/api/v1/auth/config", { cache: "no-store" });
      const config = (await response.json().catch(() => ({}))) as { turnstile_site_key?: string | null };
      const siteKey = config.turnstile_site_key;
      if (!siteKey || cancelled || !box.current) return;
      if (!window.turnstile) {
        await new Promise<void>((resolve, reject) => {
          const script = document.createElement("script");
          script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
          script.async = true;
          script.onload = () => resolve();
          script.onerror = () => reject(new Error("bot check did not load"));
          document.head.appendChild(script);
        });
      }
      if (cancelled || !box.current || !window.turnstile) return;
      widget = window.turnstile.render(box.current, {
        sitekey: siteKey,
        callback: (token: string) => callback.current(token),
        "expired-callback": () => callback.current(""),
      });
    })().catch(() => undefined);
    return () => {
      cancelled = true;
      if (widget && window.turnstile) window.turnstile.remove(widget);
    };
  }, []);

  return <div ref={box} className="botCheck" data-testid="bot-check" />;
}
