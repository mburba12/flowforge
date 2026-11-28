import { NextRequest, NextResponse } from "next/server";
const backend=process.env.FLOWFORGE_API_URL||"http://127.0.0.1:8000";
const allowed=["authorization","content-type","accept","x-tenant-id","x-legal-entity-id","idempotency-key","x-request-id"];
async function forward(request:NextRequest,context:{params:Promise<{path:string[]}>}){
 const {path}=await context.params;const target=new URL(`${backend}/${path.join("/")}`);
 request.nextUrl.searchParams.forEach((value,key)=>target.searchParams.append(key,value));
 const headers=new Headers();for(const name of allowed){const value=request.headers.get(name);if(value)headers.set(name,value)}
 const body=["GET","HEAD"].includes(request.method)?undefined:await request.arrayBuffer();
 try{const response=await fetch(target,{method:request.method,headers,body,cache:"no-store",signal:AbortSignal.timeout(60000)});const outHeaders=new Headers();
 for(const name of ["content-type","content-disposition","x-request-id"]){const value=response.headers.get(name);if(value)outHeaders.set(name,value)}
 return new NextResponse(response.body,{status:response.status,headers:outHeaders});}
 catch(error){return NextResponse.json({detail:error instanceof Error?error.message:"Backend unavailable"},{status:502})}
}
export const GET=forward;export const POST=forward;export const PUT=forward;export const PATCH=forward;export const DELETE=forward;