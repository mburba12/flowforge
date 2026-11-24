from flowforge.db.base import Base
from flowforge.phase2b import models  # noqa: F401


def test_phase2b_tables() -> None:
    expected = {
        "currencies",
        "exchange_rates",
        "fiscal_calendars",
        "accounting_periods",
        "ledgers",
        "accounts",
        "financial_dimensions",
        "dimension_values",
        "journal_entries",
        "journal_lines",
        "account_balances",
    }
    assert expected <= set(Base.metadata.tables)


def test_tenant_scoped_tables() -> None:
    for name in [
        "exchange_rates",
        "fiscal_calendars",
        "accounting_periods",
        "ledgers",
        "accounts",
        "financial_dimensions",
        "dimension_values",
        "journal_entries",
        "journal_lines",
        "account_balances",
    ]:
        assert "tenant_id" in Base.metadata.tables[name].columns
