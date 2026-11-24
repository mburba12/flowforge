from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_db

from .payment_service import APPaymentError, APPaymentService

router = APIRouter(prefix="/api/v3", tags=["phase3a-final"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_db)]


@router.post("/ap/open-items/{open_item_id}/pay")
async def pay(
    open_item_id: UUID,
    amount: Decimal,
    payment_date: date,
    ledger_id: UUID,
    period_id: UUID,
    ap_account_id: UUID,
    cash_account_id: UUID,
    currency_code: str,
    principal: P,
    db: D,
) -> dict[str, str]:
    try:
        result = await APPaymentService(
            db,
            principal.tenant_id,
            principal.user_id,
        ).pay_open_item(
            open_item_id,
            amount,
            payment_date,
            ledger_id,
            period_id,
            ap_account_id,
            cash_account_id,
            currency_code,
        )
    except APPaymentError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"id": str(result.id), "status": result.status}


@router.post("/ap/reconcile")
async def reconcile(
    ledger_id: UUID,
    period_id: UUID,
    ap_account_id: UUID,
    principal: P,
    db: D,
) -> dict[str, str]:
    result = await APPaymentService(
        db,
        principal.tenant_id,
        principal.user_id,
    ).reconcile(ledger_id, period_id, ap_account_id)
    return {
        "id": str(result.id),
        "status": result.status,
        "subledger_total": str(result.subledger_total),
        "gl_total": str(result.gl_total),
    }
