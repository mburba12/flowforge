from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for p in [
        "/phase4c/stage2/status",
        "/api/v4c/payments/connections",
        "/api/v4c/payments/connections/{connection_id}/sync",
        "/api/v4c/payments/connections/{connection_id}/webhooks",
    ]:
        assert p in paths
