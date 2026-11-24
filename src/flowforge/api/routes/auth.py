from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import create_access_token, hash_password, verify_password
from flowforge.db.session import get_db
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
    user = User(
        tenant_id=tenant.id,
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    role = Role(tenant_id=tenant.id, name="Owner", description="Tenant owner")
    db.add(role)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    for code in [
        "tenant.manage",
        "users.manage",
        "roles.manage",
        "workflows.manage",
        "documents.manage",
        "audit.read",
        "integrations.manage",
    ]:
        permission = await db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(code=code, description=code)
            db.add(permission)
            await db.flush()
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    await record_change(db, tenant.id, user.id, "created", "tenant", str(tenant.id))
    await db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id), str(tenant.id)))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    tenant = await db.scalar(
        select(Tenant).where(Tenant.slug == body.tenant_slug, Tenant.is_deleted.is_(False))
    )
    if tenant is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    user = await db.scalar(
        select(User).where(
            User.tenant_id == tenant.id, User.email == body.email.lower(), User.is_active.is_(True)
        )
    )
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id), str(tenant.id)))
