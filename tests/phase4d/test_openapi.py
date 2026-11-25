from flowforge.main import app


def test_routes() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/phase4/4d/status",
        "/api/v4/entities",
        "/api/v4/entities/{entity_id}",
        "/api/v4/entities/{entity_id}/lineage",
        "/api/v4/entities/match",
        "/api/v4/entities/merge-proposals",
        "/api/v4/entities/merge-proposals/{proposal_id}/approve",
        "/api/v4/entities/relationships",
    }
    assert required <= set(paths)
