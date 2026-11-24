from flowforge.db.base import Base
from flowforge.phase4a import models  # noqa: F401


def test_tables() -> None:
    expected = {
        "worker_profiles",
        "work_locations",
        "worker_assignments",
        "compensation_rates",
        "worker_bank_accounts",
        "worker_tax_profiles",
        "benefit_plans",
        "benefit_enrollments",
    }
    assert expected <= set(Base.metadata.tables)


def test_tenant_scope() -> None:
    for name in [
        "worker_profiles",
        "work_locations",
        "worker_assignments",
        "compensation_rates",
        "worker_bank_accounts",
        "worker_tax_profiles",
        "benefit_plans",
        "benefit_enrollments",
    ]:
        assert "tenant_id" in Base.metadata.tables[name].columns
