from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/phase4c/stage7/status",
        "/api/v4c/engagement/providers",
        "/api/v4c/engagement/connections",
        "/api/v4c/engagement/connections/{connection_id}/sync",
        "/api/v4c/engagement/connections/{connection_id}/webhooks",
    }
    assert required <= set(paths)
