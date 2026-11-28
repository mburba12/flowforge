from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import (
    create_access_token,
    hash_password_async,
    verify_password_async,
)
from flowforge.db.session import enter_tenant_context, get_db
from flowforge.platform.authorization import CATALOG, STANDARD_ROLES
from flowforge.platform.models import Permission, Role, RolePermission, Tenant, User, UserRole
from flowforge.platform.schemas import BootstrapRequest, LoginRequest, TokenResponse
from flowforge.platform.services import record_change

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap", response_model=TokenResponse, status_code=201)
async def bootstrap(body: BootstrapRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    if await db.scalar(select(Tenant).where(Tenant.slug == body.tenant.slug)):
        raise HTTPException(409, "Tenant slug already exists")
    tenant = Tenant(**body.tenant.model_dump())
    db.add(tenant)
    await db.flush()
    # Tenant-owned tables are protected by forced RLS; install the new
    # tenant's context before writing any of them.
    await enter_tenant_context(db, tenant.id)
    user = User(
        tenant_id=tenant.id,
        email=body.email.lower(),
        password_hash=await hash_password_async(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    await db.flush()
    await enter_tenant_context(db, tenant.id, user.id)
    # Permission catalog (global) and the tenant's standard roles; the owner gets Owner.
    permission_ids: dict[str, object] = {}
    for code, description in CATALOG.items():
        permission = await db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(code=code, description=description)
            db.add(permission)
            await db.flush()
        permission_ids[code] = permission.id
    for role_name, codes in STANDARD_ROLES.items():
        role = Role(tenant_id=tenant.id, name=role_name, description=f"Standard {role_name} role")
        db.add(role)
        await db.flush()
        for code in sorted(codes):
            db.add(
                RolePermission(
                    tenant_id=tenant.id, role_id=role.id, permission_id=permission_ids[code]
                )
            )
        if role_name == "Owner":
            db.add(UserRole(tenant_id=tenant.id, user_id=user.id, role_id=role.id))
    await record_change(db, tenant.id, user.id, "created", "tenant", str(tenant.id))
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant slug or owner email already exists",
        ) from exc
    return TokenResponse(access_token=create_access_token(str(user.id), str(tenant.id)))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    tenant = await db.scalar(
        select(Tenant).where(Tenant.slug == body.tenant_slug, Tenant.is_deleted.is_(False))
    )
    if tenant is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    # users is tenant-owned and RLS-protected; scope the lookup to this tenant.
    await enter_tenant_context(db, tenant.id)
    user = await db.scalar(
        select(User).where(
            User.tenant_id == tenant.id, User.email == body.email.lower(), User.is_active.is_(True)
        )
    )
    if user is None or not await verify_password_async(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id), str(tenant.id)))
