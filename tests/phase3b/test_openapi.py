from flowforge.main import app


def test_routes():
    paths = app.openapi()["paths"]
    for p in [
        "/phase3b/status",
        "/api/v3b/customers",
        "/api/v3b/products",
        "/api/v3b/warehouses",
        "/api/v3b/locations",
        "/api/v3b/inventory/adjust",
        "/api/v3b/orders",
        "/api/v3b/orders/{order_id}/reserve",
        "/api/v3b/orders/{order_id}/ship-invoice",
        "/api/v3b/receipts",
    ]:
        assert p in paths
