from flowforge.db.base import Base
from flowforge.phase4c_stage5 import models  # noqa:F401


def test_tables() -> None:
    expected = {
        "finance_connections",
        "finance_external_accounts",
        "finance_account_mappings",
        "finance_parties",
        "finance_documents",
        "finance_payment_statuses",
        "finance_external_journal_entries",
        "finance_external_journal_lines",
        "finance_expense_transactions",
        "finance_treasury_positions",
        "finance_reconciliation_exceptions",
        "finance_sync_runs",
        "finance_webhook_events",
    }
    assert expected <= set(Base.metadata.tables)
    for name in expected:
        assert "tenant_id" in Base.metadata.tables[name].columns
