from flowforge.main import app


def test_catalog_is_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/catalog/tables" in paths
    assert "/api/v1/catalog/tables/{table_name}/records" in paths
