import type { Session } from "./types";
export function requirePermission(s:Session,p:string){if(!s.permissions.has(p))throw new Error(`Missing permission: ${p}`)}
export function requireEntitlement(s:Session,m:string){if(!s.entitlements.has(m))throw new Error(`Module not entitled: ${m}`)}
export function tenantHeaders(s:Session):HeadersInit{return {Authorization:`Bearer ${s.accessToken}`,"X-Legal-Entity-Id":s.legalEntityId??""}}
// tenantId is intentionally never sent as an authority header; backend derives it from the token.
