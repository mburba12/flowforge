"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { AppIcon } from "@/components/app-icon";
import { labelOf, navGroups } from "@/lib/modules";
import { clearSession } from "@/lib/session";
import { SectionFiles } from "@/release/files";

/** Signed-in chrome: grouped sidebar (specialist tools folded away) and a slim top bar. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  if (path === "/login" || path === "/onboarding" || path.startsWith("/connections/")) return <>{children}</>;
  const current = path.startsWith("/modules/") ? path.split("/")[2] : "";
  const inMoreTools = navGroups.some((g) => g.collapsed && g.items.some(([slug]) => slug === current));

  return (
    <div className={open ? "shell navOpen" : "shell"}>
      <aside className="side">
        <Link className="brand" href={"/modules/dashboard" as never} onClick={() => setOpen(false)}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="brandLogo" src="/krov-workagent-logo.svg" alt="Krov WorkAgent" width={172} height={30} />
        </Link>
        <nav aria-label="Main">
          {navGroups.map((group, index) => {
            const links = group.items.map(([slug, label, icon]) => {
              const href = `/modules/${slug}`;
              return (
                <Link
                  key={slug}
                  className={current === slug ? "active" : ""}
                  aria-current={current === slug ? "page" : undefined}
                  href={href as never}
                  onClick={() => setOpen(false)}
                >
                  <AppIcon name={icon} />
                  <span>{label}</span>
                </Link>
              );
            });
            if (group.collapsed) {
              return (
                <details key={index} className="navMore" open={inMoreTools || undefined}>
                  <summary>{group.label}</summary>
                  {links}
                </details>
              );
            }
            return (
              <div key={index} className="navGroup">
                {group.label ? <span className="navLabel">{group.label}</span> : null}
                {links}
              </div>
            );
          })}
        </nav>
      </aside>
      <div className="main">
        <header>
          <button type="button" className="navToggle" aria-label="Menu" onClick={() => setOpen((o) => !o)}>
            ☰
          </button>
          <b className="topTitle">{current ? labelOf(current) : "Krov WorkAgent"}</b>
          <SectionFiles key={current} section={current} />
          <button
            type="button"
            onClick={() => {
              clearSession();
              router.replace("/login" as never);
              router.refresh();
            }}
          >
            Log out
          </button>
        </header>
        {children}
      </div>
      {open ? <div className="navScrim" onClick={() => setOpen(false)} /> : null}
    </div>
  );
}
