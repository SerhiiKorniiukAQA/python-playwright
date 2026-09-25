from pages.base_page import BasePage


class CartPage(BasePage):
    """First step of checkout: the shopping cart."""

    path = "/checkout"

    def __init__(self, page) -> None:
        super().__init__(page)
        self.product_titles = page.get_by_test_id("product-title")
        self.product_quantities = page.get_by_test_id("product-quantity")
        self.line_prices = page.get_by_test_id("line-price")
        self.cart_total = page.get_by_test_id("cart-total")
        self.proceed_button = page.get_by_test_id("proceed-1")

    @staticmethod
    def _to_amount(text: str) -> float:
        return float(text.strip().lstrip("$").replace(",", ""))

    def get_total(self) -> float:
        return self._to_amount(self.cart_total.inner_text())

    def get_line_price(self, index: int = 0) -> float:
        # Line price is quantity x unit price, before cart-level discounts
        # (e.g. the eco discount), so it is the stable value to assert on.
        return self._to_amount(self.line_prices.nth(index).inner_text())
