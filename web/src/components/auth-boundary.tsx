"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { readSession } from "@/lib/session";

export function AuthBoundary({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const publicRoute = pathname === "/login" || pathname === "/onboarding";
  const authenticated = publicRoute || Boolean(readSession()?.accessToken);

  useEffect(() => {
    if (!authenticated) {
      router.replace("/login" as never);
    }
  }, [authenticated, router]);

  if (publicRoute) {
    return <>{children}</>;
  }

  if (!authenticated) {
    return <div className="authLoading">Loading FlowForge...</div>;
  }

  return <>{children}</>;
}