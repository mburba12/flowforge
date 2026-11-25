from flowforge.db.base import Base
from flowforge.phase4c import models  # noqa:F401


def test_tables() -> None:
    expected = {
        "bank_connections",
        "connected_bank_accounts",
        "bank_account_gl_mappings",
        "bank_transactions",
        "bank_balance_snapshots",
        "bank_sync_runs",
        "bank_webhook_events",
    }
    assert expected <= set(Base.metadata.tables)


def test_tenant_scope() -> None:
    for n in [
        "bank_connections",
        "connected_bank_accounts",
        "bank_account_gl_mappings",
        "bank_transactions",
        "bank_balance_snapshots",
        "bank_sync_runs",
    ]:
        assert "tenant_id" in Base.metadata.tables[n].columns
