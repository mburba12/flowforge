"use client";

import { useMemo, useState } from "react";

type AccountSeries = {
  id: string;
  name: string;
  currency: "USD";
  values: number[];
};

const labels = ["Oct 27", "Oct 30", "Nov 2", "Nov 5", "Nov 8", "Nov 11", "Nov 14", "Nov 17", "Nov 20", "Nov 23", "Nov 24", "Nov 26"];

const accounts: AccountSeries[] = [
  { id: "operating", name: "Operating account", currency: "USD", values: [42000, 55000, 47000, 63000, 58000, 71000, 68000, 76000, 61000, 83000, 78000, 88000] },
  { id: "payroll", name: "Payroll account", currency: "USD", values: [18500, 17600, 22100, 19800, 24600, 20900, 27400, 23100, 28600, 24900, 31200, 26700] },
  { id: "tax", name: "Tax reserve", currency: "USD", values: [6800, 9200, 11800, 14500, 17200, 20100, 22900, 25400, 28100, 30700, 33800, 36500] },
  { id: "all", name: "All cash accounts", currency: "USD", values: [67300, 81800, 83100, 97300, 99800, 112000, 118300, 124500, 117700, 144000, 143000, 151200] },
];

function niceCeiling(value: number) {
  if (value <= 0) return 1000;
  const roughStep = value / 4;
  const magnitude = 10 ** Math.floor(Math.log10(roughStep));
  const residual = roughStep / magnitude;
  const niceResidual = residual <= 1 ? 1 : residual <= 2 ? 2 : residual <= 2.5 ? 2.5 : residual <= 5 ? 5 : 10;
  const step = niceResidual * magnitude;
  return Math.ceil(value / step) * step;
}

function formatAxis(value: number) {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(value % 1000000 === 0 ? 0 : 1)}m`;
  if (value >= 1000) return `$${Math.round(value / 1000)}k`;
  return `$${value}`;
}

const dollars = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export function CashFlowChart() {
  const [accountId, setAccountId] = useState("operating");
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const account = accounts.find((item) => item.id === accountId) ?? accounts[0];

  const maximum = useMemo(() => niceCeiling(Math.max(...account.values) * 1.08), [account.values]);
  const ticks = useMemo(() => [maximum, maximum * 0.75, maximum * 0.5, maximum * 0.25, 0], [maximum]);

  return (
    <div className="cash-chart" aria-label={`${account.name} cash balance in US dollars`}>
      <div className="cash-chart-controls">
        <label>
          <span>Account</span>
          <select value={accountId} onChange={(event) => { setAccountId(event.target.value); setActiveIndex(null); }}>
            {accounts.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
          </select>
        </label>
        <div><small>Current balance</small><strong>{dollars.format(account.values.at(-1) ?? 0)}</strong></div>
      </div>
      <div className="cash-chart-y-title">Cash balance (USD)</div>
      <div className="cash-chart-layout">
        <div className="cash-chart-axis" aria-hidden="true">{ticks.map((tick) => <span key={tick}>{formatAxis(tick)}</span>)}</div>
        <div className="cash-chart-plot">
          <div className="cash-chart-grid" aria-hidden="true">{ticks.map((tick) => <span key={tick} />)}</div>
          <div className="cash-chart-bars">
            {account.values.map((amount, index) => {
              const percentage = (amount / maximum) * 100;
              const active = activeIndex === index;
              return (
                <button
                  type="button"
                  className={`cash-chart-bar-wrap${active ? " active" : ""}`}
                  key={`${account.id}-${labels[index]}`}
                  aria-label={`${account.name}, ${labels[index]}: ${dollars.format(amount)}`}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(null)}
                  onFocus={() => setActiveIndex(index)}
                  onBlur={() => setActiveIndex(null)}
                >
                  {active && <span className="cash-chart-tooltip" role="tooltip" style={{ bottom: `calc(28px + ${percentage}% - 10px)` }}><strong>{dollars.format(amount)}</strong><small>{labels[index]} | {account.name}</small></span>}
                  <span className="cash-chart-bar" style={{ height: `${percentage}%` }} />
                  <span className="cash-chart-x-label">{index % 2 === 0 || index === account.values.length - 1 ? labels[index] : ""}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
