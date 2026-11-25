$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$WebRoot = Join-Path $ProjectRoot "web"
$DashboardPath = Join-Path $WebRoot "src\app\dashboard\page.tsx"
$ComponentPath = Join-Path $WebRoot "src\components\cash-flow-chart.tsx"
$CssPath = Join-Path $WebRoot "src\app\globals.css"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

foreach ($Path in @($DashboardPath, $CssPath, $Python)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Component = @'
"use client";

import { useState } from "react";

const data = [
  { label: "Oct 27", amount: 42000 },
  { label: "Oct 30", amount: 55000 },
  { label: "Nov 2", amount: 47000 },
  { label: "Nov 5", amount: 63000 },
  { label: "Nov 8", amount: 58000 },
  { label: "Nov 11", amount: 71000 },
  { label: "Nov 14", amount: 68000 },
  { label: "Nov 17", amount: 76000 },
  { label: "Nov 20", amount: 61000 },
  { label: "Nov 23", amount: 83000 },
  { label: "Nov 24", amount: 78000 },
  { label: "Nov 26", amount: 88000 },
];

const ticks = [100000, 75000, 50000, 25000, 0];
const maximum = 100000;

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function compactDollars(value: number) {
  if (value === 0) return "$0";
  return `$${value / 1000}k`;
}

export function CashFlowChart() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  return (
    <div className="cash-chart" aria-label="Cash flow outlook in US dollars">
      <div className="cash-chart-y-title">Cash balance (USD)</div>
      <div className="cash-chart-layout">
        <div className="cash-chart-axis" aria-hidden="true">
          {ticks.map((tick) => <span key={tick}>{compactDollars(tick)}</span>)}
        </div>
        <div className="cash-chart-plot">
          <div className="cash-chart-grid" aria-hidden="true">
            {ticks.map((tick) => <span key={tick} />)}
          </div>
          <div className="cash-chart-bars">
            {data.map((point, index) => {
              const active = activeIndex === index;
              return (
                <button
                  type="button"
                  className={`cash-chart-bar-wrap${active ? " active" : ""}`}
                  key={`${point.label}-${point.amount}`}
                  aria-label={`${point.label}: ${currency.format(point.amount)}`}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(null)}
                  onFocus={() => setActiveIndex(index)}
                  onBlur={() => setActiveIndex(null)}
                >
                  {active && (
                    <span className="cash-chart-tooltip" role="tooltip" style={{ bottom: `calc(28px + ${(point.amount / maximum) * 100}% - 10px)` }}>
                      <strong>{currency.format(point.amount)}</strong>
                      <small>{point.label}</small>
                    </span>
                  )}
                  <span
                    className="cash-chart-bar"
                    style={{ height: `${(point.amount / maximum) * 100}%` }}
                  />
                  <span className="cash-chart-x-label">{index % 2 === 0 || index === data.length - 1 ? point.label : ""}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
'@

[System.IO.File]::WriteAllText(
    $ComponentPath,
    $Component,
    [System.Text.UTF8Encoding]::new($false)
)

$env:FLOWFORGE_DASHBOARD_PATH = $DashboardPath
@'
import os
import re
from pathlib import Path

path = Path(os.environ["FLOWFORGE_DASHBOARD_PATH"])
text = path.read_text(encoding="utf-8")

import_line = 'import { CashFlowChart } from "@/components/cash-flow-chart";'
if import_line not in text:
    imports = list(re.finditer(r'^import .*?;\s*$', text, flags=re.MULTILINE))
    if imports:
        position = imports[-1].end()
        text = text[:position] + "\n" + import_line + text[position:]
    elif text.startswith('"use client";'):
        position = len('"use client";')
        text = text[:position] + "\n\n" + import_line + text[position:]
    else:
        text = import_line + "\n" + text

if "<CashFlowChart />" not in text:
    patterns = [
        r'<div\s+className="chart">\s*\{\s*\[42,\s*55,\s*47,\s*63,\s*58,\s*71,\s*68,\s*76,\s*61,\s*83,\s*78,\s*88\].*?</div>',
        r'<div\s+className="chart">.*?</div>',
    ]
    updated = text
    for pattern in patterns:
        updated, count = re.subn(pattern, '<CashFlowChart />', updated, count=1, flags=re.DOTALL)
        if count:
            break
    else:
        raise RuntimeError("Cash flow chart markup was not found in dashboard/page.tsx")
    text = updated

path.write_text(text.rstrip() + "\n", encoding="utf-8")
print("PATCHED: dashboard cash flow chart")
'@ | & $Python -

if ($LASTEXITCODE -ne 0) {
    throw "Dashboard cash flow chart patch failed."
}

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.cash-chart-layout') {
    $Css += @'

.cash-chart{position:relative;padding:4px 2px 0}.cash-chart-y-title{margin:0 0 8px 48px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.cash-chart-layout{display:grid;grid-template-columns:48px minmax(0,1fr);height:300px}.cash-chart-axis{display:flex;flex-direction:column;justify-content:space-between;align-items:flex-end;padding:0 10px 28px 0;color:var(--muted);font-size:10px;font-weight:700}.cash-chart-plot{position:relative;min-width:0}.cash-chart-grid{position:absolute;inset:0 0 28px;display:flex;flex-direction:column;justify-content:space-between;pointer-events:none}.cash-chart-grid span{display:block;border-top:1px solid #dfe4ef}.cash-chart-grid span:last-child{border-top-color:#cdd5e4}.cash-chart-bars{position:absolute;inset:0 0 0;display:grid;grid-template-columns:repeat(12,minmax(18px,1fr));gap:10px;align-items:end}.cash-chart-bar-wrap{position:relative;height:100%;border:0;background:transparent;padding:0 0 28px;display:flex;align-items:flex-end;justify-content:center;cursor:pointer;min-width:0}.cash-chart-bar{display:block;width:100%;max-width:54px;min-height:2px;border-radius:7px 7px 0 0;background:linear-gradient(180deg,#657deb 0%,#3e5bd7 100%);box-shadow:0 0 0 1px #3453ce18;transition:filter .15s ease,transform .15s ease}.cash-chart-bar-wrap:hover .cash-chart-bar,.cash-chart-bar-wrap:focus-visible .cash-chart-bar,.cash-chart-bar-wrap.active .cash-chart-bar{filter:brightness(.88);transform:translateY(-2px)}.cash-chart-bar-wrap:focus-visible{outline:2px solid #3157d5;outline-offset:3px;border-radius:8px}.cash-chart-x-label{position:absolute;bottom:5px;left:50%;transform:translateX(-50%);white-space:nowrap;color:var(--muted);font-size:9px;font-weight:650}.cash-chart-tooltip{position:absolute;z-index:5;top:auto;transform:translateY(-10px);background:#172033;color:white;border-radius:8px;padding:8px 10px;box-shadow:0 10px 28px #17203344;white-space:nowrap;pointer-events:none}.cash-chart-tooltip:after{content:"";position:absolute;left:50%;bottom:-5px;transform:translateX(-50%);border:5px solid transparent;border-top-color:#172033;border-bottom:0}.cash-chart-tooltip strong,.cash-chart-tooltip small{display:block}.cash-chart-tooltip strong{font-size:11px}.cash-chart-tooltip small{font-size:9px;color:#cbd3e5;margin-top:2px}@media(max-width:760px){.cash-chart-layout{height:250px;grid-template-columns:42px minmax(0,1fr)}.cash-chart-bars{gap:5px}.cash-chart-x-label{display:none}.cash-chart-axis{padding-right:7px}.cash-chart-y-title{margin-left:42px}}
'@
}

# Position each tooltip above its actual bar using the same percentage.
$Css = $Css.Replace(
    'className={`cash-chart-bar-wrap${active ? " active" : ""}`}',
    'className={`cash-chart-bar-wrap${active ? " active" : ""}`}'
)

[System.IO.File]::WriteAllText(
    $CssPath,
    $Css,
    [System.Text.UTF8Encoding]::new($false)
)

Push-Location $WebRoot
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Cash flow chart TypeScript validation failed." }

    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Cash flow chart production build failed." }
}
finally {
    Pop-Location
}

Write-Host "FLOWFORGE CASH FLOW CHART PASSED" -ForegroundColor Green
