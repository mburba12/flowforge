$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$Components = Join-Path $Web "src\components"
$TopbarPath = Join-Path $Components "topbar.tsx"
$SearchPath = Join-Path $Components "global-search.tsx"
$CssPath = Join-Path $Web "src\app\globals.css"

foreach ($Path in @($TopbarPath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Search = @'
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { Route } from "next";
import { AppIcon } from "@/components/app-icon";
import { navigation } from "@/lib/navigation";

type SearchItem = {
  id: string;
  title: string;
  description: string;
  category: "Page" | "Record" | "Person" | "Action";
  href?: Route;
  keywords: string;
};

const records: SearchItem[] = [
  { id: "record-inv-2098", title: "INV-2098", description: "Riverbend Medical - $28,400 overdue", category: "Record", href: "/ar", keywords: "invoice receivable overdue customer riverbend medical 28400" },
  { id: "record-bill-1048", title: "BILL-1048", description: "Northstar Components - $18,420 pending approval", category: "Record", href: "/ap", keywords: "bill payable vendor northstar components approval 18420" },
  { id: "record-so-6812", title: "SO-6812", description: "Atlas Motion - $42,900 ready to ship", category: "Record", href: "/orders", keywords: "sales order atlas motion fulfillment shipping 42900" },
  { id: "record-va-440", title: "VA-440", description: "Valve Assembly - critical low stock", category: "Record", href: "/inventory", keywords: "inventory sku valve assembly low stock critical" },
  { id: "record-pr-2026-24", title: "PR-2026-24", description: "Payroll run - November 29 pay date", category: "Record", href: "/payroll", keywords: "payroll run november pay date 284920" },
  { id: "record-tax-1041", title: "TAX-1041", description: "Michigan sales and use tax - due December 20", category: "Record", href: "/tax", keywords: "tax michigan sales use filing deadline 18470" },
  { id: "person-maya", title: "Maya Chen", description: "Owner - Reconciliation", category: "Person", href: "/work-queue", keywords: "maya chen reconciliation owner employee" },
  { id: "person-sam", title: "Sam Rivera", description: "Owner - Inventory", category: "Person", href: "/work-queue", keywords: "sam rivera inventory owner employee" },
];

const actions: SearchItem[] = [
  { id: "action-create", title: "Create a record", description: "Open the dashboard creation workflow", category: "Action", href: "/dashboard", keywords: "create add new record" },
  { id: "action-approvals", title: "Review approvals", description: "Open pending approvals", category: "Action", href: "/approvals", keywords: "review approve reject pending" },
  { id: "action-work", title: "View my work", description: "Open priority tasks and exceptions", category: "Action", href: "/work-queue", keywords: "work queue task exception assigned" },
  { id: "action-ai", title: "Open FlowForge AI", description: "Use the minimized AI launcher in the lower-right corner", category: "Action", keywords: "ai assistant chatbot flowforge" },
];

const pages: SearchItem[] = navigation.map((item) => ({
  id: `page-${item.href}`,
  title: item.label,
  description: `Open the ${item.label} workspace`,
  category: "Page",
  href: item.href,
  keywords: `${item.label} ${item.group}`.toLowerCase(),
}));

const catalog = [...pages, ...records, ...actions];

export function GlobalSearch() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);

  const results = useMemo(() => {
    const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (!terms.length) return [...actions.slice(0, 3), ...pages.slice(0, 5)];
    return catalog
      .map((item) => {
        const haystack = `${item.title} ${item.description} ${item.keywords} ${item.category}`.toLowerCase();
        const score = terms.reduce((total, term) => total + (haystack.includes(term) ? (item.title.toLowerCase().includes(term) ? 4 : 1) : -10), 0);
        return { item, score };
      })
      .filter(({ score }) => score >= 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10)
      .map(({ item }) => item);
  }, [query]);

  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
        window.setTimeout(() => inputRef.current?.focus(), 0);
      }
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);

  useEffect(() => setActive(0), [query]);

  function select(item: SearchItem) {
    setOpen(false);
    setQuery("");
    if (item.id === "action-ai") {
      const button = document.querySelector<HTMLButtonElement>(".ai-launcher");
      button?.click();
      return;
    }
    if (item.href) router.push(item.href);
  }

  function keyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") { event.preventDefault(); setActive((value) => Math.min(value + 1, results.length - 1)); }
    if (event.key === "ArrowUp") { event.preventDefault(); setActive((value) => Math.max(value - 1, 0)); }
    if (event.key === "Enter" && results[active]) { event.preventDefault(); select(results[active]); }
  }

  return (
    <div className="global-search-wrap">
      <label className="search" onClick={() => setOpen(true)}>
        <AppIcon name="search" className="top-icon" />
        <input ref={inputRef} value={query} onFocus={() => setOpen(true)} onChange={(event) => setQuery(event.target.value)} onKeyDown={keyDown} placeholder="Search records, people, or actions..." aria-label="Global search" />
        <button type="button" className="shortcut" onClick={() => { setOpen(true); inputRef.current?.focus(); }}>Ctrl K</button>
      </label>

      {open && (
        <>
          <button type="button" className="search-dismiss" aria-label="Close search" onClick={() => setOpen(false)} />
          <section className="search-results" aria-label="Search results">
            <div className="search-results-head"><strong>{query ? `Results for "${query}"` : "Quick access"}</strong><span>{results.length} results</span></div>
            <div className="search-result-list">
              {results.map((item, index) => (
                <button type="button" className={`search-result ${index === active ? "active" : ""}`} key={item.id} onMouseEnter={() => setActive(index)} onClick={() => select(item)}>
                  <span className={`search-category ${item.category.toLowerCase()}`}>{item.category.slice(0, 1)}</span>
                  <span className="search-result-text"><strong>{item.title}</strong><small>{item.description}</small></span>
                  <span className="search-result-category">{item.category}</span>
                </button>
              ))}
              {!results.length && <div className="search-empty"><strong>No results found</strong><span>Try a page, invoice, customer, person, or action.</span></div>}
            </div>
            <div className="search-help"><span>Up/Down navigate</span><span>Enter open</span><span>Esc close</span></div>
          </section>
        </>
      )}
    </div>
  );
}
'@
[IO.File]::WriteAllText($SearchPath, $Search, [Text.UTF8Encoding]::new($false))

