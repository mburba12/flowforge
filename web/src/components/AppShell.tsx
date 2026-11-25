import type {ReactNode} from "react";export function AppShell({children}:{children:ReactNode}){return <div className="shell"><aside className="nav"><h2>FlowForge</h2><nav aria-label="Primary navigation"><a href="/dashboard">Dashboard</a>
<a href="/finance">Finance</a>
<a href="/ap">Accounts Payable</a>
<a href="/ar">Accounts Receivable</a>
<a href="/orders">Orders</a>
<a href="/inventory">Inventory</a>
<a href="/shipping">Shipping</a>
<a href="/payroll">Payroll</a>
<a href="/workforce">Workforce</a>
<a href="/tax">Tax & Compliance</a>
<a href="/banking">Banking & Treasury</a>
<a href="/documents">Documents</a>
<a href="/reconciliation">Reconciliation</a>
<a href="/entities">Canonical Entities</a>
<a href="/copilot">Copilot</a>
<a href="/approvals">Approvals</a>
<a href="/work-queue">Work Queue</a>
<a href="/integrations">Integrations</a>
<a href="/reports">Reports</a>
<a href="/audit">Audit</a>
<a href="/billing">Billing & Entitlements</a>
<a href="/settings">Settings</a>
<a href="/support">Help & Support</a></nav></aside><div className="main">{children}</div></div>}
