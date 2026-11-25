from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for p in [
        "/phase4c/stage3/status",
        "/api/v4c/commerce/providers",
        "/api/v4c/commerce/connections",
        "/api/v4c/commerce/connections/{connection_id}/sync",
        "/api/v4c/commerce/connections/{connection_id}/webhooks",
    ]:
        assert p in paths
