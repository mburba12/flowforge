from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for p in [
        "/phase4c/stage5/status",
        "/api/v4c/finance/providers",
        "/api/v4c/finance/connections",
        "/api/v4c/finance/connections/{connection_id}/sync",
        "/api/v4c/finance/connections/{connection_id}/webhooks",
    ]:
        assert p in paths
