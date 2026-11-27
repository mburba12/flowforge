import asyncio
import os

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from flowforge.db.base import Base
from flowforge.integration import models as phase1_integration_models  # noqa: F401
from flowforge.phase2a import models as phase2a_models  # noqa: F401
from flowforge.phase2b import models as phase2b_models  # noqa: F401
from flowforge.phase3a import integration_models  # noqa: F401
from flowforge.phase3a import integration_models as phase3a_integration_models  # noqa: F401
from flowforge.phase3a import models as phase3a_models  # noqa: F401
from flowforge.phase3b import models as phase3b_models  # noqa: F401
from flowforge.phase4a import models as phase4a_models  # noqa: F401
from flowforge.phase4a_stage2 import models as phase4a_stage2_models  # noqa: F401
from flowforge.phase4a_stage3 import models as phase4a_stage3_models  # noqa: F401
from flowforge.phase4b import models as phase4b_models  # noqa: F401
from flowforge.phase4b_stage2 import models as phase4b_stage2_models  # noqa: F401
from flowforge.phase4c import models as phase4c_models  # noqa: F401
from flowforge.phase4c_stage2 import models as phase4c_stage2_models  # noqa: F401
from flowforge.phase4c_stage3 import models as phase4c_stage3_models  # noqa: F401
from flowforge.phase4c_stage4 import models as phase4c_stage4_models  # noqa: F401
from flowforge.phase4c_stage5 import models as phase4c_stage5_models  # noqa: F401
from flowforge.phase4c_stage6 import models as phase4c_stage6_models  # noqa: F401
from flowforge.phase4c_stage7 import models as phase4c_stage7_models  # noqa: F401
from flowforge.phase4d import models as phase4d_models  # noqa: F401
from flowforge.phase4e import models as phase4e_models  # noqa: F401
from flowforge.phase4f import models as phase4f_models  # noqa: F401
from flowforge.phase4g import models as phase4g_models  # noqa: F401
from flowforge.phase4h import models as phase4h_models  # noqa: F401
from flowforge.phase4i import models as phase4i_models  # noqa: F401
from flowforge.phase4j import models as phase4j_models  # noqa: F401
from flowforge.phase5a import models as phase5a_models  # noqa: F401
from flowforge.phase5b import models as phase5b_models  # noqa: F401
from flowforge.platform import models  # noqa:F401

config = context.config
target_metadata = Base.metadata

# Deployments (for example the production "migrate" service) pass the owner
# connection through the environment; local tooling keeps using alembic.ini.
if os.environ.get("ALEMBIC_DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.environ["ALEMBIC_DATABASE_URL"])


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
