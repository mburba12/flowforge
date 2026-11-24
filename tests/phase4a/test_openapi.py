from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for path in [
        "/phase4a/status",
        "/api/v4a/workers",
        "/api/v4a/work-locations",
        "/api/v4a/workers/{worker_id}/assignments",
        "/api/v4a/workers/{worker_id}/compensation",
        "/api/v4a/workers/{worker_id}/bank-accounts",
        "/api/v4a/workers/{worker_id}/tax-profiles",
        "/api/v4a/benefit-plans",
        "/api/v4a/workers/{worker_id}/benefit-enrollments",
    ]:
        assert path in paths
