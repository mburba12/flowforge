const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
export class ApiError extends Error { constructor(public status:number,message:string){super(message)} }
export async function apiGet<T>(path:string):Promise<T>{
 const response=await fetch(`${API_BASE}${path}`,{cache:"no-store",headers:{Accept:"application/json"}});
 if(!response.ok) throw new ApiError(response.status,await response.text());
 return response.json() as Promise<T>;
}
export async function apiPost<T>(path:string,body:unknown):Promise<T>{
 const response=await fetch(`${API_BASE}${path}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
 if(!response.ok) throw new ApiError(response.status,await response.text());
 return response.json() as Promise<T>;
}
export const endpoints={phase5a:"/phase5a/status",phase5b:"/phase5b/status",openapi:"/openapi.json"};
