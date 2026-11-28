"""User, role and permission administration for a tenant (gated by authorization.POLICY)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.security import Principal, current_principal, hash_password
from flowforge.db.session import get_tenant_db
from flowforge.platform.authorization import CATALOG, STANDARD_ROLES, load_access
from flowforge.platform.models import Permission, Role, RolePermission, User, UserRole
from flowforge.platform.services import record_change

router = APIRouter(tags=["users"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]

PROTECTED_ROLE = "Owner"


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=200)
    roles: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class RoleAssignment(BaseModel):
    role: str = Field(min_length=1, max_length=100)


class RolePermissionsUpdate(BaseModel):
    permissions: list[str]


async def _role_by_name(db: AsyncSession, tenant_id: UUID, name: str) -> Role:
    role = await db.scalar(
        select(Role).where(
            Role.tenant_id == tenant_id, Role.name == name, Role.is_deleted.is_(False)
        )
    )
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Role not found: {name}")
    return role


async def _user(db: AsyncSession, tenant_id: UUID, user_id: UUID) -> User:
    user = await db.scalar(
        select(User).where(
            User.id == user_id, User.tenant_id == tenant_id, User.is_deleted.is_(False)
        )
    )
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


async def _role_names(db: AsyncSession, tenant_id: UUID, user_id: UUID) -> list[str]:
    rows = await db.scalars(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, UserRole.tenant_id == tenant_id)
        .order_by(Role.name)
    )
    return list(rows.all())


async def _user_view(db: AsyncSession, user: User) -> dict[str, object]:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "is_active": user.is_active,
        "roles": await _role_names(db, user.tenant_id, user.id),
    }


@router.get("/users")
async def list_users(p: P, db: D) -> list[dict[str, object]]:
    users = (
        await db.scalars(
            select(User)
            .where(User.tenant_id == p.tenant_id, User.is_deleted.is_(False))
            .order_by(User.email)
        )
    ).all()
    return [await _user_view(db, user) for user in users]


@router.post("/users", status_code=201)
async def create_user(body: UserCreate, p: P, db: D) -> dict[str, object]:
    roles = [await _role_by_name(db, p.tenant_id, name) for name in dict.fromkeys(body.roles)]
    user = User(
        tenant_id=p.tenant_id,
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        is_active=True,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A user with this email already exists"
        ) from exc
    for role in roles:
        db.add(UserRole(tenant_id=p.tenant_id, user_id=user.id, role_id=role.id))
    await record_change(
        db,
        p.tenant_id,
        p.user_id,
        "created",
        "user",
        str(user.id),
        {"roles": [r.name for r in roles]},
    )
    await db.commit()
    return await _user_view(db, user)


@router.patch("/users/{user_id}")
async def update_user(user_id: UUID, body: UserUpdate, p: P, db: D) -> dict[str, object]:
    user = await _user(db, p.tenant_id, user_id)
    changes: dict[str, object] = {}
    if body.display_name is not None:
        user.display_name = body.display_name
        changes["display_name"] = body.display_name
    if body.is_active is not None:
        if user.id == p.user_id and not body.is_active:
            raise HTTPException(status.HTTP_409_CONFLICT, "You cannot deactivate your own account")
        user.is_active = body.is_active
        changes["is_active"] = body.is_active
    await record_change(db, p.tenant_id, p.user_id, "updated", "user", str(user.id), changes)
    await db.commit()
    return await _user_view(db, user)


@router.post("/users/{user_id}/roles")
async def assign_role(user_id: UUID, body: RoleAssignment, p: P, db: D) -> dict[str, object]:
    user = await _user(db, p.tenant_id, user_id)
    role = await _role_by_name(db, p.tenant_id, body.role)
    exists = await db.scalar(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    )
    if exists is None:
        db.add(UserRole(tenant_id=p.tenant_id, user_id=user.id, role_id=role.id))
        await record_change(
            db, p.tenant_id, p.user_id, "role_assigned", "user", str(user.id), {"role": role.name}
        )
        await db.commit()
    return await _user_view(db, user)


@router.delete("/users/{user_id}/roles/{role_name}")
async def remove_role(user_id: UUID, role_name: str, p: P, db: D) -> dict[str, object]:
    user = await _user(db, p.tenant_id, user_id)
    role = await _role_by_name(db, p.tenant_id, role_name)
    if user.id == p.user_id and role.name == PROTECTED_ROLE:
        raise HTTPException(status.HTTP_409_CONFLICT, "You cannot remove your own Owner role")
    await db.execute(
        delete(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
            UserRole.tenant_id == p.tenant_id,
        )
    )
    await record_change(
        db, p.tenant_id, p.user_id, "role_removed", "user", str(user.id), {"role": role.name}
    )
    await db.commit()
    return await _user_view(db, user)


@router.get("/roles")
async def list_roles(p: P, db: D) -> list[dict[str, Any]]:
    roles = (
        await db.scalars(
            select(Role)
            .where(Role.tenant_id == p.tenant_id, Role.is_deleted.is_(False))
            .order_by(Role.name)
        )
    ).all()
    result = []
    for role in roles:
        codes = await db.scalars(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
            .order_by(Permission.code)
        )
        result.append(
            {
                "id": str(role.id),
                "name": role.name,
                "description": role.description,
                "standard": role.name in STANDARD_ROLES,
                "permissions": list(codes.all()),
            }
        )
    return result


@router.put("/roles/{role_id}/permissions")
async def set_role_permissions(
    role_id: UUID, body: RolePermissionsUpdate, p: P, db: D
) -> dict[str, object]:
    role = await db.scalar(
        select(Role).where(
            Role.id == role_id, Role.tenant_id == p.tenant_id, Role.is_deleted.is_(False)
        )
    )
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    if role.name == PROTECTED_ROLE:
        raise HTTPException(status.HTTP_409_CONFLICT, "The Owner role's permissions are fixed")
    unknown = sorted(set(body.permissions) - set(CATALOG))
    if unknown or "platform.tenants.create" in body.permissions:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unknown or non-grantable permissions: {unknown or ['platform.tenants.create']}",
        )
    permissions = (
        await db.scalars(select(Permission).where(Permission.code.in_(body.permissions)))
    ).all()
    await db.execute(
        delete(RolePermission).where(
            RolePermission.role_id == role.id, RolePermission.tenant_id == p.tenant_id
        )
    )
    for permission in permissions:
        db.add(RolePermission(tenant_id=p.tenant_id, role_id=role.id, permission_id=permission.id))
    await record_change(
        db,
        p.tenant_id,
        p.user_id,
        "permissions_set",
        "role",
        str(role.id),
        {"permissions": sorted(body.permissions)},
    )
    await db.commit()
    return {"id": str(role.id), "name": role.name, "permissions": sorted(body.permissions)}


@router.get("/permissions")
async def list_permissions(p: P) -> list[dict[str, str]]:
    return [{"code": code, "description": text} for code, text in sorted(CATALOG.items())]


@router.get("/me/permissions")
async def my_permissions(p: P) -> dict[str, object]:
    granted = await load_access(p)
    return {"user_id": str(p.user_id), "permissions": sorted(granted or set())}
