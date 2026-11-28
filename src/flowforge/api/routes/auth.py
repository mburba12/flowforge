"""Sign-in and sign-up (public endpoints, rate limited per client address)."""

import re
import secrets
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.accounts.models import UserMfa
from flowforge.accounts.policy import bootstrap_allowed
from flowforge.accounts.service import check_bot, send_verification
from flowforge.core.security import (
    create_access_token,
    create_mfa_challenge,
    hash_password_async,
    verify_password_async,
)
from flowforge.db.session import enter_tenant_context, get_db
from flowforge.platform import ratelimit
from flowforge.platform.authorization import CATALOG, STANDARD_ROLES
from flowforge.platform.models import Permission, Role, RolePermission, Tenant, User, UserRole
from flowforge.platform.schemas import (
    BootstrapRequest,
    LoginRequest,
    SignupRequest,
    SignupResponse,
    TenantCreate,
    TokenResponse,
)
from flowforge.platform.services import record_change

router = APIRouter(prefix="/auth", tags=["auth"])

SIGNUP_LIMIT = (5, 3600)  # new workspaces per client address per hour
LOGIN_LIMIT = (20, 300)  # sign-in attempts per client address per 5 minutes
LOGIN_EMAIL_LIMIT = (10, 300)  # sign-in attempts per address and email per 5 minutes


async def _create_workspace(db: AsyncSession, body: BootstrapRequest) -> tuple[Tenant, User]:
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
    return tenant, user


@router.post("/bootstrap", response_model=TokenResponse, status_code=201)
async def bootstrap(
    body: BootstrapRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    if not bootstrap_allowed():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")  # sign up at /signup
    ratelimit.check(f"signup:{ratelimit.client_address(request)}", *SIGNUP_LIMIT)
    tenant, user = await _create_workspace(db, body)
    return TokenResponse(access_token=create_access_token(str(user.id), str(tenant.id)))


async def _tenants_for_email(db: AsyncSession, email: str) -> list[UUID]:
    """Workspaces with an active user of this email (ff_login_tenants, migration ff_login_001)."""
    rows = await db.execute(text("SELECT ff_login_tenants(:e)"), {"e": email.lower()})
    return [row[0] for row in rows]


def _slug_base(organization: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", organization.lower()).strip("-")[:40].strip("-")
    return base if len(base) >= 2 else "workspace"


@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(
    body: SignupRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> SignupResponse:
    """Public sign-up: a new workspace with this person as its owner, signed in."""
    address = ratelimit.client_address(request)
    ratelimit.check(f"signup:{address}", *SIGNUP_LIMIT)
    await check_bot(body.turnstile_token, address)
    if await _tenants_for_email(db, body.email):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An account with this email already exists. Sign in instead.",
        )
    base = _slug_base(body.organization)
    slug = base
    while await db.scalar(select(Tenant.id).where(Tenant.slug == slug)):
        slug = f"{base}-{secrets.token_hex(2)}"
    tenant, user = await _create_workspace(
        db,
        BootstrapRequest(
            tenant=TenantCreate(name=body.organization.strip(), slug=slug),
            email=body.email,
            password=body.password,
            display_name=body.name.strip(),
        ),
    )
    await enter_tenant_context(db, tenant.id, user.id)
    await send_verification(db, user)
    await db.commit()
    return SignupResponse(
        access_token=create_access_token(str(user.id), str(tenant.id)), tenant_slug=tenant.slug
    )


async def _user_if_password_matches(
    db: AsyncSession, tenant_id: UUID, email: str, password: str
) -> User | None:
    # users is tenant-owned and RLS-protected; scope the lookup to this tenant.
    await enter_tenant_context(db, tenant_id)
    user = await db.scalar(
        select(User).where(
            User.tenant_id == tenant_id, User.email == email.lower(), User.is_active.is_(True)
        )
    )
    if user is None or not await verify_password_async(password, user.password_hash):
        return None
    return user


async def _signed_in(db: AsyncSession, tenant_id: UUID, user: User) -> dict[str, Any]:
    """A sign-in token, or (when two-step sign-in is on) a challenge for the code."""
    await enter_tenant_context(db, tenant_id)
    enabled = await db.scalar(
        select(UserMfa.enabled_at).where(UserMfa.tenant_id == tenant_id, UserMfa.user_id == user.id)
    )
    if enabled is not None:
        return {
            "mfa_required": True,
            "challenge": create_mfa_challenge(str(user.id), str(tenant_id)),
        }
    return {
        "access_token": create_access_token(str(user.id), str(tenant_id)),
        "token_type": "bearer",
    }


@router.post("/login")
async def login(
    body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    address = ratelimit.client_address(request)
    ratelimit.check(f"login:{address}", *LOGIN_LIMIT)
    ratelimit.check(f"login:{address}:{body.email.lower()}", *LOGIN_EMAIL_LIMIT)
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if body.tenant_slug:
        tenant = await db.scalar(
            select(Tenant).where(Tenant.slug == body.tenant_slug, Tenant.is_deleted.is_(False))
        )
        if tenant is None:
            raise invalid
        user = await _user_if_password_matches(db, tenant.id, body.email, body.password)
        if user is None:
            raise invalid
        return await _signed_in(db, tenant.id, user)

    # Email only: the workspace(s) this email and password open.
    matches: list[tuple[UUID, User]] = []
    for tenant_id in await _tenants_for_email(db, body.email):
        found = await _user_if_password_matches(db, tenant_id, body.email, body.password)
        if found is not None:
            matches.append((tenant_id, found))
    if not matches:
        raise invalid
    if len(matches) > 1:
        tenants = (
            await db.scalars(select(Tenant).where(Tenant.id.in_([t for t, _ in matches])))
        ).all()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {
                "code": "workspace_required",
                "message": "This email opens more than one workspace. Choose one.",
                "workspaces": [{"slug": t.slug, "name": t.name} for t in tenants],
            },
        )
    tenant_id, user = matches[0]
    return await _signed_in(db, tenant_id, user)
