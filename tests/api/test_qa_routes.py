import pytest

import application.routes.qa as qa_routes


@pytest.mark.api
class TestQADashboard:

    def test_dashboard_without_previous_runs(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: []
        )

        response = authenticated_client.get("/qa")

        assert response.status_code == 200

    def test_dashboard_with_existing_runs(self, authenticated_client, monkeypatch):

        runs = [
            {
                "id": "run-001",
                "total": 4,
                "passed": 3,
                "failed": 1,
                "skipped": 0,
                "errors": 0,
                "duration": 12.5,
                "status": "completed",
                "started_at": "2026-11-14T10:00:00"
            }
        ]

        details = {
            "run": runs[0],
            "results": [
                {
                    "test_name": "test_api",
                    "category": "API",
                    "status": "passed",
                    "duration": 1.234,
                    "failure_details": None,
                    "screenshot_path": None
                },
                {
                    "test_name": "test_database",
                    "category": "Database",
                    "status": "passed",
                    "duration": 2.345,
                    "failure_details": None,
                    "screenshot_path": None
                },
                {
                    "test_name": "test_functional",
                    "category": "Functional",
                    "status": "passed",
                    "duration": 3.456,
                    "failure_details": None,
                    "screenshot_path": None
                },
                {
                    "test_name": "test_ui",
                    "category": "UI",
                    "status": "failed",
                    "duration": 4.567,
                    "failure_details": "Assertion failed",
                    "screenshot_path": None
                },
                {
                    "test_name": "test_other",
                    "category": "Other",
                    "status": "passed",
                    "duration": 1.111,
                    "failure_details": None,
                    "screenshot_path": None
                }
            ]
        }

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: runs
        )

        monkeypatch.setattr(
            qa_routes,
            "get_run_details",
            lambda run_id: details
        )

        response = authenticated_client.get("/qa")

        assert response.status_code == 200

    def test_dashboard_with_valid_run_id(self, authenticated_client, monkeypatch):

        run = {
            "id": "run-002",
            "total": 2,
            "passed": 2,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 10.5,
            "status": "completed",
            "started_at": "2026-11-14T11:00:00"
        }

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: [run]
        )

        monkeypatch.setattr(
            qa_routes,
            "get_run_details",
            lambda run_id: {
                "run": run,
                "results": []
            }
        )

        response = authenticated_client.get("/qa?run_id=run-002")

        assert response.status_code == 200

    def test_dashboard_with_invalid_run_id(self, authenticated_client, monkeypatch):

        run = {
            "id": "run-003",
            "total": 1,
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 8.5,
            "status": "completed",
            "started_at": "2026-11-14T12:00:00"
        }

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: [run]
        )

        def mock_details(run_id):

            if run_id == "invalid":
                return {"run": None, "results": []}

            return {"run": run, "results": []}

        monkeypatch.setattr(
            qa_routes,
            "get_run_details",
            mock_details
        )

        response = authenticated_client.get("/qa?run_id=invalid")

        assert response.status_code == 200

    def test_dashboard_comparison_page(self, authenticated_client):

        response = authenticated_client.get("/qa/compare")

        assert response.status_code == 200


@pytest.mark.api
class TestQAExecutionAPI:

    def test_start_execution_success(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "start_execution",
            lambda test_type: {
                "status": "running",
                "test_type": test_type
            }
        )

        response = authenticated_client.post(
            "/api/qa/start",
            json={"test_type": "api"}
        )

        assert response.status_code == 202
        assert response.json["success"] is True
        assert response.json["execution"]["test_type"] == "api"

    def test_start_execution_default_suite(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "start_execution",
            lambda test_type: {"test_type": test_type}
        )

        response = authenticated_client.post("/api/qa/start", json={})

        assert response.status_code == 202
        assert response.json["execution"]["test_type"] == "all"

    def test_start_execution_invalid_suite(self, authenticated_client, monkeypatch):

        def mock_start(test_type):
            raise ValueError("Invalid test suite.")

        monkeypatch.setattr(
            qa_routes,
            "start_execution",
            mock_start
        )

        response = authenticated_client.post(
            "/api/qa/start",
            json={"test_type": "invalid"}
        )

        assert response.status_code == 400
        assert response.json["success"] is False

    def test_start_execution_runtime_error(self, authenticated_client, monkeypatch):

        def mock_start(test_type):
            raise RuntimeError("Target application is unhealthy.")

        monkeypatch.setattr(
            qa_routes,
            "start_execution",
            mock_start
        )

        response = authenticated_client.post(
            "/api/qa/start",
            json={"test_type": "all"}
        )

        assert response.status_code == 409
        assert response.json["success"] is False

    def test_start_execution_unexpected_error(self, authenticated_client, monkeypatch):

        def mock_start(test_type):
            raise Exception("Unexpected error.")

        monkeypatch.setattr(
            qa_routes,
            "start_execution",
            mock_start
        )

        response = authenticated_client.post(
            "/api/qa/start",
            json={"test_type": "all"}
        )

        assert response.status_code == 500
        assert response.json["success"] is False

    def test_execution_status(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "get_execution_status",
            lambda: {"status": "running"}
        )

        response = authenticated_client.get("/api/qa/status")

        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["execution"]["status"] == "running"

    def test_execution_logs(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "get_execution_log",
            lambda: ["Test started", "Test completed"]
        )

        response = authenticated_client.get("/api/qa/logs")

        assert response.status_code == 200
        assert len(response.json["logs"]) == 2

    def test_available_test_suites(self, authenticated_client):

        response = authenticated_client.get("/api/qa/suites")

        assert response.status_code == 200
        assert response.json["success"] is True
        assert "all" in response.json["suites"]
        assert "parallel" in response.json["suites"]


