from flowforge.main import app


def test_phase2b_routes() -> None:
    paths = app.openapi()["paths"]
    for path in [
        "/phase2b/status",
        "/api/v2/currencies",
        "/api/v2/fiscal-calendars",
        "/api/v2/accounting-periods",
        "/api/v2/ledgers",
        "/api/v2/accounts",
        "/api/v2/journals",
        "/api/v2/journals/{journal_id}/approve",
        "/api/v2/journals/{journal_id}/post",
        "/api/v2/trial-balance",
    ]:
        assert path in paths
