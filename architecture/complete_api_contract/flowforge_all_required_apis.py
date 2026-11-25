from __future__ import annotations

from typing import Any
from uuid import uuid4
from fastapi import FastAPI, Header, HTTPException, Request, Response

app = FastAPI(title="FlowForge Complete Required API Contract", version="1.0.0")
STORE: dict[tuple[str,str,str], dict[str,Any]] = {}

def tenant(x_tenant_id: str | None) -> str:
    if not x_tenant_id:
        raise HTTPException(401, "Authenticated tenant context required")
    return x_tenant_id

@app.api_route("/api/v1/{module}/{resource}", methods=["GET","POST"])
async def collection(module: str, resource: str, request: Request, x_tenant_id: str | None = Header(default=None)):
    t=tenant(x_tenant_id)
    if request.method == "GET":
        return {"items":[v for (tenant_id,m,_),v in STORE.items() if tenant_id==t and m==f"{module}/{resource}"],"next_cursor":None}
    payload=await request.json(); rid=str(uuid4()); record={"id":rid,"tenant_id":t,**payload}; STORE[(t,f"{module}/{resource}",rid)]=record; return record

@app.api_route("/api/v1/{module}/{resource}/{record_id}", methods=["GET","PATCH","DELETE"])
async def item(module: str, resource: str, record_id: str, request: Request, x_tenant_id: str | None = Header(default=None)):
    t=tenant(x_tenant_id); key=(t,f"{module}/{resource}",record_id)
    if key not in STORE: raise HTTPException(404,"Not found")
    if request.method == "GET": return STORE[key]
    if request.method == "DELETE": del STORE[key]; return Response(status_code=204)
    STORE[key].update(await request.json()); return STORE[key]

@app.post("/api/v1/{module}/actions/{action}", status_code=202)
async def action(module: str, action: str, request: Request, x_tenant_id: str | None = Header(default=None)):
    t=tenant(x_tenant_id); payload=await request.json()
    if not payload.get("idempotency_key"): raise HTTPException(400,"idempotency_key required")
    return {"accepted":True,"tenant_id":t,"module":module,"action":action,"job_id":str(uuid4()),"status":"queued","payload":payload}
