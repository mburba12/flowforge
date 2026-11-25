from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import (
    Principal,
    current_principal,
)
from flowforge.db.session import get_tenant_db

from .integration import APIntegrationService

router = APIRouter(
    prefix="/api/v3",
    tags=["phase3a-integration"],
)

PrincipalDependency = Annotated[
    Principal,
    Depends(current_principal),
]
DatabaseDependency = Annotated[
    AsyncSession,
    Depends(get_tenant_db),
]


@router.post("/vendor-invoices/{invoice_id}/match")
async def match_invoice(
    invoice_id: UUID,
    principal: PrincipalDependency,
    db: DatabaseDependency,
) -> dict[str, object]:
    service = APIntegrationService(
        db,
        principal.tenant_id,
        principal.user_id,
    )

    try:
        result = await service.match_invoice(invoice_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(result.id),
        "status": result.status,
        "exceptions": result.exception_count,
        "details": result.details,
    }


@router.post("/vendor-invoices/{invoice_id}/post")
async def post_invoice(
    invoice_id: UUID,
    ledger_id: UUID,
    period_id: UUID,
    ap_account_id: UUID,
    principal: PrincipalDependency,
    db: DatabaseDependency,
) -> dict[str, str]:
    service = APIntegrationService(
        db,
        principal.tenant_id,
        principal.user_id,
    )

    try:
        invoice = await service.post_invoice(
            invoice_id=invoice_id,
            ledger_id=ledger_id,
            period_id=period_id,
            ap_account_id=ap_account_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "id": str(invoice.id),
        "status": invoice.status,
        "journal_id": str(invoice.posted_journal_id),
    }
