from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/phase4c/stage6/status",
        "/api/v4c/workforce/providers",
        "/api/v4c/workforce/connections",
        "/api/v4c/workforce/connections/{connection_id}/sync",
        "/api/v4c/workforce/connections/{connection_id}/webhooks",
    }
    assert required <= set(paths)
