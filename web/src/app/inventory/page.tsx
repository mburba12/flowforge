"use client";

import { useMemo, useState } from "react";

type InventoryEvent = {
  id: string;
  at: string;
  type: "Purchase received" | "Sale fulfilled" | "Adjustment" | "Transfer in" | "Transfer out" | "Return received";
  quantity: number;
  balance: number;
  reference: string;
  location: string;
  user: string;
};

type Sku = {
  id: string;
  name: string;
  available: number;
  reorder: number;
  status: string;
  events: InventoryEvent[];
};

const skus: Sku[] = [
  {
    id: "VA-440", name: "Valve Assembly", available: 9, reorder: 25, status: "Critical",
    events: [
      { id: "EV-8142", at: "Nov 24, 2026 3:42 PM", type: "Sale fulfilled", quantity: -6, balance: 9, reference: "SO-6812", location: "Flushing Main", user: "Sam Rivera" },
      { id: "EV-8137", at: "Nov 24, 2026 10:18 AM", type: "Adjustment", quantity: -2, balance: 15, reference: "ADJ-402", location: "Flushing Main", user: "Maya Chen" },
      { id: "EV-8129", at: "Nov 23, 2026 4:05 PM", type: "Transfer out", quantity: -8, balance: 17, reference: "TR-2291", location: "Flushing Main", user: "Alex Morgan" },
      { id: "EV-8114", at: "Nov 22, 2026 11:30 AM", type: "Purchase received", quantity: 20, balance: 25, reference: "PO-2208", location: "Flushing Main", user: "Jordan Lee" },
      { id: "EV-8098", at: "Nov 21, 2026 2:16 PM", type: "Sale fulfilled", quantity: -12, balance: 5, reference: "SO-6788", location: "Flushing Main", user: "Sam Rivera" },
      { id: "EV-8076", at: "Nov 19, 2026 9:41 AM", type: "Return received", quantity: 3, balance: 17, reference: "RMA-318", location: "Flushing Main", user: "Maya Chen" },
      { id: "EV-8041", at: "Nov 15, 2026 1:55 PM", type: "Purchase received", quantity: 30, balance: 14, reference: "PO-2174", location: "Flushing Main", user: "Jordan Lee" },
    ],
  },
  {
    id: "MC-182", name: "Motor Controller", available: 64, reorder: 30, status: "Healthy",
    events: [
      { id: "EV-8140", at: "Nov 24, 2026 1:20 PM", type: "Sale fulfilled", quantity: -4, balance: 64, reference: "SO-6811", location: "Flushing Main", user: "Sam Rivera" },
      { id: "EV-8124", at: "Nov 23, 2026 8:42 AM", type: "Purchase received", quantity: 25, balance: 68, reference: "PO-2201", location: "Flushing Main", user: "Jordan Lee" },
      { id: "EV-8105", at: "Nov 22, 2026 9:10 AM", type: "Transfer in", quantity: 10, balance: 43, reference: "TR-2280", location: "Flushing Main", user: "Alex Morgan" },
      { id: "EV-8087", at: "Nov 20, 2026 3:35 PM", type: "Sale fulfilled", quantity: -8, balance: 33, reference: "SO-6799", location: "Flushing Main", user: "Sam Rivera" },
      { id: "EV-8063", at: "Nov 18, 2026 12:22 PM", type: "Adjustment", quantity: 1, balance: 41, reference: "ADJ-395", location: "Flushing Main", user: "Maya Chen" },
      { id: "EV-8034", at: "Nov 14, 2026 10:51 AM", type: "Purchase received", quantity: 40, balance: 40, reference: "PO-2168", location: "Flushing Main", user: "Jordan Lee" },
    ],
  },
  {
    id: "PC-900", name: "Pressure Coupler", available: 38, reorder: 20, status: "Healthy",
    events: [
      { id: "EV-8144", at: "Nov 24, 2026 4:14 PM", type: "Sale fulfilled", quantity: -5, balance: 38, reference: "SO-6813", location: "Flushing Main", user: "Sam Rivera" },
      { id: "EV-8132", at: "Nov 23, 2026 2:37 PM", type: "Return received", quantity: 2, balance: 43, reference: "RMA-321", location: "Flushing Main", user: "Maya Chen" },
      { id: "EV-8119", at: "Nov 22, 2026 3:02 PM", type: "Transfer out", quantity: -10, balance: 41, reference: "TR-2287", location: "Flushing Main", user: "Alex Morgan" },
      { id: "EV-8091", at: "Nov 21, 2026 9:46 AM", type: "Purchase received", quantity: 24, balance: 51, reference: "PO-2190", location: "Flushing Main", user: "Jordan Lee" },
      { id: "EV-8079", at: "Nov 19, 2026 1:18 PM", type: "Sale fulfilled", quantity: -7, balance: 27, reference: "SO-6774", location: "Flushing Main", user: "Sam Rivera" },
      { id: "EV-8050", at: "Nov 16, 2026 8:25 AM", type: "Adjustment", quantity: -1, balance: 34, reference: "ADJ-388", location: "Flushing Main", user: "Maya Chen" },
    ],
  },
];

