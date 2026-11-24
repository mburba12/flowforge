from flowforge.main import app


def test_phase3_final_routes() -> None:
    paths = app.openapi()["paths"]
    assert "/phase3/status" in paths
    assert "/api/v3/final/reconcile" in paths
