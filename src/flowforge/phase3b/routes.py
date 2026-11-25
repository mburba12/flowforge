from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db

from .schemas import (
    CustomerCreate,
    InventoryAdjust,
    LocationCreate,
    OrderCreate,
    ProductCreate,
    ReceiptCreate,
    WarehouseCreate,
)
from .service import CommerceService, Phase3BError

router = APIRouter(prefix="/api/v3b", tags=["phase3b"])

PrincipalDependency = Annotated[
    Principal,
    Depends(current_principal),
]
DatabaseDependency = Annotated[
    AsyncSession,
    Depends(get_tenant_db),
]
ServiceDependency = Annotated[
    CommerceService,
    Depends(
        lambda principal=Depends(current_principal), db=Depends(get_tenant_db): CommerceService(
            db, principal.tenant_id, principal.user_id
        )
    ),
]


def service(
    principal: PrincipalDependency,
    db: DatabaseDependency,
) -> CommerceService:
    return CommerceService(
        db,
        principal.tenant_id,
        principal.user_id,
    )


CommerceServiceDependency = Annotated[
    CommerceService,
    Depends(service),
]


@router.post("/customers", status_code=201)
async def create_customer(
    body: CustomerCreate,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    customer = await commerce.customer(body)
    return {
        "id": str(customer.id),
        "customer_number": customer.customer_number,
    }


@router.post("/products", status_code=201)
async def create_product(
    body: ProductCreate,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    product = await commerce.product(body)
    return {
        "id": str(product.id),
        "sku": product.sku,
    }


@router.post("/warehouses", status_code=201)
async def create_warehouse(
    body: WarehouseCreate,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    warehouse = await commerce.warehouse(body)
    return {
        "id": str(warehouse.id),
        "code": warehouse.code,
    }


@router.post("/locations", status_code=201)
async def create_location(
    body: LocationCreate,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    location = await commerce.location(body)
    return {
        "id": str(location.id),
        "code": location.code,
    }


@router.post("/inventory/adjust", status_code=201)
async def adjust_inventory(
    body: InventoryAdjust,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    try:
        balance = await commerce.adjust(body)
    except Phase3BError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(balance.id),
        "on_hand": str(balance.on_hand),
    }


@router.post("/orders", status_code=201)
async def create_order(
    body: OrderCreate,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    order = await commerce.order(body)
    return {
        "id": str(order.id),
        "status": order.status,
        "total": str(order.total_amount),
    }


@router.post("/orders/{order_id}/reserve")
async def reserve_order(
    order_id: UUID,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    try:
        order = await commerce.reserve(order_id)
    except Phase3BError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(order.id),
        "status": order.status,
    }


@router.post("/orders/{order_id}/ship-invoice")
async def ship_and_invoice_order(
    order_id: UUID,
    ship_date: date,
    due_date: date,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    try:
        invoice = await commerce.ship_and_invoice(
            order_id,
            ship_date,
            due_date,
        )
    except Phase3BError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(invoice.id),
        "status": invoice.status,
        "total": str(invoice.total_amount),
    }


@router.post("/receipts", status_code=201)
async def create_receipt(
    body: ReceiptCreate,
    commerce: CommerceServiceDependency,
) -> dict[str, str]:
    try:
        receipt = await commerce.receipt(body)
    except Phase3BError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(receipt.id),
        "status": receipt.status,
        "amount": str(receipt.amount),
    }