function quantity(value: number) { return value > 0 ? `+${value}` : `${value}`; }

export default function InventoryPage() {
  const [selectedId, setSelectedId] = useState("VA-440");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [query, setQuery] = useState("");
  const selected = skus.find((sku) => sku.id === selectedId) ?? skus[0];
  const recent = selected.events.slice(0, 5);
  const visibleSkus = useMemo(() => skus.filter((sku) => `${sku.id} ${sku.name} ${sku.status}`.toLowerCase().includes(query.toLowerCase())), [query]);

  return (
    <main className="page inventory-page">
      <header className="pagehead"><div><small>OPERATIONS</small><h1>Inventory</h1><p>Monitor availability, reservations, movements, aging, and replenishment risk.</p></div><div className="page-actions"><button type="button" className="btn">Import</button><button type="button" className="btn primary">Adjust inventory</button></div></header>
      <section className="metrics"><article><span>Inventory value</span><strong>$1.84M</strong><small>+2.6%</small></article><article><span>Low stock</span><strong>12</strong><small>4 critical</small></article><article><span>Turnover</span><strong>6.8x</strong><small>+0.3x</small></article></section>

      <div className="inventory-layout">
        <section className="panel inventory-skus">
          <div className="panelhead"><div><h2>Stock items</h2><p>Select a SKU to review inventory activity.</p></div><input className="field" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search SKU or product" /></div>
          <div className="tablewrap"><table className="data"><thead><tr><th>SKU</th><th>Product</th><th className="right">Available</th><th className="right">Reorder point</th><th>Status</th></tr></thead><tbody>{visibleSkus.map((sku) => <tr key={sku.id} className={`clickable-row${sku.id === selected.id ? " selected" : ""}`} role="button" tabIndex={0} onClick={() => setSelectedId(sku.id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") setSelectedId(sku.id); }}><td><strong>{sku.id}</strong></td><td>{sku.name}</td><td className="right">{sku.available}</td><td className="right">{sku.reorder}</td><td><span className="status">{sku.status}</span></td></tr>)}</tbody></table></div>
        </section>

        <section className="panel inventory-history-card">
          <div className="panelhead"><div><small>SELECTED SKU</small><h2>{selected.id} Â· {selected.name}</h2><p>Five most recent inventory events</p></div><button type="button" className="btn" onClick={() => setHistoryOpen(true)}>View full history</button></div>
          <div className="inventory-event-list">{recent.map((event) => <article key={event.id} className="inventory-event"><span className={`inventory-event-icon ${event.quantity > 0 ? "in" : "out"}`}>{event.quantity > 0 ? "+" : "-"}</span><div><strong>{event.type}</strong><small>{event.at} Â· {event.reference}</small><span>{event.location}</span></div><div className="inventory-event-qty"><strong>{quantity(event.quantity)}</strong><small>Balance {event.balance}</small></div></article>)}</div>
        </section>
      </div>

      {historyOpen && <div className="inventory-history-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setHistoryOpen(false); }}><section className="inventory-history-drawer" role="dialog" aria-modal="true"><header><div><small>INVENTORY HISTORY</small><h2>{selected.id} Â· {selected.name}</h2><p>{selected.events.length} demonstration events</p></div><button type="button" className="iconbtn" onClick={() => setHistoryOpen(false)}>X</button></header><div className="tablewrap"><table className="data"><thead><tr><th>Date and time</th><th>Event</th><th>Reference</th><th>Location</th><th>User</th><th className="right">Change</th><th className="right">Balance</th></tr></thead><tbody>{selected.events.map((event) => <tr key={event.id}><td>{event.at}</td><td>{event.type}</td><td>{event.reference}</td><td>{event.location}</td><td>{event.user}</td><td className={`right inventory-qty ${event.quantity > 0 ? "positive" : "negative"}`}>{quantity(event.quantity)}</td><td className="right"><strong>{event.balance}</strong></td></tr>)}</tbody></table></div><footer><button type="button" className="btn" onClick={() => window.print()}>Print history</button><button type="button" className="btn primary" onClick={() => setHistoryOpen(false)}>Done</button></footer></section></div>}
    </main>
  );
}