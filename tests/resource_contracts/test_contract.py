from flowforge.main import app


def test_business_resource_contract_is_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/business/resources" in paths
    assert "/api/v1/business/{resource}" in paths
    assert "/api/v1/business/{resource}/{record_id}" in paths
