"""UI behaviour under controlled backend responses (page.route).

Real data can't produce a server error or an arbitrary product on demand,
so these tests replace the API response and check how the UI reacts.
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from pages import HomePage
from utils.mocks import fake_product, mock_product_search, product_search_response

pytestmark = [pytest.mark.ui, allure.feature("Network mocking")]


@allure.title("Search results render exactly what the API returned")
def test_search_renders_api_data(page: Page) -> None:
    mock_product_search(page, product_search_response(fake_product("Mocked Titanium Hammer", 123.45)))
    home = HomePage(page).open()

    home.search("hammer")

    with allure.step("Check that the grid shows only the mocked product with its price"):
        expect(home.product_names).to_have_count(1)
        expect(home.product_names.first).to_have_text("Mocked Titanium Hammer")
        expect(home.product_prices.first).to_have_text("$123.45")


@pytest.mark.parametrize("status", [500, 503])
@allure.title("Search failure with HTTP {status} shows 'no results' instead of stale data")
def test_search_handles_server_error(page: Page, status: int) -> None:
    home = HomePage(page).open()
    mock_product_search(page, {"message": "Server Error"}, status=status)

    home.search("pliers")

    with allure.step("Check that previous products are cleared and 'no results' is shown"):
        expect(home.product_names).to_have_count(0)
        expect(home.no_results).to_be_visible()
