import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config import settings
from pages import AccountPage

pytestmark = [pytest.mark.ui, allure.feature("Access control")]


@pytest.mark.smoke
@allure.title("Customer logged in via API token lands straight on 'My account'")
def test_logged_in_customer_opens_account(customer_page: Page) -> None:
    account = AccountPage(customer_page).open()

    with allure.step("Check account page and user name without going through the login form"):
        expect(account.page_title).to_have_text("My account")
        expect(account.header.user_menu).to_contain_text(settings.customer.full_name)


@allure.title("Anonymous user is redirected from 'My account' to login")
def test_anonymous_user_is_redirected_to_login(page: Page) -> None:
    AccountPage(page).open()

    with allure.step("Check redirect to the login page"):
        expect(page).to_have_url(re.compile(r"/auth/login$"))


@allure.title("Customer cannot open the admin dashboard")
def test_customer_cannot_open_admin_dashboard(customer_page: Page) -> None:
    with allure.step("Open /admin/dashboard as a customer"):
        customer_page.goto("/admin/dashboard")

    with allure.step("Check that access is denied with a redirect to login"):
        expect(customer_page).to_have_url(re.compile(r"/auth/login$"))
