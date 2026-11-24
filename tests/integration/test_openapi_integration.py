from flowforge.main import app


def test_phase_routers_mounted() -> None:
    paths = app.openapi()["paths"]

    assert "/phase1a/status" in paths
    assert "/phase1b/health" in paths
    assert "/phase1/status" in paths
