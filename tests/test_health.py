"""Tests for the app's core endpoints and startup."""


def test_app_starts_up(client):
    """If this fixture builds without raising, lifespan startup succeeded."""
    # Reaching here means TestClient entered the `with` block = app started.
    assert client is not None


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["app_name"] == "SmartCourse"
    assert body["version"] == "0.1.0"
    assert "environment" in body


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Welcome to SmartCourse API"
    assert body["docs"] == "/docs"


def test_api_v1_root(client):
    response = client.get("/api/v1")

    assert response.status_code == 200
    body = response.json()
    # The v1 root advertises the endpoint groups the API will expose
    assert "endpoints" in body
    for group in ("courses", "users", "enrollments", "analytics", "ai"):
        assert group in body["endpoints"]


def test_unknown_route_returns_404(client):
    """A route that doesn't exist should 404 - proves routing is sane."""
    response = client.get("/this-does-not-exist")
    assert response.status_code == 404


def test_metrics_endpoint_exists(client):
    """Prometheus metrics should be mounted and scrapeable."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus exposition format is plain text
    assert "text/plain" in response.headers["content-type"]
