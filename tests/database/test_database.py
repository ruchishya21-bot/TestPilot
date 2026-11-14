import pytest

from application.database import db


class TestDatabaseStructure:

    @pytest.mark.database
    def test_users_table_exists(self, client):

        connection = db.get_db_connection()

        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'users'
            """
        ).fetchone()

        connection.close()

        assert result is not None

    @pytest.mark.database
    def test_users_table_has_required_columns(self, client):

        connection = db.get_db_connection()

        columns = connection.execute(
            "PRAGMA table_info(users)"
        ).fetchall()

        connection.close()

        column_names = [column["name"] for column in columns]

        expected_columns = [
            "id",
            "username",
            "email",
            "password_hash",
            "role",
            "created_at"
        ]

        for column in expected_columns:
            assert column in column_names


class TestDatabaseOperations:

    @pytest.mark.database
    def test_registered_user_is_stored(self, client):

        client.post(
            "/api/auth/register",
            json={
                "username": "databaseuser",
                "email": "database@example.com",
                "password": "TestPass@123"
            }
        )

        connection = db.get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            ("database@example.com",)
        ).fetchone()

        connection.close()

        assert user is not None
        assert user["username"] == "databaseuser"

    @pytest.mark.database
    def test_duplicate_email_is_rejected(self, client):

        payload = {
            "username": "userone",
            "email": "duplicate@example.com",
            "password": "TestPass@123"
        }

        client.post("/api/auth/register", json=payload)

        second_response = client.post(
            "/api/auth/register",
            json={
                "username": "usertwo",
                "email": "duplicate@example.com",
                "password": "TestPass@123"
            }
        )

        assert second_response.status_code == 409

    @pytest.mark.database
    def test_password_is_not_stored_as_plain_text(self, client):

        password = "TestPass@123"

        client.post(
            "/api/auth/register",
            json={
                "username": "secureuser",
                "email": "secure@example.com",
                "password": password
            }
        )

        connection = db.get_db_connection()

        user = connection.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            ("secure@example.com",)
        ).fetchone()

        connection.close()

        assert user is not None
        assert user["password_hash"] != password