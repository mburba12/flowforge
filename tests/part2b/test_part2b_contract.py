from flowforge.main import app


def test_part2b_openapi_exists() -> None:
    assert app.openapi()["paths"]
