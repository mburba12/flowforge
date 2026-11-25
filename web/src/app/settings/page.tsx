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

                {active.key === "security" && <div className="settings-list">
  <div className="customer-security-row">
    <span><strong>Multi-factor authentication</strong><small>Additional sign-in protection for your account</small></span>
    <b className="settings-warn">Not configured</b>
  </div>
  <div className="customer-security-callout">
    Multi-factor authentication is not active in this local build. It will be enabled through Microsoft Entra ID before production launch. This screen does not claim that MFA is currently enforced.
  </div>
  <label className="settings-control-row"><span><strong>Session timeout</strong><small>End inactive sessions automatically</small></span><select defaultValue="30"><option value="15">15 minutes</option><option value="30">30 minutes</option><option value="60">60 minutes</option><option value="120">2 hours</option></select></label>
  <div className="customer-security-row">
    <span><strong>Login history</strong><small>Recent account sign-ins and security events</small></span>
    <b className="settings-muted">Available after sign-in setup</b>
  </div>
  <div className="customer-security-row">
    <span><strong>Authorized users</strong><small>People who can access this company</small></span>
    <button type="button" className="btn small" onClick={() => setActive({ key: "roles", title: "Roles & permissions", description: "Review permission bundles and separation-of-duties controls." })}>Review access</button>
  </div>
  <div className="customer-security-row">
    <span><strong>Roles & permissions</strong><small>Control what authorized users can view and change</small></span>
    <button type="button" className="btn small" onClick={() => setActive({ key: "roles", title: "Roles & permissions", description: "Review permission bundles and separation-of-duties controls." })}>Manage roles</button>
  </div>
  <div className="customer-security-row">
    <span><strong>Data isolation</strong><small>Your company's data is isolated from other organizations</small></span>
    <b className="settings-good">Protected</b>
  </div>
  <div className="settings-security-note">Data isolation is enforced by the FlowForge backend and database. It cannot be disabled from customer settings.</div>
</div>}
              </div>
              <footer><button type="button" className="btn" onClick={close}>Cancel</button><button type="submit" className="btn primary">Save changes</button></footer>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}
