from typing import Self

import allure
from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.product_page import ProductPage


class HomePage(BasePage):
    """Product overview: grid of products with search, sorting and filters."""

    path = "/"

    SORT_NAME_ASC = "name,asc"
    SORT_NAME_DESC = "name,desc"
    SORT_PRICE_ASC = "price,asc"
    SORT_PRICE_DESC = "price,desc"

    def __init__(self, page) -> None:
        super().__init__(page)
        self.search_input = page.get_by_test_id("search-query")
        self.search_button = page.get_by_test_id("search-submit")
        self.search_term = page.get_by_test_id("search-term")
        self.sort_select = page.get_by_test_id("sort")
        self.product_names = page.get_by_test_id("product-name")
        self.product_prices = page.get_by_test_id("product-price")
        self.no_results = page.get_by_test_id("no-results")

    def open(self) -> Self:
        super().open()
        expect(self.product_names.first).to_be_visible()
        return self

    # The app exposes its loading state in a data-test attribute on the results
    # container (e.g. "search_completed"). Waiting on it is far more reliable
    # than sleeping or waiting for network idle.
    def _wait_for_state(self, state: str) -> None:
        expect(self.page.get_by_test_id(state)).to_be_attached()

    @allure.step("Search for '{query}'")
    def search(self, query: str) -> None:
        self.search_input.fill(query)
        self.search_button.click()
        self._wait_for_state("search_completed")

    @allure.step("Sort products by '{option}'")
    def sort_by(self, option: str) -> None:
        self.sort_select.select_option(option)
        self._wait_for_state("sorting_completed")

    @allure.step("Read product names")
    def get_product_names(self) -> list[str]:
        return [name.strip() for name in self.product_names.all_inner_texts()]

    @allure.step("Read product prices")
    def get_product_prices(self) -> list[float]:
        return [float(text.strip().lstrip("$")) for text in self.product_prices.all_inner_texts()]

    @allure.step("Open product '{name}'")
    def open_product(self, name: str) -> ProductPage:
        self.product_names.filter(has_text=name).first.click()
        product_page = ProductPage(self.page)
        expect(product_page.name).to_be_visible()
        return product_page
