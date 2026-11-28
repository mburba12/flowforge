"use client";

import { AdminWorkspace } from "./admin";
import { FinanceWorkspace } from "./finance";
import { InventoryWorkspace } from "./inventory";
import { AuditWorkspace, DashboardWorkspace } from "./overview";
import { PayablesWorkspace } from "./payables";
import { PayrollWorkspace } from "./payroll";
import { ReceivablesWorkspace } from "./receivables";
import { TaxWorkspace } from "./tax";

const WORKSPACES: Record<string, () => React.JSX.Element> = {
  dashboard: DashboardWorkspace,
  finance: FinanceWorkspace,
  ap: PayablesWorkspace,
  ar: () => <ReceivablesWorkspace initialTab="open" />,
  orders: () => <ReceivablesWorkspace initialTab="orders" />,
  inventory: InventoryWorkspace,
  payroll: () => <PayrollWorkspace initialTab="runs" />,
  workforce: () => <PayrollWorkspace initialTab="workers" />,
  tax: TaxWorkspace,
  settings: AdminWorkspace,
  audit: AuditWorkspace,
};

export function ReleaseWorkspace({ slug }: { slug: string }) {
  const Component = WORKSPACES[slug];
  return Component ? <Component /> : null;
}