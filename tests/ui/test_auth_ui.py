import uuid

import pytest

from tests.ui.pages.register_page import RegisterPage
from tests.ui.pages.login_page import LoginPage
from tests.ui.pages.dashboard_page import DashboardPage


@pytest.mark.ui
class TestAuthenticationUI:

    def generate_user(self, prefix):

        unique_id = uuid.uuid4().hex[:8]

        return {
            "username": f"{prefix}_{unique_id}",
            "email": f"{prefix}_{unique_id}@example.com",
            "password": "TestPass@123"
        }

    @pytest.mark.smoke
    def test_user_registration_ui(self, driver):

        register_page = RegisterPage(driver)

        user = self.generate_user("register")

        register_page.open("/register")

        register_page.register(
            user["username"],
            user["email"],
            user["password"]
        )

        register_page.wait.until(
            lambda d: (
                "Account created successfully" in
                register_page.get_message()
                or "already exists" in
                register_page.get_message()
            )
        )

        assert "Account created successfully" in (
            register_page.get_message()
        )

        register_page.wait_for_url("/login")

    @pytest.mark.smoke
    def test_user_login_ui(self, driver):

        register_page = RegisterPage(driver)
        login_page = LoginPage(driver)
        dashboard_page = DashboardPage(driver)

        user = self.generate_user("login")

        register_page.open("/register")

        register_page.register(
            user["username"],
            user["email"],
            user["password"]
        )

        register_page.wait_for_url("/login")

        login_page.login(
            user["email"],
            user["password"]
        )

        login_page.wait_for_url("/dashboard")

        heading = dashboard_page.get_heading()

        assert "Welcome back" in heading
        assert user["username"] in heading

    @pytest.mark.regression
    def test_invalid_login_ui(self, driver):

        login_page = LoginPage(driver)

        user = self.generate_user("unknown")

        login_page.open("/login")

        login_page.login(
            user["email"],
            "WrongPass@123"
        )

        login_page.wait.until(
            lambda d: (
                "Invalid email or password"
                in login_page.get_message()
            )
        )

        assert login_page.get_message() == (
            "Invalid email or password"
        )

    @pytest.mark.smoke
    def test_user_logout_ui(self, driver):

        register_page = RegisterPage(driver)
        login_page = LoginPage(driver)
        dashboard_page = DashboardPage(driver)

        user = self.generate_user("logout")

        register_page.open("/register")

        register_page.register(
            user["username"],
            user["email"],
            user["password"]
        )

        register_page.wait_for_url("/login")

        login_page.login(
            user["email"],
            user["password"]
        )

        login_page.wait_for_url("/dashboard")

        dashboard_page.logout()

        login_page.wait_for_url("/login")

        assert "/login" in driver.current_url