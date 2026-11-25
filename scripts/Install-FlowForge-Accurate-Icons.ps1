$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$WebSrc = Join-Path $Root "web\src"
$Components = Join-Path $WebSrc "components"
$NavigationPath = Join-Path $WebSrc "lib\navigation.ts"
$SidebarPath = Join-Path $Components "sidebar.tsx"
$TopbarPath = Join-Path $Components "topbar.tsx"
$AiPath = Join-Path $Components "flowforge-ai.tsx"
$CssPath = Join-Path $WebSrc "app\globals.css"

foreach ($Path in @($NavigationPath, $SidebarPath, $TopbarPath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Icons = @'
import type { SVGProps } from "react";

export type IconName =
  | "dashboard" | "approvals" | "work-queue" | "ap" | "ar" | "ledger"
  | "banking" | "tax" | "orders" | "inventory" | "shipping" | "payroll"
  | "workforce" | "documents" | "reconciliation" | "entities" | "reports"
  | "audit" | "integrations" | "billing" | "settings" | "support"
  | "search" | "notifications" | "help" | "spark";

const paths: Record<IconName, React.ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  approvals: <><path d="M9 11l2 2 4-5"/><path d="M6 3h12v18H6z"/><path d="M9 17h6"/></>,
  "work-queue": <><path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></>,
  ap: <><path d="M4 19h16"/><path d="M7 16v-5M12 16V8M17 16V5"/><path d="M14 5h3v3"/></>,
  ar: <><path d="M4 5h16"/><path d="M7 8v5M12 8v8M17 8v11"/><path d="M14 19h3v-3"/></>,
  ledger: <><path d="M4 4h16v16H4z"/><path d="M8 4v16M8 9h12M8 14h12"/></>,
  banking: <><path d="M3 9l9-5 9 5"/><path d="M5 10h14M6 10v8M10 10v8M14 10v8M18 10v8M4 20h16"/></>,
  tax: <><circle cx="7" cy="7" r="3"/><circle cx="17" cy="17" r="3"/><path d="M5 19L19 5"/></>,
  orders: <><path d="M4 7l8-4 8 4-8 4z"/><path d="M4 7v10l8 4 8-4V7M12 11v10"/></>,
  inventory: <><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 9v11M16 9v11"/></>,
  shipping: <><path d="M3 6h11v11H3zM14 10h4l3 3v4h-7z"/><circle cx="7" cy="19" r="2"/><circle cx="17" cy="19" r="2"/></>,
  payroll: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h3M8 15h8M14 10v4M12 12h4"/></>,
  workforce: <><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2"/><path d="M3 20c0-4 3-7 6-7s6 3 6 7M14 14c3 0 6 2 6 6"/></>,
  documents: <><path d="M6 3h9l4 4v14H6z"/><path d="M15 3v5h5M9 12h7M9 16h7"/></>,
  reconciliation: <><path d="M4 8h14l-3-3M20 16H6l3 3"/><path d="M18 8l-3 3M6 16l3-3"/></>,
  entities: <><circle cx="12" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/><path d="M10 8L7 15M14 8l3 7M9 18h6"/></>,
  reports: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>,
  audit: <><circle cx="10" cy="10" r="6"/><path d="M14.5 14.5L21 21M8 10l2 2 4-5"/></>,
  integrations: <><path d="M8 3v5H3M16 3v5h5M8 21v-5H3M16 21v-5h5"/><rect x="8" y="8" width="8" height="8" rx="2"/></>,
  billing: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9L7 7M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/></>,
  support: <><circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.5 2.5 0 114.2 1.8c-1.2.9-2 1.3-2 3.2M12 18h.01"/></>,
  search: <><circle cx="10" cy="10" r="6"/><path d="M15 15l6 6"/></>,
  notifications: <><path d="M6 17h12l-2-3V9a4 4 0 00-8 0v5z"/><path d="M10 20h4"/></>,
  help: <><circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.5 2.5 0 114.2 1.8c-1.2.9-2 1.3-2 3.2M12 18h.01"/></>,
  spark: <><path d="M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z"/><path d="M19 16l.7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z"/></>,
};

export function AppIcon({ name, ...props }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}
'@
[IO.File]::WriteAllText((Join-Path $Components "app-icon.tsx"), $Icons, [Text.UTF8Encoding]::new($false))

$Navigation = @'
import type { NavItem } from "./types";

export const navigation: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "dashboard", group: "Overview" },
  { label: "Approvals", href: "/approvals", icon: "approvals", group: "Overview", badge: 8 },
  { label: "Work queue", href: "/work-queue", icon: "work-queue", group: "Overview", badge: 14 },
  { label: "Accounts payable", href: "/ap", icon: "ap", group: "Finance" },
  { label: "Accounts receivable", href: "/ar", icon: "ar", group: "Finance" },
  { label: "General ledger", href: "/finance", icon: "ledger", group: "Finance" },
  { label: "Banking & treasury", href: "/banking", icon: "banking", group: "Finance" },
  { label: "Tax", href: "/tax", icon: "tax", group: "Finance" },
  { label: "Orders", href: "/orders", icon: "orders", group: "Operations" },
  { label: "Inventory", href: "/inventory", icon: "inventory", group: "Operations" },
  { label: "Shipping", href: "/shipping", icon: "shipping", group: "Operations" },
  { label: "Payroll", href: "/payroll", icon: "payroll", group: "People" },
  { label: "Workforce", href: "/workforce", icon: "workforce", group: "People" },
  { label: "Documents", href: "/documents", icon: "documents", group: "Intelligence" },
  { label: "Reconciliation", href: "/reconciliation", icon: "reconciliation", group: "Intelligence", badge: 5 },
  { label: "Entities", href: "/entities", icon: "entities", group: "Intelligence" },
  { label: "Reports", href: "/reports", icon: "reports", group: "Insights" },
  { label: "Audit", href: "/audit", icon: "audit", group: "Insights" },
  { label: "Integrations", href: "/integrations", icon: "integrations", group: "Admin" },
  { label: "Billing", href: "/billing", icon: "billing", group: "Admin" },
  { label: "Settings", href: "/settings", icon: "settings", group: "Admin" },
  { label: "Support", href: "/support", icon: "support", group: "Admin" },
];
'@
[IO.File]::WriteAllText($NavigationPath, $Navigation, [Text.UTF8Encoding]::new($false))

