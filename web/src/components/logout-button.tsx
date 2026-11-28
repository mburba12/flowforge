"use client";

import { useRouter } from "next/navigation";

export function LogoutButton() {
  const router = useRouter();

  function logout() {
    sessionStorage.clear();

    for (const key of Object.keys(localStorage)) {
      if (key.startsWith("flowforge")) {
        localStorage.removeItem(key);
      }
    }

    document.cookie =
      "flowforge_session=; Path=/; Max-Age=0; SameSite=Lax";

    router.replace("/onboarding");
    router.refresh();
  }

  return (
    <button
      type="button"
      onClick={logout}
      aria-label="Log out of Krov WorkAgent"
      style={{
        position: "fixed",
        top: "16px",
        right: "20px",
        zIndex: 10000,
        padding: "9px 14px",
        border: "1px solid #475569",
        borderRadius: "8px",
        background: "#172033",
        color: "#ffffff",
        fontWeight: 600,
        cursor: "pointer",
      }}
    >
      Log out
    </button>
  );
}