import pytest
import sqlite3

from application.database import db


BASE_URL = "/api/auth"


class TestUserRegistration:

    @pytest.mark.api
    @pytest.mark.smoke
    def test_successful_registration(self, client):

        response = client.post(
            f"{BASE_URL}/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass@123"
            }
        )

        assert response.status_code == 201
        assert response.json["message"] == "Registration successful"

    @pytest.mark.api
    def test_duplicate_registration(self, client):

        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass@123"
        }

        client.post(f"{BASE_URL}/register", json=payload)

        response = client.post(
            f"{BASE_URL}/register",
            json=payload
        )

        assert response.status_code == 409

    @pytest.mark.api
    def test_missing_registration_fields(self, client):

        response = client.post(
            f"{BASE_URL}/register",
            json={
                "username": "testuser"
            }
        )

        assert response.status_code == 400

    @pytest.mark.api
    def test_short_password(self, client):

        response = client.post(
            f"{BASE_URL}/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "123"
            }
        )

        assert response.status_code == 400

    @pytest.mark.api
    def test_password_is_hashed(self, client):

        client.post(
            f"{BASE_URL}/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass@123"
            }
        )

        connection = db.get_db_connection()

        user = connection.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            ("test@example.com",)
        ).fetchone()

        connection.close()

        assert user is not None
        assert user["password_hash"] != "TestPass@123"


class TestUserLogin:

    @pytest.fixture(autouse=True)
    def create_user(self, client):

        client.post(
            f"{BASE_URL}/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass@123"
            }
        )

    @pytest.mark.api
    @pytest.mark.smoke
    def test_successful_login(self, client):

        response = client.post(
            f"{BASE_URL}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass@123"
            }
        )

        assert response.status_code == 200
        assert response.json["message"] == "Login successful"

    @pytest.mark.api
    def test_invalid_password(self, client):

        response = client.post(
            f"{BASE_URL}/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401

    @pytest.mark.api
    def test_unknown_email(self, client):

        response = client.post(
            f"{BASE_URL}/login",
            json={
                "email": "unknown@example.com",
                "password": "TestPass@123"
            }
        )

        assert response.status_code == 401

    @pytest.mark.api
    def test_missing_login_fields(self, client):

        response = client.post(
            f"{BASE_URL}/login",
            json={
                "email": "test@example.com"
            }
        )

        assert response.status_code == 400

    @pytest.mark.api
    def test_successful_logout(self, client):

        client.post(
            f"{BASE_URL}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass@123"
            }
        )

        response = client.post(f"{BASE_URL}/logout")

        assert response.status_code == 200
        assert response.json["message"] == "Logout successful"