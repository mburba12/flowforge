from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for p in [
        "/phase4c/status",
        "/api/v4c/connections/link-session",
        "/api/v4c/connections/exchange",
        "/api/v4c/accounts/{account_id}/gl-mapping",
        "/api/v4c/transactions/manual",
        "/api/v4c/connections/{connection_id}/sync",
    ]:
        assert p in paths
