$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$WebRoot = Join-Path $ProjectRoot "web"
$ChartPath = Join-Path $WebRoot "src\components\cash-flow-chart.tsx"
$SettingsPath = Join-Path $WebRoot "src\app\settings\page.tsx"
$CssPath = Join-Path $WebRoot "src\app\globals.css"

foreach ($Path in @($ChartPath, $SettingsPath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$Chart = @'
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
'@

[IO.File]::WriteAllText($ChartPath, $Chart, [Text.UTF8Encoding]::new($false))

$Settings = Get-Content -LiteralPath $SettingsPath -Raw
$OldSecurity = '{active.key === "security" && <div className="settings-list"><div><strong>Multi-factor authentication</strong><span>Required for administrators and high-risk actions</span><b className="settings-good">Enforced</b></div><div><strong>Session timeout</strong><span>30 minutes of inactivity</span><b className="settings-good">Active</b></div><div><strong>Forced row-level security</strong><span>Tenant isolation at the PostgreSQL layer</span><b className="settings-good">268 tables</b></div><div><strong>High-risk execution</strong><span>Production financial execution remains disabled</span><b className="settings-warn">Disabled</b></div></div>}'
$NewSecurity = @'
{active.key === "security" && <div className="settings-list">
  <label className="settings-toggle"><span><strong>Multi-factor authentication</strong><small>Require MFA for administrators and high-risk actions</small></span><input type="checkbox" defaultChecked /></label>
  <label className="settings-control-row"><span><strong>Session timeout</strong><small>End inactive sessions automatically</small></span><select defaultValue="30"><option value="15">15 minutes</option><option value="30">30 minutes</option><option value="60">60 minutes</option><option value="120">2 hours</option></select></label>
  <div><strong>Forced row-level security</strong><span>Tenant isolation at the PostgreSQL layer</span><b className="settings-good">268 tables</b></div>
  <label className="settings-toggle"><span><strong>High-risk execution</strong><small>Allow production financial execution after launch gates pass</small></span><input type="checkbox" disabled title="Locked until production launch gates pass" /></label>
  <div className="settings-security-note">Forced RLS and high-risk execution cannot be weakened from the browser. RLS is database-enforced, and high-risk execution remains locked until server-side launch evidence is approved.</div>
</div>}
'@

if ($Settings.Contains($OldSecurity)) {
    $Settings = $Settings.Replace($OldSecurity, $NewSecurity)
} elseif ($Settings -notmatch 'settings-control-row') {
    throw "The current Security settings block was not found."
}
[IO.File]::WriteAllText($SettingsPath, $Settings, [Text.UTF8Encoding]::new($false))

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.cash-chart-controls') {
$Css += @'

.cash-chart-controls{display:flex;align-items:end;justify-content:space-between;gap:14px;margin:0 0 12px 48px}.cash-chart-controls label{display:grid;gap:5px}.cash-chart-controls label span,.cash-chart-controls div small{font-size:9px;color:var(--muted);font-weight:750;text-transform:uppercase;letter-spacing:.05em}.cash-chart-controls select{min-width:190px;border:1px solid var(--line);border-radius:8px;background:white;padding:8px 30px 8px 10px;color:var(--text);font-weight:700}.cash-chart-controls div{text-align:right}.cash-chart-controls div strong{display:block;font-size:15px;margin-top:3px}.settings-control-row{display:flex!important;align-items:center!important;gap:12px!important;border:1px solid var(--line)!important;border-radius:10px!important;padding:14px!important}.settings-control-row>span{display:block}.settings-control-row strong,.settings-control-row small{display:block}.settings-control-row small{font-size:10px;color:var(--muted);margin-top:3px}.settings-control-row select{margin-left:auto;border:1px solid var(--line);border-radius:8px;padding:8px;background:white;font-weight:700}@media(max-width:680px){.cash-chart-controls{margin-left:42px;align-items:stretch;flex-direction:column}.cash-chart-controls div{text-align:left}.cash-chart-controls select{width:100%}}
'@
}
[IO.File]::WriteAllText($CssPath, $Css, [Text.UTF8Encoding]::new($false))

Push-Location $WebRoot
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Editable security/adaptive chart typecheck failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Editable security/adaptive chart build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE EDITABLE SECURITY AND ADAPTIVE CHART PASSED" -ForegroundColor Green
