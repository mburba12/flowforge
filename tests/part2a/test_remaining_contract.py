from flowforge.main import app


def test_part2a_resource_contract_registered() -> None:
    assert "/api/v1/resources/{resource}" in app.openapi()["paths"]
