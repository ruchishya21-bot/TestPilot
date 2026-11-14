class TestApplicationPages:

    def test_home_page_without_login(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert b"html" in response.data

    def test_home_page_with_login(self, client):
        with client.session_transaction() as session:
            session["user_id"] = 1

        response = client.get("/")

        assert response.status_code == 302
        assert response.location.endswith("/dashboard")

    def test_login_page_without_login(self, client):
        response = client.get("/login")

        assert response.status_code == 200

    def test_login_page_with_login(self, client):
        with client.session_transaction() as session:
            session["user_id"] = 1

        response = client.get("/login")

        assert response.status_code == 302
        assert response.location.endswith("/dashboard")

    def test_register_page_without_login(self, client):
        response = client.get("/register")

        assert response.status_code == 200

    def test_register_page_with_login(self, client):
        with client.session_transaction() as session:
            session["user_id"] = 1

        response = client.get("/register")

        assert response.status_code == 302
        assert response.location.endswith("/dashboard")

    def test_dashboard_without_login(self, client):
        response = client.get("/dashboard")

        assert response.status_code == 302
        assert response.location.endswith("/login")

    def test_dashboard_with_login(self, client):
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["username"] = "TestUser"

        response = client.get("/dashboard")

        assert response.status_code == 200
        assert b"TestUser" in response.data

    def test_health_endpoint(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.get_json() == {
            "status": "healthy"
        }