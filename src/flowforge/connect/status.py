"""One summary of a tenant's connections, for the home page setup checklist."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.phase4c.models import BankConnection

from .banking import plaid_configured
from .models import Attachment, CarrierAccount, PayrollMigration, TrackedShipment
from .payroll import gusto_configured

router = APIRouter(prefix="/api/v1/connections", tags=["connections"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]


@router.get("/status")
async def connection_status(db: D, p: P) -> dict[str, Any]:
    async def count(statement: Any) -> int:
        return int(await db.scalar(statement) or 0)

    t = p.tenant_id
    return {
        "banks": await count(
            select(func.count())
            .select_from(BankConnection)
            .where(BankConnection.tenant_id == t, BankConnection.status != "disconnected")
        ),
        "carriers": await count(
            select(func.count()).select_from(CarrierAccount).where(CarrierAccount.tenant_id == t)
        ),
        "shipments": await count(
            select(func.count()).select_from(TrackedShipment).where(TrackedShipment.tenant_id == t)
        ),
        "payroll_imports": await count(
            select(func.count())
            .select_from(PayrollMigration)
            .where(PayrollMigration.tenant_id == t, PayrollMigration.status == "completed")
        ),
        "files": await count(
            select(func.count())
            .select_from(Attachment)
            .where(Attachment.tenant_id == t, Attachment.is_deleted.is_(False))
        ),
        "live_bank_connections_available": plaid_configured(),
        "gusto_connection_available": gusto_configured(),
    }
