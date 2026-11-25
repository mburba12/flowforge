import type { Route } from "next";

export type Severity = "low" | "medium" | "high" | "critical";
export type Status = "draft" | "pending" | "approved" | "rejected" | "completed" | "failed";
export interface Metric { label:string; value:string; delta:string; trend:"up"|"down"|"flat"; tone:"positive"|"warning"|"danger"|"neutral" }
export interface Activity { id:string; title:string; detail:string; module:string; timestamp:string; status:Status }
export interface WorkItem { id:string; title:string; module:string; owner:string; due:string; severity:Severity; status:Status }
export interface NavItem { label:string; href: Route; icon:string; group:string; badge?:number }
export interface TableColumn { key:string; label:string; align?:"left"|"right"|"center" }
export interface WorkspaceConfig { title:string; eyebrow:string; description:string; primaryAction:string; metrics:Metric[]; columns:TableColumn[]; rows:Record<string,string>[] }

export interface Session {
  accessToken: string;
  tenantId: string;
  legalEntityId?: string;
  userId?: string;
  displayName?: string;
  email?: string;
  permissions: ReadonlySet<string>;
  entitlements: ReadonlySet<string>;
}