@pytest.mark.api
class TestQAAnalyticsAPI:

    def test_analytics_with_execution_history(self, authenticated_client, monkeypatch):

        runs = [
            {
                "id": "analytics-001",
                "started_at": "2026-11-14T10:00:00",
                "total": 10,
                "passed": 8,
                "failed": 1,
                "skipped": 1,
                "errors": 0,
                "duration": 12.345,
                "status": "completed"
            }
        ]

        details = {
            "run": runs[0],
            "results": [
                {"category": "API"},
                {"category": "API"},
                {"category": "Database"},
                {"category": "UI"},
                {"category": "Other"}
            ]
        }

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: runs
        )

        monkeypatch.setattr(
            qa_routes,
            "get_run_details",
            lambda run_id: details
        )

        response = authenticated_client.get("/api/qa/analytics")

        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["summary"]["total_runs"] == 1
        assert response.json["summary"]["total_tests"] == 10
        assert response.json["summary"]["pass_rate"] == 80.0
        assert response.json["category_distribution"]["API"] == 2

    def test_analytics_without_execution_history(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: []
        )

        response = authenticated_client.get("/api/qa/analytics")

        assert response.status_code == 200
        assert response.json["summary"]["total_runs"] == 0
        assert response.json["summary"]["pass_rate"] == 0

    def test_analytics_with_zero_test_run(self, authenticated_client, monkeypatch):

        runs = [
            {
                "id": "analytics-002",
                "started_at": "2026-11-14T10:00:00",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "duration": 0,
                "status": "completed"
            }
        ]

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: runs
        )

        monkeypatch.setattr(
            qa_routes,
            "get_run_details",
            lambda run_id: {
                "run": runs[0],
                "results": []
            }
        )

        response = authenticated_client.get("/api/qa/analytics")

        assert response.status_code == 200
        assert response.json["execution_trends"][0]["pass_rate"] == 0

    def test_analytics_database_error(self, authenticated_client, monkeypatch):

        def mock_runs(limit):
            raise Exception("Database unavailable.")

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            mock_runs
        )

        response = authenticated_client.get("/api/qa/analytics")

        assert response.status_code == 500
        assert response.json["success"] is False


@pytest.mark.api
class TestQAFailureAPI:

    def test_failure_analysis_success(self, authenticated_client, monkeypatch):

        failures = [
            {
                "test_name": "test_login",
                "failure_details": "Assertion failed"
            }
        ]

        monkeypatch.setattr(
            qa_routes,
            "get_failure_analysis",
            lambda limit: failures
        )

        response = authenticated_client.get("/api/qa/failures")

        assert response.status_code == 200
        assert response.json["total_failures"] == 1

    def test_failure_analysis_empty(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "get_failure_analysis",
            lambda limit: []
        )

        response = authenticated_client.get("/api/qa/failures")

        assert response.status_code == 200
        assert response.json["total_failures"] == 0

    def test_failure_analysis_error(self, authenticated_client, monkeypatch):

        def mock_failures(limit):
            raise Exception("Failure database error.")

        monkeypatch.setattr(
            qa_routes,
            "get_failure_analysis",
            mock_failures
        )

        response = authenticated_client.get("/api/qa/failures")

        assert response.status_code == 500
        assert response.json["success"] is False


@pytest.mark.api
class TestQAComparisonAPI:

    def test_comparison_missing_parameters(self, authenticated_client):

        response = authenticated_client.get("/api/qa/compare")

        assert response.status_code == 400

    def test_comparison_same_run_ids(self, authenticated_client):

        response = authenticated_client.get(
            "/api/qa/compare?baseline=run-1&comparison=run-1"
        )

        assert response.status_code == 400

    def test_comparison_success(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "compare_test_runs",
            lambda baseline, comparison: {
                "pass_rate_change": 5
            }
        )

        response = authenticated_client.get(
            "/api/qa/compare?baseline=run-1&comparison=run-2"
        )

        assert response.status_code == 200
        assert response.json["success"] is True

    def test_comparison_missing_runs(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "compare_test_runs",
            lambda baseline, comparison: None
        )

        response = authenticated_client.get(
            "/api/qa/compare?baseline=run-1&comparison=run-2"
        )

        assert response.status_code == 404

    def test_comparison_unexpected_error(self, authenticated_client, monkeypatch):

        def mock_compare(baseline, comparison):
            raise Exception("Comparison failed.")

        monkeypatch.setattr(
            qa_routes,
            "compare_test_runs",
            mock_compare
        )

        response = authenticated_client.get(
            "/api/qa/compare?baseline=run-1&comparison=run-2"
        )

        assert response.status_code == 500
        assert response.json["success"] is False


@pytest.mark.api
class TestQARunHistoryAPI:

    def test_get_test_runs_success(self, authenticated_client, monkeypatch):

        runs = [
            {"id": "run-001"},
            {"id": "run-002"}
        ]

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: runs
        )

        response = authenticated_client.get("/api/qa/runs")

        assert response.status_code == 200
        assert response.json["total_runs"] == 2

    def test_get_test_runs_empty(self, authenticated_client, monkeypatch):

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            lambda limit: []
        )

        response = authenticated_client.get("/api/qa/runs")

        assert response.status_code == 200
        assert response.json["total_runs"] == 0

    def test_get_test_runs_error(self, authenticated_client, monkeypatch):

        def mock_runs(limit):
            raise Exception("Unable to access history.")

        monkeypatch.setattr(
            qa_routes,
            "get_recent_runs",
            mock_runs
        )

        response = authenticated_client.get("/api/qa/runs")

        assert response.status_code == 500
        assert response.json["success"] is False
