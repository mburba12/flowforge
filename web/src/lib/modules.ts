import type { IconName } from "@/components/app-icon";

/**
 * Sidebar: everyday work in a few plain-language groups; specialist tools under "More tools"
 * (collapsed). Every workspace the server assigns operations to must be listed here
 * (tests/workflows/test_ui_reachability.py reads the ["slug", "Label"] pairs).
 */
export type NavItem = readonly [slug: string, label: string, icon: IconName];
export type NavGroup = { label: string | null; items: readonly NavItem[]; collapsed?: boolean };

export const navGroups: readonly NavGroup[] = [
  { label: null, items: [["dashboard", "Home", "dashboard"]] },
  {
    label: "Money",
    items: [
      ["banking", "Bank accounts", "banking"],
      ["ap", "Bills to pay", "ap"],
      ["ar", "Invoices & payments", "ar"],
      ["finance", "Accounting", "ledger"],
      ["tax", "Taxes", "tax"],
    ],
  },
  {
    label: "Sales",
    items: [
      ["orders", "Orders", "orders"],
      ["crm", "Customers & deals", "entities"],
      ["shipping", "Shipments", "shipping"],
    ],
  },
  {
    label: "Products",
    items: [
      ["inventory", "Inventory", "inventory"],
      ["commerce", "Purchasing & warehouse", "integrations"],
    ],
  },
  {
    label: "People",
    items: [
      ["workforce", "Employees", "workforce"],
      ["payroll", "Payroll", "payroll"],
    ],
  },
  {
    label: null,
    items: [
      ["documents", "Files", "documents"],
      ["settings", "Settings", "settings"],
    ],
  },
  {
    label: "More tools",
    collapsed: true,
    items: [
      ["finance-advanced", "Close, budgets & assets", "reports"],
      ["reconciliation", "Reconciliation", "reconciliation"],
      ["reports", "Reports", "reports"],
      ["billing", "Subscriptions & projects", "billing"],
      ["payroll-tax", "Payroll filings & adjustments", "payroll"],
      ["talent", "HR & talent", "workforce"],
      ["manufacturing", "Manufacturing & quality", "inventory"],
      ["master-data", "Contacts & master data", "entities"],
      ["entities", "Entities", "entities"],
      ["approvals", "Approvals", "approvals"],
      ["work-queue", "Work queue", "work-queue"],
      ["copilot", "Knowledge & copilot", "spark"],
      ["operations", "Operations runs", "work-queue"],
      ["integrations", "Integrations", "integrations"],
      ["governance", "Governance & controls", "audit"],
      ["audit", "Audit trail", "audit"],
      ["support", "Support", "support"],
    ],
  },
];

/** Every sidebar entry as [slug, label]. */
export const modules: readonly (readonly [string, string])[] = navGroups.flatMap((g) => g.items.map(([slug, label]) => [slug, label] as const));

export function labelOf(slug: string): string {
  return modules.find(([s]) => s === slug)?.[1] ?? slug;
}

export const tagMap:Record<string,string[]>={dashboard:["health","phase1","phase5a","phase5b"],ap:["phase3a","phase3a-integration","phase3a-final"],ar:["phase3b"],orders:["phase3b","phase4c-commerce"],inventory:["phase3a","phase3b"],finance:["phase2b","phase4c-finance"],banking:["phase4c-banking","phase4c-payments"],reconciliation:["phase4e-reconciliation","phase3-final"],workforce:["phase4a","phase4a-time","phase4c-workforce"],payroll:["phase4a-payroll"],tax:["phase4b-tax","phase4b-filing"],integrations:["platform","phase4c-banking","phase4c-payments","phase4c-commerce","phase4c-logistics","phase4c-finance","phase4c-workforce","phase4c-engagement"],documents:["platform","phase4f-ai"],entities:["phase2a","phase4d-entities"],approvals:["phase2b","phase3a","phase4a-time","phase4a-payroll","phase4b-filing","phase4d-entities"],"work-queue":["platform","support"],audit:["platform"],reports:["phase2b","phase3-final"],settings:["platform","tenants","auth"],support:["support"],copilot:["phase4f-ai"]};
