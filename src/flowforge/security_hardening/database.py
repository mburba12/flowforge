from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .context import require_tenant_context

TENANT_CONTEXT_SQL = """
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


async def apply_tenant_context(
    session: AsyncSession,
) -> None:
    context = require_tenant_context()

    await session.execute(
        text(TENANT_CONTEXT_SQL),
        {
            "tenant_id": str(context.tenant_id),
            "user_id": str(context.user_id),
        },
    )


def assert_safe_database_role(
    role_name: str,
    bypass_rls: bool,
    is_superuser: bool,
) -> None:
    if bypass_rls or is_superuser:
        raise RuntimeError(f"Unsafe application database role: {role_name}")
