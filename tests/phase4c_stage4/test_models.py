from flowforge.db.base import Base
from flowforge.phase4c_stage4 import models  # noqa:F401


def test_tables() -> None:
    expected = {
        "logistics_connections",
        "shipping_services",
        "shipping_rate_quotes",
        "logistics_shipments",
        "shipping_packages",
        "shipping_labels",
        "tracking_events",
        "return_shipments",
        "fulfillment_orders",
        "logistics_inventory_balances",
        "customs_documents",
        "logistics_sync_runs",
        "logistics_webhook_events",
    }
    assert expected <= set(Base.metadata.tables)
    for name in expected:
        assert "tenant_id" in Base.metadata.tables[name].columns
