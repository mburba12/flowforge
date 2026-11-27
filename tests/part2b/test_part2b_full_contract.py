from flowforge.main import app


def test_part2b_platform_contract() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/platform/{resource}" in paths
    assert "/api/v1/platform/{resource}/{record_id}" in paths
    assert "/api/v1/platform/search/all" in paths
