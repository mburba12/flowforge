from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_db

from .reconciliation import Phase3ReconciliationService

router = APIRouter(prefix="/api/v3/final", tags=["phase3-final"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_db)]


@router.get("/reconcile")
async def reconcile(
    ap_account_id: UUID,
    ar_account_id: UUID,
    inventory_account_id: UUID,
    principal: P,
    db: D,
) -> dict[str, str]:
    return await Phase3ReconciliationService(db, principal.tenant_id).summary(
        ap_account_id,
        ar_account_id,
        inventory_account_id,
    )
