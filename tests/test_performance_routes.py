from application.routes import performance


class TestPerformanceDashboard:

    def test_performance_dashboard_loads(self, client):

        response = client.get("/qa/performance")

        assert response.status_code == 200
        assert b"Performance Analytics" in response.data
        assert b"Run Test" in response.data
        assert b"responseChart" in response.data


class TestPerformanceExecution:

    def test_run_performance_success(self, client, monkeypatch):

        expected_results = {
            "id": "test-run-123",
            "endpoint": "/health",
            "total_requests": 5,
            "concurrency": 2,
            "successful_requests": 5,
            "failed_requests": 0,
            "average_response_time": 10.5,
            "requests_per_second": 100.0
        }

        monkeypatch.setattr(
            performance,
            "run_performance_test",
            lambda **kwargs: expected_results
        )

        response = client.post(
            "/api/performance/run",
            json={
                "endpoint": "/health",
                "total_requests": 5,
                "concurrency": 2
            }
        )

        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert response.get_json()["results"] == expected_results

    def test_run_performance_invalid_request_count(self, client):

        response = client.post(
            "/api/performance/run",
            json={"total_requests": 0}
        )

        assert response.status_code == 400

    def test_run_performance_invalid_concurrency(self, client):

        response = client.post(
            "/api/performance/run",
            json={
                "total_requests": 10,
                "concurrency": 26
            }
        )

        assert response.status_code == 400

    def test_run_performance_target_unavailable(
        self, client, monkeypatch
    ):

        def raise_runtime_error(**kwargs):
            raise RuntimeError("Target application is unavailable.")

        monkeypatch.setattr(
            performance,
            "run_performance_test",
            raise_runtime_error
        )

        response = client.post(
            "/api/performance/run",
            json={
                "endpoint": "/health",
                "total_requests": 5,
                "concurrency": 2
            }
        )

        assert response.status_code == 503


class TestPerformanceHistory:

    def test_performance_history_success(self, client, monkeypatch):

        sample_history = [
            {
                "id": "run-123",
                "endpoint": "/health",
                "total_requests": 10,
                "successful_requests": 10,
                "failed_requests": 0,
                "average_response_time": 12.5,
                "requests_per_second": 100.0
            }
        ]

        monkeypatch.setattr(
            performance,
            "get_performance_history",
            lambda limit=20: sample_history
        )

        response = client.get("/api/performance/history")

        assert response.status_code == 200
        assert response.get_json()["total_runs"] == 1
        assert response.get_json()["history"] == sample_history

    def test_performance_history_invalid_limit(self, client):

        response = client.get(
            "/api/performance/history?limit=101"
        )

        assert response.status_code == 400


class TestPerformanceStatistics:

    def test_performance_statistics_success(
        self, client, monkeypatch
    ):

        sample_history = [
            {
                "total_requests": 10,
                "successful_requests": 9,
                "failed_requests": 1,
                "average_response_time": 20.0,
                "requests_per_second": 50.0
            },
            {
                "total_requests": 20,
                "successful_requests": 20,
                "failed_requests": 0,
                "average_response_time": 30.0,
                "requests_per_second": 100.0
            }
        ]

        monkeypatch.setattr(
            performance,
            "initialize_performance_database",
            lambda: None
        )

        monkeypatch.setattr(
            performance,
            "get_performance_history",
            lambda limit=100: sample_history
        )

        response = client.get("/api/performance/stats")

        data = response.get_json()

        assert response.status_code == 200
        assert data["success"] is True

        assert data["stats"]["total_runs"] == 2
        assert data["stats"]["total_requests"] == 30
        assert data["stats"]["successful_requests"] == 29
        assert data["stats"]["failed_requests"] == 1
        assert data["stats"]["average_response_time"] == 25.0
        assert data["stats"]["average_throughput"] == 75.0

    def test_performance_statistics_empty_history(
        self, client, monkeypatch
    ):

        monkeypatch.setattr(
            performance,
            "initialize_performance_database",
            lambda: None
        )

        monkeypatch.setattr(
            performance,
            "get_performance_history",
            lambda limit=100: []
        )

        response = client.get("/api/performance/stats")

        data = response.get_json()

        assert response.status_code == 200
        assert data["success"] is True
        assert data["stats"]["total_runs"] == 0
        assert data["stats"]["total_requests"] == 0
        assert data["stats"]["average_response_time"] == 0
        assert data["stats"]["average_throughput"] == 0