from flowforge.db.base import Base
from flowforge.phase4b_stage2 import models  # noqa:F401


def test_tables() -> None:
    expected = {
        "tax_liabilities",
        "tax_filing_calendars",
        "tax_returns",
        "tax_return_lines",
        "tax_remittances",
        "tax_remittance_allocations",
        "tax_notices",
        "tax_reconciliation_runs",
    }
    assert expected <= set(Base.metadata.tables)
