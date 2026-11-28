"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

import { readSession } from "@/lib/session";

const noSubscription = () => () => {};

/**
 * Signed-in gate. The session lives in sessionStorage, which the server cannot see, so
 * the first render (server and hydration) is the neutral loading state; the browser then
 * switches to the page or the sign-in redirect. Reading storage during the first render
 * made server and browser HTML differ (React hydration error #418).
 */
export function AuthBoundary({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const publicRoute = pathname === "/login" || pathname === "/onboarding";
  // undefined while hydrating, null when signed out, the token when signed in.
  const token = useSyncExternalStore(
    noSubscription,
    () => readSession()?.accessToken ?? null,
    () => undefined,
  );

  useEffect(() => {
    if (!publicRoute && token === null) {
      router.replace("/login" as never);
    }
  }, [publicRoute, token, router]);

  if (publicRoute || token) {
    return <>{children}</>;
  }
  return <div className="authLoading">Loading FlowForge...</div>;
}
