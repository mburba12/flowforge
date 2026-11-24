from flowforge.db.base import Base
from flowforge.phase4b import models  # noqa:F401


def test_tables() -> None:
    assert {
        "tax_jurisdictions",
        "tax_authorities",
        "tax_registrations",
        "tax_rules",
        "worker_tax_elections",
        "payroll_tax_calculations",
    } <= set(Base.metadata.tables)
