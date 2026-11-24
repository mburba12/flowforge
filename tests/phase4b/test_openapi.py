from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for p in [
        "/phase4b/status",
        "/api/v4b/jurisdictions",
        "/api/v4b/tax-rules",
        "/api/v4b/worker-elections",
        "/api/v4b/calculate",
    ]:
        assert p in paths
