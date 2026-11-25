from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for p in [
        "/phase4c/stage4/status",
        "/api/v4c/logistics/providers",
        "/api/v4c/logistics/connections",
        "/api/v4c/logistics/connections/{connection_id}/sync",
        "/api/v4c/logistics/connections/{connection_id}/webhooks",
    ]:
        assert p in paths
