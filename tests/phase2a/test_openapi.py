from flowforge.main import app


def test_phase2a_routes() -> None:
    paths = app.openapi()["paths"]
    for p in [
        "/phase2a/status",
        "/api/v2/organizations",
        "/api/v2/people",
        "/api/v2/parties/search",
        "/api/v2/parties/{party_id}",
        "/api/v2/organization-units",
    ]:
        assert p in paths
