from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for path in [
        "/phase4a/stage2/status",
        "/api/v4a/work-schedules",
        "/api/v4a/time-entries",
        "/api/v4a/time-entries/{entry_id}/approve",
        "/api/v4a/leave-types",
        "/api/v4a/leave-requests",
        "/api/v4a/pay-groups",
        "/api/v4a/pay-periods",
    ]:
        assert path in paths
