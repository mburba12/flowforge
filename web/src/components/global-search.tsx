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