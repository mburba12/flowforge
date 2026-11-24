from flowforge.db.base import Base
from flowforge.phase4a_stage3 import models  # noqa: F401


def test_tables() -> None:
    expected = {
        "payroll_runs",
        "payroll_run_workers",
        "payroll_earnings",
        "payroll_deductions",
        "payroll_tax_lines",
        "payroll_liabilities",
        "payroll_payments",
        "payroll_reconciliation_runs",
    }
    assert expected <= set(Base.metadata.tables)
