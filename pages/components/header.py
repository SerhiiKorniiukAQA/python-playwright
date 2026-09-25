import allure
from playwright.sync_api import Page


class Header:
    """Top navigation bar, shared by every page."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.sign_in_link = page.get_by_test_id("nav-sign-in")
        self.user_menu = page.get_by_test_id("nav-menu")
        self.cart_link = page.get_by_test_id("nav-cart")
        self.cart_quantity = page.get_by_test_id("cart-quantity")

    @allure.step("Go to Sign in")
    def go_to_sign_in(self) -> None:
        self.sign_in_link.click()

    @allure.step("Go to cart")
    def go_to_cart(self) -> None:
        self.cart_link.click()
