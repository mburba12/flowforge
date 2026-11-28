from flowforge.main import app


def test_part2a_openapi_available():
    assert app.openapi()["paths"]
