import type { SVGProps } from "react";

export type IconName =
  | "dashboard" | "approvals" | "work-queue" | "ap" | "ar" | "ledger"
  | "banking" | "tax" | "orders" | "inventory" | "shipping" | "payroll"
  | "workforce" | "documents" | "reconciliation" | "entities" | "reports"
  | "audit" | "integrations" | "billing" | "settings" | "support"
  | "search" | "notifications" | "help" | "spark";

const paths: Record<IconName, React.ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  approvals: <><path d="M9 11l2 2 4-5"/><path d="M6 3h12v18H6z"/><path d="M9 17h6"/></>,
  "work-queue": <><path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></>,
  ap: <><path d="M4 19h16"/><path d="M7 16v-5M12 16V8M17 16V5"/><path d="M14 5h3v3"/></>,
  ar: <><path d="M4 5h16"/><path d="M7 8v5M12 8v8M17 8v11"/><path d="M14 19h3v-3"/></>,
  ledger: <><path d="M4 4h16v16H4z"/><path d="M8 4v16M8 9h12M8 14h12"/></>,
  banking: <><path d="M3 9l9-5 9 5"/><path d="M5 10h14M6 10v8M10 10v8M14 10v8M18 10v8M4 20h16"/></>,
  tax: <><circle cx="7" cy="7" r="3"/><circle cx="17" cy="17" r="3"/><path d="M5 19L19 5"/></>,
  orders: <><path d="M4 7l8-4 8 4-8 4z"/><path d="M4 7v10l8 4 8-4V7M12 11v10"/></>,
  inventory: <><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 9v11M16 9v11"/></>,
  shipping: <><path d="M3 6h11v11H3zM14 10h4l3 3v4h-7z"/><circle cx="7" cy="19" r="2"/><circle cx="17" cy="19" r="2"/></>,
  payroll: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h3M8 15h8M14 10v4M12 12h4"/></>,
  workforce: <><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2"/><path d="M3 20c0-4 3-7 6-7s6 3 6 7M14 14c3 0 6 2 6 6"/></>,
  documents: <><path d="M6 3h9l4 4v14H6z"/><path d="M15 3v5h5M9 12h7M9 16h7"/></>,
  reconciliation: <><path d="M4 8h14l-3-3M20 16H6l3 3"/><path d="M18 8l-3 3M6 16l3-3"/></>,
  entities: <><circle cx="12" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/><path d="M10 8L7 15M14 8l3 7M9 18h6"/></>,
  reports: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>,
  audit: <><circle cx="10" cy="10" r="6"/><path d="M14.5 14.5L21 21M8 10l2 2 4-5"/></>,
  integrations: <><path d="M8 3v5H3M16 3v5h5M8 21v-5H3M16 21v-5h5"/><rect x="8" y="8" width="8" height="8" rx="2"/></>,
  billing: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9L7 7M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/></>,
  support: <><circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.5 2.5 0 114.2 1.8c-1.2.9-2 1.3-2 3.2M12 18h.01"/></>,
  search: <><circle cx="10" cy="10" r="6"/><path d="M15 15l6 6"/></>,
  notifications: <><path d="M6 17h12l-2-3V9a4 4 0 00-8 0v5z"/><path d="M10 20h4"/></>,
  help: <><circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.5 2.5 0 114.2 1.8c-1.2.9-2 1.3-2 3.2M12 18h.01"/></>,
  spark: <><path d="M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z"/><path d="M19 16l.7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z"/></>,
};

export function AppIcon({ name, ...props }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}
