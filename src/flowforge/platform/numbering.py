"""Atomic per-tenant document numbering.

count()+1 numbering let two concurrent requests in one tenant pick the same number
(the second failed on a unique constraint). A row in document_sequences per
(tenant, key) is incremented with INSERT ... ON CONFLICT DO UPDATE ... RETURNING,
which Postgres serialises on the row, so every caller gets a distinct number. The
first use of a key starts after the rows that already exist, so numbering continues.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# key -> (table whose existing rows seed the sequence, prefix)
SEQUENCES: dict[str, tuple[str, str]] = {
    "party": ("parties", "P"),
    "journal": ("journal_entries", "JE"),
    "vendor": ("vendor_profiles", "V"),
    "purchase_order": ("purchase_orders", "PO"),
    "goods_receipt": ("goods_receipts", "GR"),
    "sales_order": ("sales_orders", "SO"),
    "customer": ("customer_profiles", "C"),
    "worker": ("worker_profiles", "W"),
    "payroll_run": ("payroll_runs", "PR"),
}


async def next_number(db: AsyncSession, tenant_id: UUID, key: str) -> str:
    table, prefix = SEQUENCES[key]  # internal constants only; never user input
    value = await db.scalar(
        text(
            "INSERT INTO document_sequences (tenant_id, key, value)"
            f" VALUES (:t, :k, (SELECT count(*) + 1 FROM {table} WHERE tenant_id = :t))"
            " ON CONFLICT (tenant_id, key)"
            " DO UPDATE SET value = document_sequences.value + 1"
            " RETURNING value"
        ),
        {"t": tenant_id, "k": key},
    )
    return f"{prefix}-{int(value or 0):08d}"
