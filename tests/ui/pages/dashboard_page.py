from selenium.webdriver.common.by import By

from tests.ui.pages.base_page import BasePage


class DashboardPage(BasePage):

    DASHBOARD_HEADING = (
        By.CSS_SELECTOR,
        ".dashboard-heading h1"
    )

    LOGOUT_BUTTON = (By.ID, "logoutButton")

    def get_heading(self):

        return self.get_text(self.DASHBOARD_HEADING)

    def logout(self):

        self.click(self.LOGOUT_BUTTON)