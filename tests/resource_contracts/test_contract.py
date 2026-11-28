from flowforge.main import app


def test_business_resource_contract_is_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/business/resources" in paths
    assert "/api/v1/business/{resource}" in paths
    assert "/api/v1/business/{resource}/{record_id}" in paths


def test_business_resource_contract_is_read_only() -> None:
    paths = app.openapi()["paths"]
    for path, operations in paths.items():
        if path.startswith("/api/v1/business"):
            assert set(operations) <= {"get", "parameters"}, path


def test_business_resource_contract_requires_authentication() -> None:
    paths = app.openapi()["paths"]
    for path, operations in paths.items():
        if path.startswith("/api/v1/business"):
            assert operations["get"].get("security"), path
