from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import event, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import SessionTransaction

from flowforge.core.config import settings
from flowforge.core.security import (
    Principal,
    current_principal,
)

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@event.listens_for(
    Session,
    "after_begin",
)
def install_transaction_tenant_context(
    session: Session,
    transaction: SessionTransaction,
    connection: Connection,
) -> None:
    tenant_id = session.info.get("tenant_id")
    user_id = session.info.get("user_id")

    if tenant_id is None:
        return

    if user_id is None:
        raise RuntimeError("Tenant-scoped session is missing user context")

    connection.execute(
        text(
            """
            SELECT
                set_config(
                    'app.current_tenant_id',
                    :tenant_id,
                    true
                ),
                set_config(
                    'app.current_user_id',
                    :user_id,
                    true
                )
            """
        ),
        {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
        },
    )


async def enter_tenant_context(
    session: AsyncSession,
    tenant_id: UUID,
    user_id: UUID | None = None,
) -> None:
    """
    Install tenant (and optionally user) context on the current transaction.

    For pre-principal flows (bootstrap, login) that use get_db: once the
    tenant is known server-side, row-level security policies on tenant-owned
    tables require app.current_tenant_id. The setting is transaction-local.
    When user_id is supplied, it is also stored in session.info so the
    after_begin listener reinstalls it for later transactions.
    """
    await session.execute(
        text(
            "SELECT set_config('app.current_tenant_id', :tenant_id, true),"
            " set_config('app.current_user_id', :user_id, true)"
        ),
        {"tenant_id": str(tenant_id), "user_id": str(user_id) if user_id else ""},
    )
    if user_id is not None:
        session.info["tenant_id"] = tenant_id
        session.info["user_id"] = user_id


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    Bootstrap database dependency.

    Use only before a verified tenant principal
    exists, such as login and token creation.
    """
    async with SessionLocal() as session:
        yield session


async def get_tenant_db(
    principal: Annotated[
        Principal,
        Depends(current_principal),
    ],
) -> AsyncIterator[AsyncSession]:
    """
    Authenticated tenant-scoped dependency.

    Tenant context is reinstalled automatically
    whenever SQLAlchemy begins a transaction,
    including after a service calls commit().
    """
    async with SessionLocal() as session:
        session.info["tenant_id"] = UUID(str(principal.tenant_id))
        session.info["user_id"] = UUID(str(principal.user_id))

        yield session
