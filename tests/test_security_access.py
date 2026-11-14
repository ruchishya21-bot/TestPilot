import pytest


@pytest.mark.parametrize(
    "endpoint",
    [
        "/qa",
        "/qa/compare",
        "/qa/flaky",
        "/qa/performance",
    ],
)
def test_unauthenticated_dashboard_access(client, endpoint):
    response = client.get(endpoint)

    assert response.status_code == 302
    assert "/login" in response.location


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/qa/status",
        "/api/qa/logs",
        "/api/qa/analytics",
        "/api/qa/runs",
        "/api/qa/failures",
        "/api/qa/flaky",
        "/api/qa/flaky/stats",
        "/api/performance/history",
        "/api/performance/stats",
    ],
)
def test_unauthenticated_api_access(client, endpoint):
    response = client.get(endpoint)

    assert response.status_code == 401
    assert response.json["success"] is False
    assert "Authentication required" in response.json["error"]


def test_health_endpoint_remains_public(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_login_page_remains_public(client):
    response = client.get("/login")

    assert response.status_code == 200


def test_registration_page_remains_public(client):
    response = client.get("/register")

    assert response.status_code == 200