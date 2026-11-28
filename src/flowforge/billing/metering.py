"""What each workspace uses: requests (counted as they happen) and storage (measured daily).

Free, never counted: sign-in/sign-up, health, moving data in (payroll imports, bank
statement imports, shipment imports, uploads of import files) and data sync (bank feed
refresh, shipment tracking refresh, Gusto sync).
"""

import re
from collections import Counter
from datetime import UTC, date, datetime
from threading import Lock
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import UsageDay

FREE_PATHS = re.compile(
    r"^/api/v1/(auth/|health|me/permissions|me/preferences|account-billing/)"
    r"|^/api/v1/payroll-migration/"
    r"|^/api/v1/banking/(statements|link|connections/[^/]+/sync)"
    r"|^/api/v1/shipping/(shipments/import|refresh|shipments/[^/]+/refresh)"
    r"|^/api/v1/connections/"
)

_counts: Counter[tuple[UUID, date]] = Counter()
_lock = Lock()


def today() -> date:
    return datetime.now(UTC).date()


def count_request(tenant_id: Any, path: str) -> None:
    """Called for every authorized API request (from authorization.enforce)."""
    if FREE_PATHS.search(path):
        return
    try:
        key = (UUID(str(tenant_id)), today())
    except ValueError:
        return
    with _lock:
        _counts[key] += 1


def take_counts() -> dict[tuple[UUID, date], int]:
    with _lock:
        taken = dict(_counts)
        _counts.clear()
    return taken


def restore_counts(counts: dict[tuple[UUID, date], int]) -> None:
    with _lock:
        for key, n in counts.items():
            _counts[key] += n


async def add_requests(db: AsyncSession, tenant_id: UUID, day: date, n: int) -> None:
    """Add n requests to the workspace's usage for day (db is in that tenant's context)."""
    statement = insert(UsageDay).values(tenant_id=tenant_id, day=day, requests=n)
    await db.execute(
        statement.on_conflict_do_update(
            constraint="uq_usage_day", set_={"requests": UsageDay.requests + n}
        )
    )


async def storage_by_tenant(db: AsyncSession) -> dict[UUID, int]:
    rows = await db.execute(text("SELECT tenant_id, bytes FROM ff_tenant_storage_bytes()"))
    return {row[0]: int(row[1] or 0) for row in rows}


async def record_snapshot(
    db: AsyncSession, tenant_id: UUID, day: date, storage_bytes: int, bank_accounts: int
) -> None:
    statement = insert(UsageDay).values(
        tenant_id=tenant_id,
        day=day,
        storage_bytes=storage_bytes,
        bank_accounts=bank_accounts,
        measured_at=func.now(),
    )
    await db.execute(
        statement.on_conflict_do_update(
            constraint="uq_usage_day",
            set_={
                "storage_bytes": storage_bytes,
                "bank_accounts": bank_accounts,
                "measured_at": func.now(),
            },
        )
    )


async def bank_account_count(db: AsyncSession, tenant_id: UUID) -> int:
    from flowforge.phase4c.models import ConnectedBankAccount

    return int(
        await db.scalar(
            select(func.count())
            .select_from(ConnectedBankAccount)
            .where(ConnectedBankAccount.tenant_id == tenant_id)
        )
        or 0
    )
