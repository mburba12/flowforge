from flowforge.main import app


def test_routes():
    paths = app.openapi()["paths"]
    for p in [
        "/phase3a/status",
        "/api/v3/vendors",
        "/api/v3/purchase-orders",
        "/api/v3/purchase-orders/{po_id}/submit",
        "/api/v3/purchase-orders/{po_id}/approve",
        "/api/v3/goods-receipts",
        "/api/v3/vendor-invoices",
    ]:
        assert p in paths
