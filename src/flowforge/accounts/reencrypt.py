"""Bring every encrypted value onto the current key, and encrypt what is still plain.

    python -m flowforge.accounts.reencrypt            # do it
    python -m flowforge.accounts.reencrypt --check    # report only; exit 1 if work remains

Run as the database owner (it reads every workspace): the production `migrate` service
has that connection (ALEMBIC_DATABASE_URL). Needs the same keys as the API: the current
FLOWFORGE_CREDENTIALS_KEY, plus whatever sealed the old values (the JWT secret for the
legacy derived key, FLOWFORGE_CREDENTIALS_KEY_PREVIOUS for older dedicated keys).
Every rewrite is verified by decrypting it again before it is saved.
"""

import asyncio
import os
import sys
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from flowforge.core import crypto
from flowforge.core.encrypted_types import ENCRYPTED_COLUMNS

# Credentials sealed with a per-row context: (table, column, context builder).
ROW_CONTEXT: list[tuple[str, str, Callable[[str, str], str]]] = [
    ("bank_connections", "encrypted_access_token", lambda t, i: f"{t}:bank:{i}"),
    ("carrier_accounts", "encrypted_credentials", lambda t, i: f"{t}:carrier:{i}"),
    ("payroll_migrations", "encrypted_tokens", lambda t, i: f"{t}:payroll:{i}"),
]


def _fixed(context: str) -> Callable[[str, str], str]:
    """Columns sealed with one context for every row (the column name)."""

    def build(_tenant: str, _row: str) -> str:
        return context

    return build


UNREADABLE: list[str] = []


async def _text_rows(
    conn: AsyncConnection, table: str, column: str, context: Callable[[str, str], str], check: bool
) -> tuple[int, int]:
    rows = (
        await conn.execute(
            text(f"SELECT id, tenant_id, {column} FROM {table} WHERE {column} IS NOT NULL")  # noqa: S608
        )
    ).all()
    pending = done = 0
    for row_id, tenant_id, value in rows:
        if not crypto.needs_reencryption(value):
            continue
        pending += 1
        if check:
            continue
        ctx = context(str(tenant_id), str(row_id))
        try:
            plain = crypto.decrypt(value, ctx) if crypto.is_encrypted(value) else value
        except Exception:  # noqa: BLE001 - report and leave the value as it is
            UNREADABLE.append(f"{table}.{column} id={row_id}")
            continue
        sealed = crypto.encrypt(plain, ctx)
        assert crypto.decrypt(sealed, ctx) == plain
        await conn.execute(
            text(f"UPDATE {table} SET {column} = :v WHERE id = :i"),  # noqa: S608
            {"v": sealed, "i": row_id},
        )
        done += 1
    return pending, done


async def _bytes_rows(
    conn: AsyncConnection, table: str, column: str, ctx: str, check: bool
) -> tuple[int, int]:
    ids = (
        (await conn.execute(text(f"SELECT id FROM {table} WHERE {column} IS NOT NULL")))
        .scalars()
        .all()
    )  # noqa: S608
    pending = done = 0
    for row_id in ids:  # one row at a time: files can be large
        value = await conn.scalar(
            text(f"SELECT {column} FROM {table} WHERE id = :i"), {"i": row_id}
        )  # noqa: S608
        data = bytes(value)
        if not crypto.bytes_need_reencryption(data):
            continue
        pending += 1
        if check:
            continue
        try:
            plain = crypto.decrypt_bytes(data, ctx)
        except Exception:  # noqa: BLE001 - report and leave the value as it is
            UNREADABLE.append(f"{table}.{column} id={row_id}")
            continue
        sealed = crypto.encrypt_bytes(plain, ctx)
        assert crypto.decrypt_bytes(sealed, ctx) == plain
        await conn.execute(
            text(f"UPDATE {table} SET {column} = :v WHERE id = :i"), {"v": sealed, "i": row_id}
        )  # noqa: S608
        done += 1
    return pending, done


async def run(check: bool) -> int:
    url = os.environ.get("ALEMBIC_DATABASE_URL") or os.environ["FLOWFORGE_DATABASE_URL"]
    engine = create_async_engine(url)
    crypto.reset_keys()
    if not crypto.uses_dedicated_key():
        print("WARNING: FLOWFORGE_CREDENTIALS_KEY is not set; values stay on the JWT-derived key.")
    total_pending = 0
    try:
        async with engine.begin() as conn:
            for table, column, context in ROW_CONTEXT:
                pending, done = await _text_rows(conn, table, column, context, check)
                total_pending += pending - done
                print(f"{table}.{column}: {pending} to update, {done} updated")
            for table, column, ctx, kind in ENCRYPTED_COLUMNS:
                if kind == "text":
                    pending, done = await _text_rows(conn, table, column, _fixed(ctx), check)
                else:
                    pending, done = await _bytes_rows(conn, table, column, ctx, check)
                total_pending += pending - done
                print(f"{table}.{column}: {pending} to update, {done} updated")
    finally:
        await engine.dispose()
    if UNREADABLE:
        print(f"UNREADABLE (left unchanged; reconnect these accounts): {len(UNREADABLE)}")
        for item in UNREADABLE:
            print(f"  {item}")
    if total_pending - len(UNREADABLE) > 0:
        print(f"REENCRYPTION INCOMPLETE: {total_pending} value(s) not on the current key")
        return 1
    if UNREADABLE:
        print("DONE: all readable values are on the current key; the ones above were left as is")
        return 2
    print("ALL ENCRYPTED VALUES ARE ON THE CURRENT KEY")
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(check="--check" in sys.argv)))


if __name__ == "__main__":
    main()
