from flowforge.db.base import Base
from flowforge.phase4c_stage2 import models  # noqa:F401


def test_tables() -> None:
    expected = {
        "payment_connections",
        "merchant_locations",
        "payment_terminals",
        "processor_payments",
        "processor_fees",
        "processor_refunds",
        "processor_payouts",
        "payment_webhook_events",
    }
    assert expected <= set(Base.metadata.tables)
    for name in expected:
        assert "tenant_id" in Base.metadata.tables[name].columns