$Sidebar = @'
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AppIcon, type IconName } from "@/components/app-icon";
import { navigation } from "@/lib/navigation";

export function Sidebar() {
  const path = usePathname();
  const groups = [...new Set(navigation.map((item) => item.group))];

  return (
    <aside className="sidebar">
      <div className="brand"><div className="brandmark">F</div><span>FlowForge</span></div>
      <div className="company"><small>Company</small><strong>Apex Manufacturing</strong></div>
      {groups.map((group) => <div key={group}>
        <div className="navgroup">{group}</div>
        {navigation.filter((item) => item.group === group).map((item) => (
          <Link className={`navitem ${path === item.href ? "active" : ""}`} href={item.href} key={item.href}>
            <span className="navicon"><AppIcon name={item.icon as IconName} /></span>
            <span>{item.label}</span>
            {item.badge && <span className="badge">{item.badge}</span>}
          </Link>
        ))}
      </div>)}
    </aside>
  );
}
'@
[IO.File]::WriteAllText($SidebarPath, $Sidebar, [Text.UTF8Encoding]::new($false))

$Topbar = @'
"use client";

import { useState } from "react";
import { AppIcon } from "@/components/app-icon";

export function Topbar() {
  const [query, setQuery] = useState("");
  return <header className="topbar">
    <label className="search"><AppIcon name="search" className="top-icon"/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search records, people, or actions..."/><span className="shortcut">Ctrl K</span></label>
    <div className="topactions"><button className="iconbtn" type="button" title="Notifications" aria-label="Notifications"><AppIcon name="notifications" className="top-icon"/></button><button className="iconbtn" type="button" title="Help" aria-label="Help"><AppIcon name="help" className="top-icon"/></button><div className="avatar">MB</div></div>
  </header>;
}
'@
[IO.File]::WriteAllText($TopbarPath, $Topbar, [Text.UTF8Encoding]::new($false))

if (Test-Path -LiteralPath $AiPath) {
  $Ai = Get-Content -LiteralPath $AiPath -Raw
  if ($Ai -notmatch 'app-icon') {
    $Ai = $Ai.Replace('import { FormEvent, useState } from "react";', 'import { FormEvent, useState } from "react";`nimport { AppIcon } from "@/components/app-icon";')
  }
  $Ai = [regex]::Replace($Ai, '<span className="ai-spark">.*?</span>', '<span className="ai-spark"><AppIcon name="spark" /></span>')
  [IO.File]::WriteAllText($AiPath, $Ai, [Text.UTF8Encoding]::new($false))
}

$Css = Get-Content -LiteralPath $CssPath -Raw
$Css += @'

.navicon{width:24px;height:24px;min-width:24px;display:grid;place-items:center;color:#aeb8ca}.navicon svg{width:18px;height:18px}.navitem.active .navicon,.navitem:hover .navicon{color:white}.top-icon{width:17px;height:17px}.ai-spark{display:grid;place-items:center;width:24px;height:24px}.ai-spark svg{width:19px;height:19px}.shortcut{white-space:nowrap;color:#7a8497;font-size:10px;font-weight:700}
'@
[IO.File]::WriteAllText($CssPath, $Css, [Text.UTF8Encoding]::new($false))

Push-Location (Join-Path $Root "web")
try {
  npm run typecheck
  if ($LASTEXITCODE -ne 0) { throw "Accurate icon TypeScript validation failed." }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "Accurate icon production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE ACCURATE ICONS PASSED" -ForegroundColor Green
