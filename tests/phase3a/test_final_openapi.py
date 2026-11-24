from flowforge.main import app


def test_final_phase3a_routes() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v3/ap/open-items/{open_item_id}/pay" in paths
    assert "/api/v3/ap/reconcile" in paths
