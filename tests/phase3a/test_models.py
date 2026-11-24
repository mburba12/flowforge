from flowforge.db.base import Base
from flowforge.phase3a import models  # noqa:F401


def test_tables():
    expected = {
        "vendor_profiles",
        "purchase_orders",
        "purchase_order_lines",
        "goods_receipts",
        "goods_receipt_lines",
        "vendor_invoices",
        "vendor_invoice_lines",
        "ap_match_policies",
        "invoice_matches",
        "ap_open_items",
    }
    assert expected <= set(Base.metadata.tables)


def test_tenant_scope():
    for n in [
        "vendor_profiles",
        "purchase_orders",
        "purchase_order_lines",
        "goods_receipts",
        "goods_receipt_lines",
        "vendor_invoices",
        "vendor_invoice_lines",
        "ap_match_policies",
        "invoice_matches",
        "ap_open_items",
    ]:
        assert "tenant_id" in Base.metadata.tables[n].columns
