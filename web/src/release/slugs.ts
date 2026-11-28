/** Module slugs that have a full release workspace (shared by server and client code). */
export const RELEASE_SLUGS = ["dashboard", "finance", "ap", "ar", "orders", "inventory", "payroll", "workforce", "tax", "settings", "audit", "banking", "shipping", "documents"] as const;

export function hasReleaseWorkspace(slug: string): boolean {
  return (RELEASE_SLUGS as readonly string[]).includes(slug);
}

export type WorkspaceMeta = { title: string; description: string; accent: string };

/**
 * Extended domains: workspaces generated from the server's operation catalog
 * (/api/v1/operations). Keys must match the backend's EXTENDED_WORKSPACES values.
 */
export const EXTENDED_WORKSPACES: Record<string, WorkspaceMeta> = {
  crm: { title: "CRM & sales", description: "Leads, opportunities, quotes, campaigns, activities and pricing", accent: "#0891b2" },
  commerce: { title: "Procurement & logistics", description: "Requisitions, reservations, transfers, counts, shipments, returns and claims", accent: "#0d9488" },
  "finance-advanced": { title: "Close, budgets & assets", description: "Close runs, accruals, allocations, recurring journals, budgets, consolidations and fixed assets", accent: "#4f46e5" },
  "payroll-tax": { title: "Payroll & tax operations", description: "Adjustments, retro pay, garnishments, filings, payment batches and year-end forms", accent: "#dc2626" },
  talent: { title: "HR & talent", description: "Positions, recruiting, onboarding, benefits, learning, reviews, schedules, time and leave", accent: "#db2777" },
  "master-data": { title: "Master data", description: "Parties, contacts, addresses, identifiers, relationships, payment terms and merges", accent: "#334155" },
  billing: { title: "Subscriptions & projects", description: "Plans, subscriptions, usage, billing runs, projects, time, expenses and project billing", accent: "#7c3aed" },
  manufacturing: { title: "Manufacturing & quality", description: "Manufacturing and quality records, transitions and lot genealogy", accent: "#b45309" },
  copilot: { title: "Knowledge & copilot", description: "Knowledge records, search, copilot proposals and document inspection", accent: "#7c3aed" },
  operations: { title: "Operations runs", description: "Operational runs and their completion", accent: "#475569" },
  governance: { title: "Governance & controls", description: "Entitlements, access reviews, delegations, approval limits, SoD rules and data stewardship", accent: "#ca8a04" },
  integrations: { title: "Integrations", description: "Banking, payments, commerce, logistics, finance, workforce and engagement providers", accent: "#475569" },
  entities: { title: "Entities", description: "Entities, relationships, lineage, matching and merges", accent: "#334155" },
};

export function hasExtendedWorkspace(slug: string): boolean {
  return slug in EXTENDED_WORKSPACES;
}
