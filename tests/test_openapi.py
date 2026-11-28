from fastapi.testclient import TestClient

from flowforge.main import app


def test_openapi_schema() -> None:
    schema = app.openapi()

    assert schema["info"]["title"] == "Krov WorkAgent API"
    assert "/api/v1/health" in schema["paths"]


def test_health_endpoint() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