$Topbar = @'
"use client";

import { AppIcon } from "@/components/app-icon";
import { GlobalSearch } from "@/components/global-search";

export function Topbar() {
  return (
    <header className="topbar">
      <GlobalSearch />
      <div className="topactions">
        <button className="iconbtn" type="button" title="Notifications" aria-label="Notifications"><AppIcon name="notifications" className="top-icon" /></button>
        <button className="iconbtn" type="button" title="Help" aria-label="Help"><AppIcon name="help" className="top-icon" /></button>
        <div className="avatar" title="User account">MB</div>
      </div>
    </header>
  );
}
'@
[IO.File]::WriteAllText($TopbarPath, $Topbar, [Text.UTF8Encoding]::new($false))

$CssText = Get-Content -LiteralPath $CssPath -Raw
if ($CssText -notmatch '\.search-results') {
$CssText += @'

.global-search-wrap{position:relative;width:min(620px,58vw)}.global-search-wrap .search{width:100%;position:relative;z-index:72}.shortcut{border:0;background:transparent;cursor:pointer}.search-dismiss{position:fixed;inset:0;z-index:70;border:0;background:#1118272e}.search-results{position:absolute;left:0;right:0;top:51px;z-index:75;background:white;border:1px solid var(--line);border-radius:14px;box-shadow:0 24px 70px #17203333;overflow:hidden}.search-results-head{display:flex;justify-content:space-between;padding:13px 15px;border-bottom:1px solid var(--line);font-size:11px}.search-results-head span{color:var(--muted)}.search-result-list{max-height:430px;overflow:auto;padding:6px}.search-result{width:100%;display:flex;align-items:center;gap:11px;border:0;background:white;padding:10px;border-radius:9px;text-align:left;cursor:pointer;color:var(--text)}.search-result:hover,.search-result.active{background:#f0f3ff}.search-category{width:29px;height:29px;min-width:29px;border-radius:8px;display:grid;place-items:center;background:#e8edff;color:#3859d7;font-size:10px;font-weight:900}.search-category.record{background:#e8f7f0;color:#138a61}.search-category.person{background:#fff1dd;color:#b96b08}.search-category.action{background:#f0eafe;color:#6942bb}.search-result-text{display:grid;gap:3px;min-width:0;flex:1}.search-result-text strong{font-size:12px}.search-result-text small{color:var(--muted);font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.search-result-category{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.search-empty{display:grid;gap:6px;text-align:center;padding:35px;color:var(--muted);font-size:11px}.search-help{display:flex;gap:18px;padding:9px 14px;border-top:1px solid var(--line);background:#f8f9fc;color:var(--muted);font-size:9px}@media(max-width:680px){.global-search-wrap{width:68vw}.search-results{position:fixed;left:7px;right:7px;top:62px}.search-result-category{display:none}}
'@
}
[IO.File]::WriteAllText($CssPath, $CssText, [Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Global search TypeScript validation failed." }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Global search unit tests failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Global search production build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE GLOBAL SEARCH PASSED" -ForegroundColor Green
