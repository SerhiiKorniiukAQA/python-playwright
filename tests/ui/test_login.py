import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config import settings
from pages import AccountPage, HomePage, LoginPage
from utils.data_factory import unique_email

pytestmark = [pytest.mark.ui, allure.feature("Login")]


@pytest.mark.smoke
@allure.title("Customer logs in and lands on 'My account'")
def test_login_with_valid_credentials(page: Page) -> None:
    home = HomePage(page).open()
    home.header.go_to_sign_in()

    LoginPage(page).login(settings.customer_email, settings.customer_password)

    account = AccountPage(page)
    expect(page).to_have_url(re.compile(r"/account$"))
    expect(account.page_title).to_have_text("My account")
    expect(account.header.user_menu).to_contain_text(settings.customer_full_name)


@allure.title("Wrong credentials show an error and keep the user on the login page")
def test_login_with_invalid_credentials(page: Page) -> None:
    login = LoginPage(page).open()

    # Random email: failed attempts against a real account would lock it.
    login.login(unique_email(), "WrongPassword1!")

    expect(login.login_error).to_contain_text("Invalid email or password")
    expect(page).to_have_url(re.compile(r"/auth/login$"))


@allure.title("Submitting an empty form shows field validation errors")
def test_login_with_empty_fields(page: Page) -> None:
    login = LoginPage(page).open()

    login.submit_button.click()

    expect(login.email_error).to_be_visible()
    expect(login.password_error).to_be_visible()
