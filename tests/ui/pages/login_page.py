from selenium.webdriver.common.by import By

from tests.ui.pages.base_page import BasePage


class LoginPage(BasePage):

    EMAIL = (By.ID, "email")

    PASSWORD = (By.ID, "password")

    LOGIN_BUTTON = (
        By.CSS_SELECTOR,
        "#loginForm button[type='submit']"
    )

    MESSAGE = (By.ID, "loginMessage")

    def login(self, email, password):

        self.enter_text(self.EMAIL, email)

        self.enter_text(self.PASSWORD, password)

        self.click(self.LOGIN_BUTTON)

    def get_message(self):

        return self.get_text(self.MESSAGE)