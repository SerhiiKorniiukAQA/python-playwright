import allure
import pytest
from playwright.sync_api import Page, expect

from pages import CartPage, HomePage

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

    expect(product_page.header.cart_quantity).to_have_text("1")

    product_page.header.go_to_cart()
    cart = CartPage(page)
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
    expect(product_page.header.cart_quantity).to_have_text(str(quantity))

    cart = CartPage(page).open()
    expect(cart.product_quantities.first).to_have_value(str(quantity))
    assert cart.get_line_price() == pytest.approx(unit_price * quantity)
