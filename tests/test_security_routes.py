import pytest


def test_security_dashboard_loads(authenticated_client):

    response = authenticated_client.get("/qa/security")

    assert response.status_code == 200
    assert b"Security Command Center" in response.data
    assert b"Run Security Scan" in response.data


def test_security_dashboard_requires_authentication(client):

    response = client.get("/qa/security")

    assert response.status_code == 302
    assert "/login" in response.location


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/security/stats",
        "/api/security/history",
        "/api/security/findings"
    ]
)
def test_security_apis_require_authentication(client, endpoint):

    response = client.get(endpoint)

    assert response.status_code == 401
    assert response.json["success"] is False


def test_security_stats(authenticated_client):

    response = authenticated_client.get("/api/security/stats")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert "stats" in response.json


def test_security_history(authenticated_client):

    response = authenticated_client.get("/api/security/history")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert "history" in response.json


def test_security_findings(authenticated_client):

    response = authenticated_client.get("/api/security/findings")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert "findings" in response.json


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/security/history?limit=101",
        "/api/security/history?limit=0",
        "/api/security/findings?limit=501",
        "/api/security/findings?limit=0"
    ]
)
def test_security_api_rejects_invalid_limits(
    authenticated_client,
    endpoint
):

    response = authenticated_client.get(endpoint)

    assert response.status_code == 400
    assert response.json["success"] is False


def test_security_scan_api(authenticated_client, monkeypatch):

    from application.routes import security

    fake_results = {
        "id": "test-security-scan",
        "status": "completed",
        "total_checks": 2,
        "passed": 2,
        "failed": 0,
        "warnings": 0,
        "risk_score": 0,
        "findings": []
    }

    monkeypatch.setattr(
        security,
        "run_security_scan",
        lambda: fake_results
    )

    response = authenticated_client.post(
        "/api/security/scan",
        json={}
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["results"]["id"] == "test-security-scan"


@pytest.mark.parametrize(
    "error, expected_status, expected_message",
    [
        (
            ValueError("Invalid target URL."),
            400,
            "Invalid target URL."
        ),
        (
            RuntimeError("Target application unavailable."),
            503,
            "Target application unavailable."
        ),
        (
            Exception("Unexpected internal error."),
            500,
            "Security scan could not be completed."
        )
    ]
)
def test_security_scan_error_handling(
    authenticated_client,
    monkeypatch,
    error,
    expected_status,
    expected_message
):

    from application.routes import security

    def raise_error():
        raise error

    monkeypatch.setattr(
        security,
        "run_security_scan",
        raise_error
    )

    response = authenticated_client.post(
        "/api/security/scan",
        json={}
    )

    assert response.status_code == expected_status
    assert response.json["success"] is False
    assert response.json["error"] == expected_message


def test_security_history_database_error(
    authenticated_client,
    monkeypatch
):

    from application.routes import security

    def raise_error(**kwargs):
        raise RuntimeError("Database unavailable.")

    monkeypatch.setattr(
        security,
        "get_security_history",
        raise_error
    )

    response = authenticated_client.get("/api/security/history")

    assert response.status_code == 500
    assert response.json["success"] is False
    assert response.json["error"] == (
        "Unable to retrieve security scan history."
    )


def test_security_findings_database_error(
    authenticated_client,
    monkeypatch
):

    from application.routes import security

    def raise_error(**kwargs):
        raise RuntimeError("Database unavailable.")

    monkeypatch.setattr(
        security,
        "get_security_findings",
        raise_error
    )

    response = authenticated_client.get("/api/security/findings")

    assert response.status_code == 500
    assert response.json["success"] is False
    assert response.json["error"] == (
        "Unable to retrieve security findings."
    )


def test_security_stats_empty_history(
    authenticated_client,
    monkeypatch
):

    from application.routes import security

    monkeypatch.setattr(
        security,
        "initialize_security_database",
        lambda: None
    )

    monkeypatch.setattr(
        security,
        "get_security_history",
        lambda limit: []
    )

    response = authenticated_client.get("/api/security/stats")

    assert response.status_code == 200
    assert response.json["success"] is True

    stats = response.json["stats"]

    assert stats["total_scans"] == 0
    assert stats["completed_scans"] == 0
    assert stats["average_risk_score"] == 0
    assert stats["latest_risk_score"] == 0
    assert stats["latest_scan_status"] == "No scans yet"
    assert stats["latest_not_assessed"] == 0


def test_security_stats_database_error(
    authenticated_client,
    monkeypatch
):

    from application.routes import security

    def raise_error():
        raise RuntimeError("Database unavailable.")

    monkeypatch.setattr(
        security,
        "initialize_security_database",
        raise_error
    )

    response = authenticated_client.get("/api/security/stats")

    assert response.status_code == 500
    assert response.json["success"] is False
    assert response.json["error"] == (
        "Unable to calculate security statistics."
    )