$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$PagePath = Join-Path $Web "src\app\settings\page.tsx"
$CssPath = Join-Path $Web "src\app\globals.css"

if (-not (Test-Path -LiteralPath $PagePath)) { throw "Run from the FlowForge project root." }

$Page = @'
"use client";

import { FormEvent, useState } from "react";

type PanelKey = "company" | "entities" | "roles" | "approvals" | "notifications" | "security";

type Panel = {
  key: PanelKey;
  title: string;
  description: string;
};

const panels: Panel[] = [
  { key: "company", title: "Company profile", description: "Review the authenticated company profile and business details." },
  { key: "entities", title: "Legal entities", description: "Maintain legal entities, registrations, currencies, and reporting status." },
  { key: "roles", title: "Roles & permissions", description: "Review permission bundles and separation-of-duties controls." },
  { key: "approvals", title: "Approval policies", description: "Configure approval thresholds, escalation, and dual-control rules." },
  { key: "notifications", title: "Notifications", description: "Choose in-app, email, and Microsoft Teams notification preferences." },
  { key: "security", title: "Security", description: "Review MFA, session, audit, and high-risk action protections." },
];

export default function SettingsPage() {
  const [active, setActive] = useState<Panel | null>(null);
  const [saved, setSaved] = useState("");
  const [company, setCompany] = useState({ legalName: "Apex Manufacturing", displayName: "Apex Manufacturing", taxId: "XX-XXX1041", timezone: "America/Detroit" });
  const [notifications, setNotifications] = useState({ inApp: true, email: true, teams: false });

  function close() { setActive(null); }
  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(`${active?.title ?? "Settings"} saved locally`);
    close();
    window.setTimeout(() => setSaved(""), 3000);
  }

  return (
    <main className="page settings-page">
      <header className="pagehead"><div><small>ADMINISTRATION</small><h1>Settings</h1><p>Configure company, entities, permissions, workflows, notifications, and security.</p></div></header>
      <section className="settings-grid">
        {panels.map((panel) => (
          <article className="settings-card" id={panel.key} key={panel.key}>
            <h2>{panel.title}</h2><p>{panel.description}</p>
            <button type="button" className="btn" onClick={() => setActive(panel)}>Open</button>
          </article>
        ))}
      </section>

      {saved && <div className="settings-toast" role="status">{saved}</div>}

      {active && (
        <div className="settings-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}>
          <section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-title">
            <header><div><small>SETTINGS</small><h2 id="settings-title">{active.title}</h2></div><button type="button" className="iconbtn" onClick={close}>X</button></header>
            <form onSubmit={save}>
              <div className="settings-dialog-body">
                {active.key === "company" && <div className="settings-form-grid">
                  <label><span>Legal name</span><input value={company.legalName} onChange={(event) => setCompany({ ...company, legalName: event.target.value })} /></label>
                  <label><span>Display name</span><input value={company.displayName} onChange={(event) => setCompany({ ...company, displayName: event.target.value })} /></label>
                  <label><span>Tax ID</span><input value={company.taxId} onChange={(event) => setCompany({ ...company, taxId: event.target.value })} /></label>
                  <label><span>Timezone</span><select value={company.timezone} onChange={(event) => setCompany({ ...company, timezone: event.target.value })}><option>America/Detroit</option><option>America/Chicago</option><option>America/New_York</option></select></label>
                  <div className="settings-security-note">Company and tenant identity come from the authenticated server session. Users cannot switch to another customer's tenant.</div>
                </div>}

                {active.key === "entities" && <div className="settings-list"><div><strong>Apex Manufacturing LLC</strong><span>United States | USD | Active</span><button type="button" className="btn small">Review</button></div><div><strong>Apex Distribution LLC</strong><span>United States | USD | Draft</span><button type="button" className="btn small">Review</button></div><button type="button" className="btn primary" onClick={() => setSaved("New legal entity draft opened")}>Add legal entity</button></div>}

                {active.key === "roles" && <div className="settings-list"><div><strong>Finance administrator</strong><span>24 permissions | 3 members</span></div><div><strong>AP specialist</strong><span>11 permissions | 5 members</span></div><div><strong>Read-only auditor</strong><span>8 permissions | 2 members</span></div><div className="settings-security-note">Role changes require an authorized administrator and remain server-enforced.</div></div>}

                {active.key === "approvals" && <div className="settings-form-grid"><label><span>Vendor payment threshold</span><input defaultValue="$10,000" /></label><label><span>Required approvers</span><select defaultValue="2"><option value="1">1 approver</option><option value="2">2 approvers</option><option value="3">3 approvers</option></select></label><label className="settings-check"><input type="checkbox" defaultChecked /> Enforce creator/approver separation</label><label className="settings-check"><input type="checkbox" defaultChecked /> Require step-up authentication</label></div>}

                {active.key === "notifications" && <div className="settings-list"><label className="settings-toggle"><span><strong>In-app notifications</strong><small>Approvals, exceptions, and deadlines</small></span><input type="checkbox" checked={notifications.inApp} onChange={(event) => setNotifications({ ...notifications, inApp: event.target.checked })} /></label><label className="settings-toggle"><span><strong>Email notifications</strong><small>Daily summaries and escalations</small></span><input type="checkbox" checked={notifications.email} onChange={(event) => setNotifications({ ...notifications, email: event.target.checked })} /></label><label className="settings-toggle"><span><strong>Microsoft Teams</strong><small>Approval and incident notifications</small></span><input type="checkbox" checked={notifications.teams} onChange={(event) => setNotifications({ ...notifications, teams: event.target.checked })} /></label></div>}

                {active.key === "security" && <div className="settings-list"><div><strong>Multi-factor authentication</strong><span>Required for administrators and high-risk actions</span><b className="settings-good">Enforced</b></div><div><strong>Session timeout</strong><span>30 minutes of inactivity</span><b className="settings-good">Active</b></div><div><strong>Forced row-level security</strong><span>Tenant isolation at the PostgreSQL layer</span><b className="settings-good">268 tables</b></div><div><strong>High-risk execution</strong><span>Production financial execution remains disabled</span><b className="settings-warn">Disabled</b></div></div>}
              </div>
              <footer><button type="button" className="btn" onClick={close}>Cancel</button><button type="submit" className="btn primary">Save changes</button></footer>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}
'@

[IO.File]::WriteAllText($PagePath, $Page, [Text.UTF8Encoding]::new($false))

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.settings-grid') {
$Css += @'

.settings-grid{display:grid;grid-template-columns:repeat(3,minmax(240px,1fr));gap:16px}.settings-card{background:white;border:1px solid var(--line);border-radius:16px;padding:22px;display:flex;flex-direction:column;align-items:flex-start;min-height:180px}.settings-card h2{font-size:15px;margin:0 0 12px}.settings-card p{color:var(--muted);font-size:12px;line-height:1.55;flex:1;margin:0 0 18px}.settings-backdrop{position:fixed;inset:0;background:#17203366;z-index:110;display:grid;place-items:center;padding:20px}.settings-dialog{width:min(720px,100%);max-height:88vh;overflow:auto;background:white;border-radius:16px;box-shadow:0 30px 90px #17203355}.settings-dialog>header{display:flex;justify-content:space-between;align-items:center;padding:20px 22px;border-bottom:1px solid var(--line)}.settings-dialog>header small{color:var(--primary);font-size:9px;font-weight:850;letter-spacing:.1em}.settings-dialog h2{margin:4px 0 0}.settings-dialog-body{padding:22px}.settings-dialog footer{display:flex;justify-content:flex-end;gap:8px;padding:16px 22px;border-top:1px solid var(--line)}.settings-form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.settings-form-grid label{display:grid;gap:6px}.settings-form-grid label span{font-size:10px;color:var(--muted);font-weight:750}.settings-form-grid input,.settings-form-grid select{border:1px solid var(--line);border-radius:9px;padding:11px;background:white}.settings-list{display:grid;gap:10px}.settings-list>div,.settings-toggle{display:flex;align-items:center;gap:12px;border:1px solid var(--line);border-radius:10px;padding:14px}.settings-list>div strong,.settings-list>div span,.settings-toggle strong,.settings-toggle small{display:block}.settings-list>div span,.settings-toggle small{color:var(--muted);font-size:10px;margin-top:3px}.settings-list>div>.btn,.settings-list>div>b{margin-left:auto}.settings-toggle input{margin-left:auto}.settings-security-note{grid-column:1/-1;background:#fff8e8;color:#80530a;padding:12px;border-radius:9px;font-size:10px;line-height:1.5}.settings-check{display:flex!important;grid-column:1/-1;align-items:center;grid-template-columns:auto 1fr!important}.settings-good{color:#197346;font-size:10px}.settings-warn{color:#a66a00;font-size:10px}.settings-toast{position:fixed;right:22px;top:82px;z-index:130;background:#133e32;color:white;padding:12px 16px;border-radius:10px;font-size:11px;font-weight:800}@media(max-width:980px){.settings-grid{grid-template-columns:1fr 1fr}}@media(max-width:680px){.settings-grid,.settings-form-grid{grid-template-columns:1fr}.settings-backdrop{padding:8px}.settings-security-note{grid-column:1}}
'@
}
[IO.File]::WriteAllText($CssPath, $Css, [Text.UTF8Encoding]::new($false))

Push-Location $Web
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Settings action TypeScript validation failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Settings action build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE SETTINGS ACTIONS PASSED" -ForegroundColor Green
