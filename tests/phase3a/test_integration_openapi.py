from flowforge.main import app


def test_ap_integration_routes():
    paths = app.openapi()["paths"]
    assert "/api/v3/vendor-invoices/{invoice_id}/match" in paths
    assert "/api/v3/vendor-invoices/{invoice_id}/post" in paths
