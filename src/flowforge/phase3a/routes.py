from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .models import PurchaseOrder
from .schemas import InvoiceCreate, POCreate, ReceiptCreate, VendorCreate
from .service import ProcurementService

router = APIRouter(prefix="/api/v3", tags=["phase3a"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


def service(p: P, db: D) -> ProcurementService:
    return ProcurementService(db, p.tenant_id, p.user_id)


@router.post("/vendors", status_code=201)
async def vendor(
    body: VendorCreate, s: Annotated[ProcurementService, Depends(service)]
) -> dict[str, str]:
    x = await s.vendor(body)
    return {"id": str(x.id), "vendor_number": x.vendor_number}


@router.post("/purchase-orders", status_code=201)
async def purchase_order(
    body: POCreate, s: Annotated[ProcurementService, Depends(service)]
) -> dict[str, str]:
    x = await s.purchase_order(body)
    return {"id": str(x.id), "po_number": x.po_number, "status": x.status}


@router.post("/purchase-orders/{po_id}/submit")
async def submit(po_id: UUID, p: P, db: D) -> dict[str, str]:
    x = await db.scalar(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == p.tenant_id
        )
    )
    if x is None:
        raise HTTPException(404, "Purchase order not found")
    if x.status != "draft":
        raise HTTPException(409, "Only draft orders can submit")
    x.status = "submitted"
    await db.commit()
    return {"id": str(x.id), "status": x.status}


@router.post("/purchase-orders/{po_id}/approve")
async def approve(po_id: UUID, p: P, db: D) -> dict[str, str]:
    x = await db.scalar(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == p.tenant_id
        )
    )
    if x is None:
        raise HTTPException(404, "Purchase order not found")
    if x.created_by == p.user_id:
        raise HTTPException(409, "Creator cannot approve own purchase order")
    if x.status != "submitted":
        raise HTTPException(409, "Purchase order is not submitted")
    x.status = "approved"
    x.approved_by = p.user_id
    await db.commit()
    return {"id": str(x.id), "status": x.status}


@router.post("/goods-receipts", status_code=201)
async def receipt(
    body: ReceiptCreate, s: Annotated[ProcurementService, Depends(service)]
) -> dict[str, str]:
    try:
        x = await s.receipt(body)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    return {"id": str(x.id), "receipt_number": x.receipt_number, "status": x.status}


@router.post("/vendor-invoices", status_code=201)
async def invoice(
    body: InvoiceCreate, s: Annotated[ProcurementService, Depends(service)]
) -> dict[str, str]:
    x = await s.invoice(body)
    return {"id": str(x.id), "status": x.status, "total_amount": str(x.total_amount)}
