"""Automated tests for health check endpoints and core API behaviors."""

from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient) -> None:
    """GET /health must return 200 OK with simple health payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_api_v1_health_endpoint(client: TestClient) -> None:
    """GET /api/v1/health must return 200 OK with version and status metadata."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "database" in data
    assert data["database"] in ("connected", "disconnected")


def test_cors_headers_allowed_origin(client: TestClient) -> None:
    """Requests originating from allowed origin must include CORS response headers."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_preflight_request(client: TestClient) -> None:
    """OPTIONS preflight requests from allowed origin must succeed with 200."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_not_found_returns_structured_error(client: TestClient) -> None:
    """Requests to non-existent endpoints should return structured 404 error."""
    response = client.get("/api/v1/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == 404
