from flowforge.main import app


def test_phase1_routes() -> None:
    paths = app.openapi()["paths"]
    for path in [
        "/api/v1/health",
        "/api/v1/auth/bootstrap",
        "/api/v1/auth/login",
        "/api/v1/me",
        "/api/v1/roles",
        "/api/v1/audit",
        "/api/v1/workflows",
        "/api/v1/documents",
        "/api/v1/notifications",
        "/api/v1/integrations",
    ]:
        assert path in paths


def test_phase1_version() -> None:
    assert app.version == "1.0.0-phase1"
