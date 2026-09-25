"""End-to-end flows that combine API and UI.

Test data is prepared through the API (fast and stable), then the user-facing
behaviour is verified in the browser.
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from api import UsersApi
from pages import AccountPage, LoginPage
from utils.data_factory import new_user_payload

pytestmark = [pytest.mark.e2e, allure.feature("Registration")]


@allure.title("User registered via API can log in through the UI")
def test_user_registered_via_api_can_log_in(page: Page, users_api: UsersApi) -> None:
    user = new_user_payload()
    with allure.step(f"Register {user['email']} via API"):
        response = users_api.register(user)
        assert response.status == 201, response.text()

    with allure.step("Log in through the UI"):
        LoginPage(page).open().login(user["email"], user["password"])

    account = AccountPage(page)
    expect(account.page_title).to_have_text("My account")
    expect(account.header.user_menu).to_contain_text(f"{user['first_name']} {user['last_name']}")
