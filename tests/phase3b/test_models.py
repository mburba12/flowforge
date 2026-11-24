from flowforge.db.base import Base
from flowforge.phase3b import models  # noqa:F401


def test_tables():
    expected = {
        "customer_profiles",
        "units_of_measure",
        "products",
        "warehouses",
        "warehouse_locations",
        "inventory_balances",
        "inventory_movements",
        "sales_orders",
        "sales_order_lines",
        "inventory_reservations",
        "shipments",
        "customer_invoices",
        "ar_open_items",
        "customer_receipts",
        "receipt_allocations",
    }
    assert expected <= set(Base.metadata.tables)


def test_tenant_scope():
    for n in [
        "customer_profiles",
        "products",
        "warehouses",
        "warehouse_locations",
        "inventory_balances",
        "inventory_movements",
        "sales_orders",
        "sales_order_lines",
        "inventory_reservations",
        "shipments",
        "customer_invoices",
        "ar_open_items",
        "customer_receipts",
        "receipt_allocations",
    ]:
        assert "tenant_id" in Base.metadata.tables[n].columns
