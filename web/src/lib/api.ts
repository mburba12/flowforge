const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
export class ApiError extends Error { constructor(public status:number,message:string){super(message);this.name="ApiError"} }
export type ApiOptions={token?:string;legalEntityId?:string;signal?:AbortSignal;headers?:HeadersInit};
async function request<T>(path:string,init:RequestInit={},options:ApiOptions={}):Promise<T>{
 const headers=new Headers(options.headers);headers.set("Accept","application/json");
 if(init.body&&!headers.has("Content-Type"))headers.set("Content-Type","application/json");
 if(options.token)headers.set("Authorization",`Bearer ${options.token}`);
 if(options.legalEntityId)headers.set("X-Legal-Entity-Id",options.legalEntityId);
 const response=await fetch(`${API_BASE}${path}`,{...init,headers,signal:options.signal,cache:"no-store"});
 if(!response.ok){let detail=await response.text();try{detail=JSON.parse(detail).detail??detail}catch{}throw new ApiError(response.status,detail||`Request failed (${response.status})`)}
 if(response.status===204)return undefined as T;return response.json() as Promise<T>;
}
export const apiGet=<T>(path:string,options:ApiOptions={})=>request<T>(path,{},options);
export const apiPost=<T>(path:string,body:unknown,options:ApiOptions={})=>request<T>(path,{method:"POST",body:JSON.stringify(body)},options);
export const apiPut=<T>(path:string,body:unknown,options:ApiOptions={})=>request<T>(path,{method:"PUT",body:JSON.stringify(body)},options);
export const apiPatch=<T>(path:string,body:unknown,options:ApiOptions={})=>request<T>(path,{method:"PATCH",body:JSON.stringify(body)},options);
export const apiDelete=<T>(path:string,options:ApiOptions={})=>request<T>(path,{method:"DELETE"},options);
export const endpoints={health:"/api/v1/health",phase5a:"/phase5a/status",phase5b:"/phase5b/status",openapi:"/openapi.json"};