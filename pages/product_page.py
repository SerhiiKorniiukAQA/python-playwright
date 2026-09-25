from pages.base_page import BasePage


class ProductPage(BasePage):
    """Single product details page: /product/{id}."""

    def __init__(self, page) -> None:
        super().__init__(page)
        self.name = page.get_by_test_id("product-name")
        self.unit_price = page.get_by_test_id("unit-price")
        self.quantity_input = page.get_by_test_id("quantity")
        self.increase_quantity_button = page.get_by_test_id("increase-quantity")
        self.add_to_cart_button = page.get_by_test_id("add-to-cart")

    def get_unit_price(self) -> float:
        return float(self.unit_price.inner_text().strip())

    def set_quantity(self, quantity: int) -> None:
        self.quantity_input.fill(str(quantity))

    def add_to_cart(self) -> None:
        self.add_to_cart_button.click()
