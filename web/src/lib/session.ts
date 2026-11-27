export type FlowForgeSession={accessToken:string;tokenType:string;tenantId?:string;legalEntityId?:string;user?:Record<string,unknown>};
const KEY="flowforge.session";
export function readSession():FlowForgeSession|null{if(typeof window==="undefined")return null;const raw=sessionStorage.getItem(KEY);if(raw){try{return JSON.parse(raw) as FlowForgeSession}catch{sessionStorage.removeItem(KEY)}}const token=sessionStorage.getItem("flowforge.accessToken");return token?{accessToken:token,tokenType:"bearer",tenantId:sessionStorage.getItem("flowforge.tenantId")??undefined}:null}
export function writeSession(value:FlowForgeSession){sessionStorage.setItem(KEY,JSON.stringify(value));sessionStorage.setItem("flowforge.accessToken",value.accessToken);if(value.tenantId)sessionStorage.setItem("flowforge.tenantId",value.tenantId);if(value.legalEntityId)sessionStorage.setItem("flowforge.legalEntityId",value.legalEntityId)}
export function clearSession(){for(const key of Object.keys(sessionStorage))if(key.startsWith("flowforge."))sessionStorage.removeItem(key);for(const key of Object.keys(localStorage))if(key.startsWith("flowforge."))localStorage.removeItem(key)}
export function tokenFromResponse(value:Record<string,unknown>){const token=value.access_token??value.accessToken??value.token;if(typeof token!=="string"||!token)throw new Error("Login response did not contain an access token.");return token}

export type PermissionSession = {
  accessToken: string;
  userId?: string;
  permissions?: Set<string>;
  entitlements?: Set<string>;
};

export function requirePermission(
  session: PermissionSession,
  permission: string,
): void {
  if (!session.permissions?.has(permission)) {
    throw new Error(`Missing permission: ${permission}`);
  }
}

export function tenantHeaders(
  session: PermissionSession,
): Record<string, string> {
  return {
    Authorization: `Bearer ${session.accessToken}`,
  };
}