from flowforge.db.base import Base
from flowforge.phase3a import integration_models  # noqa:F401


def test_integration_tables():
    assert {"vendor_payments", "vendor_payment_allocations", "ap_reconciliation_runs"} <= set(
        Base.metadata.tables
    )


def test_tenant_scope():
    for name in ["vendor_payments", "vendor_payment_allocations", "ap_reconciliation_runs"]:
        assert "tenant_id" in Base.metadata.tables[name].columns
