import pytest


BASE_URL = "/api/auth"


class TestAuthenticationWorkflow:

    @pytest.mark.regression
    def test_complete_registration_login_logout_workflow(self, client):

        # Step 1: Register a new user
        registration = client.post(
            f"{BASE_URL}/register",
            json={
                "username": "workflowuser",
                "email": "workflow@example.com",
                "password": "TestPass@123"
            }
        )

        assert registration.status_code == 201

        # Step 2: Login using registered credentials
        login = client.post(
            f"{BASE_URL}/login",
            json={
                "email": "workflow@example.com",
                "password": "TestPass@123"
            }
        )

        assert login.status_code == 200
        assert login.json["user"]["username"] == "workflowuser"

        # Step 3: Verify session creation
        with client.session_transaction() as session:
            assert session["user_id"] is not None
            assert session["username"] == "workflowuser"

        # Step 4: Logout
        logout = client.post(f"{BASE_URL}/logout")

        assert logout.status_code == 200

        # Step 5: Verify session is cleared
        with client.session_transaction() as session:
            assert "user_id" not in session
            assert "username" not in session

    @pytest.mark.regression
    def test_user_cannot_login_with_wrong_password(self, client):

        client.post(
            f"{BASE_URL}/register",
            json={
                "username": "securityuser",
                "email": "security@example.com",
                "password": "CorrectPass@123"
            }
        )

        response = client.post(
            f"{BASE_URL}/login",
            json={
                "email": "security@example.com",
                "password": "WrongPass@123"
            }
        )

        assert response.status_code == 401

    @pytest.mark.regression
    def test_duplicate_registration_does_not_create_extra_user(self, client):

        payload = {
            "username": "duplicateuser",
            "email": "duplicate@example.com",
            "password": "TestPass@123"
        }

        client.post(f"{BASE_URL}/register", json=payload)

        second_response = client.post(
            f"{BASE_URL}/register",
            json=payload
        )

        assert second_response.status_code == 409

        from application.database import db

        connection = db.get_db_connection()

        result = connection.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?",
            ("duplicate@example.com",)
        ).fetchone()

        connection.close()

        assert result[0] == 1