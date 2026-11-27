"use client";

import { LogoutButton } from "@/components/logout-button";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AppIcon } from "@/components/app-icon";
import { GlobalSearch } from "@/components/global-search";

import { ProblemReportForm } from "@/components/problem-report-form";
type Menu = "notifications" | "help" | "profile" | null;

const notifications = [
  { id: "n1", title: "Payment batch needs approval", detail: "8 vendor payments are waiting", href: "/approvals", unread: true },
  { id: "n2", title: "Inventory exception", detail: "VA-440 is below reorder point", href: "/inventory", unread: true },
  { id: "n3", title: "Tax deadline approaching", detail: "Michigan sales tax is due Dec 20", href: "/tax", unread: false },
];

export function Topbar() {
  const router = useRouter();
  const areaRef = useRef<HTMLDivElement>(null);
  const [menu, setMenu] = useState<Menu>(null);
  const [items, setItems] = useState(notifications);
  const [reportOpen, setReportOpen] = useState(false);

  const unread = items.filter((item) => item.unread).length;

  useEffect(() => {
    function closeOutside(event: MouseEvent) {
      if (!areaRef.current?.contains(event.target as Node)) setMenu(null);
    }
    function closeEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMenu(null);
    }
    document.addEventListener("mousedown", closeOutside);
    window.addEventListener("keydown", closeEscape);
    return () => {
      document.removeEventListener("mousedown", closeOutside);
      window.removeEventListener("keydown", closeEscape);
    };
  }, []);

  function navigate(href: string) {
    setMenu(null);
    router.push(href as never);
  }

  return (
    <header className="topbar">
      <GlobalSearch />
      <div className="topactions" ref={areaRef}>
        <div className="top-control-wrap">
          <button
            className={`iconbtn ${menu === "notifications" ? "active" : ""}`}
            type="button"
            title="Notifications"
            aria-label={`Notifications, ${unread} unread`}
            aria-expanded={menu === "notifications"}
            onClick={() => setMenu((current) => current === "notifications" ? null : "notifications")}
          >
            <AppIcon name="notifications" className="top-icon" />
            {unread > 0 && <span className="notification-badge">{unread}</span>}
          </button>
          {menu === "notifications" && (
            <section className="top-popover notifications-popover" role="dialog" aria-label="Notifications">
              <div className="top-popover-head"><div><strong>Notifications</strong><small>{unread} unread</small></div><button type="button" onClick={() => setItems((current) => current.map((item) => ({ ...item, unread: false })))}>Mark all read</button></div>
              <div className="notification-list">
                {items.map((item) => (
                  <button type="button" className={`notification-item ${item.unread ? "unread" : ""}`} key={item.id} onClick={() => { setItems((current) => current.map((value) => value.id === item.id ? { ...value, unread: false } : value)); navigate(item.href); }}>
                    <span className="notification-dot" />
                    <span><strong>{item.title}</strong><small>{item.detail}</small></span>
                  </button>
                ))}
              </div>
              <button type="button" className="top-popover-footer" onClick={() => navigate("/work-queue")}>View all work</button>
            </section>
          )}
        </div>

        <div className="top-control-wrap">
          <button
            className={`iconbtn ${menu === "help" ? "active" : ""}`}
            type="button"
            title="Help"
            aria-label="Help and support"
            aria-expanded={menu === "help"}
            onClick={() => setMenu((current) => current === "help" ? null : "help")}
          >
            <AppIcon name="help" className="top-icon" />
          </button>
          {menu === "help" && (
            <section className="top-popover help-popover" role="dialog" aria-label="Help and support">
              <div className="top-popover-head"><div><strong>Help & support</strong><small>FlowForge local environment</small></div></div>
              <button type="button" className="help-item" onClick={() => navigate("/support")}><strong>Help center</strong><small>Guides, training, and common workflows</small></button>
              <button type="button" className="help-item" onClick={() => { setMenu(null); setReportOpen(true); }}><strong>Report an issue</strong><small>Send a problem report to the FlowForge team</small></button>
              <div className="help-version">FlowForge web 5.1.0</div>
            </section>
          )}
        </div>

        <div className="top-control-wrap">
          <button
            className={`avatar avatar-button ${menu === "profile" ? "active" : ""}`}
            type="button"
            title="User account"
            aria-label="Open user account menu"
            aria-expanded={menu === "profile"}
            onClick={() => setMenu((current) => current === "profile" ? null : "profile")}
          >MB</button>
          {menu === "profile" && (
            <section className="top-popover profile-popover" role="dialog" aria-label="User account">
              <div className="profile-summary"><div className="avatar large">MB</div><div><strong>Mack Burba</strong><small>Local development account</small><span>Apex Manufacturing</span></div></div>
              <button type="button" className="profile-item" onClick={() => navigate("/settings")}>Account settings</button>
              <button type="button" className="profile-item" onClick={() => navigate("/settings")}>Security & permissions</button>
              <button type="button" className="profile-item" onClick={() => navigate("/integrations")}>Connected services</button>
              <div className="profile-boundary">Company access is determined by the authenticated server session. Tenant switching is not available.</div>
              <button type="button" className="profile-item danger" onClick={() => { setMenu(null); window.location.assign("/dashboard"); }}>Reset local session</button>
            </section>
          )}
        </div>
      </div>
      <ProblemReportForm open={reportOpen} onClose={() => setReportOpen(false)} />
    </header>
  );
}
