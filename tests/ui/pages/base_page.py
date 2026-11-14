from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:

    BASE_URL = "http://127.0.0.1:5000"

    def __init__(self, driver):

        self.driver = driver

        self.wait = WebDriverWait(driver, 10)

    def open(self, path):

        self.driver.get(self.BASE_URL + path)

    def find(self, locator):

        return self.wait.until(
            EC.visibility_of_element_located(locator)
        )

    def click(self, locator):

        self.wait.until(
            EC.element_to_be_clickable(locator)
        ).click()

    def enter_text(self, locator, value):

        element = self.find(locator)

        element.clear()

        element.send_keys(value)

    def get_text(self, locator):

        return self.find(locator).text

    def wait_for_url(self, expected_path):

        self.wait.until(
            EC.url_contains(expected_path)
        )