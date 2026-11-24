from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    for path in [
        "/phase4a/stage3/status",
        "/api/v4a/payroll/runs",
        "/api/v4a/payroll/runs/{run_id}/calculate",
        "/api/v4a/payroll/runs/{run_id}/approve",
        "/api/v4a/payroll/runs/{run_id}/post",
        "/api/v4a/payroll/runs/{run_id}/payments",
        "/api/v4a/payroll/runs/{run_id}/reconcile",
    ]:
        assert path in paths
