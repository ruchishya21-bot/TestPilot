from selenium.webdriver.common.by import By

from tests.ui.pages.base_page import BasePage


class RegisterPage(BasePage):

    USERNAME = (By.ID, "username")
    EMAIL = (By.ID, "email")
    PASSWORD = (By.ID, "password")

    REGISTER_BUTTON = (
        By.CSS_SELECTOR,
        "#registerForm button[type='submit']"
    )

    MESSAGE = (By.ID, "registerMessage")

    def register(self, username, email, password):

        self.enter_text(self.USERNAME, username)

        self.enter_text(self.EMAIL, email)

        self.enter_text(self.PASSWORD, password)

        self.click(self.REGISTER_BUTTON)

    def get_message(self):

        return self.get_text(self.MESSAGE)