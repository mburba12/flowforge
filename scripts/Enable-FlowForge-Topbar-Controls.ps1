$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$TopbarPath = Join-Path $Web "src\components\topbar.tsx"
$CssPath = Join-Path $Web "src\app\globals.css"

foreach ($Path in @($TopbarPath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Topbar = @'
"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AppIcon } from "@/components/app-icon";
import { GlobalSearch } from "@/components/global-search";

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
              <button type="button" className="help-item" onClick={() => window.open("http://127.0.0.1:8000/docs", "_blank", "noopener,noreferrer")}><strong>API documentation</strong><small>Open local FastAPI Swagger documentation</small></button>
              <button type="button" className="help-item" onClick={() => navigate("/support")}><strong>Report an issue</strong><small>Open a local support request</small></button>
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
    </header>
  );
}
'@

[System.IO.File]::WriteAllText($TopbarPath, $Topbar, [System.Text.UTF8Encoding]::new($false))

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.top-control-wrap') {
$Css += @'

.top-control-wrap{position:relative}.iconbtn.active,.avatar-button.active{border-color:#9eb0ec;background:#eef2ff}.avatar-button{border:0;cursor:pointer}.notification-badge{position:absolute;right:-3px;top:-4px;min-width:17px;height:17px;padding:0 4px;border-radius:999px;background:#d83b4f;color:white;display:grid;place-items:center;font-size:9px;font-weight:900;border:2px solid white}.top-popover{position:absolute;right:0;top:48px;z-index:90;width:360px;background:white;border:1px solid var(--line);border-radius:14px;box-shadow:0 22px 65px #17203330;overflow:hidden}.top-popover-head{display:flex;align-items:center;justify-content:space-between;padding:15px 16px;border-bottom:1px solid var(--line)}.top-popover-head strong,.top-popover-head small{display:block}.top-popover-head small{color:var(--muted);font-size:10px;margin-top:3px}.top-popover-head button{border:0;background:transparent;color:var(--primary);font-size:10px;font-weight:750;cursor:pointer}.notification-list{padding:6px}.notification-item{width:100%;display:flex;gap:10px;border:0;background:white;padding:11px;border-radius:9px;text-align:left;cursor:pointer}.notification-item:hover{background:#f4f6fb}.notification-item strong,.notification-item small{display:block}.notification-item strong{font-size:11px}.notification-item small{font-size:10px;color:var(--muted);margin-top:4px}.notification-dot{width:8px;height:8px;min-width:8px;border-radius:50%;background:#c9d0df;margin-top:4px}.notification-item.unread .notification-dot{background:var(--primary)}.notification-item.unread{background:#f6f8ff}.top-popover-footer{width:100%;border:0;border-top:1px solid var(--line);background:#fafbfe;color:var(--primary);padding:11px;font-size:10px;font-weight:800;cursor:pointer}.help-popover{width:330px}.help-item{width:100%;display:grid;gap:3px;border:0;border-bottom:1px solid #eef0f5;background:white;padding:13px 16px;text-align:left;cursor:pointer}.help-item:hover,.profile-item:hover{background:#f4f6fb}.help-item strong{font-size:11px}.help-item small{font-size:10px;color:var(--muted)}.help-version{padding:10px 16px;color:var(--muted);font-size:9px;background:#fafbfe}.profile-popover{width:320px}.profile-summary{display:flex;gap:12px;padding:16px;border-bottom:1px solid var(--line)}.avatar.large{width:44px;height:44px;min-width:44px}.profile-summary strong,.profile-summary small,.profile-summary span{display:block}.profile-summary strong{font-size:12px}.profile-summary small,.profile-summary span{font-size:10px;color:var(--muted);margin-top:3px}.profile-item{width:100%;border:0;border-bottom:1px solid #eef0f5;background:white;padding:12px 16px;text-align:left;font-size:11px;font-weight:700;cursor:pointer}.profile-item.danger{color:#b42336}.profile-boundary{padding:12px 16px;background:#fff8e8;color:#80530a;font-size:9px;line-height:1.45}@media(max-width:680px){.top-popover{position:fixed;left:7px;right:7px;top:63px;width:auto}}
'@
}
[System.IO.File]::WriteAllText($CssPath, $Css, [System.Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Topbar control TypeScript validation failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Topbar control production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE TOPBAR CONTROLS PASSED" -ForegroundColor Green
