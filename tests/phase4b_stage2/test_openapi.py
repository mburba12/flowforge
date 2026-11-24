from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for path in [
        "/phase4b/stage2/status",
        "/api/v4b/liabilities",
        "/api/v4b/returns",
        "/api/v4b/returns/{return_id}/approve",
        "/api/v4b/returns/{return_id}/remit",
        "/api/v4b/notices",
        "/api/v4b/notices/{notice_id}/resolve",
        "/api/v4b/reconcile",
    ]:
        assert path in paths
