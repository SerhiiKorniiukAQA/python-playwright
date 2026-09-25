import allure
import pytest
from playwright.sync_api import Page, expect

from pages import CartPage, HomePage
from utils.allure_report import attach_screenshot

pytestmark = [pytest.mark.ui, allure.feature("Cart")]

PRODUCT = "Combination Pliers"


@pytest.mark.smoke
@allure.title("Product added from its page appears in the cart")
def test_add_product_to_cart(page: Page) -> None:
    home = HomePage(page).open()
    home.search(PRODUCT)
    product_page = home.open_product(PRODUCT)
    unit_price = product_page.get_unit_price()

    product_page.add_to_cart()

    with allure.step("Check that cart counter in the header shows 1"):
        expect(product_page.header.cart_quantity).to_have_text("1")
        attach_screenshot(page, "Product page after adding to cart")

    product_page.header.go_to_cart()
    cart = CartPage(page)
    with allure.step(f"Check that cart contains 1 x '{PRODUCT}' for ${unit_price:.2f}"):
        expect(cart.product_titles).to_have_count(1)
        expect(cart.product_titles.first).to_contain_text(PRODUCT)
        expect(cart.product_quantities.first).to_have_value("1")
        assert cart.get_line_price() == pytest.approx(unit_price)


@allure.title("Cart line price reflects the selected quantity")
def test_add_product_with_quantity(page: Page) -> None:
    quantity = 3
    home = HomePage(page).open()
    home.search(PRODUCT)
    product_page = home.open_product(PRODUCT)
    unit_price = product_page.get_unit_price()

    product_page.set_quantity(quantity)
    product_page.add_to_cart()
    with allure.step(f"Check that cart counter in the header shows {quantity}"):
        expect(product_page.header.cart_quantity).to_have_text(str(quantity))

    cart = CartPage(page).open()
    with allure.step(f"Check line price: {quantity} x ${unit_price:.2f} = ${unit_price * quantity:.2f}"):
        expect(cart.product_quantities.first).to_have_value(str(quantity))
        assert cart.get_line_price() == pytest.approx(unit_price * quantity)
