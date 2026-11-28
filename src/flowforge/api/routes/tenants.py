from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.platform.models import Tenant
from flowforge.platform.schemas import TenantCreate, TenantRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(body: TenantCreate, db: AsyncSession = Depends(get_tenant_db)) -> Tenant:
    # Requires platform.tenants.create, which no tenant role holds (see authorization.POLICY);
    # tenants are created through /auth/bootstrap.
    if await db.scalar(select(Tenant).where(Tenant.slug == body.slug)):
        raise HTTPException(409, "Tenant slug already exists")
    tenant = Tenant(**body.model_dump())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("", response_model=list[TenantRead])
async def list_tenants(
    principal: Annotated[Principal, Depends(current_principal)],
    db: AsyncSession = Depends(get_tenant_db),
) -> list[Tenant]:
    # The tenants table is not tenant-scoped by RLS; return only the caller's tenant.
    return list(
        (
            await db.scalars(
                select(Tenant).where(Tenant.id == principal.tenant_id, Tenant.is_deleted.is_(False))
            )
        ).all()
    )
