from flowforge.db.base import Base
from flowforge.phase4c_stage3 import models  # noqa:F401


def test_tables() -> None:
    expected = {
        "commerce_connections",
        "commerce_customers",
        "commerce_products",
        "commerce_variants",
        "commerce_orders",
        "commerce_order_lines",
        "commerce_fulfillments",
        "commerce_refunds",
        "commerce_settlements",
        "commerce_sync_runs",
        "commerce_webhook_events",
    }
    assert expected <= set(Base.metadata.tables)
    for name in expected:
        assert "tenant_id" in Base.metadata.tables[name].columns
