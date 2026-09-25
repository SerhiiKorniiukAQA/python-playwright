import allure

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/auth/login"

    def __init__(self, page) -> None:
        super().__init__(page)
        self.email_input = page.get_by_test_id("email")
        self.password_input = page.get_by_test_id("password")
        self.submit_button = page.get_by_test_id("login-submit")
        self.login_error = page.get_by_test_id("login-error")
        self.email_error = page.get_by_test_id("email-error")
        self.password_error = page.get_by_test_id("password-error")

    @allure.step("Log in as {email}")
    def login(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()
